"""
FSI Engine — FSI Map Generation and Storage

Provides functions to:
  • Store FSI results with component scores in Supabase
  • Generate an FSI Map (collection of FSI results for all areas)
  • Run a daily FSI update (Lambda handler triggered by EventBridge)

Requirements: 3.7, 3.8
"""

from __future__ import annotations

import importlib as _il
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_models = _il.import_module("lambda.shared.models")
FSIResult = _models.FSIResult
GeoPoint = _models.GeoPoint
SeasonData = _models.SeasonData

_calc = _il.import_module("lambda.fsi_engine.fsi_calculator")
calculate_fsi = _calc.calculate_fsi


def get_supabase_client():
    """Lazy import of the Supabase client factory."""
    _sc = _il.import_module("lambda.shared.supabase_client")
    return _sc.get_supabase_client()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Store FSI result
# ---------------------------------------------------------------------------


def store_fsi_result(result: FSIResult, area_id: str, client: Any = None) -> Dict[str, str]:
    """Store an FSI result and its component scores in Supabase.

    Inserts a row into ``fsi_results`` and a corresponding row into
    ``fsi_component_scores``.

    Parameters
    ----------
    result : FSIResult
        The computed FSI result to persist.
    area_id : str
        UUID of the fishing area this result belongs to.
    client : optional
        A Supabase client instance.  If ``None``, one is created via
        :func:`get_supabase_client`.

    Returns
    -------
    dict
        ``{"fsi_result_id": "<uuid>", "component_scores_id": "<uuid>"}``
    """
    if client is None:
        client = get_supabase_client()

    # Build the PostGIS point literal expected by the geography column.
    point_wkt = f"SRID=4326;POINT({result.location.lng} {result.location.lat})"

    # --- Insert into fsi_results -------------------------------------------
    fsi_row = {
        "area_id": area_id,
        "fsi_value": result.fsi_value,
        "zone": result.zone.value,
        "is_complete": result.data_completeness.is_complete,
        "calculated_at": result.calculated_at.isoformat(),
        "location": point_wkt,
    }

    fsi_resp = client.table("fsi_results").insert(fsi_row).execute()
    fsi_result_id = fsi_resp.data[0]["id"]

    # --- Insert into fsi_component_scores ----------------------------------
    cs = result.component_scores
    scores_row = {
        "fsi_result_id": fsi_result_id,
        "sst_score": cs.sst_score,
        "chl_a_score": cs.chl_a_score,
        "depth_score": cs.depth_score,
        "lunar_score": cs.lunar_score,
        "ndvi_score": cs.ndvi_score,
        "season_score": cs.season_score,
    }

    scores_resp = client.table("fsi_component_scores").insert(scores_row).execute()
    component_scores_id = scores_resp.data[0]["id"]

    logger.info(
        "Stored FSI result %s (area=%s, fsi=%.3f, zone=%s)",
        fsi_result_id,
        area_id,
        result.fsi_value,
        result.zone.value,
    )

    return {
        "fsi_result_id": fsi_result_id,
        "component_scores_id": component_scores_id,
    }


# ---------------------------------------------------------------------------
# Generate FSI Map
# ---------------------------------------------------------------------------


def generate_fsi_map(
    area_results: List[Tuple[str, FSIResult]],
) -> List[Dict[str, Any]]:
    """Generate an FSI Map — a collection of FSI results for all areas.

    Each entry contains the area_id, FSI value, zone classification,
    component scores, and data-completeness metadata.

    Parameters
    ----------
    area_results : list of (area_id, FSIResult) tuples
        The FSI results for each fishing area.

    Returns
    -------
    list of dict
        A list of FSI map entries, one per area.
    """
    fsi_map: List[Dict[str, Any]] = []

    for area_id, result in area_results:
        cs = result.component_scores
        entry: Dict[str, Any] = {
            "area_id": area_id,
            "location": {"lat": result.location.lat, "lng": result.location.lng},
            "fsi_value": result.fsi_value,
            "zone": result.zone.value,
            "component_scores": {
                "sst_score": cs.sst_score,
                "chl_a_score": cs.chl_a_score,
                "depth_score": cs.depth_score,
                "lunar_score": cs.lunar_score,
                "ndvi_score": cs.ndvi_score,
                "season_score": cs.season_score,
            },
            "data_completeness": {
                "available_sources": result.data_completeness.available_sources,
                "missing_sources": result.data_completeness.missing_sources,
                "is_complete": result.data_completeness.is_complete,
            },
            "calculated_at": result.calculated_at.isoformat(),
        }
        fsi_map.append(entry)

    logger.info("Generated FSI map with %d area(s)", len(fsi_map))
    return fsi_map


# ---------------------------------------------------------------------------
# Fetch latest environmental data for an area
# ---------------------------------------------------------------------------


def _fetch_latest_data_for_area(
    area_id: str, client: Any
) -> Dict[str, Any]:
    """Query Supabase for the most recent environmental data for an area.

    Returns a dict with keys matching :func:`calculate_fsi` keyword args
    (``sst``, ``chl_a``, ``ndvi``, ``depth``, ``lunar_phase``, ``season``).
    Missing data sources are omitted from the dict.
    """
    data: Dict[str, Any] = {}

    # --- Fishing area centroid (for location) ------------------------------
    area_resp = (
        client.table("fishing_areas")
        .select("id, name, region")
        .eq("id", area_id)
        .limit(1)
        .execute()
    )
    if not area_resp.data:
        logger.warning("Fishing area %s not found", area_id)
        return data

    # --- Latest SST --------------------------------------------------------
    sst_resp = (
        client.table("sst_records")
        .select("sst_celsius")
        .order("observed_at", desc=True)
        .limit(1)
        .execute()
    )
    if sst_resp.data:
        data["sst"] = sst_resp.data[0]["sst_celsius"]

    # --- Latest Chl-a ------------------------------------------------------
    chl_resp = (
        client.table("chl_a_records")
        .select("chl_a_mg_m3")
        .order("observed_at", desc=True)
        .limit(1)
        .execute()
    )
    if chl_resp.data:
        data["chl_a"] = chl_resp.data[0]["chl_a_mg_m3"]

    # --- Latest NDVI for this area -----------------------------------------
    ndvi_resp = (
        client.table("ndvi_records")
        .select("ndvi_value")
        .eq("area_id", area_id)
        .order("observed_at", desc=True)
        .limit(1)
        .execute()
    )
    if ndvi_resp.data:
        data["ndvi"] = ndvi_resp.data[0]["ndvi_value"]

    return data


# ---------------------------------------------------------------------------
# Daily FSI update — Lambda handler
# ---------------------------------------------------------------------------


def run_daily_fsi_update(event: Optional[Dict] = None, context: Any = None) -> Dict[str, Any]:
    """Lambda handler: compute and store FSI for all fishing areas.

    Triggered daily by EventBridge when SST/Chl-a data updates.

    Parameters
    ----------
    event : dict, optional
        EventBridge event payload (unused but required by Lambda signature).
    context : optional
        Lambda context object (unused).

    Returns
    -------
    dict
        Summary with ``status``, ``areas_processed``, ``fsi_map``, and
        any ``errors`` encountered.
    """
    import ephem  # noqa: local import to keep module importable without ephem

    client = get_supabase_client()

    # --- 1. Get all fishing areas ------------------------------------------
    areas_resp = client.table("fishing_areas").select("id, name, region, boundary").execute()
    areas = areas_resp.data or []

    if not areas:
        logger.warning("No fishing areas found — nothing to update")
        return {"status": "no_areas", "areas_processed": 0, "fsi_map": [], "errors": []}

    # --- 2. Compute current lunar phase ------------------------------------
    moon = ephem.Moon()
    moon.compute()
    lunar_phase = moon.phase / 100.0  # ephem gives 0–100, we need 0.0–1.0

    # --- 3. Determine current season ---------------------------------------
    now = datetime.utcnow()
    month = now.month
    is_monsoon = month in (5, 6, 7, 8, 9, 10)
    season = SeasonData(
        season="monsoon" if is_monsoon else "dry",
        month=month,
        is_monsoon=is_monsoon,
    )

    # --- 4. Process each area ----------------------------------------------
    area_results: List[Tuple[str, FSIResult]] = []
    errors: List[Dict[str, str]] = []

    for area in areas:
        area_id = area["id"]
        area_name = area.get("name", area_id)
        try:
            env_data = _fetch_latest_data_for_area(area_id, client)

            # Use a representative centroid for the area.
            # In production this would come from the area boundary centroid.
            location = GeoPoint(lat=13.5, lng=100.3)  # default; overridden below

            # Try to derive centroid from region config
            _config = _il.import_module("lambda.shared.config")
            region = area.get("region", "").lower()
            if region in _config.TARGET_REGIONS:
                bbox = _config.TARGET_REGIONS[region]
                location = GeoPoint(
                    lat=(bbox["lat_min"] + bbox["lat_max"]) / 2,
                    lng=(bbox["lon_min"] + bbox["lon_max"]) / 2,
                )

            fsi_result = calculate_fsi(
                location=location,
                sst=env_data.get("sst"),
                chl_a=env_data.get("chl_a"),
                depth=env_data.get("depth"),
                lunar_phase=lunar_phase,
                ndvi=env_data.get("ndvi"),
                season=season,
                calculated_at=now,
            )

            # Store in database
            store_fsi_result(fsi_result, area_id, client=client)
            area_results.append((area_id, fsi_result))

            logger.info(
                "FSI updated for %s: %.3f (%s)",
                area_name,
                fsi_result.fsi_value,
                fsi_result.zone.value,
            )

        except ValueError as exc:
            # No data sources at all for this area — skip
            logger.error("Skipping area %s: %s", area_name, exc)
            errors.append({"area_id": area_id, "error": str(exc)})
        except Exception as exc:
            logger.error("Error processing area %s: %s", area_name, exc)
            errors.append({"area_id": area_id, "error": str(exc)})

    # --- 5. Generate FSI Map -----------------------------------------------
    fsi_map = generate_fsi_map(area_results)

    return {
        "status": "completed",
        "areas_processed": len(area_results),
        "fsi_map": fsi_map,
        "errors": errors,
    }
