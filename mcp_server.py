from mcp.server.fastmcp import FastMCP
from tools import search_flights, get_current_weather, get_forecast, find_places_of_interest, search_flights_upgraded

from utils import log 

def create_mcp_app() -> FastMCP:
    mcp = FastMCP("travel-assistant")

    mcp.add_tool(search_flights, title="Search Flights", description="Search for available flights between two locations on a specific date.")
    mcp.add_tool(search_flights_upgraded, title="Search Flights Upgraded", description="Advanced flight search with enhanced features.")
    mcp.add_tool(get_current_weather, title="Get Current Weather", description="Retrieve the current weather for a given location.")
    mcp.add_tool(get_forecast, title="Get Forecast", description="Get the weather forecast for upcoming days for a specific location.")
    mcp.add_tool(find_places_of_interest, title="Find Places of Interest", description="Find nearby places of interest based on location and categories.")

    return mcp

if __name__ == "__main__":
    log.info("Starting MCP server in stdio mode...")
    mcp_instance = create_mcp_app()
    mcp_instance.run(transport="stdio")