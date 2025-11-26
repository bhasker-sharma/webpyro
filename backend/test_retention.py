"""
Test script to verify data retention service configuration
This script checks if the retention service is configured correctly
"""

import sys
from app.services.data_retention_service import retention_service
from app.database import SessionLocal
from app.models.device import DeviceReading

def test_retention_service():
    """Test retention service configuration"""

    print("=" * 80)
    print("DATA RETENTION SERVICE - CONFIGURATION TEST")
    print("=" * 80)

    # Check service configuration
    print(f"\nRetention Service Configuration:")
    print(f"  - Retention Period: {retention_service.retention_days} days")
    print(f"  - Max Rows Limit: {retention_service.max_rows:,} rows")
    print(f"  - Daily Cleanup Hour: {retention_service.cleanup_hour}:00")
    print(f"  - Service Running: {retention_service.is_running}")

    # Check current database stats
    db = SessionLocal()
    try:
        total_rows = db.query(DeviceReading).count()
        print(f"\nCurrent Database Status:")
        print(f"  - Total Rows: {total_rows:,}")

        if total_rows > 0:
            oldest = db.query(DeviceReading).order_by(
                DeviceReading.ts_utc.asc()
            ).first()

            newest = db.query(DeviceReading).order_by(
                DeviceReading.ts_utc.desc()
            ).first()

            if oldest and newest:
                print(f"  - Oldest Record: {oldest.ts_utc}")
                print(f"  - Newest Record: {newest.ts_utc}")

                days_span = (newest.ts_utc - oldest.ts_utc).days
                print(f"  - Data Span: {days_span} days")

                # Check if cleanup would occur
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=retention_service.retention_days)
                old_count = db.query(DeviceReading).filter(
                    DeviceReading.ts_utc < cutoff_date
                ).count()

                print(f"\nCleanup Analysis:")
                print(f"  - Cutoff Date: {cutoff_date}")
                print(f"  - Rows to be deleted: {old_count:,}")
                print(f"  - Rows to be kept: {total_rows - old_count:,}")

                if old_count > 0:
                    print(f"\n  >> Daily cleanup will delete {old_count:,} old rows")
                else:
                    print(f"\n  >> No old data to delete - all within retention period")

                # Check max rows safety limit
                if total_rows > retention_service.max_rows:
                    excess = total_rows - retention_service.max_rows
                    print(f"\n  WARNING: Row count exceeds safety limit!")
                    print(f"  >> {excess:,} excess rows will be deleted on next buffer flush")
                else:
                    remaining_capacity = retention_service.max_rows - total_rows
                    print(f"\n  OK: Within safety limit ({remaining_capacity:,} rows remaining)")
        else:
            print("  - No data in database yet")

    except Exception as e:
        print(f"\nError: {e}")
        return False
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nNext Steps:")
    print("  1. Start the server to activate scheduled cleanup")
    print("  2. Daily cleanup will run at 2:00 AM")
    print("  3. Real-time cleanup runs after each buffer flush (if needed)")
    print("  4. Monitor logs for cleanup activity")

    return True

if __name__ == "__main__":
    try:
        success = test_retention_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
