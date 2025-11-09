"""HTTP utilities with retries, exponential backoff, and circuit breaking."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Dict, Iterable, List, Optional

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    """Circuit breaker that trips after consecutive failures."""

    failure_threshold: int = 3
    reset_timeout: float = 60.0
    _failures: int = 0
    _state: str = "closed"
    _opened_at: float = 0.0
    _lock: Lock = field(default_factory=Lock)

    def allow_request(self) -> bool:
        with self._lock:
            if self._state == "open":
                if time.monotonic() - self._opened_at >= self.reset_timeout:
                    self._state = "half-open"
                    LOGGER.debug("Circuit breaker moving to half-open state")
                    return True
                LOGGER.debug("Circuit breaker open; rejecting request")
                return False
            return True

    def on_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = "closed"
            LOGGER.debug("Circuit breaker reset to closed state")

    def on_failure(self) -> None:
        with self._lock:
            self._failures += 1
            LOGGER.debug("Circuit breaker recorded failure %s", self._failures)
            if self._failures >= self.failure_threshold:
                self._state = "open"
                self._opened_at = time.monotonic()
                LOGGER.warning("Circuit breaker opened after %s failures", self._failures)


@dataclass
class HttpClient:
    """Async HTTP client with retries and exponential backoff."""

    timeout: float = 5.0
    retries: int = 2
    backoff_factor: float = 0.5
    circuit_breaker: Optional[CircuitBreaker] = None
    _client: Optional[httpx.AsyncClient] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._client = None

    async def __aenter__(self) -> HttpClient:
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()

    async def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        response = await self.request("GET", url, params=params, headers=headers)
        return response.json()

    async def request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        if self.circuit_breaker and not self.circuit_breaker.allow_request():
            raise RuntimeError("Circuit breaker open")

        # Create client if not in context manager
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        attempt = 0
        last_error: Exception | None = None
        while attempt <= self.retries:
            try:
                response = await self._client.request(method, url, params=params, headers=headers)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response
                    )
                if self.circuit_breaker:
                    self.circuit_breaker.on_success()
                return response
            except (httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
                if self.circuit_breaker:
                    self.circuit_breaker.on_failure()
                if attempt == self.retries:
                    LOGGER.error("Request failed after %s attempts: %s", attempt + 1, exc)
                    raise
                sleep_time = self.backoff_factor * (2**attempt)
                LOGGER.warning("Request attempt %s failed (%s); retrying in %.2fs", attempt + 1, exc, sleep_time)
                await asyncio.sleep(sleep_time)
                attempt += 1
        assert last_error is not None
        raise last_error


async def aggregate_paginated(
    fetch_page: Callable[[int, int], Any],
    page_size: int,
) -> List[Dict[str, Any]]:
    """Helper to fetch and aggregate paginated responses."""
    results = []
    page = 1
    while True:
        payload = await fetch_page(page=page, page_size=page_size)
        if not payload:
            break
        results.extend(payload)
        if len(payload) < page_size:
            break
        page += 1
    return results
