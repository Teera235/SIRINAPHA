"""
Unit tests for FSI Engine score functions.

Tests cover all five scoring functions: sst_score, chl_a_score, depth_score,
lunar_score, and season_score.  Each test class verifies the optimal range,
linear decay behaviour, boundary values, and the [0, 1] output invariant.

Requirements: 3.2, 3.3, 3.4, 3.5, 3.6
"""

from __future__ import annotations

import importlib

import pytest

_sf = importlib.import_module("lambda.fsi_engine.score_functions")

sst_score = _sf.sst_score
chl_a_score = _sf.chl_a_score
depth_score = _sf.depth_score
lunar_score = _sf.lunar_score
season_score = _sf.season_score

_models = importlib.import_module("lambda.shared.models")
SeasonData = _models.SeasonData


# ---------------------------------------------------------------------------
# sst_score  (Requirement 3.2)
# ---------------------------------------------------------------------------


class TestSSTScore:
    """SST 27-30 °C → 1.0, linear decay ±10 °C outside range."""

    # --- optimal range ---
    def test_optimal_lower_bound(self):
        assert sst_score(27.0) == 1.0

    def test_optimal_upper_bound(self):
        assert sst_score(30.0) == 1.0

    def test_optimal_mid(self):
        assert sst_score(28.5) == 1.0

    # --- below optimal ---
    def test_below_optimal_linear_decay(self):
        # 22 °C → 5 °C below 27 → 1 - 5/10 = 0.5
        assert sst_score(22.0) == pytest.approx(0.5)

    def test_below_optimal_at_zero_boundary(self):
        # 17 °C → 10 °C below 27 → 0.0
        assert sst_score(17.0) == pytest.approx(0.0)

    def test_below_optimal_far_below(self):
        assert sst_score(0.0) == 0.0

    def test_below_optimal_negative(self):
        assert sst_score(-5.0) == 0.0

    # --- above optimal ---
    def test_above_optimal_linear_decay(self):
        # 35 °C → 5 °C above 30 → 1 - 5/10 = 0.5
        assert sst_score(35.0) == pytest.approx(0.5)

    def test_above_optimal_at_zero_boundary(self):
        # 40 °C → 10 °C above 30 → 0.0
        assert sst_score(40.0) == pytest.approx(0.0)

    def test_above_optimal_far_above(self):
        assert sst_score(100.0) == 0.0

    # --- output range ---
    def test_output_always_in_0_1(self):
        for sst in [-50, -10, 0, 10, 17, 22, 27, 28.5, 30, 35, 40, 50, 100]:
            score = sst_score(sst)
            assert 0.0 <= score <= 1.0, f"sst={sst} → {score}"


# ---------------------------------------------------------------------------
# chl_a_score  (Requirement 3.3)
# ---------------------------------------------------------------------------


class TestChlAScore:
    """Chl-a 0.5-5.0 mg/m³ → 1.0, linear decay outside range."""

    # --- optimal range ---
    def test_optimal_lower_bound(self):
        assert chl_a_score(0.5) == 1.0

    def test_optimal_upper_bound(self):
        assert chl_a_score(5.0) == 1.0

    def test_optimal_mid(self):
        assert chl_a_score(2.5) == 1.0

    # --- below optimal ---
    def test_below_optimal_linear_decay(self):
        # 0.25 → 0.25 / 0.5 = 0.5
        assert chl_a_score(0.25) == pytest.approx(0.5)

    def test_below_optimal_at_zero(self):
        assert chl_a_score(0.0) == pytest.approx(0.0)

    def test_below_optimal_negative(self):
        assert chl_a_score(-1.0) == 0.0

    # --- above optimal ---
    def test_above_optimal_linear_decay(self):
        # 12.5 → 1 - (12.5 - 5) / 15 = 1 - 0.5 = 0.5
        assert chl_a_score(12.5) == pytest.approx(0.5)

    def test_above_optimal_at_zero_boundary(self):
        # 20.0 → 1 - (20 - 5) / 15 = 0.0
        assert chl_a_score(20.0) == pytest.approx(0.0)

    def test_above_optimal_far_above(self):
        assert chl_a_score(100.0) == 0.0

    # --- output range ---
    def test_output_always_in_0_1(self):
        for chl in [-5, -1, 0, 0.25, 0.5, 2.5, 5.0, 12.5, 20, 50, 100]:
            score = chl_a_score(chl)
            assert 0.0 <= score <= 1.0, f"chl_a={chl} → {score}"


# ---------------------------------------------------------------------------
# depth_score  (Requirement 3.4)
# ---------------------------------------------------------------------------


class TestDepthScore:
    """Depth 5-50 m → 1.0, linear decay outside range."""

    # --- optimal range ---
    def test_optimal_lower_bound(self):
        assert depth_score(5.0) == 1.0

    def test_optimal_upper_bound(self):
        assert depth_score(50.0) == 1.0

    def test_optimal_mid(self):
        assert depth_score(25.0) == 1.0

    # --- below optimal ---
    def test_below_optimal_linear_decay(self):
        # 2.5 m → 2.5 / 5 = 0.5
        assert depth_score(2.5) == pytest.approx(0.5)

    def test_below_optimal_at_zero(self):
        assert depth_score(0.0) == pytest.approx(0.0)

    def test_below_optimal_negative(self):
        assert depth_score(-10.0) == 0.0

    # --- above optimal ---
    def test_above_optimal_linear_decay(self):
        # 75 m → 1 - (75 - 50) / 50 = 0.5
        assert depth_score(75.0) == pytest.approx(0.5)

    def test_above_optimal_at_zero_boundary(self):
        # 100 m → 1 - (100 - 50) / 50 = 0.0
        assert depth_score(100.0) == pytest.approx(0.0)

    def test_above_optimal_far_above(self):
        assert depth_score(500.0) == 0.0

    # --- output range ---
    def test_output_always_in_0_1(self):
        for d in [-10, 0, 2.5, 5, 25, 50, 75, 100, 200, 500]:
            score = depth_score(d)
            assert 0.0 <= score <= 1.0, f"depth={d} → {score}"


# ---------------------------------------------------------------------------
# lunar_score  (Requirement 3.5)
# ---------------------------------------------------------------------------


class TestLunarScore:
    """New moon (0.0) → 1.0, full moon (1.0) → 0.3, linear."""

    def test_new_moon(self):
        assert lunar_score(0.0) == pytest.approx(1.0)

    def test_full_moon(self):
        assert lunar_score(1.0) == pytest.approx(0.3)

    def test_half_moon(self):
        # 0.5 → 1.0 - 0.7 * 0.5 = 0.65
        assert lunar_score(0.5) == pytest.approx(0.65)

    def test_quarter_moon(self):
        # 0.25 → 1.0 - 0.7 * 0.25 = 0.825
        assert lunar_score(0.25) == pytest.approx(0.825)

    def test_three_quarter_moon(self):
        # 0.75 → 1.0 - 0.7 * 0.75 = 0.475
        assert lunar_score(0.75) == pytest.approx(0.475)

    def test_output_range_at_extremes(self):
        assert 0.0 <= lunar_score(0.0) <= 1.0
        assert 0.0 <= lunar_score(1.0) <= 1.0

    def test_monotonically_decreasing(self):
        """Score should decrease as phase increases."""
        phases = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        scores = [lunar_score(p) for p in phases]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"Not monotonically decreasing at phase={phases[i+1]}"
            )


# ---------------------------------------------------------------------------
# season_score  (Requirement 3.6)
# ---------------------------------------------------------------------------


class TestSeasonScore:
    """Season score based on month and monsoon status."""

    def _make_season(
        self,
        month: int = 3,
        season: str = "dry",
        is_monsoon: bool = False,
    ) -> SeasonData:
        return SeasonData(season=season, month=month, is_monsoon=is_monsoon)

    # --- peak dry season ---
    def test_march_dry_season(self):
        s = self._make_season(month=3, season="dry", is_monsoon=False)
        assert season_score(s) == pytest.approx(0.9)

    def test_april_dry_season(self):
        s = self._make_season(month=4, season="dry", is_monsoon=False)
        assert season_score(s) == pytest.approx(0.9)

    # --- monsoon season ---
    def test_july_monsoon(self):
        s = self._make_season(month=7, season="monsoon", is_monsoon=True)
        # base 0.4 * 0.7 = 0.28
        assert season_score(s) == pytest.approx(0.28)

    def test_august_monsoon(self):
        s = self._make_season(month=8, season="monsoon", is_monsoon=True)
        # base 0.4 * 0.7 = 0.28
        assert season_score(s) == pytest.approx(0.28)

    # --- monsoon penalty applied ---
    def test_monsoon_penalty_reduces_score(self):
        no_monsoon = self._make_season(month=6, is_monsoon=False)
        with_monsoon = self._make_season(month=6, is_monsoon=True)
        assert season_score(with_monsoon) < season_score(no_monsoon)

    def test_monsoon_penalty_factor(self):
        # Month 2 base = 0.8; with monsoon → 0.8 * 0.7 = 0.56
        s = self._make_season(month=2, is_monsoon=True)
        assert season_score(s) == pytest.approx(0.56)

    # --- all months produce valid output ---
    def test_all_months_in_0_1(self):
        for month in range(1, 13):
            for is_monsoon in [False, True]:
                s = self._make_season(month=month, is_monsoon=is_monsoon)
                score = season_score(s)
                assert 0.0 <= score <= 1.0, (
                    f"month={month}, is_monsoon={is_monsoon} → {score}"
                )

    # --- edge: unknown month defaults to 0.5 ---
    def test_unknown_month_defaults(self):
        s = self._make_season(month=13, is_monsoon=False)
        assert season_score(s) == pytest.approx(0.5)

    def test_unknown_month_with_monsoon(self):
        s = self._make_season(month=0, is_monsoon=True)
        # default 0.5 * 0.7 = 0.35
        assert season_score(s) == pytest.approx(0.35)

    # --- transition months ---
    def test_february_good_fishing(self):
        s = self._make_season(month=2, is_monsoon=False)
        assert season_score(s) == pytest.approx(0.8)

    def test_november_moderate(self):
        s = self._make_season(month=11, is_monsoon=False)
        assert season_score(s) == pytest.approx(0.7)

    def test_january_tail_monsoon(self):
        s = self._make_season(month=1, is_monsoon=False)
        assert season_score(s) == pytest.approx(0.6)
