import aiohttp
import asyncio

async def fetch():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://httpbin.org/get') as response:
            print(await response.text())

asyncio.run(fetch())
