
import httpx
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

FX_LAST_GOOD_PATH = Path("data/fx_last_good.json")
FX_CACHE_TTL_SECONDS = 3600  # 1 hour

def _load_last_good() -> tuple[dict[str, float] | None, str]:
    """Load last good FX rates from disk. Returns (rates, timestamp_iso)"""
    # Ensure data directory exists
    FX_LAST_GOOD_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not FX_LAST_GOOD_PATH.exists():
        return None, ""
    try:
        data = json.loads(FX_LAST_GOOD_PATH.read_text())
        return data.get("rates"), data.get("timestamp", "")
    except Exception:
        return None, ""

def _save_last_good(rates: dict[str, float]) -> None:
    """Save FX rates to disk with timestamp"""
    # Ensure data directory exists
    FX_LAST_GOOD_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "rates": rates,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    FX_LAST_GOOD_PATH.write_text(json.dumps(data, indent=2))

async def get_fx_rates(base_url: str, ttl_seconds: int = FX_CACHE_TTL_SECONDS) -> tuple[dict[str, float], str]:
    """
    Fetch FX rates with fallback to last_good on failure.
    
    Returns:
        (rates: dict, fx_source: str)
        fx_source can be: "live", "last_good", "fallback_eur_only"
    """
    # Try to use cached last_good if fresh
    last_good, last_ts = _load_last_good()
    if last_good and last_ts:
        try:
            cached_time = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - cached_time).total_seconds() < ttl_seconds:
                return last_good, "cached_last_good"
        except Exception:
            pass
    
    # Try live fetch
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(base_url)
            r.raise_for_status()
            data = r.json()
            rates = data.get("rates") or {}
            rates["EUR"] = 1.0
            _save_last_good(rates)
            return rates, "live"
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        # Network error or invalid response, fallback to last_good
        if last_good:
            print(f"[FX] Network error, using last_good fallback: {type(e).__name__}", file=sys.stderr)
            return last_good, "last_good"
        # Ultimate fallback: EUR only
        return {"EUR": 1.0}, "fallback_eur_only"
