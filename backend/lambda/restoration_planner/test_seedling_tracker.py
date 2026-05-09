"""
Unit tests for the Seedling Tracker module.

Tests cover expected growth curve, growth assessment, survival rate
estimation from NDVI, and full seedling tracking reports.

Requirements: 5.5
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone

import pytest

_st = importlib.import_module("lambda.restoration_planner.seedling_tracker")
_models = importlib.import_module("lambda.shared.models")

expected_ndvi_at_day = _st.expected_ndvi_at_day
assess_growth = _st.assess_growth
estimate_survival_from_ndvi = _st.estimate_survival_from_ndvi
track_seedlings = _st.track_seedlings
GROWTH_CURVE_NDVI_MIN = _st.GROWTH_CURVE_NDVI_MIN
GROWTH_CURVE_NDVI_MAX = _st.GROWTH_CURVE_NDVI_MAX
GROWTH_CURVE_MIDPOINT_DAYS = _st.GROWTH_CURVE_MIDPOINT_DAYS

GrowthAssessment = _st.GrowthAssessment
SeedlingReport = _st.SeedlingReport
NDVITimeSeries = _models.NDVITimeSeries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_DATE = datetime(2023, 1, 1, tzinfo=timezone.utc)


def _make_series(
    day_offsets: list[int],
    ndvi_values: list[float],
) -> NDVITimeSeries:
    """Create an NDVITimeSeries from day offsets relative to _BASE_DATE."""
    timestamps = [_BASE_DATE + timedelta(days=d) for d in day_offsets]
    return NDVITimeSeries(timestamps=timestamps, values=ndvi_values)


# ---------------------------------------------------------------------------
# expected_ndvi_at_day
# ---------------------------------------------------------------------------


class TestExpectedNDVIAtDay:
    """Tests for the logistic growth curve."""

    def test_day_zero_near_minimum(self):
        """At planting, expected NDVI should be near the minimum."""
        ndvi = expected_ndvi_at_day(0)
        # At day 0, logistic curve is below midpoint
        assert ndvi >= GROWTH_CURVE_NDVI_MIN
        assert ndvi < (GROWTH_CURVE_NDVI_MIN + GROWTH_CURVE_NDVI_MAX) / 2

    def test_midpoint_near_halfway(self):
        """At the midpoint, NDVI should be roughly halfway."""
        ndvi = expected_ndvi_at_day(GROWTH_CURVE_MIDPOINT_DAYS)
        midpoint_ndvi = (GROWTH_CURVE_NDVI_MIN + GROWTH_CURVE_NDVI_MAX) / 2
        assert ndvi == pytest.approx(midpoint_ndvi, abs=0.01)

    def test_far_future_near_maximum(self):
        """After many years, NDVI should approach the maximum."""
        ndvi = expected_ndvi_at_day(5000)
        assert ndvi == pytest.approx(GROWTH_CURVE_NDVI_MAX, abs=0.01)

    def test_monotonically_increasing(self):
        """Expected NDVI should increase over time."""
        prev = expected_ndvi_at_day(0)
        for day in [30, 90, 180, 365, 730, 1095, 1825]:
            current = expected_ndvi_at_day(day)
            assert current >= prev, f"NDVI decreased at day {day}"
            prev = current

    def test_negative_days_returns_minimum(self):
        ndvi = expected_ndvi_at_day(-10)
        assert ndvi == GROWTH_CURVE_NDVI_MIN

    def test_always_in_range(self):
        """Expected NDVI must always be in [NDVI_MIN, NDVI_MAX]."""
        for day in [0, 1, 100, 365, 730, 1825, 3650, 10000]:
            ndvi = expected_ndvi_at_day(day)
            assert GROWTH_CURVE_NDVI_MIN <= ndvi <= GROWTH_CURVE_NDVI_MAX


# ---------------------------------------------------------------------------
# assess_growth
# ---------------------------------------------------------------------------


class TestAssessGrowth:
    """Tests for growth assessment against expected curve."""

    def test_on_track(self):
        """Actual NDVI matching expected → on_track."""
        expected = expected_ndvi_at_day(365)
        result = assess_growth(365, expected)
        assert result.status == "on_track"
        assert result.growth_ratio == pytest.approx(1.0, abs=0.01)

    def test_ahead(self):
        """Actual NDVI well above expected → ahead."""
        expected = expected_ndvi_at_day(365)
        result = assess_growth(365, expected * 1.3)
        assert result.status == "ahead"

    def test_behind(self):
        """Actual NDVI below expected → behind."""
        expected = expected_ndvi_at_day(365)
        result = assess_growth(365, expected * 0.6)
        assert result.status == "behind"

    def test_failing(self):
        """Very low actual NDVI → failing."""
        result = assess_growth(365, 0.01)
        assert result.status == "failing"

    def test_returns_growth_assessment(self):
        result = assess_growth(100, 0.15)
        assert isinstance(result, GrowthAssessment)
        assert result.days_since_planting == 100

    def test_day_zero(self):
        result = assess_growth(0, GROWTH_CURVE_NDVI_MIN)
        assert result.status in ("on_track", "ahead")


# ---------------------------------------------------------------------------
# estimate_survival_from_ndvi
# ---------------------------------------------------------------------------


class TestEstimateSurvivalFromNDVI:
    """Tests for survival rate estimation from NDVI series."""

    def test_matching_expected_gives_high_survival(self):
        """If actual NDVI matches expected, survival ≈ 1.0."""
        days = 365
        expected = expected_ndvi_at_day(days)
        series = _make_series([days], [expected])
        survival = estimate_survival_from_ndvi(series, _BASE_DATE)
        assert survival == pytest.approx(1.0, abs=0.05)

    def test_half_expected_gives_half_survival(self):
        """If actual NDVI is half of expected, survival ≈ 0.5."""
        days = 365
        expected = expected_ndvi_at_day(days)
        series = _make_series([days], [expected * 0.5])
        survival = estimate_survival_from_ndvi(series, _BASE_DATE)
        assert survival == pytest.approx(0.5, abs=0.1)

    def test_zero_ndvi_gives_zero_survival(self):
        series = _make_series([365], [0.0])
        survival = estimate_survival_from_ndvi(series, _BASE_DATE)
        assert survival == 0.0

    def test_empty_series_returns_zero(self):
        series = NDVITimeSeries(timestamps=[], values=[])
        survival = estimate_survival_from_ndvi(series, _BASE_DATE)
        assert survival == 0.0

    def test_survival_clamped_to_one(self):
        """Even if actual > expected, survival caps at 1.0."""
        days = 365
        expected = expected_ndvi_at_day(days)
        series = _make_series([days], [expected * 2.0])
        survival = estimate_survival_from_ndvi(series, _BASE_DATE)
        assert survival <= 1.0

    def test_survival_non_negative(self):
        series = _make_series([365], [-0.5])
        survival = estimate_survival_from_ndvi(series, _BASE_DATE)
        assert survival >= 0.0


# ---------------------------------------------------------------------------
# track_seedlings
# ---------------------------------------------------------------------------


class TestTrackSeedlings:
    """Tests for full seedling tracking report generation."""

    def test_returns_seedling_report(self):
        series = _make_series([30, 60, 90], [0.12, 0.14, 0.16])
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert isinstance(report, SeedlingReport)
        assert report.site_id == "site-1"

    def test_assessments_count_matches_observations(self):
        series = _make_series([30, 60, 90, 120], [0.12, 0.14, 0.16, 0.18])
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert len(report.assessments) == 4

    def test_latest_assessment_is_last(self):
        series = _make_series([30, 60, 90], [0.12, 0.14, 0.16])
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert report.latest_assessment is not None
        assert report.latest_assessment.days_since_planting == 90

    def test_empty_series_critical_status(self):
        series = NDVITimeSeries(timestamps=[], values=[])
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert report.overall_status == "critical"
        assert report.estimated_survival_rate == 0.0
        assert report.latest_assessment is None

    def test_healthy_growth_good_status(self):
        """Seedlings matching expected curve → good or excellent."""
        days = [30, 90, 180, 365]
        ndvi_vals = [expected_ndvi_at_day(d) for d in days]
        series = _make_series(days, ndvi_vals)
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert report.overall_status in ("good", "excellent")
        assert report.estimated_survival_rate >= 0.8

    def test_poor_growth_concerning_or_critical(self):
        """Very low NDVI → concerning or critical."""
        series = _make_series([30, 90, 180, 365], [0.02, 0.02, 0.03, 0.03])
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert report.overall_status in ("concerning", "critical")

    def test_observations_before_planting_skipped(self):
        """Observations before planting date should be excluded."""
        planting = _BASE_DATE + timedelta(days=60)
        series = _make_series([30, 60, 90, 120], [0.1, 0.12, 0.14, 0.16])
        report = track_seedlings("site-1", planting, series)
        # Day 30 is before planting (day 60), so excluded.
        # Days 60, 90, 120 are at or after planting → 3 assessments
        assert len(report.assessments) == 3
        assert report.assessments[0].days_since_planting == 0  # day 60 = planting day

    def test_planting_date_preserved(self):
        series = _make_series([30], [0.12])
        report = track_seedlings("site-1", _BASE_DATE, series)
        assert report.planting_date == _BASE_DATE
