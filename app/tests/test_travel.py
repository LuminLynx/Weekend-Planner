"""
Tests for travel distance and carbon calculations.
"""

import pytest
from app.connectors.travel import (
    haversine_distance,
    calculate_distance,
    calculate_co2,
    estimate_transport_mode,
    get_travel_info,
    get_city_coords
)


def test_haversine_distance_same_point():
    """Test distance between same point is 0"""
    distance = haversine_distance(38.709, -9.133, 38.709, -9.133)
    assert distance == 0.0


def test_haversine_distance_known_cities():
    """Test distance between known cities"""
    # Lisbon to Paris (approximately 1450 km)
    distance = haversine_distance(38.709, -9.133, 48.8566, 2.3522)
    assert 1400 < distance < 1500


def test_get_city_coords_valid():
    """Test getting coordinates for valid city"""
    coords = get_city_coords("Lisbon")
    assert coords is not None
    assert "lat" in coords
    assert "lng" in coords
    assert coords["lat"] == 38.709
    assert coords["lng"] == -9.133


def test_get_city_coords_case_insensitive():
    """Test city lookup is case-insensitive"""
    assert get_city_coords("LISBON") == get_city_coords("lisbon")
    assert get_city_coords("Berlin") == get_city_coords("berlin")


def test_get_city_coords_invalid():
    """Test getting coordinates for invalid city"""
    coords = get_city_coords("NonexistentCity")
    assert coords is None


def test_calculate_distance_valid_cities():
    """Test distance calculation between valid cities"""
    distance = calculate_distance("Berlin", "Paris")
    assert distance is not None
    assert 800 < distance < 1000  # Approximately 878 km


def test_calculate_distance_invalid_city():
    """Test distance calculation with invalid city"""
    distance = calculate_distance("Berlin", "NonexistentCity")
    assert distance is None


def test_calculate_co2_air():
    """Test CO2 calculation for air travel"""
    co2 = calculate_co2(1000, "air")
    assert co2 == 150.0  # 1000 km * 0.15 kg/km


def test_calculate_co2_rail():
    """Test CO2 calculation for rail travel"""
    co2 = calculate_co2(500, "rail")
    assert co2 == 20.0  # 500 km * 0.04 kg/km


def test_calculate_co2_car():
    """Test CO2 calculation for car travel"""
    co2 = calculate_co2(300, "car")
    assert co2 == 36.0  # 300 km * 0.12 kg/km


def test_calculate_co2_unknown_mode():
    """Test CO2 calculation with unknown transport mode defaults to air"""
    co2 = calculate_co2(1000, "unknown")
    assert co2 == 150.0  # Defaults to air


def test_estimate_transport_mode_air():
    """Test transport mode estimation for long distance"""
    mode = estimate_transport_mode(1500)
    assert mode == "air"


def test_estimate_transport_mode_rail_long():
    """Test transport mode estimation for medium-long distance"""
    mode = estimate_transport_mode(500)
    assert mode == "rail"


def test_estimate_transport_mode_car():
    """Test transport mode estimation for medium distance"""
    mode = estimate_transport_mode(200)
    assert mode == "car"


def test_estimate_transport_mode_rail_short():
    """Test transport mode estimation for short distance"""
    mode = estimate_transport_mode(50)
    assert mode == "rail"


def test_get_travel_info_valid():
    """Test getting complete travel info for valid cities"""
    info = get_travel_info("Berlin", "Lisbon")
    assert info is not None
    assert "distance_km" in info
    assert "transport_mode" in info
    assert "co2_kg_pp" in info
    assert info["distance_km"] > 0
    assert info["transport_mode"] == "air"  # Long distance
    assert info["co2_kg_pp"] > 0


def test_get_travel_info_short_distance():
    """Test travel info for shorter distance"""
    info = get_travel_info("Berlin", "Amsterdam")
    assert info is not None
    # Berlin to Amsterdam is about 580 km, should use rail
    assert info["transport_mode"] in ["rail", "car"]


def test_get_travel_info_invalid():
    """Test travel info with invalid city"""
    info = get_travel_info("Berlin", "NonexistentCity")
    assert info is None


def test_get_travel_info_consistency():
    """Test that travel info components are consistent"""
    info = get_travel_info("Paris", "Berlin")
    assert info is not None
    
    # Recalculate CO2 to verify consistency
    expected_co2 = calculate_co2(info["distance_km"], info["transport_mode"])
    assert info["co2_kg_pp"] == expected_co2
