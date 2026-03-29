import httpx

# Replace with your actual API key later
API_KEY = "e197d0aff8a7b8619109ed8330273dae79b27bd6" 

async def get_market_sentiment(symbol="BTC"):
    """Fetches the latest news headlines for a specific coin."""
    url = f"https://cryptopanic.com{API_KEY}&currencies={symbol}&kind=news"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            # Get the top 5 headlines
            headlines = [post['title'] for post in data['results'][:5]]
            return " | ".join(headlines)
    except Exception as e:
        return "No recent news found."
