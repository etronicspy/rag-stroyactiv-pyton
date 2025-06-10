from fastapi import APIRouter
from core.config import settings, get_vector_db_client, get_ai_client
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@router.get("/config")
async def config_status():
    """Check configuration and external services status"""
    status = {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_type": settings.DATABASE_TYPE.value,
        "ai_provider": settings.AI_PROVIDER.value,
        "services": {}
    }
    
    # Check OpenAI API
    try:
        if settings.AI_PROVIDER.value == "openai":
            async with httpx.AsyncClient() as client:
                ai_config = settings.get_ai_config()
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {ai_config['api_key']}"},
                    timeout=10
                )
                if response.status_code == 200:
                    status["services"]["openai"] = {"status": "healthy", "model": ai_config["model"]}
                else:
                    status["services"]["openai"] = {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        elif settings.AI_PROVIDER.value == "huggingface":
            # For HuggingFace, just check if model is configured
            ai_config = settings.get_ai_config()
            status["services"]["huggingface"] = {"status": "configured", "model": ai_config["model"]}
    except Exception as e:
        status["services"]["ai_provider"] = {"status": "error", "error": str(e)}
    
    # Check Qdrant
    try:
        if settings.DATABASE_TYPE.value in ["qdrant_cloud", "qdrant_local"]:
            qdrant_client = get_vector_db_client()
            collections = qdrant_client.get_collections()
            db_config = settings.get_vector_db_config()
            status["services"]["qdrant"] = {
                "status": "healthy",
                "url": db_config["url"][:50] + "..." if len(db_config["url"]) > 50 else db_config["url"],
                "collections_count": len(collections.collections)
            }
    except Exception as e:
        status["services"]["vector_db"] = {"status": "error", "error": str(e)}
    
    return status 