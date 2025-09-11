from typing import Optional
from commons import get_coordinates 
from utils import handle_tool_errors, ValidationError, cached_tool,log, weather_client

@handle_tool_errors
@cached_tool(ttl=600)
async def get_current_weather(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict:
    log.info(f"Executing get_current_weather for location='{location}', lat={latitude}, lon={longitude}")

    if location:
        log.info(f"Location name provided. Calling get_coordinates for '{location}'.")
        coords = await get_coordinates(place_name=location)
        lat, lon = coords['latitude'], coords['longitude']
        resolved_location = coords['matched_location']
    elif latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
        resolved_location = f"Lat/Lon: {lat}, {lon}"
    else:
        raise ValidationError("You must provide either a 'location' name or 'latitude' and 'longitude'.")
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true"
    }

    log.info(f"Calling Open-Meteo Weather API for current conditions at {resolved_location}...")
    response = await weather_client.get_json("/v1/forecast", params=params)

    current_weather = response.get("current_weather", {})
    
    return {
        "success": True,
        "data": {
            "location": resolved_location,
            "latitude": lat,
            "longitude": lon,
            "temperature": current_weather.get('temperature'),
            "temperature_unit": "celsius",
            "windspeed": current_weather.get('windspeed'),
            "windspeed_unit": "km/h",
            "weathercode": current_weather.get('weathercode'),
            "source": "Open-Meteo Weather API"
        }
    }