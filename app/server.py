"""FastAPI application exposing planning endpoints."""
from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import HTMLResponse, PlainTextResponse
except ImportError as exc:  # pragma: no cover - allow optional install
    raise SystemExit("fastapi must be installed to run app.server") from exc

from app.services.planner import Planner
from app.utils.share import get_share_manager, generate_html_view
from app.utils.metrics import export_prometheus

app = FastAPI(title="Weekend Planner")
planner = Planner()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/plan")
async def plan(date: str = Query(...), budget: float = Query(...), with_dining: bool = Query(False)) -> dict:
    if budget <= 0:
        raise HTTPException(status_code=400, detail="budget must be positive")
    result = await planner.plan(date=date, budget_pp=budget, with_dining=with_dining)
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
async def plan_debug(date: str = Query(...), budget: float = Query(...), with_dining: bool = Query(False)) -> dict:
    base_response = await plan(date=date, budget=budget, with_dining=with_dining)
    for itinerary in base_response["itineraries"]:
        itinerary["breakdown"] = itinerary["price"]["components"]
    base_response["meta"] = {"cache": {"fx": "disk"}}
    return base_response


@app.post("/share")
def create_share(plan_data: dict) -> dict:
    """
    Save a plan and return its share ID.
    
    Request body should contain the plan data (itineraries dict).
    Returns a JSON object with the share_id.
    """
    share_manager = get_share_manager()
    plan_id = share_manager.save_plan(plan_data)
    return {"share_id": plan_id}


@app.get("/share/{plan_id}", response_class=HTMLResponse)
def get_share(plan_id: str) -> str:
    """
    Retrieve a shared plan and render it as HTML.
    
    Returns an HTML page displaying the shared itinerary.
    Raises 404 if the plan_id doesn't exist.
    """
    share_manager = get_share_manager()
    plan_data = share_manager.get_plan(plan_id)
    
    if plan_data is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    html = generate_html_view(plan_data, plan_id)
    return html


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    """
    Return metrics in Prometheus text format.
    
    Exposes operational metrics including:
    - fx_live_latency_ms: FX API call latency
    - cache_hit_ratio: Cache hit ratio
    - vendor_a_latency_ms: Vendor A API call latency
    - planning_duration_ms: Planning operation duration
    """
    return export_prometheus()
