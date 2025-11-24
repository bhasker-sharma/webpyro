"""
Database Connection Module
Handles PostgreSQL connection using SQLAlchemy
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
import logging

# Get settings
settings = get_settings()

# Get logger for this module
logger = logging.getLogger(__name__)

# Create database engine
# echo=False disables SQL query logging in console
try:
    engine = create_engine(
        settings.database_url,
        echo=False,           # Disable SQL query logging
        pool_pre_ping=True,   # Test connections before using them
        pool_size=10,         # Number of connections to keep open
        max_overflow=20       # Maximum number of connections to create beyond pool_size
    )
    logger.info("Database engine created successfully")
    logger.debug(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'N/A'}")  # Log without password
    logger.debug(f"Pool size: 10, Max overflow: 20")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}", exc_info=True)
    raise

# Create SessionLocal class - each instance is a database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all database models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """
    Database session dependency.
    Creates a new session for each request and closes it after.

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            # use db here
    """
    db = SessionLocal()
    try:
        # Don't log session creation (happens on every API request - too verbose)
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    finally:
        db.close()
        # Don't log session close (too verbose)


# Function to test database connection
def test_connection():
    """
    Test database connection
    Returns True if successful, False otherwise
    """
    try:
        logger.info("Testing database connection...")
        # Try to connect
        connection = engine.connect()
        connection.close()
        logger.info("Database connection test SUCCESSFUL")
        return True
    except Exception as e:
        logger.error(f"Database connection test FAILED: {e}", exc_info=True)
        return False


# Function to create all tables (if they don't exist)
def create_tables():
    """
    Create all tables defined in models.
    This is a backup - we already created tables in pgAdmin.
    """
    try:
        logger.info("Creating/verifying database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully!")

        # Log table names
        table_names = Base.metadata.tables.keys()
        logger.info(f"Tables: {', '.join(table_names)}")
    except Exception as e:
        logger.error(f"Failed to create/verify database tables: {e}", exc_info=True)
        raise