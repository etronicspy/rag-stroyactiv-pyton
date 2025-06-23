from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    """Standardized error response for API endpoints.

    Provides consistent error reporting across all API endpoints with structured
    error information for better client-side error handling and debugging.

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 400,
                "message": "Invalid request data",
                "details": {
                    "field": "name",
                    "error": "must not be empty"
                }
            }
        }
    )


# Default error responses map for FastAPI route decorators
ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    404: {"model": ErrorResponse, "description": "Resource Not Found"},
    429: {"model": ErrorResponse, "description": "Too Many Requests"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
} 