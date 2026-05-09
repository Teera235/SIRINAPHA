"""
Unit tests for the Restoration Site Analyzer module.

Tests cover site analysis, CO2 potential calculation, survival rate
estimation, site ranking, area conversion, and database storage.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.6
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

_sa = importlib.import_module("lambda.restoration_planner.site_analyzer")
_models = importlib.import_module("lambda.shared.models")

analyze_site = _sa.analyze_site
rank_sites = _sa.rank_sites
analyze_and_rank_sites = _sa.analyze_and_rank_sites
calculate_co2_potential = _sa.calculate_co2_potential
estimate_survival_rate = _sa.estimate_survival_rate
sq_meters_to_rai = _sa.sq_meters_to_rai
store_restoration_sites = _sa.store_restoration_sites
BASELINE_SEQUESTRATION_RATE = _sa.BASELINE_SEQUESTRATION_RATE

RestorationSite = _models.RestorationSite
NDVITimeSeries = _models.NDVITimeSeries
SoilData = _models.SoilData
TidalData = _models.TidalData

_PATCH_PREFIX = "lambda.restoration_planner.site_analyzer"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ndvi_history(values: list[float]) -> NDVITimeSeries:
    """Create an NDVITimeSeries with dummy timestamps."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    timestamps = [
        datetime(2024, 1, 1 + i, tzinfo=timezone.utc) for i in range(len(values))
    ]
    return NDVITimeSeries(timestamps=timestamps, values=values)


def _make_ideal_soil() -> SoilData:
    return SoilData(type="clay-loam", ph=7.0, salinity=20.0)


def _make_ideal_tidal() -> TidalData:
    return TidalData(min_m=0.3, max_m=2.5, mean_m=1.5)


def _make_site(
    site_id: str = "site-1",
    area_rai: float = 100.0,
    ndvi_values: list[float] | None = None,
    soil: SoilData | None = None,
    tidal: TidalData | None = None,
) -> RestorationSite:
    """Create a RestorationSite via analyze_site with sensible defaults."""
    if ndvi_values is None:
        ndvi_values = [0.3, 0.35, 0.4]
    if soil is None:
        soil = _make_ideal_soil()
    if tidal is None:
        tidal = _make_ideal_tidal()
    return analyze_site(
        site_id=site_id,
        geometry={"type": "Polygon", "coordinates": [[[100.0, 13.0]]]},
        area_rai=area_rai,
        ndvi_history=_make_ndvi_history(ndvi_values),
        soil_condition=soil,
        tidal_range=tidal,
    )


# ---------------------------------------------------------------------------
# sq_meters_to_rai (Requirement 5.3)
# ---------------------------------------------------------------------------


class TestSqMetersToRai:
    """Tests for area conversion from m² to rai."""

    def test_one_rai(self):
        assert sq_meters_to_rai(1600.0) == pytest.approx(1.0)

    def test_zero(self):
        assert sq_meters_to_rai(0.0) == 0.0

    def test_negative_returns_zero(self):
        assert sq_meters_to_rai(-500.0) == 0.0

    def test_fractional(self):
        assert sq_meters_to_rai(800.0) == pytest.approx(0.5)

    def test_large_area(self):
        assert sq_meters_to_rai(160000.0) == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# calculate_co2_potential (Requirement 5.6)
# ---------------------------------------------------------------------------


class TestCalculateCO2Potential:
    """Tests for CO2 sequestration potential calculation."""

    def test_typical_site(self):
        ndvi = _make_ndvi_history([0.5, 0.5, 0.5])
        co2 = calculate_co2_potential(100.0, ndvi)
        expected = 100.0 * 0.5 * BASELINE_SEQUESTRATION_RATE
        assert co2 == pytest.approx(expected, rel=1e-4)

    def test_zero_area_returns_zero(self):
        ndvi = _make_ndvi_history([0.6])
        assert calculate_co2_potential(0.0, ndvi) == 0.0

    def test_negative_area_returns_zero(self):
        ndvi = _make_ndvi_history([0.6])
        assert calculate_co2_potential(-10.0, ndvi) == 0.0

    def test_empty_ndvi_returns_zero(self):
        ndvi = NDVITimeSeries(timestamps=[], values=[])
        assert calculate_co2_potential(100.0, ndvi) == 0.0

    def test_negative_ndvi_clamped_to_zero(self):
        ndvi = _make_ndvi_history([-0.5, -0.3])
        assert calculate_co2_potential(100.0, ndvi) == 0.0

    def test_co2_always_non_negative(self):
        test_cases = [
            (0.0, [0.0]),
            (100.0, [-1.0]),
            (50.0, [0.01]),
        ]
        for area, vals in test_cases:
            ndvi = _make_ndvi_history(vals)
            co2 = calculate_co2_potential(area, ndvi)
            assert co2 >= 0.0

    def test_monotonically_increasing_with_area(self):
        ndvi = _make_ndvi_history([0.5])
        prev = 0.0
        for area in [10.0, 50.0, 100.0, 500.0]:
            co2 = calculate_co2_potential(area, ndvi)
            assert co2 >= prev
            prev = co2

    def test_high_ndvi_gives_more_co2(self):
        low = calculate_co2_potential(100.0, _make_ndvi_history([0.2]))
        high = calculate_co2_potential(100.0, _make_ndvi_history([0.8]))
        assert high > low


# ---------------------------------------------------------------------------
# estimate_survival_rate (Requirement 5.4)
# ---------------------------------------------------------------------------


class TestEstimateSurvivalRate:
    """Tests for seedling survival rate estimation."""

    def test_ideal_conditions_high_survival(self):
        ndvi = _make_ndvi_history([0.3, 0.35, 0.4])
        soil = _make_ideal_soil()
        tidal = _make_ideal_tidal()
        rate = estimate_survival_rate(ndvi, soil, tidal)
        assert rate >= 0.75  # Should be high for ideal conditions

    def test_survival_in_target_range(self):
        """Survival rate must be in [0.45, 0.85] range."""
        ndvi = _make_ndvi_history([0.3, 0.35, 0.4])
        soil = _make_ideal_soil()
        tidal = _make_ideal_tidal()
        rate = estimate_survival_rate(ndvi, soil, tidal)
        assert 0.45 <= rate <= 0.85

    def test_poor_soil_lower_survival(self):
        ndvi = _make_ndvi_history([0.3, 0.35, 0.4])
        ideal_soil = _make_ideal_soil()
        poor_soil = SoilData(type="sand", ph=3.0, salinity=60.0)
        tidal = _make_ideal_tidal()
        ideal_rate = estimate_survival_rate(ndvi, ideal_soil, tidal)
        poor_rate = estimate_survival_rate(ndvi, poor_soil, tidal)
        assert poor_rate < ideal_rate  # Poor soil → lower survival

    def test_extreme_tidal_lower_survival(self):
        ndvi = _make_ndvi_history([0.3, 0.35, 0.4])
        soil = _make_ideal_soil()
        extreme_tidal = TidalData(min_m=0.0, max_m=10.0, mean_m=7.0)
        rate = estimate_survival_rate(ndvi, soil, extreme_tidal)
        assert rate < 0.85

    def test_empty_ndvi_still_returns_valid_rate(self):
        ndvi = NDVITimeSeries(timestamps=[], values=[])
        soil = _make_ideal_soil()
        tidal = _make_ideal_tidal()
        rate = estimate_survival_rate(ndvi, soil, tidal)
        assert 0.45 <= rate <= 0.85

    def test_worst_case_still_at_minimum(self):
        ndvi = _make_ndvi_history([-0.5])
        poor_soil = SoilData(type="rock", ph=2.0, salinity=70.0)
        bad_tidal = TidalData(min_m=0.0, max_m=15.0, mean_m=10.0)
        rate = estimate_survival_rate(ndvi, poor_soil, bad_tidal)
        assert rate >= 0.45


# ---------------------------------------------------------------------------
# analyze_site (Requirement 5.1)
# ---------------------------------------------------------------------------


class TestAnalyzeSite:
    """Tests for single site analysis."""

    def test_returns_restoration_site(self):
        site = _make_site()
        assert isinstance(site, RestorationSite)

    def test_site_id_preserved(self):
        site = _make_site(site_id="mahachai-01")
        assert site.site_id == "mahachai-01"

    def test_area_preserved(self):
        site = _make_site(area_rai=250.0)
        assert site.area_rai == 250.0

    def test_co2_potential_positive(self):
        site = _make_site(area_rai=100.0, ndvi_values=[0.4, 0.5])
        assert site.carbon_potential_tco2_year > 0

    def test_survival_rate_in_range(self):
        site = _make_site()
        assert 0.45 <= site.expected_survival_rate <= 0.85

    def test_priority_rank_initially_zero(self):
        site = _make_site()
        assert site.priority_rank == 0


# ---------------------------------------------------------------------------
# rank_sites (Requirement 5.2 / Property 11)
# ---------------------------------------------------------------------------


class TestRankSites:
    """Tests for site ranking by carbon potential (descending)."""

    def test_descending_order(self):
        """Sites must be ranked by carbon_potential descending."""
        sites = [
            _make_site("low", area_rai=10.0, ndvi_values=[0.2]),
            _make_site("high", area_rai=500.0, ndvi_values=[0.8]),
            _make_site("mid", area_rai=100.0, ndvi_values=[0.5]),
        ]
        ranked = rank_sites(sites)
        potentials = [s.carbon_potential_tco2_year for s in ranked]
        assert potentials == sorted(potentials, reverse=True)

    def test_ranks_assigned_correctly(self):
        sites = [
            _make_site("a", area_rai=10.0, ndvi_values=[0.2]),
            _make_site("b", area_rai=500.0, ndvi_values=[0.8]),
        ]
        ranked = rank_sites(sites)
        assert ranked[0].priority_rank == 1
        assert ranked[1].priority_rank == 2

    def test_highest_potential_is_rank_1(self):
        sites = [
            _make_site("small", area_rai=10.0, ndvi_values=[0.1]),
            _make_site("large", area_rai=1000.0, ndvi_values=[0.9]),
        ]
        ranked = rank_sites(sites)
        assert ranked[0].site_id == "large"
        assert ranked[0].priority_rank == 1

    def test_empty_list(self):
        ranked = rank_sites([])
        assert ranked == []

    def test_single_site(self):
        sites = [_make_site("only")]
        ranked = rank_sites(sites)
        assert len(ranked) == 1
        assert ranked[0].priority_rank == 1

    def test_equal_potential_stable(self):
        """Sites with equal potential should both get sequential ranks."""
        sites = [
            _make_site("a", area_rai=100.0, ndvi_values=[0.5]),
            _make_site("b", area_rai=100.0, ndvi_values=[0.5]),
        ]
        ranked = rank_sites(sites)
        assert ranked[0].priority_rank == 1
        assert ranked[1].priority_rank == 2

    def test_many_sites(self):
        sites = [
            _make_site(f"site-{i}", area_rai=float(i * 50), ndvi_values=[0.5])
            for i in range(1, 11)
        ]
        ranked = rank_sites(sites)
        potentials = [s.carbon_potential_tco2_year for s in ranked]
        assert potentials == sorted(potentials, reverse=True)
        assert ranked[0].priority_rank == 1
        assert ranked[-1].priority_rank == 10


# ---------------------------------------------------------------------------
# analyze_and_rank_sites
# ---------------------------------------------------------------------------


class TestAnalyzeAndRankSites:
    """Tests for batch analysis and ranking."""

    def test_returns_ranked_list(self):
        configs = [
            {
                "site_id": "a",
                "geometry": {"type": "Polygon", "coordinates": []},
                "area_rai": 50.0,
                "ndvi_history": _make_ndvi_history([0.3]),
                "soil_condition": _make_ideal_soil(),
                "tidal_range": _make_ideal_tidal(),
            },
            {
                "site_id": "b",
                "geometry": {"type": "Polygon", "coordinates": []},
                "area_rai": 200.0,
                "ndvi_history": _make_ndvi_history([0.6]),
                "soil_condition": _make_ideal_soil(),
                "tidal_range": _make_ideal_tidal(),
            },
        ]
        ranked = analyze_and_rank_sites(configs)
        assert len(ranked) == 2
        assert ranked[0].carbon_potential_tco2_year >= ranked[1].carbon_potential_tco2_year
        assert ranked[0].priority_rank == 1

    def test_empty_configs(self):
        ranked = analyze_and_rank_sites([])
        assert ranked == []


# ---------------------------------------------------------------------------
# store_restoration_sites
# ---------------------------------------------------------------------------


class TestStoreRestorationSites:
    """Tests for database storage of restoration sites."""

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_into_restoration_sites_table(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        sites = [_make_site("site-1"), _make_site("site-2")]
        ranked = rank_sites(sites)
        result = store_restoration_sites(ranked)

        mock_client.table.assert_called_once_with("restoration_sites")
        assert "2" in result

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_row_contains_correct_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        sites = [_make_site("site-42", area_rai=200.0)]
        ranked = rank_sites(sites)
        store_restoration_sites(ranked)

        insert_call = mock_client.table.return_value.insert
        rows = insert_call.call_args[0][0]
        row = rows[0]
        assert row["site_id"] == "site-42"
        assert row["area_rai"] == 200.0
        assert row["priority_rank"] == 1
        assert "carbon_potential" in row
        assert "expected_survival_rate" in row
        assert "created_at" in row

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_returns_confirmation_string(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        sites = [_make_site("s1")]
        ranked = rank_sites(sites)
        result = store_restoration_sites(ranked)

        assert isinstance(result, str)
        assert "1" in result
