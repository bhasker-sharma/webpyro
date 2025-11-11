"""
Device Models
SQLAlchemy models for device_settings, device_readings, and reading_archive tables
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, BigInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class DeviceSettings(Base):
    """
    Device Settings Model
    Represents a Modbus temperature device configuration
    """
    __tablename__ = "device_settings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slave_id = Column(Integer, nullable=False, index=True)
    baud_rate = Column(Integer, nullable=False, default=9600)
    com_port = Column(String(20), nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    show_in_graph = Column(Boolean, default=False, index=True)
    register_address = Column(Integer, nullable=False)
    function_code = Column(Integer, nullable=False, default=3)
    start_register = Column(Integer, nullable=False)
    register_count = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to readings
    readings = relationship("DeviceReading", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DeviceSettings(id={self.id}, name='{self.name}', slave_id={self.slave_id})>"


class DeviceReading(Base):
    """
    Device Reading Model
    Represents a temperature reading from a device
    """
    __tablename__ = "device_readings"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("device_settings.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(100), nullable=False)
    ts_utc = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    value = Column(Float, nullable=False)
    ambient_temp = Column(Float, nullable=True)  # Ambient temperature from separate register
    status = Column(String(10), nullable=False, index=True)  # OK, Stale, Err
    raw_hex = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to device
    device = relationship("DeviceSettings", back_populates="readings")

    def __repr__(self):
        return f"<DeviceReading(id={self.id}, device='{self.device_name}', value={self.value}, status='{self.status}')>"


class ReadingArchive(Base):
    """
    Reading Archive Model
    Stores archived readings when device_readings table grows too large
    """
    __tablename__ = "reading_archive"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False, index=True)
    device_name = Column(String(100), nullable=False)
    ts_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)
    ambient_temp = Column(Float, nullable=True)  # Ambient temperature from separate register
    status = Column(String(10), nullable=False)
    raw_hex = Column(String(100))
    archived_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<ReadingArchive(id={self.id}, device='{self.device_name}', value={self.value})>"