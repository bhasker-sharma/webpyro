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

logger = logging.getLogger(__name__)


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
            logger.warning("Polling service already running")
            return
        
        self.is_running = True
        logger.info("Starting polling service...")
        
        # Start polling task
        self.polling_task = asyncio.create_task(self._polling_loop())
        
        logger.info("Polling service started")
    
    async def stop(self):
        """Stop the polling service"""
        if not self.is_running:
            return
        
        logger.info("Stopping polling service...")
        self.is_running = False
        
        # Cancel polling task
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining buffer data to database
        reading_buffer.flush_all()
        
        # Disconnect Modbus
        modbus_service.disconnect()
        
        logger.info("Polling service stopped")
    
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
            
            return devices
        finally:
            db.close()
    
    async def _polling_loop(self):
        """
        Main polling loop - runs continuously
        """
        logger.debug("Polling loop started")
        
        while self.is_running:
            try:
                self.cycle_count += 1
                cycle_start = datetime.now()
                
                # Get enabled devices
                devices = self._get_enabled_devices()
                
                if not devices:
                    logger.warning("No enabled devices found, waiting...")
                    await asyncio.sleep(5)
                    continue
                
                logger.debug(f"Cycle #{self.cycle_count}: Reading {len(devices)} devices...")
                
                # Read each device
                for device in devices:
                    if not self.is_running:
                        break
                    
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
                    
                    # Read temperature from device
                    result = await asyncio.to_thread(
                        modbus_service.read_temperature,
                        device_config
                    )
                    
                    # Prepare reading data
                    reading_data = {
                        'device_id': result['device_id'],
                        'device_name': result['device_name'],
                        'temperature': result['temperature'],
                        'status': result['status'],
                        'raw_hex': result['raw_hex'],
                        'timestamp': datetime.fromisoformat(result['timestamp'])
                    }
                    
                    # Add to buffer (will be saved to DB when buffer is full)
                    reading_buffer.add_reading(reading_data)
                    
                    # TODO: Broadcast to WebSocket clients (will add in next step)
                    
                    # Log reading
                    if result['status'] == 'OK':
                        logger.debug(f"Device {device.name}: {result['temperature']}C")
                    else:
                        logger.warning(f"Device {device.name}: {result['error_message']}")
                
                # Calculate cycle time
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds()

                logger.debug(f"Cycle #{self.cycle_count} complete in {cycle_duration:.2f}s")
                
                # Optional: Small delay between cycles (give devices a rest)
                # Comment out this line if you want continuous reading
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.debug("Polling loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

        logger.debug("Polling loop ended")
    
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