def get_trade_size(confidence, balance_usdt):
    """
    Revised Logic: Strict Fractional Sizing.
    - Confidence < 85%: $0 (Still too risky)
    - 85% - 92%: 0.2% of balance (~$20) - The 'Test' Trade
    - 92% - 96%: 1.0% of balance (~$100) - The 'Standard' Trade
    - > 96%: 2.0% of balance (~$200) - The 'Exceptional' Trade
    """
    if confidence < 0.85:
        return 0
    elif 0.85 <= confidence < 0.92:
        return balance_usdt * 0.002 # 0.2% fraction
    elif 0.92 <= confidence < 0.96:
        return balance_usdt * 0.01  # 1.0% standard
    else:
        return balance_usdt * 0.02  # 2.0% maximum safety limit


def calculate_dynamic_exit(current_price, trade_type, tech_data):
    """
    Logic: Tighten Stop-Loss if RSI is showing a reversal.
    """
    base_sl = 0.02 # 2%
    # If RSI is extreme (>75), we tighten the stop to 1% to exit quickly on reversal
    if tech_data['rsi'] > 75 or tech_data['rsi'] < 25:
        base_sl = 0.01 

    if trade_type == "BUY":
        return {
            "sl": current_price * (1 - base_sl),
            "tp": current_price * 1.05 # 5% Profit target
        }
    return {"sl": None, "tp": None}
