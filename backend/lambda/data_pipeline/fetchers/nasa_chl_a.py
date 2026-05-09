"""
NASA MODIS Chlorophyll-a Data Fetcher via earthaccess.

Fetches daily Chlorophyll-a concentration data from NASA MODIS Aqua L3
using the ``earthaccess`` library to search and download granules.
Supports bounding box filtering for Mahachai and Ranong target regions.

Requirements: 1.2, 1.6, 1.9
"""

from __future__ import annotations

import importlib as _il
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

_config = _il.import_module("lambda.shared.config")
TARGET_REGIONS = _config.TARGET_REGIONS
NASA_MODIS_COLLECTION = _config.NASA_MODIS_COLLECTION


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class ChlADataPoint:
    """A single Chlorophyll-a observation with coordinates and timestamp."""

    latitude: float
    longitude: float
    chl_a_mg_m3: float
    data_timestamp: datetime


@dataclass
class FetchResult:
    """Outcome of a data fetch operation."""

    source: str
    timestamp: datetime
    status: str  # "success" | "failed" | "partial"
    data: List[ChlADataPoint] = field(default_factory=list)
    error: Optional[str] = None
    attempts: int = 1
    region: str = ""


# ---------------------------------------------------------------------------
# earthaccess search
# ---------------------------------------------------------------------------


def search_modis_granules(
    bbox: Dict[str, float],
    target_date: datetime,
    collection: str = NASA_MODIS_COLLECTION,
) -> List[Any]:
    """Search for MODIS Aqua L3 Chl-a granules using earthaccess.

    Parameters
    ----------
    bbox:
        Dictionary with keys ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    target_date:
        Date to search granules for.
    collection:
        NASA CMR collection short name.

    Returns
    -------
    list
        List of earthaccess granule results.
    """
    import earthaccess

    # Authenticate (uses .netrc or environment variables)
    earthaccess.login(strategy="environment")

    date_start = target_date.strftime("%Y-%m-%d")
    date_end = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

    results = earthaccess.search_data(
        short_name=collection,
        bounding_box=(
            bbox["lon_min"],
            bbox["lat_min"],
            bbox["lon_max"],
            bbox["lat_max"],
        ),
        temporal=(date_start, date_end),
    )

    logger.info(
        "Found %d MODIS Chl-a granules for date=%s bbox=%s",
        len(results),
        date_start,
        bbox,
    )
    return results


def download_granules(
    granules: List[Any],
    output_dir: Optional[str] = None,
) -> List[str]:
    """Download granules to a local directory using earthaccess.

    Parameters
    ----------
    granules:
        List of earthaccess granule results from ``search_modis_granules``.
    output_dir:
        Directory to download files into. Uses a temp directory if not given.

    Returns
    -------
    list[str]
        Paths to downloaded files.
    """
    import earthaccess

    if not granules:
        return []

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="modis_chl_a_")

    downloaded = earthaccess.download(granules, output_dir)
    paths = [str(p) for p in downloaded]
    logger.info("Downloaded %d granule files to %s", len(paths), output_dir)
    return paths


# ---------------------------------------------------------------------------
# HDF/NetCDF parsing
# ---------------------------------------------------------------------------


def parse_chl_a_file(
    file_path: str,
    bbox: Dict[str, float],
    data_timestamp: datetime,
) -> List[ChlADataPoint]:
    """Parse a MODIS Chl-a HDF/NetCDF file and extract data within a bounding box.

    Supports both HDF4 (using pyhdf or rasterio) and NetCDF (using xarray)
    formats. The function attempts xarray first as it handles both formats
    when the appropriate backend is available.

    Parameters
    ----------
    file_path:
        Path to the downloaded HDF or NetCDF file.
    bbox:
        Bounding box to filter data points.
    data_timestamp:
        Timestamp to assign to extracted data points.

    Returns
    -------
    list[ChlADataPoint]
        Extracted Chl-a data points within the bounding box.
    """
    import xarray as xr

    data_points: List[ChlADataPoint] = []

    try:
        ds = xr.open_dataset(file_path)
    except Exception:
        # Fallback: try with netcdf4 engine explicitly
        try:
            ds = xr.open_dataset(file_path, engine="netcdf4")
        except Exception as exc:
            logger.error("Cannot open file %s: %s", file_path, exc)
            raise ValueError(f"Unable to open data file: {exc}") from exc

    try:
        # MODIS L3 mapped products typically use 'chlor_a' as the variable name
        # and 'lat'/'lon' as coordinate names.
        chl_a_var = _find_chl_a_variable(ds)
        if chl_a_var is None:
            raise ValueError(
                f"No chlorophyll-a variable found in {file_path}. "
                f"Available variables: {list(ds.data_vars)}"
            )

        lat_name, lon_name = _find_coordinate_names(ds)

        lats = ds[lat_name].values
        lons = ds[lon_name].values
        chl_a_data = ds[chl_a_var].values

        # Handle multi-dimensional data (squeeze single-element time dims)
        while chl_a_data.ndim > 2:
            chl_a_data = chl_a_data[0]

        # Build masks for the bounding box
        lat_mask = (lats >= bbox["lat_min"]) & (lats <= bbox["lat_max"])
        lon_mask = (lons >= bbox["lon_min"]) & (lons <= bbox["lon_max"])

        lat_indices = np.where(lat_mask)[0]
        lon_indices = np.where(lon_mask)[0]

        if len(lat_indices) == 0 or len(lon_indices) == 0:
            logger.warning(
                "No data points within bounding box for file %s", file_path
            )
            return []

        for lat_idx in lat_indices:
            for lon_idx in lon_indices:
                value = float(chl_a_data[lat_idx, lon_idx])

                # Skip fill values and NaN
                if np.isnan(value) or value < 0:
                    continue

                data_points.append(
                    ChlADataPoint(
                        latitude=float(lats[lat_idx]),
                        longitude=float(lons[lon_idx]),
                        chl_a_mg_m3=value,
                        data_timestamp=data_timestamp,
                    )
                )
    finally:
        ds.close()

    logger.info(
        "Parsed %d Chl-a data points from %s", len(data_points), file_path
    )
    return data_points


def _find_chl_a_variable(ds: Any) -> Optional[str]:
    """Locate the chlorophyll-a variable in a dataset.

    Checks common variable names used in MODIS L3 products.
    """
    candidates = ["chlor_a", "Chlorophyll_a", "chl_a", "CHL", "chlorophyll"]
    for name in candidates:
        if name in ds.data_vars:
            return name
    # Fallback: look for any variable with 'chlor' or 'chl' in the name
    for var_name in ds.data_vars:
        if "chlor" in var_name.lower() or "chl" in var_name.lower():
            return var_name
    return None


def _find_coordinate_names(ds: Any) -> tuple:
    """Locate latitude and longitude coordinate names in a dataset.

    Returns
    -------
    tuple[str, str]
        (lat_name, lon_name)
    """
    lat_candidates = ["lat", "latitude", "Latitude", "LAT"]
    lon_candidates = ["lon", "longitude", "Longitude", "LON"]

    lat_name = None
    lon_name = None

    for name in lat_candidates:
        if name in ds.coords or name in ds.dims:
            lat_name = name
            break

    for name in lon_candidates:
        if name in ds.coords or name in ds.dims:
            lon_name = name
            break

    if lat_name is None or lon_name is None:
        raise ValueError(
            f"Cannot find lat/lon coordinates. "
            f"Available coords: {list(ds.coords)}, dims: {list(ds.dims)}"
        )

    return lat_name, lon_name


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------


def validate_chl_a_data(data_points: List[ChlADataPoint]) -> List[ChlADataPoint]:
    """Validate Chl-a data points, removing invalid entries.

    Valid Chl-a concentrations are non-negative finite numbers.
    Typical ocean values range from ~0.01 to ~100 mg/m³, but we accept
    any non-negative finite value and let downstream consumers apply
    stricter filtering.

    Parameters
    ----------
    data_points:
        Raw parsed data points.

    Returns
    -------
    list[ChlADataPoint]
        Data points that pass validation.
    """
    valid = []
    for dp in data_points:
        if np.isnan(dp.chl_a_mg_m3) or np.isinf(dp.chl_a_mg_m3):
            logger.warning(
                "Skipping invalid Chl-a value %s at (%s, %s)",
                dp.chl_a_mg_m3,
                dp.latitude,
                dp.longitude,
            )
            continue
        if dp.chl_a_mg_m3 < 0:
            logger.warning(
                "Skipping negative Chl-a value %s at (%s, %s)",
                dp.chl_a_mg_m3,
                dp.latitude,
                dp.longitude,
            )
            continue
        valid.append(dp)
    return valid


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------


def store_raw_chl_a_data(
    data_points: List[ChlADataPoint],
    region: str,
    bbox: Dict[str, float],
    fetched_at: Optional[datetime] = None,
) -> None:
    """Persist raw Chl-a data into the ``satellite_raw_data`` table.

    Each call inserts one row per region fetch, storing all data points as a
    JSONB array in the ``data`` column.

    Parameters
    ----------
    data_points:
        Validated Chl-a observations.
    region:
        Region name (e.g. ``"mahachai"`` or ``"ranong"``).
    bbox:
        Bounding box used for the fetch.
    fetched_at:
        Override for the ``fetched_at`` timestamp (defaults to ``now()``).
    """
    if not data_points:
        logger.info("No Chl-a data points to store for region %s", region)
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
        "source": "nasa_modis_chl_a",
        "fetched_at": fetched_at.isoformat(),
        "data_timestamp": data_timestamp.isoformat(),
        "data": {
            "region": region,
            "bbox": bbox,
            "points": [
                {
                    "latitude": dp.latitude,
                    "longitude": dp.longitude,
                    "chl_a_mg_m3": dp.chl_a_mg_m3,
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
        "Stored %d Chl-a data points for region %s (fetched_at=%s)",
        len(data_points),
        region,
        fetched_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------


def fetch_chl_a_for_region(
    region: str,
    bbox: Dict[str, float],
    target_date: Optional[datetime] = None,
) -> FetchResult:
    """Fetch Chl-a data for a single region from NASA MODIS via earthaccess.

    Parameters
    ----------
    region:
        Human-readable region name (e.g. ``"mahachai"``).
    bbox:
        Bounding box with ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    target_date:
        Date to fetch Chl-a for. Defaults to today (UTC).

    Returns
    -------
    FetchResult
        Contains parsed data points on success, or an error message on failure.
    """
    now = datetime.now(timezone.utc)
    if target_date is None:
        target_date = now

    logger.info(
        "Fetching Chl-a for region=%s date=%s",
        region,
        target_date.strftime("%Y-%m-%d"),
    )

    # Step 1: Search for granules
    try:
        granules = search_modis_granules(bbox, target_date)
    except Exception as exc:
        logger.error("Granule search failed for region %s: %s", region, exc)
        return FetchResult(
            source="nasa_modis_chl_a",
            timestamp=now,
            status="failed",
            error=f"Granule search failed: {exc}",
            region=region,
        )

    if not granules:
        return FetchResult(
            source="nasa_modis_chl_a",
            timestamp=now,
            status="partial",
            data=[],
            error="No MODIS Chl-a granules found for the target date",
            region=region,
        )

    # Step 2: Download granules
    try:
        file_paths = download_granules(granules)
    except Exception as exc:
        logger.error("Granule download failed for region %s: %s", region, exc)
        return FetchResult(
            source="nasa_modis_chl_a",
            timestamp=now,
            status="failed",
            error=f"Granule download failed: {exc}",
            region=region,
        )

    if not file_paths:
        return FetchResult(
            source="nasa_modis_chl_a",
            timestamp=now,
            status="partial",
            data=[],
            error="No files downloaded from earthaccess",
            region=region,
        )

    # Step 3: Parse downloaded files and extract Chl-a values
    all_data_points: List[ChlADataPoint] = []
    parse_errors: List[str] = []

    for fp in file_paths:
        try:
            points = parse_chl_a_file(fp, bbox, target_date)
            all_data_points.extend(points)
        except Exception as exc:
            logger.error("Failed to parse file %s: %s", fp, exc)
            parse_errors.append(f"{fp}: {exc}")

    # Step 4: Validate data
    valid_points = validate_chl_a_data(all_data_points)

    if not valid_points:
        error_msg = "No valid Chl-a data points after parsing and validation"
        if parse_errors:
            error_msg += f"; parse errors: {'; '.join(parse_errors)}"
        return FetchResult(
            source="nasa_modis_chl_a",
            timestamp=now,
            status="partial",
            data=[],
            error=error_msg,
            region=region,
        )

    # Step 5: Store in database
    try:
        store_raw_chl_a_data(valid_points, region, bbox, fetched_at=now)
    except Exception as exc:
        logger.error("Failed to store Chl-a data for region %s: %s", region, exc)
        return FetchResult(
            source="nasa_modis_chl_a",
            timestamp=now,
            status="failed",
            data=valid_points,
            error=f"Database storage failed: {exc}",
            region=region,
        )

    return FetchResult(
        source="nasa_modis_chl_a",
        timestamp=now,
        status="success",
        data=valid_points,
        region=region,
    )


def fetch_chl_a_all_regions(
    target_date: Optional[datetime] = None,
) -> List[FetchResult]:
    """Fetch Chl-a data for all configured target regions.

    Iterates over ``TARGET_REGIONS`` from the shared config and fetches Chl-a
    data for each bounding box.

    Parameters
    ----------
    target_date:
        Date to fetch Chl-a for. Defaults to today (UTC).

    Returns
    -------
    list[FetchResult]
        One result per region.
    """
    results: List[FetchResult] = []
    for region_name, bbox in TARGET_REGIONS.items():
        result = fetch_chl_a_for_region(region_name, bbox, target_date)
        results.append(result)
    return results
