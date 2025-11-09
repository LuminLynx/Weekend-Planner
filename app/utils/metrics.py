"""Metrics collection and Prometheus-style export for observability."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Dict, List


class MetricsCollector:
    """Thread-safe metrics collector for recording latency and cache hits."""
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._cache_hits = 0
        self._cache_misses = 0
    
    def record_latency(self, metric_name: str, duration_ms: float) -> None:
        """Record a latency measurement in milliseconds."""
        with self._lock:
            self._latencies[metric_name].append(duration_ms)
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._cache_misses += 1
    
    def get_metrics(self) -> Dict[str, float]:
        """Get current metrics as a dictionary."""
        with self._lock:
            metrics = {}
            
            # Calculate average latencies for each metric
            for metric_name, latencies in self._latencies.items():
                if latencies:
                    metrics[metric_name] = sum(latencies) / len(latencies)
                else:
                    metrics[metric_name] = 0.0
            
            # Calculate cache hit ratio
            total_cache_ops = self._cache_hits + self._cache_misses
            if total_cache_ops > 0:
                metrics["cache_hit_ratio"] = self._cache_hits / total_cache_ops
            else:
                metrics["cache_hit_ratio"] = 0.0
            
            return metrics
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        metrics = self.get_metrics()
        lines = []
        
        for metric_name, value in sorted(metrics.items()):
            # Add metric type hint (gauge for all our metrics)
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{metric_name} {value:.6f}")
        
        return "\n".join(lines) + "\n"
    
    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._latencies.clear()
            self._cache_hits = 0
            self._cache_misses = 0


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def record_latency(metric_name: str, duration_ms: float) -> None:
    """Record a latency measurement to the global collector."""
    _metrics_collector.record_latency(metric_name, duration_ms)


def record_cache_hit() -> None:
    """Record a cache hit to the global collector."""
    _metrics_collector.record_cache_hit()


def record_cache_miss() -> None:
    """Record a cache miss to the global collector."""
    _metrics_collector.record_cache_miss()


def get_metrics() -> Dict[str, float]:
    """Get current metrics from the global collector."""
    return _metrics_collector.get_metrics()


def export_prometheus() -> str:
    """Export metrics in Prometheus text format from the global collector."""
    return _metrics_collector.export_prometheus()
