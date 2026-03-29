import sqlite3
from agent.database import get_balance, close_position_in_db
from agent.config import TAKE_PROFIT_PCT, STOP_LOSS_PCT, DB_NAME

async def monitor_open_positions(current_price):
    try:
        # 1. Fetch current USDT and BTC holdings from the NEW Dynamic Wallet
        # This replaces the old "SELECT balance_usdt" which was crashing
        usdt_balance = get_balance("USDT")
        btc_held = get_balance("BTC") 

        # If we don't own any BTC, there is nothing to monitor
        if btc_held <= 0:
            return None

        # 2. Get the Entry Price from your trade history
        conn = sqlite3.connect(DB_NAME)
        # Using a row factory makes the data easier to read
        conn.row_factory = sqlite3.Row
        trade = conn.execute("SELECT entry_price, amount FROM paper_trades WHERE status='OPEN'").fetchone()
        conn.close()

        if not trade: 
            return None
            
        entry_p = trade['entry_price']
        qty = trade['amount']

        # 3. Calculate Profit/Loss percentage
        pnl_pct = (current_price - entry_p) / entry_p
        
        # 4. The Exit Logic (Hardened with Config)
        if pnl_pct >= TAKE_PROFIT_PCT:
            new_bal = usdt_balance + (qty * current_price)
            close_position_in_db(new_bal)
            return f"✅ PROFIT EXIT: Sold at {current_price} | PnL: {pnl_pct*100:.2f}%"

        if pnl_pct <= -STOP_LOSS_PCT:
            new_bal = usdt_balance + (qty * current_price)
            close_position_in_db(new_bal)
            return f"❌ STOP LOSS: Sold at {current_price} | PnL: {pnl_pct*100:.2f}%"

        return f"⏳ Holding BTC: Unrealized PnL: {pnl_pct*100:.2f}%"

    except Exception as e:
        # This catches any remaining SQL errors and tells us exactly where they are
        return f"⚠️ Monitor Error: {e}"