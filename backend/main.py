"""
Desktop Version of Pyrometer Monitor
Uses pywebview to display the application in a native window
"""

import webview
import threading
import uvicorn
import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import traceback

from app.config import get_settings
from app.api.routes import router as api_router
from app.database import test_connection, create_tables
from app.services.polling_service import polling_service
from app.services.data_retention_service import retention_service
from app.logging_config import setup_logging

# Initialize centralized logging system
log_dir = setup_logging()

# Get logger for main module
logger = logging.getLogger(__name__)

settings = get_settings()

# Global flag to track if backend is ready
backend_ready = False


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    """
    global backend_ready

    # STARTUP
    logger.info("=" * 80)
    logger.info(f"{settings.app_name} STARTING UP...")
    logger.info(f"Server running in {'DEBUG' if settings.debug else 'PRODUCTION'} mode")
    logger.info(f"Log files location: {log_dir.absolute()}")
    logger.info("=" * 80)

    # Test database connection
    logger.info("Testing database connection...")
    try:
        if test_connection():
            logger.info("Database connected successfully!")
            create_tables()
        else:
            logger.error("Database connection failed!")
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)

    # Start polling service
    logger.info("Starting polling service...")
    try:
        await polling_service.start()
        logger.info("Polling service started successfully!")
    except Exception as e:
        logger.error(f"Failed to start polling service: {e}", exc_info=True)

    # Start data retention service
    logger.info("Starting data retention service...")
    try:
        await retention_service.start()
        logger.info("Data retention service started successfully!")
    except Exception as e:
        logger.error(f"Failed to start retention service: {e}", exc_info=True)

    # Mark backend as ready
    backend_ready = True
    logger.info("Backend is ready!")

    yield  # Application runs here

    # SHUTDOWN
    logger.info("=" * 80)
    logger.info("SHUTTING DOWN SERVER...")
    logger.info("=" * 80)

    # Stop data retention service
    logger.info("Stopping data retention service...")
    try:
        await retention_service.stop()
        logger.info("Data retention service stopped successfully!")
    except Exception as e:
        logger.error(f"Error stopping retention service: {e}", exc_info=True)

    # Stop polling service
    logger.info("Stopping polling service...")
    try:
        await polling_service.stop()
        logger.info("Polling service stopped successfully!")
    except Exception as e:
        logger.error(f"Error stopping polling service: {e}", exc_info=True)

    logger.info("Server shutdown complete")
    logger.info("=" * 80)


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="Modbus RS485 Temperature Monitoring System - Desktop Version",
    version="1.0.0",
    lifespan=lifespan
)


# API Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all API requests and responses
    """
    import time

    # Skip logging for WebSocket upgrades
    if request.url.path == "/api/ws":
        return await call_next(request)

    # Log request
    start_time = time.time()
    client_ip = request.client.host if request.client else "Unknown"

    logger.info(f"API Request: {request.method} {request.url.path} from {client_ip}")

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(f"API Response: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s")

        return response

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"API Request FAILED: {request.method} {request.url.path} - Duration: {duration:.3f}s - Error: {e}", exc_info=True)
        raise


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch and log all unhandled exceptions
    """
    logger.error("=" * 80)
    logger.error("UNHANDLED EXCEPTION OCCURRED")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Client: {request.client.host if request.client else 'Unknown'}")
    logger.error(f"Exception: {type(exc).__name__}: {str(exc)}")
    logger.error("Traceback:")
    logger.error(traceback.format_exc())
    logger.error("=" * 80)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "type": type(exc).__name__
        }
    )


# Include API routes
app.include_router(api_router)


# Mount static files (frontend build)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    # PyInstaller puts data files in _internal folder
    base_dir = os.path.dirname(sys.executable)
    static_dir = os.path.join(base_dir, "_internal", "frontend")
    # Fallback to direct path if _internal doesn't exist (onefile mode)
    if not os.path.exists(static_dir):
        static_dir = os.path.join(base_dir, "frontend")
else:
    # Running in development
    static_dir = os.path.join(os.path.dirname(__file__), "frontend")

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    logger.info(f"Serving frontend from: {static_dir}")
else:
    logger.warning(f"Frontend directory not found: {static_dir}")


def start_backend_server():
    """
    Start the FastAPI backend server in a separate thread
    """
    logger.info(f"Starting Uvicorn server on {settings.server_host}:{settings.server_port}...")
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="warning"
    )


def main():
    """
    Main entry point for the desktop application
    """
    # Start backend server in a separate thread
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()

    # Wait a bit for the backend to start
    import time
    max_wait = 10  # seconds
    waited = 0
    while not backend_ready and waited < max_wait:
        time.sleep(0.5)
        waited += 0.5

    # Create pywebview window
    logger.info("Creating desktop window...")
    window = webview.create_window(
        title=settings.app_name,
        url=f"http://{settings.server_host}:{settings.server_port}",
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(1000, 700)
    )

    # Start the webview
    logger.info("Starting webview...")
    webview.start(debug=settings.debug)

    # When window is closed, the application exits
    logger.info("Desktop window closed. Application exiting...")


if __name__ == "__main__":
    main()
