"""
Modbus Service
Handles communication with Modbus RTU devices over RS485/Serial
"""
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import struct
import logging
from datetime import datetime
from typing import Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModbusService:
    """
    Service to communicate with Modbus temperature devices
    """
    
    def __init__(self):
        """Initialize with default values"""
        self.client = None
        self.current_port = None
        self.current_baudrate = None
    
    def connect(self, port: str, baudrate: int, timeout: int = 5) -> bool:
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
                self.disconnect()
            
            # Create client if needed
            if not self.client:
                logger.info(f"Connecting to {port} at {baudrate} baud...")
                
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
                    logger.info(f"✅ Connected to {port}")
                    return True
                else:
                    logger.error(f"❌ Failed to connect to {port}")
                    self.client = None
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            self.client = None
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.client:
            try:
                self.client.close()
                logger.info(f"Disconnected from {self.current_port}")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.client = None
                self.current_port = None
                self.current_baudrate = None
    
    def read_temperature(self, device_config: Dict) -> Dict:
        """
        Read temperature from a Modbus device
        
        Args:
            device_config: Dictionary with device settings:
                - name: Device name
                - slave_id: Modbus slave ID (1-247)
                - baud_rate: Baud rate
                - com_port: COM port
                - register_address: Starting register
                - function_code: 3 (Holding) or 4 (Input)
                - start_register: Register to read from
                - register_count: Number of registers (1 or 2)
        
        Returns:
            Dictionary with:
                - device_id: Device database ID
                - device_name: Device name
                - temperature: Temperature value (float)
                - status: 'OK', 'Stale', or 'Err'
                - raw_hex: Raw response in hex
                - timestamp: Reading timestamp
                - error_message: Error details (if status='Err')
        """
        
        device_name = device_config.get('name', 'Unknown')
        device_id = device_config.get('id', 0)
        slave_id = device_config.get('slave_id', 1)
        
        result = {
            'device_id': device_id,
            'device_name': device_name,
            'temperature': None,
            'status': 'Err',
            'raw_hex': '',
            'timestamp': datetime.utcnow().isoformat(),
            'error_message': ''
        }
        
        try:
            # Connect to serial port
            port = device_config.get('com_port', 'COM3')
            baudrate = device_config.get('baud_rate', 9600)
            
            if not self.connect(port, baudrate):
                result['error_message'] = f"Cannot connect to {port}"
                logger.error(f"❌ {device_name}: {result['error_message']}")
                return result
            
            # Get Modbus parameters
            function_code = device_config.get('function_code', 3)
            start_register = device_config.get('start_register', 0)
            register_count = device_config.get('register_count', 2)
            
            logger.info(f"📡 Reading {device_name} (Slave ID: {slave_id})...")
            logger.info(f"   Function: {function_code}, Register: {start_register}, Count: {register_count}")
            
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
                logger.error(f"❌ {device_name}: {result['error_message']}")
                return result
            
            # Get register values
            registers = response.registers
            logger.info(f"   Raw registers: {registers}")
            
            # Convert raw hex for logging
            result['raw_hex'] = ' '.join([f'{reg:04X}' for reg in registers])
            logger.info(f"   Raw hex: {result['raw_hex']}")
            
            # Decode temperature based on register count
            if register_count == 1:
                # 16-bit integer (single register)
                # Assume temperature is in 0.1°C units (e.g., 235 = 23.5°C)
                temp_raw = registers[0]
                temperature = temp_raw / 10.0
                
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
                logger.info(f"✅ {device_name}: {temperature:.2f}°C - Status: OK")
            else:
                result['temperature'] = temperature
                result['status'] = 'Err'
                result['error_message'] = f"Temperature out of range: {temperature}"
                logger.warning(f"⚠️  {device_name}: {result['error_message']}")
            
            return result
            
        except ModbusException as e:
            result['error_message'] = f"Modbus exception: {str(e)}"
            logger.error(f"❌ {device_name}: {result['error_message']}")
            return result
            
        except Exception as e:
            result['error_message'] = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {device_name}: {result['error_message']}")
            return result
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


# Create singleton instance
modbus_service = ModbusService()