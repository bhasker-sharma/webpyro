"""
Reading Service
Handles fetching temperature readings from database
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from datetime import timezone, datetime, timedelta

from app.models.device import DeviceReading, DeviceSettings


class ReadingService:
    """Service for reading operations"""
    
    @staticmethod
    def get_latest_readings(db: Session) -> List[Dict]:
        """
        Get the latest reading for each device
        
        Returns:
            List of dictionaries with device info and latest reading
        """
        # Get all devices
        devices = db.query(DeviceSettings).all()
        
        result = []
        for device in devices:
            # Get latest reading for this device
            latest_reading = db.query(DeviceReading)\
                .filter(DeviceReading.device_id == device.id)\
                .order_by(desc(DeviceReading.ts_utc))\
                .first()
            
            device_data = {
                'device_id': device.id,
                'device_name': device.name,
                'slave_id': device.slave_id,
                'com_port': device.com_port,
                'baud_rate': device.baud_rate,
                'enabled': device.enabled,
                'latest_reading': None
            }
            
            if latest_reading:
                # Convert UTC timestamp to local time (IST = UTC + 5:30)
                local_timestamp = latest_reading.ts_utc + timedelta(hours=5, minutes=30)

                device_data['latest_reading'] = {
                    'temperature': latest_reading.value,
                    'status': latest_reading.status,
                    'raw_hex': latest_reading.raw_hex,
                    'timestamp': local_timestamp.isoformat(),
                    'time_ago': ReadingService._time_ago(latest_reading.ts_utc)
                }
            
            result.append(device_data)
        
        return result
    
    @staticmethod
    def get_device_readings(
        db: Session,
        device_id: int,
        limit: Optional[int] = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DeviceReading]:
        """
        Get readings for a specific device

        Args:
            db: Database session
            device_id: Device ID
            limit: Maximum number of readings to return (None for no limit)
            start_date: Filter readings after this date
            end_date: Filter readings before this date

        Returns:
            List of DeviceReading objects
        """
        query = db.query(DeviceReading).filter(
            DeviceReading.device_id == device_id
        )

        # Apply date filters
        if start_date:
            query = query.filter(DeviceReading.ts_utc >= start_date)
        if end_date:
            query = query.filter(DeviceReading.ts_utc <= end_date)

        # Order by timestamp descending
        query = query.order_by(desc(DeviceReading.ts_utc))

        # Apply limit only if specified
        if limit is not None:
            query = query.limit(limit)

        readings = query.all()

        return readings
    
    @staticmethod
    def get_reading_stats(db: Session) -> Dict:
        """
        Get overall reading statistics
        
        Returns:
            Dictionary with statistics
        """
        # Total readings
        total_readings = db.query(DeviceReading).count()
        
        # Readings per device
        devices = db.query(DeviceSettings).all()
        device_stats = []
        
        for device in devices:
            count = db.query(DeviceReading)\
                .filter(DeviceReading.device_id == device.id)\
                .count()
            
            # Get latest reading
            latest = db.query(DeviceReading)\
                .filter(DeviceReading.device_id == device.id)\
                .order_by(desc(DeviceReading.ts_utc))\
                .first()
            
            # Convert UTC timestamp to local time if available
            latest_timestamp_local = None
            if latest:
                local_ts = latest.ts_utc + timedelta(hours=5, minutes=30)
                latest_timestamp_local = local_ts.isoformat()

            device_stats.append({
                'device_id': device.id,
                'device_name': device.name,
                'reading_count': count,
                'latest_status': latest.status if latest else None,
                'latest_timestamp': latest_timestamp_local
            })
        
        # Readings by status
        ok_count = db.query(DeviceReading)\
            .filter(DeviceReading.status == 'OK')\
            .count()
        
        err_count = db.query(DeviceReading)\
            .filter(DeviceReading.status == 'Err')\
            .count()
        
        stale_count = db.query(DeviceReading)\
            .filter(DeviceReading.status == 'Stale')\
            .count()
        
        return {
            'total_readings': total_readings,
            'readings_by_status': {
                'ok': ok_count,
                'error': err_count,
                'stale': stale_count
            },
            'devices': device_stats
        }
    
    @staticmethod
    def _time_ago(timestamp: datetime) -> str:
        """
        Calculate human-readable time ago

        Args:
            timestamp: DateTime to calculate from

        Returns:
            String like "2 seconds ago", "5 minutes ago"
        """
        now = datetime.now(timezone.utc)

        # Make timestamp timezone-aware if it's naive
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"