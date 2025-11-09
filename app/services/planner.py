"""Core planning orchestration."""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Dict, List

from app.config import Settings, load_settings
from app.connectors.dining import DiningConnector
from app.connectors.fx import FXConnector
from app.connectors.ticket_vendor_a import TicketVendorAConnector
from app.connectors.ticket_vendor_b import TicketVendorBConnector
from app.connectors.travel import get_travel_info
from app.normalizers.price import calculate_price
from app.ranking.scorer import buy_now_heuristic, days_until, score_itinerary
from app.utils.profile import get_profile_manager


@dataclass
class PlannerResult:
    itineraries: List[Dict]
    dining: List[Dict]
    fx_used: Dict[str, float]


class Planner:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.fx = FXConnector(self.settings.fx)
        vendor_a_token = os.getenv("VENDOR_A_TOKEN")
        vendor_b_token = os.getenv("VENDOR_B_TOKEN")
        dining_token = os.getenv("DINING_TOKEN")
        self.vendor_a = TicketVendorAConnector(self.settings.connector("ticket_vendor_a"), vendor_a_token)
        self.vendor_b = TicketVendorBConnector(self.settings.connector("ticket_vendor_b"), vendor_b_token)
        self.dining = DiningConnector(self.settings.connector("dining"), dining_token)

    async def plan(self, *, date: str, budget_pp: float, with_dining: bool = False) -> PlannerResult:
        # Fetch all data concurrently
        vendor_a_task = self.vendor_a.fetch(date=date)
        vendor_b_task = self.vendor_b.fetch(date=date)
        fx_rates_task = self.fx.get_rates()
        
        # Gather the vendor results and FX rates
        vendor_a_events, vendor_b_events, rates = await asyncio.gather(
            vendor_a_task, vendor_b_task, fx_rates_task
        )
        
        raw_events = []
        raw_events.extend(vendor_a_events)
        raw_events.extend(vendor_b_events)

        target_currency = self.settings.app.currency
        
        # Get user's home city from profile
        profile_mgr = get_profile_manager()
        profile = profile_mgr.load()
        home_city = profile.home_city

        itineraries: List[Dict] = []
        for event in raw_events:
            price_breakdown = await calculate_price(event, fx=self.fx, target_currency=target_currency)
            event_days_to = days_until(event["start_ts"])
            buy_now, reason = buy_now_heuristic(
                inventory_hint=event.get("inventory_hint", "unknown"),
                days_to_event=event_days_to,
                price_variance=0.0,
                settings={
                    "price_drop_days_threshold": self.settings.app.price_drop_days_threshold,
                    "price_drop_low_inventory_bonus": self.settings.app.price_drop_low_inventory_bonus,
                    "price_drop_high_inventory_penalty": self.settings.app.price_drop_high_inventory_penalty,
                },
            )
            
            # Calculate travel info
            event_city = event.get("city")
            distance_km = 0.0
            co2_kg_pp = 0.0
            if event_city and home_city:
                travel_info = get_travel_info(home_city, event_city)
                if travel_info:
                    distance_km = travel_info["distance_km"]
                    co2_kg_pp = travel_info["co2_kg_pp"]
            
            score = score_itinerary(
                price=price_breakdown,
                budget_pp=budget_pp,
                buy_now=buy_now,
                days_to_event=event_days_to,
                distance_km=distance_km,
                co2_kg_pp=co2_kg_pp,
            )
            itineraries.append(
                {
                    "provider": event["provider"],
                    "title": event["title"],
                    "start_ts": event["start_ts"],
                    "venue": event["venue"],
                    "city": event_city,
                    "url": event["url"],
                    "price": price_breakdown,
                    "score": score,
                    "buy_now": buy_now,
                    "buy_reason": reason,
                    "distance_km": distance_km,
                    "co2_kg_pp": co2_kg_pp,
                }
            )

        itineraries.sort(key=lambda item: item["score"], reverse=True)

        dining_options: List[Dict] = []
        if with_dining:
            dining_options = await self.dining.fetch(date=date)

        return PlannerResult(
            itineraries=itineraries,
            dining=dining_options,
            fx_used=rates,
        )
