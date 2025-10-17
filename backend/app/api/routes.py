#all api endpoints are here

from fastapi import APIRouter, HTTPException, Depends  
from sqlalchemy.orm import Session  
from typing import List, Dict
from app.api.devices import router as devices_router
from app.database import get_db, engine  
from sqlalchemy import text
from app.models.device import DeviceSettings, DeviceReading
from datetime import datetime
from app.services.reading_service import ReadingService
from datetime import datetime


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
        result.append({
            'id':reading.id,
            'device_id':reading.device_id,
            'device_name':reading.device_name,
            'temperature': reading.value,
            'status': reading.status,
            'raw_hex': reading.raw_hex,
            'timestamp': reading.ts_utc.isoformat()
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
            result["recent_readings"].append({
                "id": reading.id,
                "device_id": reading.device_id,
                "device_name": reading.device_name,
                "temperature": reading.value,
                "status": reading.status,
                "timestamp": reading.ts_utc.isoformat()
            })

        return result
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# INCLUDE SUB-ROUTERS
# ============================================================================

# Include device routes (they have their own /api/devices prefix)
router.include_router(devices_router, tags=["devices"])