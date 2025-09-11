import os
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from commons import get_coordinates 
from utils.error_handler import handle_tool_errors
from utils.errors import ValidationError
from utils.cache import cached_tool
from utils.logger import log
from utils.http_client import google_api_client 

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@handle_tool_errors
@cached_tool(ttl=86400) 
async def get_place_details(place_id: str) -> Dict[str, Any]:
    log.info(f"Fetching details for place_id: {place_id}")
    if not API_KEY:
        raise ValidationError("GOOGLE_MAPS_API_KEY is not set.")

    params = {
        "place_id": place_id,
        "fields": "name,rating,user_ratings_total,reviews,formatted_address,website,international_phone_number,place_id",
        "key": API_KEY,
    }
    
    response_data = await google_api_client.get_json("/details/json", params=params)

    if response_data.get("status") == "OK":
        return response_data.get("result", {})
    else:
        log.error(f"Place Details API Error: {response_data.get('status')}")
        return {}


@handle_tool_errors
async def find_places_of_interest(
    place_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    categories: Optional[List[str]] = None,
    radius: int = 15000  
) -> Dict[str, Any]:

    if not API_KEY:
        raise ValidationError("GOOGLE_MAPS_API_KEY is not set.")
        
    if not place_name and not (latitude and longitude):
        raise ValidationError("You must provide either a 'place_name' or both 'latitude' and 'longitude'.")

    search_coords = {}
    if place_name:
        coord_data = await get_coordinates(place_name)
        search_coords = {
            "latitude": coord_data["latitude"],
            "longitude": coord_data["longitude"],
            "resolved_location_name": coord_data["matched_location"]
        }
    else:
        search_coords = {"latitude": latitude, "longitude": longitude}
    
    lat, lon = search_coords["latitude"], search_coords["longitude"]
    log.info(f"Searching near coordinates: ({lat}, {lon})")

    if not categories:
        categories = ["tourist attraction"]
        log.info("No categories provided, defaulting to 'tourist attraction'.")

    search_tasks = []
    for category in categories:
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "keyword": category,
            "key": API_KEY,
        }
        search_tasks.append(google_api_client.get_json("/nearbysearch/json", params=params))
        
    search_responses = await asyncio.gather(*search_tasks)

    place_ids_to_fetch = set()
    raw_results_by_category = {}
    for category, response in zip(categories, search_responses):
        if response and response.get("status") == "OK":
            places = response.get("results", [])
            raw_results_by_category[category] = places
            for place in places:
                if place.get("place_id"):
                    place_ids_to_fetch.add(place["place_id"])

    details_tasks = [get_place_details(pid) for pid in place_ids_to_fetch]
    details_results = await asyncio.gather(*details_tasks)
    
    details_map = {result.get('place_id'): result for result in details_results if result and result.get('place_id')}

    final_categorized_places = {}
    for category, places in raw_results_by_category.items():
        category_places_list = []
        for place in places:
            place_details = details_map.get(place.get('place_id'))
            if place_details:
                combined_place = {
                    "name": place.get("name"),
                    "address": place_details.get("formatted_address", place.get("vicinity")),
                    "location": place.get("geometry", {}).get("location"),
                    "rating": place_details.get("rating", 0),
                    "total_ratings": place_details.get("user_ratings_total", 0),
                    "types": place.get("types"),
                    "website": place_details.get("website"),
                    "phone_number": place_details.get("international_phone_number"),
                    "reviews": place_details.get("reviews", [])
                }
                category_places_list.append(combined_place)
        
        final_categorized_places[category] = sorted(
            category_places_list, key=lambda p: p.get("rating", 0), reverse=True
        )

    return {
        "search_coordinates": search_coords,
        "results": final_categorized_places
    }