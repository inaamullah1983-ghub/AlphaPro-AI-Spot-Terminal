import os
import json
from groq import Groq
from dotenv import load_dotenv
from agent.database import get_recent_klines, save_ai_signal
from agent.indicators import calculate_indicators

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# In agent/ai_engine.py
async def get_ai_signal(symbol: str, tech: dict, news: str):
    # Your logic lock code here...
    score = tech['python_score']
    # ... etc
    rsi = tech['rsi']
    
    if score >= 70 and rsi < 60:
        actual_signal = "BUY"
    elif score <= 30 or rsi > 70:
        actual_signal = "SELL"
    else:
        actual_signal = "HOLD"

    # --- 2. LLAMA REASONING (The Secretary) ---
    prompt = f"""
    SYSTEM: You are a Crypto Analyst. The Python Engine has decided the signal is {actual_signal}.
    DATA: Score: {score}, RSI: {rsi}, Trend: {tech['trend']}, News: {news}
    
    TASK: Write a 1-sentence technical justification for why {actual_signal} is the correct move based on the Score and RSI.
    
    JSON OUTPUT ONLY:
    {{"signal": "{actual_signal}", "confidence": 1.0, "reason": "..."}}
    """
    
    # ... your existing Groq client.chat.completions code ...




    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",  # Extremely fast
        response_format={"type": "json_object"}
    )
    
    return json.loads(chat_completion.choices[0].message.content)