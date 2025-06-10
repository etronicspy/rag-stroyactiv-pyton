from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from api.routes import reference, health, materials, prices, search

app = FastAPI()

# Custom JSON response class to ensure UTF-8 encoding
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

# Set default response class
app.default_response_class = UTF8JSONResponse

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
app.include_router(prices.router, prefix="/api/v1/prices", tags=["prices"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Construction Materials API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    } 