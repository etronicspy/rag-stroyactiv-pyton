from fastapi import APIRouter
from core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION
    }

@router.get("/config")
async def get_config():
    # Test database connection
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    try:
        await client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    finally:
        client.close()
    
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_status": db_status,
        "embedding_model": settings.EMBEDDING_MODEL
    } 