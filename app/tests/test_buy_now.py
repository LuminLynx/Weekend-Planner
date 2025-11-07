
from app.policies.buy_now import buy_now_policy


def test_buy_now_urgent_days():
    """Test buy_now when event is very soon"""
    buy, reason = buy_now_policy(prob=0.5, days_to_event=2, threshold=0.25, min_days_force_buy=3)
    assert buy is True
    assert "2d_left" in reason


def test_buy_now_low_inventory():
    """Test buy_now when inventory is low"""
    buy, reason = buy_now_policy(prob=0.5, days_to_event=10, threshold=0.25, 
                                  min_days_force_buy=3, inventory_hint="low")
    assert buy is True
    assert "low_inventory" in reason


def test_buy_now_low_drop_probability():
    """Test buy_now when drop probability is below threshold"""
    buy, reason = buy_now_policy(prob=0.15, days_to_event=10, threshold=0.25, min_days_force_buy=3)
    assert buy is True
    assert "low_drop_prob" in reason


def test_not_buy_now_high_drop_probability():
    """Test wait when drop probability is high"""
    buy, reason = buy_now_policy(prob=0.45, days_to_event=10, threshold=0.25, min_days_force_buy=3)
    assert buy is False
    assert "high_drop_prob" in reason
    assert "wait" in reason


def test_buy_now_edge_case_exact_threshold():
    """Test behavior at exact threshold"""
    buy, reason = buy_now_policy(prob=0.25, days_to_event=10, threshold=0.25, min_days_force_buy=3)
    assert buy is False  # prob >= threshold means wait
