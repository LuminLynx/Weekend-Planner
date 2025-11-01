"""Utilities for price normalisation across ticket vendors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from app.connectors.fx import FXConnector


@dataclass
class PriceBreakdown:
    base: float
    vat: float
    fees: float
    promos: float
    total: float
    currency: str
    components: Dict[str, float]
    promo_applied: Dict | None


def _parse_amount(entry: Dict, key: str) -> float:
    value = entry.get(key)
    return float(value) if value is not None else 0.0


def _convert_amount(fx: FXConnector, amount: float, from_currency: str, target: str) -> float:
    if from_currency == target:
        return amount
    return fx.convert(amount, from_currency, target)


def calculate_price(event: Dict, *, fx: FXConnector, target_currency: str) -> PriceBreakdown:
    price_info = event.get("price", {})
    currency = price_info.get("currency", target_currency)
    includes_vat = price_info.get("includes_vat", True)
    base_amount = float(price_info.get("amount", 0.0))

    converted_base = _convert_amount(fx, base_amount, currency, target_currency)

    vat_rate = float(event.get("vat_rate", 0.0) or 0.0)
    vat_amount = 0.0 if includes_vat else converted_base * vat_rate
    gross_base = converted_base + vat_amount

    fees_amount = 0.0
    for fee in event.get("fees", []):
        fee_amount = _convert_amount(
            fx,
            _parse_amount(fee, "amount"),
            fee.get("currency", currency),
            target_currency,
        )
        fees_amount += fee_amount

    promo_discount, applied_promo = _best_promo(
        event.get("promos", []), gross_base + fees_amount, currency, fx, target_currency
    )

    total = max(gross_base + fees_amount - promo_discount, 0.0)

    components = {
        "base": round(converted_base, 2),
        "vat": round(vat_amount, 2),
        "fees": round(fees_amount, 2),
        "promo": round(promo_discount, 2),
    }

    return PriceBreakdown(
        base=round(converted_base, 2),
        vat=round(vat_amount, 2),
        fees=round(fees_amount, 2),
        promos=round(promo_discount, 2),
        total=round(total, 2),
        currency=target_currency,
        components=components,
        promo_applied=applied_promo,
    )


def _best_promo(promos: List[Dict], subtotal: float, price_currency: str, fx: FXConnector, target_currency: str) -> Tuple[float, Dict | None]:
    best_discount = 0.0
    best = None
    for promo in promos or []:
        if promo.get("type") == "percent":
            percent = float(promo.get("value", 0.0)) / 100.0
            discount = subtotal * percent
        elif promo.get("type") == "fixed":
            currency = promo.get("currency", price_currency)
            discount = _convert_amount(
                fx,
                float(promo.get("value", 0.0)),
                currency,
                target_currency,
            )
        else:
            continue
        if discount > best_discount:
            best_discount = discount
            best = promo
    return best_discount, best
