"""
Modbus Service
Handles communication with Modbus RTU devices over RS485/Serial
"""
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import struct
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Optional
from app.config import get_settings

# Setup logging
logger = logging.getLogger(__name__)
settings = get_settings()


class ModbusService:
    """
    Service to communicate with Modbus temperature devices
    Thread-safe for RS485 serial communication (only one device at a time)
    """

    def __init__(self):
        """Initialize with default values"""
        self.client = None
        self.current_port = None
        self.current_baudrate = None
        self._lock = threading.Lock()  # Ensure only one device reads at a time
    
    def connect(self, port: str, baudrate: int, timeout: int = None) -> bool:
        """
        Connect to serial port

        Args:
            port: COM port (e.g., 'COM3')
            baudrate: Baud rate (e.g., 9600)
            timeout: Connection timeout in seconds

        Returns:
            True if connected, False otherwise
        """
        try:
            # Close existing connection if different port/baudrate
            if self.client and (port != self.current_port or baudrate != self.current_baudrate):
                logger.info(f"Switching connection from {self.current_port}@{self.current_baudrate} to {port}@{baudrate}")
                self.disconnect()

            # Create client if needed
            if not self.client:
                # Use timeout from settings if not specified
                if timeout is None:
                    timeout = settings.modbus_timeout

                logger.info(f"Attempting Modbus connection to {port} at {baudrate} baud (timeout: {timeout}s)...")

                self.client = ModbusSerialClient(
                    port=port,
                    baudrate=baudrate,
                    bytesize=8,
                    parity='N',  # None
                    stopbits=1,
                    timeout=timeout
                )

                # Try to connect
                if self.client.connect():
                    self.current_port = port
                    self.current_baudrate = baudrate
                    logger.info(f"Modbus connection established to {port}")
                    return True
                else:
                    logger.error(f"Modbus connection FAILED to {port} - Port may be in use or not available")
                    self.client = None
                    return False

            return True

        except Exception as e:
            logger.error(f"Modbus connection error on {port}: {type(e).__name__}: {e}", exc_info=True)
            self.client = None
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.client:
            try:
                self.client.close()
                logger.info(f"Modbus connection closed from {self.current_port}")
            except Exception as e:
                logger.error(f"Error during Modbus disconnect from {self.current_port}: {e}", exc_info=True)
            finally:
                self.client = None
                self.current_port = None
                self.current_baudrate = None
    
    def read_temperature(self, device_config: Dict) -> Dict:

        device_name = device_config.get('name', 'Unknown')
        device_id = device_config.get('id', 0)
        slave_id = device_config.get('slave_id', 1)

        result = {
            'device_id': device_id,
            'device_name': device_name,
            'temperature': None,
            'ambient_temp': None,
            'status': 'Err',
            'raw_hex': '',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_message': ''
        }

        # Use lock to ensure only one device reads at a time (critical for RS485)
        with self._lock:
            try:
                # Connect to serial port
                port = device_config.get('com_port', 'COM3')
                baudrate = device_config.get('baud_rate', 9600)

                if not self.connect(port, baudrate):
                    result['error_message'] = f"Cannot connect to {port}"
                    logger.error(f"{device_name} (ID:{device_id}): Connection failed - {result['error_message']}")
                    return result

                # Verify client is connected before attempting to read
                if not self.client:
                    result['error_message'] = f"Modbus client not initialized"
                    logger.error(f"{device_name} (ID:{device_id}): Modbus client not initialized")
                    return result

                # Get Modbus parameters
                function_code = device_config.get('function_code', 3)
                start_register = device_config.get('start_register', 0)
                register_count = device_config.get('register_count', 2)

                # Only log device reads at DEBUG level (won't appear in production logs)
                logger.debug(f"Reading {device_name} (Slave:{slave_id}, Func:{function_code}, Reg:{start_register})")

                # Clear any stale data from previous device (critical for RS485 bus with many devices)
                try:
                    if hasattr(self.client, 'socket') and self.client.socket:
                        # Flush input buffer to clear any crosstalk from other devices
                        if hasattr(self.client.socket, 'reset_input_buffer'):
                            self.client.socket.reset_input_buffer()
                except Exception:
                    pass  # Ignore if socket doesn't support flush

                # Read registers based on function code
                if function_code == 3:
                    # Read Holding Registers (Function Code 3)
                    response = self.client.read_holding_registers(
                        address=start_register,
                        count=register_count,
                        device_id=slave_id
                    )
                elif function_code == 4:
                    # Read Input Registers (Function Code 4)
                    response = self.client.read_input_registers(
                        address=start_register,
                        count=register_count,
                        device_id=slave_id
                    )
                else:
                    result['error_message'] = f"Invalid function code: {function_code}"
                    logger.error(f"❌ {device_name}: {result['error_message']}")
                    return result

                # Check for errors in response
                if response.isError():
                    result['error_message'] = f"Modbus error: {response}"
                    logger.error(f"{device_name} (ID:{device_id}, Slave:{slave_id}): Modbus read error - {result['error_message']}")
                    logger.error(f"  Port: {port}, Baud: {baudrate}, Function: {function_code}, Register: {start_register}")
                    return result

                # Get register values
                registers = response.registers

                # Convert raw hex for logging
                result['raw_hex'] = ' '.join([f'{reg:04X}' for reg in registers])

                # Only log raw data at DEBUG level (too verbose for production)
                logger.debug(f"{device_name}: registers={registers}, hex={result['raw_hex']}")

                # Decode temperature based on register count
                if register_count == 1:
                    # 16-bit integer (single register)
                    # Assume temperature is in 0.1°C units (e.g., 235 = 23.5°C)
                    temp_raw = registers[0]
                    temperature = temp_raw

                elif register_count == 2:
                    # 32-bit float (two registers)
                    # Combine two 16-bit registers into one 32-bit float
                    # Big-endian byte order (register[0] is high word)
                    byte_data = struct.pack('>HH', registers[0], registers[1])
                    temperature = struct.unpack('>f', byte_data)[0]
                else:
                    result['error_message'] = f"Unsupported register count: {register_count}"
                    logger.error(f"❌ {device_name}: {result['error_message']}")
                    return result

                # Validate temperature (sanity check)
                if -50 <= temperature <= 1500:  # Reasonable range for pyrometer
                    result['temperature'] = round(temperature, 2)
                    result['status'] = 'OK'
                    # Don't log successful reads (too verbose) - only errors
                else:
                    result['temperature'] = temperature
                    result['status'] = 'Err'
                    result['error_message'] = f"Temperature out of range: {temperature}"
                    logger.warning(f"{device_name} (ID:{device_id}): Temperature out of range: {temperature}°C")

                # Read ambient temperature from separate register
                try:
                    ambient_start_register = settings.ambient_temp_start_register
                    logger.debug(f"{device_name}: Reading ambient temp from register {ambient_start_register}")

                    # Read ambient temperature registers based on function code
                    if function_code == 3:
                        ambient_response = self.client.read_holding_registers(
                            address=ambient_start_register,
                            count=register_count,
                            device_id=slave_id
                        )
                    elif function_code == 4:
                        ambient_response = self.client.read_input_registers(
                            address=ambient_start_register,
                            count=register_count,
                            device_id=slave_id
                        )

                    # Check for errors in ambient response
                    if not ambient_response.isError():
                        ambient_registers = ambient_response.registers

                        # Decode ambient temperature based on register count
                        if register_count == 1:
                            ambient_temp_raw = ambient_registers[0]
                            ambient_temperature = ambient_temp_raw
                        elif register_count == 2:
                            ambient_byte_data = struct.pack('>HH', ambient_registers[0], ambient_registers[1])
                            ambient_temperature = struct.unpack('>f', ambient_byte_data)[0]

                        # Validate ambient temperature
                        if -50 <= ambient_temperature <= 1500:
                            result['ambient_temp'] = round(ambient_temperature, 2)
                            # Don't log successful ambient reads (too verbose)
                        else:
                            logger.warning(f"{device_name} (ID:{device_id}): Ambient temp out of range: {ambient_temperature}°C")
                    else:
                        logger.warning(f"{device_name} (ID:{device_id}): Failed to read ambient temp: {ambient_response}")
                except Exception as ambient_error:
                    # Only log first ambient error, then suppress (reduces noise)
                    logger.debug(f"{device_name}: Ambient read error: {ambient_error}")
                    # Don't fail the entire reading if ambient temp fails

                return result

            except ModbusException as e:
                result['error_message'] = f"Modbus exception: {str(e)}"
                logger.error(f"{device_name} (ID:{device_id}, Slave:{slave_id}): Modbus exception", exc_info=True)
                logger.error(f"  Port: {port}, Baud: {baudrate}, Error: {result['error_message']}")
                return result

            except Exception as e:
                result['error_message'] = f"Unexpected error: {str(e)}"
                logger.error(f"{device_name} (ID:{device_id}, Slave:{slave_id}): Unexpected error during temperature read", exc_info=True)
                logger.error(f"  Port: {port}, Baud: {baudrate}, Error: {result['error_message']}")
                return result
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


# Create singleton instance
modbus_service = ModbusService()