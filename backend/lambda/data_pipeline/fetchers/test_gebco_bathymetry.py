"""
Unit tests for the GEBCO Bathymetry Data Loader.

Tests cover data loading, caching, depth queries at specific coordinates,
bounding box extraction, and graceful error handling for missing files.

Requirements: 1.4
"""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

_gebco = importlib.import_module("lambda.data_pipeline.fetchers.gebco_bathymetry")
_config = importlib.import_module("lambda.shared.config")

load_gebco = _gebco.load_gebco
clear_cache = _gebco.clear_cache
get_depth_at_point = _gebco.get_depth_at_point
get_depths_in_bbox = _gebco.get_depths_in_bbox
get_depths_all_regions = _gebco.get_depths_all_regions
DepthPoint = _gebco.DepthPoint

MAHACHAI_BBOX = _config.MAHACHAI_BBOX
RANONG_BBOX = _config.RANONG_BBOX

_PATCH_PREFIX = "lambda.data_pipeline.fetchers.gebco_bathymetry"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gebco_data(
    lat_range=(13.0, 14.0),
    lon_range=(100.0, 101.0),
    n_lat=11,
    n_lon=11,
    base_elevation=-25.0,
):
    """Create a synthetic GEBCO-like data dict for testing.

    Generates a grid of lat/lon with uniform elevation (negative = ocean).
    """
    lats = np.linspace(lat_range[0], lat_range[1], n_lat)
    lons = np.linspace(lon_range[0], lon_range[1], n_lon)
    elevation = np.full((n_lat, n_lon), base_elevation)
    return {"lat": lats, "lon": lons, "elevation": elevation}


@pytest.fixture(autouse=True)
def _clear_gebco_cache():
    """Ensure the GEBCO cache is cleared before and after each test."""
    clear_cache()
    yield
    clear_cache()


# ---------------------------------------------------------------------------
# load_gebco — caching behaviour
# ---------------------------------------------------------------------------


class TestLoadGebco:
    """Tests for GEBCO data loading and caching."""

    @patch(f"{_PATCH_PREFIX}._load_gebco_dataset")
    def test_loads_data_from_disk(self, mock_load):
        mock_data = _make_gebco_data()
        mock_load.return_value = mock_data

        result = load_gebco(file_path="/fake/gebco.nc")

        mock_load.assert_called_once_with("/fake/gebco.nc")
        assert "lat" in result
        assert "lon" in result
        assert "elevation" in result

    @patch(f"{_PATCH_PREFIX}._load_gebco_dataset")
    def test_caches_data_on_second_call(self, mock_load):
        mock_data = _make_gebco_data()
        mock_load.return_value = mock_data

        load_gebco(file_path="/fake/gebco.nc")
        load_gebco(file_path="/fake/gebco.nc")

        # Should only load from disk once
        assert mock_load.call_count == 1

    @patch(f"{_PATCH_PREFIX}._load_gebco_dataset")
    def test_force_reload_bypasses_cache(self, mock_load):
        mock_data = _make_gebco_data()
        mock_load.return_value = mock_data

        load_gebco(file_path="/fake/gebco.nc")
        load_gebco(file_path="/fake/gebco.nc", force_reload=True)

        assert mock_load.call_count == 2

    @patch(f"{_PATCH_PREFIX}._load_gebco_dataset")
    def test_clear_cache_forces_reload(self, mock_load):
        mock_data = _make_gebco_data()
        mock_load.return_value = mock_data

        load_gebco(file_path="/fake/gebco.nc")
        clear_cache()
        load_gebco(file_path="/fake/gebco.nc")

        assert mock_load.call_count == 2


# ---------------------------------------------------------------------------
# _load_gebco_dataset — error handling
# ---------------------------------------------------------------------------


class TestLoadGebcoDataset:
    """Tests for the internal dataset loading function."""

    def test_raises_file_not_found_for_missing_file(self):
        with pytest.raises(FileNotFoundError, match="GEBCO bathymetry file not found"):
            _gebco._load_gebco_dataset("/nonexistent/path/gebco.nc")


# ---------------------------------------------------------------------------
# get_depth_at_point
# ---------------------------------------------------------------------------


class TestGetDepthAtPoint:
    """Tests for single-point depth queries."""

    def test_returns_positive_depth_for_ocean(self):
        data = _make_gebco_data(base_elevation=-30.0)
        depth = get_depth_at_point(13.5, 100.5, gebco_data=data)
        assert depth == 30.0

    def test_returns_zero_for_land(self):
        data = _make_gebco_data(base_elevation=50.0)
        depth = get_depth_at_point(13.5, 100.5, gebco_data=data)
        assert depth == 0.0

    def test_returns_zero_for_sea_level(self):
        data = _make_gebco_data(base_elevation=0.0)
        depth = get_depth_at_point(13.5, 100.5, gebco_data=data)
        assert depth == 0.0

    def test_nearest_neighbour_interpolation(self):
        """Depth query should find the nearest grid cell."""
        data = _make_gebco_data(
            lat_range=(13.0, 14.0),
            lon_range=(100.0, 101.0),
            n_lat=3,
            n_lon=3,
        )
        # Set a specific cell to a known depth
        data["elevation"][1, 1] = -42.0  # lat=13.5, lon=100.5

        depth = get_depth_at_point(13.5, 100.5, gebco_data=data)
        assert depth == 42.0

    def test_handles_edge_coordinates(self):
        data = _make_gebco_data(
            lat_range=(13.0, 14.0),
            lon_range=(100.0, 101.0),
            base_elevation=-10.0,
        )
        # Query at the exact edge of the grid
        depth = get_depth_at_point(13.0, 100.0, gebco_data=data)
        assert depth == 10.0

    def test_varying_depths_across_grid(self):
        """Different grid cells should return different depths."""
        data = _make_gebco_data(n_lat=3, n_lon=3)
        data["elevation"][0, 0] = -10.0
        data["elevation"][2, 2] = -50.0

        depth_shallow = get_depth_at_point(13.0, 100.0, gebco_data=data)
        depth_deep = get_depth_at_point(14.0, 101.0, gebco_data=data)

        assert depth_shallow == 10.0
        assert depth_deep == 50.0


# ---------------------------------------------------------------------------
# get_depths_in_bbox
# ---------------------------------------------------------------------------


class TestGetDepthsInBbox:
    """Tests for bounding box depth extraction."""

    def test_returns_points_within_bbox(self):
        data = _make_gebco_data(
            lat_range=(13.0, 14.0),
            lon_range=(100.0, 101.0),
            n_lat=11,
            n_lon=11,
            base_elevation=-20.0,
        )
        bbox = {"lat_min": 13.4, "lat_max": 13.6, "lon_min": 100.2, "lon_max": 100.5}
        points = get_depths_in_bbox(bbox, gebco_data=data)

        assert len(points) > 0
        for pt in points:
            assert isinstance(pt, DepthPoint)
            assert pt.latitude >= bbox["lat_min"]
            assert pt.latitude <= bbox["lat_max"]
            assert pt.longitude >= bbox["lon_min"]
            assert pt.longitude <= bbox["lon_max"]
            assert pt.depth_meters == 20.0

    def test_returns_empty_for_bbox_outside_data(self):
        data = _make_gebco_data(
            lat_range=(13.0, 14.0),
            lon_range=(100.0, 101.0),
        )
        bbox = {"lat_min": 50.0, "lat_max": 51.0, "lon_min": 0.0, "lon_max": 1.0}
        points = get_depths_in_bbox(bbox, gebco_data=data)
        assert points == []

    def test_depth_values_are_positive_for_ocean(self):
        data = _make_gebco_data(base_elevation=-35.0)
        points = get_depths_in_bbox(MAHACHAI_BBOX, gebco_data=data)

        for pt in points:
            assert pt.depth_meters >= 0.0

    def test_mahachai_bbox_extraction(self):
        data = _make_gebco_data(
            lat_range=(13.0, 14.0),
            lon_range=(100.0, 101.0),
            n_lat=21,
            n_lon=21,
            base_elevation=-15.0,
        )
        points = get_depths_in_bbox(MAHACHAI_BBOX, gebco_data=data)
        assert len(points) > 0


# ---------------------------------------------------------------------------
# get_depths_all_regions
# ---------------------------------------------------------------------------


class TestGetDepthsAllRegions:
    """Tests for multi-region depth extraction."""

    def test_returns_results_for_all_regions(self):
        # Create data covering both Mahachai and Ranong
        data = _make_gebco_data(
            lat_range=(9.0, 14.0),
            lon_range=(98.0, 101.0),
            n_lat=51,
            n_lon=31,
            base_elevation=-20.0,
        )
        results = get_depths_all_regions(gebco_data=data)

        assert "mahachai" in results
        assert "ranong" in results
        assert len(results["mahachai"]) > 0
        assert len(results["ranong"]) > 0

    def test_each_region_has_depth_points(self):
        data = _make_gebco_data(
            lat_range=(9.0, 14.0),
            lon_range=(98.0, 101.0),
            n_lat=51,
            n_lon=31,
            base_elevation=-30.0,
        )
        results = get_depths_all_regions(gebco_data=data)

        for region_name, points in results.items():
            assert all(isinstance(pt, DepthPoint) for pt in points), (
                f"Region {region_name} has non-DepthPoint entries"
            )
