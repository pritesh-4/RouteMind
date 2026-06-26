"""
Main application entry point for RouteMind Backend.
Configures CORS, registers API routers, sets up basic logging, and defines lifecycle events.
"""

from contextlib import asynccontextmanager
import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.errors import BaseRouteMindError

# Setup basic logging configuration as per standard practices
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("routemind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for application startup and shutdown.
    Logs provider availability at startup for hackathon readiness.
    """
    logger.info("Starting up RouteMind Backend...")
    logger.info("Provider Status:")

    from app.services import ProviderManager
    from app.services.health_monitor import health_monitor

    mgr = ProviderManager()
    mgr.log_provider_status()

    # Start the background health tracking
    await health_monitor.start()

    yield
    # Stop background health tracking
    await health_monitor.stop()
    logger.info("Shutting down RouteMind Backend...")


# Initialize FastAPI application with centralized configuration metadata
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Intelligent AI Orchestration and Routing Platform API.",
    lifespan=lifespan,
)

# Custom Global Exception Handlers

@app.exception_handler(BaseRouteMindError)
async def routemind_exception_handler(request: Request, exc: BaseRouteMindError):
    return JSONResponse(
        status_code=400 if exc.error_code in ("VALIDATION_ERROR", "ROUTING_ERROR") else 500,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "fallback_used": True,
            "provider": exc.provider,
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": str(exc),
            "fallback_used": False,
            "provider": "system",
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception caught by middleware: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred.",
            "fallback_used": False,
            "provider": "system",
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
        }
    )

# Configure CORS Middleware using settings defined in environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router, tags=["System"])
app.include_router(chat_router, tags=["Chat"])
