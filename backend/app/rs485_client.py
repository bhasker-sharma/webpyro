"""
RS-485 Modbus RTU Client for Pyrometer Emissivity Control

This module provides functions to read and write emissivity values to the pyrometer
device via RS-485 serial communication using Modbus RTU protocol.

Emissivity values are stored as scaled integers: emissivity × 1000
Example: 0.95 → 950
"""

import logging
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from app.config import get_settings

logger = logging.getLogger(__name__)

# Modbus configuration
EMISSIVITY_REGISTER_ADDRESS = 4  # Holding register address for emissivity
SLAVE_ID = 1  # Device slave ID
BAUD_RATE = 9600
BYTESIZE = 8
PARITY = 'N'
STOPBITS = 1

# Emissivity valid range
MIN_EMISSIVITY = 0.20
MAX_EMISSIVITY = 1.00

# Scaled integer range (emissivity × 1000)
MIN_EMISSIVITY_INT = int(MIN_EMISSIVITY * 1000)
MAX_EMISSIVITY_INT = int(MAX_EMISSIVITY * 1000)


class EmissivityError(Exception):
    """Custom exception for emissivity-related errors"""
    pass


def _get_modbus_client() -> ModbusSerialClient:
    """
    Create and return a Modbus serial client instance.

    Returns:
        ModbusSerialClient: Configured Modbus serial client
    """
    settings = get_settings()
    port = 'COM3'  # Default fallback - should always pass com_port in production

    client = ModbusSerialClient(
        port=port,
        baudrate=BAUD_RATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS,
        timeout=settings.modbus_timeout
    )

    return client


def _validate_emissivity(value: float) -> None:
    """
    Validate emissivity value range.

    Args:
        value: Emissivity value to validate

    Raises:
        EmissivityError: If value is out of valid range
    """
    if not isinstance(value, (int, float)):
        raise EmissivityError(f"Emissivity must be a number, got {type(value).__name__}")

    if value < MIN_EMISSIVITY or value > MAX_EMISSIVITY:
        raise EmissivityError(
            f"Emissivity must be between {MIN_EMISSIVITY} and {MAX_EMISSIVITY}, got {value}"
        )


def _float_to_int(emissivity: float) -> int:
    """
    Convert emissivity float to scaled integer.

    Args:
        emissivity: Emissivity value (0.20-1.00)

    Returns:
        int: Scaled integer value (200-1000)
    """
    return int(round(emissivity * 1000))


def _int_to_float(value: int) -> float:
    """
    Convert scaled integer to emissivity float.

    Args:
        value: Scaled integer value (200-1000)

    Returns:
        float: Emissivity value (0.20-1.00)
    """
    return value / 1000.0


def read_emissivity(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> float:
    """
    Read emissivity value from pyrometer device.

    Uses Modbus function 0x03 (Read Holding Registers) to read the emissivity
    value from register address 4.

    Args:
        slave_id: Device slave ID (1-16). If None, uses default SLAVE_ID.
        com_port: COM port to use. If None, uses configured port.
        pause_polling: If True, pauses the polling service to avoid COM port conflicts.

    Returns:
        float: Emissivity value (0.20-1.00)

    Raises:
        EmissivityError: If communication fails or value is invalid
    """
    logger.debug("=" * 60)
    logger.debug(f"READ EMISSIVITY REQUEST - slave_id={slave_id}, com_port={com_port}, pause_polling={pause_polling}")

    # Import here to avoid circular dependency
    from app.services.polling_service import polling_service

    polling_was_running = False

    try:
        # Pause polling if requested to avoid COM port conflicts
        if pause_polling and polling_service.is_running:
            logger.info("Pausing polling service to read emissivity")
            polling_was_running = True
            # Stop polling service (async operation, need to run in event loop)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.stop())
            # Give a moment for polling to release the port
            import time
            time.sleep(0.5)
            logger.debug("Polling service paused, waiting 500ms for COM port release")

        # Use provided slave_id or default
        device_id = slave_id if slave_id is not None else SLAVE_ID
        logger.debug(f"Using device_id: {device_id}")

        # Get client with specified or default COM port
        if com_port:
            logger.debug(f"Creating Modbus client for COM port: {com_port}")
            settings = get_settings()
            client = ModbusSerialClient(
                port=com_port,
                baudrate=BAUD_RATE,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=settings.modbus_timeout
            )
            logger.debug(f"Client config: port={com_port}, baud={BAUD_RATE}, timeout={settings.modbus_timeout}s")
        else:
            logger.debug("Using default Modbus client")
            client = _get_modbus_client()

        try:
            # Connect to device
            logger.debug("Attempting to connect to Modbus device...")
            if not client.connect():
                port_name = com_port if com_port else "configured port"
                logger.error(f"Connection failed to {port_name}")
                raise EmissivityError(f"Failed to connect to RS-485 device on {port_name}")

            # Get port name for logging (different pymodbus versions have different attributes)
            port_name = com_port if com_port else getattr(client, 'port', getattr(client.socket, 'port', 'unknown'))
            logger.info(f"Connected successfully to {port_name}")
            logger.info(f"Reading emissivity from device (slave_id={device_id}, register={EMISSIVITY_REGISTER_ADDRESS})")

            # Read holding register (function code 0x03)
            # Note: pymodbus uses 0-based addressing, so we read from address 4
            # Use 'device_id' parameter for this pymodbus version
            logger.debug(f"Sending read_holding_registers command: address={EMISSIVITY_REGISTER_ADDRESS}, count=1, device_id={device_id}")
            response = client.read_holding_registers(
                address=EMISSIVITY_REGISTER_ADDRESS,
                count=1,
                device_id=device_id
            )

            logger.debug(f"Received response: {response}")

            # Check for errors
            if response.isError():
                logger.error(f"Modbus read error response: {response}")
                raise EmissivityError(f"Modbus read error: {response}")

            # Extract value
            emissivity_int = response.registers[0]
            logger.info(f"Read raw value: {emissivity_int}")
            logger.debug(f"Raw register value (int): {emissivity_int}, Binary: {bin(emissivity_int)}, Hex: {hex(emissivity_int)}")

            # Validate range
            if emissivity_int < MIN_EMISSIVITY_INT or emissivity_int > MAX_EMISSIVITY_INT:
                logger.warning(f"Read emissivity value {emissivity_int} is out of range ({MIN_EMISSIVITY_INT}-{MAX_EMISSIVITY_INT})")

            # Convert to float
            emissivity = _int_to_float(emissivity_int)
            logger.info(f"Emissivity read successfully: {emissivity}")
            logger.debug("=" * 60)

            return emissivity

        except ModbusException as e:
            logger.error(f"Modbus exception while reading emissivity: {e}", exc_info=True)
            raise EmissivityError(f"Modbus communication error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error while reading emissivity: {e}", exc_info=True)
            raise EmissivityError(f"Failed to read emissivity: {str(e)}")

        finally:
            # Always close connection
            client.close()

    finally:
        # Resume polling if it was running before
        if polling_was_running:
            logger.info("Resuming polling service after emissivity read")
            import asyncio
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.start())


def write_emissivity(value: float, slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> None:
    """
    Write emissivity value to pyrometer device.

    Uses Modbus function 0x06 (Write Single Register) to write the emissivity
    value to register address 4.

    Args:
        value: Emissivity value to write (0.20-1.00)
        slave_id: Device slave ID (1-16). If None, uses default SLAVE_ID.
        com_port: COM port to use. If None, uses configured port.
        pause_polling: If True, pauses the polling service to avoid COM port conflicts.

    Raises:
        EmissivityError: If value is invalid or communication fails
    """
    logger.debug("=" * 60)
    logger.debug(f"WRITE EMISSIVITY REQUEST - value={value}, slave_id={slave_id}, com_port={com_port}, pause_polling={pause_polling}")

    # Import here to avoid circular dependency
    from app.services.polling_service import polling_service

    polling_was_running = False

    try:
        # Pause polling if requested to avoid COM port conflicts
        if pause_polling and polling_service.is_running:
            logger.info("Pausing polling service to write emissivity")
            polling_was_running = True
            # Stop polling service (async operation, need to run in event loop)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.stop())
            # Give a moment for polling to release the port
            import time
            time.sleep(0.5)
            logger.debug("Polling service paused, waiting 500ms for COM port release")

        # Validate input
        logger.debug(f"Validating emissivity value: {value}")
        _validate_emissivity(value)
        logger.debug("Validation passed")

        # Convert to scaled integer
        emissivity_int = _float_to_int(value)
        logger.debug(f"Converted to scaled integer: {emissivity_int}")

        # Use provided slave_id or default
        device_id = slave_id if slave_id is not None else SLAVE_ID

        # Get client with specified or default COM port
        if com_port:
            settings = get_settings()
            client = ModbusSerialClient(
                port=com_port,
                baudrate=BAUD_RATE,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=settings.modbus_timeout
            )
        else:
            client = _get_modbus_client()

        try:
            # Connect to device
            if not client.connect():
                port_name = com_port if com_port else "configured port"
                raise EmissivityError(f"Failed to connect to RS-485 device on {port_name}")

            # Get port name for logging
            port_name = com_port if com_port else getattr(client, 'port', getattr(client.socket, 'port', 'unknown'))
            logger.info(f"Connected successfully to {port_name}")
            logger.info(f"Writing emissivity to device (slave_id={device_id}): {value} (raw: {emissivity_int})")

            # Write single register (function code 0x06)
            # Use 'device_id' parameter for this pymodbus version
            logger.debug(f"Sending write_register command: address={EMISSIVITY_REGISTER_ADDRESS}, value={emissivity_int}, device_id={device_id}")
            response = client.write_register(
                address=EMISSIVITY_REGISTER_ADDRESS,
                value=emissivity_int,
                device_id=device_id
            )

            logger.debug(f"Received write response: {response}")

            # Check for errors
            if response.isError():
                logger.error(f"Modbus write error response: {response}")
                raise EmissivityError(f"Modbus write error: {response}")

            logger.info(f"Emissivity written successfully: {value}")
            logger.debug("=" * 60)

        except ModbusException as e:
            logger.error(f"Modbus exception while writing emissivity: {e}")
            raise EmissivityError(f"Modbus communication error: {str(e)}")

        except EmissivityError:
            # Re-raise EmissivityError as-is
            raise

        except Exception as e:
            logger.error(f"Unexpected error while writing emissivity: {e}")
            raise EmissivityError(f"Failed to write emissivity: {str(e)}")

        finally:
            # Always close connection
            client.close()

    finally:
        # Resume polling if it was running before
        if polling_was_running:
            logger.info("Resuming polling service after emissivity write")
            import asyncio
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.start())


def test_connection() -> bool:
    """
    Test RS-485 connection to pyrometer device.

    Returns:
        bool: True if connection successful, False otherwise
    """
    client = _get_modbus_client()

    try:
        connected = client.connect()
        if connected:
            logger.info(f"RS-485 connection test successful on {client.port}")
        else:
            logger.error(f"RS-485 connection test failed on {client.port}")
        return connected

    except Exception as e:
        logger.error(f"RS-485 connection test exception: {e}")
        return False

    finally:
        client.close()
