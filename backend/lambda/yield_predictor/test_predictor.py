"""
Unit tests for Yield Predictor — predictor module.

Covers:
  • Feature preprocessing: normalisation, missing-value imputation, pad/trim
  • SageMaker inference with mock endpoint
  • Response parsing (species predictions, confidence intervals)
  • End-to-end predict() with mock SageMaker
  • Confidence interval invariant: confidence_lower ≤ confidence_upper

Requirements: 4.1, 4.2, 4.3, 4.4
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock

import pytest

_pred = importlib.import_module("lambda.yield_predictor.predictor")
_normalise = _pred._normalise
_fill_missing = _pred._fill_missing
_pad_or_trim = _pred._pad_or_trim
preprocess_features = _pred.preprocess_features
invoke_sagemaker = _pred.invoke_sagemaker
parse_species_predictions = _pred.parse_species_predictions
parse_confidence_interval = _pred.parse_confidence_interval
predict = _pred.predict
HISTORY_LENGTH = _pred.HISTORY_LENGTH
DEFAULT_NDVI_AVG = _pred.DEFAULT_NDVI_AVG
DEFAULT_SST_AVG = _pred.DEFAULT_SST_AVG
DEFAULT_CHL_A_AVG = _pred.DEFAULT_CHL_A_AVG
DEFAULT_SPECIES = _pred.DEFAULT_SPECIES

_models = importlib.import_module("lambda.shared.models")
SeasonData = _models.SeasonData
SpeciesPrediction = _models.SpeciesPrediction
ConfidenceInterval = _models.ConfidenceInterval
YieldPrediction = _models.YieldPrediction

# Shared fixtures
SEASON_DRY = SeasonData(season="dry", month=3, is_monsoon=False)
SEASON_MONSOON = SeasonData(season="monsoon", month=8, is_monsoon=True)


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------


class TestNormalise:
    def test_mid_range(self):
        assert _normalise(0.5, 0.0, 1.0) == pytest.approx(0.5)

    def test_min_value(self):
        assert _normalise(0.0, 0.0, 1.0) == pytest.approx(0.0)

    def test_max_value(self):
        assert _normalise(1.0, 0.0, 1.0) == pytest.approx(1.0)

    def test_below_range_clamped(self):
        assert _normalise(-5.0, 0.0, 10.0) == 0.0

    def test_above_range_clamped(self):
        assert _normalise(15.0, 0.0, 10.0) == 1.0

    def test_sst_normalisation(self):
        # SST range 15-35, value 25 → (25-15)/(35-15) = 0.5
        assert _normalise(25.0, 15.0, 35.0) == pytest.approx(0.5)

    def test_equal_min_max(self):
        assert _normalise(5.0, 5.0, 5.0) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# _fill_missing
# ---------------------------------------------------------------------------


class TestFillMissing:
    def test_no_missing(self):
        result = _fill_missing([1.0, 2.0, 3.0], 0.0)
        assert result == [1.0, 2.0, 3.0]

    def test_all_missing_uses_default(self):
        result = _fill_missing([None, None, None], 5.0)
        assert result == [5.0, 5.0, 5.0]

    def test_partial_missing_uses_average(self):
        result = _fill_missing([2.0, None, 4.0], 0.0)
        # Average of valid values = (2+4)/2 = 3.0
        assert result == [2.0, 3.0, 4.0]

    def test_single_valid_value(self):
        result = _fill_missing([None, 10.0, None], 0.0)
        assert result == [10.0, 10.0, 10.0]

    def test_empty_list(self):
        result = _fill_missing([], 5.0)
        assert result == []


# ---------------------------------------------------------------------------
# _pad_or_trim
# ---------------------------------------------------------------------------


class TestPadOrTrim:
    def test_exact_length(self):
        result = _pad_or_trim([1.0, 2.0, 3.0], 3)
        assert result == [1.0, 2.0, 3.0]

    def test_trim_from_front(self):
        result = _pad_or_trim([1.0, 2.0, 3.0, 4.0, 5.0], 3)
        assert result == [3.0, 4.0, 5.0]

    def test_pad_at_front(self):
        result = _pad_or_trim([3.0, 4.0], 4)
        assert result == [3.0, 3.0, 3.0, 4.0]

    def test_empty_list_pads_with_zero(self):
        result = _pad_or_trim([], 3)
        assert result == [0.0, 0.0, 0.0]

    def test_single_element_padded(self):
        result = _pad_or_trim([7.0], 3)
        assert result == [7.0, 7.0, 7.0]


# ---------------------------------------------------------------------------
# preprocess_features
# ---------------------------------------------------------------------------


class TestPreprocessFeatures:
    def test_output_keys(self):
        result = preprocess_features(
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
        )
        assert "ndvi" in result
        assert "sst" in result
        assert "chl_a" in result
        assert "season_encoded" in result
        assert "is_monsoon" in result
        assert "month" in result

    def test_output_lengths(self):
        result = preprocess_features(
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
        )
        assert len(result["ndvi"]) == HISTORY_LENGTH
        assert len(result["sst"]) == HISTORY_LENGTH
        assert len(result["chl_a"]) == HISTORY_LENGTH

    def test_values_normalised_to_0_1(self):
        result = preprocess_features(
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
        )
        for key in ["ndvi", "sst", "chl_a"]:
            for v in result[key]:
                assert 0.0 <= v <= 1.0, f"{key} value {v} out of [0,1]"

    def test_season_encoding_dry(self):
        result = preprocess_features(
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
        )
        assert result["season_encoded"] == 0.0
        assert result["is_monsoon"] == 0.0

    def test_season_encoding_monsoon(self):
        result = preprocess_features(
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_MONSOON,
        )
        assert result["season_encoded"] == 1.0
        assert result["is_monsoon"] == 1.0

    def test_month_normalised(self):
        result = preprocess_features(
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
        )
        assert result["month"] == pytest.approx(3 / 12.0)

    def test_handles_missing_values(self):
        """Missing values should be filled, not cause errors."""
        result = preprocess_features(
            ndvi_history=[None] * 30,
            sst_history=[None] * 30,
            chl_a_history=[None] * 30,
            season=SEASON_DRY,
        )
        assert len(result["ndvi"]) == HISTORY_LENGTH
        # All filled with defaults, then normalised
        for v in result["ndvi"]:
            assert 0.0 <= v <= 1.0

    def test_handles_short_history(self):
        """Short histories should be padded."""
        result = preprocess_features(
            ndvi_history=[0.5] * 10,
            sst_history=[28.0] * 10,
            chl_a_history=[2.0] * 10,
            season=SEASON_DRY,
        )
        assert len(result["ndvi"]) == HISTORY_LENGTH

    def test_handles_long_history(self):
        """Long histories should be trimmed."""
        result = preprocess_features(
            ndvi_history=[0.5] * 60,
            sst_history=[28.0] * 60,
            chl_a_history=[2.0] * 60,
            season=SEASON_DRY,
        )
        assert len(result["ndvi"]) == HISTORY_LENGTH


# ---------------------------------------------------------------------------
# parse_species_predictions
# ---------------------------------------------------------------------------


class TestParseSpeciesPredictions:
    def test_parses_valid_response(self):
        raw = {
            "predictions": [
                {"species_name": "กุ้ง", "estimated_catch_kg": 120.5, "confidence": 0.82},
                {"species_name": "ปลาทู", "estimated_catch_kg": 80.0, "confidence": 0.75},
            ]
        }
        result = parse_species_predictions(raw)
        assert len(result) == 2
        assert result[0].species_name == "กุ้ง"
        assert result[0].estimated_catch_kg == pytest.approx(120.5)
        assert result[0].confidence == pytest.approx(0.82)

    def test_empty_predictions(self):
        result = parse_species_predictions({"predictions": []})
        assert result == []

    def test_missing_predictions_key(self):
        result = parse_species_predictions({})
        assert result == []

    def test_negative_catch_clamped_to_zero(self):
        raw = {
            "predictions": [
                {"species_name": "กุ้ง", "estimated_catch_kg": -10.0, "confidence": 0.5},
            ]
        }
        result = parse_species_predictions(raw)
        assert result[0].estimated_catch_kg == 0.0

    def test_confidence_clamped_to_0_1(self):
        raw = {
            "predictions": [
                {"species_name": "กุ้ง", "estimated_catch_kg": 10.0, "confidence": 1.5},
            ]
        }
        result = parse_species_predictions(raw)
        assert result[0].confidence == 1.0

    def test_confidence_negative_clamped(self):
        raw = {
            "predictions": [
                {"species_name": "กุ้ง", "estimated_catch_kg": 10.0, "confidence": -0.5},
            ]
        }
        result = parse_species_predictions(raw)
        assert result[0].confidence == 0.0


# ---------------------------------------------------------------------------
# parse_confidence_interval
# ---------------------------------------------------------------------------


class TestParseConfidenceInterval:
    def test_normal_interval(self):
        raw = {"confidence_lower": 100.0, "confidence_upper": 200.0, "confidence_level": 0.95}
        ci = parse_confidence_interval(raw)
        assert ci.lower == pytest.approx(100.0)
        assert ci.upper == pytest.approx(200.0)
        assert ci.confidence_level == pytest.approx(0.95)

    def test_swapped_lower_upper(self):
        """When lower > upper, they should be swapped (Requirement 4.4)."""
        raw = {"confidence_lower": 300.0, "confidence_upper": 100.0, "confidence_level": 0.95}
        ci = parse_confidence_interval(raw)
        assert ci.lower <= ci.upper
        assert ci.lower == pytest.approx(100.0)
        assert ci.upper == pytest.approx(300.0)

    def test_equal_lower_upper(self):
        raw = {"confidence_lower": 150.0, "confidence_upper": 150.0, "confidence_level": 0.90}
        ci = parse_confidence_interval(raw)
        assert ci.lower == ci.upper

    def test_defaults_when_missing(self):
        ci = parse_confidence_interval({})
        assert ci.lower == 0.0
        assert ci.upper == 0.0
        assert ci.confidence_level == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# invoke_sagemaker (with mock)
# ---------------------------------------------------------------------------


def _make_mock_sagemaker_client(response_body: dict):
    """Create a mock SageMaker client that returns the given response."""
    mock_client = MagicMock()
    body_bytes = json.dumps(response_body).encode("utf-8")
    mock_response = {"Body": BytesIO(body_bytes)}
    mock_client.invoke_endpoint.return_value = mock_response
    return mock_client


class TestInvokeSagemaker:
    def test_calls_endpoint(self):
        mock_response = {"predictions": []}
        mock_client = _make_mock_sagemaker_client(mock_response)

        result = invoke_sagemaker(
            features={"ndvi": [0.5] * 30},
            area_id="area-1",
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        mock_client.invoke_endpoint.assert_called_once()
        call_kwargs = mock_client.invoke_endpoint.call_args[1]
        assert call_kwargs["EndpointName"] == "test-endpoint"
        assert call_kwargs["ContentType"] == "application/json"

    def test_returns_parsed_json(self):
        mock_response = {
            "predictions": [
                {"species_name": "กุ้ง", "estimated_catch_kg": 50.0, "confidence": 0.8}
            ]
        }
        mock_client = _make_mock_sagemaker_client(mock_response)

        result = invoke_sagemaker(
            features={},
            area_id="area-1",
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert result["predictions"][0]["species_name"] == "กุ้ง"

    def test_payload_includes_species(self):
        mock_client = _make_mock_sagemaker_client({"predictions": []})

        invoke_sagemaker(
            features={},
            area_id="area-1",
            species=["กุ้ง", "ปลาทู"],
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        call_kwargs = mock_client.invoke_endpoint.call_args[1]
        payload = json.loads(call_kwargs["Body"])
        assert payload["species"] == ["กุ้ง", "ปลาทู"]


# ---------------------------------------------------------------------------
# predict (end-to-end with mock)
# ---------------------------------------------------------------------------


class TestPredict:
    def _mock_sagemaker_response(self):
        return {
            "predictions": [
                {"species_name": "กุ้ง", "estimated_catch_kg": 100.0, "confidence": 0.85},
                {"species_name": "ปลาทู", "estimated_catch_kg": 60.0, "confidence": 0.70},
            ],
            "confidence_lower": 50.0,
            "confidence_upper": 200.0,
            "confidence_level": 0.95,
            "forecast_7day": {
                "estimated_revenue_thb": 50000.0,
                "confidence_lower": 40000.0,
                "confidence_upper": 60000.0,
            },
            "forecast_30day": {
                "estimated_revenue_thb": 200000.0,
                "confidence_lower": 150000.0,
                "confidence_upper": 250000.0,
            },
        }

    def test_returns_yield_prediction(self):
        mock_client = _make_mock_sagemaker_client(self._mock_sagemaker_response())

        result = predict(
            area_id="mahachai-01",
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert isinstance(result, YieldPrediction)
        assert result.area_id == "mahachai-01"
        assert len(result.predictions) == 2
        assert result.predictions[0].species_name == "กุ้ง"

    def test_confidence_interval_invariant(self):
        """confidence_lower ≤ confidence_upper (Requirement 4.4)."""
        mock_client = _make_mock_sagemaker_client(self._mock_sagemaker_response())

        result = predict(
            area_id="mahachai-01",
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert result.confidence_interval.lower <= result.confidence_interval.upper
        assert result.forecast_7day.confidence_lower <= result.forecast_7day.confidence_upper
        assert result.forecast_30day.confidence_lower <= result.forecast_30day.confidence_upper

    def test_model_version_set(self):
        mock_client = _make_mock_sagemaker_client(self._mock_sagemaker_response())

        result = predict(
            area_id="area-1",
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert result.model_version == "v1.0.0"

    def test_predicted_at_is_set(self):
        mock_client = _make_mock_sagemaker_client(self._mock_sagemaker_response())

        result = predict(
            area_id="area-1",
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert isinstance(result.predicted_at, datetime)

    def test_handles_missing_values_in_history(self):
        mock_client = _make_mock_sagemaker_client(self._mock_sagemaker_response())

        result = predict(
            area_id="area-1",
            ndvi_history=[None, 0.5, None] * 10,
            sst_history=[None, 28.0, None] * 10,
            chl_a_history=[None, 2.0, None] * 10,
            season=SEASON_DRY,
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert isinstance(result, YieldPrediction)

    def test_swapped_forecast_confidence_corrected(self):
        """Forecasts with swapped lower/upper should be corrected."""
        response = self._mock_sagemaker_response()
        response["forecast_7day"]["confidence_lower"] = 70000.0
        response["forecast_7day"]["confidence_upper"] = 30000.0
        mock_client = _make_mock_sagemaker_client(response)

        result = predict(
            area_id="area-1",
            ndvi_history=[0.5] * 30,
            sst_history=[28.0] * 30,
            chl_a_history=[2.0] * 30,
            season=SEASON_DRY,
            sagemaker_client=mock_client,
            endpoint_name="test-endpoint",
        )

        assert result.forecast_7day.confidence_lower <= result.forecast_7day.confidence_upper
