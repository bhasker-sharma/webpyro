"""
Device Schemas
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


# ============================================================================
# DEVICE SCHEMAS
# ============================================================================

class DeviceBase(BaseModel):
    """Base schema with common device fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Device name")
    slave_id: int = Field(..., ge=1, le=247, description="Modbus slave ID (1-247)")
    baud_rate: int = Field(9600, description="Baud rate for communication")
    com_port: str = Field(..., max_length=20, description="COM port (e.g., COM3)")
    enabled: bool = Field(True, description="Device enabled status")
    show_in_graph: bool = Field(False, description="Show device data in graph")
    # These fields are populated from .env and not required from client
    register_address: Optional[int] = Field(None, ge=0, description="Register address (populated from .env)")
    function_code: Optional[int] = Field(None, ge=1, le=4, description="Modbus function code (populated from .env)")
    start_register: Optional[int] = Field(None, ge=0, description="Starting register (populated from .env)")
    register_count: Optional[int] = Field(None, ge=1, description="Number of registers to read (populated from .env)")
    graph_y_min: Optional[float] = Field(600.0, description="Minimum Y-axis value for graph display")
    graph_y_max: Optional[float] = Field(2000.0, description="Maximum Y-axis value for graph display")

    @validator('baud_rate')
    def validate_baud_rate(cls, v):
        """Validate baud rate is a common value"""
        valid_rates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        if v not in valid_rates:
            raise ValueError(f'Baud rate must be one of: {valid_rates}')
        return v

    @validator('com_port')
    def validate_com_port(cls, v):
        """Validate COM port format"""
        if not v.upper().startswith('COM'):
            raise ValueError('COM port must start with "COM"')
        return v.upper()


class DeviceCreate(DeviceBase):
    """Schema for creating a new device"""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slave_id: Optional[int] = Field(None, ge=1, le=247)
    baud_rate: Optional[int] = None
    com_port: Optional[str] = Field(None, max_length=20)
    enabled: Optional[bool] = None
    show_in_graph: Optional[bool] = None
    register_address: Optional[int] = Field(None, ge=0)
    function_code: Optional[int] = Field(None, ge=1, le=4)
    start_register: Optional[int] = Field(None, ge=0)
    register_count: Optional[int] = Field(None, ge=1)
    graph_y_min: Optional[float] = None
    graph_y_max: Optional[float] = None


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows reading from SQLAlchemy models


# ============================================================================
# READING SCHEMAS
# ============================================================================

class ReadingResponse(BaseModel):
    """Schema for temperature reading response"""
    id: int
    device_id: int
    device_name: str
    ts_utc: datetime
    value: float
    ambient_temp: Optional[float] = None
    status: str
    raw_hex: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceWithLatestReading(DeviceResponse):
    """Schema for device with its latest reading"""
    latest_reading: Optional[ReadingResponse] = None