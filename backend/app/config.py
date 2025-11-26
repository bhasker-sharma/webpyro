from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads values from .env file.
    """
    app_name: str = "Modbus Temperature Monitor"
    debug: bool = True
    database_url: str
    
    # Modbus settings (optional, with defaults)
    modbus_timeout: int = 5
    modbus_poll_interval: int = 5

    # Common Modbus register settings (applied to all devices)
    modbus_register_address: int = 0
    modbus_function_code: int = 3
    modbus_start_register: int = 0
    modbus_register_count: int = 2

    # Ambient temperature register settings
    ambient_temp_start_register: int = 2

    # Configuration Access PIN
    config_pin: str = "1234"

    # Data Retention Settings (Time-based FIFO cleanup)
    data_retention_days: int = 90         # Keep last 90 days (3 months) of data
    data_retention_max_rows: int = 5000000  # Safety limit - max rows in database
    cleanup_hour: int = 2                 # Daily cleanup runs at this hour (24-hour format)

    class Config:
        # Look for .env file in parent directory (backend folder)
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        extra = "ignore"  # Ignore extra fields in .env that aren't in the class

@lru_cache()
def get_settings():
    """
    Returns cached settings instance.
    lru_cache ensures we only create one instance.
    """
    return Settings()