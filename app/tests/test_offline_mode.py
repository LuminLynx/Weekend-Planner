
import pytest
import os
from unittest.mock import AsyncMock, patch
from app.config import load_settings, AppSettings, ConnectorSettings, FXSettings, Settings
from app.services.planner import Planner
from app.connectors.fx import FXConnector
from app.connectors.dining import DiningConnector
from app.connectors.ticket_vendor_a import TicketVendorAConnector
from app.connectors.ticket_vendor_b import TicketVendorBConnector
from app.utils.cache import SimpleCache


@pytest.fixture
def test_cache(tmp_path):
    """Create a test cache instance"""
    cache = SimpleCache(cache_dir=str(tmp_path / "test_cache"))
    yield cache
    cache.clear()


def test_cache_ignore_ttl(test_cache):
    """Test that cache can ignore TTL in offline mode"""
    import time
    
    # Set a value
    test_cache.set("test_key", {"data": "old_value"})
    
    # Wait for expiration
    time.sleep(2.1)
    
    # Without ignore_ttl, should be expired
    result = test_cache.get("test_key", ttl_seconds=2)
    assert result is None
    
    # Reset for next test
    test_cache.set("test_key", {"data": "old_value"})
    time.sleep(2.1)
    
    # With ignore_ttl, should still be available
    result = test_cache.get("test_key", ttl_seconds=2, ignore_ttl=True)
    assert result == {"data": "old_value"}


def test_config_offline_mode_env_var():
    """Test that OFFLINE_MODE environment variable is read correctly"""
    # Test with OFFLINE_MODE=true
    with patch.dict(os.environ, {"OFFLINE_MODE": "true"}):
        settings = load_settings()
        assert settings.app.offline_mode is True
    
    # Test with OFFLINE_MODE=false
    with patch.dict(os.environ, {"OFFLINE_MODE": "false"}):
        settings = load_settings()
        assert settings.app.offline_mode is False
    
    # Test with OFFLINE_MODE=1
    with patch.dict(os.environ, {"OFFLINE_MODE": "1"}):
        settings = load_settings()
        assert settings.app.offline_mode is True
    
    # Test with OFFLINE_MODE not set
    with patch.dict(os.environ, {}, clear=True):
        settings = load_settings()
        assert settings.app.offline_mode is False


def test_planner_offline_mode_explicit():
    """Test that Planner accepts offline_mode parameter"""
    planner = Planner(offline_mode=True)
    assert planner.settings.app.offline_mode is True
    assert planner.fx.offline_mode is True
    assert planner.vendor_a.offline_mode is True
    assert planner.vendor_b.offline_mode is True
    assert planner.dining.offline_mode is True


def test_planner_offline_mode_from_env():
    """Test that Planner reads offline mode from environment"""
    with patch.dict(os.environ, {"OFFLINE_MODE": "true"}):
        planner = Planner()
        assert planner.settings.app.offline_mode is True


def test_fx_connector_offline_mode_config():
    """Test FX connector is created with offline mode"""
    fx_settings = FXSettings(
        base_url="http://example.com/api",
        base_currency="USD",
        fallback_rates={"USD": 1.0, "EUR": 0.9}
    )
    
    connector = FXConnector(fx_settings, offline_mode=True)
    assert connector.offline_mode is True


def test_dining_connector_offline_mode_config():
    """Test dining connector in offline mode configuration"""
    settings = ConnectorSettings(base_url="http://example.com/api")
    connector = DiningConnector(settings, offline_mode=True)
    assert connector.offline_mode is True


def test_vendor_a_offline_mode_config():
    """Test vendor A connector in offline mode configuration"""
    settings = ConnectorSettings(base_url="http://example.com/api", page_size=10)
    connector = TicketVendorAConnector(settings, offline_mode=True)
    assert connector.offline_mode is True


def test_vendor_b_offline_mode_config():
    """Test vendor B connector in offline mode configuration"""
    settings = ConnectorSettings(base_url="http://example.com/api", page_size=10)
    connector = TicketVendorBConnector(settings, offline_mode=True)
    assert connector.offline_mode is True
