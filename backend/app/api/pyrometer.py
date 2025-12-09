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
    test_connection,
    EmissivityError,
    MIN_EMISSIVITY,
    MAX_EMISSIVITY
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
