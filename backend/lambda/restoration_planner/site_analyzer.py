"""
Restoration Site Analyzer — site suitability analysis and ranking.

Analyzes candidate mangrove restoration sites based on NDVI history,
soil condition, and tidal range. Ranks sites by carbon sequestration
potential (descending) and estimates expected survival rates.

Area is measured in Thai rai (1 rai = 1,600 m²).
CO2 potential uses the same baseline rate as the carbon calculator.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.6
"""

from __future__ import annotations

import importlib as _il
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

_models = _il.import_module("lambda.shared.models")

RestorationSite = _models.RestorationSite
NDVITimeSeries = _models.NDVITimeSeries
SoilData = _models.SoilData
TidalData = _models.TidalData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Same baseline rate used in carbon_calculator (tCO2/rai/year at NDVI=1.0)
BASELINE_SEQUESTRATION_RATE = 7.0

# Conversion factor: 1 rai = 1,600 m²
SQ_METERS_PER_RAI = 1600.0

# Ideal ranges for survival rate estimation
IDEAL_SOIL_PH_MIN = 6.0
IDEAL_SOIL_PH_MAX = 8.0
IDEAL_SOIL_SALINITY_MIN = 10.0
IDEAL_SOIL_SALINITY_MAX = 35.0
IDEAL_TIDAL_MIN = 0.5  # metres
IDEAL_TIDAL_MAX = 3.0  # metres

# Survival rate bounds (Requirement 5.4: target 45% → 85%)
MIN_SURVIVAL_RATE = 0.45
MAX_SURVIVAL_RATE = 0.85


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()


# ---------------------------------------------------------------------------
# Area Conversion (Requirement 5.3)
# ---------------------------------------------------------------------------


def sq_meters_to_rai(area_sq_m: float) -> float:
    """Convert area from square metres to Thai rai.

    1 rai = 1,600 m².

    Parameters
    ----------
    area_sq_m:
        Area in square metres.

    Returns
    -------
    float
        Area in rai. Always ≥ 0.
    """
    if area_sq_m < 0:
        return 0.0
    return area_sq_m / SQ_METERS_PER_RAI


# ---------------------------------------------------------------------------
# NDVI Factor (used for CO2 potential)
# ---------------------------------------------------------------------------


def _ndvi_factor(ndvi_history: NDVITimeSeries) -> float:
    """Compute an NDVI factor from the site's NDVI history.

    Uses the average of recent NDVI values, clamped to [0, 1].
    A higher average indicates better existing vegetation or
    recovery potential.

    Returns 0.0 when no history is available.
    """
    if not ndvi_history.values:
        return 0.0
    avg = sum(ndvi_history.values) / len(ndvi_history.values)
    return max(0.0, min(1.0, avg))


# ---------------------------------------------------------------------------
# CO2 Potential Calculation (Requirement 5.6)
# ---------------------------------------------------------------------------


def calculate_co2_potential(area_rai: float, ndvi_history: NDVITimeSeries) -> float:
    """Estimate annual CO2 sequestration potential (tCO2/year).

    Formula: area_rai × NDVI_factor × BASELINE_SEQUESTRATION_RATE

    Parameters
    ----------
    area_rai:
        Site area in Thai rai.
    ndvi_history:
        Historical NDVI time-series for the site.

    Returns
    -------
    float
        Estimated CO2 potential in tCO2/year. Always ≥ 0.
    """
    if area_rai <= 0:
        return 0.0
    factor = _ndvi_factor(ndvi_history)
    return area_rai * factor * BASELINE_SEQUESTRATION_RATE


# ---------------------------------------------------------------------------
# Survival Rate Estimation (Requirement 5.4)
# ---------------------------------------------------------------------------


def _soil_suitability(soil: SoilData) -> float:
    """Score soil suitability in [0, 1].

    Ideal: pH 6–8, salinity 10–35 ppt.
    """
    # pH component
    if IDEAL_SOIL_PH_MIN <= soil.ph <= IDEAL_SOIL_PH_MAX:
        ph_score = 1.0
    elif soil.ph < IDEAL_SOIL_PH_MIN:
        ph_score = max(0.0, 1.0 - (IDEAL_SOIL_PH_MIN - soil.ph) / 4.0)
    else:
        ph_score = max(0.0, 1.0 - (soil.ph - IDEAL_SOIL_PH_MAX) / 4.0)

    # Salinity component
    if IDEAL_SOIL_SALINITY_MIN <= soil.salinity <= IDEAL_SOIL_SALINITY_MAX:
        sal_score = 1.0
    elif soil.salinity < IDEAL_SOIL_SALINITY_MIN:
        sal_score = max(0.0, soil.salinity / IDEAL_SOIL_SALINITY_MIN)
    else:
        sal_score = max(0.0, 1.0 - (soil.salinity - IDEAL_SOIL_SALINITY_MAX) / 30.0)

    return (ph_score + sal_score) / 2.0


def _tidal_suitability(tidal: TidalData) -> float:
    """Score tidal range suitability in [0, 1].

    Ideal mean tidal range: 0.5–3.0 m.
    """
    mean = tidal.mean_m
    if IDEAL_TIDAL_MIN <= mean <= IDEAL_TIDAL_MAX:
        return 1.0
    elif mean < IDEAL_TIDAL_MIN:
        return max(0.0, mean / IDEAL_TIDAL_MIN)
    else:
        return max(0.0, 1.0 - (mean - IDEAL_TIDAL_MAX) / 5.0)


def _ndvi_suitability(ndvi_history: NDVITimeSeries) -> float:
    """Score NDVI history suitability in [0, 1].

    Sites with moderate historical NDVI (indicating some existing
    vegetation or recovery potential) score higher.
    """
    factor = _ndvi_factor(ndvi_history)
    # Moderate NDVI (0.2–0.6) is ideal for restoration (degraded but recoverable)
    # Very high NDVI means already healthy — less need for restoration
    # Very low NDVI means harsh conditions
    if 0.2 <= factor <= 0.6:
        return 1.0
    elif factor < 0.2:
        return max(0.0, factor / 0.2)
    else:
        # Above 0.6 — still suitable but less priority
        return max(0.0, 1.0 - (factor - 0.6) / 0.4)


def estimate_survival_rate(
    ndvi_history: NDVITimeSeries,
    soil: SoilData,
    tidal: TidalData,
) -> float:
    """Estimate expected seedling survival rate for a site.

    Combines NDVI history, soil condition, and tidal range into a
    composite suitability score, then maps it to the target survival
    rate range of 45%–85% (Requirement 5.4).

    Parameters
    ----------
    ndvi_history:
        Historical NDVI time-series.
    soil:
        Soil condition data.
    tidal:
        Tidal range data.

    Returns
    -------
    float
        Expected survival rate in [0.45, 0.85].
    """
    ndvi_score = _ndvi_suitability(ndvi_history)
    soil_score = _soil_suitability(soil)
    tidal_score = _tidal_suitability(tidal)

    # Weighted composite: soil and tidal matter most for seedling survival
    composite = 0.25 * ndvi_score + 0.40 * soil_score + 0.35 * tidal_score
    composite = max(0.0, min(1.0, composite))

    # Map composite [0, 1] → survival rate [MIN, MAX]
    survival = MIN_SURVIVAL_RATE + composite * (MAX_SURVIVAL_RATE - MIN_SURVIVAL_RATE)
    return round(survival, 4)


# ---------------------------------------------------------------------------
# Site Analysis (Requirement 5.1)
# ---------------------------------------------------------------------------


def analyze_site(
    site_id: str,
    geometry: Dict[str, Any],
    area_rai: float,
    ndvi_history: NDVITimeSeries,
    soil_condition: SoilData,
    tidal_range: TidalData,
) -> RestorationSite:
    """Analyze a single candidate restoration site.

    Computes CO2 potential, expected survival rate, and packages
    all data into a ``RestorationSite`` object. The ``priority_rank``
    is set to 0 (unranked) — use ``rank_sites`` to assign ranks.

    Parameters
    ----------
    site_id:
        Unique identifier for the site.
    geometry:
        GeoJSON Polygon geometry.
    area_rai:
        Site area in Thai rai.
    ndvi_history:
        Historical NDVI time-series.
    soil_condition:
        Soil condition data.
    tidal_range:
        Tidal range data.

    Returns
    -------
    RestorationSite
        Analyzed site with CO2 potential and survival rate.
    """
    co2_potential = calculate_co2_potential(area_rai, ndvi_history)
    survival_rate = estimate_survival_rate(ndvi_history, soil_condition, tidal_range)

    site = RestorationSite(
        site_id=site_id,
        geometry=geometry,
        area_rai=area_rai,
        ndvi_history=ndvi_history,
        soil_condition=soil_condition,
        tidal_range=tidal_range,
        carbon_potential_tco2_year=round(co2_potential, 4),
        expected_survival_rate=survival_rate,
        priority_rank=0,  # Assigned by rank_sites
    )

    logger.info(
        "Analyzed site %s: %.2f rai, CO2=%.2f tCO2/yr, survival=%.1f%%",
        site_id,
        area_rai,
        co2_potential,
        survival_rate * 100,
    )

    return site


# ---------------------------------------------------------------------------
# Site Ranking (Requirement 5.2 / Property 11)
# ---------------------------------------------------------------------------


def rank_sites(sites: List[RestorationSite]) -> List[RestorationSite]:
    """Rank restoration sites by carbon sequestration potential.

    Sites are sorted in descending order of ``carbon_potential_tco2_year``
    and assigned ``priority_rank`` starting from 1 (highest potential).

    Property 11: For all sets of sites with different carbon potentials,
    ranking is in descending order of carbon_potential.

    Parameters
    ----------
    sites:
        List of analyzed restoration sites.

    Returns
    -------
    List[RestorationSite]
        Sites sorted by carbon potential (descending) with ranks assigned.
    """
    sorted_sites = sorted(
        sites,
        key=lambda s: s.carbon_potential_tco2_year,
        reverse=True,
    )

    for rank, site in enumerate(sorted_sites, start=1):
        site.priority_rank = rank

    return sorted_sites


# ---------------------------------------------------------------------------
# Batch Analysis + Ranking
# ---------------------------------------------------------------------------


def analyze_and_rank_sites(
    site_configs: List[Dict[str, Any]],
) -> List[RestorationSite]:
    """Analyze and rank multiple candidate restoration sites.

    Each config dict should contain:
    - site_id: str
    - geometry: GeoJSON Polygon dict
    - area_rai: float
    - ndvi_history: NDVITimeSeries
    - soil_condition: SoilData
    - tidal_range: TidalData

    Parameters
    ----------
    site_configs:
        List of site configuration dicts.

    Returns
    -------
    List[RestorationSite]
        Analyzed and ranked sites (descending by carbon potential).
    """
    sites: List[RestorationSite] = []
    for cfg in site_configs:
        site = analyze_site(
            site_id=cfg["site_id"],
            geometry=cfg["geometry"],
            area_rai=cfg["area_rai"],
            ndvi_history=cfg["ndvi_history"],
            soil_condition=cfg["soil_condition"],
            tidal_range=cfg["tidal_range"],
        )
        sites.append(site)

    ranked = rank_sites(sites)

    logger.info(
        "Analyzed and ranked %d restoration sites. Top site: %s (%.2f tCO2/yr)",
        len(ranked),
        ranked[0].site_id if ranked else "N/A",
        ranked[0].carbon_potential_tco2_year if ranked else 0.0,
    )

    return ranked


# ---------------------------------------------------------------------------
# Database Storage (Requirement 5.1)
# ---------------------------------------------------------------------------


def store_restoration_sites(sites: List[RestorationSite]) -> str:
    """Persist ranked restoration sites to the ``restoration_sites`` table.

    Parameters
    ----------
    sites:
        List of analyzed and ranked restoration sites.

    Returns
    -------
    str
        Confirmation message.
    """
    client = get_supabase_client()

    rows = []
    for site in sites:
        rows.append(
            {
                "site_id": site.site_id,
                "geometry": site.geometry,
                "area_rai": site.area_rai,
                "carbon_potential": site.carbon_potential_tco2_year,
                "expected_survival_rate": site.expected_survival_rate,
                "priority_rank": site.priority_rank,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    client.table("restoration_sites").insert(rows).execute()

    logger.info("Stored %d restoration sites in database", len(sites))

    return f"Stored {len(sites)} restoration sites (ranks 1–{len(sites)})"
