"""
Unit tests for Yield Predictor — revenue_forecast module.

Covers:
  • Daily revenue estimation from species predictions
  • 7-day and 30-day forecast generation
  • Confidence interval invariant: confidence_lower ≤ confidence_upper
  • Market price lookup with fallback

Requirements: 4.3, 4.4
"""

from __future__ import annotations

import importlib

import pytest

_rf = importlib.import_module("lambda.yield_predictor.revenue_forecast")
get_species_price = _rf.get_species_price
estimate_daily_revenue = _rf.estimate_daily_revenue
generate_revenue_forecasts = _rf.generate_revenue_forecasts
DEFAULT_MARKET_PRICES = _rf.DEFAULT_MARKET_PRICES
DEFAULT_PRICE_PER_KG = _rf.DEFAULT_PRICE_PER_KG

_models = importlib.import_module("lambda.shared.models")
SpeciesPrediction = _models.SpeciesPrediction
RevenueForecast = _models.RevenueForecast


# ---------------------------------------------------------------------------
# get_species_price
# ---------------------------------------------------------------------------


class TestGetSpeciesPrice:
    def test_known_species(self):
        assert get_species_price("กุ้ง") == 250.0

    def test_unknown_species_uses_default(self):
        assert get_species_price("ปลาไม่รู้จัก") == DEFAULT_PRICE_PER_KG

    def test_custom_prices(self):
        custom = {"กุ้ง": 300.0}
        assert get_species_price("กุ้ง", custom) == 300.0

    def test_custom_prices_fallback(self):
        custom = {"กุ้ง": 300.0}
        assert get_species_price("ปลาทู", custom) == DEFAULT_PRICE_PER_KG


# ---------------------------------------------------------------------------
# estimate_daily_revenue
# ---------------------------------------------------------------------------


class TestEstimateDailyRevenue:
    def test_single_species(self):
        preds = [SpeciesPrediction(species_name="กุ้ง", estimated_catch_kg=10.0, confidence=0.8)]
        revenue = estimate_daily_revenue(preds)
        assert revenue == pytest.approx(10.0 * 250.0)

    def test_multiple_species(self):
        preds = [
            SpeciesPrediction(species_name="กุ้ง", estimated_catch_kg=10.0, confidence=0.8),
            SpeciesPrediction(species_name="ปลาทู", estimated_catch_kg=20.0, confidence=0.7),
        ]
        revenue = estimate_daily_revenue(preds)
        expected = 10.0 * 250.0 + 20.0 * 80.0
        assert revenue == pytest.approx(expected)

    def test_empty_predictions(self):
        assert estimate_daily_revenue([]) == 0.0

    def test_zero_catch(self):
        preds = [SpeciesPrediction(species_name="กุ้ง", estimated_catch_kg=0.0, confidence=0.8)]
        assert estimate_daily_revenue(preds) == 0.0

    def test_negative_catch_treated_as_zero(self):
        preds = [SpeciesPrediction(species_name="กุ้ง", estimated_catch_kg=-5.0, confidence=0.8)]
        assert estimate_daily_revenue(preds) == 0.0


# ---------------------------------------------------------------------------
# generate_revenue_forecasts
# ---------------------------------------------------------------------------


class TestGenerateRevenueForecasts:
    def _sample_predictions(self):
        return [
            SpeciesPrediction(species_name="กุ้ง", estimated_catch_kg=10.0, confidence=0.8),
            SpeciesPrediction(species_name="ปลาทู", estimated_catch_kg=20.0, confidence=0.7),
        ]

    def test_returns_two_forecasts(self):
        f7, f30 = generate_revenue_forecasts(self._sample_predictions())
        assert isinstance(f7, RevenueForecast)
        assert isinstance(f30, RevenueForecast)

    def test_7day_revenue(self):
        preds = self._sample_predictions()
        daily = estimate_daily_revenue(preds)
        f7, _ = generate_revenue_forecasts(preds)
        assert f7.estimated_revenue_thb == pytest.approx(daily * 7)

    def test_30day_revenue(self):
        preds = self._sample_predictions()
        daily = estimate_daily_revenue(preds)
        _, f30 = generate_revenue_forecasts(preds)
        assert f30.estimated_revenue_thb == pytest.approx(daily * 30)

    def test_confidence_lower_le_upper_7day(self):
        """confidence_lower ≤ confidence_upper for 7-day (Requirement 4.4)."""
        f7, _ = generate_revenue_forecasts(self._sample_predictions())
        assert f7.confidence_lower <= f7.confidence_upper

    def test_confidence_lower_le_upper_30day(self):
        """confidence_lower ≤ confidence_upper for 30-day (Requirement 4.4)."""
        _, f30 = generate_revenue_forecasts(self._sample_predictions())
        assert f30.confidence_lower <= f30.confidence_upper

    def test_30day_wider_than_7day(self):
        """30-day forecast should have a wider confidence interval."""
        f7, f30 = generate_revenue_forecasts(self._sample_predictions())
        spread_7 = f7.confidence_upper - f7.confidence_lower
        spread_30 = f30.confidence_upper - f30.confidence_lower
        assert spread_30 > spread_7

    def test_empty_predictions_zero_revenue(self):
        f7, f30 = generate_revenue_forecasts([])
        assert f7.estimated_revenue_thb == 0.0
        assert f30.estimated_revenue_thb == 0.0

    def test_non_negative_confidence_bounds(self):
        f7, f30 = generate_revenue_forecasts(self._sample_predictions())
        assert f7.confidence_lower >= 0.0
        assert f7.confidence_upper >= 0.0
        assert f30.confidence_lower >= 0.0
        assert f30.confidence_upper >= 0.0

    def test_custom_spread(self):
        preds = self._sample_predictions()
        daily = estimate_daily_revenue(preds)
        f7, f30 = generate_revenue_forecasts(
            preds,
            confidence_spread_7day=0.10,
            confidence_spread_30day=0.20,
        )
        expected_7 = daily * 7
        assert f7.confidence_lower == pytest.approx(expected_7 * 0.90)
        assert f7.confidence_upper == pytest.approx(expected_7 * 1.10)
