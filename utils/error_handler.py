import json
from functools import wraps
from utils.logger import log
from utils.errors import CustomError

def handle_tool_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CustomError as e:
            error_message = f"Error in tool '{func.__name__}': {e.message}"
            log.error(error_message)
            return json.dumps({"success": False, "error": e.message, "type": type(e).__name__})
        except Exception:
            error_message = f"An unexpected error occurred in tool '{func.__name__}'."
            log.exception(error_message) 
            return json.dumps({"success": False, "error": "An internal server error occurred.", "type": "UnhandledException"})
    return wrapper