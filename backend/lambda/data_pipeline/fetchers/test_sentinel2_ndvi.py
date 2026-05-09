"""
Unit tests for the Sentinel-2 NDVI data fetcher.

Tests cover OAuth2 authentication, Process API request building, response
parsing, data validation, database storage, and the main fetch orchestration
with mocked HTTP and Supabase calls.

Requirements: 1.3, 1.6, 1.9
"""

from __future__ import annotations

import importlib
import math
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# ``lambda`` is a Python keyword, so we use importlib to load modules.
_sentinel2 = importlib.import_module("lambda.data_pipeline.fetchers.sentinel2_ndvi")
_config = importlib.import_module("lambda.shared.config")

authenticate_copernicus = _sentinel2.authenticate_copernicus
build_process_request = _sentinel2.build_process_request
fetch_sentinel2_bands = _sentinel2.fetch_sentinel2_bands
parse_sentinel2_response = _sentinel2.parse_sentinel2_response
_extract_band_values = _sentinel2._extract_band_values
validate_sentinel2_data = _sentinel2.validate_sentinel2_data
store_raw_sentinel2_data = _sentinel2.store_raw_sentinel2_data
fetch_sentinel2_for_region = _sentinel2.fetch_sentinel2_for_region
fetch_sentinel2_all_regions = _sentinel2.fetch_sentinel2_all_regions
FetchResult = _sentinel2.FetchResult
Sentinel2DataPoint = _sentinel2.Sentinel2DataPoint

MAHACHAI_BBOX = _config.MAHACHAI_BBOX
RANONG_BBOX = _config.RANONG_BBOX

# Patch target prefix for the sentinel2_ndvi module
_PATCH_PREFIX = "lambda.data_pipeline.fetchers.sentinel2_ndvi"


# ---------------------------------------------------------------------------
# authenticate_copernicus
# ---------------------------------------------------------------------------


class TestAuthenticateCopernicus:
    """Tests for Copernicus OAuth2 authentication."""

    @patch(f"{_PATCH_PREFIX}.requests.post")
    def test_returns_access_token_on_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-token-123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        token = authenticate_copernicus(
            client_id="test-id",
            client_secret="test-secret",
        )

        assert token == "test-token-123"

    @patch(f"{_PATCH_PREFIX}.requests.post")
    def test_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "tok"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        authenticate_copernicus(
            client_id="my-id",
            client_secret="my-secret",
        )

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")
        assert payload["grant_type"] == "client_credentials"
        assert payload["client_id"] == "my-id"
        assert payload["client_secret"] == "my-secret"

    def test_raises_when_credentials_missing(self):
        with pytest.raises(ValueError, match="COPERNICUS_CLIENT_ID"):
            authenticate_copernicus(client_id="", client_secret="secret")

    def test_raises_when_secret_missing(self):
        with pytest.raises(ValueError, match="COPERNICUS_CLIENT_ID"):
            authenticate_copernicus(client_id="id", client_secret="")

    @patch(f"{_PATCH_PREFIX}.requests.post")
    def test_raises_on_http_error(self, mock_post):
        import requests as _requests

        mock_post.side_effect = _requests.ConnectionError("Connection refused")

        with pytest.raises(_requests.ConnectionError):
            authenticate_copernicus(
                client_id="id", client_secret="secret"
            )

    @patch(f"{_PATCH_PREFIX}.requests.post")
    def test_raises_when_no_access_token_in_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "invalid_client"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="No access_token"):
            authenticate_copernicus(
                client_id="id", client_secret="secret"
            )


# ---------------------------------------------------------------------------
# build_process_request
# ---------------------------------------------------------------------------


class TestBuildProcessRequest:
    """Tests for Sentinel Hub Process API request construction."""

    def test_request_contains_bbox(self):
        req = build_process_request(
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        bbox = req["input"]["bounds"]["bbox"]
        assert bbox[0] == MAHACHAI_BBOX["lon_min"]
        assert bbox[1] == MAHACHAI_BBOX["lat_min"]
        assert bbox[2] == MAHACHAI_BBOX["lon_max"]
        assert bbox[3] == MAHACHAI_BBOX["lat_max"]

    def test_request_contains_5_day_time_range(self):
        target = datetime(2024, 1, 15, tzinfo=timezone.utc)
        req = build_process_request(MAHACHAI_BBOX, target)
        time_range = req["input"]["data"][0]["dataFilter"]["timeRange"]
        assert "2024-01-10" in time_range["from"]
        assert "2024-01-15" in time_range["to"]

    def test_request_uses_sentinel2_l2a(self):
        req = build_process_request(
            RANONG_BBOX,
            datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        assert req["input"]["data"][0]["type"] == "sentinel-2-l2a"

    def test_request_has_max_cloud_coverage(self):
        req = build_process_request(
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        cloud = req["input"]["data"][0]["dataFilter"]["maxCloudCoverage"]
        assert cloud == 30

    def test_request_has_evalscript_with_b04_b08(self):
        req = build_process_request(
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        evalscript = req["evalscript"]
        assert "B04" in evalscript
        assert "B08" in evalscript

    def test_request_has_json_output_format(self):
        req = build_process_request(
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        responses = req["output"]["responses"]
        assert any(r["format"]["type"] == "application/json" for r in responses)

    def test_request_uses_epsg_4326(self):
        req = build_process_request(
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        crs = req["input"]["bounds"]["properties"]["crs"]
        assert "4326" in crs


# ---------------------------------------------------------------------------
# _extract_band_values
# ---------------------------------------------------------------------------


class TestExtractBandValues:
    """Tests for band value extraction from various sample formats."""

    def test_extracts_from_list(self):
        b4, b8 = _extract_band_values([0.1, 0.5])
        assert b4 == 0.1
        assert b8 == 0.5

    def test_extracts_from_tuple(self):
        b4, b8 = _extract_band_values((0.2, 0.6))
        assert b4 == 0.2
        assert b8 == 0.6

    def test_extracts_from_dict_B04_B08(self):
        b4, b8 = _extract_band_values({"B04": 0.15, "B08": 0.55})
        assert b4 == 0.15
        assert b8 == 0.55

    def test_extracts_from_dict_lowercase(self):
        b4, b8 = _extract_band_values({"b04": 0.12, "b08": 0.48})
        assert b4 == 0.12
        assert b8 == 0.48

    def test_extracts_from_dict_descriptive_keys(self):
        b4, b8 = _extract_band_values(
            {"band_4_red": 0.1, "band_8_nir": 0.4}
        )
        assert b4 == 0.1
        assert b8 == 0.4

    def test_returns_none_for_short_list(self):
        b4, b8 = _extract_band_values([0.1])
        assert b4 is None
        assert b8 is None

    def test_returns_none_for_invalid_type(self):
        b4, b8 = _extract_band_values("invalid")
        assert b4 is None
        assert b8 is None

    def test_returns_none_for_non_numeric_list(self):
        b4, b8 = _extract_band_values(["abc", "def"])
        assert b4 is None
        assert b8 is None

    def test_returns_none_for_empty_dict(self):
        b4, b8 = _extract_band_values({})
        assert b4 is None
        assert b8 is None


# ---------------------------------------------------------------------------
# parse_sentinel2_response
# ---------------------------------------------------------------------------


class TestParseSentinel2Response:
    """Tests for Sentinel Hub Process API response parsing."""

    def test_parses_list_of_lists(self):
        response_data = [[0.1, 0.5], [0.2, 0.6], [0.15, 0.55], [0.18, 0.52]]
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert len(points) == 4
        assert points[0].band_4_red == 0.1
        assert points[0].band_8_nir == 0.5

    def test_parses_dict_with_data_key(self):
        response_data = {
            "data": [[0.1, 0.5], [0.2, 0.6]],
        }
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert len(points) == 2

    def test_parses_dict_with_samples_key(self):
        response_data = {
            "samples": [{"B04": 0.1, "B08": 0.5}],
        }
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert len(points) == 1

    def test_assigns_scene_id(self):
        response_data = [[0.1, 0.5]]
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
            scene_id="S2A_MSIL2A_20240115",
        )
        assert points[0].sentinel2_scene_id == "S2A_MSIL2A_20240115"

    def test_auto_generates_scene_id(self):
        response_data = [[0.1, 0.5]]
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert "S2_L2A_20240115" in points[0].sentinel2_scene_id

    def test_empty_list_returns_empty(self):
        points = parse_sentinel2_response(
            [],
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert points == []

    def test_empty_dict_returns_empty(self):
        points = parse_sentinel2_response(
            {},
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert points == []

    def test_unexpected_type_returns_empty(self):
        points = parse_sentinel2_response(
            "unexpected",
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert points == []

    def test_coordinates_within_bbox(self):
        # 4 samples -> 2x2 grid
        response_data = [[0.1, 0.5], [0.2, 0.6], [0.15, 0.55], [0.18, 0.52]]
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        for p in points:
            assert MAHACHAI_BBOX["lat_min"] <= p.latitude <= MAHACHAI_BBOX["lat_max"]
            assert MAHACHAI_BBOX["lon_min"] <= p.longitude <= MAHACHAI_BBOX["lon_max"]

    def test_skips_invalid_samples(self):
        response_data = [[0.1, 0.5], ["bad", "data"], [0.2, 0.6]]
        points = parse_sentinel2_response(
            response_data,
            MAHACHAI_BBOX,
            datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert len(points) == 2


# ---------------------------------------------------------------------------
# validate_sentinel2_data
# ---------------------------------------------------------------------------


class TestValidateSentinel2Data:
    """Tests for Sentinel-2 data validation."""

    def test_accepts_valid_reflectance_values(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
            Sentinel2DataPoint(
                13.6, 100.35, 0.2, 0.6,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 2

    def test_accepts_zero_values(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.0, 0.0,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 1

    def test_rejects_nan_band4(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, float("nan"), 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 0

    def test_rejects_nan_band8(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, float("nan"),
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 0

    def test_rejects_inf_values(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, float("inf"), 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
            Sentinel2DataPoint(
                13.6, 100.35, 0.1, float("-inf"),
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 0

    def test_rejects_negative_band4(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, -0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 0

    def test_rejects_negative_band8(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, -0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 0

    def test_mixed_valid_and_invalid(self):
        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
            Sentinel2DataPoint(
                13.6, 100.35, float("nan"), 0.6,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
            Sentinel2DataPoint(
                13.7, 100.45, 0.2, 0.7,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]
        result = validate_sentinel2_data(points)
        assert len(result) == 2

    def test_empty_list_returns_empty(self):
        result = validate_sentinel2_data([])
        assert result == []


# ---------------------------------------------------------------------------
# store_raw_sentinel2_data
# ---------------------------------------------------------------------------


class TestStoreRawSentinel2Data:
    """Tests for database storage of raw Sentinel-2 data."""

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_record_with_correct_source(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            Sentinel2DataPoint(
                latitude=13.5,
                longitude=100.25,
                band_4_red=0.1,
                band_8_nir=0.5,
                data_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
                sentinel2_scene_id="S2A_test",
            )
        ]
        fetched_at = datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc)

        store_raw_sentinel2_data(
            points, "mahachai", MAHACHAI_BBOX, fetched_at=fetched_at
        )

        mock_client.table.assert_called_once_with("satellite_raw_data")
        insert_call = mock_client.table.return_value.insert
        assert insert_call.called
        record = insert_call.call_args[0][0]
        assert record["source"] == "sentinel2_ndvi"
        assert record["status"] == "valid"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_sentinel2_scene_id(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "S2A_MSIL2A_20240115",
            )
        ]

        store_raw_sentinel2_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["data"]["sentinel2_scene_id"] == "S2A_MSIL2A_20240115"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_band_data_points(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
            Sentinel2DataPoint(
                13.6, 100.35, 0.2, 0.6,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]

        store_raw_sentinel2_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["data"]["region"] == "mahachai"
        assert len(record["data"]["points"]) == 2
        assert record["data"]["points"][0]["band_4_red"] == 0.1
        assert record["data"]["points"][0]["band_8_nir"] == 0.5

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_contains_coverage_polygon(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            ),
        ]

        store_raw_sentinel2_data(points, "mahachai", MAHACHAI_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert "POLYGON" in record["coverage"]
        assert "SRID=4326" in record["coverage"]

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_skips_insert_when_no_data_points(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        store_raw_sentinel2_data([], "mahachai", MAHACHAI_BBOX)

        mock_client.table.assert_not_called()

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_has_fetched_at_timestamp(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        fetched_at = datetime(2024, 3, 10, 6, 0, 0, tzinfo=timezone.utc)
        points = [
            Sentinel2DataPoint(
                10.0, 98.5, 0.15, 0.55,
                datetime(2024, 3, 10, tzinfo=timezone.utc),
                "scene1",
            ),
        ]

        store_raw_sentinel2_data(
            points, "ranong", RANONG_BBOX, fetched_at=fetched_at
        )

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["fetched_at"] == fetched_at.isoformat()

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_record_has_bbox_in_data(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        points = [
            Sentinel2DataPoint(
                10.0, 98.5, 0.15, 0.55,
                datetime(2024, 3, 10, tzinfo=timezone.utc),
                "scene1",
            ),
        ]

        store_raw_sentinel2_data(points, "ranong", RANONG_BBOX)

        record = mock_client.table.return_value.insert.call_args[0][0]
        assert record["data"]["bbox"] == RANONG_BBOX


# ---------------------------------------------------------------------------
# fetch_sentinel2_for_region
# ---------------------------------------------------------------------------


class TestFetchSentinel2ForRegion:
    """Tests for the main single-region fetch function."""

    @patch(f"{_PATCH_PREFIX}.store_raw_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.validate_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.parse_sentinel2_response")
    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_successful_fetch_returns_success(
        self, mock_fetch_bands, mock_parse, mock_validate, mock_store
    ):
        mock_fetch_bands.return_value = [[0.1, 0.5]]
        parsed_points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            )
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        assert result.status == "success"
        assert result.source == "sentinel2_ndvi"
        assert result.region == "mahachai"
        assert len(result.data) == 1
        assert result.error is None

    @patch(f"{_PATCH_PREFIX}.authenticate_copernicus")
    def test_auth_failure_returns_failed(self, mock_auth):
        mock_auth.side_effect = ValueError("Missing credentials")

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        assert result.status == "failed"
        assert "Authentication failed" in result.error

    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_api_error_returns_failed(self, mock_fetch_bands):
        import requests as _requests

        mock_fetch_bands.side_effect = _requests.ConnectionError("Timeout")

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        assert result.status == "failed"
        assert "Process API request failed" in result.error

    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_invalid_response_returns_failed(self, mock_fetch_bands):
        mock_fetch_bands.side_effect = ValueError("Invalid JSON")

        result = fetch_sentinel2_for_region(
            "ranong",
            RANONG_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        assert result.status == "failed"
        assert "Invalid response" in result.error

    @patch(f"{_PATCH_PREFIX}.parse_sentinel2_response")
    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_empty_data_returns_partial(self, mock_fetch_bands, mock_parse):
        mock_fetch_bands.return_value = []
        mock_parse.return_value = []

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        assert result.status == "partial"
        assert result.data == []

    @patch(f"{_PATCH_PREFIX}.validate_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.parse_sentinel2_response")
    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_no_valid_data_returns_partial(
        self, mock_fetch_bands, mock_parse, mock_validate
    ):
        mock_fetch_bands.return_value = [[float("nan"), 0.5]]
        mock_parse.return_value = [
            Sentinel2DataPoint(
                13.5, 100.25, float("nan"), 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            )
        ]
        mock_validate.return_value = []

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        assert result.status == "partial"
        assert "No valid Sentinel-2 data points" in result.error

    @patch(f"{_PATCH_PREFIX}.store_raw_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.validate_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.parse_sentinel2_response")
    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_db_failure_returns_failed_with_data(
        self, mock_fetch_bands, mock_parse, mock_validate, mock_store
    ):
        mock_fetch_bands.return_value = [[0.1, 0.5]]
        parsed_points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            )
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points
        mock_store.side_effect = Exception("DB connection failed")

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        assert result.status == "failed"
        assert "Database storage failed" in result.error
        assert len(result.data) == 1

    @patch(f"{_PATCH_PREFIX}.store_raw_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.validate_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.parse_sentinel2_response")
    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    def test_calls_store_with_correct_args(
        self, mock_fetch_bands, mock_parse, mock_validate, mock_store
    ):
        mock_fetch_bands.return_value = [[0.15, 0.55]]
        parsed_points = [
            Sentinel2DataPoint(
                10.0, 98.5, 0.15, 0.55,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            )
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points

        fetch_sentinel2_for_region(
            "ranong",
            RANONG_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            access_token="test-token",
        )

        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][1] == "ranong"  # region
        assert call_args[0][2] == RANONG_BBOX  # bbox

    @patch(f"{_PATCH_PREFIX}.store_raw_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.validate_sentinel2_data")
    @patch(f"{_PATCH_PREFIX}.parse_sentinel2_response")
    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_bands")
    @patch(f"{_PATCH_PREFIX}.authenticate_copernicus")
    def test_authenticates_when_no_token_provided(
        self, mock_auth, mock_fetch_bands, mock_parse, mock_validate, mock_store
    ):
        mock_auth.return_value = "auto-token"
        mock_fetch_bands.return_value = [[0.1, 0.5]]
        parsed_points = [
            Sentinel2DataPoint(
                13.5, 100.25, 0.1, 0.5,
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                "scene1",
            )
        ]
        mock_parse.return_value = parsed_points
        mock_validate.return_value = parsed_points

        result = fetch_sentinel2_for_region(
            "mahachai",
            MAHACHAI_BBOX,
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        mock_auth.assert_called_once()
        assert result.status == "success"


# ---------------------------------------------------------------------------
# fetch_sentinel2_all_regions
# ---------------------------------------------------------------------------


class TestFetchSentinel2AllRegions:
    """Tests for the multi-region fetch orchestrator."""

    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_for_region")
    @patch(f"{_PATCH_PREFIX}.authenticate_copernicus")
    def test_fetches_all_configured_regions(self, mock_auth, mock_fetch):
        mock_auth.return_value = "shared-token"
        mock_fetch.return_value = FetchResult(
            source="sentinel2_ndvi",
            timestamp=datetime.now(timezone.utc),
            status="success",
            region="test",
        )

        results = fetch_sentinel2_all_regions(
            target_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
        )

        assert len(results) == 2  # mahachai + ranong
        called_regions = {call.args[0] for call in mock_fetch.call_args_list}
        assert "mahachai" in called_regions
        assert "ranong" in called_regions

    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_for_region")
    @patch(f"{_PATCH_PREFIX}.authenticate_copernicus")
    def test_authenticates_once_for_all_regions(self, mock_auth, mock_fetch):
        mock_auth.return_value = "shared-token"
        mock_fetch.return_value = FetchResult(
            source="sentinel2_ndvi",
            timestamp=datetime.now(timezone.utc),
            status="success",
            region="test",
        )

        fetch_sentinel2_all_regions()

        mock_auth.assert_called_once()
        # Verify token is passed to each region fetch
        for call in mock_fetch.call_args_list:
            assert call.kwargs.get("access_token") == "shared-token"

    @patch(f"{_PATCH_PREFIX}.fetch_sentinel2_for_region")
    @patch(f"{_PATCH_PREFIX}.authenticate_copernicus")
    def test_returns_results_for_each_region(self, mock_auth, mock_fetch):
        mock_auth.return_value = "token"
        mock_fetch.side_effect = [
            FetchResult(
                source="sentinel2_ndvi",
                timestamp=datetime.now(timezone.utc),
                status="success",
                region="mahachai",
            ),
            FetchResult(
                source="sentinel2_ndvi",
                timestamp=datetime.now(timezone.utc),
                status="failed",
                error="cloud coverage too high",
                region="ranong",
            ),
        ]

        results = fetch_sentinel2_all_regions()

        assert results[0].status == "success"
        assert results[1].status == "failed"

    @patch(f"{_PATCH_PREFIX}.authenticate_copernicus")
    def test_auth_failure_returns_failed_for_all_regions(self, mock_auth):
        mock_auth.side_effect = ValueError("Missing credentials")

        results = fetch_sentinel2_all_regions()

        assert len(results) == 2
        for r in results:
            assert r.status == "failed"
            assert "Authentication failed" in r.error
