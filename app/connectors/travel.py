"""
Travel distance and carbon footprint calculations.

Provides distance estimation and CO2 emissions calculations for trips.
"""

import math
from typing import Optional


# City coordinates for distance calculations (same as weather)
CITY_COORDS = {
    "lisbon": {"lat": 38.709, "lng": -9.133},
    "berlin": {"lat": 52.52, "lng": 13.405},
    "paris": {"lat": 48.8566, "lng": 2.3522},
    "london": {"lat": 51.5074, "lng": -0.1278},
    "madrid": {"lat": 40.4168, "lng": -3.7038},
    "rome": {"lat": 41.9028, "lng": 12.4964},
    "amsterdam": {"lat": 52.3676, "lng": 4.9041},
}

# CO2 emission factors (kg CO2 per km per person)
CO2_FACTORS = {
    "air": 0.15,      # Average flight emissions
    "rail": 0.04,     # Train emissions (electric)
    "car": 0.12,      # Average car emissions
    "bus": 0.06,      # Bus emissions
}


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using the Haversine formula.
    
    Args:
        lat1, lng1: Coordinates of first point
        lat2, lng2: Coordinates of second point
    
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 1)


def get_city_coords(city_name: str) -> Optional[dict]:
    """
    Get coordinates for a city by name.
    
    Args:
        city_name: City name (case-insensitive)
    
    Returns:
        Dict with lat, lng or None if city not found
    """
    return CITY_COORDS.get(city_name.lower())


def calculate_distance(from_city: str, to_city: str) -> Optional[float]:
    """
    Calculate distance between two cities.
    
    Args:
        from_city: Origin city name
        to_city: Destination city name
    
    Returns:
        Distance in km or None if cities not found
    """
    from_coords = get_city_coords(from_city)
    to_coords = get_city_coords(to_city)
    
    if not from_coords or not to_coords:
        return None
    
    return haversine_distance(
        from_coords["lat"], from_coords["lng"],
        to_coords["lat"], to_coords["lng"]
    )


def calculate_co2(distance_km: float, transport_mode: str = "air") -> float:
    """
    Calculate CO2 emissions for a trip.
    
    Args:
        distance_km: Distance in kilometers
        transport_mode: Transport mode (air, rail, car, bus)
    
    Returns:
        CO2 emissions in kg per person
    """
    factor = CO2_FACTORS.get(transport_mode, CO2_FACTORS["air"])
    return round(distance_km * factor, 2)


def estimate_transport_mode(distance_km: float) -> str:
    """
    Estimate likely transport mode based on distance.
    
    Args:
        distance_km: Distance in kilometers
    
    Returns:
        Estimated transport mode (air, rail, car, bus)
    """
    if distance_km > 1000:
        return "air"
    elif distance_km > 300:
        return "rail"
    elif distance_km > 100:
        return "car"
    else:
        return "rail"


def get_travel_info(from_city: str, to_city: str) -> Optional[dict]:
    """
    Get complete travel information between two cities.
    
    Args:
        from_city: Origin city name
        to_city: Destination city name
    
    Returns:
        Dict with distance_km, transport_mode, co2_kg_pp or None if cities not found
    """
    distance = calculate_distance(from_city, to_city)
    
    if distance is None:
        return None
    
    transport_mode = estimate_transport_mode(distance)
    co2 = calculate_co2(distance, transport_mode)
    
    return {
        "distance_km": distance,
        "transport_mode": transport_mode,
        "co2_kg_pp": co2
    }
