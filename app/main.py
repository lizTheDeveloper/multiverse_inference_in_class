"""Main FastAPI application for the Multiverse Inference Gateway.

This module initializes the FastAPI application, sets up middleware,
configures logging, initializes the database, and registers API routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.utils.config import get_settings
from app.utils.database import init_database, close_database, health_check_database
from app.utils.logger import setup_logger, get_logger
from app.services.health_checker import start_health_checker, stop_health_checker

# Initialize settings and logger
settings = get_settings()
logger = setup_logger(
    name="multiverse_gateway",
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    log_file=settings.log_file,
    max_bytes=settings.log_max_bytes,
    backup_count=settings.log_backup_count,
    enable_console=settings.enable_console_logging,
    enable_file=settings.enable_file_logging
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.
    
    This function handles startup and shutdown events for the application.
    It initializes resources on startup and cleans them up on shutdown.
    
    Args:
        app: FastAPI application instance
    
    Yields:
        None
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)
    
    logger.info(f"Host: {settings.host}:{settings.port}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Database: {settings.database_url}")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_database()
        logger.info("Database initialized successfully")
        
        # Verify database health
        db_healthy = await health_check_database()
        if not db_healthy:
            logger.error("Database health check failed!")
        else:
            logger.info("Database health check passed")
        
        # Start background health checker
        logger.info("Starting background health checker...")
        await start_health_checker()
        logger.info("Background health checker started")
        
        logger.info("Application startup complete")
        logger.info("=" * 60)
        
    except Exception as error:
        logger.critical(f"Failed to start application: {error}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down application...")
    logger.info("=" * 60)
    
    try:
        # Stop background health checker
        await stop_health_checker()
        logger.info("Health checker stopped")
        
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown complete")
        
    except Exception as error:
        logger.error(f"Error during shutdown: {error}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A distributed AI inference gateway that enables students to share and "
        "access AI models hosted on their own servers through a unified "
        "OpenAI-compatible API."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Configure CORS
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    logger.info("CORS middleware enabled")


# Health check endpoint
@app.get(
    "/health",
    tags=["System"],
    summary="Gateway health check",
    description="Check if the gateway is running and healthy",
    response_description="Health status of the gateway"
)
async def health_check() -> JSONResponse:
    """Gateway health check endpoint.
    
    This endpoint checks:
    - If the application is running
    - If the database is accessible
    
    Returns:
        JSON response with health status
    """
    # Check database health
    db_healthy = await health_check_database()
    
    health_status = {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": "healthy" if db_healthy else "unhealthy",
    }
    
    status_code = 200 if db_healthy else 503
    
    return JSONResponse(
        content=health_status,
        status_code=status_code
    )


# Root endpoint
@app.get(
    "/",
    tags=["System"],
    summary="API root",
    description="Get basic information about the API"
)
async def root() -> dict:
    """Root endpoint with basic API information.
    
    Returns:
        Basic API information
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# Register routers
from app.routers import admin
app.include_router(admin.router)

# Inference router (Phase 3)
from app.routers import inference
app.include_router(inference.router)


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )

