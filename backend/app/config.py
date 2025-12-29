from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache
from typing import Optional
import os
import sys

class Settings(BaseSettings):
    """
    Application configuration settings for Desktop Version.
    Uses SQLite instead of PostgreSQL.
    """
    app_name: str = "Pyrometer Desktop Monitor"
    debug: bool = False

    # SQLite database path (stored in user's AppData folder)
    database_url: Optional[str] = None

    # Modbus settings (optional, with defaults)
    modbus_timeout: int = 1
    modbus_poll_interval: int = 20

    # Dynamic Polling Configuration
    modbus_enable_dynamic_polling: bool = True
    modbus_per_device_time: float = 0.5
    modbus_min_poll_interval: float = 1.0
    modbus_max_poll_interval: float = 20.0
    modbus_safety_factor: float = 2.5

    # Common Modbus register settings (applied to all devices)
    modbus_register_address: int = 4002
    modbus_function_code: int = 3
    modbus_start_register: int = 1
    modbus_register_count: int = 1

    # Ambient temperature register settings
    ambient_temp_start_register: int = 5

    # Configuration Access PIN
    config_pin: str = "1234"

    # Data Retention Settings (Time-based FIFO cleanup)
    data_retention_days: float = 90       # Keep last 90 days (3 months) of data
    data_retention_max_rows: int = 5000000  # Safety limit - max rows in database
    cleanup_hour: int = 2                 # Daily cleanup runs at this hour (24-hour format)

    # Server settings for internal use
    server_host: str = "127.0.0.1"  # Localhost only for desktop
    server_port: int = 8000

    class Config:
        # Look for .env file
        # In frozen mode (exe), it's in _internal folder next to the exe
        # In development, it's in the backend folder
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
            env_file = os.path.join(base_dir, "_internal", ".env")
        else:
            # Running in development - look for .env file in parent directory (backend folder)
            env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        extra = "ignore"  # Ignore extra fields in .env that aren't in the class

    @model_validator(mode='after')
    def set_database_path(self):
        """Set database path if not provided"""
        if self.database_url is None:
            # Get application data directory
            if getattr(sys, 'frozen', False):
                # Running as compiled executable - use AppData for database
                # This ensures database can be written even when installed in Program Files
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                app_dir = os.path.join(app_data, "Pyrometer Desktop Monitor")
            else:
                # Running in development
                app_dir = os.path.dirname(os.path.dirname(__file__))

            # Create data directory if it doesn't exist
            data_dir = os.path.join(app_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            # Set SQLite database path
            db_path = os.path.join(data_dir, "pyrometer.db")
            self.database_url = f"sqlite:///{db_path}"

        return self

@lru_cache()
def get_settings():
    """
    Returns cached settings instance.
    lru_cache ensures we only create one instance.
    """
    return Settings()
