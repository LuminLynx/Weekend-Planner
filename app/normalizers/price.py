
from dataclasses import dataclass
from typing import Dict, Iterable
from decimal import Decimal, ROUND_HALF_UP

def round2(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

@dataclass
class Money:
    amount: float
    currency: str

def convert_fx(amount: float, from_cur: str, to_cur: str, fx_rates: Dict[str, float]) -> float:
    if from_cur == to_cur:
        return amount
    # convert via EUR as pivot
    if from_cur != "EUR":
        amount = amount / fx_rates.get(from_cur, 1.0)
    if to_cur != "EUR":
        amount = amount * fx_rates.get(to_cur, 1.0)
    return amount

def _target_amount(rule: dict, base: float, fees: float, tax: float) -> float:
    applies = rule.get("applies_to", "total")
    if applies == "base":
        return base
    if applies == "base_plus_fees":
        return base + fees
    return base + fees + tax

def best_promo(total_before_promo: float, available_codes: Iterable[str], promo_rules: Dict[str, dict],
               base: float, fees: float, tax: float) -> float:
    best = 0.0
    for code in (available_codes or []):
        rule = promo_rules.get(code)
        if not rule:
            continue
        target = _target_amount(rule, base, fees, tax)
        if rule["type"] == "percent":
            pct = rule.get("discount_multiplier", 1.0) * (rule["value"] / 100.0)
            disc = target * pct
        else:
            disc = float(rule["value"])
        if disc > best:
            best = disc
    return min(best, total_before_promo)

def compute_landed(offer: dict, user_currency: str, fx_rates: Dict[str, float],
                   vat_fallback_rate: float, promo_rules: Dict[str, dict]) -> tuple[dict, dict]:
    cur = offer["price"]["currency"]
    base = float(offer["price"]["amount"])
    
    # Handle mixed-currency fees - convert each fee to base currency first
    fees_in_base_currency = 0.0
    for fee in offer.get("fees", []):
        fee_amount = float(fee["amount"])
        fee_currency = fee.get("currency", cur)  # default to base currency if not specified
        if fee_currency != cur:
            # Convert fee to base currency
            fee_amount = convert_fx(fee_amount, fee_currency, cur, fx_rates)
        fees_in_base_currency += fee_amount
    
    includes_vat = bool(offer["price"].get("includes_vat", False))
    vat_rate = offer.get("vat_rate", None)
    if vat_rate is None:
        vat_rate = vat_fallback_rate

    tax = 0.0 if includes_vat else base * vat_rate
    total_before_promo = base + fees_in_base_currency + tax
    promo = best_promo(total_before_promo, offer.get("promos", []), promo_rules, base, fees_in_base_currency, tax)

    # Ensure promo doesn't reduce total below a floor (e.g., not below 0)
    total_vendor_currency = max(0.0, total_before_promo - promo)
    
    # convert after promo
    total_user_cur = convert_fx(total_vendor_currency, cur, user_currency, fx_rates)
    fx_adj = total_user_cur - total_vendor_currency if cur != user_currency else 0.0

    landed = {"amount": round2(total_user_cur), "currency": user_currency}
    breakdown = {
        "base": round2(base),
        "fees": round2(fees_in_base_currency),
        "vat": round2(tax),
        "promo": round2(promo),
        "fx": round2(fx_adj),
    }
    return landed, breakdown
