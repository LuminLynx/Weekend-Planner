
# Stub dining: replace with OpenTable/Places later.
from ..utils.cache import get_cache

DINING_CACHE_TTL = 900  # 15 minutes

async def search_dining(query: str) -> list[dict]:
    """
    Search for dining options by query string.
    
    Args:
        query: Search query (e.g., "italian near Lisbon")
    
    Returns:
        List of dining options with name, est_pp, distance_m, booking_url
    """
    cache = get_cache()
    cache_key = f"dining_search_{query}"
    
    # Try cache first
    cached = cache.get(cache_key, DINING_CACHE_TTL)
    if cached:
        return cached
    
    # Stub data (would be live API call in production)
    results = [
        {
            "name": f"Restaurant for {query}",
            "est_pp": 25.0,
            "distance_m": 300,
            "booking_url": "https://opentable.example/book/123"
        }
    ]
    
    # Cache results
    cache.set(cache_key, results)
    return results

async def get_nearby(venue: dict) -> tuple[list[dict], bool]:
    """
    Get nearby dining options.
    
    Returns:
        (results, cache_hit)
    """
    cache = get_cache()
    cache_key = f"dining_{venue['lat']}_{venue['lng']}"
    
    # Try cache first
    cached = cache.get(cache_key, DINING_CACHE_TTL)
    if cached:
        return cached, True
    
    # Stub data (would be live API call)
    results = [
        {"name": "Taberna X", "price_tier": "€€", "est_pp": 18.0, "distance_m": 450, "booking_url": "https://..."}
    ]
    
    # Cache results
    cache.set(cache_key, results)
    return results, False
