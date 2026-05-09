"""
NOAA OISST SST Data Fetcher via ERDDAP API.

Fetches daily Sea Surface Temperature (SST) data from the NOAA OISST v2
dataset using the ERDDAP griddap JSON interface. Supports bounding box
filtering for Mahachai and Ranong target regions.

Requirements: 1.1, 1.6, 1.9
"""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

import importlib as _il

_config = _il.import_module("lambda.shared.config")
NOAA_ERDDAP_BASE_URL = _config.NOAA_ERDDAP_BASE_URL
NOAA_OISST_DATASET_ID = _config.NOAA_OISST_DATASET_ID
TARGET_REGIONS = _config.TARGET_REGIONS


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class SSTDataPoint:
    """A single SST observation with coordinates and timestamp."""

    latitude: float
    longitude: float
    sst_celsius: float
    data_timestamp: datetime


@dataclass
class FetchResult:
    """Outcome of a data fetch operation."""

    source: str
    timestamp: datetime
    status: str  # "success" | "failed" | "partial"
    data: List[SSTDataPoint] = field(default_factory=list)
    error: Optional[str] = None
    attempts: int = 1
    region: str = ""


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------

def build_erddap_url(
    date_str: str,
    bbox: Dict[str, float],
    base_url: str = NOAA_ERDDAP_BASE_URL,
    dataset_id: str = NOAA_OISST_DATASET_ID,
) -> str:
    """Build an ERDDAP griddap URL for SST data within a bounding box.

    Parameters
    ----------
    date_str:
        ISO-8601 date string, e.g. ``"2024-01-15T00:00:00Z"``.
    bbox:
        Dictionary with keys ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    base_url:
        ERDDAP server base URL.
    dataset_id:
        ERDDAP dataset identifier.

    Returns
    -------
    str
        Fully-qualified ERDDAP griddap request URL returning JSON.
    """
    # ERDDAP griddap constraint expression:
    #   sst[(time)][(lat_min):(lat_max)][(lon_min):(lon_max)]
    constraint = (
        f"sst[({date_str})]"
        f"[({bbox['lat_min']}):({bbox['lat_max']})]"
        f"[({bbox['lon_min']}):({bbox['lon_max']})]"
    )
    url = f"{base_url}/griddap/{dataset_id}.json?{urllib.parse.quote(constraint, safe='[]():,')}"
    return url


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_erddap_response(response_json: Dict[str, Any]) -> List[SSTDataPoint]:
    """Parse an ERDDAP griddap JSON response into ``SSTDataPoint`` objects.

    The ERDDAP JSON response has the structure::

        {
          "table": {
            "columnNames": ["time", "latitude", "longitude", "sst"],
            "columnTypes": [...],
            "rows": [
              ["2024-01-15T00:00:00Z", 13.5, 100.25, 28.3],
              ...
            ]
          }
        }

    Parameters
    ----------
    response_json:
        Parsed JSON body from the ERDDAP endpoint.

    Returns
    -------
    list[SSTDataPoint]
        Extracted SST data points. Points with ``NaN`` SST values are skipped.
    """
    table = response_json.get("table", {})
    column_names = table.get("columnNames", [])
    rows = table.get("rows", [])

    if not column_names or not rows:
        return []

    # Build a column-name → index mapping for resilience against column
    # order changes.
    col_idx = {name: idx for idx, name in enumerate(column_names)}

    required_cols = {"time", "latitude", "longitude", "sst"}
    if not required_cols.issubset(col_idx):
        missing = required_cols - set(col_idx)
        raise ValueError(f"ERDDAP response missing required columns: {missing}")

    time_idx = col_idx["time"]
    lat_idx = col_idx["latitude"]
    lon_idx = col_idx["longitude"]
    sst_idx = col_idx["sst"]

    data_points: List[SSTDataPoint] = []
    for row in rows:
        sst_val = row[sst_idx]
        # ERDDAP may return NaN for missing grid cells — skip them.
        if sst_val is None or (isinstance(sst_val, float) and sst_val != sst_val):
            continue

        try:
            ts = datetime.fromisoformat(row[time_idx].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning("Skipping row with unparseable timestamp: %s", row[time_idx])
            continue

        data_points.append(
            SSTDataPoint(
                latitude=float(row[lat_idx]),
                longitude=float(row[lon_idx]),
                sst_celsius=float(sst_val),
                data_timestamp=ts,
            )
        )

    return data_points


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------

def store_raw_sst_data(
    data_points: List[SSTDataPoint],
    region: str,
    bbox: Dict[str, float],
    fetched_at: Optional[datetime] = None,
) -> None:
    """Persist raw SST data into the ``satellite_raw_data`` table.

    Each call inserts one row per region fetch, storing all data points as a
    JSONB array in the ``data`` column.

    Parameters
    ----------
    data_points:
        Parsed SST observations.
    region:
        Region name (e.g. ``"mahachai"`` or ``"ranong"``).
    bbox:
        Bounding box used for the fetch.
    fetched_at:
        Override for the ``fetched_at`` timestamp (defaults to ``now()``).
    """
    if not data_points:
        logger.info("No SST data points to store for region %s", region)
        return

    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    # Use the earliest data_timestamp from the points as the canonical
    # data_timestamp for this raw record.
    data_timestamp = min(dp.data_timestamp for dp in data_points)

    # Build a WKT polygon from the bounding box for the coverage column.
    coverage_wkt = (
        f"SRID=4326;POLYGON(("
        f"{bbox['lon_min']} {bbox['lat_min']},"
        f"{bbox['lon_max']} {bbox['lat_min']},"
        f"{bbox['lon_max']} {bbox['lat_max']},"
        f"{bbox['lon_min']} {bbox['lat_max']},"
        f"{bbox['lon_min']} {bbox['lat_min']}"
        f"))"
    )

    record = {
        "source": "noaa_oisst",
        "fetched_at": fetched_at.isoformat(),
        "data_timestamp": data_timestamp.isoformat(),
        "data": {
            "region": region,
            "bbox": bbox,
            "points": [
                {
                    "latitude": dp.latitude,
                    "longitude": dp.longitude,
                    "sst_celsius": dp.sst_celsius,
                    "data_timestamp": dp.data_timestamp.isoformat(),
                }
                for dp in data_points
            ],
        },
        "status": "valid",
        "coverage": coverage_wkt,
    }

    client = get_supabase_client()
    client.table("satellite_raw_data").insert(record).execute()
    logger.info(
        "Stored %d SST data points for region %s (fetched_at=%s)",
        len(data_points),
        region,
        fetched_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT_SECONDS = 30


def fetch_sst_for_region(
    region: str,
    bbox: Dict[str, float],
    target_date: Optional[datetime] = None,
) -> FetchResult:
    """Fetch SST data for a single region from NOAA ERDDAP.

    Parameters
    ----------
    region:
        Human-readable region name (e.g. ``"mahachai"``).
    bbox:
        Bounding box with ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    target_date:
        Date to fetch SST for. Defaults to today (UTC).

    Returns
    -------
    FetchResult
        Contains parsed data points on success, or an error message on failure.
    """
    now = datetime.now(timezone.utc)
    if target_date is None:
        target_date = now

    date_str = target_date.strftime("%Y-%m-%dT00:00:00Z")
    url = build_erddap_url(date_str, bbox)

    logger.info("Fetching SST for region=%s date=%s url=%s", region, date_str, url)

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("HTTP request failed for region %s: %s", region, exc)
        return FetchResult(
            source="noaa_oisst",
            timestamp=now,
            status="failed",
            error=str(exc),
            region=region,
        )

    try:
        response_json = response.json()
    except ValueError as exc:
        logger.error("Failed to parse JSON response for region %s: %s", region, exc)
        return FetchResult(
            source="noaa_oisst",
            timestamp=now,
            status="failed",
            error=f"Invalid JSON response: {exc}",
            region=region,
        )

    try:
        data_points = parse_erddap_response(response_json)
    except ValueError as exc:
        logger.error("Failed to parse ERDDAP data for region %s: %s", region, exc)
        return FetchResult(
            source="noaa_oisst",
            timestamp=now,
            status="failed",
            error=str(exc),
            region=region,
        )

    if not data_points:
        return FetchResult(
            source="noaa_oisst",
            timestamp=now,
            status="partial",
            data=[],
            error="No valid SST data points in response",
            region=region,
        )

    # Persist to database
    try:
        store_raw_sst_data(data_points, region, bbox, fetched_at=now)
    except Exception as exc:
        logger.error("Failed to store SST data for region %s: %s", region, exc)
        return FetchResult(
            source="noaa_oisst",
            timestamp=now,
            status="failed",
            data=data_points,
            error=f"Database storage failed: {exc}",
            region=region,
        )

    return FetchResult(
        source="noaa_oisst",
        timestamp=now,
        status="success",
        data=data_points,
        region=region,
    )


def fetch_sst_all_regions(
    target_date: Optional[datetime] = None,
) -> List[FetchResult]:
    """Fetch SST data for all configured target regions.

    Iterates over ``TARGET_REGIONS`` from the shared config and fetches SST
    data for each bounding box.

    Parameters
    ----------
    target_date:
        Date to fetch SST for. Defaults to today (UTC).

    Returns
    -------
    list[FetchResult]
        One result per region.
    """
    results: List[FetchResult] = []
    for region_name, bbox in TARGET_REGIONS.items():
        result = fetch_sst_for_region(region_name, bbox, target_date)
        results.append(result)
    return results
