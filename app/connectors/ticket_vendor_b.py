"""Connector implementation for ticket vendor B."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.config import ConnectorSettings
from app.utils.http import CircuitBreaker, HttpClient, aggregate_paginated

LOGGER = logging.getLogger(__name__)


@dataclass
class TicketVendorBConnector:
    settings: ConnectorSettings
    token: str | None = None
    offline_mode: bool = False

    def __post_init__(self) -> None:
        self._circuit_breaker = CircuitBreaker()
        self._client = HttpClient(
            timeout=self.settings.timeout_seconds,
            retries=self.settings.retries,
            circuit_breaker=self._circuit_breaker,
        )

    async def fetch(self, *, date: str) -> List[Dict]:
        page_size = self.settings.page_size or 50

        async def _page_loader(page: int, page_size: int) -> List[Dict]:
            # In offline mode, use fallback data directly
            if self.offline_mode:
                LOGGER.debug("OFFLINE MODE: Using bundled vendor B dataset")
                return self._load_fallback(page=page, page_size=page_size)
            
            params = {"date": date, "page": page, "limit": page_size}
            headers = {"X-Api-Key": self.token} if self.token else None
            try:
                payload = await self._client.get_json(self.settings.base_url, params=params, headers=headers)
                events = payload.get("results", [])
                LOGGER.debug("Vendor B page %s returned %s events", page, len(events))
                return events
            except Exception as exc:  # noqa: BLE001 - fallback intentionally broad
                LOGGER.warning("Vendor B API unavailable (%s); using bundled dataset", exc)
                return self._load_fallback(page=page, page_size=page_size)

        raw_events = await aggregate_paginated(_page_loader, page_size)
        return [self._normalise(event) for event in raw_events]

    def _load_fallback(self, *, page: int, page_size: int) -> List[Dict]:
        data_path = Path(__file__).resolve().parent.parent / "data" / "vendor_b.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        events = payload.get("results", [])
        start = (page - 1) * page_size
        end = start + page_size
        return events[start:end]

    def _normalise(self, event: Dict) -> Dict:
        promos = event.get("promos", [])
        return {
            "provider": "vendor_b",
            "title": event.get("name"),
            "start_ts": event.get("start"),
            "venue": event.get("venue"),
            "city": event.get("city"),
            "price": event.get("price", {}),
            "fees": event.get("fees", []),
            "vat_rate": event.get("vat_rate"),
            "promos": promos,
            "inventory_hint": event.get("inventory_hint", "unknown"),
            "url": event.get("url"),
        }
