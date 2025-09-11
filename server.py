
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from mcp_server import create_mcp_app
from utils.errors import ValidationError
from utils.logger import log


app = FastAPI(
    title="Travel Assistant Tools API",
    description="An API for invoking backend tools for weather, flight searches, and finding places of interest.",
    version="1.0.0"
)

log.info("Creating and loading tools into MCP instance for FastAPI server...")
mcp = create_mcp_app()
log.info(f"Tools loaded successfully: {list(mcp.tools.keys())}")


class ToolCallRequest(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any] = {}

class ToolInfo(BaseModel):
    name: str
    
@app.get("/", summary="Health Check", tags=["General"])
async def read_root():
    return {"status": "ok", "message": "Travel Assistant API is running."}

@app.get("/tools", summary="List Available Tools", response_model=List[ToolInfo], tags=["Tools"])
async def list_tools():
    return [{"name": tool_name} for tool_name in mcp.tools.keys()]

@app.post("/invoke", summary="Invoke a Tool", tags=["Tools"])
async def invoke_tool(request: ToolCallRequest):
    log.info(f"Received request to invoke tool: '{request.tool_name}' with args: {request.tool_args}")

    if request.tool_name not in mcp.tools:
        log.warning(f"Tool '{request.tool_name}' not found.")
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.tool_name}' not found. Available tools: {list(mcp.tools.keys())}"
        )

    try:
        tool_function = mcp.tools[request.tool_name]
        result = await tool_function(**request.tool_args)
        return result
    except ValidationError as e:
        log.error(f"Validation error calling '{request.tool_name}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.exception(f"An unexpected error occurred in tool '{request.tool_name}': {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


if __name__ == "__main__":
    log.info("Starting FastAPI server in development mode...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)