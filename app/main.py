"""Command line entry point for the weekend planner."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.planner import Planner  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Weekend Planner")
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--budget-pp", type=float, required=True, help="Budget per person")
    parser.add_argument("--with-dining", action="store_true", help="Include dining suggestions")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    planner = Planner()
    result = planner.plan(date=args.date, budget_pp=args.budget_pp, with_dining=args.with_dining)

    if args.json:
        serialisable = {
            "itineraries": [
                {
                    **{k: v for k, v in itinerary.items() if k != "price"},
                    "price": itinerary["price"].__dict__,
                }
                for itinerary in result.itineraries
            ],
            "dining": result.dining,
            "fx_used": result.fx_used,
        }
        print(json.dumps(serialisable, indent=2, sort_keys=True))
    else:
        for itinerary in result.itineraries:
            price = itinerary["price"]
            print(f"{itinerary['title']} ({itinerary['provider']})")
            print(f"  When: {itinerary['start_ts']} @ {itinerary['venue']}")
            print(f"  Total (pp): {price.total:.2f} {price.currency}")
            print(f"  Score: {itinerary['score']}")
            print(f"  Buy now: {itinerary['buy_now']} ({itinerary['buy_reason']})")
            print(f"  URL: {itinerary['url']}")
            print("")
        if args.with_dining and result.dining:
            print("Dining suggestions:")
            for option in result.dining:
                print(
                    f"- {option['name']} · {option['est_pp']} {price.currency} pp · "
                    f"{option['distance_m']}m away"
                )
                print(f"  Book: {option['booking_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
