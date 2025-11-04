# Weekend Plan Synthesizer — Budget/Pricing First

Generates 1–3 weekend options optimized for **total landed cost** with a transparent breakdown
(base, fees, VAT, promos, FX). Optionally bundles a nearby dining suggestion.

📄 **[View Project Website](https://luminlynx.github.io/Weekend-Planner/)**

## Quickstart
```bash
pip install -e .
pytest -q
python app/main.py --date 2025-11-02 --budget-pp 30 --with-dining
# or run as a web app:
uvicorn app.server:app --host 0.0.0.0 --port 8000

Fill-ins

Replace vendor stubs in app/connectors/ticket_vendor_*.py with real API calls.

Swap the placeholder price-drop probs with a trained model:

Train with app/models/price_drop/train.py

Save to app/models/price_drop/model.bin and load in your runtime.


Wire real FX provider (ECB/exchangerate.host) and dining API.
