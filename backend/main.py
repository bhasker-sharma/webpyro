from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import traceback
from datetime import datetime

from app.config import get_settings
from app.api.routes import router as api_router
from app.database import test_connection, create_tables
from app.services.polling_service import polling_service
from app.services.data_retention_service import retention_service
from app.services.log_retention_service import LogRetentionService
from app.logging_config import setup_logging  # Import centralized logging

# Initialize centralized logging system
log_dir = setup_logging()

# Initialize log retention service
log_retention_service = LogRetentionService(log_dir)

# Get logger for main module
logger = logging.getLogger(__name__)

settings = get_settings()

# Track app startup time (for "Up From" timestamp in frontend)
APP_STARTUP_TIME = datetime.now()


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    """
    # STARTUP
    logger.info("=" * 80)
    logger.info(f"{settings.app_name} STARTING UP...")
    print("-----------SERVER IS STARTED, DO NOT CLOSE---------------")
    logger.info(f"Server running in {'DEBUG' if settings.debug else 'PRODUCTION'} mode")
    logger.info(f"Log files location: {log_dir.absolute()}")
    logger.info("=" * 80)

    # Test database connection
    logger.info("Testing database connection...")
    try:
        if test_connection():
            logger.info("Database connected successfully!")
            print("** DATBASE CONNECTED SUCCESSFULLY ")
            create_tables()
        else:
            logger.error("Database connection failed!")
            print("** DAtABASE CONNECTION FAILED")
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)

    # Start polling service
    logger.info("Starting polling service...")

    try:
        await polling_service.start()
        logger.info("Polling service started successfully!")
        print("---------polling started--------")
    except Exception as e:
        logger.error(f"Failed to start polling service: {e}", exc_info=True)
        print(f"Failed to start polling service: {e}", exc_info=True)

    # Start data retention service
    logger.info("Starting data retention service...")

    try:
        await retention_service.start()
        logger.info("Data retention service started successfully!")
        print("---------data retention service started--------")
    except Exception as e:
        logger.error(f"Failed to start retention service: {e}", exc_info=True)
        print(f"Failed to start retention service: {e}", exc_info=True)

    # Start log retention service
    logger.info("Starting log retention service...")

    try:
        await log_retention_service.start()
        logger.info("Log retention service started successfully!")
        print("---------log retention service started--------")
    except Exception as e:
        logger.error(f"Failed to start log retention service: {e}", exc_info=True)
        print(f"Failed to start log retention service: {e}", exc_info=True)


    yield  # Application runs here

    # SHUTDOWN
    logger.info("=" * 80)
    logger.info("SHUTTING DOWN SERVER...")
    print("SHUTTING DOWN SERVER...")
    logger.info("=" * 80)

    # Stop log retention service
    logger.info("Stopping log retention service...")
    try:
        await log_retention_service.stop()
        logger.info("Log retention service stopped successfully!")
    except Exception as e:
        logger.error(f"Error stopping log retention service: {e}", exc_info=True)

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
    print("Server shutdown complete")
    logger.info("=" * 80)


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="Modbus RS485 Temperature Monitoring System",
    version="1.0.0",
    lifespan=lifespan  # Use lifespan instead of on_event
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


# Configure CORS - Allow access from any origin on the network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to catch and log all unhandled exceptions
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


# Run server when executed directly (for PyInstaller exe)
if __name__ == "__main__":
    import uvicorn

    # Get host and port from settings
    host = settings.server_host if hasattr(settings, 'server_host') else "0.0.0.0"
    port = settings.server_port if hasattr(settings, 'server_port') else 8000

    logger.info(f"Starting Uvicorn server on {host}:{port}...")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning"
    )