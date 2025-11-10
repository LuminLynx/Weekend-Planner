"""Foreign exchange connector with simple disk caching."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from app.config import FXSettings
from app.utils.http import HttpClient
from app.utils.metrics import record_cache_hit, record_cache_miss, record_latency

LOGGER = logging.getLogger(__name__)
CACHE_FILENAME = "fx_rates.json"
CACHE_MAX_AGE = timedelta(hours=24)


@dataclass
class FXConnector:
    settings: FXSettings
    offline_mode: bool = False
    _memory_cache: Dict[str, float] = field(default_factory=dict, init=False)
    _fx_source: str = field(default="live", init=False)

    def __post_init__(self) -> None:
        self._client = HttpClient(timeout=6, retries=1)
        cache_dir = Path("~/.weekend-planner/cache").expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path = cache_dir / CACHE_FILENAME

    async def get_rates(self) -> Dict[str, float]:
        if self._memory_cache:
            record_cache_hit()
            return self._memory_cache
        
        # In offline mode, use last good cached data without checking TTL
        if self.offline_mode:
            if self._cache_path.exists():
                LOGGER.debug("OFFLINE MODE: Using last good FX rates from %s", self._cache_path)
                self._memory_cache = self._load_cache()
                self._fx_source = "last_good"
                record_cache_hit()
                return self._memory_cache
            else:
                LOGGER.warning("OFFLINE MODE: No cached FX data available, using fallback rates")
                self._memory_cache = dict(self.settings.fallback_rates)
                self._fx_source = "last_good"
                return self._memory_cache
        
        if self._is_cache_valid():
            LOGGER.debug("Using cached FX rates from %s", self._cache_path)
            self._memory_cache = self._load_cache()
            self._fx_source = "cached"
            record_cache_hit()
            return self._memory_cache

        record_cache_miss()
        params = {"base": self.settings.base_currency}
        try:
            start_time = time.time()
            payload = await self._client.get_json(self.settings.base_url, params=params)
            latency_ms = (time.time() - start_time) * 1000
            record_latency("fx_live_latency_ms", latency_ms)
            rates = payload.get("rates", {})
            rates[self.settings.base_currency] = 1.0
            self._write_cache(rates)
            self._memory_cache = rates
            self._fx_source = "live"
            return rates
        except Exception as exc:  # noqa: BLE001 - fallback to cached/built-in
            LOGGER.warning("FX provider unavailable (%s); using fallback rates", exc)
            if self._cache_path.exists():
                self._memory_cache = self._load_cache()
                self._fx_source = "last_good"
                return self._memory_cache
            self._memory_cache = dict(self.settings.fallback_rates)
            self._fx_source = "last_good"
            return self._memory_cache

    async def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        rates = await self.get_rates()
        if from_currency not in rates or to_currency not in rates:
            return amount
        base_amount = amount / rates[from_currency]
        return base_amount * rates[to_currency]

    def _is_cache_valid(self) -> bool:
        if not self._cache_path.exists():
            return False
        modified = datetime.fromtimestamp(self._cache_path.stat().st_mtime, tz=timezone.utc)
        return datetime.now(timezone.utc) - modified < CACHE_MAX_AGE

    def _load_cache(self) -> Dict[str, float]:
        with self._cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_cache(self, rates: Dict[str, float]) -> None:
        with self._cache_path.open("w", encoding="utf-8") as handle:
            json.dump(rates, handle)
    
    def get_fx_source(self) -> str:
        """Get the FX source for debug information."""
        return self._fx_source
