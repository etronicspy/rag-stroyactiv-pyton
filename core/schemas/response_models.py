from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    """Standardized error response for API endpoints.

    Args:
        code: HTTP status code returned by the server.
        message: Human-readable error description.
        details: Optional additional information (e.g., validation errors).

    Example:
        {
            "code": 400,
            "message": "Invalid request data",
            "details": {
                "field": "name",
                "error": "must not be empty"
            }
        }
    """

    code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# Default error responses map for FastAPI route decorators
ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    404: {"model": ErrorResponse, "description": "Resource Not Found"},
    429: {"model": ErrorResponse, "description": "Too Many Requests"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
} 