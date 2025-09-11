from typing import Optional
from commons import get_coordinates 
from utils import handle_tool_errors, ValidationError, cached_tool,log, weather_client

@handle_tool_errors
@cached_tool(ttl=1800)
async def get_forecast(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    forecast_days: int = 3,
) -> dict:
    log.info(f"Executing get_forecast for location='{location}', lat={latitude}, lon={longitude}")

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

    if forecast_days <= 0 or forecast_days > 16:
        log.warning(f"Invalid forecast_days ({forecast_days}). Clamping to 3.")
        forecast_days = 3

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": forecast_days
    }

    log.info(f"Calling Open-Meteo API for {forecast_days}-day forecast at {resolved_location}...")
    response = await weather_client.get_json("/v1/forecast", params=params)
    
    daily_data = response.get("daily", {})
    
    forecasts = []
    if all(k in daily_data for k in ['time', 'temperature_2m_max', 'temperature_2m_min']):
        for i, date_str in enumerate(daily_data['time']):
            forecasts.append({
                "date": date_str,
                "max_temp": daily_data['temperature_2m_max'][i],
                "min_temp": daily_data['temperature_2m_min'][i],
            })

    return {
        "success": True,
        "data": {
            "location": resolved_location,
            "latitude": lat,
            "longitude": lon,
            "temperature_unit": "celsius",
            "forecasts": forecasts,
        }
    }