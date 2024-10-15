# api.py
import asyncio
import logging
import aiohttp
import json

logger = logging.getLogger(__name__)


class API:
    def __init__(self, api_key, secret_key, is_production, debug):
        self.API_BASE_URL = "https://uexcorp.space/api/2.0"
        if is_production:
            self.API_BASE_URL = "https://uexcorp.space/api/2.0"  # Replace with actual production URL

        self.api_key = api_key
        self.secret_key = secret_key
        self.is_production = is_production
        self.debug = debug
        self.session = aiohttp.ClientSession()

    def update_credentials(self, api_key, secret_key):
        """Updates the API key and secret key."""
        self.api_key = api_key
        self.secret_key = secret_key

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

    async def get_commodity_id(self, commodity_name):
        """Fetches the commodity ID based on the commodity name."""
        url = f"{self.API_BASE_URL}/commodities"  # Assuming this endpoint exists
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "secret_key": self.secret_key
        }
        params = {"name": commodity_name}

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and data.get("data"):
                        return data["data"][0].get("id_commodity")  # Adjust if needed
                else:
                    logger.error(f"Error fetching commodity ID: {response.status} - {await response.text()}")
                return None
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching commodity ID: {e}")
            return None

    async def perform_trade(self, data):
        """Performs a trade operation (buy/sell)."""
        url = f"{self.API_BASE_URL}/user_trades_add/"
        headers = {
            "Authorization": f"Bearer {self.api_key}",  # Send api_key as Bearer Token
            "secret_key": self.secret_key 
        }

        try:
            # Serialize data to JSON with double quotes
            json_data = json.dumps(data)
            async with self.session.post(url, data=json_data, headers=headers) as response:
                logger.info(f"API Request: POST {url} {json_data}")
                response.raise_for_status()  # Raise an exception for bad status codes
                return await response.json() 
        except aiohttp.ClientResponseError as e:
            logger.error(f"API request failed with status {e.status}: {e.message} - {await e.text()}")
            raise  # Re-raise the exception to be handled by the calling function
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            raise 
