"""
Centralized datetime utilities for consistent timestamp handling

SYSTEM-WIDE CONVENTION:
- All timestamps MUST be stored in UTC
- All timestamps MUST be timezone-aware
- All API responses MUST use ISO format with timezone indicator
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC timestamp (timezone-aware)

    Use this instead of datetime.now() or datetime.utcnow()

    Returns:
        datetime: Current UTC time with timezone info

    Example:
        >>> utc_now()
        datetime.datetime(2025, 11, 29, 6, 2, 35, 123456, tzinfo=datetime.timezone.utc)
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware UTC

    Args:
        dt: Datetime to convert (naive or timezone-aware)

    Returns:
        datetime: Timezone-aware UTC datetime

    Example:
        >>> naive_dt = datetime(2025, 11, 29, 12, 0, 0)
        >>> ensure_utc(naive_dt)
        datetime.datetime(2025, 11, 29, 12, 0, 0, tzinfo=datetime.timezone.utc)
    """
    if dt.tzinfo is None:
        # Naive datetime - assume it's UTC
        return dt.replace(tzinfo=timezone.utc)
    # Already timezone-aware - convert to UTC
    return dt.astimezone(timezone.utc)


def to_iso_utc(dt: datetime) -> str:
    """
    Convert datetime to ISO format with 'Z' suffix for UTC

    This ensures consistent format for frontend JavaScript:
    "2025-11-29T06:02:35.123456Z"

    Args:
        dt: Datetime to convert

    Returns:
        str: ISO 8601 formatted string with 'Z' suffix

    Example:
        >>> dt = datetime(2025, 11, 29, 6, 2, 35, 123456, tzinfo=timezone.utc)
        >>> to_iso_utc(dt)
        '2025-11-29T06:02:35.123456Z'
    """
    utc_dt = ensure_utc(dt)
    # Use 'Z' suffix instead of '+00:00' for consistency with JavaScript
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def parse_iso_utc(iso_string: str) -> datetime:
    """
    Parse ISO format timestamp to timezone-aware UTC datetime

    Handles both 'Z' suffix and '+00:00' timezone format

    Args:
        iso_string: ISO 8601 formatted timestamp

    Returns:
        datetime: Timezone-aware UTC datetime

    Example:
        >>> parse_iso_utc('2025-11-29T06:02:35.123456Z')
        datetime.datetime(2025, 11, 29, 6, 2, 35, 123456, tzinfo=datetime.timezone.utc)
    """
    # Replace 'Z' with '+00:00' for Python's fromisoformat
    normalized = iso_string.replace('Z', '+00:00')
    dt = datetime.fromisoformat(normalized)
    return ensure_utc(dt)


# IST (India Standard Time) conversion utilities
def utc_to_ist(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST (India Standard Time, UTC+5:30)

    Args:
        utc_dt: UTC datetime to convert

    Returns:
        datetime: IST datetime (still timezone-aware)

    Note: For display purposes only. NEVER store IST in database.

    Example:
        >>> utc = datetime(2025, 11, 29, 6, 0, 0, tzinfo=timezone.utc)
        >>> utc_to_ist(utc)
        datetime.datetime(2025, 11, 29, 11, 30, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=19800)))
    """
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return ensure_utc(utc_dt).astimezone(ist_offset)


def ist_to_utc(ist_dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC

    Args:
        ist_dt: IST datetime to convert

    Returns:
        datetime: UTC datetime

    Example:
        >>> ist_offset = timezone(timedelta(hours=5, minutes=30))
        >>> ist = datetime(2025, 11, 29, 11, 30, 0, tzinfo=ist_offset)
        >>> ist_to_utc(ist)
        datetime.datetime(2025, 11, 29, 6, 0, 0, tzinfo=datetime.timezone.utc)
    """
    return ist_dt.astimezone(timezone.utc)


def format_ist_string(utc_dt: datetime) -> str:
    """
    Format UTC datetime as IST string for display

    Args:
        utc_dt: UTC datetime to convert and format

    Returns:
        str: Formatted IST datetime string

    Example:
        >>> utc = datetime(2025, 11, 29, 6, 0, 0, tzinfo=timezone.utc)
        >>> format_ist_string(utc)
        '2025-11-29 11:30:00 IST'
    """
    ist_dt = utc_to_ist(utc_dt)
    return ist_dt.strftime('%Y-%m-%d %H:%M:%S IST')
