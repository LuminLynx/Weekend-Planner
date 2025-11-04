
from app.ranking.scorer import budget_aware_score


def test_within_budget_scores_higher():
    """Test that within-budget items score higher than over-budget"""
    within = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10
    )
    over = budget_aware_score(
        base_score=0.7, landed_cost=35.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10
    )
    assert within > over


def test_bookable_bonus():
    """Test that bookable items get a bonus"""
    bookable = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10, is_bookable=True
    )
    not_bookable = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10, is_bookable=False
    )
    assert bookable > not_bookable
    assert abs(bookable - not_bookable - 0.1) < 0.01  # bonus is 0.1


def test_under_budget_gets_bonus():
    """Test that items significantly under budget get a bonus"""
    far_under = budget_aware_score(
        base_score=0.7, landed_cost=10.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10
    )
    at_budget = budget_aware_score(
        base_score=0.7, landed_cost=30.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10
    )
    assert far_under > at_budget


def test_price_drop_bonus_for_far_events():
    """Test that high drop probability gives bonus for far-out events"""
    with_bonus = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.5, days_to_event=10
    )
    without_bonus = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.2, days_to_event=10
    )
    assert with_bonus > without_bonus


def test_no_drop_bonus_for_near_events():
    """Test that drop bonus is not given for near events"""
    near = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.5, days_to_event=3
    )
    far = budget_aware_score(
        base_score=0.7, landed_cost=25.0, user_budget_pp=30.0,
        price_drop_prob_7d=0.5, days_to_event=10
    )
    assert far > near
