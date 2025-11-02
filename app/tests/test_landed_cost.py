
import yaml
from app.normalizers.price import compute_landed

def test_vat_fees_promo_fx():
    user_cur = "EUR"
    fx = {"EUR": 1.0, "USD": 1.08}  # 1 EUR = 1.08 USD
    cfg = yaml.safe_load(open("app/config/settings.example.yaml"))
    vat_fallback = cfg["pricing"]["vat_fallback_rate"]
    promos = cfg["pricing"]["promo_rules"]

    # Vendor A: EUR, VAT included, service fees, percent promo
    offer_a = {
        "price": {"amount": 22.0, "currency": "EUR", "includes_vat": True},
        "fees": [{"type": "service", "amount": 2.5, "currency": "EUR"}],
        "vat_rate": 0.23,
        "promos": ["STUDENT10"]
    }
    landed_a, _ = compute_landed(offer_a, user_cur, fx, vat_fallback, promos)
    assert abs(landed_a["amount"] - 22.95) < 0.01   # 22 + 2.5 - 10%

    # Vendor B: USD, VAT excluded, fixed promo, FX convert
    offer_b = {
        "price": {"amount": 19.0, "currency": "USD", "includes_vat": False},
        "fees": [{"type": "service", "amount": 3.1, "currency": "USD"}],
        "vat_rate": None,
        "promos": ["LOYALTY5"]
    }
    landed_b, _ = compute_landed(offer_b, user_cur, fx, vat_fallback, promos)
    assert landed_b["currency"] == "EUR"
    assert landed_b["amount"] > 0
