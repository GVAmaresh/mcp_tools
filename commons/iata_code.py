import json
from functools import lru_cache
from typing import Optional, List, Dict
from math import radians, sin, cos, sqrt, atan2

from utils.error_handler import handle_tool_errors
from utils.errors import ValidationError
from utils.http_client import geocoding_client
from utils.logger import log

# --- Airport Data Loading ---

@lru_cache(maxsize=1)
def load_airports_data() -> List[Dict]:
    """
    Loads airport data from the airports.json file.
    The result is cached in memory for efficiency.
    """
    try:
        with open("data/airports.json", "r", encoding="utf-8") as f:
            # Filter for entries that are airports and have an IATA code.
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

# --- Geocoding and Coordinate Tools ---

@handle_tool_errors
async def get_coordinates(place_name: str) -> dict:
    """
    Gets geographic coordinates (latitude, longitude) for a given place name.
    """
    log.info(f"Executing get_coordinates for '{place_name}'")
    if not place_name:
        raise ValidationError("Place name must be provided.")

    params = {"name": place_name, "count": 1, "format": "json"}
    response = await geocoding_client.get_json("/v1/search", params=params)

    if not response.get("results"):
        raise ValidationError(f"Could not find coordinates for '{place_name}'.")

    return response["results"][0]

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the distance between two lat/lon points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

# --- Primary Tool ---

@handle_tool_errors
async def find_nearest_airport(location_name: str) -> dict:
    """
    Finds the nearest commercial airport to a given location name.
    Useful for destinations that do not have their own airport.
    """
    log.info(f"Finding nearest airport for '{location_name}'")
    try:
        location_data = await get_coordinates(location_name)
    except ValidationError:
        raise ValidationError(f"Could not determine coordinates for '{location_name}'.")

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
            "query_location": location_name,
            "nearest_airport": {
                "name": closest_airport.get("name"),
                "iata": closest_airport.get("iata"),
                "city": closest_airport.get("city"),
                "country": closest_airport.get("iso"),
            },
            "distance_km": round(min_distance, 2)
        }
    }
