"""Tests for metrics collection and export."""
import pytest
from app.utils.metrics import MetricsCollector, get_metrics_collector, record_latency, record_cache_hit, record_cache_miss


def test_metrics_collector_latency():
    """Test recording and retrieving latency metrics."""
    collector = MetricsCollector()
    
    collector.record_latency("test_metric", 100.5)
    collector.record_latency("test_metric", 200.5)
    
    metrics = collector.get_metrics()
    assert "test_metric" in metrics
    assert metrics["test_metric"] == 150.5  # Average of 100.5 and 200.5


def test_metrics_collector_cache_ratio():
    """Test cache hit ratio calculation."""
    collector = MetricsCollector()
    
    collector.record_cache_hit()
    collector.record_cache_hit()
    collector.record_cache_hit()
    collector.record_cache_miss()
    
    metrics = collector.get_metrics()
    assert "cache_hit_ratio" in metrics
    assert metrics["cache_hit_ratio"] == 0.75  # 3 hits out of 4 total


def test_metrics_collector_no_data():
    """Test metrics with no recorded data."""
    collector = MetricsCollector()
    
    metrics = collector.get_metrics()
    assert metrics["cache_hit_ratio"] == 0.0


def test_metrics_collector_prometheus_export():
    """Test Prometheus format export."""
    collector = MetricsCollector()
    
    collector.record_latency("fx_live_latency_ms", 50.0)
    collector.record_latency("vendor_a_latency_ms", 100.0)
    collector.record_cache_hit()
    collector.record_cache_miss()
    
    prometheus_text = collector.export_prometheus()
    
    # Check that the output contains the expected metrics
    assert "# TYPE cache_hit_ratio gauge" in prometheus_text
    assert "cache_hit_ratio 0.500000" in prometheus_text
    assert "# TYPE fx_live_latency_ms gauge" in prometheus_text
    assert "fx_live_latency_ms 50.000000" in prometheus_text
    assert "# TYPE vendor_a_latency_ms gauge" in prometheus_text
    assert "vendor_a_latency_ms 100.000000" in prometheus_text


def test_metrics_collector_reset():
    """Test resetting metrics."""
    collector = MetricsCollector()
    
    collector.record_latency("test_metric", 100.0)
    collector.record_cache_hit()
    
    collector.reset()
    
    metrics = collector.get_metrics()
    assert metrics["cache_hit_ratio"] == 0.0
    assert "test_metric" not in metrics or metrics["test_metric"] == 0.0


def test_global_metrics_collector():
    """Test the global metrics collector functions."""
    # Reset the global collector first
    collector = get_metrics_collector()
    collector.reset()
    
    record_latency("planning_duration_ms", 500.0)
    record_cache_hit()
    record_cache_miss()
    
    metrics = collector.get_metrics()
    assert "planning_duration_ms" in metrics
    assert metrics["planning_duration_ms"] == 500.0
    assert metrics["cache_hit_ratio"] == 0.5
    
    # Clean up
    collector.reset()


def test_multiple_latency_recordings():
    """Test that multiple recordings are averaged correctly."""
    collector = MetricsCollector()
    
    for i in range(10):
        collector.record_latency("test_metric", float(i * 10))
    
    metrics = collector.get_metrics()
    assert metrics["test_metric"] == 45.0  # Average of 0, 10, 20, ..., 90
