
# Stub connector; replace with real API mapping later.
import httpx
import asyncio
import yaml
from pathlib import Path
from ..utils.cache import get_cache

# Circuit breaker state
_circuit_breaker = {
    "failures": 0,
    "last_failure_time": 0,
    "state": "closed"  # closed (normal), open (failing), half_open (testing)
}

CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_FAILURES = 3
CIRCUIT_OPEN_DURATION = 60  # seconds

def _should_allow_request() -> bool:
    """Check if circuit breaker allows request"""
    import time
    state = _circuit_breaker["state"]
    
    if state == "closed":
        return True
    
    if state == "open":
        # Check if we should transition to half_open
        if time.time() - _circuit_breaker["last_failure_time"] > CIRCUIT_OPEN_DURATION:
            _circuit_breaker["state"] = "half_open"
            return True
        return False
    
    # half_open state
    return True

def _record_success():
    """Record successful request"""
    _circuit_breaker["failures"] = 0
    _circuit_breaker["state"] = "closed"

def _record_failure():
    """Record failed request"""
    import time
    _circuit_breaker["failures"] += 1
    _circuit_breaker["last_failure_time"] = time.time()
    
    if _circuit_breaker["failures"] >= MAX_FAILURES:
        _circuit_breaker["state"] = "open"
        print(f"[VENDOR_A] Circuit breaker OPEN after {_circuit_breaker['failures']} failures", 
              file=__import__('sys').stderr)

async def get_offers(session, event_query: dict) -> list[dict]:
    """
    Get offers from Vendor A with authentication, pagination, caching, and circuit breaker.
    
    In production, this would:
    - Use API token from config
    - Handle pagination for large result sets
    - Parse real API responses through normalizers
    - Apply circuit breaker on 5xx errors or timeouts
    """
    cache = get_cache()
    cache_key = f"vendor_a_{event_query['title']}_{event_query['start_ts']}"
    
    # Try cache first
    cached = cache.get(cache_key, CACHE_TTL_SECONDS)
    if cached:
        return cached
    
    # Check circuit breaker
    if not _should_allow_request():
        print("[VENDOR_A] Circuit breaker OPEN, using cached/fallback data", 
              file=__import__('sys').stderr)
        # Return cached data even if expired, or empty list
        stale_cached = cache.get(cache_key, CACHE_TTL_SECONDS * 10)
        return stale_cached if stale_cached else []
    
    # In production, this would make a real API call:
    # try:
    #     config = yaml.safe_load(open("app/config/settings.example.yaml"))
    #     token = config["apis"]["vendors"]["vendor_a"]["token"]
    #     base_url = config["apis"]["vendors"]["vendor_a"]["base_url"]
    #     
    #     headers = {"Authorization": f"Bearer {token}"}
    #     all_results = []
    #     page = 1
    #     
    #     while True:
    #         response = await session.get(
    #             f"{base_url}/events/search",
    #             params={"query": event_query["title"], "page": page},
    #             headers=headers,
    #             timeout=10
    #         )
    #         response.raise_for_status()
    #         data = response.json()
    #         all_results.extend(normalize_vendor_a_response(data["results"]))
    #         
    #         if not data.get("has_more"):
    #             break
    #         page += 1
    #     
    #     _record_success()
    #     cache.set(cache_key, all_results)
    #     return all_results
    #     
    # except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
    #     if isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500:
    #         _record_failure()
    #     # Fallback to stale cache or empty
    #     stale_cached = cache.get(cache_key, CACHE_TTL_SECONDS * 10)
    #     return stale_cached if stale_cached else []
    
    # For now, return stub data
    try:
        # Simulate occasional failures for circuit breaker testing
        # In production, this would be real API call
        results = [
            {
                "provider": "a",
                "title": event_query["title"],
                "start_ts": event_query["start_ts"],
                "venue": {"lat": 38.709, "lng": -9.133, "address": "Lisbon"},
                "price": {"amount": 22.0, "currency": "EUR", "includes_vat": True},
                "fees": [{"type": "service", "amount": 2.5, "currency": "EUR"}],
                "vat_rate": 0.23,
                "promos": ["STUDENT10"],
                "inventory_hint": "med",
                "url": "https://vendor-a.example/tickets/abc",
                "source_id": "a-abc"
            }
        ]
        _record_success()
        cache.set(cache_key, results)
        return results
    except Exception as e:
        _record_failure()
        print(f"[VENDOR_A] Error: {e}", file=__import__('sys').stderr)
        # Return stale cache or empty
        stale_cached = cache.get(cache_key, CACHE_TTL_SECONDS * 10)
        return stale_cached if stale_cached else []
