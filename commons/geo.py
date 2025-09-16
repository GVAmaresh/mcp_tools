from utils import handle_tool_errors, ValidationError, cached_tool, log,geocoding_client

@handle_tool_errors
@cached_tool(ttl=86400)
async def get_coordinates(place_name: str) -> dict:
    log.info(f"Executing get_coordinates for '{place_name}'")
    if not place_name:
        raise ValidationError("Place name must be provided.")

    params = {"name": place_name, "count": 1, "format": "json"}
    
    log.info(f"Calling Geocoding API for '{place_name}'...")
    response = await geocoding_client.get_json("/v1/search", params=params)

    print(response)
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


# @handle_tool_errors
# @cached_tool(ttl=86400)
# async def get_coordinates(place_name: str) -> dict:
#     log.info(f"Executing get_coordinates for '{place_name}'")
#     if not place_name:
#         raise ValidationError("Place name must be provided.")

#     # Try different variations of the location name
#     location_variations = [place_name]
    
#     # Split by commas and try different combinations
#     parts = [part.strip() for part in place_name.split(',')]
#     if len(parts) > 1:
#         # Try just the city name
#         location_variations.append(parts[0])
#         # Try city + country
#         if len(parts) > 2:
#             location_variations.append(f"{parts[0]}, {parts[-1]}")
#         location_variations.append(f"{parts[0]}, {parts[1]}")

#     for location_variation in location_variations:
#         params = {"name": location_variation, "count": 1, "format": "json"}
        
#         log.info(f"Calling Geocoding API for '{location_variation}'...")
#         response = await geocoding_client.get_json("/v1/search", params=params)

#         if response.get("results"):
#             place_data = response["results"][0]
            
#             location_name = place_data.get('name', 'N/A')
#             admin1 = place_data.get('admin1')
#             country = place_data.get('country')
            
#             if admin1 and country:
#                 full_location_name = f"{location_name}, {admin1}, {country}"
#             else:
#                 full_location_name = location_name

#             result_data = {
#                 "input_query": place_name,
#                 "matched_location": full_location_name,
#                 "latitude": place_data.get("latitude"),
#                 "longitude": place_data.get("longitude"),
#                 "timezone": place_data.get("timezone"),
#             }
#             log.info(f"Found coordinates for '{place_name}': {result_data}")
#             return result_data

#     # If none of the variations worked
#     raise ValidationError(f"Could not find coordinates for '{place_name}'. Please try a more specific location name.")