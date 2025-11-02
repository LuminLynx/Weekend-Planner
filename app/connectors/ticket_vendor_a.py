
# Stub connector; replace with real API mapping later.
async def get_offers(session, event_query: dict) -> list[dict]:
    return [
        {
            "provider": "a",
            "title": event_query["title"],
            "start_ts": event_query["start_ts"],
            "venue": {"lat": 38.709, "lng": -9.133, "address": "Lisbon"},
            "price": {"amount": 22.0, "currency": "EUR", "includes_vat": True},
            "fees": [{"type": "service", "amount": 2.5, "currency": "EUR"}],
            "vat_rate": 0.23,
            "promos": ["STUDENT10"],
            "inventory_hint": "med",
            "url": "https://vendor-a.example/tickets/abc",
            "source_id": "a-abc"
        }
    ]
