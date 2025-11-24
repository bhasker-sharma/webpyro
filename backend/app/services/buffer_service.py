"""
Ping-Pong Buffer Service
Efficiently batches readings before saving to database
"""

import threading
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.device import DeviceReading
import logging

logger = logging.getLogger(__name__)


class PingPongBuffer:
    """
    Dual buffer system for efficient database writes.
    When one buffer fills up, it switches to the other buffer
    and saves the full buffer to database in background.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize ping-pong buffer
        
        Args:
            max_size: Maximum number of readings per buffer before flush
        """
        self.buffer_a = []
        self.buffer_b = []
        self.active_buffer = 'a'
        self.max_size = max_size
        self.lock = threading.Lock()
        self.total_saved = 0

        logger.info(f"Ping-Pong Buffer initialized (max_size: {max_size})")
    
    def add_reading(self, reading_data: Dict) -> None:
        """
        Add a reading to the active buffer
        
        Args:
            reading_data: Dictionary with reading information
        """
        with self.lock:
            # Add to active buffer
            if self.active_buffer == 'a':
                self.buffer_a.append(reading_data)
                
                # Check if buffer is full
                if len(self.buffer_a) >= self.max_size:
                    logger.info(f"Buffer A full ({len(self.buffer_a)} readings), switching to B")
                    
                    # Switch to buffer B
                    self.active_buffer = 'b'
                    
                    # Save buffer A in background
                    buffer_copy = self.buffer_a.copy()
                    threading.Thread(
                        target=self._save_buffer_to_db,
                        args=(buffer_copy, 'A'),
                        daemon=True
                    ).start()
                    
                    # Clear buffer A
                    self.buffer_a.clear()
            
            else:  # active_buffer == 'b'
                self.buffer_b.append(reading_data)
                
                # Check if buffer is full
                if len(self.buffer_b) >= self.max_size:
                    logger.info(f"Buffer B full ({len(self.buffer_b)} readings), switching to A")
                    
                    # Switch to buffer A
                    self.active_buffer = 'a'
                    
                    # Save buffer B in background
                    buffer_copy = self.buffer_b.copy()
                    threading.Thread(
                        target=self._save_buffer_to_db,
                        args=(buffer_copy, 'B'),
                        daemon=True
                    ).start()
                    
                    # Clear buffer B
                    self.buffer_b.clear()
    
    def _save_buffer_to_db(self, readings: List[Dict], buffer_name: str) -> None:
        """
        Save a batch of readings to database
        
        Args:
            readings: List of reading dictionaries
            buffer_name: Name of buffer being saved (for logging)
        """
        if not readings:
            return
        
        db = SessionLocal()
        try:
            logger.info(f"Saving Buffer {buffer_name} to database ({len(readings)} readings)...")

            # Create DeviceReading objects
            db_readings = []
            for reading in readings:
                try:
                    db_reading = DeviceReading(
                        device_id=reading['device_id'],
                        device_name=reading['device_name'],
                        ts_utc=reading['timestamp'],
                        value=reading['temperature'] if reading['temperature'] is not None else 0.0,
                        ambient_temp=reading.get('ambient_temp'),  # Add ambient temperature
                        status=reading['status'],
                        raw_hex=reading['raw_hex']
                    )
                    db_readings.append(db_reading)
                except Exception as reading_error:
                    logger.warning(f"Skipping invalid reading: {reading_error}")
                    continue

            if not db_readings:
                logger.warning(f"No valid readings to save in Buffer {buffer_name}")
                return

            # Batch insert with error recovery
            try:
                db.bulk_save_objects(db_readings)
                db.commit()
                self.total_saved += len(db_readings)
                logger.info(f"Buffer {buffer_name} saved successfully ({len(db_readings)} readings, Total: {self.total_saved})")
            except Exception as bulk_error:
                # If bulk insert fails, try saving one by one (slower but more reliable)
                db.rollback()
                logger.warning(f"Bulk insert failed, trying individual inserts: {bulk_error}")

                saved_count = 0
                for reading_obj in db_readings:
                    try:
                        db.add(reading_obj)
                        db.commit()
                        saved_count += 1
                    except Exception as individual_error:
                        db.rollback()
                        logger.debug(f"Skipped duplicate/invalid reading: {individual_error}")
                        continue

                self.total_saved += saved_count
                logger.info(f"Buffer {buffer_name} saved {saved_count}/{len(db_readings)} readings individually (Total: {self.total_saved})")

        except Exception as e:
            logger.error(f"Error saving Buffer {buffer_name} to database: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    def flush_all(self) -> None:
        """
        Force flush both buffers to database (called on shutdown)
        """
        logger.info("Flushing all buffers to database...")

        with self.lock:
            if self.buffer_a:
                self._save_buffer_to_db(self.buffer_a.copy(), 'A (flush)')
                self.buffer_a.clear()

            if self.buffer_b:
                self._save_buffer_to_db(self.buffer_b.copy(), 'B (flush)')
                self.buffer_b.clear()

        logger.info("All buffers flushed")
    
    def get_stats(self) -> Dict:
        """
        Get buffer statistics
        
        Returns:
            Dictionary with buffer stats
        """
        with self.lock:
            return {
                'active_buffer': self.active_buffer,
                'buffer_a_size': len(self.buffer_a),
                'buffer_b_size': len(self.buffer_b),
                'max_size': self.max_size,
                'total_saved': self.total_saved
            }


# Create singleton instance
reading_buffer = PingPongBuffer(max_size=100)