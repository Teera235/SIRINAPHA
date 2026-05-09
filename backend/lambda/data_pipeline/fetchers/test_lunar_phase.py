"""
Unit tests for the Lunar Phase Calculator.

Tests cover phase calculation for known dates, range validation,
convenience functions, and next new/full moon calculations.

Requirements: 1.5
"""

from __future__ import annotations

import importlib
from datetime import date, datetime, timezone

import pytest

_lunar = importlib.import_module("lambda.data_pipeline.fetchers.lunar_phase")

get_lunar_phase = _lunar.get_lunar_phase
get_lunar_phase_today = _lunar.get_lunar_phase_today
get_next_new_moon = _lunar.get_next_new_moon
get_next_full_moon = _lunar.get_next_full_moon


# ---------------------------------------------------------------------------
# get_lunar_phase — known dates
# ---------------------------------------------------------------------------


class TestGetLunarPhase:
    """Tests for lunar phase calculation against known astronomical dates."""

    def test_new_moon_has_low_phase(self):
        """A known new moon date should have a phase near 0.0."""
        # 2024-01-11 is a new moon
        phase = get_lunar_phase(date(2024, 1, 11))
        assert phase < 0.05, f"New moon phase should be near 0.0, got {phase}"

    def test_full_moon_has_high_phase(self):
        """A known full moon date should have a phase near 1.0."""
        # 2024-01-25 is a full moon
        phase = get_lunar_phase(date(2024, 1, 25))
        assert phase > 0.95, f"Full moon phase should be near 1.0, got {phase}"

    def test_first_quarter_has_mid_phase(self):
        """A first quarter moon should have a phase around 0.5."""
        # 2024-01-18 is approximately first quarter
        phase = get_lunar_phase(date(2024, 1, 18))
        assert 0.3 < phase < 0.7, f"First quarter phase should be ~0.5, got {phase}"

    def test_phase_is_float(self):
        phase = get_lunar_phase(date(2024, 6, 15))
        assert isinstance(phase, float)

    def test_phase_in_valid_range(self):
        """Phase must always be between 0.0 and 1.0."""
        phase = get_lunar_phase(date(2024, 3, 10))
        assert 0.0 <= phase <= 1.0

    def test_accepts_datetime_object(self):
        """Should accept datetime in addition to date."""
        phase = get_lunar_phase(datetime(2024, 1, 25, 12, 0, 0, tzinfo=timezone.utc))
        assert phase > 0.95

    def test_defaults_to_today(self):
        """Calling without arguments should return a valid phase for today."""
        phase = get_lunar_phase()
        assert 0.0 <= phase <= 1.0

    def test_different_dates_can_have_different_phases(self):
        """New moon and full moon dates should have distinctly different phases."""
        new_moon_phase = get_lunar_phase(date(2024, 1, 11))
        full_moon_phase = get_lunar_phase(date(2024, 1, 25))
        assert full_moon_phase > new_moon_phase

    def test_another_new_moon(self):
        """Verify with a second known new moon date."""
        # 2024-02-09 is a new moon
        phase = get_lunar_phase(date(2024, 2, 9))
        assert phase < 0.05, f"New moon phase should be near 0.0, got {phase}"

    def test_another_full_moon(self):
        """Verify with a second known full moon date."""
        # 2024-02-24 is a full moon
        phase = get_lunar_phase(date(2024, 2, 24))
        assert phase > 0.95, f"Full moon phase should be near 1.0, got {phase}"


# ---------------------------------------------------------------------------
# get_lunar_phase_today
# ---------------------------------------------------------------------------


class TestGetLunarPhaseToday:
    """Tests for the convenience function."""

    def test_returns_valid_phase(self):
        phase = get_lunar_phase_today()
        assert 0.0 <= phase <= 1.0

    def test_returns_float(self):
        phase = get_lunar_phase_today()
        assert isinstance(phase, float)


# ---------------------------------------------------------------------------
# get_next_new_moon
# ---------------------------------------------------------------------------


class TestGetNextNewMoon:
    """Tests for next new moon calculation."""

    def test_returns_date_after_input(self):
        ref = date(2024, 1, 1)
        next_new = get_next_new_moon(ref)
        assert next_new > ref

    def test_returns_date_object(self):
        next_new = get_next_new_moon(date(2024, 6, 1))
        assert isinstance(next_new, date)

    def test_known_next_new_moon(self):
        """After 2024-01-01, the next new moon is 2024-01-11."""
        next_new = get_next_new_moon(date(2024, 1, 1))
        assert next_new == date(2024, 1, 11)

    def test_accepts_datetime(self):
        next_new = get_next_new_moon(
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        assert isinstance(next_new, date)

    def test_defaults_to_today(self):
        next_new = get_next_new_moon()
        assert isinstance(next_new, date)


# ---------------------------------------------------------------------------
# get_next_full_moon
# ---------------------------------------------------------------------------


class TestGetNextFullMoon:
    """Tests for next full moon calculation."""

    def test_returns_date_after_input(self):
        ref = date(2024, 1, 1)
        next_full = get_next_full_moon(ref)
        assert next_full > ref

    def test_returns_date_object(self):
        next_full = get_next_full_moon(date(2024, 6, 1))
        assert isinstance(next_full, date)

    def test_known_next_full_moon(self):
        """After 2024-01-01, the next full moon is 2024-01-25."""
        next_full = get_next_full_moon(date(2024, 1, 1))
        assert next_full == date(2024, 1, 25)

    def test_accepts_datetime(self):
        next_full = get_next_full_moon(
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        assert isinstance(next_full, date)

    def test_defaults_to_today(self):
        next_full = get_next_full_moon()
        assert isinstance(next_full, date)
