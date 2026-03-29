import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- 1. CORE SYSTEM SETTINGS ---
# Fixes the 'ImportError: cannot import name DB_NAME'
DB_NAME = "market_data.db"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
TIMEZONE_OFFSET = "+5 hours"

# --- 2. API KEYS (Pulled from .env) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")

# --- 3. TRADING & AI LOGIC ---
# Increased to 50 to ensure Bollinger Bands and Fibonacci have enough history
MIN_CANDLES_REQUIRED = 50

# Only trade if AI confidence is high (0.0 to 1.0)
CONFIDENCE_THRESHOLD = 0.85

# Amount to spend per paper trade (USDT)
TRADE_SIZE_USD = 100.0

# --- 4. RISK MANAGEMENT (EXIT RULES) ---
# Sell if profit hits +4%
TAKE_PROFIT_PCT = 0.04

# Sell if loss hits -2%
STOP_LOSS_PCT = 0.02