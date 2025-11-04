
import asyncio, json, yaml, httpx
from datetime import datetime
from app.connectors import ticket_vendor_a, ticket_vendor_b, fx as fx_api, dining as dining_api
from app.normalizers.price import compute_landed
from app.ranking.scorer import budget_aware_score
from app.policies.buy_now import buy_now_policy
from app.ui.copy.templates import itinerary_copy

def _days_to_event(start_ts: str) -> int:
    """Calculate days from now until event"""
    try:
        event_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
        now = datetime.now(event_dt.tzinfo)
        return max(0, (event_dt - now).days)
    except Exception:
        return 5  # fallback

async def run(city: str, date_iso: str, budget_pp: float, with_dining: bool):
    event = {
        "title": "Indie Concert",
        "start_ts": f"{date_iso}T20:30:00Z",
        "venue": {"lat": 38.709, "lng": -9.133, "address": "Lisbon"}
    }

    async with httpx.AsyncClient(timeout=10) as session:
        fx_rates, fx_source = await fx_api.get_fx_rates("https://api.exchangerate.host/latest")
        offers = []
        for get_offers in (ticket_vendor_a.get_offers, ticket_vendor_b.get_offers):
            offers.extend(await get_offers(session, event))

        cfg = yaml.safe_load(open("app/config/settings.example.yaml"))
        days_to_event = _days_to_event(event["start_ts"])
        
        top = []
        for offer in offers:
            landed, breakdown = compute_landed(
                offer, user_currency=cfg["currency"], fx_rates=fx_rates,
                vat_fallback_rate=cfg["pricing"]["vat_fallback_rate"],
                promo_rules=cfg["pricing"]["promo_rules"]
            )
            prob = 0.18 if offer["provider"] == "a" else 0.46  # placeholder until model is trained
            buy_now, buy_reason = buy_now_policy(
                prob=prob,
                days_to_event=days_to_event,
                threshold=cfg["model"]["price_drop_threshold"],
                min_days_force_buy=cfg["model"]["min_days_force_buy"],
                inventory_hint=offer.get("inventory_hint", "med")
            )
            dining_choice = None
            if with_dining:
                near, _ = await dining_api.get_nearby(event["venue"])
                dining_choice = near[0] if near else None
            score = budget_aware_score(
                base_score=0.7,
                landed_cost=landed["amount"],
                user_budget_pp=budget_pp,
                price_drop_prob_7d=prob,
                days_to_event=days_to_event,
                dining_est_pp=(dining_choice or {}).get("est_pp", 0.0)
            )
            row = {
                "event_title": event["title"],
                "start_ts": event["start_ts"],
                "best_price": {
                    "landed": landed, "breakdown": breakdown, "provider": offer["provider"],
                    "price_drop_prob_7d": prob, "buy_now": buy_now, "url": offer.get("url")
                },
                "meal_bundle": {"chosen": dining_choice} if dining_choice else None,
                "score": score,
                "rationale": itinerary_copy(
                    event["title"], event["start_ts"], landed["amount"], landed["currency"],
                    offer["provider"], prob, buy_now,
                    (dining_choice or {}).get("name"), (dining_choice or {}).get("est_pp")
                )
            }
            top.append(row)

        top = sorted(top, key=lambda r: r["score"], reverse=True)[:3]
        print(json.dumps({"itineraries": top}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--city", default="Lisbon")
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--budget-pp", type=float, default=30)
    p.add_argument("--with-dining", action="store_true")
    args = p.parse_args()
    asyncio.run(run(args.city, args.date, args.budget_pp, args.with_dining))
