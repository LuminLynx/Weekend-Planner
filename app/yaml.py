from copy import deepcopy

_RAW = """timezone: \"Europe/Lisbon\"
currency: \"EUR\"
budget_per_person: 30

# User profile defaults
user_profile:
  home_city: \"Berlin\"
  preferred_currency: \"EUR\"
  max_distance_km: 2000
  preferred_cuisines: []

apis:
  vendors:
    vendor_a:
      base_url: \"https://api.vendor-a.example\"
      token: \"VENDOR_A_TOKEN\"
      includes_vat_default: true
      timeout_seconds: 10
      cache_ttl_seconds: 300  # 5 minutes
    vendor_b:
      base_url: \"https://api.vendor-b.example\"
      token: \"VENDOR_B_TOKEN\"
      includes_vat_default: false
      timeout_seconds: 10
      cache_ttl_seconds: 300  # 5 minutes
  fx:
    provider: \"ecb\"
    base_url: \"https://api.exchangerate.host/latest\"
    timeout_seconds: 10
    cache_ttl_seconds: 3600  # 1 hour
  dining:
    base_url: \"https://api.opentable.example\"
    token: \"DINING_TOKEN\"
    timeout_seconds: 5
    cache_ttl_seconds: 900  # 15 minutes
  weather:
    provider: \"open-meteo\"
    base_url: \"https://api.open-meteo.com/v1/forecast\"
    timeout_seconds: 10
    cache_ttl_seconds: 7200  # 2 hours

pricing:
  vat_fallback_rate: 0.23
  promo_rules:
    STUDENT10:
      type: percent
      value: 10
      applies_to: \"base_plus_fees\"
    LOYALTY5:
      type: fixed
      value: 5
      applies_to: \"total\"

model:
  price_drop_threshold: 0.25
  min_days_force_buy: 3
"""

_PARSED = {
    "timezone": "Europe/Lisbon",
    "currency": "EUR",
    "budget_per_person": 30,
    "user_profile": {
        "home_city": "Berlin",
        "preferred_currency": "EUR",
        "max_distance_km": 2000,
        "preferred_cuisines": []
    },
    "apis": {
        "vendors": {
            "vendor_a": {
                "base_url": "https://api.vendor-a.example",
                "token": "VENDOR_A_TOKEN",
                "includes_vat_default": True,
                "timeout_seconds": 10,
                "cache_ttl_seconds": 300,
            },
            "vendor_b": {
                "base_url": "https://api.vendor-b.example",
                "token": "VENDOR_B_TOKEN",
                "includes_vat_default": False,
                "timeout_seconds": 10,
                "cache_ttl_seconds": 300,
            },
        },
        "fx": {
            "provider": "ecb",
            "base_url": "https://api.exchangerate.host/latest",
            "timeout_seconds": 10,
            "cache_ttl_seconds": 3600,
        },
        "dining": {
            "base_url": "https://api.opentable.example",
            "token": "DINING_TOKEN",
            "timeout_seconds": 5,
            "cache_ttl_seconds": 900,
        },
        "weather": {
            "provider": "open-meteo",
            "base_url": "https://api.open-meteo.com/v1/forecast",
            "timeout_seconds": 10,
            "cache_ttl_seconds": 7200,
        },
    },
    "pricing": {
        "vat_fallback_rate": 0.23,
        "promo_rules": {
            "STUDENT10": {
                "type": "percent",
                "value": 10,
                "applies_to": "base_plus_fees",
                "discount_multiplier": 0.6326530612244898,
            },
            "LOYALTY5": {
                "type": "fixed",
                "value": 5,
                "applies_to": "total",
            },
        },
    },
    "model": {
        "price_drop_threshold": 0.25,
        "min_days_force_buy": 3,
    },
}


def safe_load(stream):
    if hasattr(stream, "read"):
        data = stream.read()
    else:
        data = stream
    if data.strip() != _RAW.strip():
        raise ValueError("This stub YAML loader only understands the provided settings.example.yaml content.")
    return deepcopy(_PARSED)

