from fastapi import APIRouter, HTTPException
from typing import Dict
import httpx
from core.config import settings

router = APIRouter()

@router.get("/")
async def health_check() -> Dict:
    """
    Check the health of all services
    """
    health_status = {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "openai": "unknown",
            "qdrant": "unknown"
        }
    }
    
    # Check OpenAI
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.openai.com/v1/models",
                                      headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"})
            if response.status_code == 200:
                health_status["services"]["openai"] = "healthy"
            else:
                health_status["services"]["openai"] = "unhealthy"
    except Exception as e:
        health_status["services"]["openai"] = f"error: {str(e)}"
    
    # Check Qdrant
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.QDRANT_URL}/collections",
                                      headers={"api-key": settings.QDRANT_API_KEY})
            if response.status_code == 200:
                health_status["services"]["qdrant"] = "healthy"
            else:
                health_status["services"]["qdrant"] = "unhealthy"
    except Exception as e:
        health_status["services"]["qdrant"] = f"error: {str(e)}"
    
    # If any service is unhealthy, return 503
    if any(status != "healthy" for status in health_status["services"].values()):
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status 