"""
Weather connector using Open-Meteo API.

Open-Meteo is a free weather API that doesn't require an API key.
"""

import httpx
from typing import Optional
from ..utils.cache import get_cache

WEATHER_CACHE_TTL = 7200  # 2 hours

# City coordinates lookup (stub - in production would use geocoding API)
CITY_COORDS = {
    "lisbon": {"lat": 38.709, "lng": -9.133},
    "berlin": {"lat": 52.52, "lng": 13.405},
    "paris": {"lat": 48.8566, "lng": 2.3522},
    "london": {"lat": 51.5074, "lng": -0.1278},
    "madrid": {"lat": 40.4168, "lng": -3.7038},
    "rome": {"lat": 41.9028, "lng": 12.4964},
    "amsterdam": {"lat": 52.3676, "lng": 4.9041},
}


async def get_weather(lat: float, lng: float, offline_mode: bool = False) -> Optional[dict]:
    """
    Fetch weather forecast for given coordinates.
    
    Args:
        lat: Latitude
        lng: Longitude
        offline_mode: If True, only use cached data without HTTP calls
    
    Returns:
        Weather dict with desc, temp_c, temp_min, temp_max
        None if fetch fails
    """
    cache = get_cache()
    cache_key = f"weather_{lat:.2f}_{lng:.2f}"
    
    # Try cache first
    cached = cache.get(cache_key, WEATHER_CACHE_TTL, ignore_ttl=offline_mode)
    if cached:
        return cached
    
    # In offline mode, don't make HTTP calls
    if offline_mode:
        return None
    
    # Fetch from Open-Meteo
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract current weather
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            # Map weather codes to descriptions (simplified)
            weather_code = current.get("weather_code", 0)
            desc = _weather_code_to_desc(weather_code)
            
            result = {
                "desc": desc,
                "temp_c": round(current.get("temperature_2m", 15.0), 1),
                "temp_min": round(daily.get("temperature_2m_min", [15])[0], 1) if daily.get("temperature_2m_min") else None,
                "temp_max": round(daily.get("temperature_2m_max", [20])[0], 1) if daily.get("temperature_2m_max") else None,
            }
            
            # Cache the result
            cache.set(cache_key, result)
            return result
    
    except (httpx.HTTPError, KeyError, ValueError):
        # Return None on error (weather is optional)
        return None


async def get_weather_by_city(city_name: str, offline_mode: bool = False) -> Optional[dict]:
    """
    Fetch weather for a city by name.
    
    Args:
        city_name: City name (e.g., "Lisbon", "Berlin")
        offline_mode: If True, only use cached data without HTTP calls
    
    Returns:
        Weather dict or None if city not found or fetch fails
    """
    city_lower = city_name.lower()
    coords = CITY_COORDS.get(city_lower)
    
    if not coords:
        return None
    
    return await get_weather(coords["lat"], coords["lng"], offline_mode=offline_mode)


def _weather_code_to_desc(code: int) -> str:
    """
    Convert WMO weather code to human-readable description.
    
    WMO Weather interpretation codes (simplified):
    0: Clear sky
    1-3: Partly cloudy
    45-48: Fog
    51-67: Rain
    71-86: Snow
    95-99: Thunderstorm
    """
    if code == 0:
        return "Clear"
    elif 1 <= code <= 3:
        return "Partly Cloudy"
    elif 45 <= code <= 48:
        return "Foggy"
    elif 51 <= code <= 67:
        return "Rainy"
    elif 71 <= code <= 86:
        return "Snowy"
    elif 95 <= code <= 99:
        return "Stormy"
    else:
        return "Cloudy"
