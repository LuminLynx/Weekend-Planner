"""Foreign exchange connector with simple disk caching."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from app.config import FXSettings
from app.utils.http import HttpClient

LOGGER = logging.getLogger(__name__)
CACHE_FILENAME = "fx_rates.json"
CACHE_MAX_AGE = timedelta(hours=24)


@dataclass
class FXConnector:
    settings: FXSettings
    _memory_cache: Dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._client = HttpClient(timeout=6, retries=1)
        cache_dir = Path("~/.weekend-planner/cache").expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path = cache_dir / CACHE_FILENAME

    def get_rates(self) -> Dict[str, float]:
        if self._memory_cache:
            return self._memory_cache
        if self._is_cache_valid():
            LOGGER.debug("Using cached FX rates from %s", self._cache_path)
            self._memory_cache = self._load_cache()
            return self._memory_cache

        params = {"base": self.settings.base_currency}
        try:
            payload = self._client.get_json(self.settings.base_url, params=params)
            rates = payload.get("rates", {})
            rates[self.settings.base_currency] = 1.0
            self._write_cache(rates)
            self._memory_cache = rates
            return rates
        except Exception as exc:  # noqa: BLE001 - fallback to cached/built-in
            LOGGER.warning("FX provider unavailable (%s); using fallback rates", exc)
            if self._cache_path.exists():
                self._memory_cache = self._load_cache()
                return self._memory_cache
            self._memory_cache = dict(self.settings.fallback_rates)
            return self._memory_cache

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        rates = self.get_rates()
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
