"""
Modbus Test Script
Run this independently to test Modbus communication
WITHOUT starting the full FastAPI server
"""

import sys
import os

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.modbus_service import modbus_service
import time


def test_single_device():
    """
    Test reading from a single device
    """
    print("=" * 70)
    print("MODBUS COMMUNICATION TEST - SINGLE DEVICE")
    print("=" * 70)
    print()
    
    test_device = {
        'id': 1,
        'name': 'Test Device 1',
        'slave_id': 1,
        'baud_rate': 9600,
        'com_port': 'COM2',
        'modbus_address': 4002,
        'function_code': 3,
        'start_register': 1,
        'register_count': 1
    }
    
    print("Test Configuration:")
    print(f"   Device Name    : {test_device['name']}")
    print(f"   COM Port       : {test_device['com_port']}")
    print(f"   Baud Rate      : {test_device['baud_rate']}")
    print(f"   Slave ID       : {test_device['slave_id']}")
    print(f"   Function Code  : {test_device['function_code']}")
    print(f"   Start Register : {test_device['start_register']}")
    print(f"   Register Count : {test_device['register_count']}")
    print()
    print("-" * 70)
    print()
    
    print("Attempting to read temperature...")
    print()
    
    result = modbus_service.read_temperature(test_device)
    
    print()
    print("-" * 70)
    print("RESULT:")
    print("-" * 70)
    print(f"   Device Name    : {result['device_name']}")
    print(f"   Status         : {result['status']}")
    
    if result['temperature'] is not None:
        print(f"   Temperature    : {result['temperature']}C")
    else:
        print(f"   Temperature    : N/A")
    
    print(f"   Raw Hex        : {result['raw_hex']}")
    print(f"   Timestamp      : {result['timestamp']}")
    
    if result['error_message']:
        print(f"   ERROR: {result['error_message']}")
    
    print("=" * 70)
    print()
    
    modbus_service.disconnect()
    return result


def test_multiple_devices_once():
    """
    Test reading from multiple devices (one read each)
    """
    print("=" * 70)
    print("MODBUS COMMUNICATION TEST - ALL DEVICES (Single Read)")
    print("=" * 70)
    print()
    
    # Ask user how many devices to test
    try:
        num_devices = int(input("How many devices to test (1-16)? ").strip())
        if num_devices < 1 or num_devices > 16:
            print("Invalid number! Using 4 devices.")
            num_devices = 4
    except ValueError:
        print("Invalid input! Using 4 devices.")
        num_devices = 4
    
    print()
    print(f"Testing {num_devices} devices...")
    print("-" * 70)
    print()
    
    # Test each device
    for slave_id in range(1, num_devices + 1):
        test_device = {
            'id': slave_id,
            'name': f'Device {slave_id}',
            'slave_id': slave_id,
            'baud_rate': 9600,
            'com_port': 'COM2',
            'modbus_address': 4002,
            'function_code': 3,
            'start_register': 1,
            'register_count': 1
        }
        
        print(f"Reading Device {slave_id}...", end=' ')
        result = modbus_service.read_temperature(test_device)
        
        if result['status'] == 'OK':
            print(f"SUCCESS: {result['temperature']}C")
        else:
            print(f"ERROR: {result['error_message']}")
    
    print()
    print("=" * 70)
    print()
    
    modbus_service.disconnect()


def test_continuous_all_devices():
    """
    Test reading from multiple devices continuously
    """
    print("=" * 70)
    print("CONTINUOUS READING TEST - ALL DEVICES")
    print("=" * 70)
    print()
    
    # Ask user how many devices to monitor
    try:
        num_devices = int(input("How many devices to monitor (1-16)? ").strip())
        if num_devices < 1 or num_devices > 16:
            print("Invalid number! Using 4 devices.")
            num_devices = 4
    except ValueError:
        print("Invalid input! Using 4 devices.")
        num_devices = 4
    
    # Ask user how many readings
    try:
        num_readings = int(input("How many readings per device (1-100)? ").strip())
        if num_readings < 1 or num_readings > 100:
            print("Invalid number! Using 10 readings.")
            num_readings = 10
    except ValueError:
        print("Invalid input! Using 10 readings.")
        num_readings = 10
    
    print()
    print(f"Monitoring {num_devices} devices, {num_readings} readings each")
    print("Press Ctrl+C to stop")
    print()
    print("-" * 70)
    print()
    
    # Create device configurations
    devices = []
    for slave_id in range(1, num_devices + 1):
        device = {
            'id': slave_id,
            'name': f'Device {slave_id}',
            'slave_id': slave_id,
            'baud_rate': 9600,
            'com_port': 'COM2',
            'modbus_address': 4002,
            'function_code': 3,
            'start_register': 1,
            'register_count': 1
        }
        devices.append(device)
    
    try:
        for reading_num in range(1, num_readings + 1):
            print(f"Reading #{reading_num}/{num_readings}")
            print("-" * 70)
            
            for device in devices:
                result = modbus_service.read_temperature(device)
                
                if result['status'] == 'OK':
                    temp = result['temperature']
                    print(f"  Device {device['slave_id']:2d} | Temp: {temp:6.2f}C | Status: OK")
                else:
                    error = result['error_message'][:40]
                    print(f"  Device {device['slave_id']:2d} | ERROR: {error}")
            
            print()
            
            # Wait before next reading (except for last one)
            if reading_num < num_readings:
                time.sleep(2)  # 2 seconds between readings
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    print()
    print("=" * 70)
    print()
    
    modbus_service.disconnect()


def test_continuous_single_device():
    """
    Test reading from one device continuously
    """
    print("=" * 70)
    print("CONTINUOUS READING TEST - SINGLE DEVICE")
    print("=" * 70)
    print()
    
    # Ask which device to monitor
    try:
        slave_id = int(input("Which device to monitor (1-16)? ").strip())
        if slave_id < 1 or slave_id > 16:
            print("Invalid ID! Using device 1.")
            slave_id = 1
    except ValueError:
        print("Invalid input! Using device 1.")
        slave_id = 1
    
    # Ask how many readings
    try:
        num_readings = int(input("How many readings (1-100)? ").strip())
        if num_readings < 1 or num_readings > 100:
            print("Invalid number! Using 10 readings.")
            num_readings = 10
    except ValueError:
        print("Invalid input! Using 10 readings.")
        num_readings = 10
    
    print()
    print(f"Monitoring Device {slave_id}, {num_readings} readings")
    print("Press Ctrl+C to stop")
    print()
    print("-" * 70)
    print()
    
    test_device = {
        'id': slave_id,
        'name': f'Device {slave_id}',
        'slave_id': slave_id,
        'baud_rate': 9600,
        'com_port': 'COM2',
        'modbus_address': 4002,
        'function_code': 3,
        'start_register': 1,
        'register_count': 1
    }
    
    try:
        for i in range(1, num_readings + 1):
            result = modbus_service.read_temperature(test_device)
            
            if result['status'] == 'OK':
                print(f"Reading #{i:2d}/{num_readings} | "
                      f"Temp: {result['temperature']:6.2f}C | "
                      f"Raw: {result['raw_hex']}")
            else:
                print(f"Reading #{i:2d}/{num_readings} | "
                      f"ERROR: {result['error_message']}")
            
            # Wait before next reading (except for last one)
            if i < num_readings:
                time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    print()
    print("=" * 70)
    print()
    
    modbus_service.disconnect()

def test_realtime_dashboard():
    """
    Display real-time dashboard of all devices (updating display)
    """
    import sys
    import logging

    print("=" * 70)
    print("REAL-TIME DASHBOARD - ALL DEVICES")
    print("=" * 70)
    print()

    # Ask user how many devices to monitor
    try:
        num_devices = int(input("How many devices to monitor (1-16)? ").strip())
        if num_devices < 1 or num_devices > 16:
            print("Invalid number! Using 4 devices.")
            num_devices = 4
    except ValueError:
        print("Invalid input! Using 4 devices.")
        num_devices = 4

    print()
    print(f"Monitoring {num_devices} devices in real-time")
    print("Press Ctrl+C to stop")
    print()
    print("=" * 70)
    print()

    # Create device configurations
    devices = []
    for slave_id in range(1, num_devices + 1):
        device = {
            'id': slave_id,
            'name': f'Device {slave_id}',
            'slave_id': slave_id,
            'baud_rate': 9600,
            'com_port': 'COM2',
            'modbus_address': 4002,
            'function_code': 3,
            'start_register': 1,
            'register_count': 1
        }
        devices.append(device)

    # Print header
    print("Live Temperature Readings:")
    print("-" * 70)
    print()

    # Temporarily disable modbus_service logging to prevent interference
    modbus_logger = logging.getLogger('app.services.modbus_service')
    original_level = modbus_logger.level
    modbus_logger.setLevel(logging.WARNING)  # Only show warnings and errors

    try:
        reading_count = 0
        first_iteration = True

        while True:
            reading_count += 1

            # Move cursor up to overwrite previous output (skip on first iteration)
            if not first_iteration:
                # Move up by number of device lines
                for _ in range(num_devices):
                    sys.stdout.write('\033[F')  # Move cursor up one line
                    sys.stdout.write('\033[K')  # Clear line
                sys.stdout.flush()
            else:
                first_iteration = False

            # Read and display each device
            for device in devices:
                result = modbus_service.read_temperature(device)

                if result['status'] == 'OK':
                    temp = result['temperature']
                    line = (f"Device {device['slave_id']:2d} | "
                           f"Temp: {temp:6.2f}C | "
                           f"Status: OK   | "
                           f"Readings: {reading_count:<5}")
                    print(line.ljust(70))  # Pad to clear any old text
                else:
                    error = result['error_message'][:25]
                    line = (f"Device {device['slave_id']:2d} | "
                           f"Temp:   ----C | "
                           f"Status: ERR  | "
                           f"Error: {error:<25}")
                    print(line.ljust(70))  # Pad to clear any old text

            # Wait 2 seconds before next update
            time.sleep(0.1)

    except KeyboardInterrupt:
        print()
        print()
        print("Stopped by user")
    finally:
        # Restore original logging level
        modbus_logger.setLevel(original_level)

    print()
    print("=" * 70)
    print()

    modbus_service.disconnect()
    
def main():
    """
    Main test menu
    """
    print()
    print("=" * 70)
    print("           MODBUS SERVICE TEST UTILITY")
    print("=" * 70)
    print()
    print("Choose a test:")
    print("  1. Single device - one reading")
    print("  2. Multiple devices - one reading each")
    print("  3. Single device - continuous readings")
    print("  4. Multiple devices - continuous readings")
    print("  5. Real-time dashboard (live updating)")
    print("  6. Exit")
    print()
    
    choice = input("Enter choice (1-6): ").strip()
    print()
    
    if choice == '1':
        test_single_device()
    elif choice == '2':
        test_multiple_devices_once()
    elif choice == '3':
        test_continuous_single_device()
    elif choice == '4':
        test_continuous_all_devices()
    elif choice == '5':
        test_realtime_dashboard()
    elif choice == '6':
        print("Goodbye!")
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()