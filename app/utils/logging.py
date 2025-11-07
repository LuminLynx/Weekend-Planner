
import json
import sys
from datetime import datetime, timezone
from typing import Any

def log_itinerary(provider: str, landed_amount: float, currency: str, 
                 fx_source: str, cache_fx: bool, buy_now: bool, 
                 reason: str, score: float, **extra):
    """
    Log structured JSON for each itinerary with key metrics.
    
    Args:
        provider: Ticket provider name
        landed_amount: Final landed price
        currency: Currency code
        fx_source: FX source (live, last_good, cached_last_good, fallback_eur_only)
        cache_fx: Whether FX was from cache
        buy_now: Whether to buy now
        reason: Buy-now reason
        score: Ranking score
        **extra: Additional fields to log
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "type": "itinerary",
        "provider": provider,
        "landed": landed_amount,
        "currency": currency,
        "fx_source": fx_source,
        "cache_fx": cache_fx,
        "buy_now": buy_now,
        "reason": reason,
        "score": score,
    }
    log_entry.update(extra)
    print(json.dumps(log_entry), file=sys.stderr)
