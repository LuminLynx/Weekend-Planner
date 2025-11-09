"""Scoring utilities for itineraries."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from app.normalizers.price import PriceBreakdown


def _parse_iso8601(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def days_until(event_ts: str, reference: datetime | None = None) -> int:
    ref = reference or datetime.now(timezone.utc)
    event_dt = _parse_iso8601(event_ts)
    delta = event_dt - ref
    return max(int(delta.total_seconds() // 86400), 0)


def buy_now_heuristic(
    *,
    inventory_hint: str,
    days_to_event: int,
    price_variance: float,
    settings: Dict,
) -> tuple[bool, str]:
    threshold = settings.get("price_drop_days_threshold", 5)
    low_bonus = settings.get("price_drop_low_inventory_bonus", 0.2)
    high_penalty = settings.get("price_drop_high_inventory_penalty", -0.1)

    if days_to_event <= threshold:
        return True, f"Event happening soon (<= {threshold} days)"
    if inventory_hint == "low":
        return True, f"Low inventory (bonus {low_bonus:+.0%})"
    if inventory_hint == "high" and price_variance <= 0:
        return False, f"High inventory (penalty {high_penalty:+.0%})"
    if price_variance > 0.15:
        return True, "Recent price volatility"
    return False, "No urgency detected"


def score_itinerary(
    *,
    price: PriceBreakdown,
    budget_pp: float,
    buy_now: bool,
    days_to_event: int,
    distance_km: float = 0.0,
    co2_kg_pp: float = 0.0,
) -> float:
    if budget_pp <= 0:
        affordability_score = 0.2
    else:
        budget_gap = budget_pp - price.total
        if budget_gap >= 0:
            affordability_score = min(1.0, 0.6 + 0.4 * min(budget_pp / max(price.total, 1.0), 1.0))
        else:
            overshoot = abs(budget_gap)
            affordability_score = max(0.2, 0.6 - min(overshoot / max(price.total, 1.0), 0.5))

    urgency_bonus = 0.15 if buy_now else 0.0
    timeline_bonus = max(0.0, 0.15 - min(days_to_event / 40.0, 0.15))
    
    # Distance penalty: -0.01 per 500km (max -0.10)
    distance_penalty = min(0.10, (distance_km / 500.0) * 0.01)
    
    # CO2 penalty: -0.01 per 10kg (max -0.10)
    co2_penalty = min(0.10, (co2_kg_pp / 10.0) * 0.01)

    score = max(0.0, min(1.0, affordability_score + urgency_bonus + timeline_bonus - distance_penalty - co2_penalty))
    return round(score, 4)
