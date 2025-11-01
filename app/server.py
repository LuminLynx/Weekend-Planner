"""FastAPI application exposing planning endpoints."""
from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from fastapi import FastAPI, HTTPException, Query
except ImportError as exc:  # pragma: no cover - allow optional install
    raise SystemExit("fastapi must be installed to run app.server") from exc

from app.services.planner import Planner

app = FastAPI(title="Weekend Planner")
planner = Planner()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/plan")
def plan(date: str = Query(...), budget: float = Query(...), with_dining: bool = Query(False)) -> dict:
    if budget <= 0:
        raise HTTPException(status_code=400, detail="budget must be positive")
    result = planner.plan(date=date, budget_pp=budget, with_dining=with_dining)
    return {
        "itineraries": [
            {
                **{k: v for k, v in itinerary.items() if k != "price"},
                "price": itinerary["price"].__dict__,
                "total_pp": itinerary["price"].total,
            }
            for itinerary in result.itineraries
        ],
        "dining": result.dining,
        "fx_used": result.fx_used,
    }


@app.get("/plan/debug")
def plan_debug(date: str = Query(...), budget: float = Query(...), with_dining: bool = Query(False)) -> dict:
    base_response = plan(date=date, budget=budget, with_dining=with_dining)
    for itinerary in base_response["itineraries"]:
        itinerary["breakdown"] = itinerary["price"]["components"]
    base_response["meta"] = {"cache": {"fx": "disk"}}
    return base_response
