
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse, HTMLResponse
import asyncio, yaml, json, httpx
from datetime import datetime
from .connectors import ticket_vendor_a, ticket_vendor_b, fx as fx_api, dining as dining_api, weather as weather_api
from .normalizers.price import compute_landed
from .ranking.scorer import budget_aware_score
from .policies.buy_now import buy_now_policy
from .ui.copy import templates as tpl
from .utils.logging import log_itinerary
from .utils.profile import get_profile_manager

app = FastAPI(title="Weekend Planner API")

def _days_to_event(start_ts: str) -> int:
    """Calculate days from now until event"""
    try:
        event_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
        now = datetime.now(event_dt.tzinfo)
        return max(0, (event_dt - now).days)
    except Exception:
        return 5  # fallback

async def _generate_itineraries(date: str, budget: float, with_dining: bool, debug: bool = False):
    """Generate itineraries with optional debug info"""
    # Load user preferences
    profile_manager = get_profile_manager()
    user_profile = profile_manager.load()
    user_prefs = user_profile.to_dict()
    
    event = {
        "title": "Indie Concert",
        "start_ts": f"{date}T20:30:00Z",
        "venue": {"lat": 38.709, "lng": -9.133, "address": "Lisbon"}
    }
    
    # Fetch weather for the event location
    weather = await weather_api.get_weather(event["venue"]["lat"], event["venue"]["lng"])
    
    async with httpx.AsyncClient(timeout=10) as session:
        fx_rates, fx_source = await fx_api.get_fx_rates("https://api.exchangerate.host/latest")
        offers = []
        for get_offers in (ticket_vendor_a.get_offers, ticket_vendor_b.get_offers):
            offers.extend(await get_offers(session, event))

        cfg = yaml.safe_load(open("app/config/settings.example.yaml"))
        days_to_event = _days_to_event(event["start_ts"])
        
        items = []
        for offer in offers:
            landed, breakdown = compute_landed(
                offer, user_currency=cfg["currency"], fx_rates=fx_rates,
                vat_fallback_rate=cfg["pricing"]["vat_fallback_rate"],
                promo_rules=cfg["pricing"]["promo_rules"]
            )
            prob = 0.18 if offer["provider"] == "a" else 0.46  # placeholder
            buy_now, buy_reason = buy_now_policy(
                prob=prob,
                days_to_event=days_to_event,
                threshold=cfg["model"]["price_drop_threshold"],
                min_days_force_buy=cfg["model"]["min_days_force_buy"],
                inventory_hint=offer.get("inventory_hint", "med")
            )
            dining_choice = None
            dining_cache_hit = False
            dining_cuisines = []
            if with_dining:
                near, dining_cache_hit = await dining_api.get_nearby(event["venue"])
                dining_choice = near[0] if near else None
                # Extract cuisines if available
                if dining_choice and "cuisines" in dining_choice:
                    dining_cuisines = dining_choice["cuisines"]
            
            score = budget_aware_score(
                base_score=0.7,
                landed_cost=landed["amount"],
                user_budget_pp=budget,
                price_drop_prob_7d=prob,
                days_to_event=days_to_event,
                dining_est_pp=(dining_choice or {}).get("est_pp", 0.0),
                user_preferences=user_prefs,
                event_city=event["venue"].get("address"),
                dining_cuisines=dining_cuisines
            )
            
            # Structured logging for observability
            log_itinerary(
                provider=offer["provider"],
                landed_amount=landed["amount"],
                currency=landed["currency"],
                fx_source=fx_source,
                cache_fx=fx_source == "cached_last_good",
                buy_now=buy_now,
                reason=buy_reason,
                score=score,
                days_to_event=days_to_event,
                price_drop_prob=prob
            )
            
            item = {
                "event_title": event["title"],
                "start_ts": event["start_ts"],
                "best_price": {
                    "landed": landed, "breakdown": breakdown, "provider": offer["provider"],
                    "price_drop_prob_7d": prob, "buy_now": buy_now, "url": offer.get("url")
                },
                "meal_bundle": {"chosen": dining_choice} if dining_choice else None,
                "weather": weather,
                "score": score,
                "rationale": tpl.itinerary_copy(
                    event["title"], event["start_ts"], landed["amount"], landed["currency"],
                    offer["provider"], prob, buy_now,
                    (dining_choice or {}).get("name"), (dining_choice or {}).get("est_pp")
                )
            }
            
            if debug:
                item["debug"] = {
                    "fx_source": fx_source,
                    "cache": {
                        "fx_hit": fx_source == "cached_last_good",
                        "dining_hit": dining_cache_hit
                    },
                    "breakdown": breakdown,
                    "scoring_inputs": {
                        "base_score": 0.7,
                        "landed_cost": landed["amount"],
                        "user_budget": budget,
                        "price_drop_prob": prob,
                        "days_to_event": days_to_event,
                        "dining_est": (dining_choice or {}).get("est_pp", 0.0),
                        "preferences": user_prefs
                    },
                    "buy_now_reason": buy_reason,
                    "inventory_hint": offer.get("inventory_hint", "med"),
                    "weather": weather
                }
            
            items.append(item)

        top = sorted(items, key=lambda r: r["score"], reverse=True)[:3]
        return {"itineraries": top}

@app.get("/healthz")
async def health():
    return {"ok": True}

@app.get("/user/preferences")
async def get_user_preferences():
    """Get current user preferences"""
    profile_manager = get_profile_manager()
    profile = profile_manager.load()
    return JSONResponse(profile.to_dict())

@app.post("/user/preferences")
async def update_user_preferences(preferences: dict = Body(...)):
    """Update user preferences"""
    profile_manager = get_profile_manager()
    profile = profile_manager.update(**preferences)
    return JSONResponse(profile.to_dict())

@app.get("/plan")
async def plan(date: str = Query(..., description="YYYY-MM-DD"),
               budget: float = Query(30.0, description="Budget per person"),
               with_dining: bool = Query(True, description="Include dining suggestions")):
    result = await _generate_itineraries(date, budget, with_dining, debug=False)
    return JSONResponse(result)

@app.get("/plan/debug")
async def plan_debug(date: str = Query(..., description="YYYY-MM-DD"),
                     budget: float = Query(30.0, description="Budget per person"),
                     with_dining: bool = Query(True, description="Include dining suggestions")):
    result = await _generate_itineraries(date, budget, with_dining, debug=True)
    return JSONResponse(result)

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weekend Planner</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 20px; line-height: 1.4; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    input, button { font-size: 16px; padding: 10px; border-radius: 8px; border: 1px solid #ccc; }
    button { background: #111; color: white; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; }
    .muted { color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <h2>Weekend Planner (Budget First)</h2>
  <div class="row">
    <label>Date: <input id="date" type="date"/></label>
    <label>Budget (pp): <input id="budget" type="number" value="30" step="1"/></label>
    <label><input id="dining" type="checkbox" checked/> Dining</label>
    <button onclick="run()">Plan</button>
  </div>
  <div id="out" style="margin-top:16px;"></div>
  <p class="muted">Tip: Works well on phones/tablets. No login needed.</p>
  <script>
    async function run() {
      const d = document.getElementById('date').value;
      const b = document.getElementById('budget').value || 30;
      const w = document.getElementById('dining').checked;
      if (!d) { alert('Pick a date'); return; }
      const res = await fetch(`/plan?date=${encodeURIComponent(d)}&budget=${encodeURIComponent(b)}&with_dining=${w}`);
      const js = await res.json();
      const div = document.getElementById('out');
      div.innerHTML = '';
      js.itineraries.forEach(it => {
        const el = document.createElement('div');
        el.className = 'card';
        el.innerHTML = `<b>${it.event_title}</b> — ${it.start_ts}<br/>` +
          `${it.rationale}<br/>` +
          `<div class="muted">Provider: ${it.best_price.provider} · Total: ${it.best_price.landed.amount} ${it.best_price.landed.currency}</div>`;
        div.appendChild(el);
      });
    }
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)
