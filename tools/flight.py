import serpapi
import json
import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Optional, List, Dict
from math import radians, sin, cos, sqrt, atan2

from utils.error_handler import handle_tool_errors
from utils.errors import ValidationError, APIError
from utils.http_client import geocoding_client
from utils.logger import log
from config import settings
from utils.cache import cached_tool

@lru_cache(maxsize=1)
def load_airports_data() -> List[Dict]:
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
    dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
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
    full_location_name = f"{place_data.get('name', '')}, {place_data.get('admin1', '')}, {place_data.get('country', '')}".strip(', ')

    return {
        "input_query": place_name,
        "matched_location": full_location_name,
        "latitude": place_data.get("latitude"),
        "longitude": place_data.get("longitude"),
    }

@handle_tool_errors
@cached_tool(ttl=300) 
async def search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int = 1
) -> dict:
    origin_iata = get_iata_code(origin)
    destination_iata = get_iata_code(destination)

    if not origin_iata: raise ValidationError(f"Could not find an airport for origin: '{origin}'.")
    if not destination_iata: raise ValidationError(f"Could not find an airport for destination: '{destination}'.")

    log.info(f"Executing REAL flight search for {origin_iata} -> {destination_iata} on {date}")
    
    if settings.SERPAPI_API_KEY == "YOUR_API_KEY_HERE":
        raise APIError("The flight search tool is not configured. Missing API key.")

    try:
        outbound_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError("Invalid date format. Please use YYYY-MM-DD.")

    params = {
        "engine": "google_flights", "api_key": settings.SERPAPI_API_KEY,
        "departure_id": origin_iata, "arrival_id": destination_iata,
        "outbound_date": outbound_date, "adults": passengers, "currency": "INR", "hl": "en"
    }

    try:
        search_result = await asyncio.to_thread(serpapi.search, params)
        results = search_result.as_dict()

        if "error" in results: raise APIError(f"SerpApi error: {results['error']}")

        flight_results = results.get('best_flights', []) + results.get('other_flights', [])
        if not flight_results:
            return {"success": True, "data": {"message": f"No flights found from {origin} to {destination} on {date}."}}
            
        parsed_flights = [
            {
                "price": flight.get('price'), "airline": flight['flights'][0].get('airline'),
                "departure_airport": flight['flights'][0]['departure_airport']['name'],
                "arrival_airport": flight['flights'][0]['arrival_airport']['name'],
                "duration_minutes": flight['flights'][0].get('duration'), "stops": flight['flights'][0].get('stops', 0),
            } for flight in flight_results if flight.get('flights')
        ]

        return {"success": True, "data": {"flight_count": len(parsed_flights), "flights": parsed_flights}}
    except Exception as e:
        log.exception(f"Unexpected flight search error: {e}")
        raise APIError("Failed to fetch flight data.")

@handle_tool_errors
async def find_nearest_airport(location_name: str) -> dict:
    """
    Finds the nearest commercial airport to a location (e.g., a city without an airport).
    """
    log.info(f"Finding nearest airport for '{location_name}'")
    location_data = await get_coordinates(location_name)
    loc_lat, loc_lon = location_data.get("latitude"), location_data.get("longitude")

    if loc_lat is None or loc_lon is None:
        raise ValidationError(f"Could not get valid coordinates for '{location_name}'.")

    airports, closest_airport, min_distance = load_airports_data(), None, float('inf')
    if not airports: raise APIError("Airport data is not available for searching.")

    for airport in airports:
        dist = _haversine_distance(loc_lat, loc_lon, float(airport["lat"]), float(airport["lon"]))
        if dist < min_distance:
            min_distance, closest_airport = dist, airport

    if not closest_airport: raise ValidationError(f"Could not find any nearby airports for '{location_name}'.")

    return {
        "success": True,
        "data": {
            "query_location": location_name,
            "nearest_airport": { "name": closest_airport.get("name"), "iata": closest_airport.get("iata"), "city": closest_airport.get("city") },
            "distance_km": round(min_distance, 2)
        }
    }


@handle_tool_errors
async def search_flights_upgraded(origin: str, destination: str, date: str, passengers: int = 1) -> dict:
    log.info(f"Creating travel plan from '{origin}' to '{destination}'")
    
    origin_iata = get_iata_code(origin)
    if not origin_iata:
        origin_airport_data = await find_nearest_airport(origin)
        origin_iata = origin_airport_data['data']['nearest_airport']['iata']
        origin_note = f"Origin '{origin}' resolved to nearest airport: {origin_iata}"
    else:
        origin_note = f"Origin '{origin}' is an airport: {origin_iata}"

    destination_iata = get_iata_code(destination)
    if not destination_iata:
        dest_airport_data = await find_nearest_airport(destination)
        destination_iata = dest_airport_data['data']['nearest_airport']['iata']
        destination_note = f"Destination '{destination}' resolved to nearest airport: {destination_iata}"
    else:
        destination_note = f"Destination '{destination}' is an airport: {destination_iata}"

    log.info(f"Proceeding to search flights from {origin_iata} to {destination_iata}.")
    flight_results = await search_flights(origin_iata, destination_iata, date, passengers)

    if not flight_results.get("success"): raise APIError("Flight search sub-task failed.")

    return {
        "success": True,
        "data": {
            "plan_summary": {"origin_resolution": origin_note, "destination_resolution": destination_note},
            "flight_details": flight_results['data']
        }
    }
