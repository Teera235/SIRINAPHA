"""
FSI Engine — Serializers

Converts FSI results between internal Python objects and external formats:
  • JSON   — for API responses (Requirement 11.1, 11.4)
  • GeoJSON — for map display  (Requirement 11.2, 11.5)
  • Thai text — for LINE/SMS   (Requirement 11.3)
  • Error-safe JSON parsing     (Requirement 11.6)

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
"""

from __future__ import annotations

import importlib as _il
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

_models = _il.import_module("lambda.shared.models")
FSIComponentScores = _models.FSIComponentScores
FSIDataCompleteness = _models.FSIDataCompleteness
FSIResult = _models.FSIResult
FSIZone = _models.FSIZone
GeoPoint = _models.GeoPoint


# ---------------------------------------------------------------------------
# Zone → Thai label mapping  (Requirement 11.3)
# ---------------------------------------------------------------------------

ZONE_THAI: Dict[str, str] = {
    "green": "เหมาะสมมาก 🟢",
    "yellow": "เหมาะสมปานกลาง 🟡",
    "red": "ไม่เหมาะสม 🔴",
}


# ---------------------------------------------------------------------------
# Structured parse error
# ---------------------------------------------------------------------------

class FSIParseError:
    """Structured error returned when JSON parsing fails (Requirement 11.6).

    Attributes
    ----------
    position : int | None
        Character offset where the error was detected (0-based), or ``None``
        if the position cannot be determined.
    cause : str
        Human-readable description of the error.
    raw_input : str
        The original input string that failed to parse.
    """

    def __init__(self, *, position: Optional[int], cause: str, raw_input: str) -> None:
        self.position = position
        self.cause = cause
        self.raw_input = raw_input

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "position": self.position,
            "cause": self.cause,
        }

    def __repr__(self) -> str:
        return (
            f"FSIParseError(position={self.position!r}, "
            f"cause={self.cause!r})"
        )


# ===================================================================
# 6.1  FSI ↔ JSON  (Requirements 11.1, 11.4)
# ===================================================================


def fsi_to_json(result: FSIResult) -> Dict[str, Any]:
    """Serialize an :class:`FSIResult` to a JSON-compatible dict.

    The returned dict follows the ``FSIJson`` interface from the design:

    .. code-block:: json

        {
          "fsi_value": 0.67,
          "zone": "yellow",
          "location": {"lat": 13.5, "lng": 100.3},
          "component_scores": {"sst_score": 1.0, ...},
          "calculated_at": "2024-06-15T08:00:00+00:00",
          "data_completeness": {
            "available_sources": ["sst", "chl_a", ...],
            "missing_sources": []
          }
        }
    """
    return {
        "fsi_value": result.fsi_value,
        "zone": result.zone.value,
        "location": {"lat": result.location.lat, "lng": result.location.lng},
        "component_scores": {
            "sst_score": result.component_scores.sst_score,
            "chl_a_score": result.component_scores.chl_a_score,
            "depth_score": result.component_scores.depth_score,
            "lunar_score": result.component_scores.lunar_score,
            "ndvi_score": result.component_scores.ndvi_score,
            "season_score": result.component_scores.season_score,
        },
        "calculated_at": result.calculated_at.isoformat(),
        "data_completeness": {
            "available_sources": list(result.data_completeness.available_sources),
            "missing_sources": list(result.data_completeness.missing_sources),
        },
    }


def json_to_fsi(data: Dict[str, Any]) -> FSIResult:
    """Deserialize a JSON-compatible dict back to an :class:`FSIResult`.

    This is the inverse of :func:`fsi_to_json` and supports the round-trip
    property (Requirement 11.4).
    """
    loc = data["location"]
    cs = data["component_scores"]
    dc = data["data_completeness"]

    return FSIResult(
        fsi_value=float(data["fsi_value"]),
        zone=FSIZone(data["zone"]),
        location=GeoPoint(lat=float(loc["lat"]), lng=float(loc["lng"])),
        component_scores=FSIComponentScores(
            sst_score=float(cs["sst_score"]),
            chl_a_score=float(cs["chl_a_score"]),
            depth_score=float(cs["depth_score"]),
            lunar_score=float(cs["lunar_score"]),
            ndvi_score=float(cs["ndvi_score"]),
            season_score=float(cs["season_score"]),
        ),
        calculated_at=datetime.fromisoformat(data["calculated_at"]),
        data_completeness=FSIDataCompleteness(
            available_sources=list(dc["available_sources"]),
            missing_sources=list(dc["missing_sources"]),
            is_complete=len(dc["missing_sources"]) == 0,
        ),
    )


# ===================================================================
# 6.2  FSI ↔ GeoJSON  (Requirements 11.2, 11.5)
# ===================================================================


def fsi_to_geojson(result: FSIResult) -> Dict[str, Any]:
    """Serialize an :class:`FSIResult` to a GeoJSON Feature dict.

    Follows the ``FSIGeoJSON`` interface from the design:
    - ``geometry.coordinates`` is ``[lng, lat]`` (GeoJSON order).
    - All FSI data goes into ``properties``.
    """
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [result.location.lng, result.location.lat],
        },
        "properties": {
            "fsi_value": result.fsi_value,
            "zone": result.zone.value,
            "component_scores": {
                "sst_score": result.component_scores.sst_score,
                "chl_a_score": result.component_scores.chl_a_score,
                "depth_score": result.component_scores.depth_score,
                "lunar_score": result.component_scores.lunar_score,
                "ndvi_score": result.component_scores.ndvi_score,
                "season_score": result.component_scores.season_score,
            },
            "calculated_at": result.calculated_at.isoformat(),
            "data_completeness": {
                "available_sources": list(result.data_completeness.available_sources),
                "missing_sources": list(result.data_completeness.missing_sources),
            },
        },
    }


def geojson_to_fsi(data: Dict[str, Any]) -> FSIResult:
    """Deserialize a GeoJSON Feature dict back to an :class:`FSIResult`.

    This is the inverse of :func:`fsi_to_geojson` and supports the
    round-trip property (Requirement 11.5).
    """
    coords = data["geometry"]["coordinates"]  # [lng, lat]
    props = data["properties"]
    cs = props["component_scores"]
    dc = props["data_completeness"]

    return FSIResult(
        fsi_value=float(props["fsi_value"]),
        zone=FSIZone(props["zone"]),
        location=GeoPoint(lat=float(coords[1]), lng=float(coords[0])),
        component_scores=FSIComponentScores(
            sst_score=float(cs["sst_score"]),
            chl_a_score=float(cs["chl_a_score"]),
            depth_score=float(cs["depth_score"]),
            lunar_score=float(cs["lunar_score"]),
            ndvi_score=float(cs["ndvi_score"]),
            season_score=float(cs["season_score"]),
        ),
        calculated_at=datetime.fromisoformat(props["calculated_at"]),
        data_completeness=FSIDataCompleteness(
            available_sources=list(dc["available_sources"]),
            missing_sources=list(dc["missing_sources"]),
            is_complete=len(dc["missing_sources"]) == 0,
        ),
    )


# ===================================================================
# 6.3  FSI → Thai text  (Requirement 11.3)
# ===================================================================


def fsi_to_thai_text(result: FSIResult, area_name: str = "พื้นที่") -> str:
    """Format an :class:`FSIResult` as a Thai summary for LINE/SMS.

    Output format::

        📊 FSI {area}: {value} ({zone_thai})
        SST: {sst}°C | Chl-a: {chl_a} mg/m³

    The SST and Chl-a values shown are the *scores* (0–1), formatted as
    representative values for readability.  The zone name is in Thai with
    an emoji indicator.
    """
    zone_label = ZONE_THAI.get(result.zone.value, result.zone.value)
    fsi_str = f"{result.fsi_value:.2f}"

    cs = result.component_scores

    line1 = f"📊 FSI {area_name}: {fsi_str} ({zone_label})"
    line2 = (
        f"SST: {cs.sst_score:.2f} | "
        f"Chl-a: {cs.chl_a_score:.2f} | "
        f"Depth: {cs.depth_score:.2f} | "
        f"Lunar: {cs.lunar_score:.2f}"
    )

    return f"{line1}\n{line2}"


# ===================================================================
# 6.4  Safe JSON parsing  (Requirement 11.6)
# ===================================================================


def parse_fsi_json(raw: str) -> Union[FSIResult, FSIParseError]:
    """Parse a JSON string into an :class:`FSIResult`, never raising.

    If the input is malformed JSON or missing required fields, returns an
    :class:`FSIParseError` with position and cause information.

    This function **never** raises an unhandled exception.
    """
    # Step 1: parse raw JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return FSIParseError(
            position=exc.pos,
            cause=f"Invalid JSON: {exc.msg}",
            raw_input=raw,
        )
    except Exception as exc:  # pragma: no cover — defensive
        return FSIParseError(
            position=None,
            cause=f"Unexpected error during JSON parsing: {exc}",
            raw_input=raw,
        )

    # Step 2: validate structure and convert to FSIResult
    try:
        return json_to_fsi(data)
    except KeyError as exc:
        return FSIParseError(
            position=None,
            cause=f"Missing required field: {exc}",
            raw_input=raw,
        )
    except (ValueError, TypeError) as exc:
        return FSIParseError(
            position=None,
            cause=f"Invalid field value: {exc}",
            raw_input=raw,
        )
    except Exception as exc:  # pragma: no cover — defensive
        return FSIParseError(
            position=None,
            cause=f"Unexpected error during FSI conversion: {exc}",
            raw_input=raw,
        )
