import os
import streamlit as st
from dotenv import load_dotenv

# --- 1. LOAD ENVIRONMENT ---
# Load .env locally (Ignored on Streamlit Cloud automatically)
load_dotenv()

def get_secret(key, default=None):
    """Hybrid secret loader: Checks Streamlit Cloud Secrets, then Local .env"""
    try:
        # Try Streamlit Secrets first (Cloud)
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        # Fallback to local .env or System Environment Variables
        return os.getenv(key, default)

# --- 2. API KEYS (Hybrid Loading) ---
GROQ_API_KEY = get_secret("GROQ_API_KEY")
BINANCE_API_KEY = get_secret("BINANCE_API_KEY")
BINANCE_SECRET = get_secret("BINANCE_SECRET")

# --- 3. CORE SYSTEM SETTINGS ---
DB_NAME = "market_data.db"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
TIMEZONE_OFFSET = "+5 hours"

# --- 4. TRADING & AI LOGIC ---
# Warm-up period for Technical Indicators
MIN_CANDLES_REQUIRED = 50

# Logic thresholds
CONFIDENCE_THRESHOLD = 0.85
TRADE_SIZE_USD = 100.0

# --- 5. RISK MANAGEMENT (EXIT RULES) ---
TAKE_PROFIT_PCT = 0.04
STOP_LOSS_PCT = 0.02