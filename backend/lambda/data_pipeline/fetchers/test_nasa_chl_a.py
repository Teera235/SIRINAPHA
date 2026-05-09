"""
Unit tests for the NASA MODIS Chlorophyll-a data fetcher.

Tests cover earthaccess search/download, HDF/NetCDF parsing, data validation,
database storage, and the main fetch orchestration with mocked dependencies.

Requirements: 1.2, 1.6, 1.9
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ``lambda`` is a Python keyword, so we use importlib to load modules.
_nasa_chl_a = importlib.import_module("lambda.data_pipeline.fetchers.nasa_chl_a")
_config = importlib.import_module("lambda.shared.config")

search_modis_granules = _nasa_chl_a.search_modis_granules
download_granules = _nasa_chl_a.download_granules
parse_chl_a_file = _nasa_chl_a.parse_chl_a_file
validate_chl_a_data = _nasa_chl_a.validate_chl_a_data
store_raw_chl_a_data = _nasa_chl_a.store_raw_chl_a_data
fetch_chl_a_for_region = _nasa_chl_a.fetch_chl_a_for_region
fetch_chl_a_all_regions = _nasa_chl_a.fetch_chl_a_all_regions
_find_chl_a_variable = _nasa_chl_a._find_chl_a_variable
_find_coordinate_names = _nasa_chl_a._find_coordinate_names
FetchResult = _nasa_chl_a.FetchResult
ChlADataPoint = _nasa_chl_a.ChlADataPoint

MAHACHAI_BBOX = _config.MAHACHAI_BBOX
RANONG_BBOX = _config.RANONG_BBOX

# Patch target prefix for the nasa_chl_a module
_PATCH_PREFIX = "lambda.data_pipeline.fetchers.nasa_chl_a"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_dataset(
    chl_a_data: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    var_name: str = "chlor_a",
    lat_name: str = "lat",
    lon_name: str = "lon",
):
    """Create a mock xarray-like dataset for testing parse_chl_a_file."""
    ds = MagicMock()
    ds.data_vars = {var_name: MagicMock()}
    ds.coords = {lat_name: MagicMock(), lon_name: MagicMock()}
    ds.dims = {lat_name: len(lats), lon_name: len(lons)}

    ds.__getitem__ = lambda self, key: {
        var_name: MagicMock(values=chl_a_data),
        lat_name: MagicMock(values=lats),
        lon_name: MagicMock(values=lons),
    }[key]

    ds.__contains__ = lambda self, key: key in {var_name, lat_name, lon_name}
    ds.close = MagicMock()
    return ds


# ---------------------------------------------------------------------------
# validate_chl_a_data
# ---------------------------------------------------------------------------


class TestValidateChlAData:
    """Tests for Chl-a data validation."""

    def test_accepts_valid_positive_values(self):
        points = [
            ChlADataPoint(13.5, 100.25, 2.5, datetime(2024, 1, 15, tzinfo=timezone.utc)),
            ChlADataPoint(13.6, 100.35, 0.1, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]
        result = validate_chl_a_data(points)
        assert len(result) == 2

    def test_accepts_zero_value(self):
        points = [
            ChlADataPoint(13.5, 100.25, 0.0, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]
        result = validate_chl_a_data(points)
        assert len(result) == 1

    def test_rejects_nan_values(self):
        points = [
            ChlADataPoint(13.5, 100.25, float("nan"), datetime(2024, 1, 15, tzinfo=timezone.utc)),
            ChlADataPoint(13.6, 100.35, 1.5, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]
        result = validate_chl_a_data(points)
        assert len(result) == 1
        assert result[0].chl_a_mg_m3 == 1.5

    def test_rejects_inf_values(self):
        points = [
            ChlADataPoint(13.5, 100.25, float("inf"), datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]
        result = validate_chl_a_data(points)
        assert len(result) == 0

    def test_rejects_negative_values(self):
        points = [
            ChlADataPoint(13.5, 100.25, -1.0, datetime(2024, 1, 15, tzinfo=timezone.utc)),
            ChlADataPoint(13.6, 100.35, 3.0, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]
        result = validate_chl_a_data(points)
        assert len(result) == 1
        assert result[0].chl_a_mg_m3 == 3.0

    def test_empty_list_returns_empty(self):
        result = validate_chl_a_data([])
        assert result == []


# ---------------------------------------------------------------------------
# _find_chl_a_variable
# ---------------------------------------------------------------------------


class TestFindChlAVariable:
    """Tests for locating the Chl-a variable in a dataset."""

    def test_finds_chlor_a(self):
        ds = MagicMock()
        ds.data_vars = {"chlor_a": MagicMock(), "other": MagicMock()}
        assert _find_chl_a_variable(ds) == "chlor_a"

    def test_finds_chl_a(self):
        ds = MagicMock()
        ds.data_vars = {"chl_a": MagicMock()}
        assert _find_chl_a_variable(ds) == "chl_a"

    def test_finds_CHL(self):
        ds = MagicMock()
        ds.data_vars = {"CHL": MagicMock()}
        assert _find_chl_a_variable(ds) == "CHL"

    def test_finds_by_partial_match(self):
        ds = MagicMock()
        ds.data_vars = {"modis_chlor_a_level3": MagicMock()}
        assert _find_chl_a_variable(ds) == "modis_chlor_a_level3"

    def test_returns_none_when_not_found(self):
        ds = MagicMock()
        ds.data_vars = {"temperature": MagicMock(), "salinity": MagicMock()}
        assert _find_chl_a_variable(ds) is None


# ---------------------------------------------------------------------------
# _find_coordinate_names
# ---------------------------------------------------------------------------


class TestFindCoordinateNames:
    """Tests for locating lat/lon coordinate names."""

    def test_finds_lat_lon(self):
        ds = MagicMock()
        ds.coords = {"lat": MagicMock(), "lon": MagicMock()}
        ds.dims = {}
        assert _find_coordinate_names(ds) == ("lat", "lon")

    def test_finds_latitude_longitude(self):
        ds = MagicMock()
        ds.coords = {"latitude": MagicMock(), "longitude": MagicMock()}
        ds.dims = {}
        assert _find_coordinate_names(ds) == ("latitude", "longitude")

    def test_finds_in_dims(self):
        ds = MagicMock()
        ds.coords = {}
        ds.dims = {"lat": 180, "lon": 360}
        assert _find_coordinate_names(ds) == ("lat", "lon")

    def test_raises_when_not_found(self):
        ds = MagicMock()
        ds.coords = {"x": MagicMock(), "y": MagicMock()}
        ds.dims = {"x": 100, "y": 200}
        with pytest.raises(ValueError, match="Cannot find lat/lon"):
            _find_coordinate_names(ds)


# ---------------------------------------------------------------------------
# store_raw_chl_a_data
# ---------------------------------------------------------------------------


class TestStoreRawChlAData:
    """Tests for database storage of raw Chl-a data."""

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_record_with_correct_source(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            ChlADataPoint(
                latitude=13.5,
                longitude=100.25,
                chl_a_mg_m3=2.5,
                data_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            )
        ]
        fetched_at = datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc)

        store_raw_chl_a_data(points, "mahachai", MAHACHAI_BBOX, fetched_at=fetched_at)

        mock_client.table.assert_called_once_with("satellite_raw_data")
        insert_call = mock_client.table.return_value.insert
        assert insert_call.called
        record = insert_call.call_args[0][0]
        assert record["source"] == "nasa_modis_chl_a"
        assert record["status"] == "valid"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_data_points(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            ChlADataPoint(13.5, 100.25, 2.5, datetime(2024, 1, 15, tzinfo=timezone.utc)),
            ChlADataPoint(13.6, 100.35, 3.1, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]

        store_raw_chl_a_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["data"]["region"] == "mahachai"
        assert len(record["data"]["points"]) == 2
        assert record["data"]["points"][0]["chl_a_mg_m3"] == 2.5

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_coverage_polygon(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            ChlADataPoint(13.5, 100.25, 2.5, datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ]

        store_raw_chl_a_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert "POLYGON" in record["coverage"]
        assert "SRID=4326" in record["coverage"]

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_skips_insert_when_no_data_points(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        store_raw_chl_a_data([], "mahachai", MAHACHAI_BBOX)

        mock_client.table.assert_not_called()

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_has_fetched_at_timestamp(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        fetched_at = datetime(2024, 3, 10, 6, 0, 0, tzinfo=timezone.utc)
        points = [
            ChlADataPoint(10.0, 98.5, 1.8, datetime(2024, 3, 10, tzinfo=timezone.utc)),
        ]

        store_raw_chl_a_data(points, "ranong", RANONG_BBOX, fetched_at=fetched_at)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["fetched_at"] == fetched_at.isoformat()

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_has_bbox_in_data(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            ChlADataPoint(10.0, 98.5, 1.8, datetime(2024, 3, 10, tzinfo=timezone.utc)),
        ]

        store_raw_chl_a_data(points, "ranong", RANONG_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["data"]["bbox"] == RANONG_BBOX


# ---------------------------------------------------------------------------
# fetch_chl_a_for_region
# ---------------------------------------------------------------------------


class TestFetchChlAForRegion:
    """Tests for the main single-region fetch function."""

    @patch(f"{_PATCH_PREFIX}.store_raw_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.validate_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.parse_chl_a_file")
    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_successful_fetch_returns_success(
        self, mock_search, mock_download, mock_parse, mock_validate, mock_store
    ):
        mock_search.return_value = [MagicMock()]
        mock_download.return_value = ["/tmp/test.nc"]
        parsed_points = [
            ChlADataPoint(13.5, 100.25, 2.5, datetime(2024, 1, 15, tzinfo=timezone.utc))
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "success"
        assert result.source == "nasa_modis_chl_a"
        assert result.region == "mahachai"
        assert len(result.data) == 1
        assert result.error is None

    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_search_failure_returns_failed(self, mock_search):
        mock_search.side_effect = Exception("Authentication failed")

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert "Granule search failed" in result.error

    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_no_granules_returns_partial(self, mock_search):
        mock_search.return_value = []

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "partial"
        assert "No MODIS Chl-a granules" in result.error

    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_download_failure_returns_failed(self, mock_search, mock_download):
        mock_search.return_value = [MagicMock()]
        mock_download.side_effect = Exception("Download timeout")

        result = fetch_chl_a_for_region(
            "ranong",
            RANONG_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert "Granule download failed" in result.error

    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_empty_download_returns_partial(self, mock_search, mock_download):
        mock_search.return_value = [MagicMock()]
        mock_download.return_value = []

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "partial"
        assert "No files downloaded" in result.error

    @patch(f"{_PATCH_PREFIX}.validate_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.parse_chl_a_file")
    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_no_valid_data_returns_partial(
        self, mock_search, mock_download, mock_parse, mock_validate
    ):
        mock_search.return_value = [MagicMock()]
        mock_download.return_value = ["/tmp/test.nc"]
        mock_parse.return_value = [
            ChlADataPoint(13.5, 100.25, float("nan"), datetime(2024, 1, 15, tzinfo=timezone.utc))
        ]
        mock_validate.return_value = []

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "partial"
        assert "No valid Chl-a data points" in result.error

    @patch(f"{_PATCH_PREFIX}.store_raw_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.validate_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.parse_chl_a_file")
    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_db_failure_returns_failed_with_data(
        self, mock_search, mock_download, mock_parse, mock_validate, mock_store
    ):
        mock_search.return_value = [MagicMock()]
        mock_download.return_value = ["/tmp/test.nc"]
        parsed_points = [
            ChlADataPoint(13.5, 100.25, 2.5, datetime(2024, 1, 15, tzinfo=timezone.utc))
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points
        mock_store.side_effect = Exception("DB connection failed")

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert "Database storage failed" in result.error
        assert len(result.data) == 1

    @patch(f"{_PATCH_PREFIX}.store_raw_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.validate_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.parse_chl_a_file")
    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_calls_store_with_correct_args(
        self, mock_search, mock_download, mock_parse, mock_validate, mock_store
    ):
        mock_search.return_value = [MagicMock()]
        mock_download.return_value = ["/tmp/test.nc"]
        parsed_points = [
            ChlADataPoint(10.0, 98.5, 1.8, datetime(2024, 1, 15, tzinfo=timezone.utc))
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points

        fetch_chl_a_for_region(
            "ranong",
            RANONG_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][1] == "ranong"  # region
        assert call_args[0][2] == RANONG_BBOX  # bbox

    @patch(f"{_PATCH_PREFIX}.store_raw_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.validate_chl_a_data")
    @patch(f"{_PATCH_PREFIX}.parse_chl_a_file")
    @patch(f"{_PATCH_PREFIX}.download_granules")
    @patch(f"{_PATCH_PREFIX}.search_modis_granules")
    def test_parse_error_still_processes_other_files(
        self, mock_search, mock_download, mock_parse, mock_validate, mock_store
    ):
        mock_search.return_value = [MagicMock(), MagicMock()]
        mock_download.return_value = ["/tmp/bad.nc", "/tmp/good.nc"]
        good_points = [
            ChlADataPoint(13.5, 100.25, 2.5, datetime(2024, 1, 15, tzinfo=timezone.utc))
        ]
        mock_parse.side_effect = [
            Exception("Corrupt file"),
            good_points,
        ]
        mock_validate.return_value = good_points

        result = fetch_chl_a_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "success"
        assert len(result.data) == 1


# ---------------------------------------------------------------------------
# fetch_chl_a_all_regions
# ---------------------------------------------------------------------------


class TestFetchChlAAllRegions:
    """Tests for the multi-region fetch orchestrator."""

    @patch(f"{_PATCH_PREFIX}.fetch_chl_a_for_region")
    def test_fetches_all_configured_regions(self, mock_fetch):
        mock_fetch.return_value = FetchResult(
            source="nasa_modis_chl_a",
            timestamp=datetime.now(timezone.utc),
            status="success",
            region="test",
        )

        results = fetch_chl_a_all_regions(
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
        )

        assert len(results) == 2  # mahachai + ranong
        called_regions = {call.args[0] for call in mock_fetch.call_args_list}
        assert "mahachai" in called_regions
        assert "ranong" in called_regions

    @patch(f"{_PATCH_PREFIX}.fetch_chl_a_for_region")
    def test_returns_results_for_each_region(self, mock_fetch):
        mock_fetch.side_effect = [
            FetchResult(
                source="nasa_modis_chl_a",
                timestamp=datetime.now(timezone.utc),
                status="success",
                region="mahachai",
            ),
            FetchResult(
                source="nasa_modis_chl_a",
                timestamp=datetime.now(timezone.utc),
                status="failed",
                error="timeout",
                region="ranong",
            ),
        ]

        results = fetch_chl_a_all_regions()

        assert results[0].status == "success"
        assert results[1].status == "failed"
