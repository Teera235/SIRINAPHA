"""
Lunar Phase Calculator using the ephem library.

Calculates daily lunar phase as a float from 0.0 (new moon) to 1.0
(full moon) for use in the FSI Engine's lunar score calculation.

Requirements: 1.5
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

import ephem

logger = logging.getLogger(__name__)


def get_lunar_phase(target_date: Optional[date] = None) -> float:
    """Calculate the lunar illumination phase for a given date.

    Uses the ``ephem`` library to compute the fraction of the Moon's
    surface that is illuminated as seen from Earth. This value serves
    as the lunar phase input for the FSI Engine.

    Parameters
    ----------
    target_date:
        Date to calculate the lunar phase for. Accepts ``date`` or
        ``datetime`` objects. Defaults to today (UTC).

    Returns
    -------
    float
        Lunar phase as a fraction from 0.0 (new moon) to 1.0 (full moon).
        Represents the Moon's illuminated fraction.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    # Convert datetime to date if needed
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    # Create an ephem date from the target date (noon UTC for stability)
    ephem_date = ephem.Date(target_date.strftime("%Y/%m/%d 12:00:00"))

    # Compute the Moon for this date
    moon = ephem.Moon(ephem_date)

    # moon.phase returns percentage illuminated (0-100)
    # We normalise to 0.0-1.0
    phase = float(moon.phase) / 100.0

    # Clamp to [0.0, 1.0] for safety
    phase = max(0.0, min(1.0, phase))

    logger.debug(
        "Lunar phase for %s: %.4f (%.1f%% illuminated)",
        target_date.isoformat(),
        phase,
        phase * 100,
    )

    return phase


def get_lunar_phase_today() -> float:
    """Convenience function to get today's lunar phase.

    Returns
    -------
    float
        Lunar phase for today (UTC), 0.0 to 1.0.
    """
    return get_lunar_phase()


def get_next_new_moon(target_date: Optional[date] = None) -> date:
    """Calculate the date of the next new moon after the given date.

    Parameters
    ----------
    target_date:
        Reference date. Defaults to today (UTC).

    Returns
    -------
    date
        Date of the next new moon.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    if isinstance(target_date, datetime):
        target_date = target_date.date()

    ephem_date = ephem.Date(target_date.strftime("%Y/%m/%d 12:00:00"))
    next_new = ephem.next_new_moon(ephem_date)

    return ephem.Date(next_new).datetime().date()


def get_next_full_moon(target_date: Optional[date] = None) -> date:
    """Calculate the date of the next full moon after the given date.

    Parameters
    ----------
    target_date:
        Reference date. Defaults to today (UTC).

    Returns
    -------
    date
        Date of the next full moon.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    if isinstance(target_date, datetime):
        target_date = target_date.date()

    ephem_date = ephem.Date(target_date.strftime("%Y/%m/%d 12:00:00"))
    next_full = ephem.next_full_moon(ephem_date)

    return ephem.Date(next_full).datetime().date()
