"""Alternative lightweight server using standard library only."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from app.services.planner import Planner

planner = Planner()


class PlannerHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http handler signature
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self._send_json({"status": "ok"})
            return
        if parsed.path not in {"/plan", "/plan/debug"}:
            self._send_json({"detail": "not found"}, status=404)
            return
        params = parse_qs(parsed.query)
        try:
            date = params["date"][0]
            budget = float(params["budget"][0])
            with_dining = params.get("with_dining", ["false"])[0].lower() == "true"
        except Exception:  # noqa: BLE001 - respond to malformed requests
            self._send_json({"detail": "missing or invalid parameters"}, status=400)
            return
        result = planner.plan(date=date, budget_pp=budget, with_dining=with_dining)
        response = {
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
        if parsed.path == "/plan/debug":
            for itinerary in response["itineraries"]:
                itinerary["breakdown"] = itinerary["price"]["components"]
            response["meta"] = {"cache": {"fx": "disk"}}
        self._send_json(response)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), PlannerHandler)
    print(f"Serving on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
