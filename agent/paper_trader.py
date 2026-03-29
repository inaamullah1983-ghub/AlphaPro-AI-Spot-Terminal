import sqlite3
from agent.database import DB_NAME, save_paper_trade, get_balance, update_balance
from agent.config import TRADE_SIZE_USD, TAKE_PROFIT_PCT, STOP_LOSS_PCT

def get_open_positions():
    """Helper to fetch USDT, BTC, and Entry Price from the Dynamic Wallet."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        # Fetch balances using the NEW 'asset' column logic
        usdt_row = conn.execute("SELECT amount FROM wallet WHERE asset='USDT'").fetchone()
        btc_row = conn.execute("SELECT amount FROM wallet WHERE asset='BTC'").fetchone()
        
        balance = usdt_row['amount'] if usdt_row else 10000.0
        btc_held = btc_row['amount'] if btc_row else 0.0
        
        # Fetch the entry price of the last OPEN trade
        trade = conn.execute(
            "SELECT entry_price FROM paper_trades WHERE status='OPEN' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        
        entry_p = trade['entry_price'] if trade else 0.0
        return btc_held, balance, entry_p

async def process_paper_trade(symbol, ai_signal, current_price):
    """The 'Execution' Engine: Handles Buy/Sell logic based on AI and Risk Rules."""
    btc_held, balance, entry_price = get_open_positions()
    signal = ai_signal.get("signal")
    
    # 1. EXIT LOGIC: If we are HOLDING
    if btc_held > 0:
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Determine if we should Exit (AI Signal, Profit Target, or Stop Loss)
        should_exit = False
        exit_type = ""
        
        if signal == "SELL":
            should_exit = True
            exit_type = "AI-EXIT"
        elif pnl_pct >= TAKE_PROFIT_PCT:
            should_exit = True
            exit_type = "PROFIT LOCK"
        elif pnl_pct <= -STOP_LOSS_PCT:
            should_exit = True
            exit_type = "STOP LOSS"

        if should_exit:
            cash_gained = btc_held * current_price
            new_total_balance = balance + cash_gained
            pnl_usd = cash_gained - (btc_held * entry_price)
            
            # Update Database: Reset BTC to 0, Update USDT
            update_balance("USDT", new_total_balance)
            update_balance("BTC", 0.0)
            
            # Close the trade record
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute(
                    "UPDATE paper_trades SET exit_price = ?, pnl_amount = ?, status = 'CLOSED' WHERE status = 'OPEN'",
                    (current_price, pnl_usd)
                )
            
            return f"📈 {exit_type}: Sold at {current_price} | PnL: ${pnl_usd:.2f}"
        
        return f"⏳ Holding {symbol}: PnL {pnl_pct*100:.2f}%"

    # 2. ENTRY LOGIC: If we have NO HOLDINGS
    elif signal == "BUY" and btc_held <= 0:
        if balance >= TRADE_SIZE_USD:
            btc_to_buy = TRADE_SIZE_USD / current_price
            new_usdt_balance = balance - TRADE_SIZE_USD
            
            # Update Dynamic Wallet
            update_balance("USDT", new_usdt_balance)
            update_balance("BTC", btc_to_buy)
            
            # Log the new Buy Trade
            save_paper_trade(symbol, "BUY", current_price, btc_to_buy, status='OPEN')
            
            return f"📉 BOUGHT ${TRADE_SIZE_USD} of {symbol} at {current_price}"

    return "⏸️ Standing by (No active trade or signal)"