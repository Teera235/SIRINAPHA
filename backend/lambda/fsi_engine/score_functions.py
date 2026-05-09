"""
FSI Engine — Score Functions

Individual scoring functions that convert raw environmental measurements
into normalised scores in [0.0, 1.0] for the Fishery Suitability Index.

Each function implements a piecewise-linear mapping:
  • Values inside the optimal range score 1.0.
  • Values outside decay linearly toward 0.0.

Requirements: 3.2, 3.3, 3.4, 3.5, 3.6
"""

from __future__ import annotations

import importlib as _il

_models = _il.import_module("lambda.shared.models")
SeasonData = _models.SeasonData


# ---------------------------------------------------------------------------
# SST Score  (Requirement 3.2)
# ---------------------------------------------------------------------------

def sst_score(sst: float) -> float:
    """Convert sea-surface temperature (°C) to a score in [0, 1].

    Optimal range: 27–30 °C → 1.0
    Linear decay: ±10 °C outside the range → 0.0
    """
    if 27.0 <= sst <= 30.0:
        return 1.0
    elif sst < 27.0:
        return max(0.0, 1.0 - (27.0 - sst) / 10.0)
    else:
        return max(0.0, 1.0 - (sst - 30.0) / 10.0)


# ---------------------------------------------------------------------------
# Chlorophyll-a Score  (Requirement 3.3)
# ---------------------------------------------------------------------------

def chl_a_score(chl_a: float) -> float:
    """Convert chlorophyll-a concentration (mg/m³) to a score in [0, 1].

    Optimal range: 0.5–5.0 mg/m³ → 1.0
    Below 0.5: linear decay to 0.0 at 0.0
    Above 5.0: linear decay to 0.0 at 20.0
    """
    if 0.5 <= chl_a <= 5.0:
        return 1.0
    elif chl_a < 0.5:
        return max(0.0, chl_a / 0.5)
    else:
        return max(0.0, 1.0 - (chl_a - 5.0) / 15.0)


# ---------------------------------------------------------------------------
# Depth Score  (Requirement 3.4)
# ---------------------------------------------------------------------------

def depth_score(depth: float) -> float:
    """Convert bathymetric depth (metres) to a score in [0, 1].

    Optimal range: 5–50 m → 1.0  (suitable for small fishing boats)
    Below 5 m: linear decay to 0.0 at 0 m
    Above 50 m: linear decay to 0.0 at 100 m
    """
    if 5.0 <= depth <= 50.0:
        return 1.0
    elif depth < 5.0:
        return max(0.0, depth / 5.0)
    else:
        return max(0.0, 1.0 - (depth - 50.0) / 50.0)


# ---------------------------------------------------------------------------
# Lunar Score  (Requirement 3.5)
# ---------------------------------------------------------------------------

def lunar_score(phase: float) -> float:
    """Convert lunar phase to a score in [0.3, 1.0].

    phase 0.0 (new moon / เดือนมืด) → 1.0  (best for fishing)
    phase 1.0 (full moon / เต็มดวง) → 0.3
    Linear interpolation between the two extremes.
    """
    return 1.0 - 0.7 * phase


# ---------------------------------------------------------------------------
# Season Score  (Requirement 3.6)
# ---------------------------------------------------------------------------

# Thailand fishing seasons by month.
# Gulf of Thailand monsoon: Oct–Jan (NE monsoon, rougher seas)
# Andaman Sea monsoon: May–Oct (SW monsoon, rougher seas)
# Scores reflect general suitability for small-boat fishing.

_MONTH_BASE_SCORES: dict[int, float] = {
    1: 0.6,   # Jan — tail of NE monsoon, improving
    2: 0.8,   # Feb — dry season, good fishing
    3: 0.9,   # Mar — peak dry season, excellent
    4: 0.9,   # Apr — peak dry season, excellent
    5: 0.7,   # May — SW monsoon starts
    6: 0.5,   # Jun — monsoon season
    7: 0.4,   # Jul — monsoon season
    8: 0.4,   # Aug — monsoon season
    9: 0.5,   # Sep — monsoon easing
    10: 0.6,  # Oct — transition, NE monsoon starts
    11: 0.7,  # Nov — NE monsoon, moderate
    12: 0.7,  # Dec — NE monsoon, moderate
}


def season_score(season: SeasonData) -> float:
    """Convert seasonal / meteorological data to a score in [0, 1].

    Uses the month to look up a base score reflecting Thailand's fishing
    seasons, then applies a penalty during active monsoon periods.

    Parameters
    ----------
    season : SeasonData
        Contains ``month`` (1–12), ``season`` (str), and ``is_monsoon`` (bool).
    """
    base = _MONTH_BASE_SCORES.get(season.month, 0.5)

    # Apply monsoon penalty: reduce score by 30 % during monsoon
    if season.is_monsoon:
        base *= 0.7

    # Clamp to [0, 1]
    return max(0.0, min(1.0, base))
