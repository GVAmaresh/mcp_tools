import serpapi
import asyncio
from datetime import datetime
from typing import Optional

from utils.error_handler import handle_tool_errors
from utils.errors import ValidationError, APIError
from utils.logger import log
from config import settings
from utils.cache import cached_tool
from commons import get_iata_code, find_nearest_airport, get_coordinates

# @handle_tool_errors
# @cached_tool(ttl=300) 
# async def search_flights(
#     origin: str,
#     destination: str,
#     date: str,
#     passengers: int = 1
# ) -> dict:
#     origin_iata = get_iata_code(origin)
#     destination_iata = get_iata_code(destination)

#     if not origin_iata: raise ValidationError(f"Could not find an airport for origin: '{origin}'.")
#     if not destination_iata: raise ValidationError(f"Could not find an airport for destination: '{destination}'.")

#     log.info(f"Executing REAL flight search for {origin_iata} -> {destination_iata} on {date}")
    
#     if settings.SERPAPI_API_KEY == "YOUR_API_KEY_HERE" or not settings.SERPAPI_API_KEY:
#         raise APIError("The flight search tool is not configured. Missing SERPAPI_API_KEY.")

#     try:
#         datetime.strptime(date, "%Y-%m-%d")
#     except ValueError:
#         raise ValidationError("Invalid date format. Please use YYYY-MM-DD.")

#     params = {
#         "engine": "google_flights", "api_key": settings.SERPAPI_API_KEY,
#         "departure_id": origin_iata, "arrival_id": destination_iata,
#         "outbound_date": date, "adults": passengers, "currency": "INR", "hl": "en"
#     }

#     try:
#         loop = asyncio.get_running_loop()
#         search_result = await loop.run_in_executor(None, lambda: serpapi.search(params))
#         results = search_result.as_dict()

#         if "error" in results: raise APIError(f"SerpApi error: {results['error']}")

#         flight_results = results.get('best_flights', []) + results.get('other_flights', [])
#         if not flight_results:
#             return {"success": True, "data": {"message": f"No flights found from {origin} to {destination} on {date}."}}
            
#         parsed_flights = [
#             {
#                 "price": flight.get('price'), "airline": flight['flights'][0].get('airline'),
#                 "departure_airport": flight['flights'][0]['departure_airport']['name'],
#                 "arrival_airport": flight['flights'][0]['arrival_airport']['name'],
#                 "duration_minutes": flight['flights'][0].get('duration'), "stops": len(flight['flights'][0].get('layovers', [])),
#             } for flight in flight_results if flight.get('flights')
#         ]

#         return {"success": True, "data": {"flight_count": len(parsed_flights), "flights": parsed_flights}}
#     except Exception as e:
#         log.exception(f"Unexpected flight search error: {e}")
#         raise APIError("Failed to fetch flight data.")


import asyncio
import aiohttp
from datetime import datetime
# from utils import handle_tool_errors, ValidationError, cached_tool, log, APIError
# from tools.flight_utils import get_iata_code
from config import settings

import aiohttp
import asyncio
from datetime import datetime
from config import settings
from utils.logger import log
from utils.errors import APIError, ValidationError
from utils.error_handler import handle_tool_errors
from utils.cache import cached_tool
from commons import get_iata_code

@handle_tool_errors
@cached_tool(ttl=300)
async def search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int = 1
) -> dict:
    """
    Searches for flights using the SerpAPI Google Flights endpoint.

    This function is asynchronous and uses aiohttp for non-blocking HTTP requests.
    """
    origin_iata = get_iata_code(origin)
    destination_iata = get_iata_code(destination)

    if not origin_iata:
        raise ValidationError(f"Could not find an IATA code for origin: '{origin}'.")
    if not destination_iata:
        raise ValidationError(f"Could not find an IATA code for destination: '{destination}'.")

    log.info(f"Executing flight search for {origin_iata} -> {destination_iata} on {date}")

    if not settings.SERPAPI_API_KEY or settings.SERPAPI_API_KEY == "YOUR_API_KEY_HERE":
        raise APIError("The flight search tool is not configured. Missing SERPAPI_API_KEY.")

    try:
        # Validate that the date is in the correct YYYY-MM-DD format.
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Invalid date format. Please use YYYY-MM-DD.")

    params = {
        "engine": "google_flights",
        "api_key": settings.SERPAPI_API_KEY,
        "departure_id": origin_iata,
        "arrival_id": destination_iata,
        "outbound_date": date,
        "adults": passengers,
        "currency": "INR",
        "hl": "en",
        "type": 2  # *** CORRECTED: Explicitly set to 2 for a one-way trip ***
    }

    try:
        # Set a reasonable timeout for the external API call.
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://serpapi.com/search', params=params) as response:
                if response.status != 200:
                    error_details = await response.text()
                    log.error(f"SerpAPI returned a non-200 status: {response.status}. Details: {error_details}")
                    raise APIError(f"API request failed with status {response.status}: {error_details}")

                results = await response.json()

                if "error" in results:
                    raise APIError(f"SerpAPI returned an error: {results['error']}")

                flight_results = results.get('best_flights', []) + results.get('other_flights', [])

                if not flight_results:
                    # Return a structured message when no flights are found.
                    return {
                        "success": True,
                        "data": {
                            "message": f"No flights found from {origin} to {destination} on {date}.",
                            "origin": origin,
                            "origin_iata": origin_iata,
                            "destination": destination,
                            "destination_iata": destination_iata,
                            "date": date
                        }
                    }

                parsed_flights = []
                for flight in flight_results:
                    if flight.get('flights'):
                        first_flight_leg = flight['flights'][0]
                        parsed_flights.append({
                            "price": flight.get('price'),
                            "airline": first_flight_leg.get('airline'),
                            "departure_airport": first_flight_leg['departure_airport']['name'],
                            "arrival_airport": first_flight_leg['arrival_airport']['name'],
                            "duration_minutes": first_flight_leg.get('duration'),
                            "stops": len(first_flight_leg.get('layovers', []))
                        })

                return {
                    "success": True,
                    "data": {
                        "flight_count": len(parsed_flights),
                        "flights": parsed_flights,
                        "origin": origin,
                        "destination": destination,
                        "date": date
                    }
                }

    except asyncio.TimeoutError:
        log.error("Flight search request to SerpAPI timed out.")
        raise APIError("Flight search timed out. Please try again.")
    except aiohttp.ClientError as e:
        log.exception(f"A network error occurred during flight search: {e}")
        raise APIError("A network error occurred while searching for flights.")
    except Exception as e:
        log.exception(f"An unexpected error occurred during flight search: {e}")
        raise APIError("An unexpected error occurred while fetching flight data.")
    
    
@handle_tool_errors
async def search_flights_upgraded(origin: str, destination: str, date: str, passengers: int = 1) -> dict:
    log.info(f"Creating travel plan from '{origin}' to '{destination}'")
    
    origin_iata = get_iata_code(origin)
    if not origin_iata:
        origin_airport_data = await find_nearest_airport(origin)
        origin_iata = origin_airport_data['data']['nearest_airport']['iata']
        origin_note = f"Origin '{origin}' resolved to nearest airport: {origin_iata} ({origin_airport_data['data']['nearest_airport']['name']})"
    else:
        origin_note = f"Origin '{origin}' resolved to airport: {origin_iata}"

    destination_iata = get_iata_code(destination)
    if not destination_iata:
        dest_airport_data = await find_nearest_airport(destination)
        destination_iata = dest_airport_data['data']['nearest_airport']['iata']
        destination_note = f"Destination '{destination}' resolved to nearest airport: {destination_iata} ({dest_airport_data['data']['nearest_airport']['name']})"
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
