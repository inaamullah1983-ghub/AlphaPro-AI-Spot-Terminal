import sqlite3

# LOCAL CONSTANT - Breaks circular loops
DB_NAME = "market_data.db"

def init_db():
    """Initializes the Professional Multi-Asset Schema."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS klines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, timestamp INTEGER, open REAL, high REAL, low REAL, close REAL, volume REAL
            );
            CREATE TABLE IF NOT EXISTS ai_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                signal TEXT, confidence REAL, reason TEXT
            );
            CREATE TABLE IF NOT EXISTS wallet (
                asset TEXT PRIMARY KEY, 
                amount REAL DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, type TEXT, entry_price REAL, exit_price REAL, 
                amount REAL, pnl_amount REAL, status TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            INSERT OR IGNORE INTO wallet (asset, amount) VALUES ('USDT', 10000.0);
            INSERT OR IGNORE INTO wallet (asset, amount) VALUES ('BTC', 0.0);
            INSERT OR IGNORE INTO wallet (asset, amount) VALUES ('ETH', 0.0);
        ''')

# --- DATA READERS ---

def get_balance(asset="USDT"):
    """Fetch balance as a clean NUMBER (Unwraps the tuple)."""
    with sqlite3.connect(DB_NAME) as conn:
        res = conn.execute("SELECT amount FROM wallet WHERE asset=?", (asset.upper(),)).fetchone()
        return res[0] if res else 0.0

def get_recent_klines(symbol: str, limit=50):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM klines WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?', (symbol.upper(), limit))
        return cursor.fetchall()

# --- DATA WRITERS ---

def save_kline(symbol, k):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('INSERT INTO klines (symbol, timestamp, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (symbol.upper(), k['t'], k['o'], k['h'], k['l'], k['c'], k['v']))

def save_ai_signal(symbol, signal_data):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('INSERT INTO ai_signals (symbol, signal, confidence, reason) VALUES (?, ?, ?, ?)',
                     (symbol.upper(), signal_data.get('signal'), signal_data.get('confidence'), signal_data.get('reason')))

def save_paper_trade(symbol, trade_type, price, amount, status='OPEN', pnl=0.0):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('INSERT INTO paper_trades (symbol, type, entry_price, amount, status, pnl_amount) VALUES (?, ?, ?, ?, ?, ?)',
                     (symbol.upper(), trade_type, price, amount, status, pnl))

# --- THE MISSING LINK (Fixes the ImportError) ---

def update_balance(asset, amount):
    """Updates the amount for any asset in the Dynamic Wallet."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO wallet (asset, amount) VALUES (?, ?)", (asset.upper(), amount))
        conn.commit()

def close_position_in_db(new_balance):
    """Resets holdings and updates cash after a successful exit."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE wallet SET amount = ? WHERE asset = 'USDT'", (new_balance,))
        conn.execute("UPDATE wallet SET amount = 0.0 WHERE asset != 'USDT'")
        conn.execute("UPDATE paper_trades SET status = 'CLOSED' WHERE status = 'OPEN'")
        conn.commit()