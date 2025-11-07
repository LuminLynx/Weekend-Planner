
from datetime import datetime
import numpy as np

def make_features(price_series: list[dict], now: datetime|None=None) -> dict:
    if not price_series:
        return {"rolling_min_7": 0, "rolling_std_7": 0, "vendor_a": 0, "vendor_b": 0}
    prices = np.array([p["price"] for p in price_series[-30:]], dtype=float)
    rolling_min_7 = float(np.min(prices[-7:])) if prices.size else 0.0
    rolling_std_7 = float(np.std(prices[-7:])) if prices.size else 0.0
    vendor = price_series[-1].get("vendor", "a")
    return {
        "rolling_min_7": rolling_min_7,
        "rolling_std_7": rolling_std_7,
        "vendor_a": 1 if vendor == "a" else 0,
        "vendor_b": 1 if vendor == "b" else 0,
    }
