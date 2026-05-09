"""
GEBCO Bathymetry Data Loader.

Loads pre-downloaded GEBCO NetCDF bathymetry data as static reference data.
Provides depth queries at specific lat/lon coordinates and within bounding
boxes for the Mahachai and Ranong target regions.

Requirements: 1.4
"""

from __future__ import annotations

import importlib as _il
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

_config = _il.import_module("lambda.shared.config")
TARGET_REGIONS = _config.TARGET_REGIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEBCO_FILE_PATH = os.environ.get("GEBCO_FILE_PATH", "data/gebco_bathymetry.nc")

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class DepthPoint:
    """A single bathymetry depth observation with coordinates."""

    latitude: float
    longitude: float
    depth_meters: float  # positive = below sea level


# ---------------------------------------------------------------------------
# In-memory cache for static reference data
# ---------------------------------------------------------------------------

_cached_data: Optional[Dict] = None


def _load_gebco_dataset(file_path: str) -> Dict:
    """Load GEBCO NetCDF file and return lat, lon, and elevation arrays.

    Parameters
    ----------
    file_path:
        Path to the GEBCO NetCDF file.

    Returns
    -------
    dict
        Dictionary with keys ``lat``, ``lon``, ``elevation`` containing
        numpy arrays.

    Raises
    ------
    FileNotFoundError
        If the GEBCO file does not exist.
    ValueError
        If the file cannot be parsed or is missing required variables.
    """
    import xarray as xr

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"GEBCO bathymetry file not found: {file_path}. "
            "Download from https://download.gebco.net/ and set "
            "GEBCO_FILE_PATH environment variable."
        )

    try:
        ds = xr.open_dataset(file_path)
    except Exception as exc:
        raise ValueError(f"Unable to open GEBCO file: {exc}") from exc

    try:
        # GEBCO uses 'elevation' variable and 'lat'/'lon' coordinates
        elev_var = _find_elevation_variable(ds)
        if elev_var is None:
            raise ValueError(
                f"No elevation variable found in GEBCO file. "
                f"Available variables: {list(ds.data_vars)}"
            )

        lat_name, lon_name = _find_coordinate_names(ds)

        data = {
            "lat": ds[lat_name].values.copy(),
            "lon": ds[lon_name].values.copy(),
            "elevation": ds[elev_var].values.copy(),
        }
    finally:
        ds.close()

    logger.info(
        "Loaded GEBCO data: lat shape=%s, lon shape=%s, elevation shape=%s",
        data["lat"].shape,
        data["lon"].shape,
        data["elevation"].shape,
    )
    return data


def _find_elevation_variable(ds) -> Optional[str]:
    """Locate the elevation/depth variable in a GEBCO dataset."""
    candidates = ["elevation", "Elevation", "depth", "Depth", "z", "Z"]
    for name in candidates:
        if name in ds.data_vars:
            return name
    for var_name in ds.data_vars:
        if "elev" in var_name.lower() or "depth" in var_name.lower():
            return var_name
    return None


def _find_coordinate_names(ds) -> tuple:
    """Locate latitude and longitude coordinate names in a dataset.

    Returns
    -------
    tuple[str, str]
        (lat_name, lon_name)
    """
    lat_candidates = ["lat", "latitude", "Latitude", "LAT", "y"]
    lon_candidates = ["lon", "longitude", "Longitude", "LON", "x"]

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
# Public API
# ---------------------------------------------------------------------------


def load_gebco(file_path: Optional[str] = None, force_reload: bool = False) -> Dict:
    """Load GEBCO data into memory, using cache for subsequent calls.

    Since GEBCO bathymetry is static reference data, it is loaded once and
    cached in memory for the lifetime of the Lambda execution context.

    Parameters
    ----------
    file_path:
        Path to the GEBCO NetCDF file. Defaults to ``GEBCO_FILE_PATH``.
    force_reload:
        If ``True``, reload from disk even if cached.

    Returns
    -------
    dict
        Dictionary with ``lat``, ``lon``, ``elevation`` numpy arrays.
    """
    global _cached_data

    if _cached_data is not None and not force_reload:
        return _cached_data

    if file_path is None:
        file_path = GEBCO_FILE_PATH

    _cached_data = _load_gebco_dataset(file_path)
    return _cached_data


def clear_cache() -> None:
    """Clear the in-memory GEBCO data cache."""
    global _cached_data
    _cached_data = None


def get_depth_at_point(
    lat: float,
    lon: float,
    gebco_data: Optional[Dict] = None,
) -> float:
    """Query depth at a specific latitude/longitude coordinate.

    Uses nearest-neighbour interpolation to find the closest grid cell
    in the GEBCO dataset.

    Parameters
    ----------
    lat:
        Latitude in decimal degrees.
    lon:
        Longitude in decimal degrees.
    gebco_data:
        Pre-loaded GEBCO data dict. If ``None``, loads from cache/disk.

    Returns
    -------
    float
        Depth in meters (positive value = below sea level).
        GEBCO elevation is negative for ocean, so we negate it.
    """
    if gebco_data is None:
        gebco_data = load_gebco()

    lats = gebco_data["lat"]
    lons = gebco_data["lon"]
    elevation = gebco_data["elevation"]

    # Find nearest grid cell indices
    lat_idx = int(np.argmin(np.abs(lats - lat)))
    lon_idx = int(np.argmin(np.abs(lons - lon)))

    # GEBCO elevation: negative = below sea level, positive = above
    # We return depth as positive meters below sea level
    elev_value = float(elevation[lat_idx, lon_idx])
    depth = -elev_value if elev_value < 0 else 0.0

    return depth


def get_depths_in_bbox(
    bbox: Dict[str, float],
    gebco_data: Optional[Dict] = None,
) -> List[DepthPoint]:
    """Extract depth values within a bounding box.

    Parameters
    ----------
    bbox:
        Dictionary with keys ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    gebco_data:
        Pre-loaded GEBCO data dict. If ``None``, loads from cache/disk.

    Returns
    -------
    list[DepthPoint]
        Depth observations within the bounding box.
    """
    if gebco_data is None:
        gebco_data = load_gebco()

    lats = gebco_data["lat"]
    lons = gebco_data["lon"]
    elevation = gebco_data["elevation"]

    lat_mask = (lats >= bbox["lat_min"]) & (lats <= bbox["lat_max"])
    lon_mask = (lons >= bbox["lon_min"]) & (lons <= bbox["lon_max"])

    lat_indices = np.where(lat_mask)[0]
    lon_indices = np.where(lon_mask)[0]

    if len(lat_indices) == 0 or len(lon_indices) == 0:
        logger.warning("No GEBCO data points within bounding box: %s", bbox)
        return []

    data_points: List[DepthPoint] = []
    for lat_idx in lat_indices:
        for lon_idx in lon_indices:
            elev_value = float(elevation[lat_idx, lon_idx])
            # Convert elevation to depth (positive = below sea level)
            depth = -elev_value if elev_value < 0 else 0.0

            data_points.append(
                DepthPoint(
                    latitude=float(lats[lat_idx]),
                    longitude=float(lons[lon_idx]),
                    depth_meters=depth,
                )
            )

    logger.info(
        "Extracted %d depth points from GEBCO for bbox %s",
        len(data_points),
        bbox,
    )
    return data_points


def get_depths_all_regions(
    gebco_data: Optional[Dict] = None,
) -> Dict[str, List[DepthPoint]]:
    """Extract depth values for all configured target regions.

    Parameters
    ----------
    gebco_data:
        Pre-loaded GEBCO data dict. If ``None``, loads from cache/disk.

    Returns
    -------
    dict[str, list[DepthPoint]]
        Mapping of region name to depth points.
    """
    results: Dict[str, List[DepthPoint]] = {}
    for region_name, bbox in TARGET_REGIONS.items():
        results[region_name] = get_depths_in_bbox(bbox, gebco_data)
    return results
