from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.connectors.fx import FXConnector
from app.config import FXSettings
from app.normalizers.price import calculate_price
from app.ranking.scorer import score_itinerary


def make_fx(rates: dict[str, float]) -> FXConnector:
    settings = FXSettings(base_url="", base_currency="EUR", fallback_rates=rates)
    connector = FXConnector(settings)
    connector._write_cache(rates)  # preload cache for deterministic tests
    return connector


def test_vat_included_vs_excluded(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    fx = make_fx({"EUR": 1.0})
    event_included = {
        "price": {"amount": 50, "currency": "EUR", "includes_vat": True},
        "fees": [],
        "vat_rate": 0.2,
    }
    event_excluded = {
        "price": {"amount": 50, "currency": "EUR", "includes_vat": False},
        "fees": [],
        "vat_rate": 0.2,
    }
    price_included = calculate_price(event_included, fx=fx, target_currency="EUR")
    price_excluded = calculate_price(event_excluded, fx=fx, target_currency="EUR")
    assert price_included.total == pytest.approx(50.0)
    assert price_excluded.total == pytest.approx(60.0)


def test_multiple_fees_aggregation(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    fx = make_fx({"EUR": 1.0})
    event = {
        "price": {"amount": 20, "currency": "EUR", "includes_vat": True},
        "fees": [
            {"label": "Service", "amount": 2.0, "currency": "EUR"},
            {"label": "Facility", "amount": 1.5, "currency": "EUR"},
        ],
        "vat_rate": 0.2,
    }
    price = calculate_price(event, fx=fx, target_currency="EUR")
    assert price.fees == pytest.approx(3.5)
    assert price.total == pytest.approx(23.5)


def test_promo_ties(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    fx = make_fx({"EUR": 1.0, "GBP": 0.86})
    event = {
        "price": {"amount": 40, "currency": "EUR", "includes_vat": True},
        "fees": [],
        "promos": [
            {"code": "TENPCT", "type": "percent", "value": 10},
            {"code": "FIVE_FIXED", "type": "fixed", "value": 5, "currency": "EUR"},
        ],
        "vat_rate": 0.2,
    }
    price = calculate_price(event, fx=fx, target_currency="EUR")
    assert price.promos == pytest.approx(5.0)
    assert price.total == pytest.approx(35.0)


def test_fx_pivot(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    fx = make_fx({"EUR": 1.0, "USD": 1.2, "GBP": 0.9})
    event = {
        "price": {"amount": 30, "currency": "USD", "includes_vat": True},
        "fees": [
            {"label": "Service", "amount": 2.0, "currency": "GBP"},
        ],
        "vat_rate": 0.1,
    }
    price = calculate_price(event, fx=fx, target_currency="EUR")
    usd_to_eur = 30 / 1.2
    gbp_to_eur = 2.0 / 0.9
    expected = usd_to_eur + gbp_to_eur
    assert price.total == pytest.approx(expected, rel=1e-3)


def test_scoring_edges(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    fx = make_fx({"EUR": 1.0})
    event = {
        "price": {"amount": 50, "currency": "EUR", "includes_vat": True},
        "fees": [],
        "vat_rate": 0.2,
        "inventory_hint": "low",
        "start_ts": datetime.now(timezone.utc).isoformat(),
    }
    price = calculate_price(event, fx=fx, target_currency="EUR")
    score_no_bonus = score_itinerary(price=price, budget_pp=40, buy_now=False, days_to_event=0)
    score_with_bonus = score_itinerary(price=price, budget_pp=40, buy_now=True, days_to_event=0)
    assert score_with_bonus > score_no_bonus
    score_under_budget = score_itinerary(price=price, budget_pp=80, buy_now=False, days_to_event=30)
    assert score_under_budget >= score_no_bonus
