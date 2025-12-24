#all api endpoints are here

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.api.devices import router as devices_router
from app.api.websocket import router as websocket_router  # WebSocket routes
from app.api.pyrometer import router as pyrometer_router  # Pyrometer control routes
from app.database import get_db, engine
from sqlalchemy import text
from app.models.device import DeviceSettings, DeviceReading
from datetime import datetime, timedelta, timezone
from app.services.reading_service import ReadingService
from app.utils.datetime_utils import utc_now, ensure_utc, to_iso_utc, parse_iso_utc, utc_to_ist
from fastapi.responses import StreamingResponse
from app.config import get_settings
from pydantic import BaseModel
import io
import csv
import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api",
    tags=["api"]  # Groups endpoints in documentation
)

# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

class PinVerification(BaseModel):
    pin: str

@router.get("/config/com-ports")
async def get_available_com_ports():
    """
    Get list of available COM ports on the system
    Includes physical, USB, and virtual COM ports (like com0com)
    """
    try:
        # Get all ports detected by pyserial
        ports = serial.tools.list_ports.comports()
        available_ports = []

        for port in ports:
            available_ports.append({
                "port": port.device,
                "description": port.description or "Unknown Device",
                "hwid": port.hwid or "N/A"
            })

        # Also check for virtual COM ports that might not be auto-detected
        # com0com and other virtual COM emulators often use CNCA0, CNCB0, COM10-COM20 range
        import platform
        if platform.system() == "Windows":
            # Try to detect common virtual COM port names
            import winreg
            try:
                # Check Windows registry for additional COM ports
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
                detected_ports = set(p["port"] for p in available_ports)

                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if value not in detected_ports:
                            # Found a COM port not in the list
                            available_ports.append({
                                "port": value,
                                "description": f"Virtual/Registry Port ({name})",
                                "hwid": "Registry"
                            })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                pass  # Registry key not found, skip
            except Exception as reg_error:
                logger.warning(f"Registry COM port detection failed: {reg_error}")

        # Sort by port name (COM1, COM2, etc.)
        available_ports.sort(key=lambda x: (
            int(''.join(filter(str.isdigit, x["port"]))) if any(c.isdigit() for c in x["port"]) else 999,
            x["port"]
        ))

        return {
            "ports": available_ports,
            "count": len(available_ports)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get COM ports: {str(e)}"
        )

@router.post("/config/verify-pin")
async def verify_config_pin(pin_data: PinVerification):
    """
    Verify the configuration access PIN
    """
    settings = get_settings()
    if pin_data.pin == settings.config_pin:
        return {"valid": True, "message": "PIN verified successfully"}
    else:
        return {"valid": False, "message": "Invalid PIN"}

@router.post("/config/clear-settings")
async def clear_device_settings(db: Session = Depends(get_db)):
    """
    Clear all device settings from database
    This is called when saving new configuration to ensure clean state
    """
    try:
        # Delete all device settings (cascade will delete readings too)
        db.query(DeviceSettings).delete()
        db.commit()
        return {
            "status": "success",
            "message": "All device settings cleared successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear device settings: {str(e)}"
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
        "timestamp": to_iso_utc(utc_now())
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

@router.post("/polling/pause")
async def pause_polling():
    """
    Pause the polling service
    Call this before accessing device parameters to avoid COM port conflicts
    """
    from app.services.polling_service import polling_service
    try:
        await polling_service.stop()
        return {
            "status": "success",
            "message": "Polling service paused successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause polling service: {str(e)}"
        )

@router.post("/polling/resume")
async def resume_polling():
    """
    Resume the polling service
    Call this after accessing device parameters to resume temperature monitoring
    """
    from app.services.polling_service import polling_service
    try:
        await polling_service.start()
        return {
            "status": "success",
            "message": "Polling service resumed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume polling service: {str(e)}"
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
        # Return timestamp as-is (timezone-aware from database)
        result.append({
            'id':reading.id,
            'device_id':reading.device_id,
            'device_name':reading.device_name,
            'temperature': reading.value,
            'ambient_temp': reading.ambient_temp,  # Include ambient temperature
            'status': reading.status,
            'raw_hex': reading.raw_hex,
            'timestamp': to_iso_utc(reading.ts_utc)
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
            # Parse datetime string (frontend sends UTC time from user's local timezone)
            start_dt = parse_iso_utc(start_date)
            logger.info(f"Filter start_date: {start_date} -> {start_dt} UTC")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid start_date format: {e}")

    if end_date:
        try:
            # Parse datetime string (frontend sends UTC time from user's local timezone)
            end_dt = parse_iso_utc(end_date)
            logger.info(f"Filter end_date: {end_date} -> {end_dt} UTC")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid end_date format: {e}")

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
        # Return timestamp as-is (timezone-aware datetime from database)
        # The database stores timezone-aware timestamps, so no conversion needed
        result.append({
            'id': reading.id,
            'device_id': reading.device_id,
            'device_name': reading.device_name,
            'value': reading.value,
            'ambient_temp': reading.ambient_temp,  # Include ambient temperature
            'status': reading.status,
            'raw_hex': reading.raw_hex,
            'timestamp': to_iso_utc(reading.ts_utc),
            'created_at': to_iso_utc(reading.created_at) if reading.created_at else None
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
            # Parse datetime string (frontend sends UTC time from user's local timezone)
            start_dt = parse_iso_utc(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            # Parse datetime string (frontend sends UTC time from user's local timezone)
            end_dt = parse_iso_utc(end_date)
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

    # Row 3: Date range (use timestamps as stored in database)
    if start_dt:
        start_date_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        start_date_str = "Beginning"

    if end_dt:
        end_date_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        end_date_str = "End"

    writer.writerow([f"{start_date_str} - {end_date_str}"])

    # Row 4: Empty row
    writer.writerow([])

    # Row 5: Column headers
    writer.writerow(['Serial Number', 'Database ID', 'Date', 'Time', 'Temperature', 'Ambient Temp', 'Status'])

    # Write data rows
    for idx, reading in enumerate(readings, start=1):
        # Use timestamp exactly as stored in database (no conversion)
        date_str = reading.ts_utc.strftime("%Y-%m-%d")
        time_str = reading.ts_utc.strftime("%H:%M:%S")

        writer.writerow([
            idx,  # Serial number starting from 1
            reading.id,  # Database ID
            date_str,  # Date in YYYY-MM-DD format
            time_str,  # Time in HH:MM:SS format
            reading.value,  # Temperature value
            reading.ambient_temp if reading.ambient_temp is not None else '',  # Ambient temperature
            reading.status  # Status
        ])

    # Prepare response
    output.seek(0)

    # Filename with device name and current timestamp
    filename_time = utc_now()
    filename = f"{device_name}_readings_{filename_time.strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/reading/export/pdf")
async def export_readings_pdf(
    device_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export filtered readings as PDF file

    Query Parameters:
        - device_id: Device ID to filter readings
        - start_date: Start datetime in ISO format
        - end_date: End datetime in ISO format
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import os

    # Parse datetime strings if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = parse_iso_utc(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = parse_iso_utc(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Get filtered readings (no limit for export)
    readings = ReadingService.get_device_readings(
        db=db,
        device_id=device_id,
        limit=None,
        start_date=start_dt,
        end_date=end_dt
    )

    # Get device name
    device = db.query(DeviceSettings).filter(DeviceSettings.id == device_id).first()
    device_name = device.name if device else f"Device {device_id}"

    # Create PDF in memory
    pdf_buffer = io.BytesIO()

    # Get logo path
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'logo.png')
    logo_exists = os.path.exists(logo_path)

    # Define custom header function for every page
    def add_header_and_border(canvas, doc):
        """Add header with logos on every page"""
        canvas.saveState()

        # Page dimensions (Portrait mode)
        page_width, page_height = A4

        # Header elements
        header_y = page_height - 40  # Position from top

        # Left logo (small)
        if logo_exists:
            try:
                canvas.drawImage(
                    logo_path,
                    x=30,
                    y=header_y - 10,
                    width=0.35*inch,
                    height=0.35*inch,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except:
                pass

        # "TIPL" text next to left logo
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(colors.HexColor('#1f2937'))
        canvas.drawString(30 + 0.4*inch, header_y, "TIPL")

        # Center text: "Temperature Data Report - Device X"
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(colors.HexColor('#3b82f6'))
        header_text = f"Temperature Data Report - {device_name}"
        text_width = canvas.stringWidth(header_text, 'Helvetica-Bold', 12)
        canvas.drawString((page_width - text_width) / 2, header_y, header_text)

        # Right logo (small)
        # if logo_exists:
        #     try:
        #         canvas.drawImage(
        #             logo_path,
        #             x=page_width - 30 - 0.35*inch,
        #             y=header_y - 10,
        #             width=0.35*inch,
        #             height=0.35*inch,
        #             preserveAspectRatio=True,
        #             mask='auto'
        #         )
        #     except:
        #         pass

        # Draw BLACK line below header to separate it - FULL WIDTH (edge to edge)
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1.5)
        canvas.line(0, header_y - 20, page_width, header_y - 20)

        # Page number at bottom
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.gray)
        page_num_text = f"Page {doc.page}"
        canvas.drawCentredString(page_width / 2, 25, page_num_text)

        canvas.restoreState()

    # Create PDF document (Portrait mode)
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=35,
    )

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=12,
        alignment=TA_CENTER
    )

    # Date range subtitle (use timestamps as stored in database)
    if start_dt and end_dt:
        date_range = f"{start_dt.strftime('%d/%m/%Y %H:%M')} to {end_dt.strftime('%d/%m/%Y %H:%M')}"
    else:
        date_range = "All Records"

    subtitle = Paragraph(f"<b>Period:</b> {date_range} | <b>Total Records:</b> {len(readings)}", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.2*inch))

    # Table data
    table_data = [
        ['S.No', 'Date', 'Time', 'Temperature (°C)', 'Ambient Temp (°C)', 'Status']
    ]

    for idx, reading in enumerate(readings, start=1):
        # Use timestamp exactly as stored in database (no conversion)
        date_str = reading.ts_utc.strftime("%d/%m/%Y")
        time_str = reading.ts_utc.strftime("%H:%M:%S")

        ambient_temp_str = f"{reading.ambient_temp:.1f}" if reading.ambient_temp is not None else 'N/A'

        table_data.append([
            str(idx),
            date_str,
            time_str,
            f"{reading.value:.1f}",
            ambient_temp_str,
            reading.status
        ])

    # Create table (expanded widths to prevent text overlap)
    table = Table(table_data, colWidths=[0.6*inch, 1.1*inch, 1.0*inch, 1.4*inch, 1.4*inch, 0.8*inch])

    # Table style
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),

        # Status column color coding
        ('TEXTCOLOR', (5, 1), (5, -1), colors.HexColor('#059669')),  # Green for OK status
    ]))

    elements.append(table)

    # Build PDF with custom header and border on every page
    doc.build(elements, onFirstPage=add_header_and_border, onLaterPages=add_header_and_border)

    # Prepare response
    pdf_buffer.seek(0)

    # Filename with device name and current timestamp
    filename_time = utc_now()
    filename = f"{device_name}_report_{filename_time.strftime('%Y%m%d_%H%M%S')}.pdf"

    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
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
            # Return timestamp as-is (timezone-aware from database)
            result["recent_readings"].append({
                "id": reading.id,
                "device_id": reading.device_id,
                "device_name": reading.device_name,
                "temperature": reading.value,
                "status": reading.status,
                "timestamp": to_iso_utc(reading.ts_utc)
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

# Include pyrometer control routes (they have their own /api/pyrometer prefix)
router.include_router(pyrometer_router, tags=["pyrometer"])