# api.py
import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)


class API:
    def __init__(self, api_key, is_production, debug):
        self.API_BASE_URL = "https://uexcorp.space/api/2.0"
        self.api_key = api_key
        self.is_production = is_production
        self.debug = debug

    async def fetch_data(self, endpoint, params=None):
        url = f"{self.API_BASE_URL}{endpoint}"
        logger.debug(f"API Request: GET {url} {params if params else ''}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"API Response: {data}")
                    return data
                else:
                    error_message = await response.text()
                    logger.error(f"API request failed with status {response.status}: {error_message}")
                    return []

    async def perform_trade(self, data):
        url = f"{self.API_BASE_URL}/user_trades_add/"
        logger.info(f"API Request: POST {url} {data}")
        async with aiohttp.ClientSession(headers={"secret_key": self.api_key}) as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Trade successful: {result}")
                    return result
                else:
                    error_message = await response.text()
                    logger.error(f"API request failed with status {response.status}: {error_message}")
                    return {"message": error_message}
