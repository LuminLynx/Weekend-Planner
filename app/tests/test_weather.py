"""
Tests for weather connector.
"""

import pytest
from app.connectors.weather import _weather_code_to_desc, CITY_COORDS


def test_weather_code_to_desc_clear():
    """Test clear sky weather code"""
    assert _weather_code_to_desc(0) == "Clear"


def test_weather_code_to_desc_partly_cloudy():
    """Test partly cloudy weather codes"""
    assert _weather_code_to_desc(1) == "Partly Cloudy"
    assert _weather_code_to_desc(2) == "Partly Cloudy"
    assert _weather_code_to_desc(3) == "Partly Cloudy"


def test_weather_code_to_desc_fog():
    """Test foggy weather codes"""
    assert _weather_code_to_desc(45) == "Foggy"
    assert _weather_code_to_desc(48) == "Foggy"


def test_weather_code_to_desc_rain():
    """Test rainy weather codes"""
    assert _weather_code_to_desc(51) == "Rainy"
    assert _weather_code_to_desc(61) == "Rainy"
    assert _weather_code_to_desc(67) == "Rainy"


def test_weather_code_to_desc_snow():
    """Test snowy weather codes"""
    assert _weather_code_to_desc(71) == "Snowy"
    assert _weather_code_to_desc(75) == "Snowy"
    assert _weather_code_to_desc(86) == "Snowy"


def test_weather_code_to_desc_storm():
    """Test stormy weather codes"""
    assert _weather_code_to_desc(95) == "Stormy"
    assert _weather_code_to_desc(99) == "Stormy"


def test_weather_code_to_desc_unknown():
    """Test unknown weather codes default to Cloudy"""
    assert _weather_code_to_desc(100) == "Cloudy"
    assert _weather_code_to_desc(4) == "Cloudy"


def test_city_coords_contains_expected_cities():
    """Test that city coordinates database contains expected cities"""
    assert "lisbon" in CITY_COORDS
    assert "berlin" in CITY_COORDS
    assert "paris" in CITY_COORDS
    assert "london" in CITY_COORDS
    
    # Verify coordinates format
    lisbon = CITY_COORDS["lisbon"]
    assert "lat" in lisbon
    assert "lng" in lisbon
    assert isinstance(lisbon["lat"], (int, float))
    assert isinstance(lisbon["lng"], (int, float))
