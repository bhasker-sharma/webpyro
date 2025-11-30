"""
Log File Retention Service - DATE-BASED FOLDER DELETION
Simple implementation: Just delete old date folders!
✨ Detects manual time changes - checks actual computer time every minute!
"""

import logging
import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from app.config import get_settings

# Use dedicated retention logger (logs to retention.log)
logger = logging.getLogger('app.services.retention')
settings = get_settings()


class LogRetentionService:
    """
    Manages log folder retention using date-based cleanup
    Deletes entire date folders older than retention period

    Simple approach:
    - Each day has its own folder: logs/DD-MM-YYYY/
    - At cleanup hour, delete folders older than retention_days
    - Much simpler than managing individual log files!

    ✨ Uses time-checking loop instead of scheduler - detects manual time changes!
    """

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir  # Base logs directory (e.g., E:/webpyro/backend/logs)
        self.retention_days = settings.log_retention_days
        self.cleanup_hour = settings.log_cleanup_hour
        self.is_running = False
        self.cleanup_task = None
        self.last_cleanup_date = None  # Track which date we last ran cleanup

        logger.info(f"Log Retention Service initialized:")
        logger.info(f"  - Log directory: {self.log_dir.absolute()}")
        logger.info(f"  - Retention period: {self.retention_days} days")
        logger.info(f"  - Daily cleanup at: {self.cleanup_hour}:00")
        logger.info(f"  ✨ Time-check mode: detects manual time changes!")

    async def start(self):
        """Start time-checking loop"""
        if self.is_running:
            logger.warning("Log retention service already running")
            return

        logger.info("=" * 60)
        logger.info("LOG RETENTION SERVICE STARTING...")
        logger.info("=" * 60)

        self.is_running = True

        # Start background task that checks time every minute
        self.cleanup_task = asyncio.create_task(self._time_check_loop())

        logger.info(f"Will run cleanup at {self.cleanup_hour}:00 every day")
        logger.info("✨ Checking actual computer time every minute")
        logger.info("Log retention service started successfully")
        logger.info("=" * 60)

    async def stop(self):
        """Stop time-checking loop"""
        if not self.is_running:
            return

        logger.info("Stopping log retention service...")

        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Log retention service stopped")

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
                    logger.info("Triggering log folder cleanup...")

                    # Run cleanup
                    await self.daily_log_cleanup()

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

    async def daily_log_cleanup(self):
        """
        Daily log cleanup job - deletes date folders older than retention_days
        Runs at configured hour (default 3 AM)

        Example:
        - Today: 30-11-2025
        - Retention: 30 days
        - Cutoff: 31-10-2025
        - Deletes: All folders with dates before 31-10-2025
        """
        logger.info("=" * 80)
        logger.info("DAILY LOG FOLDER CLEANUP STARTED (Date-based)")
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info("=" * 80)

        try:
            # Calculate cutoff date
            # ✨ IMPORTANT: Only use DATE portion, not time!
            # Otherwise, folders get deleted on same day they're created
            cutoff_datetime = datetime.now() - timedelta(days=self.retention_days)
            cutoff_date = cutoff_datetime.date()  # Extract just the DATE

            logger.info(f"Retention period: {self.retention_days} days")
            logger.info(f"Cutoff date: {cutoff_date.strftime('%d-%m-%Y')}")
            logger.info(f"Deleting all log folders OLDER than: {cutoff_date.strftime('%d-%m-%Y')}")
            logger.info(f"Note: Comparing DATES only (not times) to avoid deleting today's folder")
            logger.info("")

            # Get all date folders
            date_folders = self._get_date_folders()
            logger.info(f"Found {len(date_folders)} total date folders in {self.log_dir}")

            if len(date_folders) == 0:
                logger.info("✓ No date folders found - nothing to clean up")
                logger.info("=" * 80)
                return

            deleted_folders = []
            kept_folders = []
            total_size_freed = 0

            # Get today's date for safety check
            today = datetime.now().date()

            for folder_path, folder_date in date_folders:
                try:
                    # Check if folder date is older than cutoff date
                    # ✨ Compare DATES only (not datetime) to prevent deleting today's folder!
                    folder_date_only = folder_date.date()  # Extract just the DATE

                    # Safety check: NEVER delete today's folder!
                    if folder_date_only == today:
                        logger.info(f"Skipping today's folder: {folder_path.name} (never delete current folder)")
                        kept_folders.append({
                            'path': folder_path.name,
                            'date': folder_date
                        })
                        continue

                    if folder_date_only < cutoff_date:
                        # Calculate folder size before deletion
                        folder_size = self._get_folder_size(folder_path)

                        # ✨ IMPORTANT: Close all log file handlers for this date first!
                        # This prevents "file in use" errors on Windows
                        from app.logging_config import DailyFolderHandler
                        DailyFolderHandler.close_handlers_for_date(folder_path.name)

                        # Wait a moment for file handles to release
                        import asyncio
                        await asyncio.sleep(0.1)

                        # Delete the entire folder
                        shutil.rmtree(folder_path)

                        deleted_folders.append({
                            'path': folder_path.name,
                            'date': folder_date,
                            'size': folder_size
                        })
                        total_size_freed += folder_size
                        logger.info(f"✓ Deleted folder: {folder_path.name} (date: {folder_date.strftime('%d-%m-%Y')}, size: {self._format_bytes(folder_size)})")
                    else:
                        kept_folders.append({
                            'path': folder_path.name,
                            'date': folder_date
                        })

                except Exception as e:
                    logger.error(f"Error deleting folder {folder_path}: {e}")

            # Summary
            logger.info("")
            logger.info("=" * 80)
            logger.info("LOG CLEANUP SUMMARY:")
            logger.info(f"  - Total folders scanned: {len(date_folders)}")
            logger.info(f"  - Folders deleted: {len(deleted_folders)}")
            logger.info(f"  - Folders kept: {len(kept_folders)}")
            logger.info(f"  - Storage freed: {self._format_bytes(total_size_freed)}")

            if len(deleted_folders) == 0:
                logger.info("✓ No old log folders to delete - all folders are within retention period")
            else:
                logger.info(f"✓ Successfully deleted {len(deleted_folders)} old log folder(s)")

            logger.info("=" * 80)
            logger.info("DAILY LOG CLEANUP COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"DAILY LOG CLEANUP FAILED: {e}")
            logger.error("=" * 80, exc_info=True)

    def _get_date_folders(self) -> list[tuple[Path, datetime]]:
        """
        Get all date folders in the logs directory

        Returns:
            List of tuples: (folder_path, folder_date)
        """
        date_folders = []

        try:
            for item in self.log_dir.iterdir():
                if item.is_dir():
                    try:
                        # Parse folder name as date (DD-MM-YYYY format)
                        folder_date = datetime.strptime(item.name, "%d-%m-%Y")
                        date_folders.append((item, folder_date))
                    except ValueError:
                        # Skip folders that don't match date format
                        logger.debug(f"Skipping non-date folder: {item.name}")
                        continue

        except Exception as e:
            logger.error(f"Error scanning log directory: {e}", exc_info=True)

        # Sort by date (oldest first)
        date_folders.sort(key=lambda x: x[1])

        return date_folders

    def _get_folder_size(self, folder_path: Path) -> int:
        """
        Calculate total size of a folder (all files inside)

        Args:
            folder_path: Path to the folder

        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for file in folder_path.rglob('*'):
                if file.is_file():
                    total_size += file.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating folder size for {folder_path}: {e}")

        return total_size

    def _format_bytes(self, bytes_size: int) -> str:
        """
        Format bytes to human-readable string

        Args:
            bytes_size: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    def get_stats(self) -> dict:
        """
        Get log retention statistics

        Returns:
            Dictionary with retention stats
        """
        try:
            date_folders = self._get_date_folders()
            total_size = sum(self._get_folder_size(f[0]) for f in date_folders)

            if date_folders:
                oldest_folder = date_folders[0]
                newest_folder = date_folders[-1]

                return {
                    'is_running': self.is_running,
                    'retention_days': self.retention_days,
                    'log_directory': str(self.log_dir.absolute()),
                    'total_date_folders': len(date_folders),
                    'total_size': self._format_bytes(total_size),
                    'total_size_bytes': total_size,
                    'oldest_folder': oldest_folder[0].name,
                    'oldest_folder_date': oldest_folder[1].strftime('%d-%m-%Y'),
                    'newest_folder': newest_folder[0].name,
                    'newest_folder_date': newest_folder[1].strftime('%d-%m-%Y'),
                    'cleanup_hour': self.cleanup_hour,
                    'last_cleanup_date': self.last_cleanup_date
                }
            else:
                return {
                    'is_running': self.is_running,
                    'retention_days': self.retention_days,
                    'log_directory': str(self.log_dir.absolute()),
                    'total_date_folders': 0,
                    'total_size': '0 B',
                    'total_size_bytes': 0,
                    'cleanup_hour': self.cleanup_hour,
                    'last_cleanup_date': self.last_cleanup_date
                }

        except Exception as e:
            logger.error(f"Error getting log retention stats: {e}", exc_info=True)
            return {
                'is_running': self.is_running,
                'retention_days': self.retention_days,
                'error': str(e)
            }
