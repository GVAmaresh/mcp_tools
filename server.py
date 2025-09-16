
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import json

from mcp_server import create_mcp_app
from utils import ValidationError, log


app = FastAPI(
    title="Travel Assistant Tools API",
    description="An API for invoking backend tools for weather, flight searches, and finding places of interest.",
    version="1.0.0"
)

log.info("Creating and loading tools into MCP instance for FastAPI server...")
mcp = create_mcp_app()

try:
    tools_list = mcp.list_tools() 
    print("Registered tools:")
    for tool_name in tools_list:
        print("-", tool_name)
except Exception as e:
    print("Error fetching tools:", e)
# log.info(f"Tools loaded successfully: {list(mcp.tools.keys())}")


class ToolCallRequest(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any] = {}

class ToolInfo(BaseModel):
    name: str
    
@app.get("/tools")
async def get_tools():
    tools_list = await mcp.list_tools()  
    filtered_tools = [
        {
            "name":tool.name,
            "title": tool.title, 
            "description": tool.description
        }
        for tool in tools_list
    ]
    return filtered_tools


@app.get("/", summary="Health Check", tags=["General"])
async def read_root():
    return {"status": "ok", "message": "Travel Assistant API is running."}

@app.get("/tools", summary="List Available Tools", response_model=List[ToolInfo], tags=["Tools"])
async def list_tools():
    tools_list = mcp.tool() 
    return [{"name": tool_name} for tool_name in tools_list]

@app.post("/invoke", summary="Invoke a Tool", tags=["Tools"])
async def invoke_tool(request: ToolCallRequest):
    log.info(f"Received request to invoke tool: '{request.tool_name}' with args: {request.tool_args}")
    available_tools = await get_tools()
    tools_name = [tool["name"] for tool in available_tools]
    print(tools_name)
    if request.tool_name not in tools_name:
        log.warning(f"Tool '{request.tool_name}' not found.")
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.tool_name}' not found. Available tools: {list(mcp.tools.keys())}"
        )

    try:
        response = await mcp.call_tool(request.tool_name, request.tool_args)
        # return {response}
        
        # response = await mcp.call_tool(request.tool_name, request.tool_args)
        
        # Extract result from different possible response formats
        def extract_result(obj):
            """Recursively extract text content from MCP response objects"""
            if hasattr(obj, 'text') and obj.text:
                try:
                    import json
                    return json.loads(obj.text)
                except json.JSONDecodeError:
                    return obj.text
            elif hasattr(obj, 'content'):
                for item in obj.content:
                    result = extract_result(item)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = extract_result(item)
                    if result is not None:
                        return result
            elif hasattr(obj, '__dict__'):
                for attr_name, attr_value in obj.__dict__.items():
                    if attr_name not in ['_meta', 'annotations']:  
                        result = extract_result(attr_value)
                        if result is not None:
                            return result
            return None
        
        result = extract_result(response)
        
        if result is not None:
            return result
        
        return {"status": "success", "message": "Tool executed successfully", "raw_response": str(response)}
    except ValidationError as e:
        log.error(f"Validation error calling '{request.tool_name}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.exception(f"An unexpected error occurred in tool '{request.tool_name}': {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")






# @app.post("/invoke", summary="Invoke a Tool", tags=["Tools"])
# async def invoke_tool(request: ToolCallRequest):
#     log.info(f"Received request to invoke tool: '{request.tool_name}' with args: {request.tool_args}")
#     available_tools = await get_tools()
#     tools_name = [tool["name"] for tool in available_tools]
    
#     if request.tool_name not in tools_name:
#         log.warning(f"Tool '{request.tool_name}' not found.")
#         raise HTTPException(
#             status_code=404,
#             detail=f"Tool '{request.tool_name}' not found. Available tools: {tools_name}"
#         )

#     try:
#         response = await mcp.call_tool(request.tool_name, request.tool_args)
        
#         # Handle the case where response is a list (as seen in the previous error)
#         if isinstance(response, list):
#             log.info(f"Response is a list with {len(response)} items")
#             for item in response:
#                 log.info(f"List item type: {type(item)}")
#                 if hasattr(item, 'text') and item.text:
#                     log.info(f"List item text: {item.text}")
#                     try:
#                         result = json.loads(item.text)
#                         return result
#                     except json.JSONDecodeError:
#                         return {"result": item.text}
        
#         # Handle TextContent objects directly
#         elif hasattr(response, 'text') and response.text:
#             log.info(f"Response text: {response.text}")
#             try:
#                 return json.loads(response.text)
#             except json.JSONDecodeError:
#                 return {"result": response.text}
        
#         # Handle other cases
#         elif isinstance(response, (dict, list)):
#             return response
        
#         else:
#             return {"status": "success", "message": "Tool executed successfully", "raw_response": str(response)}


#     except ValidationError as e:
#         log.error(f"Validation error calling '{request.tool_name}': {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         log.exception(f"An unexpected error occurred in tool '{request.tool_name}': {e}")
#         raise HTTPException(status_code=500, detail="An internal server error occurred.")


if __name__ == "__main__":
    log.info("Starting FastAPI server in development mode...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
    