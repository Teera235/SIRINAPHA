"""
Seedling Tracker — survival rate and growth monitoring via NDVI.

Tracks planted seedling survival and growth by comparing actual NDVI
changes over time against expected growth curves. Uses NDVI as a proxy
for canopy development and seedling establishment.

Requirements: 5.5
"""

from __future__ import annotations

import importlib as _il
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

_models = _il.import_module("lambda.shared.models")

NDVITimeSeries = _models.NDVITimeSeries

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Expected NDVI growth curve parameters (logistic growth model)
# Mangrove seedlings typically take 3–5 years to establish canopy.
# The logistic curve models NDVI from planting baseline to mature canopy.
GROWTH_CURVE_NDVI_MIN = 0.10   # NDVI at planting (bare soil + seedlings)
GROWTH_CURVE_NDVI_MAX = 0.65   # NDVI at maturity (~5 years)
GROWTH_CURVE_MIDPOINT_DAYS = 730  # ~2 years to reach midpoint
GROWTH_CURVE_STEEPNESS = 0.005    # logistic steepness parameter


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class GrowthAssessment:
    """Assessment of seedling growth at a specific point in time."""

    days_since_planting: int
    actual_ndvi: float
    expected_ndvi: float
    growth_ratio: float       # actual / expected (1.0 = on track)
    status: str               # "ahead", "on_track", "behind", "failing"


@dataclass
class SeedlingReport:
    """Overall seedling tracking report for a restoration site."""

    site_id: str
    planting_date: datetime
    latest_assessment: Optional[GrowthAssessment]
    assessments: List[GrowthAssessment]
    estimated_survival_rate: float  # 0.0–1.0
    overall_status: str             # "excellent", "good", "concerning", "critical"


# ---------------------------------------------------------------------------
# Expected Growth Curve
# ---------------------------------------------------------------------------


def expected_ndvi_at_day(days_since_planting: int) -> float:
    """Compute expected NDVI at a given number of days after planting.

    Uses a logistic growth model:
        NDVI(t) = NDVI_min + (NDVI_max - NDVI_min) / (1 + exp(-k*(t - t0)))

    where:
        t  = days since planting
        t0 = midpoint (days to reach halfway between min and max)
        k  = steepness

    Parameters
    ----------
    days_since_planting:
        Number of days since seedlings were planted. Must be ≥ 0.

    Returns
    -------
    float
        Expected NDVI value, in [NDVI_MIN, NDVI_MAX].
    """
    if days_since_planting < 0:
        return GROWTH_CURVE_NDVI_MIN

    exponent = -GROWTH_CURVE_STEEPNESS * (days_since_planting - GROWTH_CURVE_MIDPOINT_DAYS)
    # Clamp exponent to avoid overflow
    exponent = max(-500.0, min(500.0, exponent))

    ndvi = GROWTH_CURVE_NDVI_MIN + (
        (GROWTH_CURVE_NDVI_MAX - GROWTH_CURVE_NDVI_MIN)
        / (1.0 + math.exp(exponent))
    )
    return round(ndvi, 4)


# ---------------------------------------------------------------------------
# Growth Assessment
# ---------------------------------------------------------------------------


def assess_growth(
    days_since_planting: int,
    actual_ndvi: float,
) -> GrowthAssessment:
    """Compare actual NDVI against the expected growth curve.

    Parameters
    ----------
    days_since_planting:
        Days elapsed since planting.
    actual_ndvi:
        Observed NDVI value at this time point.

    Returns
    -------
    GrowthAssessment
        Comparison of actual vs expected growth.
    """
    expected = expected_ndvi_at_day(days_since_planting)

    if expected > 0:
        ratio = actual_ndvi / expected
    else:
        ratio = 1.0 if actual_ndvi >= 0 else 0.0

    # Classify growth status
    if ratio >= 1.15:
        status = "ahead"
    elif ratio >= 0.80:
        status = "on_track"
    elif ratio >= 0.50:
        status = "behind"
    else:
        status = "failing"

    return GrowthAssessment(
        days_since_planting=days_since_planting,
        actual_ndvi=round(actual_ndvi, 4),
        expected_ndvi=round(expected, 4),
        growth_ratio=round(ratio, 4),
        status=status,
    )


# ---------------------------------------------------------------------------
# Survival Rate Estimation from NDVI
# ---------------------------------------------------------------------------


def estimate_survival_from_ndvi(
    ndvi_series: NDVITimeSeries,
    planting_date: datetime,
) -> float:
    """Estimate seedling survival rate from NDVI time-series.

    Compares the latest NDVI against the expected value at the same
    time point. A ratio near 1.0 suggests most seedlings survived;
    a low ratio suggests significant mortality.

    Parameters
    ----------
    ndvi_series:
        Observed NDVI time-series after planting.
    planting_date:
        Date when seedlings were planted.

    Returns
    -------
    float
        Estimated survival rate in [0.0, 1.0].
    """
    if not ndvi_series.values or not ndvi_series.timestamps:
        return 0.0

    latest_ts = ndvi_series.timestamps[-1]
    latest_ndvi = ndvi_series.values[-1]

    days = (latest_ts - planting_date).days
    if days < 0:
        return 0.0

    expected = expected_ndvi_at_day(days)

    if expected <= 0:
        return min(1.0, max(0.0, latest_ndvi))

    # Survival rate is approximated by the ratio of actual to expected NDVI
    # clamped to [0, 1]
    survival = latest_ndvi / expected
    return round(max(0.0, min(1.0, survival)), 4)


# ---------------------------------------------------------------------------
# Full Seedling Tracking Report
# ---------------------------------------------------------------------------


def track_seedlings(
    site_id: str,
    planting_date: datetime,
    ndvi_series: NDVITimeSeries,
) -> SeedlingReport:
    """Generate a comprehensive seedling tracking report.

    Compares each NDVI observation against the expected growth curve
    and produces an overall assessment.

    Parameters
    ----------
    site_id:
        Restoration site identifier.
    planting_date:
        Date when seedlings were planted.
    ndvi_series:
        Observed NDVI time-series after planting.

    Returns
    -------
    SeedlingReport
        Full tracking report with assessments and survival estimate.
    """
    assessments: List[GrowthAssessment] = []

    for ts, ndvi_val in zip(ndvi_series.timestamps, ndvi_series.values):
        days = (ts - planting_date).days
        if days < 0:
            continue
        assessment = assess_growth(days, ndvi_val)
        assessments.append(assessment)

    # Estimate survival from the full series
    survival = estimate_survival_from_ndvi(ndvi_series, planting_date)

    # Determine overall status from latest assessment
    latest = assessments[-1] if assessments else None

    if latest is None:
        overall_status = "critical"
    elif latest.status == "ahead":
        overall_status = "excellent"
    elif latest.status == "on_track":
        overall_status = "good"
    elif latest.status == "behind":
        overall_status = "concerning"
    else:
        overall_status = "critical"

    report = SeedlingReport(
        site_id=site_id,
        planting_date=planting_date,
        latest_assessment=latest,
        assessments=assessments,
        estimated_survival_rate=survival,
        overall_status=overall_status,
    )

    logger.info(
        "Seedling tracking for site %s: survival=%.1f%%, status=%s, "
        "%d assessments",
        site_id,
        survival * 100,
        overall_status,
        len(assessments),
    )

    return report
