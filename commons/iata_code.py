import json
from functools import lru_cache
from typing import Optional, List, Dict
from math import radians, sin, cos, sqrt, atan2

from utils.error_handler import handle_tool_errors
from utils.errors import ValidationError
from utils.http_client import geocoding_client
from utils.logger import log
from utils.cache import cached_tool


@lru_cache(maxsize=1)
def load_airports_data() -> List[Dict]:
    """
    Loads airport data from the airports.json file.
    The result is cached in memory for efficiency.
    """
    try:
        with open("data/airports.json", "r", encoding="utf-8") as f:
            return [
                airport for airport in json.load(f) 
                if airport.get("iata") and airport.get("type") == "airport"
            ]
    except FileNotFoundError:
        log.warning("data/airports.json not found. IATA code lookup will be limited.")
        return []
    except json.JSONDecodeError:
        log.error("Failed to decode data/airports.json.")
        return []

def get_iata_code(location: str) -> Optional[str]:
    if len(location) == 3 and location.isalpha() and location.isupper():
        return location

    airports = load_airports_data()
    search_term = location.lower()
    for airport in airports:
        if (airport.get('city') and search_term == airport['city'].lower()) or \
           (airport.get('name') and search_term == airport['name'].lower()):
            log.info(f"Resolved exact match '{location}' to IATA code '{airport['iata']}'.")
            return airport['iata']
    for airport in airports:
        if airport.get('name') and search_term in airport['name'].lower():
            log.info(f"Resolved partial match '{location}' to IATA code '{airport['iata']}'.")
            return airport['iata']
            
    log.warning(f"Could not resolve '{location}' to an IATA code.")
    return None


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  
    
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

@handle_tool_errors
@cached_tool(ttl=86400) 
async def get_coordinates(place_name: str) -> dict:
    log.info(f"Executing get_coordinates for '{place_name}'")
    if not place_name:
        raise ValidationError("Place name must be provided.")

    params = {"name": place_name, "count": 1, "format": "json"}
    response = await geocoding_client.get_json("/v1/search", params=params)

    if not response.get("results"):
        raise ValidationError(f"Could not find coordinates for '{place_name}'.")

    place_data = response["results"][0]
    full_location_name = ", ".join(filter(None, [
        place_data.get('name'),
        place_data.get('admin1'),
        place_data.get('country')
    ]))

    return {
        "input_query": place_name,
        "matched_location": full_location_name,
        "latitude": place_data.get("latitude"),
        "longitude": place_data.get("longitude"),
    }


@handle_tool_errors
async def find_nearest_airport(location_name: str) -> dict:
    log.info(f"Finding nearest airport for '{location_name}'")
    
    location_data = await get_coordinates(location_name)
    loc_lat = location_data.get("latitude")
    loc_lon = location_data.get("longitude")

    if loc_lat is None or loc_lon is None:
        raise ValidationError(f"Could not get valid coordinates for '{location_name}'.")

    airports = load_airports_data()
    if not airports:
        raise ValidationError("Airport data is not available for searching.")

    closest_airport = None
    min_distance = float('inf')

    for airport in airports:
        airport_lat = airport.get("lat")
        airport_lon = airport.get("lon")
        if not airport_lat or not airport_lon:
            continue

        distance = _haversine_distance(loc_lat, loc_lon, float(airport_lat), float(airport_lon))
        
        if distance < min_distance:
            min_distance = distance
            closest_airport = airport

    if not closest_airport:
        raise ValidationError(f"Could not find any nearby airports for '{location_name}'.")

    return {
        "success": True,
        "data": {
            "query_location": location_data['matched_location'],
            "nearest_airport": {
                "name": closest_airport.get("name"),
                "iata": closest_airport.get("iata"),
                "city": closest_airport.get("city"),
                "country": closest_airport.get("iso"),
            },
            "distance_km": round(min_distance, 2)
        }
    }