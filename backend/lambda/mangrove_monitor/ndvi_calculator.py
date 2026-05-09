"""
NDVI Calculator — Mangrove health monitoring via Sentinel-2 imagery.

Calculates the Normalized Difference Vegetation Index (NDVI) from
Sentinel-2 Band 4 (Red) and Band 8 (NIR) reflectance values, classifies
mangrove health into four levels, and stores time-series records in the
``ndvi_records`` table.

Requirements: 2.1, 2.2, 2.3
"""

from __future__ import annotations

import importlib as _il
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_config = _il.import_module("lambda.shared.config")
_models = _il.import_module("lambda.shared.models")

HealthLevel = _models.HealthLevel
NDVI_THRESHOLDS = _models.NDVI_THRESHOLDS

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Sentinel2Input:
    """Raw Sentinel-2 band values for a single pixel."""

    latitude: float
    longitude: float
    band_4_red: float  # Red reflectance (≥ 0)
    band_8_nir: float  # NIR reflectance (≥ 0)
    observed_at: datetime
    sentinel2_scene_id: str
    area_id: Optional[str] = None


@dataclass
class NDVIRecord:
    """Computed NDVI result ready for storage."""

    area_id: Optional[str]
    latitude: float
    longitude: float
    ndvi_value: float  # -1.0 to 1.0
    health_level: str  # healthy | moderate | degraded | critical
    sentinel2_scene_id: str
    observed_at: datetime


# ---------------------------------------------------------------------------
# Core NDVI calculation (Requirement 2.1)
# ---------------------------------------------------------------------------


def calculate_ndvi(nir: float, red: float) -> float:
    """Calculate NDVI from NIR (Band 8) and Red (Band 4) reflectance values.

    Formula: NDVI = (NIR - Red) / (NIR + Red)

    Parameters
    ----------
    nir:
        Near-infrared reflectance value (Band 8). Must be ≥ 0.
    red:
        Red reflectance value (Band 4). Must be ≥ 0.

    Returns
    -------
    float
        NDVI value in the range [-1.0, 1.0].
        Returns 0.0 when both NIR and Red are zero (division-by-zero case).
    """
    denominator = nir + red
    if denominator == 0.0:
        return 0.0
    return (nir - red) / denominator


# ---------------------------------------------------------------------------
# Health classification (Requirement 2.2)
# ---------------------------------------------------------------------------


def classify_health(ndvi: float) -> str:
    """Classify mangrove health based on NDVI value.

    Thresholds (from design document):
    - healthy:  NDVI > 0.6
    - moderate: NDVI 0.4–0.6 (inclusive on both ends)
    - degraded: NDVI 0.2–0.4 (inclusive at 0.2, exclusive at 0.4)
    - critical: NDVI < 0.2

    Parameters
    ----------
    ndvi:
        NDVI value, typically in [-1.0, 1.0].

    Returns
    -------
    str
        One of ``"healthy"``, ``"moderate"``, ``"degraded"``, ``"critical"``.
    """
    if ndvi > 0.6:
        return HealthLevel.HEALTHY.value
    if ndvi >= 0.4:
        return HealthLevel.MODERATE.value
    if ndvi >= 0.2:
        return HealthLevel.DEGRADED.value
    return HealthLevel.CRITICAL.value


# ---------------------------------------------------------------------------
# Batch processing (Requirement 2.1 + 2.2)
# ---------------------------------------------------------------------------


def process_sentinel2_data(data_points: List[Sentinel2Input]) -> List[NDVIRecord]:
    """Process raw Sentinel-2 band data into NDVI records.

    For each data point, calculates NDVI and classifies health level.
    Skips data points with invalid (negative) band values.

    Parameters
    ----------
    data_points:
        Raw Sentinel-2 observations with Band 4 and Band 8 values.

    Returns
    -------
    list[NDVIRecord]
        Computed NDVI records with health classifications.
    """
    records: List[NDVIRecord] = []

    for dp in data_points:
        # Skip invalid reflectance values
        if dp.band_4_red < 0 or dp.band_8_nir < 0:
            logger.warning(
                "Skipping data point with negative band values "
                "(B04=%s, B08=%s) at (%s, %s)",
                dp.band_4_red,
                dp.band_8_nir,
                dp.latitude,
                dp.longitude,
            )
            continue

        ndvi = calculate_ndvi(dp.band_8_nir, dp.band_4_red)
        health = classify_health(ndvi)

        records.append(
            NDVIRecord(
                area_id=dp.area_id,
                latitude=dp.latitude,
                longitude=dp.longitude,
                ndvi_value=ndvi,
                health_level=health,
                sentinel2_scene_id=dp.sentinel2_scene_id,
                observed_at=dp.observed_at,
            )
        )

    logger.info(
        "Processed %d/%d Sentinel-2 data points into NDVI records",
        len(records),
        len(data_points),
    )
    return records


# ---------------------------------------------------------------------------
# Database storage (Requirement 2.3)
# ---------------------------------------------------------------------------


def store_ndvi_records(records: List[NDVIRecord]) -> int:
    """Store NDVI records in the ``ndvi_records`` table as time-series data.

    Each record is inserted as a row with a PostGIS Point geometry for
    geospatial querying.

    Parameters
    ----------
    records:
        Computed NDVI records to persist.

    Returns
    -------
    int
        Number of records successfully stored.
    """
    if not records:
        logger.info("No NDVI records to store")
        return 0

    rows = []
    for rec in records:
        location_wkt = f"SRID=4326;POINT({rec.longitude} {rec.latitude})"
        rows.append(
            {
                "area_id": rec.area_id,
                "ndvi_value": rec.ndvi_value,
                "health_level": rec.health_level,
                "sentinel2_scene_id": rec.sentinel2_scene_id,
                "observed_at": rec.observed_at.isoformat(),
                "location": location_wkt,
            }
        )

    client = get_supabase_client()
    client.table("ndvi_records").insert(rows).execute()

    logger.info("Stored %d NDVI records in ndvi_records table", len(rows))
    return len(rows)
