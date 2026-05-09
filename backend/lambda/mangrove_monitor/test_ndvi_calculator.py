"""
Unit tests for the NDVI calculator module.

Tests cover NDVI calculation, health classification, batch processing of
Sentinel-2 data, and database storage of NDVI records.

Requirements: 2.1, 2.2, 2.3
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

_ndvi = importlib.import_module("lambda.mangrove_monitor.ndvi_calculator")

calculate_ndvi = _ndvi.calculate_ndvi
classify_health = _ndvi.classify_health
process_sentinel2_data = _ndvi.process_sentinel2_data
store_ndvi_records = _ndvi.store_ndvi_records
Sentinel2Input = _ndvi.Sentinel2Input
NDVIRecord = _ndvi.NDVIRecord

_PATCH_PREFIX = "lambda.mangrove_monitor.ndvi_calculator"


# ---------------------------------------------------------------------------
# calculate_ndvi
# ---------------------------------------------------------------------------


class TestCalculateNDVI:
    """Tests for the NDVI formula: (NIR - Red) / (NIR + Red)."""

    def test_typical_healthy_vegetation(self):
        # NIR much higher than Red → high NDVI
        ndvi = calculate_ndvi(nir=0.5, red=0.1)
        assert ndvi == pytest.approx(0.6666, abs=1e-3)

    def test_typical_bare_soil(self):
        # NIR slightly higher than Red → low positive NDVI
        ndvi = calculate_ndvi(nir=0.3, red=0.25)
        assert ndvi == pytest.approx(0.0909, abs=1e-3)

    def test_water_body(self):
        # Red higher than NIR → negative NDVI
        ndvi = calculate_ndvi(nir=0.05, red=0.2)
        assert ndvi == pytest.approx(-0.6, abs=1e-3)

    def test_equal_bands_returns_zero(self):
        ndvi = calculate_ndvi(nir=0.3, red=0.3)
        assert ndvi == 0.0

    def test_division_by_zero_both_zero(self):
        # Both bands zero → return 0.0 (not an error)
        ndvi = calculate_ndvi(nir=0.0, red=0.0)
        assert ndvi == 0.0

    def test_nir_only(self):
        # Red = 0, NIR > 0 → NDVI = 1.0
        ndvi = calculate_ndvi(nir=0.5, red=0.0)
        assert ndvi == 1.0

    def test_red_only(self):
        # NIR = 0, Red > 0 → NDVI = -1.0
        ndvi = calculate_ndvi(nir=0.0, red=0.5)
        assert ndvi == -1.0

    def test_result_in_valid_range(self):
        # For any non-negative inputs, NDVI should be in [-1, 1]
        test_cases = [
            (0.8, 0.1),
            (0.1, 0.8),
            (1.0, 0.0),
            (0.0, 1.0),
            (0.5, 0.5),
            (0.001, 0.999),
        ]
        for nir, red in test_cases:
            ndvi = calculate_ndvi(nir=nir, red=red)
            assert -1.0 <= ndvi <= 1.0, f"NDVI={ndvi} for nir={nir}, red={red}"

    def test_very_small_values(self):
        ndvi = calculate_ndvi(nir=1e-10, red=1e-10)
        assert ndvi == 0.0

    def test_large_values(self):
        ndvi = calculate_ndvi(nir=10000.0, red=5000.0)
        assert ndvi == pytest.approx(1 / 3, abs=1e-6)


# ---------------------------------------------------------------------------
# classify_health
# ---------------------------------------------------------------------------


class TestClassifyHealth:
    """Tests for NDVI health classification thresholds."""

    def test_healthy_above_0_6(self):
        assert classify_health(0.7) == "healthy"
        assert classify_health(0.8) == "healthy"
        assert classify_health(1.0) == "healthy"

    def test_healthy_boundary_just_above(self):
        assert classify_health(0.61) == "healthy"

    def test_moderate_at_0_6(self):
        # 0.6 is the boundary — moderate includes 0.6
        assert classify_health(0.6) == "moderate"

    def test_moderate_range(self):
        assert classify_health(0.5) == "moderate"
        assert classify_health(0.4) == "moderate"

    def test_degraded_boundary_at_0_4(self):
        # 0.4 is moderate (inclusive), just below is degraded
        assert classify_health(0.39) == "degraded"

    def test_degraded_range(self):
        assert classify_health(0.3) == "degraded"
        assert classify_health(0.2) == "degraded"

    def test_critical_below_0_2(self):
        assert classify_health(0.19) == "critical"
        assert classify_health(0.1) == "critical"
        assert classify_health(0.0) == "critical"

    def test_critical_negative_ndvi(self):
        assert classify_health(-0.5) == "critical"
        assert classify_health(-1.0) == "critical"

    def test_all_thresholds_covered(self):
        """Verify the full range maps to exactly one classification."""
        test_values = [-1.0, -0.5, 0.0, 0.1, 0.19, 0.2, 0.3, 0.39,
                       0.4, 0.5, 0.6, 0.61, 0.7, 0.8, 1.0]
        for v in test_values:
            result = classify_health(v)
            assert result in ("healthy", "moderate", "degraded", "critical"), (
                f"Unexpected classification '{result}' for NDVI={v}"
            )


# ---------------------------------------------------------------------------
# process_sentinel2_data
# ---------------------------------------------------------------------------


class TestProcessSentinel2Data:
    """Tests for batch processing of Sentinel-2 data into NDVI records."""

    def _make_input(
        self,
        red: float = 0.1,
        nir: float = 0.5,
        lat: float = 13.5,
        lon: float = 100.3,
        area_id: str = "area-1",
    ) -> Sentinel2Input:
        return Sentinel2Input(
            latitude=lat,
            longitude=lon,
            band_4_red=red,
            band_8_nir=nir,
            observed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            sentinel2_scene_id="S2A_test_scene",
            area_id=area_id,
        )

    def test_processes_single_point(self):
        inputs = [self._make_input(red=0.1, nir=0.5)]
        records = process_sentinel2_data(inputs)

        assert len(records) == 1
        assert records[0].ndvi_value == pytest.approx(0.6666, abs=1e-3)
        assert records[0].health_level == "healthy"
        assert records[0].area_id == "area-1"

    def test_processes_multiple_points(self):
        inputs = [
            self._make_input(red=0.1, nir=0.5),   # NDVI=0.667 → healthy
            self._make_input(red=0.25, nir=0.5),   # NDVI=0.333 → degraded
            self._make_input(red=0.4, nir=0.3),    # NDVI=-0.143 → critical
        ]
        records = process_sentinel2_data(inputs)

        assert len(records) == 3
        assert records[0].health_level == "healthy"
        assert records[1].health_level == "degraded"
        assert records[2].health_level == "critical"

    def test_skips_negative_band_values(self):
        inputs = [
            self._make_input(red=0.1, nir=0.5),
            self._make_input(red=-0.1, nir=0.5),  # invalid
            self._make_input(red=0.1, nir=-0.3),  # invalid
        ]
        records = process_sentinel2_data(inputs)

        assert len(records) == 1

    def test_handles_both_bands_zero(self):
        inputs = [self._make_input(red=0.0, nir=0.0)]
        records = process_sentinel2_data(inputs)

        assert len(records) == 1
        assert records[0].ndvi_value == 0.0
        assert records[0].health_level == "critical"

    def test_empty_input_returns_empty(self):
        records = process_sentinel2_data([])
        assert records == []

    def test_preserves_metadata(self):
        inputs = [self._make_input(area_id="area-42")]
        records = process_sentinel2_data(inputs)

        assert records[0].area_id == "area-42"
        assert records[0].sentinel2_scene_id == "S2A_test_scene"
        assert records[0].latitude == 13.5
        assert records[0].longitude == 100.3

    def test_preserves_timestamp(self):
        ts = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        inp = Sentinel2Input(
            latitude=13.5,
            longitude=100.3,
            band_4_red=0.1,
            band_8_nir=0.5,
            observed_at=ts,
            sentinel2_scene_id="scene-1",
            area_id="area-1",
        )
        records = process_sentinel2_data([inp])
        assert records[0].observed_at == ts


# ---------------------------------------------------------------------------
# store_ndvi_records
# ---------------------------------------------------------------------------


class TestStoreNDVIRecords:
    """Tests for storing NDVI records in the database."""

    def _make_record(
        self,
        ndvi: float = 0.65,
        health: str = "healthy",
        area_id: str = "area-1",
    ) -> NDVIRecord:
        return NDVIRecord(
            area_id=area_id,
            latitude=13.5,
            longitude=100.3,
            ndvi_value=ndvi,
            health_level=health,
            sentinel2_scene_id="S2A_test",
            observed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_records_into_ndvi_records_table(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        records = [self._make_record()]
        count = store_ndvi_records(records)

        assert count == 1
        mock_client.table.assert_called_once_with("ndvi_records")

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_correct_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        records = [self._make_record(ndvi=0.55, health="moderate")]
        store_ndvi_records(records)

        insert_call = mock_client.table.return_value.insert
        rows = insert_call.call_args[0][0]
        assert len(rows) == 1
        row = rows[0]
        assert row["area_id"] == "area-1"
        assert row["ndvi_value"] == 0.55
        assert row["health_level"] == "moderate"
        assert row["sentinel2_scene_id"] == "S2A_test"
        assert "POINT" in row["location"]
        assert "SRID=4326" in row["location"]

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_stores_multiple_records(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        records = [
            self._make_record(ndvi=0.7, health="healthy"),
            self._make_record(ndvi=0.3, health="degraded"),
        ]
        count = store_ndvi_records(records)

        assert count == 2
        rows = mock_client.table.return_value.insert.call_args[0][0]
        assert len(rows) == 2

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_returns_zero_for_empty_list(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        count = store_ndvi_records([])

        assert count == 0
        mock_client.table.assert_not_called()

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_location_wkt_format(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        rec = NDVIRecord(
            area_id="area-1",
            latitude=10.0,
            longitude=98.5,
            ndvi_value=0.5,
            health_level="moderate",
            sentinel2_scene_id="scene-1",
            observed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        store_ndvi_records([rec])

        rows = mock_client.table.return_value.insert.call_args[0][0]
        assert rows[0]["location"] == "SRID=4326;POINT(98.5 10.0)"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_observed_at_is_iso_format(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        records = [self._make_record()]
        store_ndvi_records(records)

        rows = mock_client.table.return_value.insert.call_args[0][0]
        assert rows[0]["observed_at"] == "2024-01-15T00:00:00+00:00"
