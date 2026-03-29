import asyncio
import json
import websockets

WS_BASE = "wss://stream.binance.com:9443"  # Standard Production URL


async def _listen(symbol: str, interval: str, handler):
    """Internal listener with simple reconnect/backoff logic.

    Handler is an async callable accepting the parsed JSON message.
    """
    backoff = 1
    while True:
        stream = f"{symbol.lower()}@kline_{interval}"
        url = f"{WS_BASE}/ws/{stream}"
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                backoff = 1
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                    except Exception:
                        continue
                    try:
                        await handler(data)
                    except Exception:
                        # handler errors should not stop the loop
                        continue
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


def start_stream(symbol: str, interval: str, handler):
    """Schedule the stream listener in the running event loop and return the Task."""
    loop = asyncio.get_event_loop()
    return loop.create_task(_listen(symbol, interval, handler))
