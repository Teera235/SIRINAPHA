"""
Unit tests for FSI Engine — fsi_calculator module.

Covers:
  • Full-data weighted-sum calculation (Requirement 3.1)
  • Clamping to [0.0, 1.0] (Requirement 3.10)
  • Graceful degradation with missing sources (Requirement 3.9)
  • Zone classification consistency
  • Edge cases and error handling
"""

from __future__ import annotations

import importlib
from datetime import datetime

import pytest

_calc = importlib.import_module("lambda.fsi_engine.fsi_calculator")
calculate_fsi = _calc.calculate_fsi
_ndvi_to_score = _calc._ndvi_to_score
_classify_zone = _calc._classify_zone
ALL_SOURCES = _calc.ALL_SOURCES

_models = importlib.import_module("lambda.shared.models")
GeoPoint = _models.GeoPoint
SeasonData = _models.SeasonData
FSIZone = _models.FSIZone
FSI_WEIGHTS = _models.FSI_WEIGHTS

_sf = importlib.import_module("lambda.fsi_engine.score_functions")
sst_score_fn = _sf.sst_score
chl_a_score_fn = _sf.chl_a_score
depth_score_fn = _sf.depth_score
lunar_score_fn = _sf.lunar_score
season_score_fn = _sf.season_score

# Shared test fixtures
LOCATION = GeoPoint(lat=13.5, lng=100.3)
SEASON_DRY = SeasonData(season="dry", month=3, is_monsoon=False)
SEASON_MONSOON = SeasonData(season="monsoon", month=7, is_monsoon=True)
NOW = datetime(2024, 6, 15, 8, 0, 0)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _full_kwargs(**overrides):
    """Return keyword arguments for a complete FSI calculation."""
    defaults = dict(
        location=LOCATION,
        sst=28.5,
        chl_a=2.0,
        depth=20.0,
        lunar_phase=0.0,
        ndvi=0.7,
        season=SEASON_DRY,
        calculated_at=NOW,
    )
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# NDVI-to-score helper
# ---------------------------------------------------------------------------


class TestNdviToScore:
    """_ndvi_to_score maps [-1, 1] → [0, 1] linearly."""

    def test_ndvi_minus_one(self):
        assert _ndvi_to_score(-1.0) == pytest.approx(0.0)

    def test_ndvi_zero(self):
        assert _ndvi_to_score(0.0) == pytest.approx(0.5)

    def test_ndvi_one(self):
        assert _ndvi_to_score(1.0) == pytest.approx(1.0)

    def test_ndvi_mid_positive(self):
        assert _ndvi_to_score(0.5) == pytest.approx(0.75)

    def test_ndvi_clamped_below(self):
        assert _ndvi_to_score(-2.0) == 0.0

    def test_ndvi_clamped_above(self):
        assert _ndvi_to_score(3.0) == 1.0


# ---------------------------------------------------------------------------
# Zone classification
# ---------------------------------------------------------------------------


class TestClassifyZone:
    def test_green_zone(self):
        assert _classify_zone(0.8) == FSIZone.GREEN

    def test_green_boundary(self):
        assert _classify_zone(0.71) == FSIZone.GREEN

    def test_yellow_zone(self):
        assert _classify_zone(0.55) == FSIZone.YELLOW

    def test_yellow_lower_boundary(self):
        assert _classify_zone(0.4) == FSIZone.YELLOW

    def test_yellow_upper_boundary(self):
        assert _classify_zone(0.7) == FSIZone.YELLOW

    def test_red_zone(self):
        assert _classify_zone(0.2) == FSIZone.RED

    def test_red_boundary(self):
        assert _classify_zone(0.39) == FSIZone.RED

    def test_red_zero(self):
        assert _classify_zone(0.0) == FSIZone.RED

    def test_green_max(self):
        assert _classify_zone(1.0) == FSIZone.GREEN


# ---------------------------------------------------------------------------
# Full-data FSI calculation  (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestFullDataFSI:
    """When all six sources are present, FSI = weighted sum of scores."""

    def test_weighted_sum_matches_formula(self):
        result = calculate_fsi(**_full_kwargs())

        # The raw weights sum to 1.10, so they are re-normalised.
        scores = {
            "sst": sst_score_fn(28.5),
            "chl_a": chl_a_score_fn(2.0),
            "depth": depth_score_fn(20.0),
            "lunar": lunar_score_fn(0.0),
            "ndvi": _ndvi_to_score(0.7),
            "season": season_score_fn(SEASON_DRY),
        }
        weight_sum = sum(FSI_WEIGHTS.values())
        expected = sum(
            (FSI_WEIGHTS[k] / weight_sum) * scores[k] for k in scores
        )
        assert result.fsi_value == pytest.approx(expected, abs=1e-9)

    def test_is_complete_flag(self):
        result = calculate_fsi(**_full_kwargs())
        assert result.data_completeness.is_complete is True

    def test_no_missing_sources(self):
        result = calculate_fsi(**_full_kwargs())
        assert result.data_completeness.missing_sources == []

    def test_all_sources_available(self):
        result = calculate_fsi(**_full_kwargs())
        assert sorted(result.data_completeness.available_sources) == sorted(ALL_SOURCES)

    def test_location_preserved(self):
        result = calculate_fsi(**_full_kwargs())
        assert result.location == LOCATION

    def test_calculated_at_preserved(self):
        result = calculate_fsi(**_full_kwargs())
        assert result.calculated_at == NOW

    def test_component_scores_populated(self):
        result = calculate_fsi(**_full_kwargs())
        cs = result.component_scores
        assert cs.sst_score == pytest.approx(sst_score_fn(28.5))
        assert cs.chl_a_score == pytest.approx(chl_a_score_fn(2.0))
        assert cs.depth_score == pytest.approx(depth_score_fn(20.0))
        assert cs.lunar_score == pytest.approx(lunar_score_fn(0.0))
        assert cs.ndvi_score == pytest.approx(_ndvi_to_score(0.7))
        assert cs.season_score == pytest.approx(season_score_fn(SEASON_DRY))

    def test_optimal_inputs_high_fsi(self):
        """All optimal inputs should produce a high FSI (green zone)."""
        result = calculate_fsi(**_full_kwargs(
            sst=28.5,       # optimal
            chl_a=2.0,      # optimal
            depth=20.0,     # optimal
            lunar_phase=0.0, # new moon → 1.0
            ndvi=1.0,        # max NDVI → 1.0
            season=SEASON_DRY,
        ))
        assert result.fsi_value > 0.7
        assert result.zone == FSIZone.GREEN

    def test_poor_inputs_low_fsi(self):
        """All poor inputs should produce a low FSI (red zone)."""
        result = calculate_fsi(**_full_kwargs(
            sst=5.0,          # far below optimal
            chl_a=0.0,        # zero
            depth=0.0,        # zero
            lunar_phase=1.0,  # full moon → 0.3
            ndvi=-1.0,        # worst NDVI → 0.0
            season=SEASON_MONSOON,
        ))
        assert result.fsi_value < 0.4
        assert result.zone == FSIZone.RED


# ---------------------------------------------------------------------------
# Clamping  (Requirement 3.10)
# ---------------------------------------------------------------------------


class TestFSIClamping:
    """FSI must always be in [0.0, 1.0]."""

    def test_fsi_at_most_one(self):
        # All scores at maximum → FSI = 1.0
        result = calculate_fsi(**_full_kwargs(
            sst=28.5,
            chl_a=2.0,
            depth=20.0,
            lunar_phase=0.0,
            ndvi=1.0,
            season=SEASON_DRY,
        ))
        assert result.fsi_value <= 1.0

    def test_fsi_at_least_zero(self):
        # All scores at minimum → FSI ≥ 0.0
        result = calculate_fsi(**_full_kwargs(
            sst=-50.0,
            chl_a=-10.0,
            depth=-100.0,
            lunar_phase=1.0,
            ndvi=-1.0,
            season=SEASON_MONSOON,
        ))
        assert result.fsi_value >= 0.0

    def test_extreme_sst_still_valid(self):
        result = calculate_fsi(**_full_kwargs(sst=1000.0))
        assert 0.0 <= result.fsi_value <= 1.0

    def test_extreme_chl_a_still_valid(self):
        result = calculate_fsi(**_full_kwargs(chl_a=500.0))
        assert 0.0 <= result.fsi_value <= 1.0

    def test_extreme_depth_still_valid(self):
        result = calculate_fsi(**_full_kwargs(depth=10000.0))
        assert 0.0 <= result.fsi_value <= 1.0


# ---------------------------------------------------------------------------
# Graceful degradation  (Requirement 3.9)
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """FSI should be calculable from any non-empty subset of sources."""

    def test_single_source_sst(self):
        result = calculate_fsi(location=LOCATION, sst=28.5, calculated_at=NOW)
        assert result.data_completeness.is_complete is False
        assert "sst" in result.data_completeness.available_sources
        assert len(result.data_completeness.missing_sources) == 5
        assert 0.0 <= result.fsi_value <= 1.0

    def test_single_source_chl_a(self):
        result = calculate_fsi(location=LOCATION, chl_a=2.0, calculated_at=NOW)
        assert result.data_completeness.is_complete is False
        assert "chl_a" in result.data_completeness.available_sources
        assert 0.0 <= result.fsi_value <= 1.0

    def test_single_source_depth(self):
        result = calculate_fsi(location=LOCATION, depth=20.0, calculated_at=NOW)
        assert result.data_completeness.is_complete is False
        assert "depth" in result.data_completeness.available_sources
        assert 0.0 <= result.fsi_value <= 1.0

    def test_single_source_lunar(self):
        result = calculate_fsi(location=LOCATION, lunar_phase=0.5, calculated_at=NOW)
        assert result.data_completeness.is_complete is False
        assert "lunar" in result.data_completeness.available_sources
        assert 0.0 <= result.fsi_value <= 1.0

    def test_single_source_ndvi(self):
        result = calculate_fsi(location=LOCATION, ndvi=0.6, calculated_at=NOW)
        assert result.data_completeness.is_complete is False
        assert "ndvi" in result.data_completeness.available_sources
        assert 0.0 <= result.fsi_value <= 1.0

    def test_single_source_season(self):
        result = calculate_fsi(location=LOCATION, season=SEASON_DRY, calculated_at=NOW)
        assert result.data_completeness.is_complete is False
        assert "season" in result.data_completeness.available_sources
        assert 0.0 <= result.fsi_value <= 1.0

    def test_two_sources(self):
        result = calculate_fsi(
            location=LOCATION, sst=28.5, chl_a=2.0, calculated_at=NOW,
        )
        assert result.data_completeness.is_complete is False
        assert sorted(result.data_completeness.available_sources) == ["chl_a", "sst"]
        assert len(result.data_completeness.missing_sources) == 4
        assert 0.0 <= result.fsi_value <= 1.0

    def test_five_sources_missing_season(self):
        result = calculate_fsi(
            location=LOCATION,
            sst=28.5,
            chl_a=2.0,
            depth=20.0,
            lunar_phase=0.0,
            ndvi=0.7,
            calculated_at=NOW,
        )
        assert result.data_completeness.is_complete is False
        assert result.data_completeness.missing_sources == ["season"]
        assert 0.0 <= result.fsi_value <= 1.0

    def test_renormalised_weights_sum_to_one(self):
        """When sources are missing, re-normalised weights must sum to 1."""
        # With only sst and chl_a: weights 0.25 + 0.25 = 0.50
        # Re-normalised: 0.5 and 0.5
        result = calculate_fsi(
            location=LOCATION, sst=28.5, chl_a=2.0, calculated_at=NOW,
        )
        # Both scores are 1.0 (optimal), so FSI should be 1.0
        assert result.fsi_value == pytest.approx(1.0)

    def test_missing_sources_listed_correctly(self):
        result = calculate_fsi(
            location=LOCATION, sst=28.5, ndvi=0.5, calculated_at=NOW,
        )
        expected_missing = sorted(["chl_a", "depth", "lunar", "season"])
        assert result.data_completeness.missing_sources == expected_missing

    def test_missing_source_component_scores_zero(self):
        """Component scores for missing sources should be 0.0."""
        result = calculate_fsi(location=LOCATION, sst=28.5, calculated_at=NOW)
        assert result.component_scores.chl_a_score == 0.0
        assert result.component_scores.depth_score == 0.0
        assert result.component_scores.lunar_score == 0.0
        assert result.component_scores.ndvi_score == 0.0
        assert result.component_scores.season_score == 0.0

    def test_partial_data_fsi_equals_renormalised_sum(self):
        """Verify the re-normalised weighted sum for a partial input."""
        # sst=28.5 → score 1.0, depth=20.0 → score 1.0
        # weights: sst=0.25, depth=0.15 → sum=0.40
        # normalised: sst=0.625, depth=0.375
        # FSI = 0.625*1.0 + 0.375*1.0 = 1.0
        result = calculate_fsi(
            location=LOCATION, sst=28.5, depth=20.0, calculated_at=NOW,
        )
        assert result.fsi_value == pytest.approx(1.0)

    def test_partial_data_mixed_scores(self):
        """Verify re-normalised sum with different score values."""
        # sst=22.0 → score 0.5, chl_a=2.0 → score 1.0
        # weights: sst=0.25, chl_a=0.25 → sum=0.50
        # normalised: sst=0.5, chl_a=0.5
        # FSI = 0.5*0.5 + 0.5*1.0 = 0.75
        result = calculate_fsi(
            location=LOCATION, sst=22.0, chl_a=2.0, calculated_at=NOW,
        )
        assert result.fsi_value == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# No data sources → error
# ---------------------------------------------------------------------------


class TestNoDataError:
    def test_no_sources_raises_value_error(self):
        with pytest.raises(ValueError, match="no data sources"):
            calculate_fsi(location=LOCATION, calculated_at=NOW)

    def test_all_none_raises_value_error(self):
        with pytest.raises(ValueError, match="no data sources"):
            calculate_fsi(
                location=LOCATION,
                sst=None,
                chl_a=None,
                depth=None,
                lunar_phase=None,
                ndvi=None,
                season=None,
                calculated_at=NOW,
            )


# ---------------------------------------------------------------------------
# Zone classification via calculate_fsi
# ---------------------------------------------------------------------------


class TestZoneViaCalculateFSI:
    """Verify zone classification is consistent with FSI value."""

    def test_green_zone_result(self):
        result = calculate_fsi(**_full_kwargs(
            sst=28.5, chl_a=2.0, depth=20.0,
            lunar_phase=0.0, ndvi=1.0, season=SEASON_DRY,
        ))
        assert result.zone == FSIZone.GREEN
        assert result.fsi_value > 0.7

    def test_red_zone_result(self):
        result = calculate_fsi(**_full_kwargs(
            sst=5.0, chl_a=0.0, depth=0.0,
            lunar_phase=1.0, ndvi=-1.0, season=SEASON_MONSOON,
        ))
        assert result.zone == FSIZone.RED
        assert result.fsi_value < 0.4

    def test_zone_matches_fsi_value(self):
        """Zone classification must be consistent with the FSI value."""
        result = calculate_fsi(**_full_kwargs())
        fsi = result.fsi_value
        if fsi > 0.7:
            assert result.zone == FSIZone.GREEN
        elif fsi >= 0.4:
            assert result.zone == FSIZone.YELLOW
        else:
            assert result.zone == FSIZone.RED


# ---------------------------------------------------------------------------
# Default calculated_at
# ---------------------------------------------------------------------------


class TestDefaultCalculatedAt:
    def test_default_calculated_at_is_set(self):
        result = calculate_fsi(location=LOCATION, sst=28.5)
        assert isinstance(result.calculated_at, datetime)
