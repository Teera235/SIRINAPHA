"""
Unit tests for the NOAA OISST SST data fetcher.

Tests cover URL construction, ERDDAP response parsing, database storage,
and the main fetch orchestration with mocked HTTP and Supabase calls.

Requirements: 1.1, 1.6, 1.9
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# ``lambda`` is a Python keyword, so we use importlib to load modules.
_noaa_sst = importlib.import_module("lambda.data_pipeline.fetchers.noaa_sst")
_config = importlib.import_module("lambda.shared.config")

build_erddap_url = _noaa_sst.build_erddap_url
parse_erddap_response = _noaa_sst.parse_erddap_response
store_raw_sst_data = _noaa_sst.store_raw_sst_data
fetch_sst_for_region = _noaa_sst.fetch_sst_for_region
fetch_sst_all_regions = _noaa_sst.fetch_sst_all_regions
FetchResult = _noaa_sst.FetchResult
SSTDataPoint = _noaa_sst.SSTDataPoint

MAHACHAI_BBOX = _config.MAHACHAI_BBOX
RANONG_BBOX = _config.RANONG_BBOX

# Patch target prefix for the noaa_sst module
_PATCH_PREFIX = "lambda.data_pipeline.fetchers.noaa_sst"


# ---------------------------------------------------------------------------
# build_erddap_url
# ---------------------------------------------------------------------------


class TestBuildErddapUrl:
    """Tests for ERDDAP URL construction."""

    def test_url_contains_base_and_dataset(self):
        url = build_erddap_url(
            "2024-01-15T00:00:00Z",
            MAHACHAI_BBOX,
            base_url="https://example.com/erddap",
            dataset_id="test_dataset",
        )
        assert "https://example.com/erddap/griddap/test_dataset.json" in url

    def test_url_contains_date_constraint(self):
        url = build_erddap_url("2024-06-01T00:00:00Z", MAHACHAI_BBOX)
        assert "2024-06-01T00:00:00Z" in url

    def test_url_contains_bbox_coordinates(self):
        url = build_erddap_url("2024-01-15T00:00:00Z", MAHACHAI_BBOX)
        assert str(MAHACHAI_BBOX["lat_min"]) in url
        assert str(MAHACHAI_BBOX["lat_max"]) in url
        assert str(MAHACHAI_BBOX["lon_min"]) in url
        assert str(MAHACHAI_BBOX["lon_max"]) in url

    def test_url_uses_json_format(self):
        url = build_erddap_url("2024-01-15T00:00:00Z", RANONG_BBOX)
        assert ".json?" in url

    def test_url_for_ranong_region(self):
        url = build_erddap_url("2024-01-15T00:00:00Z", RANONG_BBOX)
        assert str(RANONG_BBOX["lat_min"]) in url
        assert str(RANONG_BBOX["lon_min"]) in url


# ---------------------------------------------------------------------------
# parse_erddap_response
# ---------------------------------------------------------------------------


def _make_erddap_response(rows, column_names=None):
    """Helper to build a mock ERDDAP JSON response."""
    if column_names is None:
        column_names = ["time", "latitude", "longitude", "sst"]
    return {
        "table": {
            "columnNames": column_names,
            "columnTypes": ["String", "float", "float", "float"],
            "rows": rows,
        }
    }


class TestParseErddapResponse:
    """Tests for ERDDAP JSON response parsing."""

    def test_parses_single_row(self):
        resp = _make_erddap_response(
            [["2024-01-15T00:00:00Z", 13.5, 100.25, 28.3]]
        )
        points = parse_erddap_response(resp)
        assert len(points) == 1
        assert points[0].latitude == 13.5
        assert points[0].longitude == 100.25
        assert points[0].sst_celsius == 28.3

    def test_parses_multiple_rows(self):
        resp = _make_erddap_response(
            [
                ["2024-01-15T00:00:00Z", 13.4, 100.2, 27.5],
                ["2024-01-15T00:00:00Z", 13.5, 100.3, 28.1],
                ["2024-01-15T00:00:00Z", 13.6, 100.4, 29.0],
            ]
        )
        points = parse_erddap_response(resp)
        assert len(points) == 3

    def test_skips_nan_sst_values(self):
        resp = _make_erddap_response(
            [
                ["2024-01-15T00:00:00Z", 13.5, 100.25, float("nan")],
                ["2024-01-15T00:00:00Z", 13.6, 100.35, 28.0],
            ]
        )
        points = parse_erddap_response(resp)
        assert len(points) == 1
        assert points[0].sst_celsius == 28.0

    def test_skips_none_sst_values(self):
        resp = _make_erddap_response(
            [
                ["2024-01-15T00:00:00Z", 13.5, 100.25, None],
                ["2024-01-15T00:00:00Z", 13.6, 100.35, 27.0],
            ]
        )
        points = parse_erddap_response(resp)
        assert len(points) == 1

    def test_empty_rows_returns_empty_list(self):
        resp = _make_erddap_response([])
        points = parse_erddap_response(resp)
        assert points == []

    def test_empty_table_returns_empty_list(self):
        resp = {"table": {}}
        points = parse_erddap_response(resp)
        assert points == []

    def test_missing_table_key_returns_empty_list(self):
        resp = {}
        points = parse_erddap_response(resp)
        assert points == []

    def test_raises_on_missing_required_columns(self):
        resp = _make_erddap_response(
            [["2024-01-15T00:00:00Z", 13.5]],
            column_names=["time", "latitude"],
        )
        with pytest.raises(ValueError, match="missing required columns"):
            parse_erddap_response(resp)

    def test_parses_timestamp_correctly(self):
        resp = _make_erddap_response(
            [["2024-06-15T00:00:00Z", 10.0, 98.5, 29.5]]
        )
        points = parse_erddap_response(resp)
        assert points[0].data_timestamp == datetime(
            2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc
        )

    def test_handles_reordered_columns(self):
        """Parser should work regardless of column order."""
        resp = {
            "table": {
                "columnNames": ["sst", "longitude", "time", "latitude"],
                "columnTypes": ["float", "float", "String", "float"],
                "rows": [[28.5, 100.3, "2024-01-15T00:00:00Z", 13.5]],
            }
        }
        points = parse_erddap_response(resp)
        assert len(points) == 1
        assert points[0].sst_celsius == 28.5
        assert points[0].latitude == 13.5
        assert points[0].longitude == 100.3


# ---------------------------------------------------------------------------
# store_raw_sst_data
# ---------------------------------------------------------------------------


class TestStoreRawSstData:
    """Tests for database storage of raw SST data."""

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_record_with_correct_source(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            SSTDataPoint(
                latitude=13.5,
                longitude=100.25,
                sst_celsius=28.3,
                data_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            )
        ]
        fetched_at = datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc)

        store_raw_sst_data(points, "mahachai", MAHACHAI_BBOX, fetched_at=fetched_at)

        mock_client.table.assert_called_once_with("satellite_raw_data")
        insert_call = mock_client.table.return_value.insert
        assert insert_call.called
        record = insert_call.call_args[0][0]
        assert record["source"] == "noaa_oisst"
        assert record["status"] == "valid"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_data_points(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            SSTDataPoint(13.5, 100.25, 28.3, datetime(2024, 1, 15, tzinfo=timezone.utc)),
            SSTDataPoint(13.6, 100.35, 29.0, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]

        store_raw_sst_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["data"]["region"] == "mahachai"
        assert len(record["data"]["points"]) == 2
        assert record["data"]["points"][0]["sst_celsius"] == 28.3

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_coverage_polygon(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            SSTDataPoint(13.5, 100.25, 28.3, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]

        store_raw_sst_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert "POLYGON" in record["coverage"]
        assert "SRID=4326" in record["coverage"]

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_skips_insert_when_no_data_points(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        store_raw_sst_data([], "mahachai", MAHACHAI_BBOX)

        mock_client.table.assert_not_called()

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_has_fetched_at_timestamp(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        fetched_at = datetime(2024, 3, 10, 6, 0, 0, tzinfo=timezone.utc)
        points = [
            SSTDataPoint(13.5, 100.25, 28.3, datetime(2024, 3, 10, tzinfo=timezone.utc)),
        ]

        store_raw_sst_data(points, "ranong", RANONG_BBOX, fetched_at=fetched_at)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["fetched_at"] == fetched_at.isoformat()


# ---------------------------------------------------------------------------
# fetch_sst_for_region
# ---------------------------------------------------------------------------


class TestFetchSstForRegion:
    """Tests for the main single-region fetch function."""

    @patch(f"{_PATCH_PREFIX}.store_raw_sst_data")
    @patch(f"{_PATCH_PREFIX}.requests.get")
    def test_successful_fetch_returns_success(self, mock_get, mock_store):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_erddap_response(
            [["2024-01-15T00:00:00Z", 13.5, 100.25, 28.3]]
        )
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_sst_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "success"
        assert result.source == "noaa_oisst"
        assert result.region == "mahachai"
        assert len(result.data) == 1
        assert result.error is None

    @patch(f"{_PATCH_PREFIX}.requests.get")
    def test_http_error_returns_failed(self, mock_get):
        import requests as _requests
        mock_get.side_effect = _requests.ConnectionError("Connection timeout")

        result = fetch_sst_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert result.error is not None
        assert "Connection timeout" in result.error

    @patch(f"{_PATCH_PREFIX}.requests.get")
    def test_invalid_json_returns_failed(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = fetch_sst_for_region(
            "ranong",
            RANONG_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert "Invalid JSON" in result.error

    @patch(f"{_PATCH_PREFIX}.store_raw_sst_data")
    @patch(f"{_PATCH_PREFIX}.requests.get")
    def test_empty_data_returns_partial(self, mock_get, mock_store):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = _make_erddap_response([])
        mock_get.return_value = mock_response

        result = fetch_sst_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "partial"
        assert result.data == []

    @patch(f"{_PATCH_PREFIX}.store_raw_sst_data")
    @patch(f"{_PATCH_PREFIX}.requests.get")
    def test_db_failure_returns_failed_with_data(self, mock_get, mock_store):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = _make_erddap_response(
            [["2024-01-15T00:00:00Z", 13.5, 100.25, 28.3]]
        )
        mock_get.return_value = mock_response
        mock_store.side_effect = Exception("DB connection failed")

        result = fetch_sst_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert "Database storage failed" in result.error
        # Data was parsed successfully even though storage failed
        assert len(result.data) == 1

    @patch(f"{_PATCH_PREFIX}.store_raw_sst_data")
    @patch(f"{_PATCH_PREFIX}.requests.get")
    def test_calls_store_with_correct_args(self, mock_get, mock_store):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = _make_erddap_response(
            [["2024-01-15T00:00:00Z", 13.5, 100.25, 28.3]]
        )
        mock_get.return_value = mock_response

        fetch_sst_for_region(
            "ranong",
            RANONG_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][1] == "ranong"  # region
        assert call_args[0][2] == RANONG_BBOX  # bbox


# ---------------------------------------------------------------------------
# fetch_sst_all_regions
# ---------------------------------------------------------------------------


class TestFetchSstAllRegions:
    """Tests for the multi-region fetch orchestrator."""

    @patch(f"{_PATCH_PREFIX}.fetch_sst_for_region")
    def test_fetches_all_configured_regions(self, mock_fetch):
        mock_fetch.return_value = FetchResult(
            source="noaa_oisst",
            timestamp=datetime.now(timezone.utc),
            status="success",
            region="test",
        )

        results = fetch_sst_all_regions(
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
        )

        assert len(results) == 2  # mahachai + ranong
        # Verify both regions were called
        called_regions = {call.args[0] for call in mock_fetch.call_args_list}
        assert "mahachai" in called_regions
        assert "ranong" in called_regions

    @patch(f"{_PATCH_PREFIX}.fetch_sst_for_region")
    def test_returns_results_for_each_region(self, mock_fetch):
        mock_fetch.side_effect = [
            FetchResult(
                source="noaa_oisst",
                timestamp=datetime.now(timezone.utc),
                status="success",
                region="mahachai",
            ),
            FetchResult(
                source="noaa_oisst",
                timestamp=datetime.now(timezone.utc),
                status="failed",
                error="timeout",
                region="ranong",
            ),
        ]

        results = fetch_sst_all_regions()

        assert results[0].status == "success"
        assert results[1].status == "failed"
