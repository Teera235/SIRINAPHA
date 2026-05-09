"""
FSI Engine — FSI Calculator

Computes the Fishery Suitability Index (FSI) from up to six environmental
data sources using a weighted-sum formula.  Supports graceful degradation
when some data sources are unavailable: weights are re-normalised over the
available sources so the result remains in [0.0, 1.0].

Formula (all sources present):
    FSI = 0.25×SST + 0.25×Chl-a + 0.15×Depth + 0.10×Lunar + 0.25×NDVI + 0.10×Season

Requirements: 3.1, 3.9, 3.10
"""

from __future__ import annotations

import importlib as _il
from datetime import datetime
from typing import Dict, List, Optional

_models = _il.import_module("lambda.shared.models")
FSIComponentScores = _models.FSIComponentScores
FSIDataCompleteness = _models.FSIDataCompleteness
FSIResult = _models.FSIResult
FSIZone = _models.FSIZone
GeoPoint = _models.GeoPoint
SeasonData = _models.SeasonData
FSI_WEIGHTS = _models.FSI_WEIGHTS

_sf = _il.import_module("lambda.fsi_engine.score_functions")
sst_score = _sf.sst_score
chl_a_score = _sf.chl_a_score
depth_score = _sf.depth_score
lunar_score = _sf.lunar_score
season_score = _sf.season_score

# All recognised data source names (keys match FSI_WEIGHTS).
ALL_SOURCES = list(FSI_WEIGHTS.keys())


def _ndvi_to_score(ndvi: float) -> float:
    """Convert raw NDVI (-1..1) to a 0..1 score.

    Maps the NDVI range [-1, 1] linearly to [0, 1].
    """
    return max(0.0, min(1.0, (ndvi + 1.0) / 2.0))


def _classify_zone(fsi: float) -> FSIZone:
    """Classify an FSI value into a traffic-light zone.

    FSI > 0.7  → green  (เหมาะสมมาก)
    FSI 0.4–0.7 → yellow (เหมาะสมปานกลาง)
    FSI < 0.4  → red    (ไม่เหมาะสม)
    """
    if fsi > 0.7:
        return FSIZone.GREEN
    elif fsi >= 0.4:
        return FSIZone.YELLOW
    else:
        return FSIZone.RED


def calculate_fsi(
    *,
    location: GeoPoint,
    sst: Optional[float] = None,
    chl_a: Optional[float] = None,
    depth: Optional[float] = None,
    lunar_phase: Optional[float] = None,
    ndvi: Optional[float] = None,
    season: Optional[SeasonData] = None,
    calculated_at: Optional[datetime] = None,
) -> FSIResult:
    """Calculate the Fishery Suitability Index with graceful degradation.

    Parameters that are ``None`` are treated as *missing* data sources.
    The FSI is computed from the available sources only, with weights
    re-normalised so they sum to 1.0.

    Raises ``ValueError`` if **no** data sources are provided.

    Returns an :class:`FSIResult` with full component scores and
    data-completeness metadata.
    """

    # --- 1. Compute individual scores for available sources ----------------
    available_scores: Dict[str, float] = {}

    if sst is not None:
        available_scores["sst"] = sst_score(sst)
    if chl_a is not None:
        available_scores["chl_a"] = chl_a_score(chl_a)
    if depth is not None:
        available_scores["depth"] = depth_score(depth)
    if lunar_phase is not None:
        available_scores["lunar"] = lunar_score(lunar_phase)
    if ndvi is not None:
        available_scores["ndvi"] = _ndvi_to_score(ndvi)
    if season is not None:
        available_scores["season"] = season_score(season)

    if not available_scores:
        raise ValueError(
            "Cannot calculate FSI: no data sources provided."
        )

    # --- 2. Determine available / missing sources --------------------------
    available_sources: List[str] = sorted(available_scores.keys())
    missing_sources: List[str] = sorted(
        s for s in ALL_SOURCES if s not in available_scores
    )
    is_complete = len(missing_sources) == 0

    # --- 3. Re-normalise weights for available sources ---------------------
    raw_weight_sum = sum(FSI_WEIGHTS[s] for s in available_scores)
    normalised_weights: Dict[str, float] = {
        s: FSI_WEIGHTS[s] / raw_weight_sum for s in available_scores
    }

    # --- 4. Weighted sum ---------------------------------------------------
    fsi_raw = sum(
        normalised_weights[s] * available_scores[s]
        for s in available_scores
    )

    # Clamp to [0.0, 1.0]  (Requirement 3.10)
    fsi_value = max(0.0, min(1.0, fsi_raw))

    # --- 5. Build component scores (0.0 for missing sources) ---------------
    component_scores = FSIComponentScores(
        sst_score=available_scores.get("sst", 0.0),
        chl_a_score=available_scores.get("chl_a", 0.0),
        depth_score=available_scores.get("depth", 0.0),
        lunar_score=available_scores.get("lunar", 0.0),
        ndvi_score=available_scores.get("ndvi", 0.0),
        season_score=available_scores.get("season", 0.0),
    )

    # --- 6. Assemble result ------------------------------------------------
    return FSIResult(
        location=location,
        fsi_value=fsi_value,
        zone=_classify_zone(fsi_value),
        component_scores=component_scores,
        data_completeness=FSIDataCompleteness(
            available_sources=available_sources,
            missing_sources=missing_sources,
            is_complete=is_complete,
        ),
        calculated_at=calculated_at or datetime.utcnow(),
    )
