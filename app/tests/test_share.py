"""
Tests for itinerary sharing functionality.
"""

import json
import tempfile
from pathlib import Path
import pytest
from app.utils.share import ShareManager, generate_html_view


@pytest.fixture
def temp_share_dir():
    """Create temporary directory for share tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_save_plan(temp_share_dir):
    """Test saving a plan"""
    manager = ShareManager(temp_share_dir)
    
    plan_data = {
        "itineraries": [
            {
                "event_title": "Test Event",
                "score": 0.8
            }
        ]
    }
    
    plan_id = manager.save_plan(plan_data)
    
    assert plan_id is not None
    assert len(plan_id) == 36  # UUID length
    
    # Verify file was created
    plan_file = temp_share_dir / f"{plan_id}.json"
    assert plan_file.exists()


def test_get_plan(temp_share_dir):
    """Test retrieving a saved plan"""
    manager = ShareManager(temp_share_dir)
    
    plan_data = {
        "itineraries": [
            {
                "event_title": "Test Event",
                "score": 0.8
            }
        ]
    }
    
    plan_id = manager.save_plan(plan_data)
    retrieved = manager.get_plan(plan_id)
    
    assert retrieved is not None
    assert "plan_id" in retrieved
    assert "created_at" in retrieved
    assert "data" in retrieved
    assert retrieved["data"] == plan_data


def test_get_nonexistent_plan(temp_share_dir):
    """Test retrieving a plan that doesn't exist"""
    manager = ShareManager(temp_share_dir)
    
    retrieved = manager.get_plan("nonexistent-uuid")
    assert retrieved is None


def test_list_plans_empty(temp_share_dir):
    """Test listing plans when none exist"""
    manager = ShareManager(temp_share_dir)
    
    plans = manager.list_plans()
    assert plans == []


def test_list_plans_with_data(temp_share_dir):
    """Test listing saved plans"""
    manager = ShareManager(temp_share_dir)
    
    # Save multiple plans
    plan1 = manager.save_plan({"itineraries": [{"title": "Plan 1"}]})
    plan2 = manager.save_plan({"itineraries": [{"title": "Plan 2"}]})
    
    plans = manager.list_plans()
    
    assert len(plans) == 2
    plan_ids = [p["plan_id"] for p in plans]
    assert plan1 in plan_ids
    assert plan2 in plan_ids
    
    # Verify each plan has created_at
    for plan in plans:
        assert "created_at" in plan


def test_delete_plan(temp_share_dir):
    """Test deleting a plan"""
    manager = ShareManager(temp_share_dir)
    
    plan_data = {"itineraries": [{"title": "Test"}]}
    plan_id = manager.save_plan(plan_data)
    
    # Verify it exists
    assert manager.get_plan(plan_id) is not None
    
    # Delete it
    result = manager.delete_plan(plan_id)
    assert result is True
    
    # Verify it's gone
    assert manager.get_plan(plan_id) is None


def test_delete_nonexistent_plan(temp_share_dir):
    """Test deleting a plan that doesn't exist"""
    manager = ShareManager(temp_share_dir)
    
    result = manager.delete_plan("nonexistent-uuid")
    assert result is False


def test_save_plan_creates_directory():
    """Test that save_plan creates directory if it doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        share_dir = Path(tmpdir) / "nonexistent" / "shared"
        manager = ShareManager(share_dir)
        
        plan_data = {"itineraries": []}
        plan_id = manager.save_plan(plan_data)
        
        assert share_dir.exists()
        assert (share_dir / f"{plan_id}.json").exists()


def test_generate_html_view():
    """Test HTML generation for shared plans"""
    plan_data = {
        "plan_id": "test-123",
        "created_at": "2025-11-05T10:00:00Z",
        "data": {
            "itineraries": [
                {
                    "event_title": "Concert",
                    "start_ts": "2025-11-10T20:00:00Z",
                    "score": 0.85,
                    "best_price": {
                        "landed": {"amount": 50, "currency": "EUR"},
                        "provider": "vendor_a"
                    },
                    "weather": {"desc": "Clear", "temp_c": 18},
                    "travel": {"distance_km": 500, "co2_kg_pp": 75},
                    "rationale": "Great option!"
                }
            ]
        }
    }
    
    html = generate_html_view(plan_data, "test-123")
    
    assert "test-123" in html
    assert "Concert" in html
    assert "50 EUR" in html
    assert "Clear" in html
    assert "500 km" in html
    assert "75 kg CO₂" in html
    assert "Great option!" in html


def test_generate_html_view_empty():
    """Test HTML generation with no itineraries"""
    plan_data = {
        "plan_id": "empty-123",
        "created_at": "2025-11-05T10:00:00Z",
        "data": {
            "itineraries": []
        }
    }
    
    html = generate_html_view(plan_data, "empty-123")
    
    assert "empty-123" in html
    assert "Weekend Planner" in html


def test_plan_persistence(temp_share_dir):
    """Test that saved plans persist across manager instances"""
    # Save with first manager
    manager1 = ShareManager(temp_share_dir)
    plan_data = {"itineraries": [{"title": "Persistent Plan"}]}
    plan_id = manager1.save_plan(plan_data)
    
    # Retrieve with second manager
    manager2 = ShareManager(temp_share_dir)
    retrieved = manager2.get_plan(plan_id)
    
    assert retrieved is not None
    assert retrieved["data"] == plan_data
