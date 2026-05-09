"""
Yield Predictor — Revenue Forecasting

Combines species-level catch predictions with market price data to generate
7-day and 30-day revenue forecasts with confidence intervals.

Invariant: ``confidence_lower ≤ confidence_upper`` always holds.

Requirements: 4.3, 4.4
"""

from __future__ import annotations

import importlib as _il
from typing import Dict, List, Optional

_models = _il.import_module("lambda.shared.models")
SpeciesPrediction = _models.SpeciesPrediction
RevenueForecast = _models.RevenueForecast

# ---------------------------------------------------------------------------
# Market Prices (THB per kg) — Thai commercial species
# ---------------------------------------------------------------------------

# Default market prices for common Thai species.
# In production these would come from a database or external API.
DEFAULT_MARKET_PRICES: Dict[str, float] = {
    "กุ้ง": 250.0,        # Shrimp — ~250 THB/kg
    "ปลากะพง": 180.0,    # Sea bass — ~180 THB/kg
    "ปลาทู": 80.0,       # Short mackerel — ~80 THB/kg
    "ปูม้า": 350.0,       # Blue swimming crab — ~350 THB/kg
    "หมึก": 200.0,        # Squid — ~200 THB/kg
}

# Default price for species not in the lookup table
DEFAULT_PRICE_PER_KG = 120.0

# Confidence interval scaling factors
# The 7-day forecast is more certain than the 30-day forecast.
CONFIDENCE_SPREAD_7DAY = 0.15   # ±15% of estimated revenue
CONFIDENCE_SPREAD_30DAY = 0.30  # ±30% of estimated revenue


# ---------------------------------------------------------------------------
# Revenue Calculation
# ---------------------------------------------------------------------------


def get_species_price(
    species_name: str,
    market_prices: Optional[Dict[str, float]] = None,
) -> float:
    """Look up the market price for a species.

    Falls back to :data:`DEFAULT_PRICE_PER_KG` if the species is unknown.
    """
    prices = market_prices or DEFAULT_MARKET_PRICES
    return prices.get(species_name, DEFAULT_PRICE_PER_KG)


def estimate_daily_revenue(
    predictions: List[SpeciesPrediction],
    market_prices: Optional[Dict[str, float]] = None,
) -> float:
    """Estimate total daily revenue from species predictions.

    Revenue = Σ (estimated_catch_kg × price_per_kg) for each species.
    """
    total = 0.0
    for pred in predictions:
        price = get_species_price(pred.species_name, market_prices)
        total += max(0.0, pred.estimated_catch_kg) * price
    return total


def _build_forecast(
    daily_revenue: float,
    days: int,
    spread: float,
) -> RevenueForecast:
    """Build a :class:`RevenueForecast` for a given number of days.

    The confidence interval is computed as::

        lower = estimated × (1 - spread)
        upper = estimated × (1 + spread)

    The ``confidence_lower ≤ confidence_upper`` invariant is enforced.
    """
    estimated = daily_revenue * days
    lower = estimated * (1.0 - spread)
    upper = estimated * (1.0 + spread)

    # Ensure non-negative
    lower = max(0.0, lower)
    upper = max(0.0, upper)

    # Enforce invariant (Property 20 / Requirement 4.4)
    if lower > upper:
        lower, upper = upper, lower

    return RevenueForecast(
        estimated_revenue_thb=estimated,
        confidence_lower=lower,
        confidence_upper=upper,
    )


def generate_revenue_forecasts(
    predictions: List[SpeciesPrediction],
    market_prices: Optional[Dict[str, float]] = None,
    confidence_spread_7day: float = CONFIDENCE_SPREAD_7DAY,
    confidence_spread_30day: float = CONFIDENCE_SPREAD_30DAY,
) -> tuple[RevenueForecast, RevenueForecast]:
    """Generate 7-day and 30-day revenue forecasts.

    Parameters
    ----------
    predictions : list[SpeciesPrediction]
        Species-level catch predictions (daily estimates).
    market_prices : dict | None
        Optional override for species market prices.
    confidence_spread_7day : float
        Fractional spread for the 7-day confidence interval.
    confidence_spread_30day : float
        Fractional spread for the 30-day confidence interval.

    Returns
    -------
    tuple[RevenueForecast, RevenueForecast]
        ``(forecast_7day, forecast_30day)`` — both guaranteed to satisfy
        ``confidence_lower ≤ confidence_upper``.
    """
    daily_revenue = estimate_daily_revenue(predictions, market_prices)

    forecast_7day = _build_forecast(daily_revenue, 7, confidence_spread_7day)
    forecast_30day = _build_forecast(daily_revenue, 30, confidence_spread_30day)

    return forecast_7day, forecast_30day
