"""
Tests for metrics endpoint in the server.
"""

import pytest
from fastapi.testclient import TestClient
from app.server import app
from app.utils.metrics import get_metrics_collector


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test"""
    collector = get_metrics_collector()
    collector.reset()
    yield
    collector.reset()


def test_metrics_endpoint_exists(client):
    """Test that /metrics endpoint exists and returns 200"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_metrics_endpoint_format(client):
    """Test that /metrics returns Prometheus format"""
    response = client.get("/metrics")
    text = response.text
    
    # Should contain TYPE comments
    assert "# TYPE" in text
    assert "gauge" in text


def test_metrics_endpoint_with_data(client):
    """Test metrics endpoint with actual recorded data"""
    from app.utils.metrics import record_latency, record_cache_hit, record_cache_miss
    
    # Record some test metrics
    record_latency("fx_live_latency_ms", 42.5)
    record_latency("vendor_a_latency_ms", 100.0)
    record_latency("planning_duration_ms", 250.0)
    record_cache_hit()
    record_cache_miss()
    
    response = client.get("/metrics")
    text = response.text
    
    # Check that all expected metrics are present
    assert "fx_live_latency_ms" in text
    assert "vendor_a_latency_ms" in text
    assert "planning_duration_ms" in text
    assert "cache_hit_ratio" in text
    
    # Verify that numeric values are present
    assert "42.5" in text
    assert "100.0" in text
    assert "250.0" in text
    assert "0.5" in text  # cache hit ratio should be 0.5 (1 hit, 1 miss)


def test_metrics_endpoint_empty(client):
    """Test metrics endpoint with no recorded data"""
    response = client.get("/metrics")
    text = response.text
    
    # Should still return valid Prometheus format
    assert response.status_code == 200
    assert "# TYPE cache_hit_ratio gauge" in text
    assert "cache_hit_ratio 0.000000" in text
