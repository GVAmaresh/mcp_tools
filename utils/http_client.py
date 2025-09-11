
import httpx
from .errors import APIError
from .logger import log

class HTTPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def get_json(self, endpoint: str, params: dict | None = None) -> dict:
        try:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()  
            return response.json()
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise APIError(f"API request failed with status {e.response.status_code}")
        except httpx.RequestError as e:
            log.error(f"Request error occurred: {e}")
            raise APIError(f"An error occurred while requesting {e.request.url}")

    async def close(self):
        await self._client.aclose()

geocoding_client = HTTPClient(base_url="https://geocoding-api.open-meteo.com")
weather_client = HTTPClient(base_url="https://api.open-meteo.com")