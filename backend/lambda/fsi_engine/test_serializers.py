"""
Unit tests for FSI Engine — serializers module.

Covers:
  • FSI ↔ JSON round-trip (Requirements 11.1, 11.4)
  • FSI ↔ GeoJSON round-trip (Requirements 11.2, 11.5)
  • Thai text formatting (Requirement 11.3)
  • Invalid JSON error handling (Requirement 11.6)
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone

import pytest

_ser = importlib.import_module("lambda.fsi_engine.serializers")
fsi_to_json = _ser.fsi_to_json
json_to_fsi = _ser.json_to_fsi
fsi_to_geojson = _ser.fsi_to_geojson
geojson_to_fsi = _ser.geojson_to_fsi
fsi_to_thai_text = _ser.fsi_to_thai_text
parse_fsi_json = _ser.parse_fsi_json
FSIParseError = _ser.FSIParseError
ZONE_THAI = _ser.ZONE_THAI

_models = importlib.import_module("lambda.shared.models")
FSIComponentScores = _models.FSIComponentScores
FSIDataCompleteness = _models.FSIDataCompleteness
FSIResult = _models.FSIResult
FSIZone = _models.FSIZone
GeoPoint = _models.GeoPoint


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

LOCATION = GeoPoint(lat=13.5463, lng=100.2742)
NOW = datetime(2024, 6, 15, 8, 0, 0)

COMPONENT_SCORES = FSIComponentScores(
    sst_score=1.0,
    chl_a_score=0.85,
    depth_score=1.0,
    lunar_score=0.65,
    ndvi_score=0.75,
    season_score=0.9,
)

DATA_COMPLETE = FSIDataCompleteness(
    available_sources=["chl_a", "depth", "lunar", "ndvi", "season", "sst"],
    missing_sources=[],
    is_complete=True,
)

DATA_PARTIAL = FSIDataCompleteness(
    available_sources=["chl_a", "sst"],
    missing_sources=["depth", "lunar", "ndvi", "season"],
    is_complete=False,
)


def _make_fsi(
    fsi_value: float = 0.67,
    zone: FSIZone = FSIZone.YELLOW,
    location: GeoPoint = LOCATION,
    component_scores: FSIComponentScores = COMPONENT_SCORES,
    data_completeness: FSIDataCompleteness = DATA_COMPLETE,
    calculated_at: datetime = NOW,
) -> FSIResult:
    return FSIResult(
        fsi_value=fsi_value,
        zone=zone,
        location=location,
        component_scores=component_scores,
        data_completeness=data_completeness,
        calculated_at=calculated_at,
    )


# ===================================================================
# 6.1  FSI ↔ JSON  (Requirements 11.1, 11.4)
# ===================================================================


class TestFsiToJson:
    """fsi_to_json produces a dict matching the FSIJson interface."""

    def test_fsi_value_preserved(self):
        d = fsi_to_json(_make_fsi(fsi_value=0.67))
        assert d["fsi_value"] == pytest.approx(0.67)

    def test_zone_is_string(self):
        d = fsi_to_json(_make_fsi(zone=FSIZone.YELLOW))
        assert d["zone"] == "yellow"

    def test_zone_green(self):
        d = fsi_to_json(_make_fsi(zone=FSIZone.GREEN))
        assert d["zone"] == "green"

    def test_zone_red(self):
        d = fsi_to_json(_make_fsi(zone=FSIZone.RED))
        assert d["zone"] == "red"

    def test_location_lat_lng(self):
        d = fsi_to_json(_make_fsi())
        assert d["location"]["lat"] == pytest.approx(13.5463)
        assert d["location"]["lng"] == pytest.approx(100.2742)

    def test_component_scores_all_present(self):
        d = fsi_to_json(_make_fsi())
        cs = d["component_scores"]
        assert set(cs.keys()) == {
            "sst_score", "chl_a_score", "depth_score",
            "lunar_score", "ndvi_score", "season_score",
        }

    def test_component_scores_values(self):
        d = fsi_to_json(_make_fsi())
        cs = d["component_scores"]
        assert cs["sst_score"] == pytest.approx(1.0)
        assert cs["chl_a_score"] == pytest.approx(0.85)

    def test_calculated_at_iso_format(self):
        d = fsi_to_json(_make_fsi())
        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(d["calculated_at"])
        assert parsed == NOW

    def test_data_completeness_complete(self):
        d = fsi_to_json(_make_fsi(data_completeness=DATA_COMPLETE))
        dc = d["data_completeness"]
        assert dc["missing_sources"] == []
        assert len(dc["available_sources"]) == 6

    def test_data_completeness_partial(self):
        d = fsi_to_json(_make_fsi(data_completeness=DATA_PARTIAL))
        dc = d["data_completeness"]
        assert dc["available_sources"] == ["chl_a", "sst"]
        assert "depth" in dc["missing_sources"]

    def test_json_serializable(self):
        """The dict must be fully JSON-serializable."""
        d = fsi_to_json(_make_fsi())
        raw = json.dumps(d)
        assert isinstance(raw, str)


class TestJsonToFsi:
    """json_to_fsi reconstructs an FSIResult from a dict."""

    def test_round_trip_fsi_value(self):
        original = _make_fsi(fsi_value=0.42)
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.fsi_value == pytest.approx(original.fsi_value)

    def test_round_trip_zone(self):
        for zone in FSIZone:
            original = _make_fsi(zone=zone)
            restored = json_to_fsi(fsi_to_json(original))
            assert restored.zone == original.zone

    def test_round_trip_location(self):
        original = _make_fsi()
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.location.lat == pytest.approx(original.location.lat)
        assert restored.location.lng == pytest.approx(original.location.lng)

    def test_round_trip_component_scores(self):
        original = _make_fsi()
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.component_scores.sst_score == pytest.approx(
            original.component_scores.sst_score
        )
        assert restored.component_scores.chl_a_score == pytest.approx(
            original.component_scores.chl_a_score
        )
        assert restored.component_scores.depth_score == pytest.approx(
            original.component_scores.depth_score
        )
        assert restored.component_scores.lunar_score == pytest.approx(
            original.component_scores.lunar_score
        )
        assert restored.component_scores.ndvi_score == pytest.approx(
            original.component_scores.ndvi_score
        )
        assert restored.component_scores.season_score == pytest.approx(
            original.component_scores.season_score
        )

    def test_round_trip_calculated_at(self):
        original = _make_fsi()
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.calculated_at == original.calculated_at

    def test_round_trip_data_completeness(self):
        original = _make_fsi(data_completeness=DATA_PARTIAL)
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.data_completeness.available_sources == original.data_completeness.available_sources
        assert restored.data_completeness.missing_sources == original.data_completeness.missing_sources
        assert restored.data_completeness.is_complete == original.data_completeness.is_complete

    def test_round_trip_complete_data(self):
        original = _make_fsi(data_completeness=DATA_COMPLETE)
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.data_completeness.is_complete is True

    def test_boundary_fsi_zero(self):
        original = _make_fsi(fsi_value=0.0, zone=FSIZone.RED)
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.fsi_value == pytest.approx(0.0)

    def test_boundary_fsi_one(self):
        original = _make_fsi(fsi_value=1.0, zone=FSIZone.GREEN)
        restored = json_to_fsi(fsi_to_json(original))
        assert restored.fsi_value == pytest.approx(1.0)


# ===================================================================
# 6.2  FSI ↔ GeoJSON  (Requirements 11.2, 11.5)
# ===================================================================


class TestFsiToGeojson:
    """fsi_to_geojson produces a valid GeoJSON Feature."""

    def test_type_is_feature(self):
        d = fsi_to_geojson(_make_fsi())
        assert d["type"] == "Feature"

    def test_geometry_type_is_point(self):
        d = fsi_to_geojson(_make_fsi())
        assert d["geometry"]["type"] == "Point"

    def test_coordinates_lng_lat_order(self):
        """GeoJSON coordinates are [lng, lat]."""
        d = fsi_to_geojson(_make_fsi())
        coords = d["geometry"]["coordinates"]
        assert coords[0] == pytest.approx(100.2742)  # lng
        assert coords[1] == pytest.approx(13.5463)   # lat

    def test_properties_fsi_value(self):
        d = fsi_to_geojson(_make_fsi(fsi_value=0.82))
        assert d["properties"]["fsi_value"] == pytest.approx(0.82)

    def test_properties_zone(self):
        d = fsi_to_geojson(_make_fsi(zone=FSIZone.GREEN))
        assert d["properties"]["zone"] == "green"

    def test_properties_component_scores(self):
        d = fsi_to_geojson(_make_fsi())
        cs = d["properties"]["component_scores"]
        assert "sst_score" in cs
        assert "chl_a_score" in cs

    def test_properties_calculated_at(self):
        d = fsi_to_geojson(_make_fsi())
        assert "calculated_at" in d["properties"]
        datetime.fromisoformat(d["properties"]["calculated_at"])

    def test_properties_data_completeness(self):
        d = fsi_to_geojson(_make_fsi())
        dc = d["properties"]["data_completeness"]
        assert "available_sources" in dc
        assert "missing_sources" in dc

    def test_json_serializable(self):
        d = fsi_to_geojson(_make_fsi())
        raw = json.dumps(d)
        assert isinstance(raw, str)


class TestGeojsonToFsi:
    """geojson_to_fsi reconstructs an FSIResult from a GeoJSON Feature."""

    def test_round_trip_fsi_value(self):
        original = _make_fsi(fsi_value=0.55)
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.fsi_value == pytest.approx(original.fsi_value)

    def test_round_trip_zone(self):
        for zone in FSIZone:
            original = _make_fsi(zone=zone)
            restored = geojson_to_fsi(fsi_to_geojson(original))
            assert restored.zone == original.zone

    def test_round_trip_location(self):
        """Coordinates survive the [lng, lat] ↔ GeoPoint round-trip."""
        original = _make_fsi()
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.location.lat == pytest.approx(original.location.lat)
        assert restored.location.lng == pytest.approx(original.location.lng)

    def test_round_trip_component_scores(self):
        original = _make_fsi()
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.component_scores.sst_score == pytest.approx(
            original.component_scores.sst_score
        )
        assert restored.component_scores.ndvi_score == pytest.approx(
            original.component_scores.ndvi_score
        )

    def test_round_trip_calculated_at(self):
        original = _make_fsi()
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.calculated_at == original.calculated_at

    def test_round_trip_data_completeness(self):
        original = _make_fsi(data_completeness=DATA_PARTIAL)
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.data_completeness.available_sources == original.data_completeness.available_sources
        assert restored.data_completeness.missing_sources == original.data_completeness.missing_sources

    def test_boundary_fsi_zero(self):
        original = _make_fsi(fsi_value=0.0, zone=FSIZone.RED)
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.fsi_value == pytest.approx(0.0)

    def test_boundary_fsi_one(self):
        original = _make_fsi(fsi_value=1.0, zone=FSIZone.GREEN)
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.fsi_value == pytest.approx(1.0)

    def test_negative_coordinates(self):
        """Locations in the southern/western hemispheres."""
        loc = GeoPoint(lat=-6.2, lng=-35.8)
        original = _make_fsi(location=loc)
        restored = geojson_to_fsi(fsi_to_geojson(original))
        assert restored.location.lat == pytest.approx(-6.2)
        assert restored.location.lng == pytest.approx(-35.8)


# ===================================================================
# 6.3  Thai text formatting  (Requirement 11.3)
# ===================================================================


class TestFsiToThaiText:
    """fsi_to_thai_text produces a Thai summary with required fields."""

    def test_contains_fsi_value(self):
        text = fsi_to_thai_text(_make_fsi(fsi_value=0.67))
        assert "0.67" in text

    def test_contains_area_name(self):
        text = fsi_to_thai_text(_make_fsi(), area_name="มหาชัย")
        assert "มหาชัย" in text

    def test_contains_chart_emoji(self):
        text = fsi_to_thai_text(_make_fsi())
        assert "📊" in text

    def test_green_zone_thai(self):
        text = fsi_to_thai_text(_make_fsi(zone=FSIZone.GREEN))
        assert "เหมาะสมมาก" in text
        assert "🟢" in text

    def test_yellow_zone_thai(self):
        text = fsi_to_thai_text(_make_fsi(zone=FSIZone.YELLOW))
        assert "เหมาะสมปานกลาง" in text
        assert "🟡" in text

    def test_red_zone_thai(self):
        text = fsi_to_thai_text(_make_fsi(zone=FSIZone.RED))
        assert "ไม่เหมาะสม" in text
        assert "🔴" in text

    def test_contains_component_scores(self):
        text = fsi_to_thai_text(_make_fsi())
        assert "SST:" in text
        assert "Chl-a:" in text

    def test_default_area_name(self):
        text = fsi_to_thai_text(_make_fsi())
        assert "พื้นที่" in text

    def test_multiline_output(self):
        text = fsi_to_thai_text(_make_fsi())
        lines = text.strip().split("\n")
        assert len(lines) >= 2

    def test_fsi_zero(self):
        text = fsi_to_thai_text(_make_fsi(fsi_value=0.0, zone=FSIZone.RED))
        assert "0.00" in text

    def test_fsi_one(self):
        text = fsi_to_thai_text(_make_fsi(fsi_value=1.0, zone=FSIZone.GREEN))
        assert "1.00" in text


# ===================================================================
# 6.4  Invalid JSON error handling  (Requirement 11.6)
# ===================================================================


class TestParseFsiJson:
    """parse_fsi_json handles malformed input gracefully."""

    def test_valid_json_returns_fsi_result(self):
        original = _make_fsi()
        raw = json.dumps(fsi_to_json(original))
        result = parse_fsi_json(raw)
        assert isinstance(result, FSIResult)
        assert result.fsi_value == pytest.approx(original.fsi_value)

    def test_empty_string_returns_error(self):
        result = parse_fsi_json("")
        assert isinstance(result, FSIParseError)
        assert result.cause is not None

    def test_malformed_json_returns_error_with_position(self):
        result = parse_fsi_json('{"fsi_value": }')
        assert isinstance(result, FSIParseError)
        assert result.position is not None
        assert isinstance(result.position, int)

    def test_malformed_json_cause_describes_problem(self):
        result = parse_fsi_json("{bad json}")
        assert isinstance(result, FSIParseError)
        assert "Invalid JSON" in result.cause

    def test_missing_field_returns_error(self):
        # Valid JSON but missing required fields
        result = parse_fsi_json('{"fsi_value": 0.5}')
        assert isinstance(result, FSIParseError)
        assert "Missing required field" in result.cause

    def test_invalid_zone_returns_error(self):
        original = _make_fsi()
        d = fsi_to_json(original)
        d["zone"] = "purple"  # invalid zone
        raw = json.dumps(d)
        result = parse_fsi_json(raw)
        assert isinstance(result, FSIParseError)
        assert "Invalid field value" in result.cause

    def test_non_numeric_fsi_value_returns_error(self):
        original = _make_fsi()
        d = fsi_to_json(original)
        d["fsi_value"] = "not_a_number"
        raw = json.dumps(d)
        result = parse_fsi_json(raw)
        assert isinstance(result, FSIParseError)

    def test_truncated_json_returns_error(self):
        result = parse_fsi_json('{"fsi_value": 0.5, "zone": "green"')
        assert isinstance(result, FSIParseError)
        assert result.position is not None

    def test_null_input_returns_error(self):
        result = parse_fsi_json("null")
        assert isinstance(result, FSIParseError)

    def test_array_input_returns_error(self):
        result = parse_fsi_json("[1, 2, 3]")
        assert isinstance(result, FSIParseError)

    def test_never_raises_exception(self):
        """parse_fsi_json must never raise — always returns a value."""
        bad_inputs = [
            "",
            "null",
            "42",
            '"string"',
            "[1,2]",
            "{}",
            '{"fsi_value": "bad"}',
            "{bad}",
            '{"fsi_value": 0.5, "zone": "green", "location": null}',
        ]
        for raw in bad_inputs:
            result = parse_fsi_json(raw)
            assert isinstance(result, (FSIResult, FSIParseError)), (
                f"Unexpected type for input {raw!r}: {type(result)}"
            )

    def test_error_to_dict(self):
        result = parse_fsi_json("{bad}")
        assert isinstance(result, FSIParseError)
        d = result.to_dict()
        assert d["error"] is True
        assert "cause" in d
        assert "position" in d

    def test_error_repr(self):
        result = parse_fsi_json("{bad}")
        assert isinstance(result, FSIParseError)
        r = repr(result)
        assert "FSIParseError" in r
