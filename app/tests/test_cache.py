
import pytest
import time
from pathlib import Path
from app.utils.cache import SimpleCache


@pytest.fixture
def test_cache(tmp_path):
    """Create a test cache instance"""
    cache = SimpleCache(cache_dir=str(tmp_path / "test_cache"))
    yield cache
    # Cleanup
    cache.clear()


def test_cache_set_and_get(test_cache):
    """Test basic cache set and get"""
    test_cache.set("test_key", {"data": "value"})
    result = test_cache.get("test_key", ttl_seconds=60)
    assert result == {"data": "value"}


def test_cache_miss(test_cache):
    """Test cache miss returns None"""
    result = test_cache.get("nonexistent", ttl_seconds=60)
    assert result is None


def test_cache_expiration(test_cache):
    """Test that cache expires after TTL"""
    test_cache.set("expiring_key", "value")
    
    # Should be available immediately
    result = test_cache.get("expiring_key", ttl_seconds=2)
    assert result == "value"
    
    # Wait for expiration
    time.sleep(2.1)
    
    # Should be expired
    result = test_cache.get("expiring_key", ttl_seconds=2)
    assert result is None


def test_cache_clear_specific_key(test_cache):
    """Test clearing a specific cache key"""
    test_cache.set("key1", "value1")
    test_cache.set("key2", "value2")
    
    test_cache.clear("key1")
    
    assert test_cache.get("key1", ttl_seconds=60) is None
    assert test_cache.get("key2", ttl_seconds=60) == "value2"


def test_cache_clear_all(test_cache):
    """Test clearing entire cache"""
    test_cache.set("key1", "value1")
    test_cache.set("key2", "value2")
    
    test_cache.clear()
    
    assert test_cache.get("key1", ttl_seconds=60) is None
    assert test_cache.get("key2", ttl_seconds=60) is None
