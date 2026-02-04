"""Main FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import api_router
from app.config import settings
from app.pages import page_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup: Initialize database tables
    from app.database import init_db
    await init_db()
    print("✓ Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Danish Online Grocery Marketplace - Phase 1 MVP",
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Get base directory
BASE_DIR = Path(__file__).resolve().parent

# Mount static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include routers
app.include_router(api_router)
app.include_router(page_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 page."""
    if request.url.path.startswith("/api/"):
        return {"detail": "Not found"}

    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 page."""
    if request.url.path.startswith("/api/"):
        return {"detail": "Internal server error"}

    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500,
    )
