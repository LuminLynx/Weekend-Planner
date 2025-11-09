"""Dining provider integration with local fallback."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.config import ConnectorSettings
from app.utils.http import CircuitBreaker, HttpClient

LOGGER = logging.getLogger(__name__)


@dataclass
class DiningConnector:
    settings: ConnectorSettings
    token: str | None = None

    def __post_init__(self) -> None:
        self._circuit_breaker = CircuitBreaker()
        self._client = HttpClient(
            timeout=self.settings.timeout_seconds,
            retries=self.settings.retries,
            circuit_breaker=self._circuit_breaker,
        )

    async def fetch(self, *, date: str, location: str | None = None) -> List[Dict]:
        params = {"date": date}
        if location:
            params["location"] = location
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else None
        try:
            payload = await self._client.get_json(self.settings.base_url, params=params, headers=headers)
            options = payload.get("restaurants", [])
            LOGGER.debug("Dining provider returned %s restaurants", len(options))
            return [self._normalise(item) for item in options]
        except Exception as exc:  # noqa: BLE001 - fallback path
            LOGGER.warning("Dining API unavailable (%s); using bundled dataset", exc)
            return self._fallback()

    def _fallback(self) -> List[Dict]:
        data_path = Path(__file__).resolve().parent.parent / "data" / "dining.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        options = payload.get("restaurants", [])
        return [self._normalise(item) for item in options]

    def _normalise(self, item: Dict) -> Dict:
        return {
            "name": item.get("name"),
            "est_pp": item.get("price_per_person"),
            "distance_m": item.get("distance_m"),
            "booking_url": item.get("booking_url"),
        }
