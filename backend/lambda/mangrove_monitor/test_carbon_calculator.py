"""
Unit tests for the Blue Carbon MRV calculator module.

Tests cover CO2 sequestration calculation, revenue sharing, report
generation, and database storage of carbon reports.

Requirements: 8.1, 8.2, 8.3, 8.5
"""

from __future__ import annotations

import importlib
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

_cc = importlib.import_module("lambda.mangrove_monitor.carbon_calculator")
_models = importlib.import_module("lambda.shared.models")

calculate_co2_sequestration = _cc.calculate_co2_sequestration
calculate_revenue_sharing = _cc.calculate_revenue_sharing
generate_carbon_report = _cc.generate_carbon_report
store_carbon_report = _cc.store_carbon_report
BASELINE_SEQUESTRATION_RATE = _cc.BASELINE_SEQUESTRATION_RATE

CarbonReport = _models.CarbonReport
RevenueSharing = _models.RevenueSharing

_PATCH_PREFIX = "lambda.mangrove_monitor.carbon_calculator"


# ---------------------------------------------------------------------------
# calculate_co2_sequestration
# ---------------------------------------------------------------------------


class TestCalculateCO2Sequestration:
    """Tests for CO2 sequestration calculation (Requirement 8.1)."""

    def test_typical_healthy_mangrove(self):
        # 100 rai with healthy NDVI of 0.7
        co2 = calculate_co2_sequestration(area_rai=100.0, avg_ndvi=0.7)
        expected = 100.0 * 0.7 * BASELINE_SEQUESTRATION_RATE
        assert co2 == pytest.approx(expected, rel=1e-6)

    def test_perfect_ndvi(self):
        # NDVI = 1.0 → maximum sequestration
        co2 = calculate_co2_sequestration(area_rai=50.0, avg_ndvi=1.0)
        expected = 50.0 * 1.0 * BASELINE_SEQUESTRATION_RATE
        assert co2 == pytest.approx(expected, rel=1e-6)

    def test_zero_area_returns_zero(self):
        co2 = calculate_co2_sequestration(area_rai=0.0, avg_ndvi=0.8)
        assert co2 == 0.0

    def test_zero_ndvi_returns_zero(self):
        co2 = calculate_co2_sequestration(area_rai=100.0, avg_ndvi=0.0)
        assert co2 == 0.0

    def test_negative_ndvi_returns_zero(self):
        # Negative NDVI (water body) → no sequestration
        co2 = calculate_co2_sequestration(area_rai=100.0, avg_ndvi=-0.5)
        assert co2 == 0.0

    def test_negative_area_treated_as_zero(self):
        co2 = calculate_co2_sequestration(area_rai=-10.0, avg_ndvi=0.7)
        assert co2 == 0.0

    def test_co2_always_non_negative(self):
        """CO2 must be ≥ 0 for any combination of inputs."""
        test_cases = [
            (0.0, 0.0),
            (100.0, -1.0),
            (-5.0, 0.5),
            (0.0, -0.3),
            (50.0, 0.01),
        ]
        for area, ndvi in test_cases:
            co2 = calculate_co2_sequestration(area, ndvi)
            assert co2 >= 0.0, f"CO2={co2} for area={area}, ndvi={ndvi}"

    def test_monotonically_increasing_with_area(self):
        """When NDVI is constant, larger area → more CO2."""
        ndvi = 0.6
        prev_co2 = 0.0
        for area in [10.0, 50.0, 100.0, 500.0, 1000.0]:
            co2 = calculate_co2_sequestration(area, ndvi)
            assert co2 >= prev_co2, (
                f"CO2 should increase with area: {co2} < {prev_co2}"
            )
            prev_co2 = co2

    def test_monotonically_increasing_with_ndvi(self):
        """When area is constant, higher NDVI → more CO2."""
        area = 100.0
        prev_co2 = 0.0
        for ndvi in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            co2 = calculate_co2_sequestration(area, ndvi)
            assert co2 >= prev_co2, (
                f"CO2 should increase with NDVI: {co2} < {prev_co2}"
            )
            prev_co2 = co2

    def test_small_area_small_ndvi(self):
        co2 = calculate_co2_sequestration(area_rai=1.0, avg_ndvi=0.1)
        expected = 1.0 * 0.1 * BASELINE_SEQUESTRATION_RATE
        assert co2 == pytest.approx(expected, rel=1e-6)

    def test_large_area(self):
        co2 = calculate_co2_sequestration(area_rai=10000.0, avg_ndvi=0.5)
        expected = 10000.0 * 0.5 * BASELINE_SEQUESTRATION_RATE
        assert co2 == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# calculate_revenue_sharing
# ---------------------------------------------------------------------------


class TestCalculateRevenueSharing:
    """Tests for revenue sharing calculation (Requirement 8.5)."""

    def test_typical_revenue(self):
        sharing = calculate_revenue_sharing(100000.0)
        assert sharing.private_sector == pytest.approx(63000.0, rel=1e-6)
        assert sharing.cooperative == pytest.approx(20000.0, rel=1e-6)
        assert sharing.government == pytest.approx(10000.0, rel=1e-6)
        assert sharing.mrv_fee == pytest.approx(7000.0, rel=1e-6)

    def test_shares_sum_to_total(self):
        total = 100000.0
        sharing = calculate_revenue_sharing(total)
        total_shares = (
            sharing.private_sector
            + sharing.cooperative
            + sharing.government
            + sharing.mrv_fee
        )
        assert total_shares == pytest.approx(total, rel=1e-4)

    def test_shares_sum_to_total_odd_amount(self):
        total = 12345.67
        sharing = calculate_revenue_sharing(total)
        total_shares = (
            sharing.private_sector
            + sharing.cooperative
            + sharing.government
            + sharing.mrv_fee
        )
        # Due to rounding, allow small tolerance
        assert total_shares == pytest.approx(total, abs=0.04)

    def test_zero_revenue(self):
        sharing = calculate_revenue_sharing(0.0)
        assert sharing.private_sector == 0.0
        assert sharing.cooperative == 0.0
        assert sharing.government == 0.0
        assert sharing.mrv_fee == 0.0

    def test_negative_revenue_treated_as_zero(self):
        sharing = calculate_revenue_sharing(-5000.0)
        assert sharing.private_sector == 0.0
        assert sharing.cooperative == 0.0
        assert sharing.government == 0.0
        assert sharing.mrv_fee == 0.0

    def test_small_revenue(self):
        sharing = calculate_revenue_sharing(1.0)
        assert sharing.private_sector == pytest.approx(0.63, abs=0.01)
        assert sharing.cooperative == pytest.approx(0.20, abs=0.01)
        assert sharing.government == pytest.approx(0.10, abs=0.01)
        assert sharing.mrv_fee == pytest.approx(0.07, abs=0.01)

    def test_large_revenue(self):
        sharing = calculate_revenue_sharing(10_000_000.0)
        assert sharing.private_sector == pytest.approx(6_300_000.0, rel=1e-6)
        assert sharing.cooperative == pytest.approx(2_000_000.0, rel=1e-6)
        assert sharing.government == pytest.approx(1_000_000.0, rel=1e-6)
        assert sharing.mrv_fee == pytest.approx(700_000.0, rel=1e-6)

    def test_returns_revenue_sharing_dataclass(self):
        sharing = calculate_revenue_sharing(1000.0)
        assert isinstance(sharing, RevenueSharing)

    def test_percentages_correct(self):
        """Verify each share is the correct percentage of total."""
        total = 50000.0
        sharing = calculate_revenue_sharing(total)
        assert sharing.private_sector / total == pytest.approx(0.63, abs=0.001)
        assert sharing.cooperative / total == pytest.approx(0.20, abs=0.001)
        assert sharing.government / total == pytest.approx(0.10, abs=0.001)
        assert sharing.mrv_fee / total == pytest.approx(0.07, abs=0.001)


# ---------------------------------------------------------------------------
# generate_carbon_report
# ---------------------------------------------------------------------------


class TestGenerateCarbonReport:
    """Tests for Blue Carbon report generation (Requirement 8.2)."""

    def test_generates_annual_report(self):
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            area_rai=200.0,
            avg_ndvi=0.65,
        )
        assert isinstance(report, CarbonReport)
        assert report.total_area_rai == 200.0
        assert report.avg_ndvi == 0.65
        assert report.total_co2_tons > 0
        assert report.period["start"] == date(2024, 1, 1)
        assert report.period["end"] == date(2024, 12, 31)

    def test_generates_monthly_report(self):
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 3, 1),
            period_end=date(2024, 3, 31),
            area_rai=100.0,
            avg_ndvi=0.7,
        )
        # Monthly CO2 should be roughly 1/12 of annual
        annual_co2 = calculate_co2_sequestration(100.0, 0.7)
        monthly_fraction = 30 / 365.0
        expected_co2 = annual_co2 * monthly_fraction
        assert report.total_co2_tons == pytest.approx(expected_co2, rel=0.01)

    def test_annual_report_co2_matches_full_year(self):
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            area_rai=100.0,
            avg_ndvi=0.5,
        )
        annual_co2 = calculate_co2_sequestration(100.0, 0.5)
        # 365 days / 365 = 1.0 fraction
        expected = annual_co2 * (365 / 365.0)
        assert report.total_co2_tons == pytest.approx(expected, rel=0.01)

    def test_report_includes_revenue_sharing(self):
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            area_rai=100.0,
            avg_ndvi=0.6,
        )
        assert isinstance(report.revenue_sharing, RevenueSharing)
        total_shares = (
            report.revenue_sharing.private_sector
            + report.revenue_sharing.cooperative
            + report.revenue_sharing.government
            + report.revenue_sharing.mrv_fee
        )
        # Revenue = CO2 × price, shares should sum to that
        assert total_shares > 0

    def test_zero_area_report(self):
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 6, 30),
            area_rai=0.0,
            avg_ndvi=0.7,
        )
        assert report.total_co2_tons == 0.0
        assert report.revenue_sharing.private_sector == 0.0

    def test_negative_ndvi_report(self):
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            area_rai=100.0,
            avg_ndvi=-0.3,
        )
        assert report.total_co2_tons == 0.0

    def test_custom_carbon_price(self):
        report_default = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            area_rai=100.0,
            avg_ndvi=0.5,
        )
        report_high = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            area_rai=100.0,
            avg_ndvi=0.5,
            carbon_price_thb=600.0,
        )
        # CO2 should be the same
        assert report_default.total_co2_tons == report_high.total_co2_tons
        # Revenue should be double
        assert report_high.revenue_sharing.private_sector == pytest.approx(
            report_default.revenue_sharing.private_sector * 2.0, rel=0.01
        )

    def test_same_start_end_date(self):
        """Edge case: period of 0 days should still produce a valid report."""
        report = generate_carbon_report(
            site_id="site-1",
            period_start=date(2024, 6, 15),
            period_end=date(2024, 6, 15),
            area_rai=100.0,
            avg_ndvi=0.5,
        )
        assert isinstance(report, CarbonReport)
        # 0 days → treated as 1 day
        assert report.total_co2_tons >= 0


# ---------------------------------------------------------------------------
# store_carbon_report
# ---------------------------------------------------------------------------


class TestStoreCarbonReport:
    """Tests for storing carbon reports in the database (Requirement 8.3)."""

    def _make_report(
        self,
        area_rai: float = 100.0,
        avg_ndvi: float = 0.6,
        co2: float = 420.0,
    ) -> CarbonReport:
        return CarbonReport(
            period={"start": date(2024, 1, 1), "end": date(2024, 12, 31)},
            total_area_rai=area_rai,
            avg_ndvi=avg_ndvi,
            total_co2_tons=co2,
            revenue_sharing=RevenueSharing(
                private_sector=79380.0,
                cooperative=25200.0,
                government=12600.0,
                mrv_fee=8820.0,
            ),
        )

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_inserts_into_carbon_reports_table(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        report = self._make_report()
        result = store_carbon_report(report, site_id="site-42")

        mock_client.table.assert_called_once_with("carbon_reports")
        assert "site-42" in result

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_row_contains_correct_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        report = self._make_report(area_rai=200.0, avg_ndvi=0.7, co2=980.0)
        store_carbon_report(report, site_id="site-1")

        insert_call = mock_client.table.return_value.insert
        rows = insert_call.call_args[0][0]
        row = rows
        assert row["site_id"] == "site-1"
        assert row["total_area_rai"] == 200.0
        assert row["avg_ndvi"] == 0.7
        assert row["total_co2_tons"] == 980.0
        assert row["period_start"] == "2024-01-01"
        assert row["period_end"] == "2024-12-31"

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_revenue_sharing_stored_as_json(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        report = self._make_report()
        store_carbon_report(report, site_id="site-1")

        insert_call = mock_client.table.return_value.insert
        row = insert_call.call_args[0][0]
        rs = row["revenue_sharing"]
        assert "private_sector" in rs
        assert "cooperative" in rs
        assert "government" in rs
        assert "mrv_fee" in rs
        assert rs["private_sector"] == 79380.0

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_generated_at_is_iso_format(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        report = self._make_report()
        store_carbon_report(report, site_id="site-1")

        insert_call = mock_client.table.return_value.insert
        row = insert_call.call_args[0][0]
        # Should be a valid ISO 8601 timestamp
        assert "T" in row["generated_at"]

    @patch(f"{_PATCH_PREFIX}.get_supabase_client")
    def test_returns_confirmation_string(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = None

        report = self._make_report(co2=500.0)
        result = store_carbon_report(report, site_id="site-99")

        assert isinstance(result, str)
        assert "site-99" in result
        assert "500.00" in result
