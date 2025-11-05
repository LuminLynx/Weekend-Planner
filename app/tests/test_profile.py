"""
Tests for user profile management.
"""

import json
from pathlib import Path
import tempfile
import pytest
from app.utils.profile import UserProfile, ProfileManager


def test_user_profile_defaults():
    """Test default user profile creation"""
    profile = UserProfile()
    assert profile.home_city == "Berlin"
    assert profile.preferred_currency == "EUR"
    assert profile.max_distance_km == 2000.0
    assert profile.preferred_cuisines == []


def test_user_profile_custom():
    """Test custom user profile creation"""
    profile = UserProfile(
        home_city="Paris",
        preferred_currency="USD",
        max_distance_km=1500.0,
        preferred_cuisines=["Italian", "French"]
    )
    assert profile.home_city == "Paris"
    assert profile.preferred_currency == "USD"
    assert profile.max_distance_km == 1500.0
    assert profile.preferred_cuisines == ["Italian", "French"]


def test_user_profile_to_dict():
    """Test profile serialization to dict"""
    profile = UserProfile(
        home_city="London",
        preferred_cuisines=["Japanese"]
    )
    data = profile.to_dict()
    assert data["home_city"] == "London"
    assert data["preferred_currency"] == "EUR"
    assert data["preferred_cuisines"] == ["Japanese"]


def test_user_profile_from_dict():
    """Test profile deserialization from dict"""
    data = {
        "home_city": "Madrid",
        "preferred_currency": "EUR",
        "max_distance_km": 1000.0,
        "preferred_cuisines": ["Spanish", "Mediterranean"]
    }
    profile = UserProfile.from_dict(data)
    assert profile.home_city == "Madrid"
    assert profile.max_distance_km == 1000.0
    assert profile.preferred_cuisines == ["Spanish", "Mediterranean"]


def test_profile_manager_save_load():
    """Test saving and loading profiles"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)
    
    try:
        manager = ProfileManager(temp_path)
        
        # Save profile
        profile = UserProfile(home_city="Amsterdam", preferred_cuisines=["Dutch"])
        manager.save(profile)
        
        # Load profile
        loaded = manager.load()
        assert loaded.home_city == "Amsterdam"
        assert loaded.preferred_cuisines == ["Dutch"]
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_profile_manager_update():
    """Test updating profile fields"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)
    
    try:
        manager = ProfileManager(temp_path)
        
        # Update fields
        profile = manager.update(
            home_city="Rome",
            preferred_cuisines=["Italian", "Pizza"]
        )
        
        assert profile.home_city == "Rome"
        assert profile.preferred_cuisines == ["Italian", "Pizza"]
        
        # Load again to verify persistence
        loaded = manager.load()
        assert loaded.home_city == "Rome"
        assert loaded.preferred_cuisines == ["Italian", "Pizza"]
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_profile_manager_missing_file():
    """Test loading when profile file doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "nonexistent.json"
        manager = ProfileManager(temp_path)
        
        # Should return defaults
        profile = manager.load()
        assert profile.home_city == "Berlin"
        assert profile.preferred_currency == "EUR"


def test_profile_manager_corrupted_file():
    """Test loading corrupted profile file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)
    
    try:
        manager = ProfileManager(temp_path)
        
        # Should return defaults on corrupted file
        profile = manager.load()
        assert profile.home_city == "Berlin"
    finally:
        if temp_path.exists():
            temp_path.unlink()
