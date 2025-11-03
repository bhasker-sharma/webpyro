from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api.routes import router as api_router
from app.database import test_connection, create_tables
from app.services.polling_service import polling_service  # NEW IMPORT

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(levelname)s: %(message)s'
)

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)

# Set application loggers to INFO level (for your custom messages)
logging.getLogger('app').setLevel(logging.INFO)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    """
    # STARTUP
    print(f"{settings.app_name} starting up...")
    print(f"Server running in {'DEBUG' if settings.debug else 'PRODUCTION'} mode")
    
    # Test database connection
    print("Testing database connection...")
    if test_connection():
        print("Database connected successfully!")
        create_tables()
    else:
        print("Database connection failed!")
    
    # Start polling service
    print("Starting polling service...")
    await polling_service.start()
    print("Polling service started!")
    
    yield  # Application runs here
    
    # SHUTDOWN
    print("Shutting down server...")
    
    # Stop polling service
    print("Stopping polling service...")
    await polling_service.stop()
    print("Polling service stopped!")
    
    print("Server shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="Modbus RS485 Temperature Monitoring System",
    version="1.0.0",
    lifespan=lifespan  # Use lifespan instead of on_event
)

# Configure CORS - Allow access from any origin on the network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)