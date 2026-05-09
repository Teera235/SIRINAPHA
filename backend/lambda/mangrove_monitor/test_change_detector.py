"""
Unit tests for the change detector module.

Tests cover NDVI change percentage calculation, alert level classification,
6-month average computation, change detection logic, alert generation,
and database storage of alerts.

Requirements: 2.4, 2.5, 2.6
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

_cd = importlib.import_module("lambda.mangrove_monitor.change_detector")

calculate_change_percent = _cd.calculate_change_percent
classify_alert_level = _cd.classify_alert_level
compute_6month_average = _cd.compute_6month_average
detect_changes = _cd.detect_changes
generate_alert = _cd.generate_alert
store_alert = _cd.store_alert
WARNING_THRESHOLD = _cd.WARNING_THRESHOLD
CRITICAL_THRESHOLD = _cd.CRITICAL_THRESHOLD

_models = importlib.import_module("lambda.shared.models")
MangroveAlert = _models.MangroveAlert
AlertLevel = _models.AlertLevel

_PATCH_PREFIX = "lambda.mangrove_monitor.change_detector"

# Sample GeoJSON polygon for tests
SAMPLE_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [
        [
            [100.2, 13.4],
            [100.5, 13.4],
            [100.5, 13.6],
            [100.2, 13.6],
            [100.2, 13.4],
        ]
    ],
}


# ---------------------------------------------------------------------------
# calculate_change_percent
# ---------------------------------------------------------------------------


class TestCalculateChangePercent:
    """Tests for percentage change calculation."""

    def test_no_change(self):
        result = calculate_change_percent(0.6, 0.6)
        assert result == pytest.approx(0.0)

    def test_20_percent_drop(self):
        # 0.48 is 80% of 0.6 → 20% drop
        result = calculate_change_percent(0.48, 0.6)
        assert result == pytest.approx(-20.0)

    def test_40_percent_drop(self):
        # 0.36 is 60% of 0.6 → 40% drop
        result = calculate_change_percent(0.36, 0.6)
        assert result == pytest.approx(-40.0)

    def test_50_percent_drop(self):
        result = calculate_change_percent(0.3, 0.6)
        assert result == pytest.approx(-50.0)

    def test_increase(self):
        result = calculate_change_percent(0.72, 0.6)
        assert result == pytest.approx(20.0)

    def test_zero_average_returns_zero(self):
        result = calculate_change_percent(0.5, 0.0)
        assert result == 0.0

    def test_small_values(self):
        result = calculate_change_percent(0.1, 0.2)
        assert result == pytest.approx(-50.0)

    def test_negative_ndvi_values(self):
        # Current NDVI can be negative (water bodies)
        result = calculate_change_percent(-0.1, 0.5)
        assert result == pytest.approx(-120.0)

    def test_both_negative(self):
        # avg_6month negative, current more negative → drop
        result = calculate_change_percent(-0.3, -0.1)
        # (-0.3 - (-0.1)) / abs(-0.1) * 100 = (-0.2 / 0.1) * 100 = -200
        assert result == pytest.approx(-200.0)

    def test_100_percent_drop(self):
        result = calculate_change_percent(0.0, 0.5)
        assert result == pytest.approx(-100.0)


# ---------------------------------------------------------------------------
# classify_alert_level
# ---------------------------------------------------------------------------


class TestClassifyAlertLevel:
    """Tests for alert level classification based on change percent."""

    def test_no_alert_for_small_drop(self):
        # 10% drop → no alert
        assert classify_alert_level(-10.0) is None

    def test_no_alert_at_exactly_minus_20(self):
        # Exactly 20% drop → no alert (threshold is >20%)
        assert classify_alert_level(-20.0) is None

    def test_warning_just_over_20_percent_drop(self):
        assert classify_alert_level(-20.1) == "warning"

    def test_warning_at_30_percent_drop(self):
        assert classify_alert_level(-30.0) == "warning"

    def test_warning_at_exactly_minus_40(self):
        # Exactly 40% drop → warning (threshold is >40% for critical)
        assert classify_alert_level(-40.0) == "warning"

    def test_critical_just_over_40_percent_drop(self):
        assert classify_alert_level(-40.1) == "critical"

    def test_critical_at_60_percent_drop(self):
        assert classify_alert_level(-60.0) == "critical"

    def test_critical_at_100_percent_drop(self):
        assert classify_alert_level(-100.0) == "critical"

    def test_no_alert_for_increase(self):
        # Positive change (increase) → no alert
        assert classify_alert_level(10.0) is None
        assert classify_alert_level(50.0) is None

    def test_no_alert_for_zero_change(self):
        assert classify_alert_level(0.0) is None

    def test_threshold_constants(self):
        assert WARNING_THRESHOLD == 20.0
        assert CRITICAL_THRESHOLD == 40.0


# ---------------------------------------------------------------------------
# compute_6month_average
# ---------------------------------------------------------------------------


class TestCompute6MonthAverage:
    """Tests for 6-month rolling average computation."""

    def test_single_value(self):
        result = compute_6month_average([0.6])
        assert result == pytest.approx(0.6)

    def test_multiple_values(self):
        result = compute_6month_average([0.5, 0.6, 0.7])
        assert result == pytest.approx(0.6)

    def test_empty_list_returns_none(self):
        result = compute_6month_average([])
        assert result is None

    def test_uniform_values(self):
        result = compute_6month_average([0.5] * 10)
        assert result == pytest.approx(0.5)

    def test_mixed_positive_negative(self):
        result = compute_6month_average([0.5, -0.1, 0.3])
        assert result == pytest.approx(0.7 / 3)


# ---------------------------------------------------------------------------
# detect_changes
# ---------------------------------------------------------------------------


class TestDetectChanges:
    """Tests for the main change detection logic."""

    def test_no_alert_when_ndvi_stable(self):
        history = [0.6, 0.58, 0.62, 0.59, 0.61]
        result = detect_changes("area-1", 0.58, history)
        assert result is None

    def test_warning_alert_on_significant_drop(self):
        # Average = 0.6, current = 0.45 → 25% drop
        history = [0.6, 0.6, 0.6, 0.6, 0.6]
        result = detect_changes("area-1", 0.45, history)

        assert result is not None
        assert result["alert_level"] == "warning"
        assert result["area_id"] == "area-1"
        assert result["current_ndvi"] == 0.45
        assert result["avg_6month"] == pytest.approx(0.6)
        assert result["change_percent"] == pytest.approx(-25.0)

    def test_critical_alert_on_severe_drop(self):
        # Average = 0.6, current = 0.3 → 50% drop
        history = [0.6, 0.6, 0.6, 0.6, 0.6]
        result = detect_changes("area-2", 0.3, history)

        assert result is not None
        assert result["alert_level"] == "critical"
        assert result["change_percent"] == pytest.approx(-50.0)

    def test_no_alert_when_ndvi_increases(self):
        history = [0.5, 0.5, 0.5]
        result = detect_changes("area-1", 0.7, history)
        assert result is None

    def test_returns_none_for_empty_history(self):
        result = detect_changes("area-1", 0.5, [])
        assert result is None

    def test_boundary_exactly_20_percent_drop_no_alert(self):
        # Average = 0.5, current = 0.4 → exactly 20% drop → no alert
        history = [0.5, 0.5, 0.5]
        result = detect_changes("area-1", 0.4, history)
        assert result is None

    def test_boundary_just_over_20_percent_drop_warning(self):
        # Average = 0.5, current = 0.399 → 20.2% drop → warning
        history = [0.5, 0.5, 0.5]
        result = detect_changes("area-1", 0.399, history)
        assert result is not None
        assert result["alert_level"] == "warning"

    def test_boundary_exactly_40_percent_drop_warning(self):
        # Average = 0.5, current = 0.3 → exactly 40% drop → warning (not critical)
        history = [0.5, 0.5, 0.5]
        result = detect_changes("area-1", 0.3, history)
        assert result is not None
        assert result["alert_level"] == "warning"

    def test_boundary_just_over_40_percent_drop_critical(self):
        # Average = 0.5, current = 0.299 → 40.2% drop → critical
        history = [0.5, 0.5, 0.5]
        result = detect_changes("area-1", 0.299, history)
        assert result is not None
        assert result["alert_level"] == "critical"


# ---------------------------------------------------------------------------
# generate_alert
# ---------------------------------------------------------------------------


class TestGenerateAlert:
    """Tests for MangroveAlert creation."""

    def test_creates_warning_alert(self):
        alert = generate_alert(
            area_id="area-1",
            current_ndvi=0.45,
            avg_6month=0.6,
            alert_level="warning",
            geometry=SAMPLE_GEOMETRY,
        )

        assert isinstance(alert, MangroveAlert)
        assert alert.area_id == "area-1"
        assert alert.alert_level == AlertLevel.WARNING
        assert alert.ndvi_current == 0.45
        assert alert.ndvi_6month_avg == 0.6
        assert alert.change_percent == pytest.approx(-25.0)
        assert alert.geometry == SAMPLE_GEOMETRY
        assert alert.id  # UUID should be set

    def test_creates_critical_alert(self):
        alert = generate_alert(
            area_id="area-2",
            current_ndvi=0.3,
            avg_6month=0.6,
            alert_level="critical",
            geometry=SAMPLE_GEOMETRY,
        )

        assert alert.alert_level == AlertLevel.CRITICAL
        assert alert.change_percent == pytest.approx(-50.0)

    def test_alert_has_utc_timestamp(self):
        alert = generate_alert(
            area_id="area-1",
            current_ndvi=0.4,
            avg_6month=0.6,
            alert_level="warning",
            geometry=SAMPLE_GEOMETRY,
        )

        assert alert.detected_at.tzinfo is not None
        assert alert.detected_at.tzinfo == timezone.utc

    def test_alert_has_unique_id(self):
        alert1 = generate_alert("a", 0.3, 0.6, "warning", SAMPLE_GEOMETRY)
        alert2 = generate_alert("a", 0.3, 0.6, "warning", SAMPLE_GEOMETRY)
        assert alert1.id != alert2.id

    def test_alert_preserves_geometry(self):
        custom_geom = {
            "type": "Polygon",
            "coordinates": [[[98.4, 9.8], [98.7, 9.8], [98.7, 10.1], [98.4, 10.1], [98.4, 9.8]]],
        }
        alert = generate_alert("area-r", 0.2, 0.5, "critical", custom_geom)
        assert alert.geometry == custom_geom


# ---------------------------------------------------------------------------
# store_alert
# ---------------------------------------------------------------------------


class TestStoreAlert:
    """Tests for persisting alerts to the mangrove_alerts table."""

    def _make_alert(
        self,
        alert_level: str = "warning",
        area_id: str = "area-1",
        current_ndvi: float = 0.45,
        avg_6month: float = 0.6,
    ) -> MangroveAlert:
        return MangroveAlert(
            id="test-alert-id-123",
            area_id=area_id,
            alert_level=AlertLevel(alert_level),
            ndvi_current=current_ndvi,
            ndvi_6month_avg=avg_6month,
            change_percent=calculate_change_percent(current_ndvi, avg_6month),
            detected_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            geometry=SAMPLE_GEOMETRY,
        )

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_into_mangrove_alerts_table(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        alert = self._make_alert()
        result_id = store_alert(alert)

        assert result_id == "test-alert-id-123"
        mock_client.table.assert_called_once_with("mangrove_alerts")

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_row_contains_correct_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        alert = self._make_alert(alert_level="critical", current_ndvi=0.3)
        store_alert(alert)

        insert_call = mock_client.table.return_value.insert
        row = insert_call.call_args[0][0]
        assert row["id"] == "test-alert-id-123"
        assert row["area_id"] == "area-1"
        assert row["alert_level"] == "critical"
        assert row["ndvi_current"] == 0.3
        assert row["ndvi_6month_avg"] == 0.6
        assert row["change_percent"] == pytest.approx(-50.0)
        assert row["detected_at"] == "2024-06-15T12:00:00+00:00"
        assert row["geometry"] == SAMPLE_GEOMETRY
        assert row["is_resolved"] is False

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_warning_alert_stored_correctly(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        alert = self._make_alert(alert_level="warning")
        store_alert(alert)

        row = mock_client.table.return_value.insert.call_args[0][0]
        assert row["alert_level"] == "warning"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_returns_alert_id(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        alert = self._make_alert()
        result = store_alert(alert)
        assert result == alert.id
