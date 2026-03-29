import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go 
import time
import asyncio
import os

# --- 1. ALL-IN-ONE ENGINE (Cloud & Loop Fix) ---
from agent.database import init_db
from agent.config import SYMBOLS, TIMEZONE_OFFSET, MIN_CANDLES_REQUIRED
from agent.tasks import start_stream
from agent.main import _ws_message_handler

# Initialize Database immediately
init_db()

# Safe Loop Handler: This ensures the background worker starts without crashing
if "worker_started" not in st.session_state:
    try:
        # Get or create the event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        for symbol in SYMBOLS:
            # We schedule the task directly on the loop to avoid "No Running Loop" error
            loop.create_task(start_stream(symbol, "1m", _ws_message_handler))
        
        st.session_state.worker_started = True
        # Using st.toast or print for non-blocking notification
        print("🚀 AlphaPro Engine Started Successfully")
    except Exception as e:
        st.error(f"Engine Startup Error: {e}")

# --- 2. PROFESSIONAL CONFIG ---
st.set_page_config(page_title="AlphaPro Terminal", page_icon="📟", layout="wide")

# --- 3. DATA FETCHING FUNCTIONS ---
def get_wallet(selected_coin):
    """Ultra-Stable Wallet Fetcher with Error Handling."""
    try:
        conn = sqlite3.connect("market_data.db", timeout=10)
        # Fetch USDT
        usdt_res = conn.execute("SELECT amount FROM wallet WHERE asset='USDT'").fetchone()
        balance = usdt_res[0] if usdt_res else 10000.0
        
        # Fetch current coin (e.g., BTC)
        asset_name = selected_coin.replace("USDT", "")
        coin_res = conn.execute("SELECT amount FROM wallet WHERE asset=?", (asset_name,)).fetchone()
        amount = coin_res[0] if coin_res else 0.0
        
        # Fetch PnL
        pnl_res = conn.execute("SELECT SUM(pnl_amount) FROM paper_trades WHERE status='CLOSED'").fetchone()
        total_pnl = pnl_res[0] if pnl_res and pnl_res[0] is not None else 0.0
        
        conn.close()
        # Estimating equity at $70k BTC for visual reference
        return balance, amount, total_pnl, (balance + (amount * 70000))
    except Exception:
        return 10000.0, 0.0, 0.0, 10000.0

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    selected_coin = st.selectbox("🎯 Select Asset", SYMBOLS, index=0)
    st.divider()
    st.info(f"Viewing: {selected_coin}")
    st.caption("AlphaPro Engine v2.0")

# --- 5. HEADER & TABS ---
st.title(f"📟 AlphaPro AI Terminal: {selected_coin}")
tab_investor, tab_scientist, tab_quant = st.tabs([
    "🏦 Portfolio Executive", 
    "🔬 Technical Lab", 
    "🧠 AI Reasoning"
])

# --- 6. TAB 1: PORTFOLIO EXECUTIVE ---
with tab_investor:
    balance, amount, total_pnl, total_equity = get_wallet(selected_coin) 
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Balance", f"${balance:,.2f}")
    m2.metric(f"{selected_coin.replace('USDT','')} Held", f"{amount:.6f}")
    m3.metric("Realized P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl:.2f}")
    m4.metric("Status", "🤖 AUTOPILOT")
    
    st.divider()
    st.subheader("📜 Recent Trade History")
    try:
        conn = sqlite3.connect("market_data.db")
        trades_df = pd.read_sql_query(f"SELECT datetime(timestamp, 'unixepoch', '+5 hours') as time, type, entry_price, exit_price, pnl_amount, status FROM paper_trades WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 10", conn)
        conn.close()
        if not trades_df.empty:
            st.dataframe(trades_df, use_container_width=True)
        else:
            st.info("No trades recorded for this asset yet.")
    except Exception:
        st.warning("Connecting to trade records...")

# --- 7. TAB 2: TECHNICAL LAB ---
with tab_scientist:
    try:
        conn = sqlite3.connect("market_data.db")
        sig_row = conn.execute(f"SELECT confidence, reason FROM ai_signals WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 1").fetchone()
        df_candles = pd.read_sql_query(f"SELECT datetime(timestamp/1000, 'unixepoch', '+5 hours') as time, open, high, low, close FROM klines WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 60", conn)
        conn.close()

        current_score = (sig_row[0] * 100.0) if sig_row else 0.0
        reason_text = str(sig_row[1]).upper() if sig_row else ""
        is_bullish = "BULLISH" in reason_text
        is_squeezing = "SQUEEZE" in reason_text

        col_chart, col_gauge = st.columns([3, 1])

        with col_chart:
            st.subheader("🕯️ Candlestick Radar")
            if not df_candles.empty:
                fig_candles = go.Figure(data=[go.Candlestick(
                    x=df_candles['time'], open=df_candles['open'], high=df_candles['high'], 
                    low=df_candles['low'], close=df_candles['close'],
                    increasing_line_color='#00CC96', decreasing_line_color='#FF4B4B'
                )])
                fig_candles.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(t=0,b=0,l=0,r=0), template="plotly_dark")
                st.plotly_chart(fig_candles, use_container_width=True)
            else:
                st.info(f"📡 Gathering market data...")

        with col_gauge:
            st.subheader("🌡️ Strategy")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = current_score,
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "white"},
                        'steps': [{'range': [0, 30], 'color': "#FF4B4B"},
                                {'range': [30, 70], 'color': "#FFAA00"},
                                {'range': [70, 100], 'color': "#00CC96"}]}))
            fig_gauge.update_layout(height=300, margin=dict(t=30,b=0,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.divider()
            st.caption("🔬 Status")
            st.write(f"Trend: {'Bull 🟢' if is_bullish else 'Bear 🔴'}")
            st.write(f"Vol: {'Squeeze 🟡' if is_squeezing else 'Normal ⚪'}")

        st.divider()
        st.subheader("📊 Live Market Statistics (OHLC)")
        if not df_candles.empty:
            st.table(df_candles[['time', 'open', 'high', 'low', 'close']].head(5))
    except Exception as e:
        st.error(f"Waiting for database... {e}")

# --- 8. TAB 3: AI REASONING ---
with tab_quant:
    st.subheader("🧠 Live Decision Logic")
    try:
        conn = sqlite3.connect("market_data.db")
        signals_df = pd.read_sql_query(f"SELECT datetime(timestamp, 'unixepoch', '+5 hours') as local_time, signal, confidence, reason FROM ai_signals WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 5", conn)
        conn.close()
        
        for _, row in signals_df.iterrows():
            with st.expander(f"{row['local_time']} - {row['signal']} ({row['confidence']*100:.0f}%)", expanded=True):
                st.write(row['reason'])
    except Exception:
        st.info("🧠 AI is analyzing live data. No signals recorded yet.")

# --- 9. AUTO-REFRESH ---
time.sleep(10) 
st.rerun()