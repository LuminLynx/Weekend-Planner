
import httpx

async def get_fx_rates(base_url: str) -> dict[str, float]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(base_url)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates") or {}
        rates["EUR"] = 1.0
        return rates
