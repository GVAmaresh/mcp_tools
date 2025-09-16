import json
from functools import wraps
from utils.logger import log
from utils.errors import CustomError  
from pydantic import ValidationError

def handle_tool_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            raise e
        except CustomError as e:
            error_message = f"A known error occurred in tool '{func.__name__}': {e.message}"
            log.error(error_message)
            return {
                "success": False, 
                "error": e.message, 
                "type": type(e).__name__
            }
        except Exception as e:
            error_message = f"An unexpected error occurred in tool '{func.__name__}'."
            log.exception(error_message)
            
            return {
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}",
                "type": type(e).__name__
            }
    return wrapper