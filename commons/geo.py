# tools/places.py (Slightly modified for easier chaining)

from utils.error_handler import handle_tool_errors
from utils.errors import ValidationError
from utils.cache import cached_tool
from utils.logger import log
from utils.http_client import geocoding_client

@handle_tool_errors
@cached_tool(ttl=86400)
async def get_coordinates(place_name: str) -> dict:
    log.info(f"Executing get_coordinates for '{place_name}'")
    if not place_name:
        raise ValidationError("Place name must be provided.")

    params = {"name": place_name, "count": 1, "format": "json"}
    
    log.info(f"Calling Geocoding API for '{place_name}'...")
    response = await geocoding_client.get_json("/v1/search", params=params)

    if not response.get("results"):
        raise ValidationError(f"Could not find coordinates for '{place_name}'. Please be more specific.")

    place_data = response["results"][0]
    
    location_name = place_data.get('name', 'N/A')
    admin1 = place_data.get('admin1')
    country = place_data.get('country')
    
    if admin1 and country:
        full_location_name = f"{location_name}, {admin1}, {country}"
    else:
        full_location_name = location_name

    result_data = {
        "input_query": place_name,
        "matched_location": full_location_name,
        "latitude": place_data.get("latitude"),
        "longitude": place_data.get("longitude"),
        "timezone": place_data.get("timezone"),
    }
    log.info(f"Found coordinates for '{place_name}': {result_data}")
    return result_data