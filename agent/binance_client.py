import httpx

BASE = "https://data-api.binance.vision"


async def fetch_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 100):
    """Fetch klines (candlesticks) from Binance public REST API (async).

    Returns the raw klines JSON (list of lists) as returned by Binance.
    """
    url = f"{BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json() 