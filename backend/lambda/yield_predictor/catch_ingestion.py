"""
Yield Predictor — Catch Report Ingestion

Receives actual catch data from fishermen, validates it, and stores it in
the ``catch_reports`` table.  This data feeds the periodic model-retraining
pipeline so the yield predictor improves over time.

Requirements: 4.5
"""

from __future__ import annotations

import importlib as _il
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class SpeciesCatch:
    """A single species entry within a catch report."""

    species_name: str   # Thai name, e.g. "กุ้ง"
    weight_kg: float    # kilograms caught


@dataclass
class CatchReport:
    """A validated catch report ready for storage."""

    id: str
    user_id: str
    area_id: str
    species_catch: List[SpeciesCatch]
    total_kg: float
    catch_date: date
    reported_at: datetime


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class CatchIngestionError(Exception):
    """Raised when catch report data is invalid."""


def validate_catch_data(data: Dict[str, Any]) -> None:
    """Validate raw catch report data.

    Raises :class:`CatchIngestionError` if required fields are missing or
    values are out of range.
    """
    required_fields = ["user_id", "area_id", "species_catch", "catch_date"]
    for f in required_fields:
        if f not in data or data[f] is None:
            raise CatchIngestionError(f"Missing required field: {f}")

    if not isinstance(data["species_catch"], list) or len(data["species_catch"]) == 0:
        raise CatchIngestionError(
            "species_catch must be a non-empty list"
        )

    for i, entry in enumerate(data["species_catch"]):
        if not isinstance(entry, dict):
            raise CatchIngestionError(
                f"species_catch[{i}] must be a dict"
            )
        if "species_name" not in entry or not entry["species_name"]:
            raise CatchIngestionError(
                f"species_catch[{i}] missing species_name"
            )
        weight = entry.get("weight_kg")
        if weight is None:
            raise CatchIngestionError(
                f"species_catch[{i}] missing weight_kg"
            )
        if not isinstance(weight, (int, float)) or weight < 0:
            raise CatchIngestionError(
                f"species_catch[{i}] weight_kg must be a non-negative number"
            )


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_catch_report(data: Dict[str, Any]) -> CatchReport:
    """Parse and validate raw data into a :class:`CatchReport`.

    Parameters
    ----------
    data : dict
        Raw catch report payload.  Expected keys:

        - ``user_id`` (str)
        - ``area_id`` (str)
        - ``species_catch`` (list of dicts with ``species_name`` and ``weight_kg``)
        - ``catch_date`` (str, ISO format ``YYYY-MM-DD``)

    Returns
    -------
    CatchReport
        Validated and structured catch report.

    Raises
    ------
    CatchIngestionError
        If validation fails.
    """
    validate_catch_data(data)

    species_catch = [
        SpeciesCatch(
            species_name=entry["species_name"],
            weight_kg=float(entry["weight_kg"]),
        )
        for entry in data["species_catch"]
    ]

    total_kg = sum(sc.weight_kg for sc in species_catch)

    # Parse catch_date
    raw_date = data["catch_date"]
    if isinstance(raw_date, date) and not isinstance(raw_date, datetime):
        catch_date = raw_date
    elif isinstance(raw_date, str):
        try:
            catch_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise CatchIngestionError(
                f"Invalid catch_date format: {raw_date!r} — expected YYYY-MM-DD"
            ) from exc
    else:
        raise CatchIngestionError(
            f"catch_date must be a string or date, got {type(raw_date).__name__}"
        )

    return CatchReport(
        id=str(uuid.uuid4()),
        user_id=data["user_id"],
        area_id=data["area_id"],
        species_catch=species_catch,
        total_kg=total_kg,
        catch_date=catch_date,
        reported_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def catch_report_to_row(report: CatchReport) -> Dict[str, Any]:
    """Convert a :class:`CatchReport` to a dict suitable for Supabase insert.

    The ``species_catch`` field is serialised as a JSON-compatible list of
    dicts for storage in a ``jsonb`` column.
    """
    return {
        "id": report.id,
        "user_id": report.user_id,
        "area_id": report.area_id,
        "species_catch": [
            {
                "species_name": sc.species_name,
                "weight_kg": sc.weight_kg,
            }
            for sc in report.species_catch
        ],
        "total_kg": report.total_kg,
        "catch_date": report.catch_date.isoformat(),
        "reported_at": report.reported_at.isoformat(),
    }


def prepare_retraining_data(
    reports: List[CatchReport],
) -> List[Dict[str, Any]]:
    """Prepare catch reports for model retraining.

    Transforms a list of catch reports into a flat list of training
    records, one per species per report, suitable for feeding into the
    SageMaker training pipeline.
    """
    records: List[Dict[str, Any]] = []
    for report in reports:
        for sc in report.species_catch:
            records.append(
                {
                    "area_id": report.area_id,
                    "catch_date": report.catch_date.isoformat(),
                    "species_name": sc.species_name,
                    "weight_kg": sc.weight_kg,
                    "total_kg": report.total_kg,
                }
            )
    return records


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """AWS Lambda entry point for catch report ingestion.

    Expects the event body to contain catch report data.  Returns a
    success response with the stored report ID, or an error response.
    """
    try:
        report = parse_catch_report(event)
        row = catch_report_to_row(report)

        # In production, store via Supabase client:
        # from lambda.shared.supabase_client import get_supabase_client
        # client = get_supabase_client()
        # client.table("catch_reports").insert(row).execute()

        logger.info(
            "Catch report %s ingested: user=%s area=%s total=%.1f kg",
            report.id,
            report.user_id,
            report.area_id,
            report.total_kg,
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Catch report ingested successfully",
                "report_id": report.id,
                "total_kg": report.total_kg,
            },
        }

    except CatchIngestionError as exc:
        logger.warning("Catch ingestion validation error: %s", exc)
        return {
            "statusCode": 400,
            "body": {"error": str(exc)},
        }
    except Exception as exc:
        logger.exception("Unexpected error during catch ingestion")
        return {
            "statusCode": 500,
            "body": {"error": "Internal server error"},
        }
