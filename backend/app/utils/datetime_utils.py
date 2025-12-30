"""
DateTime utility functions for IST timezone handling
NO CONVERSIONS - Store and display IST timestamps directly
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30), name='IST')


def ist_now() -> datetime:
    """
    Get current IST time as timezone-aware datetime

    Returns:
        Current IST time with timezone info
    """
    return datetime.now(IST)


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime
    DEPRECATED: Use ist_now() instead for consistency

    Returns:
        Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


def to_iso_ist(dt: datetime) -> str:
    """
    Convert datetime to ISO format string (as-is, no conversion)
    Removes timezone info for simple storage and display

    Args:
        dt: DateTime to convert

    Returns:
        ISO format string without timezone suffix
    """
    if dt is None:
        return None

    # If datetime has timezone, convert to IST first
    if dt.tzinfo is not None:
        dt = dt.astimezone(IST)

    # Return ISO format WITHOUT timezone suffix (naive format)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]


def to_iso_utc(dt: datetime) -> str:
    """
    Convert datetime to ISO format string in UTC
    DEPRECATED: Use to_iso_ist() instead

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


def parse_iso_ist(iso_string: str) -> datetime:
    """
    Parse ISO format string to naive datetime (IST assumed)
    NO CONVERSION - Just parse as-is

    Args:
        iso_string: ISO format datetime string (e.g., "2025-12-29T15:30:45")

    Returns:
        Naive datetime (no timezone info) - IST is assumed
    """
    if not iso_string:
        return None

    # Remove timezone suffix if present
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1]

    # Remove any +XX:XX timezone suffix
    if '+' in iso_string:
        iso_string = iso_string.split('+')[0]
    if iso_string.count('-') > 2:  # Has negative timezone offset
        parts = iso_string.split('-')
        iso_string = '-'.join(parts[:-1])

    # Parse the datetime as naive (no timezone)
    dt = datetime.fromisoformat(iso_string)

    # Return as-is without timezone info (IST is assumed)
    if dt.tzinfo is not None:
        # Remove timezone info to keep it simple
        dt = dt.replace(tzinfo=None)

    return dt


def parse_iso_utc(iso_string: str) -> datetime:
    """
    Parse ISO format string to timezone-aware UTC datetime
    DEPRECATED: Use parse_iso_ist() instead

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
