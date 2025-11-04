
import pytest
import asyncio
from pathlib import Path
from app.connectors.fx import get_fx_rates, FX_LAST_GOOD_PATH, _save_last_good


@pytest.fixture
def cleanup_fx_cache():
    """Remove fx_last_good.json before and after test"""
    if FX_LAST_GOOD_PATH.exists():
        FX_LAST_GOOD_PATH.unlink()
    yield
    if FX_LAST_GOOD_PATH.exists():
        FX_LAST_GOOD_PATH.unlink()


def test_fx_fallback_to_last_good_on_network_error(cleanup_fx_cache):
    """Test that FX falls back to last_good when network fails"""
    # Save a last_good file
    _save_last_good({"EUR": 1.0, "USD": 1.08, "GBP": 0.85})
    
    # Try to fetch from invalid URL with 0 TTL (will not use cache, goes to network then fallback)
    rates, source = asyncio.run(get_fx_rates("https://invalid-domain-12345.example/latest", ttl_seconds=0))
    
    assert source == "last_good"
    assert rates["EUR"] == 1.0
    assert rates["USD"] == 1.08


def test_fx_fallback_to_eur_only_when_no_cache(cleanup_fx_cache):
    """Test ultimate fallback when no cache exists"""
    rates, source = asyncio.run(get_fx_rates("https://invalid-domain-12345.example/latest"))
    
    assert source == "fallback_eur_only"
    assert rates == {"EUR": 1.0}


def test_fx_uses_cached_last_good_within_ttl(cleanup_fx_cache):
    """Test that cached last_good is used if within TTL"""
    # Save a recent last_good
    _save_last_good({"EUR": 1.0, "USD": 1.10})
    
    # Fetch with short TTL - should use cache even with invalid URL
    rates, source = asyncio.run(get_fx_rates("https://invalid-domain-12345.example/latest", ttl_seconds=7200))
    
    assert source == "cached_last_good"
    assert rates["USD"] == 1.10
