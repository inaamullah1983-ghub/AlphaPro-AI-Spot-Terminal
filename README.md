# AlphaPro - Binance Agent (moved)

This folder contains the agent scaffold moved from the week1 workspace. It provides a minimal FastAPI app that fetches klines from Binance and exposes a `/analyze` endpoint and websocket stream start/stop endpoints.

Run (from D:\AlphaPro):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn agent.main:app --reload --port 8000
```

Then test:

```powershell
curl -X POST "http://localhost:8000/analyze" -H "Content-Type: application/json" -d '{"symbol":"BTCUSDT","interval":"1m","limit":10}'
```
.....................................................................
Terminal 1 (Backend):
uvicorn agent.main:app --reload
Terminal 2 (Dashboard):
python -m streamlit run dashboard.py