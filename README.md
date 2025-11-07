# Weekend Plan Synthesizer — Budget/Pricing First

Generates 1–3 weekend options optimized for **total landed cost** with a transparent breakdown
(base, fees, VAT, promos, FX). Optionally bundles a nearby dining suggestion.

## 🚀 Live App - No Setup Required!

**✨ Try it now:** **[Launch Weekend Planner](https://luminlynx.github.io/Weekend-Planner/app.html)**

The app is running live on GitHub Pages - just click and start planning your weekend!

📄 **[Project Website](https://luminlynx.github.io/Weekend-Planner/)** | 📖 **[Deployment Guide](./DEPLOYMENT.md)**

## Quickstart

### Use the Live App (Recommended)
No installation needed! Just visit:
```
https://luminlynx.github.io/Weekend-Planner/app.html
```

### Local Development
For developing or testing locally:
```bash
pip install -e .
pytest -q
python app/main.py --date 2025-11-02 --budget-pp 30 --with-dining
# or run as a web app:
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

### Deployment Options
See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive deployment options including:
- ✅ GitHub Pages (current live deployment)
- Railway, Render, Fly.io (free tier backends)
- AWS Lambda, Google Cloud Run (serverless)
- Docker containerization

Fill-ins

Replace vendor stubs in app/connectors/ticket_vendor_*.py with real API calls.

Swap the placeholder price-drop probs with a trained model:

Train with app/models/price_drop/train.py

Save to app/models/price_drop/model.bin and load in your runtime.


Wire real FX provider (ECB/exchangerate.host) and dining API.
