"""
Blue Carbon MRV Calculator — CO2 sequestration and revenue sharing.

Computes CO2 sequestration (tCO2/year) from NDVI and mangrove area,
calculates revenue sharing among stakeholders, and generates monthly
and annual Blue Carbon reports stored in the ``carbon_reports`` table.

Revenue sharing breakdown (Requirement 8.5):
- Private sector: 63%
- Cooperative: 20%
- Government: 10%
- MRV fee: 7%

Requirements: 8.1, 8.2, 8.3, 8.5
"""

from __future__ import annotations

import importlib as _il
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

_models = _il.import_module("lambda.shared.models")

CarbonReport = _models.CarbonReport
RevenueSharing = _models.RevenueSharing

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Revenue sharing percentages (Requirement 8.5)
PRIVATE_SECTOR_SHARE = 0.63  # 63%
COOPERATIVE_SHARE = 0.20     # 20%
GOVERNMENT_SHARE = 0.10      # 10%
MRV_FEE_SHARE = 0.07         # 7%

# Carbon sequestration parameters
# Baseline sequestration rate for healthy mangroves: ~7.0 tCO2/rai/year
# (based on literature for Thai mangrove ecosystems)
BASELINE_SEQUESTRATION_RATE = 7.0  # tCO2 per rai per year at NDVI = 1.0

# NDVI below this threshold contributes no carbon sequestration
NDVI_MIN_THRESHOLD = 0.0


def get_supabase_client():
    """Lazy import to avoid hard dependency at module load time."""
    _sb = _il.import_module("lambda.shared.supabase_client")
    return _sb.get_supabase_client()


# ---------------------------------------------------------------------------
# CO2 Sequestration Calculation (Requirement 8.1)
# ---------------------------------------------------------------------------


def calculate_co2_sequestration(area_rai: float, avg_ndvi: float) -> float:
    """Compute annual CO2 sequestration (tCO2/year) from mangrove area and NDVI.

    The calculation uses a linear model where CO2 sequestration is
    proportional to both the area and the NDVI value (as a proxy for
    mangrove health/density). NDVI values at or below zero contribute
    no sequestration.

    Formula: tCO2 = area_rai × max(0, avg_ndvi) × BASELINE_SEQUESTRATION_RATE

    Properties:
    - CO2 ≥ 0 for all valid inputs
    - Monotonically increasing with area when NDVI is constant (and > 0)
    - Monotonically increasing with NDVI when area is constant (and > 0)

    Parameters
    ----------
    area_rai:
        Mangrove area in Thai rai units. Must be ≥ 0.
    avg_ndvi:
        Average NDVI value for the area. Typically in [-1.0, 1.0].

    Returns
    -------
    float
        Estimated CO2 sequestration in tCO2/year. Always ≥ 0.
    """
    if area_rai < 0:
        area_rai = 0.0

    # NDVI at or below threshold contributes no sequestration
    effective_ndvi = max(NDVI_MIN_THRESHOLD, avg_ndvi)

    co2 = area_rai * effective_ndvi * BASELINE_SEQUESTRATION_RATE
    return co2


# ---------------------------------------------------------------------------
# Revenue Sharing Calculation (Requirement 8.5)
# ---------------------------------------------------------------------------


def calculate_revenue_sharing(total_revenue: float) -> RevenueSharing:
    """Split carbon credit revenue among stakeholders.

    Shares (Requirement 8.5):
    - Private sector: 63%
    - Cooperative: 20%
    - Government: 10%
    - MRV fee: 7%

    The shares sum to exactly 100% of the total revenue (within
    floating-point tolerance).

    Parameters
    ----------
    total_revenue:
        Total carbon credit revenue in THB. Should be ≥ 0.

    Returns
    -------
    RevenueSharing
        Breakdown of revenue among the four stakeholder groups.
    """
    if total_revenue < 0:
        total_revenue = 0.0

    return RevenueSharing(
        private_sector=round(total_revenue * PRIVATE_SECTOR_SHARE, 2),
        cooperative=round(total_revenue * COOPERATIVE_SHARE, 2),
        government=round(total_revenue * GOVERNMENT_SHARE, 2),
        mrv_fee=round(total_revenue * MRV_FEE_SHARE, 2),
    )


# ---------------------------------------------------------------------------
# Report Generation (Requirement 8.2)
# ---------------------------------------------------------------------------

# Approximate carbon credit price in THB per tCO2
# (used for revenue estimation in reports)
DEFAULT_CARBON_PRICE_THB = 300.0  # THB per tCO2


def generate_carbon_report(
    site_id: str,
    period_start: date,
    period_end: date,
    area_rai: float,
    avg_ndvi: float,
    carbon_price_thb: float = DEFAULT_CARBON_PRICE_THB,
) -> CarbonReport:
    """Generate a Blue Carbon MRV report for a given period.

    Calculates CO2 sequestration from area and NDVI, estimates revenue
    based on carbon credit pricing, and computes the revenue sharing
    breakdown.

    Parameters
    ----------
    site_id:
        Identifier for the restoration/monitoring site.
    period_start:
        Start date of the reporting period.
    period_end:
        End date of the reporting period.
    area_rai:
        Total mangrove area in rai.
    avg_ndvi:
        Average NDVI for the area during the period.
    carbon_price_thb:
        Price per tCO2 in Thai Baht. Defaults to 300 THB/tCO2.

    Returns
    -------
    CarbonReport
        A complete Blue Carbon report with CO2 calculation and
        revenue sharing breakdown.
    """
    # Calculate CO2 sequestration
    total_co2 = calculate_co2_sequestration(area_rai, avg_ndvi)

    # Scale CO2 by the fraction of the year covered by the period
    days_in_period = (period_end - period_start).days
    if days_in_period <= 0:
        days_in_period = 1
    annual_fraction = days_in_period / 365.0
    period_co2 = total_co2 * annual_fraction

    # Estimate revenue and calculate sharing
    total_revenue = period_co2 * carbon_price_thb
    revenue_sharing = calculate_revenue_sharing(total_revenue)

    report = CarbonReport(
        period={"start": period_start, "end": period_end},
        total_area_rai=area_rai,
        avg_ndvi=avg_ndvi,
        total_co2_tons=round(period_co2, 4),
        revenue_sharing=revenue_sharing,
    )

    logger.info(
        "Generated carbon report for site %s: %.2f tCO2, %.2f THB revenue "
        "(period %s to %s)",
        site_id,
        period_co2,
        total_revenue,
        period_start.isoformat(),
        period_end.isoformat(),
    )

    return report


# ---------------------------------------------------------------------------
# Database Storage (Requirement 8.3)
# ---------------------------------------------------------------------------


def store_carbon_report(report: CarbonReport, site_id: str) -> str:
    """Persist a Blue Carbon report to the ``carbon_reports`` table.

    Parameters
    ----------
    report:
        The carbon report to store.
    site_id:
        The restoration site ID (foreign key to ``restoration_sites``).

    Returns
    -------
    str
        Confirmation message with stored report details.
    """
    revenue_sharing_json = {
        "private_sector": report.revenue_sharing.private_sector,
        "cooperative": report.revenue_sharing.cooperative,
        "government": report.revenue_sharing.government,
        "mrv_fee": report.revenue_sharing.mrv_fee,
    }

    row = {
        "site_id": site_id,
        "period_start": report.period["start"].isoformat(),
        "period_end": report.period["end"].isoformat(),
        "total_area_rai": report.total_area_rai,
        "avg_ndvi": report.avg_ndvi,
        "total_co2_tons": report.total_co2_tons,
        "revenue_sharing": revenue_sharing_json,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    client = get_supabase_client()
    client.table("carbon_reports").insert(row).execute()

    logger.info(
        "Stored carbon report for site %s (period %s to %s, %.2f tCO2)",
        site_id,
        report.period["start"].isoformat(),
        report.period["end"].isoformat(),
        report.total_co2_tons,
    )

    return (
        f"Stored carbon report for site {site_id}: "
        f"{report.total_co2_tons:.2f} tCO2, "
        f"period {report.period['start']} to {report.period['end']}"
    )
