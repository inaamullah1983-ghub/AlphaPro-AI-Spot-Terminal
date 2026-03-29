import pandas as pd
import numpy as np

def calculate_indicators(klines_rows):
    # We need at least 30 candles for stable math, 50 is better for Fibonacci
    if not klines_rows or len(klines_rows) < 30:
        return None

    # 1. DATA PREPARATION (The Scientist's Foundation)
    df = pd.DataFrame([row[:8] for row in klines_rows], 
                      columns=['id', 'symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])

    # 2. MOMENTUM: RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))

    # 3. TREND: EMA CROSS (9/21 Scalping Logic)
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

    # 4. VOLATILITY: BOLLINGER BANDS (The "Walls")
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['stddev'] = df['close'].rolling(window=20).std()
    df['upper_bb'] = df['sma20'] + (df['stddev'] * 2)
    df['lower_bb'] = df['sma20'] - (df['stddev'] * 2)

    # 5. GEOMETRY: FIBONACCI (Historical Support)
    period_high = df['high'].max()
    period_low = df['low'].min()
    fib_618 = period_high - (0.618 * (period_high - period_low))

    # --- THE "LOGIC LOCK" SCORING ENGINE (The Quant's Alpha) ---
    latest = df.iloc[-1]
    score = 0
    
    # Factor A: Trend (Max 30) - Is the price above the 21-EMA?
    if latest['close'] > latest['ema21']: score += 30
    
    # Factor B: RSI (Max 20) - Is it oversold (Buy) or overbought (Sell)?
    if latest['rsi'] < 35: score += 20
    elif latest['rsi'] > 65: score -= 20
    
    # Factor C: Volatility (Max 20) - Did we hit the "Lower Wall"?
    if latest['close'] < latest['lower_bb']: score += 20
    elif latest['close'] > latest['upper_bb']: score -= 20
    
    # Factor D: Geometry (Max 30) - Are we near the "Golden Pocket"?
    # If price is within 0.2% of the 0.618 Fib level
    if abs(latest['close'] - fib_618) / fib_618 < 0.002: score += 30

    # 6. RETURN COMPREHENSIVE DATA (Scientist & Quant View)
    return {
        "python_score": score,
        "rsi": round(latest['rsi'], 2),
        "trend": "BULLISH" if latest['close'] > latest['ema21'] else "BEARISH",
        "ema9": round(latest['ema9'], 2),
        "ema21": round(latest['ema21'], 2),
        "upper_bb": round(latest['upper_bb'], 2),
        "lower_bb": round(latest['lower_bb'], 2),
        "fib_618": round(fib_618, 2),
        "close": latest['close']
    }