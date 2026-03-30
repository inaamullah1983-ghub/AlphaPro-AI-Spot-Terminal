import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go 
import time
import asyncio
import os

# --- 1. ROBUST ENGINE (Threaded for Cloud Stability) ---
import threading
from agent.database import init_db
from agent.config import SYMBOLS
from agent.tasks import start_stream
from agent.main import _ws_message_handler

# Ensure database and tables exist immediately
init_db()

@st.cache_resource
def start_global_engine():
    """Runs the Binance stream in a dedicated background thread to stay alive on Cloud."""
    def run_async_engine():
        # Create a private event loop for this background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for symbol in SYMBOLS:
            # start_stream already creates a task internally
            start_stream(symbol, "1m", _ws_message_handler)
            
        print("🚀 Background Engine is now LIVE (Threaded)")
        # Keep this thread's loop running forever
        loop.run_forever()

    # Start the thread and set daemon=True so it closes when the app closes
    thread = threading.Thread(target=run_async_engine, daemon=True)
    thread.start()
    return True

# Trigger the engine (Streamlit caches this so it only runs ONCE)
engine_is_running = start_global_engine()

# --- 2. LAYOUT CONFIG ---
st.set_page_config(page_title="AlphaPro Terminal", page_icon="📟", layout="wide")

# --- 3. DATA HELPERS ---
def get_wallet(coin):
    """Fetches wallet balances and PnL with stable fallbacks."""
    try:
        conn = sqlite3.connect("market_data.db", timeout=10)
        usdt = conn.execute("SELECT amount FROM wallet WHERE asset='USDT'").fetchone()
        balance = usdt[0] if usdt else 10000.0
        
        asset = coin.replace("USDT", "")
        coin_res = conn.execute("SELECT amount FROM wallet WHERE asset=?", (asset,)).fetchone()
        held = coin_res[0] if coin_res else 0.0
        
        pnl_res = conn.execute("SELECT SUM(pnl_amount) FROM paper_trades WHERE status='CLOSED'").fetchone()
        pnl = pnl_res[0] if pnl_res and pnl_res[0] is not None else 0.0
        
        conn.close()
        return balance, held, pnl, (balance + (held * 70000))
    except:
        return 10000.0, 0.0, 0.0, 10000.0

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    selected_coin = st.selectbox("🎯 Select Asset", SYMBOLS, index=0)
    st.divider()
    st.info(f"Viewing: {selected_coin}")
    st.caption("AlphaPro Engine v2.0")

# --- 5. TABS ---
st.title(f"📟 AlphaPro AI Terminal: {selected_coin}")
tab_investor, tab_scientist, tab_quant = st.tabs(["🏦 Portfolio", "🔬 Technicals", "🧠 AI Logic"])

# --- 6. TAB 1: PORTFOLIO ---
with tab_investor:
    balance, held, pnl, equity = get_wallet(selected_coin) 
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Balance", f"${balance:,.2f}")
    m2.metric(f"{selected_coin.replace('USDT','')} Held", f"{held:.6f}")
    m3.metric("Realized P&L", f"${pnl:,.2f}", delta=f"{pnl:.2f}")
    m4.metric("Status", "🤖 AUTOPILOT")
    
    st.divider()
    st.subheader("📜 Recent Trade History")
    try:
        conn = sqlite3.connect("market_data.db")
        trades_df = pd.read_sql_query(
            f"SELECT datetime(timestamp, 'unixepoch', '+5 hours') as time, type, entry_price, exit_price, pnl_amount, status "
            f"FROM paper_trades WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 10", conn)
        conn.close()
        if not trades_df.empty:
            st.dataframe(trades_df, width='stretch')
        else:
            st.info("No trades recorded yet.")
    except:
        st.warning("Connecting to trade records...")

# --- 7. TAB 2: TECHNICALS ---
with tab_scientist:
    try:
        conn = sqlite3.connect("market_data.db")
        sig = conn.execute(f"SELECT confidence, reason FROM ai_signals WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 1").fetchone()
        df = pd.read_sql_query(
            f"SELECT datetime(timestamp/1000, 'unixepoch', '+5 hours') as time, open, high, low, close "
            f"FROM klines WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 60", conn)
        conn.close()

        score = (sig[0] * 100.0) if sig else 0.0
        reason = str(sig[1]).upper() if sig else ""
        
        col_chart, col_gauge = st.columns([3, 1])
        with col_chart:
            st.subheader("🕯️ Candlestick Radar")
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                                    increasing_line_color='#00CC96', decreasing_line_color='#FF4B4B')])
                fig.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(t=0,b=0,l=0,r=0), template="plotly_dark")
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("📡 Gathering market data...")

        with col_gauge:
            st.subheader("🌡️ Strategy")
            gauge = go.Figure(go.Indicator(mode="gauge+number", value=score,
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "white"},
                           'steps': [{'range': [0, 30], 'color': "#FF4B4B"},
                                     {'range': [30, 70], 'color': "#FFAA00"},
                                     {'range': [70, 100], 'color': "#00CC96"}]}))
            gauge.update_layout(height=250, margin=dict(t=30,b=0,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(gauge, width='stretch')
            st.write(f"Trend: {'Bull 🟢' if 'BULLISH' in reason else 'Bear 🔴'}")
            st.write(f"Vol: {'Squeeze 🟡' if 'SQUEEZE' in reason else 'Normal ⚪'}")

        st.divider()
        if not df.empty:
            st.table(df[['time', 'open', 'high', 'low', 'close']].head(5))
    except Exception as e:
        st.error(f"Syncing database... {e}")

# --- 8. TAB 3: AI REASONING ---
with tab_quant:
    st.subheader("🧠 Live Decision Logic")
    try:
        conn = sqlite3.connect("market_data.db")
        signals = pd.read_sql_query(
            f"SELECT datetime(timestamp, 'unixepoch', '+5 hours') as time, signal, confidence, reason "
            f"FROM ai_signals WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 5", conn)
        conn.close()
        for _, row in signals.iterrows():
            with st.expander(f"{row['time']} - {row['signal']} ({row['confidence']*100:.0f}%)"):
                st.write(row['reason'])
    except:
        st.info("AI is analyzing live data. Signals will appear shortly.")

# --- 9. AUTO-REFRESH ---
time.sleep(10) 
st.rerun()