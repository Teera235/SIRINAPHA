"""
Change Detector — Mangrove NDVI change detection and alert generation.

Compares current NDVI values with a 6-month rolling average to detect
significant drops in mangrove health. Generates "warning" alerts when
NDVI drops >20% and "critical" alerts when NDVI drops >40%.

Requirements: 2.4, 2.5, 2.6
"""

from __future__ import annotations

import importlib as _il
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_models = _il.import_module("lambda.shared.models")

AlertLevel = _models.AlertLevel
MangroveAlert = _models.MangroveAlert

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alert thresholds (from design document)
# ---------------------------------------------------------------------------

WARNING_THRESHOLD = 20.0   # NDVI drop > 20% → warning (เตือนภัย)
CRITICAL_THRESHOLD = 40.0  # NDVI drop > 40% → critical (วิกฤต)


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()


# ---------------------------------------------------------------------------
# Core change detection functions
# ---------------------------------------------------------------------------


def calculate_change_percent(current_ndvi: float, avg_6month: float) -> float:
    """Calculate the percentage change of current NDVI relative to the
    6-month rolling average.

    A negative return value indicates a drop (decline) in NDVI.
    A positive return value indicates an increase.

    Parameters
    ----------
    current_ndvi:
        The most recent NDVI value.
    avg_6month:
        The 6-month rolling average NDVI value.

    Returns
    -------
    float
        Percentage change. For example, -25.0 means a 25% drop.
        Returns 0.0 when the 6-month average is zero (avoids division
        by zero).
    """
    if avg_6month == 0.0:
        return 0.0
    return ((current_ndvi - avg_6month) / abs(avg_6month)) * 100.0


def classify_alert_level(change_percent: float) -> Optional[str]:
    """Classify the alert level based on the percentage drop in NDVI.

    Thresholds (from design document):
    - Drop > 40% → "critical" (วิกฤต)
    - Drop > 20% → "warning" (เตือนภัย)
    - Drop ≤ 20% → no alert (None)

    The ``change_percent`` is expected to be negative for drops.
    We compare the absolute magnitude of the drop against thresholds.

    Parameters
    ----------
    change_percent:
        Percentage change from ``calculate_change_percent``.

    Returns
    -------
    str or None
        ``"critical"``, ``"warning"``, or ``None``.
    """
    drop = -change_percent  # convert negative change to positive drop magnitude
    if drop > CRITICAL_THRESHOLD:
        return AlertLevel.CRITICAL.value
    if drop > WARNING_THRESHOLD:
        return AlertLevel.WARNING.value
    return None


def compute_6month_average(ndvi_history: List[float]) -> Optional[float]:
    """Compute the average NDVI from a list of historical values.

    Parameters
    ----------
    ndvi_history:
        List of NDVI values representing the 6-month history.

    Returns
    -------
    float or None
        The arithmetic mean, or ``None`` if the history is empty.
    """
    if not ndvi_history:
        return None
    return sum(ndvi_history) / len(ndvi_history)


def detect_changes(
    area_id: str,
    current_ndvi: float,
    ndvi_history: List[float],
) -> Optional[Dict[str, Any]]:
    """Compare current NDVI with the 6-month rolling average and determine
    whether an alert should be generated.

    Parameters
    ----------
    area_id:
        Identifier for the mangrove monitoring area.
    current_ndvi:
        The most recent NDVI value for the area.
    ndvi_history:
        List of NDVI values from the past 6 months.

    Returns
    -------
    dict or None
        A dictionary with change detection results if an alert is warranted,
        or ``None`` if no significant change was detected.
        Keys: ``area_id``, ``current_ndvi``, ``avg_6month``,
        ``change_percent``, ``alert_level``.
    """
    avg_6month = compute_6month_average(ndvi_history)
    if avg_6month is None:
        logger.warning(
            "No NDVI history available for area %s; skipping change detection",
            area_id,
        )
        return None

    change_percent = calculate_change_percent(current_ndvi, avg_6month)
    alert_level = classify_alert_level(change_percent)

    if alert_level is None:
        logger.info(
            "Area %s: NDVI change %.1f%% (current=%.3f, avg=%.3f) — no alert",
            area_id,
            change_percent,
            current_ndvi,
            avg_6month,
        )
        return None

    logger.info(
        "Area %s: NDVI change %.1f%% (current=%.3f, avg=%.3f) — %s alert",
        area_id,
        change_percent,
        current_ndvi,
        avg_6month,
        alert_level,
    )

    return {
        "area_id": area_id,
        "current_ndvi": current_ndvi,
        "avg_6month": avg_6month,
        "change_percent": change_percent,
        "alert_level": alert_level,
    }


def generate_alert(
    area_id: str,
    current_ndvi: float,
    avg_6month: float,
    alert_level: str,
    geometry: Dict[str, Any],
) -> MangroveAlert:
    """Create a ``MangroveAlert`` dataclass instance.

    Parameters
    ----------
    area_id:
        Identifier for the mangrove monitoring area.
    current_ndvi:
        The most recent NDVI value.
    avg_6month:
        The 6-month rolling average NDVI.
    alert_level:
        ``"warning"`` or ``"critical"``.
    geometry:
        GeoJSON Polygon describing the affected area.

    Returns
    -------
    MangroveAlert
        A fully populated alert object ready for storage.
    """
    change_percent = calculate_change_percent(current_ndvi, avg_6month)

    return MangroveAlert(
        id=str(uuid.uuid4()),
        area_id=area_id,
        alert_level=AlertLevel(alert_level),
        ndvi_current=current_ndvi,
        ndvi_6month_avg=avg_6month,
        change_percent=change_percent,
        detected_at=datetime.now(timezone.utc),
        geometry=geometry,
    )


def store_alert(alert: MangroveAlert) -> str:
    """Persist a ``MangroveAlert`` to the ``mangrove_alerts`` table.

    Parameters
    ----------
    alert:
        The alert to store.

    Returns
    -------
    str
        The alert ID that was stored.
    """
    row = {
        "id": alert.id,
        "area_id": alert.area_id,
        "alert_level": (
            alert.alert_level.value
            if isinstance(alert.alert_level, AlertLevel)
            else alert.alert_level
        ),
        "ndvi_current": alert.ndvi_current,
        "ndvi_6month_avg": alert.ndvi_6month_avg,
        "change_percent": alert.change_percent,
        "detected_at": alert.detected_at.isoformat(),
        "geometry": alert.geometry,
        "is_resolved": False,
    }

    client = get_supabase_client()
    client.table("mangrove_alerts").insert(row).execute()

    logger.info(
        "Stored %s alert %s for area %s (NDVI drop %.1f%%)",
        alert.alert_level.value
        if isinstance(alert.alert_level, AlertLevel)
        else alert.alert_level,
        alert.id,
        alert.area_id,
        abs(alert.change_percent),
    )
    return alert.id
