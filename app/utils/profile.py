"""
User profile management for personalization features.

Provides simple in-memory and file-based user profile storage.
"""

import json
from pathlib import Path
from typing import Optional


class UserProfile:
    """User profile for personalization"""
    
    def __init__(
        self,
        home_city: str = "Berlin",
        preferred_currency: str = "EUR",
        max_distance_km: float = 2000.0,
        preferred_cuisines: Optional[list[str]] = None
    ):
        self.home_city = home_city
        self.preferred_currency = preferred_currency
        self.max_distance_km = max_distance_km
        self.preferred_cuisines = preferred_cuisines or []
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary"""
        return {
            "home_city": self.home_city,
            "preferred_currency": self.preferred_currency,
            "max_distance_km": self.max_distance_km,
            "preferred_cuisines": self.preferred_cuisines
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create profile from dictionary"""
        return cls(
            home_city=data.get("home_city", "Berlin"),
            preferred_currency=data.get("preferred_currency", "EUR"),
            max_distance_km=data.get("max_distance_km", 2000.0),
            preferred_cuisines=data.get("preferred_cuisines", [])
        )


class ProfileManager:
    """Manages user profile storage and retrieval"""
    
    def __init__(self, profile_path: Optional[Path] = None):
        """
        Initialize profile manager.
        
        Args:
            profile_path: Path to profile JSON file. 
                         Defaults to ~/.weekend_profile.json
        """
        if profile_path is None:
            profile_path = Path.home() / ".weekend_profile.json"
        self.profile_path = profile_path
        self._profile: Optional[UserProfile] = None
    
    def load(self) -> UserProfile:
        """
        Load user profile from disk or return default.
        
        Returns:
            UserProfile instance
        """
        if self._profile is not None:
            return self._profile
        
        if self.profile_path.exists():
            try:
                data = json.loads(self.profile_path.read_text())
                self._profile = UserProfile.from_dict(data)
                return self._profile
            except (json.JSONDecodeError, KeyError):
                # Corrupted profile, use defaults
                pass
        
        # Return default profile
        self._profile = UserProfile()
        return self._profile
    
    def save(self, profile: UserProfile) -> None:
        """
        Save user profile to disk.
        
        Args:
            profile: UserProfile to save
        """
        self._profile = profile
        self.profile_path.write_text(json.dumps(profile.to_dict(), indent=2))
    
    def update(self, **kwargs) -> UserProfile:
        """
        Update profile fields and save.
        
        Args:
            **kwargs: Fields to update
        
        Returns:
            Updated UserProfile
        """
        profile = self.load()
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        self.save(profile)
        return profile


# Global profile manager instance
_profile_manager = ProfileManager()


def get_profile_manager() -> ProfileManager:
    """Get the global profile manager instance"""
    return _profile_manager
