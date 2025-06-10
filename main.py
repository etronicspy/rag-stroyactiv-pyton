from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from core.config import settings
from core.models.materials import Material, Category, Unit
from api.routes import reference, search, prices, health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(prices.router, prefix="/api/v1/prices", tags=["prices"])

@app.on_event("startup")
async def startup_event():
    # Initialize MongoDB connection
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize Beanie with the MongoDB client
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            Material,
            Category,
            Unit
        ]
    )

@app.get("/")
async def root():
    return {
        "message": "Welcome to Construction Materials API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    } 