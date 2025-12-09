"""
Centralized Logging Configuration
Sets up comprehensive logging for the entire application
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging():
    """
    Configure centralized logging for the entire application

    Creates separate log files for:
    - app.log: General application logs
    - modbus.log: Modbus communication logs
    - database.log: Database operation logs
    - api.log: API request/response logs
    - websocket.log: WebSocket connection logs
    - errors.log: All errors across the system

    Features:
    - Rotating file handlers (10MB max per file, 10 backups)
    - Timestamps with milliseconds
    - Structured format with module names and line numbers
    - Console output for WARNING and above
    - All ERROR and CRITICAL logs go to errors.log
    """

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Define log format with timestamps
    # Format: 2025-11-23 14:30:45,123 | INFO | modbus_service:127 | Connected to COM3
    file_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Simpler format for console (less verbose)
    console_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # =========================================================================
    # ROOT LOGGER CONFIGURATION
    # =========================================================================
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # =========================================================================
    # CONSOLE HANDLER (WARNING and above)
    # =========================================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # =========================================================================
    # FILE HANDLERS - ROTATING
    # =========================================================================

    # 1. GENERAL APPLICATION LOG (INFO and above)
    app_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=30 * 1024 * 1024,  # 30 MB
        backupCount=7,  # Keep 7 backups (one week) = ~210 MB total
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(file_format)
    root_logger.addHandler(app_handler)

    # 2. ERRORS LOG (ERROR and CRITICAL only)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "errors.log",
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=10,  # Keep 10 backups = ~500 MB total (errors are important!)
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root_logger.addHandler(error_handler)

    # =========================================================================
    # COMPONENT-SPECIFIC LOGGERS
    # =========================================================================

    # 3. MODBUS COMMUNICATION LOG
    modbus_logger = logging.getLogger('app.services.modbus_service')
    modbus_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "modbus.log",
        maxBytes=50 * 1024 * 1024,  # 50 MB (increased for longer retention)
        backupCount=5,  # Keep 5 backups = ~250 MB total
        encoding='utf-8'
    )
    modbus_handler.setLevel(logging.INFO)  # Changed from DEBUG - only log important events
    modbus_handler.setFormatter(file_format)
    modbus_logger.addHandler(modbus_handler)

    # 4. POLLING SERVICE LOG
    polling_logger = logging.getLogger('app.services.polling_service')
    polling_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "polling.log",
        maxBytes=50 * 1024 * 1024,  # 50 MB (increased for longer retention)
        backupCount=5,  # Keep 5 backups = ~250 MB total
        encoding='utf-8'
    )
    polling_handler.setLevel(logging.INFO)  # Changed from DEBUG - only log important events
    polling_handler.setFormatter(file_format)
    polling_logger.addHandler(polling_handler)

    # 5. DATABASE LOG
    database_logger = logging.getLogger('app.database')
    db_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "database.log",
        maxBytes=20 * 1024 * 1024,  # 20 MB
        backupCount=3,  # Keep 3 backups = ~60 MB total
        encoding='utf-8'
    )
    db_handler.setLevel(logging.INFO)  # Changed from DEBUG - reduce noise
    db_handler.setFormatter(file_format)
    database_logger.addHandler(db_handler)

    # 6. API ROUTES LOG
    api_logger = logging.getLogger('app.api.routes')
    api_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "api.log",
        maxBytes=30 * 1024 * 1024,  # 30 MB
        backupCount=3,  # Keep 3 backups = ~90 MB total
        encoding='utf-8'
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(file_format)
    api_logger.addHandler(api_handler)

    # 7. WEBSOCKET LOG
    websocket_logger = logging.getLogger('app.api.websocket')
    ws_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "websocket.log",
        maxBytes=20 * 1024 * 1024,  # 20 MB
        backupCount=3,  # Keep 3 backups = ~60 MB total
        encoding='utf-8'
    )
    ws_handler.setLevel(logging.INFO)  # Changed from DEBUG - only connection events
    ws_handler.setFormatter(file_format)
    websocket_logger.addHandler(ws_handler)

    # 8. PARAMETERS LOG (Emissivity, etc.)
    parameters_logger = logging.getLogger('app.rs485_client')
    parameters_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "parameters.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,  # Keep 5 backups = ~50 MB total
        encoding='utf-8'
    )
    parameters_handler.setLevel(logging.DEBUG)  # Capture all parameter operations for debugging
    parameters_handler.setFormatter(file_format)
    parameters_logger.addHandler(parameters_handler)

    # =========================================================================
    # SUPPRESS NOISY THIRD-PARTY LOGGERS
    # =========================================================================
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.WARNING)

    # =========================================================================
    # LOG STARTUP MESSAGE
    # =========================================================================
    startup_logger = logging.getLogger('app.startup')
    startup_logger.info("=" * 80)
    startup_logger.info(f"LOGGING SYSTEM INITIALIZED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    startup_logger.info(f"Log directory: {log_dir.absolute()}")
    startup_logger.info("Log files (optimized for production):")
    startup_logger.info("  - app.log: General application logs (INFO+) - 30MB x7")
    startup_logger.info("  - errors.log: All errors (ERROR+) - 50MB x10")
    startup_logger.info("  - modbus.log: Modbus errors & connections (INFO+) - 50MB x5")
    startup_logger.info("  - polling.log: Polling events (INFO+) - 50MB x5")
    startup_logger.info("  - database.log: Database operations (INFO+) - 20MB x3")
    startup_logger.info("  - api.log: API requests/responses (INFO+) - 30MB x3")
    startup_logger.info("  - websocket.log: WebSocket connections (INFO+) - 20MB x3")
    startup_logger.info("  - parameters.log: Device parameters (DEBUG+) - 10MB x5")
    startup_logger.info("Total max space: ~1.6 GB (keeps several weeks of data)")
    startup_logger.info("=" * 80)

    return log_dir


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module

    Args:
        name: Name of the module (usually __name__)

    Returns:
        Configured logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)
