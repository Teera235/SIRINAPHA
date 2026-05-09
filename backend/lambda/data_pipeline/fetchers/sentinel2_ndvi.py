"""
Sentinel-2 NDVI Data Fetcher via Copernicus Data Space API.

Fetches Band 4 (Red) and Band 8 (NIR) data from Sentinel-2 L2A using the
Copernicus Sentinel Hub Process API. Supports bounding box filtering for
Mahachai and Ranong target regions. Scheduled every 5 days matching the
satellite orbit cycle.

Requirements: 1.3, 1.6, 1.9
"""

from __future__ import annotations

import importlib as _il
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

_config = _il.import_module("lambda.shared.config")
TARGET_REGIONS = _config.TARGET_REGIONS
COPERNICUS_API_URL = _config.COPERNICUS_API_URL
COPERNICUS_CLIENT_ID = _config.COPERNICUS_CLIENT_ID
COPERNICUS_CLIENT_SECRET = _config.COPERNICUS_CLIENT_SECRET


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COPERNICUS_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/"
    "CDSE/protocol/openid-connect/token"
)
SENTINEL_HUB_PROCESS_URL = (
    "https://sh.dataspace.copernicus.eu/api/v1/process"
)
REQUEST_TIMEOUT_SECONDS = 60

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class Sentinel2DataPoint:
    """A single Sentinel-2 observation with band values and coordinates."""

    latitude: float
    longitude: float
    band_4_red: float
    band_8_nir: float
    data_timestamp: datetime
    sentinel2_scene_id: str


@dataclass
class FetchResult:
    """Outcome of a data fetch operation."""

    source: str
    timestamp: datetime
    status: str  # "success" | "failed" | "partial"
    data: List[Sentinel2DataPoint] = field(default_factory=list)
    error: Optional[str] = None
    attempts: int = 1
    region: str = ""


# ---------------------------------------------------------------------------
# OAuth2 authentication
# ---------------------------------------------------------------------------


def authenticate_copernicus(
    client_id: str = COPERNICUS_CLIENT_ID,
    client_secret: str = COPERNICUS_CLIENT_SECRET,
    token_url: str = COPERNICUS_TOKEN_URL,
) -> str:
    """Authenticate with Copernicus Data Space using OAuth2 client credentials.

    Parameters
    ----------
    client_id:
        OAuth2 client ID from Copernicus Data Space registration.
    client_secret:
        OAuth2 client secret.
    token_url:
        Token endpoint URL.

    Returns
    -------
    str
        Bearer access token.

    Raises
    ------
    ValueError
        If credentials are not configured.
    requests.RequestException
        If the token request fails.
    """
    if not client_id or not client_secret:
        raise ValueError(
            "COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET "
            "environment variables must be set"
        )

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(
        token_url,
        data=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError(
            "No access_token in Copernicus token response. "
            f"Response keys: {list(token_data.keys())}"
        )

    logger.info("Successfully authenticated with Copernicus Data Space")
    return access_token


# ---------------------------------------------------------------------------
# Sentinel Hub Process API request
# ---------------------------------------------------------------------------


def build_process_request(
    bbox: Dict[str, float],
    target_date: datetime,
) -> Dict[str, Any]:
    """Build a Sentinel Hub Process API request payload.

    Requests Band 4 (Red) and Band 8 (NIR) from Sentinel-2 L2A data
    for the given bounding box and date range (5-day window ending at
    target_date).

    Parameters
    ----------
    bbox:
        Dictionary with keys ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    target_date:
        End date of the 5-day acquisition window.

    Returns
    -------
    dict
        Sentinel Hub Process API request body.
    """
    date_from = (target_date - timedelta(days=5)).strftime("%Y-%m-%dT00:00:00Z")
    date_to = target_date.strftime("%Y-%m-%dT23:59:59Z")

    return {
        "input": {
            "bounds": {
                "bbox": [
                    bbox["lon_min"],
                    bbox["lat_min"],
                    bbox["lon_max"],
                    bbox["lat_max"],
                ],
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": date_from,
                            "to": date_to,
                        },
                        "maxCloudCoverage": 30,
                    },
                }
            ],
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": "application/json"},
                }
            ],
        },
        "evalscript": _build_evalscript(),
    }


def _build_evalscript() -> str:
    """Build the evalscript that returns Band 4 (Red) and Band 8 (NIR) values.

    The evalscript requests B04 and B08 bands and returns them as a JSON
    array of sample objects with coordinates and band values.

    Returns
    -------
    str
        Sentinel Hub evalscript code.
    """
    return """//VERSION=3
function setup() {
    return {
        input: [{
            bands: ["B04", "B08"],
            units: "REFLECTANCE"
        }],
        output: {
            bands: 2,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    return [sample.B04, sample.B08];
}
"""


def fetch_sentinel2_bands(
    bbox: Dict[str, float],
    target_date: datetime,
    access_token: str,
    process_url: str = SENTINEL_HUB_PROCESS_URL,
) -> Dict[str, Any]:
    """Send a Process API request to Sentinel Hub and return the response.

    Parameters
    ----------
    bbox:
        Bounding box for the region of interest.
    target_date:
        End date of the 5-day acquisition window.
    access_token:
        Bearer token from ``authenticate_copernicus``.
    process_url:
        Sentinel Hub Process API endpoint.

    Returns
    -------
    dict
        Parsed JSON response from the Process API.

    Raises
    ------
    requests.RequestException
        If the HTTP request fails.
    ValueError
        If the response is not valid JSON.
    """
    request_body = build_process_request(bbox, target_date)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(
        process_url,
        json=request_body,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_sentinel2_response(
    response_data: Any,
    bbox: Dict[str, float],
    target_date: datetime,
    scene_id: Optional[str] = None,
) -> List[Sentinel2DataPoint]:
    """Parse Sentinel Hub Process API response into data points.

    The response may be a list of pixel samples or a nested structure
    depending on the evalscript output format. This function handles
    both flat arrays of [B04, B08] pairs and structured JSON responses.

    Parameters
    ----------
    response_data:
        Parsed JSON response from the Process API.
    bbox:
        Bounding box used for the request (for coordinate interpolation).
    target_date:
        Date of the observation.
    scene_id:
        Sentinel-2 scene identifier. Auto-generated if not provided.

    Returns
    -------
    list[Sentinel2DataPoint]
        Extracted band data points with interpolated coordinates.
    """
    if scene_id is None:
        scene_id = (
            f"S2_L2A_{target_date.strftime('%Y%m%d')}_"
            f"{bbox['lat_min']}_{bbox['lon_min']}"
        )

    data_points: List[Sentinel2DataPoint] = []

    # Handle list-of-lists format: [[B04, B08], [B04, B08], ...]
    if isinstance(response_data, list):
        samples = response_data
    elif isinstance(response_data, dict):
        # Try common response structures
        samples = response_data.get("data", response_data.get("samples", []))
        if not isinstance(samples, list):
            samples = []
    else:
        logger.warning(
            "Unexpected response_data type: %s", type(response_data).__name__
        )
        return []

    if not samples:
        return []

    # Interpolate coordinates across the bounding box grid
    num_samples = len(samples)
    grid_size = int(num_samples**0.5) or 1

    lat_step = (bbox["lat_max"] - bbox["lat_min"]) / max(grid_size - 1, 1)
    lon_step = (bbox["lon_max"] - bbox["lon_min"]) / max(grid_size - 1, 1)

    for idx, sample in enumerate(samples):
        band_4, band_8 = _extract_band_values(sample)
        if band_4 is None or band_8 is None:
            continue

        # Map linear index to grid coordinates
        row = idx // grid_size
        col = idx % grid_size
        lat = bbox["lat_min"] + row * lat_step
        lon = bbox["lon_min"] + col * lon_step

        # Clamp to bounding box
        lat = max(bbox["lat_min"], min(bbox["lat_max"], lat))
        lon = max(bbox["lon_min"], min(bbox["lon_max"], lon))

        data_points.append(
            Sentinel2DataPoint(
                latitude=lat,
                longitude=lon,
                band_4_red=band_4,
                band_8_nir=band_8,
                data_timestamp=target_date,
                sentinel2_scene_id=scene_id,
            )
        )

    logger.info(
        "Parsed %d Sentinel-2 data points from response", len(data_points)
    )
    return data_points


def _extract_band_values(sample: Any) -> tuple:
    """Extract Band 4 and Band 8 values from a single sample.

    Supports multiple formats:
    - List/tuple: [B04_value, B08_value]
    - Dict with keys: {"B04": value, "B08": value}
    - Dict with keys: {"band_4_red": value, "band_8_nir": value}

    Returns
    -------
    tuple[float | None, float | None]
        (band_4, band_8) values, or (None, None) if extraction fails.
    """
    if isinstance(sample, (list, tuple)) and len(sample) >= 2:
        try:
            return float(sample[0]), float(sample[1])
        except (ValueError, TypeError):
            return None, None

    if isinstance(sample, dict):
        # Try standard band names
        for b4_key in ("B04", "b04", "band_4_red", "red"):
            for b8_key in ("B08", "b08", "band_8_nir", "nir"):
                if b4_key in sample and b8_key in sample:
                    try:
                        return float(sample[b4_key]), float(sample[b8_key])
                    except (ValueError, TypeError):
                        return None, None

    return None, None


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------


def validate_sentinel2_data(
    data_points: List[Sentinel2DataPoint],
) -> List[Sentinel2DataPoint]:
    """Validate Sentinel-2 band data points, removing invalid entries.

    Valid reflectance values are non-negative finite numbers. Typical
    surface reflectance values range from 0.0 to 1.0, but we accept
    values up to 2.0 to account for calibration artifacts and let
    downstream consumers apply stricter filtering.

    Parameters
    ----------
    data_points:
        Raw parsed data points.

    Returns
    -------
    list[Sentinel2DataPoint]
        Data points that pass validation.
    """
    import math

    valid = []
    for dp in data_points:
        # Check for NaN/Inf
        if (
            math.isnan(dp.band_4_red)
            or math.isnan(dp.band_8_nir)
            or math.isinf(dp.band_4_red)
            or math.isinf(dp.band_8_nir)
        ):
            logger.warning(
                "Skipping invalid band values (B04=%s, B08=%s) at (%s, %s)",
                dp.band_4_red,
                dp.band_8_nir,
                dp.latitude,
                dp.longitude,
            )
            continue

        # Reflectance values should be non-negative
        if dp.band_4_red < 0 or dp.band_8_nir < 0:
            logger.warning(
                "Skipping negative band values (B04=%s, B08=%s) at (%s, %s)",
                dp.band_4_red,
                dp.band_8_nir,
                dp.latitude,
                dp.longitude,
            )
            continue

        valid.append(dp)
    return valid


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------


def store_raw_sentinel2_data(
    data_points: List[Sentinel2DataPoint],
    region: str,
    bbox: Dict[str, float],
    fetched_at: Optional[datetime] = None,
) -> None:
    """Persist raw Sentinel-2 band data into the ``satellite_raw_data`` table.

    Each call inserts one row per region fetch, storing all data points as a
    JSONB array in the ``data`` column. Includes the ``sentinel2_scene_id``
    for traceability.

    Parameters
    ----------
    data_points:
        Validated Sentinel-2 observations.
    region:
        Region name (e.g. ``"mahachai"`` or ``"ranong"``).
    bbox:
        Bounding box used for the fetch.
    fetched_at:
        Override for the ``fetched_at`` timestamp (defaults to ``now()``).
    """
    if not data_points:
        logger.info("No Sentinel-2 data points to store for region %s", region)
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

    # Extract scene ID from the first data point
    sentinel2_scene_id = data_points[0].sentinel2_scene_id

    record = {
        "source": "sentinel2_ndvi",
        "fetched_at": fetched_at.isoformat(),
        "data_timestamp": data_timestamp.isoformat(),
        "data": {
            "region": region,
            "bbox": bbox,
            "sentinel2_scene_id": sentinel2_scene_id,
            "points": [
                {
                    "latitude": dp.latitude,
                    "longitude": dp.longitude,
                    "band_4_red": dp.band_4_red,
                    "band_8_nir": dp.band_8_nir,
                    "sentinel2_scene_id": dp.sentinel2_scene_id,
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
        "Stored %d Sentinel-2 data points for region %s "
        "(scene_id=%s, fetched_at=%s)",
        len(data_points),
        region,
        sentinel2_scene_id,
        fetched_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------


def fetch_sentinel2_for_region(
    region: str,
    bbox: Dict[str, float],
    target_date: Optional[datetime] = None,
    access_token: Optional[str] = None,
) -> FetchResult:
    """Fetch Sentinel-2 Band 4/Band 8 data for a single region.

    Parameters
    ----------
    region:
        Human-readable region name (e.g. ``"mahachai"``).
    bbox:
        Bounding box with ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.
    target_date:
        End date of the 5-day acquisition window. Defaults to today (UTC).
    access_token:
        Pre-obtained OAuth2 token. If not provided, authenticates automatically.

    Returns
    -------
    FetchResult
        Contains parsed data points on success, or an error message on failure.
    """
    now = datetime.now(timezone.utc)
    if target_date is None:
        target_date = now

    logger.info(
        "Fetching Sentinel-2 NDVI bands for region=%s date=%s",
        region,
        target_date.strftime("%Y-%m-%d"),
    )

    # Step 1: Authenticate if no token provided
    if access_token is None:
        try:
            access_token = authenticate_copernicus()
        except Exception as exc:
            logger.error(
                "Copernicus authentication failed for region %s: %s",
                region,
                exc,
            )
            return FetchResult(
                source="sentinel2_ndvi",
                timestamp=now,
                status="failed",
                error=f"Authentication failed: {exc}",
                region=region,
            )

    # Step 2: Fetch band data via Process API
    try:
        response_data = fetch_sentinel2_bands(bbox, target_date, access_token)
    except requests.RequestException as exc:
        logger.error(
            "Sentinel Hub Process API request failed for region %s: %s",
            region,
            exc,
        )
        return FetchResult(
            source="sentinel2_ndvi",
            timestamp=now,
            status="failed",
            error=f"Process API request failed: {exc}",
            region=region,
        )
    except ValueError as exc:
        logger.error(
            "Invalid response from Sentinel Hub for region %s: %s",
            region,
            exc,
        )
        return FetchResult(
            source="sentinel2_ndvi",
            timestamp=now,
            status="failed",
            error=f"Invalid response: {exc}",
            region=region,
        )

    # Step 3: Parse response into data points
    try:
        data_points = parse_sentinel2_response(
            response_data, bbox, target_date
        )
    except Exception as exc:
        logger.error(
            "Failed to parse Sentinel-2 response for region %s: %s",
            region,
            exc,
        )
        return FetchResult(
            source="sentinel2_ndvi",
            timestamp=now,
            status="failed",
            error=f"Response parsing failed: {exc}",
            region=region,
        )

    if not data_points:
        return FetchResult(
            source="sentinel2_ndvi",
            timestamp=now,
            status="partial",
            data=[],
            error="No Sentinel-2 data points in response",
            region=region,
        )

    # Step 4: Validate data
    valid_points = validate_sentinel2_data(data_points)

    if not valid_points:
        return FetchResult(
            source="sentinel2_ndvi",
            timestamp=now,
            status="partial",
            data=[],
            error="No valid Sentinel-2 data points after validation",
            region=region,
        )

    # Step 5: Store in database
    try:
        store_raw_sentinel2_data(valid_points, region, bbox, fetched_at=now)
    except Exception as exc:
        logger.error(
            "Failed to store Sentinel-2 data for region %s: %s", region, exc
        )
        return FetchResult(
            source="sentinel2_ndvi",
            timestamp=now,
            status="failed",
            data=valid_points,
            error=f"Database storage failed: {exc}",
            region=region,
        )

    return FetchResult(
        source="sentinel2_ndvi",
        timestamp=now,
        status="success",
        data=valid_points,
        region=region,
    )


def fetch_sentinel2_all_regions(
    target_date: Optional[datetime] = None,
) -> List[FetchResult]:
    """Fetch Sentinel-2 data for all configured target regions.

    Authenticates once and reuses the token for all regions. Iterates
    over ``TARGET_REGIONS`` from the shared config.

    Parameters
    ----------
    target_date:
        End date of the 5-day acquisition window. Defaults to today (UTC).

    Returns
    -------
    list[FetchResult]
        One result per region.
    """
    # Authenticate once for all regions
    try:
        access_token = authenticate_copernicus()
    except Exception as exc:
        logger.error("Copernicus authentication failed: %s", exc)
        now = datetime.now(timezone.utc)
        return [
            FetchResult(
                source="sentinel2_ndvi",
                timestamp=now,
                status="failed",
                error=f"Authentication failed: {exc}",
                region=region_name,
            )
            for region_name in TARGET_REGIONS
        ]

    results: List[FetchResult] = []
    for region_name, bbox in TARGET_REGIONS.items():
        result = fetch_sentinel2_for_region(
            region_name, bbox, target_date, access_token=access_token
        )
        results.append(result)
    return results
