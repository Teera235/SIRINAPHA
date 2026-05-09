"""
Unit tests for the data pipeline validator module.

Tests cover SST, Chl-a, and NDVI band data validation including
valid data acceptance, invalid data rejection, boundary values,
and batch validation.

Requirements: 1.9
"""

from __future__ import annotations

import importlib
import math
from datetime import datetime, timezone

import pytest

_validator = importlib.import_module("lambda.data_pipeline.validator")

validate_sst_data = _validator.validate_sst_data
validate_chl_a_data = _validator.validate_chl_a_data
validate_ndvi_band_data = _validator.validate_ndvi_band_data
validate_batch = _validator.validate_batch
ValidationResult = _validator.ValidationResult

SST_MIN_CELSIUS = _validator.SST_MIN_CELSIUS
SST_MAX_CELSIUS = _validator.SST_MAX_CELSIUS
CHL_A_MIN_MG_M3 = _validator.CHL_A_MIN_MG_M3
CHL_A_MAX_MG_M3 = _validator.CHL_A_MAX_MG_M3
NDVI_BAND_MIN = _validator.NDVI_BAND_MIN
NDVI_BAND_MAX = _validator.NDVI_BAND_MAX


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime(2024, 6, 15, tzinfo=timezone.utc)


def _sst_point(sst=28.5, lat=13.5, lon=100.3, ts=_TS):
    return {
        "sst_celsius": sst,
        "latitude": lat,
        "longitude": lon,
        "data_timestamp": ts,
    }


def _chl_a_point(chl_a=2.5, lat=13.5, lon=100.3, ts=_TS):
    return {
        "chl_a_mg_m3": chl_a,
        "latitude": lat,
        "longitude": lon,
        "data_timestamp": ts,
    }


def _ndvi_point(b4=0.1, b8=0.4, lat=13.5, lon=100.3, ts=_TS):
    return {
        "band_4_red": b4,
        "band_8_nir": b8,
        "latitude": lat,
        "longitude": lon,
        "data_timestamp": ts,
    }


# ---------------------------------------------------------------------------
# SST validation
# ---------------------------------------------------------------------------


class TestValidateSSTData:
    """Tests for SST data validation."""

    def test_valid_sst_in_optimal_range(self):
        result = validate_sst_data(_sst_point(sst=28.5))
        assert result.is_valid is True
        assert result.errors == []

    def test_valid_sst_at_lower_bound(self):
        result = validate_sst_data(_sst_point(sst=SST_MIN_CELSIUS))
        assert result.is_valid is True

    def test_valid_sst_at_upper_bound(self):
        result = validate_sst_data(_sst_point(sst=SST_MAX_CELSIUS))
        assert result.is_valid is True

    def test_invalid_sst_below_range(self):
        result = validate_sst_data(_sst_point(sst=-10.0))
        assert result.is_valid is False
        assert any("out of valid range" in e for e in result.errors)

    def test_invalid_sst_above_range(self):
        result = validate_sst_data(_sst_point(sst=50.0))
        assert result.is_valid is False
        assert any("out of valid range" in e for e in result.errors)

    def test_invalid_sst_nan(self):
        result = validate_sst_data(_sst_point(sst=float("nan")))
        assert result.is_valid is False
        assert any("finite" in e for e in result.errors)

    def test_invalid_sst_inf(self):
        result = validate_sst_data(_sst_point(sst=float("inf")))
        assert result.is_valid is False
        assert any("finite" in e for e in result.errors)

    def test_invalid_sst_not_a_number(self):
        result = validate_sst_data(
            {"sst_celsius": "hot", "latitude": 13.5, "longitude": 100.3, "data_timestamp": _TS}
        )
        assert result.is_valid is False
        assert any("must be a number" in e for e in result.errors)

    def test_missing_sst_field(self):
        result = validate_sst_data(
            {"latitude": 13.5, "longitude": 100.3, "data_timestamp": _TS}
        )
        assert result.is_valid is False
        assert any("Missing required field: sst_celsius" in e for e in result.errors)

    def test_missing_latitude(self):
        result = validate_sst_data(
            {"sst_celsius": 28.0, "longitude": 100.3, "data_timestamp": _TS}
        )
        assert result.is_valid is False
        assert any("Missing required field: latitude" in e for e in result.errors)

    def test_invalid_latitude_out_of_range(self):
        result = validate_sst_data(_sst_point(lat=95.0))
        assert result.is_valid is False
        assert any("latitude" in e and "out of valid range" in e for e in result.errors)

    def test_invalid_longitude_out_of_range(self):
        result = validate_sst_data(_sst_point(lon=200.0))
        assert result.is_valid is False
        assert any("longitude" in e and "out of valid range" in e for e in result.errors)

    def test_none_timestamp_is_invalid(self):
        result = validate_sst_data(_sst_point(ts=None))
        assert result.is_valid is False
        assert any("data_timestamp" in e for e in result.errors)

    def test_valid_sst_zero_degrees(self):
        result = validate_sst_data(_sst_point(sst=0.0))
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# Chl-a validation
# ---------------------------------------------------------------------------


class TestValidateChlAData:
    """Tests for Chlorophyll-a data validation."""

    def test_valid_chl_a_in_optimal_range(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=2.5))
        assert result.is_valid is True
        assert result.errors == []

    def test_valid_chl_a_at_zero(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=0.0))
        assert result.is_valid is True

    def test_valid_chl_a_at_upper_bound(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=CHL_A_MAX_MG_M3))
        assert result.is_valid is True

    def test_invalid_chl_a_negative(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=-0.5))
        assert result.is_valid is False
        assert any("non-negative" in e for e in result.errors)

    def test_invalid_chl_a_above_max(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=150.0))
        assert result.is_valid is False
        assert any("exceeds maximum" in e for e in result.errors)

    def test_invalid_chl_a_nan(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=float("nan")))
        assert result.is_valid is False
        assert any("finite" in e for e in result.errors)

    def test_invalid_chl_a_inf(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=float("inf")))
        assert result.is_valid is False

    def test_missing_chl_a_field(self):
        result = validate_chl_a_data(
            {"latitude": 13.5, "longitude": 100.3, "data_timestamp": _TS}
        )
        assert result.is_valid is False
        assert any("Missing required field: chl_a_mg_m3" in e for e in result.errors)

    def test_invalid_chl_a_not_a_number(self):
        result = validate_chl_a_data(_chl_a_point(chl_a="high"))
        assert result.is_valid is False
        assert any("must be a number" in e for e in result.errors)

    def test_valid_small_chl_a(self):
        result = validate_chl_a_data(_chl_a_point(chl_a=0.01))
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# NDVI band validation
# ---------------------------------------------------------------------------


class TestValidateNDVIBandData:
    """Tests for Sentinel-2 NDVI band data validation."""

    def test_valid_band_values(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=0.1, b8=0.4))
        assert result.is_valid is True
        assert result.errors == []

    def test_valid_band_at_zero(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=0.0, b8=0.0))
        assert result.is_valid is True

    def test_valid_band_at_upper_bound(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=2.0, b8=2.0))
        assert result.is_valid is True

    def test_invalid_band_4_negative(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=-0.1, b8=0.4))
        assert result.is_valid is False
        assert any("band_4_red" in e and "out of valid range" in e for e in result.errors)

    def test_invalid_band_8_negative(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=0.1, b8=-0.5))
        assert result.is_valid is False
        assert any("band_8_nir" in e and "out of valid range" in e for e in result.errors)

    def test_invalid_band_4_above_max(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=2.5, b8=0.4))
        assert result.is_valid is False
        assert any("band_4_red" in e for e in result.errors)

    def test_invalid_band_8_above_max(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=0.1, b8=3.0))
        assert result.is_valid is False
        assert any("band_8_nir" in e for e in result.errors)

    def test_invalid_band_nan(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=float("nan"), b8=0.4))
        assert result.is_valid is False
        assert any("finite" in e for e in result.errors)

    def test_invalid_band_inf(self):
        result = validate_ndvi_band_data(_ndvi_point(b4=0.1, b8=float("inf")))
        assert result.is_valid is False

    def test_missing_band_4_field(self):
        data = {"band_8_nir": 0.4, "latitude": 13.5, "longitude": 100.3, "data_timestamp": _TS}
        result = validate_ndvi_band_data(data)
        assert result.is_valid is False
        assert any("Missing required field: band_4_red" in e for e in result.errors)

    def test_missing_band_8_field(self):
        data = {"band_4_red": 0.1, "latitude": 13.5, "longitude": 100.3, "data_timestamp": _TS}
        result = validate_ndvi_band_data(data)
        assert result.is_valid is False
        assert any("Missing required field: band_8_nir" in e for e in result.errors)

    def test_invalid_band_not_a_number(self):
        result = validate_ndvi_band_data(_ndvi_point(b4="red", b8=0.4))
        assert result.is_valid is False
        assert any("must be a number" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Batch validation
# ---------------------------------------------------------------------------


class TestValidateBatch:
    """Tests for batch validation across data sources."""

    def test_all_valid_sst_points(self):
        points = [_sst_point(sst=28.0), _sst_point(sst=29.5)]
        valid, invalid = validate_batch(points, "sst")
        assert len(valid) == 2
        assert len(invalid) == 0

    def test_mixed_valid_and_invalid_sst(self):
        points = [
            _sst_point(sst=28.0),
            _sst_point(sst=100.0),  # invalid
            _sst_point(sst=29.0),
        ]
        valid, invalid = validate_batch(points, "sst")
        assert len(valid) == 2
        assert len(invalid) == 1
        assert "_validation_errors" in invalid[0]

    def test_all_invalid_points(self):
        points = [_sst_point(sst=float("nan")), _sst_point(sst=999.0)]
        valid, invalid = validate_batch(points, "sst")
        assert len(valid) == 0
        assert len(invalid) == 2

    def test_batch_chl_a_source(self):
        points = [_chl_a_point(chl_a=2.0), _chl_a_point(chl_a=-1.0)]
        valid, invalid = validate_batch(points, "chl_a")
        assert len(valid) == 1
        assert len(invalid) == 1

    def test_batch_ndvi_source(self):
        points = [_ndvi_point(b4=0.1, b8=0.4), _ndvi_point(b4=-1.0, b8=0.4)]
        valid, invalid = validate_batch(points, "ndvi")
        assert len(valid) == 1
        assert len(invalid) == 1

    def test_unknown_source_raises_error(self):
        with pytest.raises(ValueError, match="Unknown data source"):
            validate_batch([], "unknown_source")

    def test_empty_batch_returns_empty(self):
        valid, invalid = validate_batch([], "sst")
        assert valid == []
        assert invalid == []
