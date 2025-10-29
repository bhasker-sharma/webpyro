#all api endpoints are here

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.api.devices import router as devices_router
from app.api.websocket import router as websocket_router  # WebSocket routes
from app.database import get_db, engine
from sqlalchemy import text
from app.models.device import DeviceSettings, DeviceReading
from datetime import datetime, timedelta
from app.services.reading_service import ReadingService
from fastapi.responses import StreamingResponse
import io
import csv


router = APIRouter(
    prefix="/api",
    tags=["api"]  # Groups endpoints in documentation
)

# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@router.get("/")
async def api_root():
    """API Root endpoint - Basic API information"""
    return {
        "message": "Modbus Temperature Monitor API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "test": "/api/test",
            "devices": "/api/devices",
            "devices_with_readings": "/api/devices/with-readings",
            "readings_latest":"/api/reading/latest",
            "readings_device": "/api/readings/device/{id}",
            "readings_stats":"/api/readings/stats",
            "polling_stats": "/api/polling/stats",
            "polling_restart": "/api/polling/restart",
            "websocket": "/api/ws",
            "docs": "/docs"
        }
    }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint - Monitor system status
    """
    db_status ="disconnected"
    db_details = {}

    try:
        #try to execute simple query
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        #get device count 
        device_count = db.query(DeviceSettings).count()
        reading_count = db.query(DeviceReading).count()

        db_status = "connected"
        db_details = {
            "device_count": device_count,
            "reading_count": reading_count
        }
    except Exception as e:
        db_status = "error"
        db_details = {"error": str(e)}

    #overall system status
    system_status = "healthy" if db_status == "connected" else "unhealthy"

    return {
        "status": system_status,
        "database": db_status,
        "database_details": db_details,
        "modbus": "not initialized yet", 
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "message": "Backend API is working perfectly!",
        "note": "Use /api/devices to manage devices"
    }

@router.get("/polling/stats")
async def get_polling_stats():
    """
    Get polling service statistics
    """
    from app.services.polling_service import polling_service
    return polling_service.get_stats()

@router.post("/polling/restart")
async def restart_polling():
    """
    Restart the polling service
    Call this after updating device configurations to reload devices
    """
    from app.services.polling_service import polling_service
    try:
        await polling_service.restart()
        return {
            "status": "success",
            "message": "Polling service restarted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart polling service: {str(e)}"
        )

# ============================================================================
# READING ENDPOINTS (NEW)
# ============================================================================
@router.get("/reading/latest")
async def get_latest_readings(db: Session = Depends(get_db)):
    """
    Get latest reading for each device
    """
    readings = ReadingService.get_latest_readings(db)
    return readings

@router.get("/reading/device/{device_id}")
async def get_readings_for_device(
    device_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent readings for a specific device
    
    Query Parameters:
        - limit: Number of readings to return (default 10)
    """
    readings = ReadingService.get_device_readings(db, device_id, limit)
    #convert to list of dicts
    result = []
    for reading in readings:
        # Convert UTC timestamp to local time (IST = UTC + 5:30)
        local_timestamp = reading.ts_utc + timedelta(hours=5, minutes=30)

        result.append({
            'id':reading.id,
            'device_id':reading.device_id,
            'device_name':reading.device_name,
            'temperature': reading.value,
            'status': reading.status,
            'raw_hex': reading.raw_hex,
            'timestamp': local_timestamp.isoformat()
        })
    return result

@router.get("/reading/stats")
async def get_reading_stats(db: Session = Depends(get_db)):
    """
    Get overall reading statistics

    Returns:
        Statistics about readings in the system
    """
    stats = ReadingService.get_reading_stats(db)
    return stats

@router.get("/reading/filter")
async def get_filtered_readings(
    device_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get filtered readings for a specific device with date range

    Query Parameters:
        - device_id: Device ID to filter readings
        - start_date: Start datetime in ISO format (e.g., 2024-01-01T00:00:00)
        - end_date: End datetime in ISO format (e.g., 2024-01-31T23:59:59)
        - limit: Optional maximum number of readings to return (no limit if not specified)
    """
    # Parse datetime strings if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            # Convert to timezone-aware datetime, then remove timezone for naive comparison
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

    if end_date:
        try:
            # Convert to timezone-aware datetime, then remove timezone for naive comparison
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

    # Get filtered readings
    readings = ReadingService.get_device_readings(
        db=db,
        device_id=device_id,
        limit=limit,
        start_date=start_dt,
        end_date=end_dt
    )

    # Convert to list of dicts
    result = []
    for reading in readings:
        # Convert UTC timestamp to local time (IST = UTC + 5:30)
        local_timestamp = reading.ts_utc + timedelta(hours=5, minutes=30)

        result.append({
            'id': reading.id,
            'device_id': reading.device_id,
            'device_name': reading.device_name,
            'value': reading.value,
            'status': reading.status,
            'raw_hex': reading.raw_hex,
            'timestamp': local_timestamp.isoformat(),
            'created_at': reading.created_at.isoformat() if reading.created_at else None
        })

    return {
        'count': len(result),
        'readings': result
    }

@router.get("/reading/export/csv")
async def export_readings_csv(
    device_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export filtered readings as CSV file

    Query Parameters:
        - device_id: Device ID to filter readings
        - start_date: Start datetime in ISO format
        - end_date: End datetime in ISO format
    """
    # Parse datetime strings if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            # Convert to timezone-aware datetime, then remove timezone for naive comparison
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            # Convert to timezone-aware datetime, then remove timezone for naive comparison
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Get filtered readings (no limit for export)
    readings = ReadingService.get_device_readings(
        db=db,
        device_id=device_id,
        limit=None,  # No limit - export all data in time range
        start_date=start_dt,
        end_date=end_dt
    )

    # Get device name
    device = db.query(DeviceSettings).filter(DeviceSettings.id == device_id).first()
    device_name = device.name if device else f"Device {device_id}"

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Custom header section
    # Row 1: Report title with device name
    writer.writerow([f"Data Report of {device_name}"])

    # Row 2: Total data points
    writer.writerow([f"Total Data Points: {len(readings)}"])

    # Row 3: Date range (convert to IST)
    if start_dt:
        start_local = start_dt + timedelta(hours=5, minutes=30)
        start_date_str = start_local.strftime("%Y-%m-%d %H:%M:%S")
    else:
        start_date_str = "Beginning"

    if end_dt:
        end_local = end_dt + timedelta(hours=5, minutes=30)
        end_date_str = end_local.strftime("%Y-%m-%d %H:%M:%S")
    else:
        end_date_str = "End"

    writer.writerow([f"{start_date_str} - {end_date_str}"])

    # Row 4: Empty row
    writer.writerow([])

    # Row 5: Column headers
    writer.writerow(['Serial Number', 'Database ID', 'Date', 'Time', 'Value', 'Status'])

    # Write data rows
    for idx, reading in enumerate(readings, start=1):
        # Convert UTC timestamp to local datetime (IST = UTC + 5:30)
        local_dt = reading.ts_utc + timedelta(hours=5, minutes=30)
        date_str = local_dt.strftime("%Y-%m-%d")
        time_str = local_dt.strftime("%H:%M:%S")

        writer.writerow([
            idx,  # Serial number starting from 1
            reading.id,  # Database ID
            date_str,  # Date in YYYY-MM-DD format
            time_str,  # Time in HH:MM:SS format
            reading.value,  # Temperature value
            reading.status  # Status
        ])

    # Prepare response
    output.seek(0)

    # Filename with device name and timestamp
    filename = f"{device_name}_readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/debug/readings")
async def debug_readings(db: Session = Depends(get_db)):
    """
    Debug endpoint to check all readings in database
    """
    try:
        # Get all readings
        all_readings = db.query(DeviceReading).order_by(DeviceReading.ts_utc.desc()).limit(20).all()

        result = {
            "total_count": db.query(DeviceReading).count(),
            "recent_readings": []
        }

        for reading in all_readings:
            # Convert UTC timestamp to local time (IST = UTC + 5:30)
            local_timestamp = reading.ts_utc + timedelta(hours=5, minutes=30)

            result["recent_readings"].append({
                "id": reading.id,
                "device_id": reading.device_id,
                "device_name": reading.device_name,
                "temperature": reading.value,
                "status": reading.status,
                "timestamp": local_timestamp.isoformat()
            })

        return result
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# INCLUDE SUB-ROUTERS
# ============================================================================

# Include device routes (they have their own /api/devices prefix)
router.include_router(devices_router, tags=["devices"])

# Include WebSocket routes (for real-time data streaming)
router.include_router(websocket_router, tags=["websocket"])