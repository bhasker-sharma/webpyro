from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceWithLatestReading
from app.services.device_service import DeviceService
router = APIRouter(
    prefix="/devices",
    tags=["devices"]
)

@router.get("", response_model=List[DeviceResponse])
async def get_all_devices(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all devices
    
    Query Parameters:
        - enabled_only: If true, return only enabled devices
    """
    devices = DeviceService.get_all_devices(db, enabled_only=enabled_only)
    return devices

@router.get("/with-readings", response_model=List[DeviceWithLatestReading])
async def get_devices_with_readings(db: Session = Depends(get_db)):
    """
    Get all devices with their latest temperature readings
    """
    devices_data = DeviceService.get_all_devices_with_latest_readings(db)
    
    result = []
    for data in devices_data:
        device_dict = DeviceResponse.model_validate(data["device"]).model_dump()
        device_dict["latest_reading"] = data["latest_reading"]
        result.append(device_dict)
    
    return result

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get device by ID
    """
    device = DeviceService.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new device
    """
    # Check if device name already exists
    existing_device = DeviceService.get_device_by_name(db, device.name)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with name '{device.name}' already exists"
        )

    # Check if instrument ID (slave_id) already exists
    existing_slave = DeviceService.get_device_by_slave_id(db, device.slave_id)
    if existing_slave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Instrument ID {device.slave_id} is already in use by device '{existing_slave.name}'. Each device must have a unique Instrument ID (1-16)."
        )

    # Create device
    new_device = DeviceService.create_device(db, device)
    return new_device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update device configuration
    """
    # Check if name is being changed and if it conflicts
    if device_update.name:
        existing_device = DeviceService.get_device_by_name(db, device_update.name)
        if existing_device and existing_device.id != device_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device with name '{device_update.name}' already exists"
            )

    # Check if slave_id is being changed and if it conflicts
    if device_update.slave_id:
        existing_slave = DeviceService.get_device_by_slave_id(db, device_update.slave_id)
        if existing_slave and existing_slave.id != device_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instrument ID {device_update.slave_id} is already in use by device '{existing_slave.name}'. Each device must have a unique Instrument ID (1-16)."
            )

    # Update device
    updated_device = DeviceService.update_device(db, device_id, device_update)
    if not updated_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    return updated_device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete device
    
    This will also delete all readings associated with this device (CASCADE)
    """
    success = DeviceService.delete_device(db, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    return None