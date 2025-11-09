"""
Tests for travel distance and CO2 scoring penalties.
"""

import pytest
from app.ranking.scorer import score_itinerary
from app.normalizers.price import PriceBreakdown


def make_price(total: float) -> PriceBreakdown:
    """Helper to create a PriceBreakdown for testing"""
    return PriceBreakdown(
        base=total,
        vat=0.0,
        fees=0.0,
        promos=0.0,
        total=total,
        currency="EUR",
        components={"base": total, "vat": 0.0, "fees": 0.0, "promo": 0.0},
        promo_applied=None
    )


def test_no_travel_penalty():
    """Test that local events have no travel penalty"""
    price = make_price(30.0)
    score = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    # Should get max score for good affordability
    assert score == 1.0


def test_short_distance_penalty():
    """Test penalty for short distance travel (200 km, rail)"""
    price = make_price(30.0)
    
    # Baseline score with no travel
    score_base = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    
    # Score with short distance travel
    score_travel = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=200.0,
        co2_kg_pp=8.0  # 200 km * 0.04 kg/km for rail
    )
    
    # Should have a small penalty
    assert score_travel < score_base
    penalty = score_base - score_travel
    # Distance penalty: 200/500 * 0.01 = 0.004
    # CO2 penalty: 8/10 * 0.01 = 0.008
    # Total: 0.012
    assert penalty == pytest.approx(0.012, abs=0.001)


def test_medium_distance_penalty():
    """Test penalty for medium distance travel (1000 km, air)"""
    price = make_price(30.0)
    
    score_base = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    
    score_travel = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=1000.0,
        co2_kg_pp=150.0  # 1000 km * 0.15 kg/km for air
    )
    
    penalty = score_base - score_travel
    # Distance penalty: 1000/500 * 0.01 = 0.02
    # CO2 penalty: 150/10 * 0.01 = 0.15
    # But CO2 penalty is capped at 0.10, so total = 0.02 + 0.10 = 0.12
    assert penalty == pytest.approx(0.12, abs=0.001)


def test_long_distance_penalty():
    """Test penalty for long distance travel (2500 km, air)"""
    price = make_price(30.0)
    
    score_base = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    
    score_travel = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=2500.0,
        co2_kg_pp=375.0  # 2500 km * 0.15 kg/km for air
    )
    
    penalty = score_base - score_travel
    # Distance penalty: 2500/500 * 0.01 = 0.05
    # CO2 penalty: 375/10 * 0.01 = 0.375, capped at 0.10
    # Total: 0.05 + 0.10 = 0.15
    assert penalty == pytest.approx(0.15, abs=0.001)


def test_max_travel_penalty():
    """Test that travel penalty is capped at 0.20"""
    price = make_price(30.0)
    
    score_base = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    
    # Very long distance that would exceed max penalty
    score_travel = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=10000.0,  # Would give 10000/500 * 0.01 = 0.20 for distance alone
        co2_kg_pp=1500.0  # Would give 1500/10 * 0.01 = 1.50 for CO2 alone
    )
    
    penalty = score_base - score_travel
    # Both penalties are capped at 0.10 each, so max total = 0.20
    assert penalty == pytest.approx(0.20, abs=0.001)


def test_travel_penalty_with_other_bonuses():
    """Test that travel penalties work alongside other scoring factors"""
    price = make_price(30.0)
    
    # Score with travel but also with urgency bonus
    score = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=True,  # +0.15 urgency bonus
        days_to_event=10,
        distance_km=1000.0,
        co2_kg_pp=150.0  # -0.12 total penalty
    )
    
    # With urgency bonus offsetting travel penalty, should still have high score
    # Base affordability ~1.0, +0.15 urgency, -0.12 travel = 1.0 (capped)
    assert score == 1.0


def test_distance_only_penalty():
    """Test distance penalty independently"""
    price = make_price(30.0)
    
    score_base = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    
    # 500 km with minimal CO2 (e.g., electric rail)
    score_travel = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=500.0,
        co2_kg_pp=2.0  # Very low CO2
    )
    
    penalty = score_base - score_travel
    # Distance penalty: 500/500 * 0.01 = 0.01
    # CO2 penalty: 2/10 * 0.01 = 0.002
    # Total: 0.012
    assert penalty == pytest.approx(0.012, abs=0.001)


def test_co2_only_penalty():
    """Test CO2 penalty independently"""
    price = make_price(30.0)
    
    score_base = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=0.0,
        co2_kg_pp=0.0
    )
    
    # Hypothetical: short distance but high CO2 (inefficient transport)
    score_travel = score_itinerary(
        price=price,
        budget_pp=50.0,
        buy_now=False,
        days_to_event=10,
        distance_km=100.0,  # Short distance
        co2_kg_pp=50.0  # High CO2
    )
    
    penalty = score_base - score_travel
    # Distance penalty: 100/500 * 0.01 = 0.002
    # CO2 penalty: 50/10 * 0.01 = 0.05
    # Total: 0.052
    assert penalty == pytest.approx(0.052, abs=0.001)
