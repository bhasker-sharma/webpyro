"""
Centralized Logging Configuration
Sets up comprehensive logging for the entire application with DATE-BASED FOLDERS
Automatically switches to new date folder when date changes (even without restart!)
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


class DailyFolderHandler(logging.Handler):
    """
    Custom log handler that automatically switches to new date folder when date changes
    No restart needed - checks date before each log write!
    """

    # Class-level registry to track all handlers (for cleanup)
    _all_handlers = []

    def __init__(self, base_log_dir, filename, formatter, level=logging.INFO):
        super().__init__(level=level)
        self.base_log_dir = base_log_dir
        self.filename = filename
        self.setFormatter(formatter)
        self.current_date = None
        self.file_handler = None
        self._update_handler()
        # Register this handler
        DailyFolderHandler._all_handlers.append(self)

    def _update_handler(self):
        """Create or update file handler based on current date"""
        today = datetime.now().strftime("%d-%m-%Y")

        # Only update if date has changed
        if today != self.current_date:
            # Check if this is a date switch (not first creation)
            is_switch = self.current_date is not None

            # Close old handler if exists
            if self.file_handler:
                self.file_handler.close()

            # Create today's folder
            today_folder = self.base_log_dir / today
            today_folder.mkdir(exist_ok=True)

            # Create new file handler for today
            self.file_handler = logging.FileHandler(
                filename=today_folder / self.filename,
                encoding='utf-8'
            )
            self.file_handler.setFormatter(self.formatter)

            # Update current date
            old_date = self.current_date
            self.current_date = today

            # Log the folder switch (only if we're switching from old date to new date)
            if is_switch:
                print(f"[Logging] Date changed! Switched from {old_date}/ to {today}/")

    def emit(self, record):
        """Emit a log record - checks date first!"""
        try:
            # Check if date has changed and update handler if needed
            self._update_handler()

            # Emit the record using the current file handler
            if self.file_handler:
                self.file_handler.emit(record)
        except Exception:
            self.handleError(record)

    def close(self):
        """Close the handler"""
        if self.file_handler:
            self.file_handler.close()
        super().close()

    @classmethod
    def close_handlers_for_date(cls, date_str: str):
        """
        Close all file handlers for a specific date
        Called by retention service before deleting old folders

        Args:
            date_str: Date in DD-MM-YYYY format (e.g., "06-12-2025")
        """
        for handler in cls._all_handlers:
            if handler.current_date == date_str and handler.file_handler:
                try:
                    handler.file_handler.close()
                    handler.file_handler = None
                    # Reset current_date so handler can recreate on next log write
                    handler.current_date = None
                    print(f"[Logging] Closed file handler for date: {date_str}")
                except Exception as e:
                    print(f"[Logging] Error closing handler for {date_str}: {e}")


def setup_logging():
    """
    Configure centralized logging for the entire application

    Creates date-based folder structure:
    - logs/DD-MM-YYYY/ - One folder per day

    Inside each date folder:
    - app.log: General application logs
    - modbus.log: Modbus communication logs
    - database.log: Database operation logs
    - api.log: API request/response logs
    - websocket.log: WebSocket connection logs
    - errors.log: All errors across the system
    - retention.log: Data & log cleanup operations

    Features:
    - Date-based folder organization (easier management)
    - Simple retention: just delete old date folders
    - Timestamps with milliseconds
    - Structured format with module names and line numbers
    - Console output for WARNING and above
    """

    # Create base logs directory if it doesn't exist
    base_log_dir = Path(__file__).parent.parent / "logs"
    base_log_dir.mkdir(exist_ok=True)

    # Note: We don't create today's folder here anymore!
    # DailyFolderHandler will create it automatically and switch when date changes

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
    # FILE HANDLERS - DYNAMIC DATE-BASED (Auto-switches when date changes!)
    # =========================================================================

    # 1. GENERAL APPLICATION LOG (INFO and above)
    app_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="app.log",
        formatter=file_format,
        level=logging.INFO
    )
    root_logger.addHandler(app_handler)

    # 2. ERRORS LOG (ERROR and CRITICAL only)
    error_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="errors.log",
        formatter=file_format,
        level=logging.ERROR
    )
    root_logger.addHandler(error_handler)

    # =========================================================================
    # COMPONENT-SPECIFIC LOGGERS
    # =========================================================================

    # 3. MODBUS COMMUNICATION LOG
    modbus_logger = logging.getLogger('app.services.modbus_service')
    modbus_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="modbus.log",
        formatter=file_format,
        level=logging.INFO
    )
    modbus_logger.addHandler(modbus_handler)

    # 4. POLLING SERVICE LOG
    polling_logger = logging.getLogger('app.services.polling_service')
    polling_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="polling.log",
        formatter=file_format,
        level=logging.INFO
    )
    polling_logger.addHandler(polling_handler)

    # 5. DATABASE LOG
    database_logger = logging.getLogger('app.database')
    db_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="database.log",
        formatter=file_format,
        level=logging.INFO
    )
    database_logger.addHandler(db_handler)

    # 6. API ROUTES LOG
    api_logger = logging.getLogger('app.api.routes')
    api_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="api.log",
        formatter=file_format,
        level=logging.INFO
    )
    api_logger.addHandler(api_handler)

    # 7. WEBSOCKET LOG
    websocket_logger = logging.getLogger('app.api.websocket')
    ws_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="websocket.log",
        formatter=file_format,
        level=logging.INFO
    )
    websocket_logger.addHandler(ws_handler)

    # 8. RETENTION LOG (Database & Log File Cleanup)
    retention_logger = logging.getLogger('app.services.retention')
    retention_handler = DailyFolderHandler(
        base_log_dir=base_log_dir,
        filename="retention.log",
        formatter=file_format,
        level=logging.INFO
    )
    retention_logger.addHandler(retention_handler)
    # Prevent retention logs from propagating to root logger (avoid duplication in app.log)
    retention_logger.propagate = False

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
    today_folder_name = datetime.now().strftime("%d-%m-%Y")
    startup_logger.info("=" * 80)
    startup_logger.info(f"LOGGING SYSTEM INITIALIZED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    startup_logger.info(f"Base log directory: {base_log_dir.absolute()}")
    startup_logger.info(f"Current date folder: logs/{today_folder_name}/")
    startup_logger.info("✨ DYNAMIC DATE SWITCHING ENABLED ✨")
    startup_logger.info("   → Logs automatically switch to new date folder when date changes!")
    startup_logger.info("   → No restart needed - works even if you change system time")
    startup_logger.info("")
    startup_logger.info("Log files in each date folder:")
    startup_logger.info("  - app.log: General application logs (INFO+)")
    startup_logger.info("  - errors.log: All errors (ERROR+)")
    startup_logger.info("  - modbus.log: Modbus errors & connections (INFO+)")
    startup_logger.info("  - polling.log: Polling events (INFO+)")
    startup_logger.info("  - database.log: Database operations (INFO+)")
    startup_logger.info("  - api.log: API requests/responses (INFO+)")
    startup_logger.info("  - websocket.log: WebSocket connections (INFO+)")
    startup_logger.info("  - retention.log: Data & log cleanup operations (INFO+)")
    startup_logger.info("")
    startup_logger.info("Retention: Old date folders deleted automatically after retention period")
    startup_logger.info("=" * 80)

    return base_log_dir  # Return base logs directory for retention service


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
