class CustomError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self):
        return f"[Error {self.status_code}] {self.message}"

class APIError(CustomError):
    def __init__(self, message: str = "External API call failed."):
        super().__init__(message, status_code=503)

class ValidationError(CustomError):
    def __init__(self, message: str = "Invalid input provided."):
        super().__init__(message, status_code=400)

class ToolExecutionError(CustomError):
    def __init__(self, message: str = "Tool failed during execution."):
        super().__init__(message, status_code=500) 