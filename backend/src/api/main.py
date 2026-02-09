"""
TrendMuse API - Fashion Design AI Agent

Main FastAPI application for trend scanning, design generation, and sketch conversion.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from src.core.config import get_settings
from src.api.routes import scanner, generator, converter, trends, discovery
from src.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    settings = get_settings()
    print(f"🎨 TrendMuse starting...")
    print(f"   Demo mode: {settings.demo_mode}")
    print(f"   Data directory: {settings.data_dir}")
    
    yield
    
    # Shutdown
    print("👋 TrendMuse shutting down...")


# Create FastAPI app
app = FastAPI(
    title="TrendMuse API",
    description="""
    Fashion Design AI Agent API
    
    ## Features
    
    - **Trend Scanner**: Scrape fashion e-commerce sites for trending items
    - **Design Generator**: Generate AI-powered design variations  
    - **Sketch Converter**: Convert photos to fashion sketches
    
    ## Demo Mode
    
    The API runs in demo mode by default, using sample fashion data and 
    placeholder image generation. To enable real AI features:
    
    1. Set `REPLICATE_API_TOKEN` environment variable
    2. The API will automatically switch to production mode
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(scanner.router, prefix="/api")
app.include_router(generator.router, prefix="/api")
app.include_router(converter.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health status"""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        demo_mode=settings.demo_mode
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint"""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Fashion Design AI Agent",
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
        "endpoints": {
            "scanner": "/api/scanner",
            "generator": "/api/generator",
            "converter": "/api/converter",
            "health": "/health"
        }
    }


# API overview
@app.get("/api", tags=["Root"])
async def api_overview():
    """API overview and available endpoints"""
    return {
        "scanner": {
            "POST /api/scanner/scan": "Scan a fashion website",
            "GET /api/scanner/items": "Get scanned items",
            "GET /api/scanner/analysis": "Get trend analysis",
            "POST /api/scanner/demo": "Load demo data"
        },
        "generator": {
            "POST /api/generator/generate": "Generate design variations",
            "GET /api/generator/designs": "Get generated designs",
            "GET /api/generator/styles": "Get available styles"
        },
        "converter": {
            "POST /api/converter/convert": "Convert image to sketch",
            "GET /api/converter/sketches": "Get converted sketches",
            "GET /api/converter/styles": "Get sketch styles"
        },
        "trends": {
            "GET /api/trends/stats": "Get database statistics",
            "GET /api/trends/products": "Query products with filters",
            "GET /api/trends/summary": "Get trend dashboard summary",
            "GET /api/trends/price-distribution": "Get price distribution data",
            "GET /api/trends/top-colors": "Get most common colors",
            "GET /api/trends/top-tags": "Get most common tags"
        }
    }


# Mount static files for serving generated images
try:
    settings = get_settings()
    app.mount("/api/sketches", StaticFiles(directory=str(settings.sketches_dir)), name="sketches")
    app.mount("/api/generated", StaticFiles(directory=str(settings.generated_dir)), name="generated")
except Exception as e:
    print(f"Could not mount static files: {e}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
