"""
Data Retention Service
Implements FIFO-based cleanup for rolling 3-month window
Automatically deletes data older than specified retention period
✨ Detects manual time changes - checks actual computer time every minute!
"""

import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database import SessionLocal
from app.models.device import DeviceReading
from app.config import get_settings
from app.utils.datetime_utils import utc_now, to_iso_utc

# Use dedicated retention logger (logs to retention.log)
logger = logging.getLogger('app.services.retention')
settings = get_settings()


class DataRetentionService:
    """
    Manages data retention and cleanup using FIFO principle
    Keeps only last N days of data (configurable, default 90 days = 3 months)

    ✨ Uses time-checking loop instead of scheduler - detects manual time changes!
    """

    def __init__(self):
        self.retention_days = settings.data_retention_days
        self.max_rows = settings.data_retention_max_rows
        self.cleanup_hour = settings.cleanup_hour
        self.is_running = False
        self.cleanup_task = None
        self.last_cleanup_date = None  # Track which date we last ran cleanup

        logger.info(f"Data Retention Service initialized:")
        logger.info(f"  - Retention period: {self.retention_days} days")
        logger.info(f"  - Max rows limit: {self.max_rows:,}")
        logger.info(f"  - Daily cleanup at: {self.cleanup_hour}:00")
        logger.info(f"  ✨ Time-check mode: detects manual time changes!")

    async def start(self):
        """Start time-checking loop"""
        if self.is_running:
            logger.warning("Data retention service already running")
            return

        logger.info("=" * 60)
        logger.info("DATA RETENTION SERVICE STARTING...")
        logger.info("=" * 60)

        self.is_running = True

        # Start background task that checks time every minute
        self.cleanup_task = asyncio.create_task(self._time_check_loop())

        logger.info(f"Will run cleanup at {self.cleanup_hour}:00 every day")
        logger.info("✨ Checking actual computer time every minute")
        logger.info("Data retention service started successfully")
        logger.info("=" * 60)

    async def stop(self):
        """Stop time-checking loop"""
        if not self.is_running:
            return

        logger.info("Stopping data retention service...")

        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Data retention service stopped")

    async def _time_check_loop(self):
        """
        Background loop that checks actual computer time every minute
        Runs cleanup when time matches cleanup_hour
        ✨ This detects manual time changes!
        """
        logger.info("Time-check loop started - checking every 60 seconds")

        while self.is_running:
            try:
                # Check current time
                now = datetime.now()
                current_hour = now.hour
                current_date = now.strftime("%Y-%m-%d")

                # Should we run cleanup?
                # Run if:
                # 1. Current hour matches cleanup hour
                # 2. We haven't run yet today (last_cleanup_date != today)
                if current_hour == self.cleanup_hour and self.last_cleanup_date != current_date:
                    logger.info(f"⏰ Time check: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"✅ Match! Hour={current_hour}, Target={self.cleanup_hour}")
                    logger.info("Triggering cleanup...")

                    # Run cleanup
                    await self.daily_cleanup()

                    # Mark that we ran cleanup for this date
                    self.last_cleanup_date = current_date
                    logger.info(f"Cleanup done. Next cleanup: tomorrow at {self.cleanup_hour}:00")

                # Wait 60 seconds before checking again
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in time-check loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying

    async def daily_cleanup(self):
        """
        Daily cleanup job - deletes data older than retention_days
        Implements FIFO: First In, First Out (oldest data deleted first)
        Can be called manually or by time-check loop

        ✨ Uses system time (datetime.now()) for all calculations!
        """
        logger.info("=" * 80)
        logger.info("DAILY DATA CLEANUP STARTED (Time-based FIFO)")
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info("=" * 80)

        db = SessionLocal()
        try:
            # Calculate cutoff date (FIFO: delete oldest first)
            # ✨ Uses datetime.now(timezone.utc) which:
            #    - Uses SYSTEM clock (responds to manual time changes!)
            #    - Converts to UTC (matches database ts_utc column)
            from datetime import timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            logger.info(f"Retention period: {self.retention_days} days")
            logger.info(f"Cutoff date (UTC): {cutoff_date}")
            logger.info(f"Deleting all data OLDER than: {cutoff_date}")

            # Count total rows before cleanup
            total_before = db.query(DeviceReading).count()
            logger.info(f"Total rows BEFORE cleanup: {total_before:,}")

            # Count rows to be deleted
            old_count = db.query(DeviceReading).filter(
                DeviceReading.ts_utc < cutoff_date
            ).count()

            if old_count == 0:
                logger.info("✓ No old data to delete - all data is within retention period")
                logger.info("=" * 80)
                return

            logger.info(f"Found {old_count:,} rows to delete (FIFO - oldest first)")

            # Get date range of data being deleted
            oldest_record = db.query(DeviceReading).order_by(
                DeviceReading.ts_utc.asc()
            ).first()

            if oldest_record:
                logger.info(f"Oldest record timestamp: {oldest_record.ts_utc}")

            # Delete old data using raw SQL for efficiency (FIFO deletion)
            logger.info("Executing DELETE query...")
            result = db.execute(
                text("DELETE FROM device_readings WHERE ts_utc < :cutoff"),
                {"cutoff": cutoff_date}
            )
            db.commit()

            deleted = result.rowcount
            logger.info(f"✓ Successfully deleted {deleted:,} rows")

            # Count remaining rows
            total_after = db.query(DeviceReading).count()
            logger.info(f"Total rows AFTER cleanup: {total_after:,}")
            logger.info(f"Storage freed: {deleted:,} rows")

            # Get current data date range
            if total_after > 0:
                oldest_remaining = db.query(DeviceReading).order_by(
                    DeviceReading.ts_utc.asc()
                ).first()
                newest_remaining = db.query(DeviceReading).order_by(
                    DeviceReading.ts_utc.desc()
                ).first()

                if oldest_remaining and newest_remaining:
                    logger.info(f"Current data range:")
                    logger.info(f"  - Oldest: {oldest_remaining.ts_utc}")
                    logger.info(f"  - Newest: {newest_remaining.ts_utc}")

                    days_span = (newest_remaining.ts_utc - oldest_remaining.ts_utc).days
                    logger.info(f"  - Span: {days_span} days")

            logger.info("=" * 80)
            logger.info("DAILY CLEANUP COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"DAILY CLEANUP FAILED: {e}")
            logger.error("=" * 80, exc_info=True)
            db.rollback()
        finally:
            db.close()

    def cleanup_on_buffer_flush(self):
        """
        Real-time cleanup after buffer flush (safety mechanism)
        Ensures row count doesn't exceed max_rows limit
        This is a backup to the daily time-based cleanup
        """
        db = SessionLocal()
        try:
            # Check total row count
            total_rows = db.query(DeviceReading).count()

            # If exceeds safety limit, delete oldest rows (FIFO)
            if total_rows > self.max_rows:
                excess = total_rows - self.max_rows
                logger.warning("=" * 60)
                logger.warning(f"ROW COUNT SAFETY LIMIT EXCEEDED")
                logger.warning(f"Current rows: {total_rows:,}")
                logger.warning(f"Max allowed: {self.max_rows:,}")
                logger.warning(f"Excess: {excess:,}")
                logger.warning(f"Deleting {excess:,} oldest rows (FIFO)")
                logger.warning("=" * 60)

                # Delete oldest rows using subquery (FIFO principle)
                subquery = db.query(DeviceReading.id).order_by(
                    DeviceReading.ts_utc.asc()
                ).limit(excess).subquery()

                deleted = db.query(DeviceReading).filter(
                    DeviceReading.id.in_(subquery)
                ).delete(synchronize_session=False)

                db.commit()
                logger.info(f"✓ Deleted {deleted:,} oldest rows")
                logger.info(f"New row count: {db.query(DeviceReading).count():,}")
                logger.warning("=" * 60)

        except Exception as e:
            logger.error(f"Buffer flush cleanup failed: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def get_stats(self) -> dict:
        """
        Get data retention statistics

        Returns:
            Dictionary with retention stats
        """
        db = SessionLocal()
        try:
            total_rows = db.query(DeviceReading).count()

            if total_rows == 0:
                return {
                    'is_running': self.is_running,
                    'retention_days': self.retention_days,
                    'max_rows': self.max_rows,
                    'current_rows': 0,
                    'oldest_record': None,
                    'newest_record': None,
                    'data_span_days': 0
                }

            oldest = db.query(DeviceReading).order_by(
                DeviceReading.ts_utc.asc()
            ).first()

            newest = db.query(DeviceReading).order_by(
                DeviceReading.ts_utc.desc()
            ).first()

            data_span_days = 0
            if oldest and newest:
                data_span_days = (newest.ts_utc - oldest.ts_utc).days

            return {
                'is_running': self.is_running,
                'retention_days': self.retention_days,
                'max_rows': self.max_rows,
                'current_rows': total_rows,
                'oldest_record': to_iso_utc(oldest.ts_utc) if oldest else None,
                'newest_record': to_iso_utc(newest.ts_utc) if newest else None,
                'data_span_days': data_span_days,
                'cleanup_hour': self.cleanup_hour,
                'last_cleanup_date': self.last_cleanup_date
            }

        except Exception as e:
            logger.error(f"Error getting retention stats: {e}", exc_info=True)
            return {
                'is_running': self.is_running,
                'retention_days': self.retention_days,
                'max_rows': self.max_rows,
                'error': str(e)
            }
        finally:
            db.close()


# Create singleton instance
retention_service = DataRetentionService()
