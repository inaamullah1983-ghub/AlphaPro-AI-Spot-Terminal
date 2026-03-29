import asyncio
import json
from agent.binance_client import fetch_klines


async def main():
    data = await fetch_klines('BTCUSDT', '1m', 3)
    print('received', len(data), 'klines')
    print(json.dumps(data[0], indent=2)[:1000])


if __name__ == '__main__':
    asyncio.run(main())
