"""
DateTime utility functions for timezone handling
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime

    Returns:
        Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


def to_iso_utc(dt: datetime) -> str:
    """
    Convert datetime to ISO format string in UTC

    Args:
        dt: DateTime to convert (can be naive or timezone-aware)

    Returns:
        ISO format string in UTC
    """
    # Ensure datetime is timezone-aware
    dt = ensure_utc(dt)

    # Convert to ISO format with Z suffix for UTC
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware in UTC

    Args:
        dt: DateTime that may be naive or timezone-aware

    Returns:
        Timezone-aware datetime in UTC
    """
    if dt is None:
        return None

    # If datetime is naive (no timezone info), assume it's UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    # If datetime has timezone info, convert to UTC
    return dt.astimezone(timezone.utc)


def parse_iso_utc(iso_string: str) -> datetime:
    """
    Parse ISO format string to timezone-aware UTC datetime

    Args:
        iso_string: ISO format datetime string

    Returns:
        Timezone-aware datetime in UTC
    """
    # Remove 'Z' suffix if present
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1]

    # Parse the datetime
    dt = datetime.fromisoformat(iso_string)

    # Ensure it's UTC
    return ensure_utc(dt)


def utc_to_ist(dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST (Indian Standard Time)
    IST is UTC+5:30

    Args:
        dt: UTC datetime (timezone-aware or naive)

    Returns:
        Timezone-aware datetime in IST
    """
    # Ensure datetime is timezone-aware UTC
    dt = ensure_utc(dt)

    # IST is UTC+5:30
    ist_offset = timedelta(hours=5, minutes=30)
    ist_tz = timezone(ist_offset, name='IST')

    # Convert to IST
    return dt.astimezone(ist_tz)
