"""
Datetime utilities for handling timezone conversions.
"""

from datetime import datetime, timezone
from typing import Optional


def to_naive_datetime(dt: datetime) -> datetime:
    """
    Convert a timezone-aware datetime to naive datetime.

    This is needed for PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns.

    Args:
        dt: Datetime object (timezone-aware or naive)

    Returns:
        Naive datetime object
    """
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def to_utc_datetime(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC timezone-aware datetime.

    Args:
        dt: Datetime object (timezone-aware or naive)

    Returns:
        UTC timezone-aware datetime object
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ensure_naive_for_db(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure datetime is naive for database operations.

    Args:
        dt: Optional datetime object

    Returns:
        Naive datetime or None
    """
    if dt is None:
        return None
    return to_naive_datetime(dt)


def now_utc() -> datetime:
    """
    Get current UTC datetime (timezone-aware).

    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def now_naive() -> datetime:
    """
    Get current datetime as naive (for database storage).

    Returns:
        Current datetime without timezone info
    """
    return datetime.now()
