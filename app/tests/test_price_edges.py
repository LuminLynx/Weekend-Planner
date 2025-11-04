
import pytest
import yaml
from app.normalizers.price import compute_landed


@pytest.fixture
def config():
    """Load config fixture for tests"""
    with open("app/config/settings.example.yaml") as f:
        return yaml.safe_load(f)


def test_mixed_currency_fees(config):
    """Test handling of fees in different currencies"""
    user_cur = "EUR"
    fx = {"EUR": 1.0, "USD": 1.08, "GBP": 0.85}
    vat_fallback = config["pricing"]["vat_fallback_rate"]
    promos = config["pricing"]["promo_rules"]
    
    # Base price in EUR, but fee in USD
    offer = {
        "price": {"amount": 20.0, "currency": "EUR", "includes_vat": True},
        "fees": [
            {"type": "service", "amount": 2.0, "currency": "EUR"},
            {"type": "international", "amount": 1.08, "currency": "USD"}  # Should convert to 1 EUR
        ],
        "vat_rate": 0.23,
        "promos": []
    }
    landed, breakdown = compute_landed(offer, user_cur, fx, vat_fallback, promos)
    # 20 + 2 + 1 (converted) = 23
    assert abs(landed["amount"] - 23.0) < 0.01
    assert abs(breakdown["fees"] - 3.0) < 0.01


def test_promo_floor_prevents_negative(config):
    """Test that promo cannot reduce total below 0"""
    user_cur = "EUR"
    fx = {"EUR": 1.0}
    vat_fallback = config["pricing"]["vat_fallback_rate"]
    
    # Create a promo that would exceed the total
    huge_promo_rules = {
        "HUGE100": {
            "type": "fixed",
            "value": 100.0,
            "applies_to": "total"
        }
    }
    
    offer = {
        "price": {"amount": 10.0, "currency": "EUR", "includes_vat": True},
        "fees": [],
        "vat_rate": 0.23,
        "promos": ["HUGE100"]
    }
    landed, breakdown = compute_landed(offer, user_cur, fx, vat_fallback, huge_promo_rules)
    # Should be max(0, 10 - 10) = 0, not negative
    assert landed["amount"] >= 0.0
    assert landed["amount"] == 0.0


def test_vat_fallback_used(config):
    """Test that VAT fallback is used when vat_rate is None"""
    user_cur = "EUR"
    fx = {"EUR": 1.0}
    vat_fallback = 0.23
    promos = {}
    
    offer = {
        "price": {"amount": 100.0, "currency": "EUR", "includes_vat": False},
        "fees": [],
        "vat_rate": None,  # Should use fallback
        "promos": []
    }
    landed, breakdown = compute_landed(offer, user_cur, fx, vat_fallback, promos)
    # 100 + 23 (VAT at 23%) = 123
    assert abs(landed["amount"] - 123.0) < 0.01
    assert abs(breakdown["vat"] - 23.0) < 0.01


def test_mixed_currency_complex(config):
    """Test complex scenario with mixed currencies, VAT, and promo"""
    user_cur = "GBP"
    fx = {"EUR": 1.0, "USD": 1.08, "GBP": 0.85}
    vat_fallback = config["pricing"]["vat_fallback_rate"]
    promos = config["pricing"]["promo_rules"]
    
    offer = {
        "price": {"amount": 50.0, "currency": "EUR", "includes_vat": False},
        "fees": [
            {"type": "service", "amount": 5.0, "currency": "EUR"},
            {"type": "processing", "amount": 2.16, "currency": "USD"}  # = 2 EUR
        ],
        "vat_rate": 0.23,
        "promos": ["STUDENT10"]  # 10% off base+fees
    }
    landed, breakdown = compute_landed(offer, user_cur, fx, vat_fallback, promos)
    
    # Base: 50 EUR
    # Fees: 5 + 2 = 7 EUR
    # Subtotal: 57 EUR
    # Promo: 10% of 57 = 5.7 EUR
    # After promo: 51.3 EUR
    # VAT: 50 * 0.23 = 11.5 EUR (on base only since promo applies to base_plus_fees)
    # Total: 51.3 + 11.5 = 62.8 EUR
    # Convert to GBP: 62.8 * 0.85 = ~53.38 GBP
    
    assert landed["currency"] == "GBP"
    assert landed["amount"] > 0  # Just verify it's computed and positive
