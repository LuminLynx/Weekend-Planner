"""
Itinerary sharing functionality.

Allows sharing planned weekends via unique links and static snapshots.
"""

import json
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone


class ShareManager:
    """Manages sharing of itineraries"""
    
    def __init__(self, shared_dir: Optional[Path] = None):
        """
        Initialize share manager.
        
        Args:
            shared_dir: Directory to store shared plans.
                       Defaults to .cache/shared/
        """
        if shared_dir is None:
            shared_dir = Path(".cache/shared")
        self.shared_dir = shared_dir
        self.shared_dir.mkdir(parents=True, exist_ok=True)
    
    def save_plan(self, plan_data: dict) -> str:
        """
        Save a plan and return its share ID.
        
        Args:
            plan_data: Plan data to save (itineraries dict)
        
        Returns:
            Share ID (UUID)
        """
        plan_id = str(uuid.uuid4())
        
        # Add metadata
        plan_with_metadata = {
            "plan_id": plan_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": plan_data
        }
        
        # Save to file
        plan_file = self.shared_dir / f"{plan_id}.json"
        plan_file.write_text(json.dumps(plan_with_metadata, indent=2))
        
        return plan_id
    
    def get_plan(self, plan_id: str) -> Optional[dict]:
        """
        Retrieve a shared plan by ID.
        
        Args:
            plan_id: Share ID
        
        Returns:
            Plan data dict or None if not found
        """
        plan_file = self.shared_dir / f"{plan_id}.json"
        
        if not plan_file.exists():
            return None
        
        try:
            data = json.loads(plan_file.read_text())
            return data
        except (json.JSONDecodeError, KeyError):
            return None
    
    def list_plans(self) -> list[dict]:
        """
        List all shared plans.
        
        Returns:
            List of plan metadata (plan_id, created_at)
        """
        plans = []
        for plan_file in self.shared_dir.glob("*.json"):
            try:
                data = json.loads(plan_file.read_text())
                plans.append({
                    "plan_id": data.get("plan_id"),
                    "created_at": data.get("created_at")
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        return sorted(plans, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def delete_plan(self, plan_id: str) -> bool:
        """
        Delete a shared plan.
        
        Args:
            plan_id: Share ID
        
        Returns:
            True if deleted, False if not found
        """
        plan_file = self.shared_dir / f"{plan_id}.json"
        
        if not plan_file.exists():
            return False
        
        plan_file.unlink()
        return True


# Global share manager instance
_share_manager = ShareManager()


def get_share_manager() -> ShareManager:
    """Get the global share manager instance"""
    return _share_manager


def generate_html_view(plan_data: dict, plan_id: str) -> str:
    """
    Generate HTML view for a shared plan.
    
    Args:
        plan_data: Plan data with itineraries
        plan_id: Share ID
    
    Returns:
        HTML string
    """
    itineraries = plan_data.get("data", {}).get("itineraries", [])
    created_at = plan_data.get("created_at", "")
    
    # Build itinerary HTML
    itinerary_html = ""
    for idx, item in enumerate(itineraries, 1):
        event_title = item.get("event_title", "Event")
        start_ts = item.get("start_ts", "")
        score = item.get("score", 0)
        
        best_price = item.get("best_price", {})
        landed = best_price.get("landed", {})
        amount = landed.get("amount", 0)
        currency = landed.get("currency", "EUR")
        provider = best_price.get("provider", "")
        
        weather = item.get("weather", {})
        weather_desc = weather.get("desc", "N/A") if weather else "N/A"
        temp_c = weather.get("temp_c", "N/A") if weather else "N/A"
        
        travel = item.get("travel", {})
        distance_km = travel.get("distance_km", "N/A") if travel else "N/A"
        co2_kg_pp = travel.get("co2_kg_pp", "N/A") if travel else "N/A"
        
        meal_bundle = item.get("meal_bundle", {})
        dining = meal_bundle.get("chosen", {}) if meal_bundle else {}
        dining_name = dining.get("name", "None") if dining else "None"
        
        rationale = item.get("rationale", "")
        
        itinerary_html += f"""
        <div class="card">
            <h3>Option {idx}: {event_title}</h3>
            <p><strong>Date:</strong> {start_ts}</p>
            <p><strong>Price:</strong> {amount} {currency} (Provider: {provider})</p>
            <p><strong>Weather:</strong> {weather_desc}, {temp_c}°C</p>
            <p><strong>Travel:</strong> {distance_km} km, {co2_kg_pp} kg CO₂</p>
            <p><strong>Dining:</strong> {dining_name}</p>
            <p><strong>Score:</strong> {score}</p>
            <div class="rationale">{rationale}</div>
        </div>
        """
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Shared Weekend Plan - {plan_id}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin-top: 0;
            color: #007bff;
        }}
        .rationale {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #007bff;
            margin-top: 15px;
            font-style: italic;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>🗓️ Weekend Planner - Shared Itinerary</h1>
    <div class="meta">
        <p><strong>Plan ID:</strong> {plan_id}</p>
        <p><strong>Created:</strong> {created_at}</p>
    </div>
    
    {itinerary_html}
    
    <div class="footer">
        <p>Powered by Weekend Planner | <a href="/">Create your own plan</a></p>
    </div>
</body>
</html>
    """
    
    return html
