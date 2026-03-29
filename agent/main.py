import asyncio
import sqlite3
import json
import statistics
from typing import List
from fastapi import FastAPI, HTTPException

# --- 1. INTERNAL MODULES ---
from agent.config import SYMBOLS, MIN_CANDLES_REQUIRED
from agent.schemas import AnalyzeRequest, AnalyzeResponse, KlinePoint
from agent.database import init_db, save_kline, save_ai_signal, get_recent_klines
from agent.indicators import calculate_indicators
from agent.ai_engine import get_ai_signal  # <-- This is the name we must use
from agent.sentiment import get_market_sentiment
from agent.tasks import start_stream
from agent.monitor import monitor_open_positions
from agent.paper_trader import process_paper_trade

# --- APP INITIALIZATION ---
app = FastAPI(title="AlphaPro Multi-Asset Terminal")
app.state.stream_tasks = {}

# --- BACKGROUND WORKER ---
async def run_auto_analysis(symbol: str):
    """Core logic: Math -> News -> AI -> Execution."""
    try:
        # 1. Fetch data
        data = get_recent_klines(symbol, limit=50)
        if not data or len(data) < MIN_CANDLES_REQUIRED:
            print(f"⏳ {symbol}: Collecting data ({len(data)}/{MIN_CANDLES_REQUIRED})")
            return
        
        # 2. Calculate Indicators & Sentiment
        tech = calculate_indicators(data)
        news = await get_market_sentiment(symbol.replace("USDT", ""))
        current_p = float(data[0][6]) 

        # 3. Ask AI for decision (FIXED NAME)
        ai_response = await get_ai_signal(symbol, tech, news)
        
        # 4. Create 'Rich Reason'
        rich_reason = f"[{tech['trend']}] [RSI:{tech['rsi']}] | {ai_response.get('reason', '')}"

        # 5. Save to DB
        save_ai_signal(symbol, {
            "signal": ai_response.get("signal", "HOLD"),
            "confidence": tech.get('python_score', 0) / 100.0, 
            "reason": rich_reason
        })

        # 6. Trade Execution (FIXED VARIABLE NAME)
        trade_log = await process_paper_trade(symbol, ai_response, current_p)
        print(f"🤖 {symbol} Update: {trade_log}")

    except Exception as e:
        print(f"⚠️ Auto-trade error [{symbol}]: {e}")

# --- WEBSOCKET HANDLER ---
async def _ws_message_handler(data: dict):
    """Triggers when a 1-minute candle CLOSES."""
    try:
        # --- ADD THIS DEBUG LINE ---
        # print(f"📡 DEBUG: Raw data received for {data.get('s')}")

        if 'k' in data and data['k']['x']: 
            symbol = data['s']
            save_kline(symbol, data['k']) 
            asyncio.create_task(run_auto_analysis(symbol))
            print(f"✅ Candle Saved: {symbol}")
    except Exception as e:
        print(f"Error in handler: {e}")

# --- STARTUP ---
@app.on_event("startup")
async def startup():
    init_db()
    print(f"📡 Initializing Multi-Coin Engines for: {SYMBOLS}")
    
    for symbol in SYMBOLS:
        print(f"🔄 Starting background task for: {symbol}")
        # Use the imported start_stream and DO NOT 'await' it
        # This allows both BTC and ETH to start at the same time
        task = start_stream(symbol, "1m", _ws_message_handler)
        app.state.stream_tasks[symbol.upper()] = task
    
    print(f"🚀 AlphaPro Multi-Asset Mode ACTIVE")


# --- API ENDPOINTS ---
@app.get("/ai/analyze/{symbol}")
async def manual_analyze(symbol: str):
    try:
        key = symbol.upper()
        data = get_recent_klines(key, limit=50)
        if not data: return {"error": "No data in DB"}
        tech = calculate_indicators(data)
        news = await get_market_sentiment(key.replace("USDT", ""))
        return await get_ai_signal(key, tech, news)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.main:app", host="0.0.0.0", port=8000, reload=True)