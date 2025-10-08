from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import router as api_router
from app.database import test_connection,create_tables

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="Modbus RS485 Temperature Monitoring System",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows our React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_router)

# Startup event - runs when server starts
@app.on_event("startup")
async def startup_event():
    """
    This runs when the server starts.
    We can add initialization logic here later (like database connection).
    """
    print(f"{settings.app_name} starting up...")
    print(f"Server running in {'DEBUG' if settings.debug else 'PRODUCTION'} mode")
    # Test database connection
    print("Testing database connection...")
    if test_connection():
        print("Database connected successfully!")
        create_tables()  # Verify tables exist
    else:
        print("Database connection failed!")

# Shutdown event - runs when server stops
@app.on_event("shutdown")
async def shutdown_event():
    """
    This runs when the server shuts down.
    We can add cleanup logic here later (like closing database connections).
    """
    print("Shutting down server...")

