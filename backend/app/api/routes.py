#all api endpoints are here

from fastapi import APIRouter, HTTPException, Depends  
from sqlalchemy.orm import Session  
from typing import List, Dict
from app.api.devices import router as devices_router
from app.database import get_db, engine  
from sqlalchemy import text
from app.models.device import DeviceSettings, DeviceReading
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

# ============================================================================
# INCLUDE SUB-ROUTERS
# ============================================================================

# Include device routes (they have their own /api/devices prefix)
router.include_router(devices_router, tags=["devices"])