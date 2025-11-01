
# Stub connector; replace with real API mapping later.
async def get_offers(session, event_query: dict) -> list[dict]:
    return [
        {
            "provider": "b",
            "title": event_query["title"],
            "start_ts": event_query["start_ts"],
            "venue": {"lat": 38.709, "lng": -9.133, "address": "Lisbon"},
            "price": {"amount": 19.0, "currency": "USD", "includes_vat": False},
            "fees": [{"type": "service", "amount": 3.1, "currency": "USD"}],
            "vat_rate": None,
            "promos": ["LOYALTY5"],
            "inventory_hint": "low",
            "url": "https://vendor-b.example/offer/xyz",
            "source_id": "b-xyz"
        }
    ]
