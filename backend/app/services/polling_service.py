"""
Polling Service
Continuously reads temperature from all enabled Modbus devices
"""

import asyncio
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.device import DeviceSettings
from app.services.modbus_service import modbus_service
from app.services.buffer_service import reading_buffer
from app.services.websocket_service import websocket_manager
from app.config import get_settings
from app.utils.datetime_utils import parse_iso_ist

logger = logging.getLogger(__name__)
settings = get_settings()


class PollingService:
    """
    Background service that continuously polls Modbus devices
    """
    
    def __init__(self):
        self.is_running = False
        self.polling_task = None
        self.cycle_count = 0
        
    async def start(self):
        """Start the polling service"""
        if self.is_running:
            logger.warning("Polling service start requested but already running")
            return

        self.is_running = True
        logger.info("=" * 60)
        logger.info("POLLING SERVICE STARTING (SINGLE DEVICE CONTINUOUS MODE)...")
        logger.info("Reading continuously from single device (Slave ID 1)")
        logger.info("No polling interval - data comes at device read speed")
        logger.info("=" * 60)

        # Start polling task
        self.polling_task = asyncio.create_task(self._polling_loop())

        logger.info("Polling service started successfully")
    
    async def stop(self):
        """Stop the polling service"""
        if not self.is_running:
            logger.warning("Polling service stop requested but not running")
            return

        logger.info("=" * 60)
        logger.info("POLLING SERVICE STOPPING...")
        logger.info("=" * 60)
        self.is_running = False

        # Cancel polling task
        if self.polling_task:
            logger.info("Cancelling polling task...")
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                logger.info("Polling task cancelled successfully")

        # Flush remaining buffer data to database
        logger.info("Flushing remaining buffer data to database...")
        try:
            reading_buffer.flush_all()
            logger.info("Buffer flushed successfully")
        except Exception as e:
            logger.error(f"Error flushing buffer: {e}", exc_info=True)

        # Disconnect Modbus
        logger.info("Disconnecting Modbus service...")
        try:
            modbus_service.disconnect()
            logger.info("Modbus disconnected successfully")
        except Exception as e:
            logger.error(f"Error disconnecting Modbus: {e}", exc_info=True)

        logger.info("Polling service stopped successfully")
        logger.info("=" * 60)

    async def restart(self):
        """
        Restart the polling service
        Useful when device configurations are changed
        """
        logger.info("=" * 60)
        logger.info("POLLING SERVICE RESTART REQUESTED")
        logger.info("=" * 60)
        await self.stop()
        await asyncio.sleep(1)  # Brief pause between stop and start
        await self.start()
        logger.info("Polling service restarted successfully")
    
    def _get_enabled_devices(self) -> List[DeviceSettings]:
        """
        Get all enabled devices from database

        Returns:
            List of enabled DeviceSettings
        """
        db = SessionLocal()
        try:
            devices = db.query(DeviceSettings).filter(
                DeviceSettings.enabled == True
            ).order_by(DeviceSettings.slave_id).all()

            # Don't log every device retrieval (too verbose)
            return devices
        except Exception as e:
            logger.error(f"Error retrieving enabled devices from database: {e}", exc_info=True)
            return []
        finally:
            db.close()

    def _calculate_dynamic_interval(self, num_devices: int) -> float:
        """
        Calculate polling interval dynamically based on number of enabled devices

        Formula: min(max(num_devices * per_device_time * safety_factor, min_interval), max_interval)

        Args:
            num_devices: Number of enabled devices

        Returns:
            Calculated poll interval in seconds
        """
        if not settings.modbus_enable_dynamic_polling:
            # Dynamic polling disabled - use static interval from .env
            return settings.modbus_poll_interval

        # Calculate interval based on number of devices
        calculated_interval = num_devices * settings.modbus_per_device_time * settings.modbus_safety_factor

        # Apply min/max bounds
        dynamic_interval = max(
            settings.modbus_min_poll_interval,
            min(calculated_interval, settings.modbus_max_poll_interval)
        )

        return dynamic_interval

    async def _polling_loop(self):
        """
        Main continuous reading loop for single device
        Reads continuously without polling intervals
        """
        logger.info("Continuous reading loop started (single device mode)")

        while self.is_running:
            try:
                self.cycle_count += 1
                cycle_start = datetime.now()

                # Get enabled devices (should be only one in single device mode)
                devices = self._get_enabled_devices()

                if not devices:
                    if self.cycle_count == 1:
                        logger.warning("No enabled device found on first cycle, waiting...")
                    elif self.cycle_count % 20 == 0:  # Log every 20th cycle to reduce spam
                        logger.warning(f"Still no enabled device found (cycle #{self.cycle_count}), waiting...")
                    await asyncio.sleep(5)
                    continue

                # Single device mode - use first device only
                device = devices[0]

                # Log device info on first cycle and every 1000 cycles
                if self.cycle_count == 1 or self.cycle_count % 1000 == 0:
                    logger.info(f"Reading cycle #{self.cycle_count} - Device: {device.name} (Slave ID: {device.slave_id}, Port: {device.com_port})")

                # Prepare device config for Modbus service
                device_config = {
                    'id': device.id,
                    'name': device.name,
                    'slave_id': device.slave_id,
                    'baud_rate': device.baud_rate,
                    'com_port': device.com_port,
                    'function_code': device.function_code,
                    'start_register': device.start_register,
                    'register_count': device.register_count
                }

                try:
                    # Read temperature from device (in thread to avoid blocking)
                    result = await asyncio.to_thread(
                        modbus_service.read_temperature,
                        device_config
                    )

                    # Prepare reading data
                    reading_data = {
                        'device_id': result['device_id'],
                        'device_name': result['device_name'],
                        'temperature': result['temperature'],
                        'ambient_temp': result.get('ambient_temp'),
                        'status': result['status'],
                        'raw_hex': result['raw_hex'],
                        'timestamp': parse_iso_ist(result['timestamp'])
                    }

                    # Add to buffer (will be saved to DB when buffer is full)
                    reading_buffer.add_reading(reading_data)

                    # Broadcast to WebSocket clients immediately for real-time updates
                    await websocket_manager.broadcast({
                        'type': 'reading_update',
                        'data': {
                            'device_id': result['device_id'],
                            'device_name': result['device_name'],
                            'temperature': result['temperature'],
                            'ambient_temp': result.get('ambient_temp'),
                            'status': result['status'],
                            'raw_hex': result['raw_hex'],
                            'timestamp': result['timestamp'],
                            'error_message': result.get('error_message', '')
                        }
                    })

                    # Only log errors, not successful reads (too verbose)
                    if result['status'] != 'OK':
                        logger.warning(f"Device {device.name}: Error - {result['error_message']}")

                except Exception as device_error:
                    logger.error(f"Error reading device {device.name} (ID:{device.id}): {device_error}", exc_info=True)

                # Calculate cycle time
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds()

                # Log cycle time every 100 cycles for monitoring (reduced from 1000 for better visibility)
                if self.cycle_count % 100 == 0:
                    logger.info(f"Cycle #{self.cycle_count} completed in {cycle_duration:.2f}s (Continuous mode - 1 read/second)")

                # Delay between reads: 1 second (1 read per second)
                # This provides real-time data without overwhelming the database
                # The pyrometer device typically can't respond faster than this anyway
                await asyncio.sleep(1.0)  # 1 second = 1 read/second

            except asyncio.CancelledError:
                logger.info("Continuous reading loop cancelled")
                break
            except Exception as e:
                logger.error("=" * 60)
                logger.error(f"CRITICAL ERROR in continuous reading loop (cycle #{self.cycle_count}): {type(e).__name__}: {e}")
                logger.error("=" * 60, exc_info=True)
                logger.error("Waiting 5 seconds before retry...")
                await asyncio.sleep(5)  # Wait before retrying

        logger.info("Continuous reading loop ended")
    
    def get_stats(self) -> dict:
        """
        Get polling service statistics
        
        Returns:
            Dictionary with stats
        """
        buffer_stats = reading_buffer.get_stats()
        
        return {
            'is_running': self.is_running,
            'cycle_count': self.cycle_count,
            'buffer_stats': buffer_stats
        }


# Create singleton instance
polling_service = PollingService()