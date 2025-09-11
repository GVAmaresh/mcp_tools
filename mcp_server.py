from mcp.server.fastmcp import FastMCP
from tools import search_flights, get_current_weather, get_forecast, find_places_of_interest, search_flights_upgraded

from utils.logger import log 

def create_mcp_app() -> FastMCP:
    mcp = FastMCP("travel-assistant")

    mcp.add_tool(search_flights)
    mcp.add_tool(search_flights_upgraded)
    mcp.add_tool(get_current_weather) 
    mcp.add_tool(get_forecast)
    mcp.add_tool(find_places_of_interest)

    return mcp

if __name__ == "__main__":
    log.info("Starting MCP server in stdio mode...")
    mcp_instance = create_mcp_app()
    mcp_instance.run(transport="stdio")