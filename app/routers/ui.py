"""UI router for serving web interface pages.

This module implements all the web UI routes that serve HTML templates
for the dashboard, registration forms, model views, and inference testing.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["ui"])

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Root endpoint - redirect to dashboard.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Redirect to dashboard page
    """
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page.
    
    Displays overview of all registered servers, health stats, and quick actions.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTML response with dashboard page
    """
    logger.info("Serving dashboard page")
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Serve the server registration form page.
    
    Provides form for registering a new model server.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTML response with registration form
    """
    logger.info("Serving registration form page")
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@router.get("/server/{registration_id}", response_class=HTMLResponse)
async def server_detail(request: Request, registration_id: str):
    """Serve the server detail page.
    
    Displays detailed information about a specific registered server,
    including health history, metadata, and action buttons.
    
    Args:
        request: FastAPI Request object
        registration_id: Unique registration ID of the server
        
    Returns:
        HTML response with server detail page
    """
    logger.info(f"Serving server detail page for: {registration_id}")
    return templates.TemplateResponse(
        "server_detail.html",
        {"request": request, "registration_id": registration_id}
    )


@router.get("/server/{registration_id}/edit", response_class=HTMLResponse)
async def server_edit(request: Request, registration_id: str):
    """Serve the server edit form page.
    
    Provides form for editing an existing server registration.
    
    Args:
        request: FastAPI Request object
        registration_id: Unique registration ID of the server
        
    Returns:
        HTML response with server edit form
    """
    logger.info(f"Serving server edit page for: {registration_id}")
    return templates.TemplateResponse(
        "server_edit.html",
        {"request": request, "registration_id": registration_id}
    )


@router.get("/models", response_class=HTMLResponse)
async def models_page(request: Request):
    """Serve the models list page.
    
    Displays all available models grouped with their hosting servers.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTML response with models list page
    """
    logger.info("Serving models list page")
    return templates.TemplateResponse(
        "models.html",
        {"request": request}
    )


@router.get("/test", response_class=HTMLResponse)
async def inference_test_page(request: Request):
    """Serve the inference test interface page.
    
    Provides interactive interface for testing model inference requests
    with streaming support.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTML response with inference test page
    """
    logger.info("Serving inference test page")
    return templates.TemplateResponse(
        "inference_test.html",
        {"request": request}
    )


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Serve the logs viewer page (optional feature).
    
    Displays recent application logs in a searchable interface.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTML response with logs viewer page
    """
    logger.info("Serving logs viewer page")
    return templates.TemplateResponse(
        "logs.html",
        {"request": request}
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Serve the settings page (optional feature).
    
    Provides interface for configuring gateway settings.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTML response with settings page
    """
    logger.info("Serving settings page")
    return templates.TemplateResponse(
        "settings.html",
        {"request": request}
    )

