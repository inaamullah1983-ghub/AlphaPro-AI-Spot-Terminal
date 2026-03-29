import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go 
import time
from agent.config import SYMBOLS, TIMEZONE_OFFSET

# --- 1. PROFESSIONAL CONFIG ---
st.set_page_config(page_title="AlphaPro Terminal", page_icon="📟", layout="wide")

# --- 2. DATA FETCHING FUNCTIONS ---
def get_wallet():
    """Ultra-Stable Wallet Fetcher: Always returns 4 values to prevent Unpack Error."""
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
        # Always return exactly 4 things: Balance, Amount, PnL, Total Equity
        return balance, amount, total_pnl, (balance + (amount * 70000))
    except Exception:
        # Emergency Fallback: If DB is locked, return 10k so UI doesn't break
        return 10000.0, 0.0, 0.0, 10000.0

# --- 3. SIDEBAR (The Control Center) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    selected_coin = st.selectbox("🎯 Select Asset", SYMBOLS, index=0)
    st.divider()
    st.info(f"Viewing: {selected_coin}")
    st.caption("AlphaPro Engine v2.0")

# --- 4. HEADER & TABS ---
st.title(f"📟 AlphaPro AI Terminal: {selected_coin}")
tab_investor, tab_scientist, tab_quant = st.tabs([
    "🏦 Portfolio Executive", 
    "🔬 Technical Lab", 
    "🧠 AI Reasoning"
])

# --- 5. TAB 1: PORTFOLIO EXECUTIVE ---
with tab_investor:
    balance, amount, total_pnl, total_equity = get_wallet() 
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Balance", f"${balance:,.2f}")
    m2.metric(f"{selected_coin.replace('USDT','')} Held", f"{amount:.6f}")
    m3.metric("Realized P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl:.2f}")
    m4.metric("Status", "🤖 AUTOPILOT")
    
    st.divider()
    st.subheader("📜 Recent Trade History")
    conn = sqlite3.connect("market_data.db")
    trades_df = pd.read_sql_query(f"SELECT datetime(timestamp, '+5 hours') as time, type, entry_price, exit_price, pnl_amount, status FROM paper_trades WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 10", conn)
    conn.close()
    if not trades_df.empty:
        st.dataframe(trades_df, width=1200) # width='stretch' for newer versions
    else:
        st.info("No trades recorded for this asset.")

# --- 6. TAB 2: TECHNICAL LAB ---
# --- TAB 2: THE SCIENTIST VIEW (TOTAL FIX) ---
with tab_scientist:
    # 1. THE BRAIN (Fetch Data First)
    conn = sqlite3.connect("market_data.db")
    
    # --- SURGICAL PATCH: NEEDLE & STATUS SYNC ---
    sig_row = conn.execute(f"SELECT confidence, reason FROM ai_signals WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 1").fetchone()
    df_candles = pd.read_sql_query(f"SELECT datetime(timestamp/1000, 'unixepoch', '+5 hours') as time, open, high, low, close FROM klines WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 60", conn)
    conn.close()

    # Define the values for the needle and the status lights
    current_score = (sig_row[0] * 100.0) if sig_row else 0.0
    reason_text = str(sig_row[1]).upper() if sig_row else ""
    
    # These flags light up the 🟢/🔴 status dots below the needle
    is_bullish = "BULLISH" in reason_text
    is_squeezing = "SQUEEZE" in reason_text
    # --- END OF PATCH ---

    # 3. THE TOP ROW: Radar & Gauge
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
            st.plotly_chart(fig_candles, width="stretch")
        else:
            st.info("📡 Gathering market data...")

    with col_gauge:
        st.subheader("🌡️ Strategy")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = current_score,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "white"},
                    'steps': [{'range': [0, 30], 'color': "#FF4B4B"},
                            {'range': [30, 70], 'color': "#FFAA00"},
                            {'range': [70, 100], 'color': "#00CC96"}]}))
        fig_gauge.update_layout(height=300, margin=dict(t=30,b=0,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, width="stretch")
        
        # --- SCORECARD (Right below Gauge) ---
        st.divider()
        st.caption("🔬 Status")
        st.write(f"Trend: {'Bull 🟢' if is_bullish else 'Bear 🔴'}")
        st.write(f"Vol: {'Squeeze 🟡' if is_squeezing else 'Normal ⚪'}")

    # 4. THE BOTTOM ROW: Statistics Table (Outside the columns to be WIDE)
    st.divider()
    st.subheader("📊 Live Market Statistics (OHLC)")
    if not df_candles.empty:
        # Show the last 5 minutes of data in a wide, clear table
        st.table(df_candles[['time', 'open', 'high', 'low', 'close']].head(5))



# --- 7. TAB 3: AI REASONING ---
with tab_quant:
    st.subheader("🧠 Live Decision Logic")
    conn = sqlite3.connect("market_data.db")
    signals_df = pd.read_sql_query(f"SELECT datetime(timestamp, '+5 hours') as local_time, signal, confidence, reason FROM ai_signals WHERE symbol='{selected_coin}' ORDER BY id DESC LIMIT 5", conn)
    conn.close()
    
    for _, row in signals_df.iterrows():
        color = "green" if row['signal'] == "BUY" else "red" if row['signal'] == "SELL" else "gray"
        with st.expander(f"{row['local_time']} - {row['signal']} ({row['confidence']*100:.0f}%)", expanded=True):
            st.write(row['reason'])

# --- 8. REFRESH ---
time.sleep(5)
st.rerun()