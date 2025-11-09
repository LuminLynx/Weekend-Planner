"""
Tests for share endpoints in the server.
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
from pathlib import Path
from app.server import app
from app.utils.share import get_share_manager


@pytest.fixture(autouse=True)
def setup_temp_share_dir():
    """Setup temporary share directory for all tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        share_manager = get_share_manager()
        original_dir = share_manager.shared_dir
        share_manager.shared_dir = Path(tmpdir)
        share_manager.shared_dir.mkdir(parents=True, exist_ok=True)
        yield
        share_manager.shared_dir = original_dir


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_create_share(client):
    """Test creating a shared plan via POST /share"""
    plan_data = {
        "itineraries": [
            {
                "event_title": "Test Concert",
                "start_ts": "2025-11-15T20:00:00Z",
                "score": 0.85,
                "best_price": {
                    "landed": {"amount": 50, "currency": "EUR"},
                    "provider": "vendor_a"
                }
            }
        ]
    }
    
    response = client.post("/share", json=plan_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "share_id" in data
    assert len(data["share_id"]) == 36  # UUID format


def test_get_share_html(client):
    """Test retrieving a shared plan as HTML via GET /share/{plan_id}"""
    # First create a share
    plan_data = {
        "itineraries": [
            {
                "event_title": "Test Event",
                "start_ts": "2025-11-15T20:00:00Z",
                "score": 0.9,
                "best_price": {
                    "landed": {"amount": 45, "currency": "EUR"},
                    "provider": "vendor_b"
                },
                "weather": {"desc": "Sunny", "temp_c": 22},
                "travel": {"distance_km": 300, "co2_kg_pp": 50},
                "rationale": "Great choice!"
            }
        ]
    }
    
    create_response = client.post("/share", json=plan_data)
    share_id = create_response.json()["share_id"]
    
    # Now retrieve it
    response = client.get(f"/share/{share_id}")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    
    html = response.text
    assert "Weekend Planner" in html
    assert "Test Event" in html
    assert share_id in html
    assert "45 EUR" in html
    assert "Sunny" in html
    assert "Great choice!" in html


def test_get_nonexistent_share(client):
    """Test retrieving a share that doesn't exist returns 404"""
    response = client.get("/share/nonexistent-uuid-12345")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_share_empty_itineraries(client):
    """Test creating a share with empty itineraries"""
    plan_data = {"itineraries": []}
    
    response = client.post("/share", json=plan_data)
    
    assert response.status_code == 200
    share_id = response.json()["share_id"]
    
    # Verify it can be retrieved
    get_response = client.get(f"/share/{share_id}")
    assert get_response.status_code == 200


def test_share_workflow_integration(client):
    """Test complete workflow: create share, retrieve it, verify content"""
    # Create a comprehensive plan
    plan_data = {
        "itineraries": [
            {
                "event_title": "Jazz Festival",
                "start_ts": "2025-12-01T19:00:00Z",
                "score": 0.92,
                "best_price": {
                    "landed": {"amount": 75, "currency": "EUR"},
                    "provider": "vendor_a",
                    "price_drop_prob_7d": 0.25,
                    "buy_now": True,
                    "buy_reason": "event_soon"
                },
                "weather": {"desc": "Clear", "temp_c": 18},
                "travel": {"distance_km": 450, "co2_kg_pp": 65},
                "meal_bundle": {
                    "chosen": {"name": "Italian Bistro", "est_pp": 20}
                },
                "rationale": "Excellent event with good weather!"
            },
            {
                "event_title": "Rock Concert",
                "start_ts": "2025-12-01T21:00:00Z",
                "score": 0.88,
                "best_price": {
                    "landed": {"amount": 60, "currency": "EUR"},
                    "provider": "vendor_b"
                }
            }
        ],
        "dining": [
            {"name": "Cafe Downtown", "est_pp": 15}
        ],
        "fx_used": {"EUR": 1.0, "USD": 1.08}
    }
    
    # Create share
    create_response = client.post("/share", json=plan_data)
    assert create_response.status_code == 200
    share_id = create_response.json()["share_id"]
    
    # Retrieve as HTML
    html_response = client.get(f"/share/{share_id}")
    assert html_response.status_code == 200
    
    html = html_response.text
    # Verify key content is present
    assert "Jazz Festival" in html
    assert "Rock Concert" in html
    assert "75 EUR" in html
    assert "60 EUR" in html
    assert "Italian Bistro" in html
    assert "Excellent event with good weather!" in html
    
    # Verify HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert "Weekend Planner" in html
    assert share_id in html
