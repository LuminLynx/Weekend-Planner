"""HTTP utilities with retries, exponential backoff, and circuit breaking."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Dict, Iterable, List, Optional
from urllib import error, parse, request

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
class _Response:
    status: int
    body: bytes

    def json(self) -> Dict[str, Any]:
        if not self.body:
            return {}
        return json.loads(self.body.decode("utf-8"))


@dataclass
class HttpClient:
    """Simple HTTP client with retries and exponential backoff."""

    timeout: float = 5.0
    retries: int = 2
    backoff_factor: float = 0.5
    circuit_breaker: Optional[CircuitBreaker] = None

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        response = self.request("GET", url, params=params, headers=headers)
        return response.json()

    def request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> _Response:
        if self.circuit_breaker and not self.circuit_breaker.allow_request():
            raise RuntimeError("Circuit breaker open")

        attempt = 0
        last_error: Exception | None = None
        while attempt <= self.retries:
            try:
                full_url = url
                if params:
                    query = parse.urlencode(params)
                    full_url = f"{url}{'&' if '?' in url else '?'}{query}"
                req = request.Request(full_url, method=method, headers=headers or {})
                with request.urlopen(req, timeout=self.timeout) as response:  # noqa: S310 - controlled URL from config
                    if response.status >= 500:
                        raise error.HTTPError(full_url, response.status, "Server error", response.headers, None)
                    data = response.read()
                    if self.circuit_breaker:
                        self.circuit_breaker.on_success()
                    return _Response(status=response.status, body=data)
            except (error.URLError, error.HTTPError, RuntimeError) as exc:
                last_error = exc
                if self.circuit_breaker:
                    self.circuit_breaker.on_failure()
                if attempt == self.retries:
                    LOGGER.error("Request failed after %s attempts: %s", attempt + 1, exc)
                    raise
                sleep_time = self.backoff_factor * (2**attempt)
                LOGGER.warning("Request attempt %s failed (%s); retrying in %.2fs", attempt + 1, exc, sleep_time)
                time.sleep(sleep_time)
                attempt += 1
        assert last_error is not None
        raise last_error


def aggregate_paginated(
    fetch_page: Callable[[int, int], List[Dict[str, Any]]],
    page_size: int,
) -> Iterable[Dict[str, Any]]:
    """Helper to fetch and aggregate paginated responses."""
    page = 1
    while True:
        payload = fetch_page(page=page, page_size=page_size)
        if not payload:
            break
        for item in payload:
            yield item
        if len(payload) < page_size:
            break
        page += 1
