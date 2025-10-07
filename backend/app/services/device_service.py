"""
Device Service
Business logic for device operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.models.device import DeviceSettings, DeviceReading
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceService:
    """Service class for device operations"""
    @staticmethod
    def get_all_devices(db: Session, enabled_only: bool = False) -> List[DeviceSettings]:
        """
        Get all devices
        
        Args:
            db: Database session
            enabled_only: If True, return only enabled devices
            
        Returns:
            List of DeviceSettings objects
        """
        query = db.query(DeviceSettings)
        
        if enabled_only:
            query = query.filter(DeviceSettings.enabled == True)
            
        return query.order_by(DeviceSettings.id).all()

    @staticmethod
    def get_device_by_id(db: Session, device_id: int) -> Optional[DeviceSettings]:
        """
        Get device by ID
        
        Args:
            db: Database session
            device_id: Device ID
            
        Returns:
            DeviceSettings object or None
        """
        return db.query(DeviceSettings).filter(DeviceSettings.id == device_id).first()

    @staticmethod
    def get_device_by_name(db: Session, name: str) -> Optional[DeviceSettings]:
        """
        Get device by name
        
        Args:
            db: Database session
            name: Device name
            
        Returns:
            DeviceSettings object or None
        """
        return db.query(DeviceSettings).filter(DeviceSettings.name == name).first()

    @staticmethod
    def create_device(db: Session, device: DeviceCreate) -> DeviceSettings:
        """
        Create new device
        
        Args:
            db: Database session
            device: Device data
            
        Returns:
            Created DeviceSettings object
        """
        # Create device object
        db_device = DeviceSettings(**device.model_dump())
        
        # Add to database
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        return db_device

    @staticmethod
    def update_device(db: Session, device_id: int, device_update: DeviceUpdate) -> Optional[DeviceSettings]:
        """
        Update device
        
        Args:
            db: Database session
            device_id: Device ID
            device_update: Updated device data
            
        Returns:
            Updated DeviceSettings object or None
        """
        # Get existing device
        db_device = DeviceService.get_device_by_id(db, device_id)
        if not db_device:
            return None
        
        # Update fields that are provided
        update_data = device_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)
        
        # Commit changes
        db.commit()
        db.refresh(db_device)
        
        return db_device

    @staticmethod
    def delete_device(db: Session, device_id: int) -> bool:
        """
        Delete device
        
        Args:
            db: Database session
            device_id: Device ID
            
        Returns:
            True if deleted, False if not found
        """
        db_device = DeviceService.get_device_by_id(db, device_id)
        if not db_device:
            return False
        
        db.delete(db_device)
        db.commit()
        
        return True

    @staticmethod
    def get_device_with_latest_reading(db: Session, device_id: int) -> Optional[dict]:
        """
        Get device with its latest reading
        
        Args:
            db: Database session
            device_id: Device ID
            
        Returns:
            Dict with device and latest_reading, or None
        """
        device = DeviceService.get_device_by_id(db, device_id)
        if not device:
            return None
        
        # Get latest reading
        latest_reading = db.query(DeviceReading)\
            .filter(DeviceReading.device_id == device_id)\
            .order_by(desc(DeviceReading.ts_utc))\
            .first()
        
        return {
            "device": device,
            "latest_reading": latest_reading
        }

    @staticmethod
    def get_all_devices_with_latest_readings(db: Session) -> List[dict]:
        """
        Get all devices with their latest readings
        
        Returns:
            List of dicts with device and latest_reading
        """
        devices = DeviceService.get_all_devices(db)
        result = []
        
        for device in devices:
            latest_reading = db.query(DeviceReading)\
                .filter(DeviceReading.device_id == device.id)\
                .order_by(desc(DeviceReading.ts_utc))\
                .first()
            
            result.append({
                "device": device,
                "latest_reading": latest_reading
            })
        
        return result