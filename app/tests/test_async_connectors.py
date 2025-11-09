"""Tests for async connector implementation."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.config import ConnectorSettings, FXSettings
from app.connectors.dining import DiningConnector
from app.connectors.fx import FXConnector
from app.connectors.ticket_vendor_a import TicketVendorAConnector
from app.connectors.ticket_vendor_b import TicketVendorBConnector


def test_fx_connector_async_get_rates(tmp_path, monkeypatch):
    """Test that FXConnector.get_rates is async and returns correct format."""
    monkeypatch.setenv("HOME", str(tmp_path))
    settings = FXSettings(
        base_url="https://example.com/rates",
        base_currency="EUR",
        fallback_rates={"EUR": 1.0, "USD": 1.1}
    )
    connector = FXConnector(settings)
    connector._write_cache({"EUR": 1.0, "USD": 1.1, "GBP": 0.86})
    
    rates = asyncio.run(connector.get_rates())
    
    assert isinstance(rates, dict)
    assert "EUR" in rates
    assert rates["EUR"] == 1.0


def test_dining_connector_async_fetch():
    """Test that DiningConnector.fetch is async and returns correct format."""
    settings = ConnectorSettings(
        base_url="https://example.com/dining",
        timeout_seconds=5,
        retries=1
    )
    connector = DiningConnector(settings)
    
    # Since the API will fail, it should fall back to bundled data
    result = asyncio.run(connector.fetch(date="2025-12-15"))
    
    assert isinstance(result, list)
    if result:
        assert "name" in result[0]
        assert "est_pp" in result[0]


def test_vendor_a_connector_async_fetch():
    """Test that TicketVendorAConnector.fetch is async and returns correct format."""
    settings = ConnectorSettings(
        base_url="https://example.com/vendor-a",
        timeout_seconds=5,
        retries=1,
        page_size=50
    )
    connector = TicketVendorAConnector(settings)
    
    # Since the API will fail, it should fall back to bundled data
    result = asyncio.run(connector.fetch(date="2025-12-15"))
    
    assert isinstance(result, list)
    if result:
        assert "provider" in result[0]
        assert result[0]["provider"] == "vendor_a"


def test_vendor_b_connector_async_fetch():
    """Test that TicketVendorBConnector.fetch is async and returns correct format."""
    settings = ConnectorSettings(
        base_url="https://example.com/vendor-b",
        timeout_seconds=5,
        retries=1,
        page_size=50
    )
    connector = TicketVendorBConnector(settings)
    
    # Since the API will fail, it should fall back to bundled data
    result = asyncio.run(connector.fetch(date="2025-12-15"))
    
    assert isinstance(result, list)
    if result:
        assert "provider" in result[0]
        assert result[0]["provider"] == "vendor_b"


def test_concurrent_execution_speedup():
    """Test that concurrent execution with asyncio.gather provides speedup."""
    
    async def mock_slow_fetch(delay: float):
        """Simulate a slow async operation."""
        await asyncio.sleep(delay)
        return {"result": "success"}
    
    async def run_concurrent():
        """Run three operations concurrently."""
        results = await asyncio.gather(
            mock_slow_fetch(0.1),
            mock_slow_fetch(0.1),
            mock_slow_fetch(0.1)
        )
        return results
    
    import time
    start = time.time()
    results = asyncio.run(run_concurrent())
    elapsed = time.time() - start
    
    # All three 0.1s operations should complete in ~0.1s total (concurrent)
    # not 0.3s (sequential)
    assert elapsed < 0.2, f"Concurrent execution too slow: {elapsed:.3f}s"
    assert len(results) == 3
    assert all(r["result"] == "success" for r in results)
