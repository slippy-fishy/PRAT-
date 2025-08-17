"""
Main FastAPI application for PRAT
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.api.routes import api_router
from app.utils.logging import setup_logging
from app.api.endpoints import invoices, purchase_orders, folder_monitoring

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="AI-powered invoice processing system for automated payment approval",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if settings.log_level == "DEBUG" else None,
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.project_name, "version": "1.0.0"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that serves the main HTML page"""
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")

@app.get("/test-style")
async def test_style():
    """Test style page endpoint"""
    from fastapi.responses import FileResponse
    return FileResponse("app/static/test_style.html")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
