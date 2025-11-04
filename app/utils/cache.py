
import json
import time
from pathlib import Path
from typing import Optional, Any, Callable
from datetime import datetime, timezone

class SimpleCache:
    """Simple file-based cache with TTL support"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _cache_path(self, key: str) -> Path:
        """Get cache file path for a key"""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        """
        Get cached value if it exists and is not expired.
        
        Args:
            key: Cache key
            ttl_seconds: Time to live in seconds
            
        Returns:
            Cached value or None if expired/missing
        """
        cache_file = self._cache_path(key)
        if not cache_file.exists():
            return None
        
        try:
            data = json.loads(cache_file.read_text())
            cached_time = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now(timezone.utc) - cached_time).total_seconds()
            
            if age < ttl_seconds:
                return data["value"]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Corrupted cache file, ignore and return None
            pass
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set cached value with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
        """
        cache_file = self._cache_path(key)
        data = {
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        cache_file.write_text(json.dumps(data))
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache entry or entire cache.
        
        Args:
            key: If provided, clear only this key. Otherwise clear all.
        """
        if key:
            cache_file = self._cache_path(key)
            if cache_file.exists():
                cache_file.unlink()
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()


# Global cache instance
_cache = SimpleCache()

def get_cache() -> SimpleCache:
    """Get the global cache instance"""
    return _cache
