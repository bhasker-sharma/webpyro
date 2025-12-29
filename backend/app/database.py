"""
Database Connection Module
Handles SQLite connection using SQLAlchemy (Desktop Version)
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
    # SQLite specific settings
    engine = create_engine(
        settings.database_url,
        echo=False,           # Disable SQL query logging
        connect_args={
            "check_same_thread": False,  # Allow multiple threads (required for SQLite)
            "timeout": 30  # 30 second timeout for locks
        }
    )

    # Enable WAL mode for better concurrency (SQLite specific)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
        cursor.close()

    logger.info("Database engine created successfully (SQLite)")
    logger.debug(f"Database path: {settings.database_url}")
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
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    finally:
        db.close()


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
