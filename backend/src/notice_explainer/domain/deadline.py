"""Deadline helpers (pure, stdlib only).

`today` is always a parameter for testability; today_ist() supplies IST
without any tzdata dependency (fixed +05:30 offset).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

_IST = timezone(timedelta(hours=5, minutes=30))


def today_ist() -> date:
    """Current date in IST (fixed +05:30 offset, no tzdata needed)."""
    return datetime.now(_IST).date()


def days_remaining(iso_date: str | None, today: date) -> int | None:
    """Days from `today` to the ISO-8601 date. None if unparseable."""
    if not iso_date or not isinstance(iso_date, str):
        return None
    try:
        parts = iso_date.strip().split("-")
        if len(parts) != 3:
            return None
        target = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, AttributeError):
        return None
    return (target - today).days
