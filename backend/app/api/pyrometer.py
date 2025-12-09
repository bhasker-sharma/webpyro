"""
Pyrometer Control API Endpoints

This module provides REST API endpoints for controlling pyrometer device parameters
such as emissivity via RS-485 Modbus RTU communication.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
import logging

from app.rs485_client import (
    read_emissivity,
    write_emissivity,
    read_slope,
    write_slope,
    read_measurement_mode,
    write_measurement_mode,
    read_time_interval,
    write_time_interval,
    read_temp_lower_limit,
    write_temp_lower_limit,
    read_temp_upper_limit,
    write_temp_upper_limit,
    read_all_parameters,
    test_connection,
    EmissivityError,
    MIN_EMISSIVITY,
    MAX_EMISSIVITY,
    MIN_TEMP_LIMIT,
    MAX_TEMP_LIMIT,
    MIN_TIME_INTERVAL,
    MAX_TIME_INTERVAL,
    MEASUREMENT_MODES
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pyrometer",
    tags=["pyrometer"]
)


# Pydantic models for request/response
class EmissivityResponse(BaseModel):
    """Response model for emissivity value"""
    emissivity: float = Field(
        ...,
        ge=MIN_EMISSIVITY,
        le=MAX_EMISSIVITY,
        description=f"Emissivity value ({MIN_EMISSIVITY}-{MAX_EMISSIVITY})"
    )
    message: str = Field(default="Success")

    class Config:
        json_schema_extra = {
            "example": {
                "emissivity": 0.95,
                "message": "Success"
            }
        }


class EmissivityRequest(BaseModel):
    """Request model for setting emissivity value"""
    emissivity: float = Field(
        ...,
        ge=MIN_EMISSIVITY,
        le=MAX_EMISSIVITY,
        description=f"Emissivity value to set ({MIN_EMISSIVITY}-{MAX_EMISSIVITY})"
    )
    slave_id: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Device slave ID (1-16)"
    )
    com_port: str = Field(
        default=None,
        description="COM port (e.g., COM3). If not specified, uses configured default."
    )

    @field_validator('emissivity')
    @classmethod
    def validate_emissivity_range(cls, v):
        """Validate emissivity is within acceptable range"""
        if v < MIN_EMISSIVITY or v > MAX_EMISSIVITY:
            raise ValueError(f'Emissivity must be between {MIN_EMISSIVITY} and {MAX_EMISSIVITY}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "emissivity": 0.95,
                "slave_id": 1,
                "com_port": "COM3"
            }
        }


class ConnectionTestResponse(BaseModel):
    """Response model for connection test"""
    connected: bool
    message: str


class ParameterRequest(BaseModel):
    """Generic request model for parameter operations"""
    value: float = Field(..., description="Parameter value")
    slave_id: int = Field(default=1, ge=1, le=16, description="Device slave ID (1-16)")
    com_port: str = Field(default=None, description="COM port (e.g., COM3)")


class ParameterResponse(BaseModel):
    """Generic response model for parameter operations"""
    value: float = Field(..., description="Parameter value")
    message: str = Field(default="Success")


class AllParametersResponse(BaseModel):
    """Response model for all parameters"""
    slope: float
    emissivity: float
    measurement_mode: int
    measurement_mode_name: str
    time_interval: int
    temp_lower_limit: int
    temp_upper_limit: int
    message: str = Field(default="Success")


# API Endpoints

@router.get("/emissivity", response_model=EmissivityResponse)
async def get_emissivity(
    slave_id: int = 1,
    com_port: str = None
):
    """
    Get current emissivity value from pyrometer device.

    Reads the emissivity parameter from the device via RS-485 Modbus RTU
    using function code 0x03 (Read Holding Registers) at register address 4.

    Args:
        slave_id: Device slave ID (1-16). Default is 1.
        com_port: COM port (e.g., COM3). If not specified, uses configured default.

    Returns:
        EmissivityResponse: Current emissivity value

    Raises:
        HTTPException 503: If device communication fails
    """
    try:
        logger.info(f"API: Reading emissivity from pyrometer (slave_id={slave_id}, com_port={com_port})")
        emissivity = read_emissivity(slave_id=slave_id, com_port=com_port)

        return EmissivityResponse(
            emissivity=emissivity,
            message=f"Emissivity read successfully from device {slave_id}"
        )

    except EmissivityError as e:
        logger.error(f"API: Failed to read emissivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with pyrometer device: {str(e)}"
        )

    except Exception as e:
        logger.error(f"API: Unexpected error reading emissivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/emissivity", response_model=EmissivityResponse)
async def set_emissivity(request: EmissivityRequest):
    """
    Set emissivity value on pyrometer device.

    Writes the emissivity parameter to the device via RS-485 Modbus RTU
    using function code 0x06 (Write Single Register) at register address 4.

    Args:
        request: EmissivityRequest containing the emissivity value, slave_id, and com_port

    Returns:
        EmissivityResponse: Confirmation with the new emissivity value

    Raises:
        HTTPException 400: If emissivity value is invalid
        HTTPException 503: If device communication fails
    """
    try:
        logger.info(f"API: Writing emissivity to pyrometer (slave_id={request.slave_id}, com_port={request.com_port}): {request.emissivity}")
        write_emissivity(request.emissivity, slave_id=request.slave_id, com_port=request.com_port)

        # Give device time to save to non-volatile memory
        import time
        logger.info("API: Waiting 1 second for device to save value...")
        time.sleep(1.0)

        # Verify the write by reading back the value
        logger.info("API: Verifying written emissivity")
        new_emissivity = read_emissivity(slave_id=request.slave_id, com_port=request.com_port)

        return EmissivityResponse(
            emissivity=new_emissivity,
            message=f"Emissivity set successfully on device {request.slave_id}"
        )

    except EmissivityError as e:
        logger.error(f"API: Failed to set emissivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with pyrometer device: {str(e)}"
        )

    except ValueError as e:
        logger.error(f"API: Invalid emissivity value: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"API: Unexpected error setting emissivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/test-connection", response_model=ConnectionTestResponse)
async def test_pyrometer_connection():
    """
    Test RS-485 connection to pyrometer device.

    Attempts to establish a connection to the pyrometer device on the
    configured serial port (RS485_PORT).

    Returns:
        ConnectionTestResponse: Connection test result

    Raises:
        HTTPException 503: If connection test fails
    """
    try:
        logger.info("API: Testing pyrometer connection")
        connected = test_connection()

        if connected:
            return ConnectionTestResponse(
                connected=True,
                message="Connection successful"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to pyrometer device. Check serial port configuration."
            )

    except Exception as e:
        logger.error(f"API: Connection test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Connection test failed: {str(e)}"
        )


@router.get("/diagnose")
async def diagnose_connection(
    slave_id: int = 1,
    com_port: str = None
):
    """
    Diagnostic endpoint to troubleshoot RS-485 connection issues.

    Returns detailed information about the connection attempt including
    any errors encountered.
    """
    import serial.tools.list_ports
    from pymodbus.client import ModbusSerialClient

    diagnostics = {
        "com_port_requested": com_port,
        "slave_id": slave_id,
        "available_ports": [],
        "connection_test": None,
        "read_test": None,
        "errors": []
    }

    try:
        # List available COM ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            diagnostics["available_ports"].append({
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid
            })

        # Determine which port to use
        port_to_use = com_port if com_port else 'COM3'  # Default fallback

        diagnostics["com_port_used"] = port_to_use

        # Test connection
        try:
            client = ModbusSerialClient(
                port=port_to_use,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2.0
            )

            if client.connect():
                diagnostics["connection_test"] = "SUCCESS - Port opened successfully"

                # Try to read emissivity
                try:
                    response = client.read_holding_registers(
                        address=4,
                        count=1,
                        device_id=slave_id
                    )

                    if response.isError():
                        diagnostics["read_test"] = f"FAILED - Modbus error: {response}"
                        diagnostics["errors"].append(f"Modbus read error: {response}")
                    else:
                        emissivity_int = response.registers[0]
                        emissivity = emissivity_int / 1000.0
                        diagnostics["read_test"] = f"SUCCESS - Read value: {emissivity_int} ({emissivity})"

                except Exception as read_error:
                    diagnostics["read_test"] = f"FAILED - {str(read_error)}"
                    diagnostics["errors"].append(f"Read error: {str(read_error)}")

                client.close()
            else:
                diagnostics["connection_test"] = f"FAILED - Could not open {port_to_use}"
                diagnostics["errors"].append(f"Failed to open COM port {port_to_use}. It may be in use by another process.")

        except Exception as conn_error:
            diagnostics["connection_test"] = f"FAILED - {str(conn_error)}"
            diagnostics["errors"].append(f"Connection error: {str(conn_error)}")

    except Exception as e:
        diagnostics["errors"].append(f"Diagnostic error: {str(e)}")

    return diagnostics


# =========================================================================
# SLOPE (REGISTER 3) ENDPOINTS
# =========================================================================

@router.get("/slope", response_model=ParameterResponse)
async def get_slope(slave_id: int = 1, com_port: str = None):
    """Get slope (colorimetric emissivity) value from pyrometer device."""
    try:
        logger.info(f"API: Reading slope from pyrometer (slave_id={slave_id}, com_port={com_port})")
        slope = read_slope(slave_id=slave_id, com_port=com_port)
        return ParameterResponse(value=slope, message=f"Slope read successfully from device {slave_id}")
    except EmissivityError as e:
        logger.error(f"API: Failed to read slope: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error reading slope: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


@router.post("/slope", response_model=ParameterResponse)
async def set_slope(request: ParameterRequest):
    """Set slope (colorimetric emissivity) value on pyrometer device."""
    try:
        logger.info(f"API: Writing slope to pyrometer (slave_id={request.slave_id}, com_port={request.com_port}): {request.value}")
        write_slope(request.value, slave_id=request.slave_id, com_port=request.com_port)
        import time
        time.sleep(1.0)
        new_slope = read_slope(slave_id=request.slave_id, com_port=request.com_port)
        return ParameterResponse(value=new_slope, message=f"Slope set successfully on device {request.slave_id}")
    except EmissivityError as e:
        logger.error(f"API: Failed to set slope: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error setting slope: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


# =========================================================================
# MEASUREMENT MODE (REGISTER 6) ENDPOINTS
# =========================================================================

@router.get("/measurement-mode", response_model=ParameterResponse)
async def get_measurement_mode(slave_id: int = 1, com_port: str = None):
    """Get temperature measurement mode from pyrometer device."""
    try:
        logger.info(f"API: Reading measurement mode from pyrometer (slave_id={slave_id}, com_port={com_port})")
        mode = read_measurement_mode(slave_id=slave_id, com_port=com_port)
        mode_name = MEASUREMENT_MODES.get(mode, "Unknown")
        return ParameterResponse(value=float(mode),
                               message=f"Measurement mode read successfully: {mode} ({mode_name})")
    except EmissivityError as e:
        logger.error(f"API: Failed to read measurement mode: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error reading measurement mode: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


@router.post("/measurement-mode", response_model=ParameterResponse)
async def set_measurement_mode(request: ParameterRequest):
    """Set temperature measurement mode on pyrometer device."""
    try:
        mode = int(request.value)
        logger.info(f"API: Writing measurement mode to pyrometer (slave_id={request.slave_id}, com_port={request.com_port}): {mode}")
        write_measurement_mode(mode, slave_id=request.slave_id, com_port=request.com_port)
        import time
        time.sleep(1.0)
        new_mode = read_measurement_mode(slave_id=request.slave_id, com_port=request.com_port)
        mode_name = MEASUREMENT_MODES.get(new_mode, "Unknown")
        return ParameterResponse(value=float(new_mode),
                               message=f"Measurement mode set successfully: {new_mode} ({mode_name})")
    except EmissivityError as e:
        logger.error(f"API: Failed to set measurement mode: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error setting measurement mode: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


# =========================================================================
# TIME INTERVAL (REGISTER 7) ENDPOINTS
# =========================================================================

@router.get("/time-interval", response_model=ParameterResponse)
async def get_time_interval(slave_id: int = 1, com_port: str = None):
    """Get time interval from pyrometer device."""
    try:
        logger.info(f"API: Reading time interval from pyrometer (slave_id={slave_id}, com_port={com_port})")
        interval = read_time_interval(slave_id=slave_id, com_port=com_port)
        return ParameterResponse(value=float(interval),
                               message=f"Time interval read successfully: {interval}")
    except EmissivityError as e:
        logger.error(f"API: Failed to read time interval: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error reading time interval: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


@router.post("/time-interval", response_model=ParameterResponse)
async def set_time_interval(request: ParameterRequest):
    """Set time interval on pyrometer device."""
    try:
        interval = int(request.value)
        logger.info(f"API: Writing time interval to pyrometer (slave_id={request.slave_id}, com_port={request.com_port}): {interval}")
        write_time_interval(interval, slave_id=request.slave_id, com_port=request.com_port)
        import time
        time.sleep(1.0)
        new_interval = read_time_interval(slave_id=request.slave_id, com_port=request.com_port)
        return ParameterResponse(value=float(new_interval),
                               message=f"Time interval set successfully: {new_interval}")
    except EmissivityError as e:
        logger.error(f"API: Failed to set time interval: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error setting time interval: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


# =========================================================================
# TEMPERATURE LOWER LIMIT (REGISTER 8) ENDPOINTS
# =========================================================================

@router.get("/temp-lower-limit", response_model=ParameterResponse)
async def get_temp_lower_limit(slave_id: int = 1, com_port: str = None):
    """Get user temperature lower limit from pyrometer device."""
    try:
        logger.info(f"API: Reading temp lower limit from pyrometer (slave_id={slave_id}, com_port={com_port})")
        temp = read_temp_lower_limit(slave_id=slave_id, com_port=com_port)
        return ParameterResponse(value=float(temp),
                               message=f"Temperature lower limit read successfully: {temp}°C")
    except EmissivityError as e:
        logger.error(f"API: Failed to read temp lower limit: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error reading temp lower limit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


@router.post("/temp-lower-limit", response_model=ParameterResponse)
async def set_temp_lower_limit(request: ParameterRequest):
    """Set user temperature lower limit on pyrometer device."""
    try:
        temp = int(request.value)
        logger.info(f"API: Writing temp lower limit to pyrometer (slave_id={request.slave_id}, com_port={request.com_port}): {temp}")
        write_temp_lower_limit(temp, slave_id=request.slave_id, com_port=request.com_port)
        import time
        time.sleep(1.0)
        new_temp = read_temp_lower_limit(slave_id=request.slave_id, com_port=request.com_port)
        return ParameterResponse(value=float(new_temp),
                               message=f"Temperature lower limit set successfully: {new_temp}°C")
    except EmissivityError as e:
        logger.error(f"API: Failed to set temp lower limit: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error setting temp lower limit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


# =========================================================================
# TEMPERATURE UPPER LIMIT (REGISTER 9) ENDPOINTS
# =========================================================================

@router.get("/temp-upper-limit", response_model=ParameterResponse)
async def get_temp_upper_limit(slave_id: int = 1, com_port: str = None):
    """Get user temperature upper limit from pyrometer device."""
    try:
        logger.info(f"API: Reading temp upper limit from pyrometer (slave_id={slave_id}, com_port={com_port})")
        temp = read_temp_upper_limit(slave_id=slave_id, com_port=com_port)
        return ParameterResponse(value=float(temp),
                               message=f"Temperature upper limit read successfully: {temp}°C")
    except EmissivityError as e:
        logger.error(f"API: Failed to read temp upper limit: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error reading temp upper limit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


@router.post("/temp-upper-limit", response_model=ParameterResponse)
async def set_temp_upper_limit(request: ParameterRequest):
    """Set user temperature upper limit on pyrometer device."""
    try:
        temp = int(request.value)
        logger.info(f"API: Writing temp upper limit to pyrometer (slave_id={request.slave_id}, com_port={request.com_port}): {temp}")
        write_temp_upper_limit(temp, slave_id=request.slave_id, com_port=request.com_port)
        import time
        time.sleep(1.0)
        new_temp = read_temp_upper_limit(slave_id=request.slave_id, com_port=request.com_port)
        return ParameterResponse(value=float(new_temp),
                               message=f"Temperature upper limit set successfully: {new_temp}°C")
    except EmissivityError as e:
        logger.error(f"API: Failed to set temp upper limit: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error setting temp upper limit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")


# =========================================================================
# ALL PARAMETERS ENDPOINT
# =========================================================================

@router.get("/all-parameters", response_model=AllParametersResponse)
async def get_all_parameters(slave_id: int = 1, com_port: str = None):
    """Get all writable parameters from pyrometer device at once."""
    try:
        logger.info(f"API: Reading all parameters from pyrometer (slave_id={slave_id}, com_port={com_port})")
        params = read_all_parameters(slave_id=slave_id, com_port=com_port)

        mode_name = MEASUREMENT_MODES.get(params['measurement_mode'], "Unknown")

        return AllParametersResponse(
            slope=params['slope'],
            emissivity=params['emissivity'],
            measurement_mode=params['measurement_mode'],
            measurement_mode_name=mode_name,
            time_interval=params['time_interval'],
            temp_lower_limit=params['temp_lower_limit'],
            temp_upper_limit=params['temp_upper_limit'],
            message="All parameters read successfully"
        )
    except EmissivityError as e:
        logger.error(f"API: Failed to read all parameters: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail=f"Failed to communicate with pyrometer device: {str(e)}")
    except Exception as e:
        logger.error(f"API: Unexpected error reading all parameters: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Unexpected error: {str(e)}")
