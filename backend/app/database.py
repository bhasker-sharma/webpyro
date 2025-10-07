"""
Database Connection Module
Handles PostgreSQL connection using SQLAlchemy
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

# Get settings
settings = get_settings()

# Create database engine
# echo=True shows SQL queries in console (useful for debugging)
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Show SQL queries when DEBUG=True
    pool_pre_ping=True,   # Test connections before using them
    pool_size=10,         # Number of connections to keep open
    max_overflow=20       # Maximum number of connections to create beyond pool_size
)

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
    finally:
        db.close()


# Function to test database connection
def test_connection():
    """
    Test database connection
    Returns True if successful, False otherwise
    """
    try:
        # Try to connect
        connection = engine.connect()
        connection.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# Function to create all tables (if they don't exist)
def create_tables():
    """
    Create all tables defined in models.
    This is a backup - we already created tables in pgAdmin.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created!")