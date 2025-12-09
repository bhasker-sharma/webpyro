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
SLAVE_ID = 1  # Device slave ID
BAUD_RATE = 9600
BYTESIZE = 8
PARITY = 'N'
STOPBITS = 1

# Register addresses (from thermometer internal parameter address table)
REGISTER_COLORIMETRIC_TEMP = 1      # Colorimetric temperature (Read only)
REGISTER_MONOCHROME_TEMP = 2        # Monochromatic temperature (Read only)
REGISTER_SLOPE = 3                  # Slope (emissivity for colorimetric) (R/W)
REGISTER_EMISSIVITY = 4             # Emissivity (monochrome) (R/W)
REGISTER_AMBIENT_TEMP = 5           # Ambient temperature inside probe (Read only)
REGISTER_MEASUREMENT_MODE = 6       # Temperature measurement mode (R/W)
REGISTER_TIME_INTERVAL = 7          # Time interval (R/W)
REGISTER_TEMP_LOWER_LIMIT = 8       # User temperature lower limit (R/W)
REGISTER_TEMP_UPPER_LIMIT = 9       # User temperature upper limit (R/W)

# Parameter valid ranges
# Emissivity (0.01 - 1.30, scaled by 1000)
MIN_EMISSIVITY = 0.01
MAX_EMISSIVITY = 1.30
MIN_EMISSIVITY_INT = int(MIN_EMISSIVITY * 1000)  # 10
MAX_EMISSIVITY_INT = int(MAX_EMISSIVITY * 1000)  # 1300

# Slope (0.800 - 1.200, scaled by 1000)
MIN_SLOPE = 0.800
MAX_SLOPE = 1.200
MIN_SLOPE_INT = int(MIN_SLOPE * 1000)  # 800
MAX_SLOPE_INT = int(MAX_SLOPE * 1000)  # 1200

# Temperature limits (device-specific, in °C)
MIN_TEMP_LIMIT = 0
MAX_TEMP_LIMIT = 3000  # Adjust based on your device specs

# Time interval (in seconds or device units - check device manual)
MIN_TIME_INTERVAL = 1
MAX_TIME_INTERVAL = 3600

# Measurement mode (device-specific values - check manual)
# Common values: 0 = Monochrome, 1 = Colorimetric, etc.
MEASUREMENT_MODES = {
    0: "Monochrome",
    1: "Colorimetric"
}

# Backward compatibility
EMISSIVITY_REGISTER_ADDRESS = REGISTER_EMISSIVITY


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


# =========================================================================
# GENERIC PARAMETER READ/WRITE FUNCTIONS
# =========================================================================

def read_parameter(register_address: int, slave_id: int = None, com_port: str = None,
                   pause_polling: bool = True, scale_factor: float = 1.0) -> float:
    """
    Generic function to read any parameter from pyrometer device.

    Args:
        register_address: Modbus register address to read from
        slave_id: Device slave ID (1-16). If None, uses default SLAVE_ID.
        com_port: COM port to use. If None, uses configured port.
        pause_polling: If True, pauses the polling service to avoid COM port conflicts.
        scale_factor: Factor to divide the raw value by (default 1.0)

    Returns:
        float: Parameter value (scaled if scale_factor provided)

    Raises:
        EmissivityError: If communication fails or value is invalid
    """
    logger.debug("=" * 60)
    logger.debug(f"READ PARAMETER REQUEST - register={register_address}, slave_id={slave_id}, com_port={com_port}")

    from app.services.polling_service import polling_service

    polling_was_running = False

    try:
        if pause_polling and polling_service.is_running:
            logger.info(f"Pausing polling service to read register {register_address}")
            polling_was_running = True
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.stop())
            import time
            time.sleep(0.5)
            logger.debug("Polling service paused, waiting 500ms for COM port release")

        device_id = slave_id if slave_id is not None else SLAVE_ID
        logger.debug(f"Using device_id: {device_id}")

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
        else:
            logger.debug("Using default Modbus client")
            client = _get_modbus_client()

        try:
            logger.debug("Attempting to connect to Modbus device...")
            if not client.connect():
                port_name = com_port if com_port else "configured port"
                logger.error(f"Connection failed to {port_name}")
                raise EmissivityError(f"Failed to connect to RS-485 device on {port_name}")

            port_name = com_port if com_port else getattr(client, 'port', getattr(client.socket, 'port', 'unknown'))
            logger.info(f"Connected successfully to {port_name}")
            logger.info(f"Reading parameter from register {register_address} (slave_id={device_id})")

            logger.debug(f"Sending read_holding_registers: address={register_address}, count=1, device_id={device_id}")
            response = client.read_holding_registers(
                address=register_address,
                count=1,
                device_id=device_id
            )

            logger.debug(f"Received response: {response}")

            if response.isError():
                logger.error(f"Modbus read error response: {response}")
                raise EmissivityError(f"Modbus read error: {response}")

            raw_value = response.registers[0]
            logger.info(f"Read raw value from register {register_address}: {raw_value}")
            logger.debug(f"Raw register value (int): {raw_value}, Binary: {bin(raw_value)}, Hex: {hex(raw_value)}")

            value = raw_value / scale_factor
            logger.info(f"Parameter read successfully from register {register_address}: {value}")
            logger.debug("=" * 60)

            return value

        except ModbusException as e:
            logger.error(f"Modbus exception while reading register {register_address}: {e}", exc_info=True)
            raise EmissivityError(f"Modbus communication error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error while reading register {register_address}: {e}", exc_info=True)
            raise EmissivityError(f"Failed to read parameter: {str(e)}")

        finally:
            client.close()

    finally:
        if polling_was_running:
            logger.info(f"Resuming polling service after reading register {register_address}")
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.start())


def write_parameter(register_address: int, value: float, slave_id: int = None,
                    com_port: str = None, pause_polling: bool = True,
                    scale_factor: float = 1.0, min_value: float = None,
                    max_value: float = None) -> None:
    """
    Generic function to write any parameter to pyrometer device.

    Args:
        register_address: Modbus register address to write to
        value: Parameter value to write
        slave_id: Device slave ID (1-16). If None, uses default SLAVE_ID.
        com_port: COM port to use. If None, uses configured port.
        pause_polling: If True, pauses the polling service to avoid COM port conflicts.
        scale_factor: Factor to multiply the value by before writing (default 1.0)
        min_value: Minimum allowed value (optional validation)
        max_value: Maximum allowed value (optional validation)

    Raises:
        EmissivityError: If value is invalid or communication fails
    """
    logger.debug("=" * 60)
    logger.debug(f"WRITE PARAMETER REQUEST - register={register_address}, value={value}, slave_id={slave_id}")

    from app.services.polling_service import polling_service

    polling_was_running = False

    try:
        if pause_polling and polling_service.is_running:
            logger.info(f"Pausing polling service to write register {register_address}")
            polling_was_running = True
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.stop())
            import time
            time.sleep(0.5)
            logger.debug("Polling service paused, waiting 500ms for COM port release")

        if not isinstance(value, (int, float)):
            raise EmissivityError(f"Parameter value must be a number, got {type(value).__name__}")

        if min_value is not None and value < min_value:
            raise EmissivityError(f"Parameter value {value} is below minimum {min_value}")

        if max_value is not None and value > max_value:
            raise EmissivityError(f"Parameter value {value} exceeds maximum {max_value}")

        logger.debug(f"Validating parameter value: {value}")
        scaled_value = int(round(value * scale_factor))
        logger.debug(f"Converted to scaled integer: {scaled_value}")

        device_id = slave_id if slave_id is not None else SLAVE_ID

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
            if not client.connect():
                port_name = com_port if com_port else "configured port"
                raise EmissivityError(f"Failed to connect to RS-485 device on {port_name}")

            port_name = com_port if com_port else getattr(client, 'port', getattr(client.socket, 'port', 'unknown'))
            logger.info(f"Connected successfully to {port_name}")
            logger.info(f"Writing to register {register_address} (slave_id={device_id}): {value} (raw: {scaled_value})")

            logger.debug(f"Sending write_register: address={register_address}, value={scaled_value}, device_id={device_id}")
            response = client.write_register(
                address=register_address,
                value=scaled_value,
                device_id=device_id
            )

            logger.debug(f"Received write response: {response}")

            if response.isError():
                logger.error(f"Modbus write error response: {response}")
                raise EmissivityError(f"Modbus write error: {response}")

            logger.info(f"Parameter written successfully to register {register_address}: {value}")
            logger.debug("=" * 60)

        except ModbusException as e:
            logger.error(f"Modbus exception while writing register {register_address}: {e}")
            raise EmissivityError(f"Modbus communication error: {str(e)}")

        except EmissivityError:
            raise

        except Exception as e:
            logger.error(f"Unexpected error while writing register {register_address}: {e}")
            raise EmissivityError(f"Failed to write parameter: {str(e)}")

        finally:
            client.close()

    finally:
        if polling_was_running:
            logger.info(f"Resuming polling service after writing register {register_address}")
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(polling_service.start())


# =========================================================================
# SPECIFIC PARAMETER WRAPPER FUNCTIONS
# =========================================================================

def read_slope(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> float:
    """Read slope (emissivity for colorimetric mode) from register 3."""
    return read_parameter(REGISTER_SLOPE, slave_id, com_port, pause_polling, scale_factor=1000.0)


def write_slope(value: float, slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> None:
    """Write slope value to register 3."""
    write_parameter(REGISTER_SLOPE, value, slave_id, com_port, pause_polling,
                   scale_factor=1000.0, min_value=MIN_EMISSIVITY, max_value=MAX_EMISSIVITY)


def read_measurement_mode(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> int:
    """Read temperature measurement mode from register 6."""
    return int(read_parameter(REGISTER_MEASUREMENT_MODE, slave_id, com_port, pause_polling))


def write_measurement_mode(mode: int, slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> None:
    """Write temperature measurement mode to register 6."""
    if mode not in MEASUREMENT_MODES:
        raise EmissivityError(f"Invalid measurement mode {mode}. Valid modes: {list(MEASUREMENT_MODES.keys())}")
    write_parameter(REGISTER_MEASUREMENT_MODE, mode, slave_id, com_port, pause_polling)


def read_time_interval(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> int:
    """Read time interval from register 7."""
    return int(read_parameter(REGISTER_TIME_INTERVAL, slave_id, com_port, pause_polling))


def write_time_interval(interval: int, slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> None:
    """Write time interval to register 7."""
    write_parameter(REGISTER_TIME_INTERVAL, interval, slave_id, com_port, pause_polling,
                   min_value=MIN_TIME_INTERVAL, max_value=MAX_TIME_INTERVAL)


def read_temp_lower_limit(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> int:
    """Read user temperature lower limit from register 8."""
    return int(read_parameter(REGISTER_TEMP_LOWER_LIMIT, slave_id, com_port, pause_polling))


def write_temp_lower_limit(temp: int, slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> None:
    """Write user temperature lower limit to register 8."""
    write_parameter(REGISTER_TEMP_LOWER_LIMIT, temp, slave_id, com_port, pause_polling,
                   min_value=MIN_TEMP_LIMIT, max_value=MAX_TEMP_LIMIT)


def read_temp_upper_limit(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> int:
    """Read user temperature upper limit from register 9."""
    return int(read_parameter(REGISTER_TEMP_UPPER_LIMIT, slave_id, com_port, pause_polling))


def write_temp_upper_limit(temp: int, slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> None:
    """Write user temperature upper limit to register 9."""
    write_parameter(REGISTER_TEMP_UPPER_LIMIT, temp, slave_id, com_port, pause_polling,
                   min_value=MIN_TEMP_LIMIT, max_value=MAX_TEMP_LIMIT)


def read_all_parameters(slave_id: int = None, com_port: str = None, pause_polling: bool = True) -> dict:
    """
    Read all writable parameters from pyrometer device at once.

    Returns:
        dict: Dictionary containing all parameter values
    """
    logger.info("Reading all parameters from device")

    params = {
        'slope': read_slope(slave_id, com_port, pause_polling),
        'emissivity': read_emissivity(slave_id, com_port, pause_polling),
        'measurement_mode': read_measurement_mode(slave_id, com_port, pause_polling),
        'time_interval': read_time_interval(slave_id, com_port, pause_polling),
        'temp_lower_limit': read_temp_lower_limit(slave_id, com_port, pause_polling),
        'temp_upper_limit': read_temp_upper_limit(slave_id, com_port, pause_polling)
    }

    logger.info(f"All parameters read successfully: {params}")
    return params
