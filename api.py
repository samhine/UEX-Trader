# api.py
import logging
import aiohttp
from cache_manager import CacheManager

logger = logging.getLogger(__name__)


class API:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(API, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key, secret_key, is_production, debug, cache_ttl=1800):
        if not hasattr(self, 'initialized'):  # Ensure __init__ is only called once
            self.API_BASE_URL = "https://uexcorp.space/api/2.0"
            if is_production:
                self.API_BASE_URL = "https://uexcorp.space/api/2.0"  # Replace with actual production URL
            self.api_key = api_key
            self.secret_key = secret_key
            self.session = aiohttp.ClientSession()
            self.cache = CacheManager(ttl=cache_ttl)
            self.initialized = True

    def update_api_key(self, api_key):
        self.api_key = api_key

    def update_secret_key(self, secret_key):
        self.secret_key = secret_key

    async def fetch_data(self, endpoint, params=None):
        cache_key = f"{endpoint}_{params}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_data
        url = f"{self.API_BASE_URL}{endpoint}"
        logger.debug(f"API Request: GET {url} {params if params else ''}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"API Response: {data}")
                    self.cache.set(cache_key, data)
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

    async def fetch_commodities_by_id(self, id_commodity):
        params = {'id_commodity': id_commodity}
        commodities = await self.fetch_data("/commodities_prices", params=params)
        return commodities.get("data", [])

    async def fetch_commodities_from_terminal(self, id_terminal, id_commodity=None):
        params = {'id_terminal': id_terminal}
        if id_commodity:
            params['id_commodity'] = id_commodity
        commodities = await self.fetch_data("/commodities_prices", params=params)
        return commodities.get("data", [])

    async def fetch_planets(self, system_id, planet_id=None):
        params = {'id_star_system': system_id}
        planets = await self.fetch_data("/planets", params=params)
        return [planet for planet in planets.get("data", [])
                if planet.get("is_available") == 1 and (not planet_id or planet.get("id") == planet_id)]

    async def fetch_terminals(self, system_id, planet_id=None, terminal_id=None):
        params = {'id_star_system': system_id}
        if planet_id:
            params['id_planet'] = planet_id
        terminals = await self.fetch_data("/terminals", params=params)
        return [terminal for terminal in terminals.get("data", [])
                if terminal.get("type") == "commodity" and terminal.get("is_available") == 1
                and (not terminal_id or terminal.get("id") == terminal_id)]

    async def fetch_systems_from_origin_system(self, origin_system_id, max_bounce=1):
        params = {}
        # TODO - Return systems linked to origin_system_id with a maximum of "max_bounce" hops - API does not give this for now
        systems = await self.fetch_data("/star_systems", params=params)
        return [system for system in systems.get("data", [])
                if system.get("is_available") == 1]

    async def fetch_system(self, system_id):
        params = {'id_star_system': system_id}
        systems = await self.fetch_data("/star_systems", params=params)
        return [system for system in systems.get("data", [])
                if system.get("is_available") == 1]

    async def fetch_routes(self, id_planet_origin, id_planet_destination):
        params = {'id_planet_origin': id_planet_origin}
        if id_planet_destination:
            params['id_planet_destination'] = id_planet_destination
        routes = await self.fetch_data("/commodities_routes", params=params)
        return [route for route in routes.get("data", [])
                if route.get("price_margin") > 0]

    async def perform_trade(self, data):
        """Performs a trade operation (buy/sell)."""
        url = f"{self.API_BASE_URL}/user_trades_add/"
        headers = {
            "Authorization": f"Bearer {self.api_key}",  # Send api_key as Bearer Token
            "secret_key": self.secret_key
        }
        try:
            async with self.session.post(url, data=data, headers=headers) as response:
                logger.info(f"API Request: POST {url} {data}")
                response.raise_for_status()  # Raise an exception for bad status codes
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"API request failed with status {e.status}: {e.message} - {e.request_info.url}")
            raise  # Re-raise the exception to be handled by the calling function
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            raise
