"""
Yield Predictor — Feature Preprocessing and SageMaker Inference

Accepts NDVI, SST, Chl-a history (30 days) and season data, preprocesses
features (normalisation, missing-value imputation), invokes a SageMaker
endpoint for species-level catch predictions, and stores results in the
``yield_predictions`` table.

Requirements: 4.1, 4.2, 4.4
"""

from __future__ import annotations

import importlib as _il
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3

_config = _il.import_module("lambda.shared.config")
SAGEMAKER_ENDPOINT = _config.SAGEMAKER_ENDPOINT
AWS_REGION = _config.AWS_REGION

_models = _il.import_module("lambda.shared.models")
SeasonData = _models.SeasonData
SpeciesPrediction = _models.SpeciesPrediction
RevenueForecast = _models.RevenueForecast
ConfidenceInterval = _models.ConfidenceInterval
YieldPrediction = _models.YieldPrediction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HISTORY_LENGTH = 30  # days of history expected

# Normalisation ranges for feature preprocessing
NDVI_RANGE = (-1.0, 1.0)
SST_RANGE = (15.0, 35.0)   # °C — practical range for Thai waters
CHL_A_RANGE = (0.0, 20.0)  # mg/m³

# Default historical averages used when values are missing
DEFAULT_NDVI_AVG = 0.45
DEFAULT_SST_AVG = 28.5
DEFAULT_CHL_A_AVG = 2.0

# Thai commercial species (Requirement 4.2)
DEFAULT_SPECIES: List[str] = [
    "กุ้ง",        # Shrimp
    "ปลากะพง",    # Sea bass
    "ปลาทู",      # Short mackerel
    "ปูม้า",       # Blue swimming crab
    "หมึก",        # Squid
]

# Season encoding
SEASON_ENCODING: Dict[str, float] = {
    "dry": 0.0,
    "hot": 0.5,
    "monsoon": 1.0,
}

# Current model version tag
MODEL_VERSION = "v1.0.0"


# ---------------------------------------------------------------------------
# Feature Preprocessing
# ---------------------------------------------------------------------------


def _normalise(value: float, min_val: float, max_val: float) -> float:
    """Normalise *value* to [0, 1] given a known range.

    Values outside the range are clamped.
    """
    if max_val == min_val:
        return 0.5
    normalised = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalised))


def _fill_missing(
    history: List[Optional[float]],
    default_avg: float,
) -> List[float]:
    """Replace ``None`` entries in *history* with *default_avg*.

    If the list has any non-None values, the average of those values is
    used instead of the global default.
    """
    valid = [v for v in history if v is not None]
    fill_value = (sum(valid) / len(valid)) if valid else default_avg
    return [v if v is not None else fill_value for v in history]


def _pad_or_trim(history: List[float], length: int) -> List[float]:
    """Ensure *history* has exactly *length* entries.

    Trims from the front (oldest) if too long; pads at the front with the
    first available value if too short.
    """
    if len(history) == length:
        return history
    if len(history) > length:
        return history[-length:]
    # Pad at front
    pad_value = history[0] if history else 0.0
    return [pad_value] * (length - len(history)) + history


def preprocess_features(
    *,
    ndvi_history: List[Optional[float]],
    sst_history: List[Optional[float]],
    chl_a_history: List[Optional[float]],
    season: SeasonData,
) -> Dict[str, Any]:
    """Preprocess raw feature histories into a model-ready payload.

    Steps:
    1. Fill missing values with historical averages.
    2. Pad or trim to ``HISTORY_LENGTH``.
    3. Normalise each value to [0, 1].
    4. Encode season as a numeric value.

    Returns a dict with keys ``ndvi``, ``sst``, ``chl_a`` (each a list of
    floats in [0, 1]), ``season_encoded``, ``is_monsoon``, and ``month``.
    """
    # Step 1 — fill missing
    ndvi_filled = _fill_missing(ndvi_history, DEFAULT_NDVI_AVG)
    sst_filled = _fill_missing(sst_history, DEFAULT_SST_AVG)
    chl_a_filled = _fill_missing(chl_a_history, DEFAULT_CHL_A_AVG)

    # Step 2 — pad / trim
    ndvi_padded = _pad_or_trim(ndvi_filled, HISTORY_LENGTH)
    sst_padded = _pad_or_trim(sst_filled, HISTORY_LENGTH)
    chl_a_padded = _pad_or_trim(chl_a_filled, HISTORY_LENGTH)

    # Step 3 — normalise
    ndvi_norm = [_normalise(v, *NDVI_RANGE) for v in ndvi_padded]
    sst_norm = [_normalise(v, *SST_RANGE) for v in sst_padded]
    chl_a_norm = [_normalise(v, *CHL_A_RANGE) for v in chl_a_padded]

    # Step 4 — season encoding
    season_encoded = SEASON_ENCODING.get(season.season, 0.5)

    return {
        "ndvi": ndvi_norm,
        "sst": sst_norm,
        "chl_a": chl_a_norm,
        "season_encoded": season_encoded,
        "is_monsoon": 1.0 if season.is_monsoon else 0.0,
        "month": season.month / 12.0,  # normalise month to [0, 1)
    }


# ---------------------------------------------------------------------------
# SageMaker Inference
# ---------------------------------------------------------------------------


def _build_sagemaker_client():
    """Create a SageMaker Runtime client."""
    return boto3.client("sagemaker-runtime", region_name=AWS_REGION)


def invoke_sagemaker(
    features: Dict[str, Any],
    area_id: str,
    species: Optional[List[str]] = None,
    *,
    sagemaker_client=None,
    endpoint_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Invoke the SageMaker endpoint and return the raw response dict.

    Parameters
    ----------
    features : dict
        Preprocessed feature payload from :func:`preprocess_features`.
    area_id : str
        Fishing area identifier.
    species : list[str] | None
        Target species list.  Defaults to :data:`DEFAULT_SPECIES`.
    sagemaker_client
        Optional pre-built boto3 client (useful for testing).
    endpoint_name : str | None
        Override the endpoint name (defaults to config).

    Returns
    -------
    dict
        Parsed JSON response from SageMaker.
    """
    client = sagemaker_client or _build_sagemaker_client()
    ep = endpoint_name or SAGEMAKER_ENDPOINT
    species = species or DEFAULT_SPECIES

    payload = {
        "area_id": area_id,
        "features": features,
        "species": species,
    }

    response = client.invoke_endpoint(
        EndpointName=ep,
        ContentType="application/json",
        Body=json.dumps(payload),
    )

    body = response["Body"].read()
    return json.loads(body)


# ---------------------------------------------------------------------------
# Response Parsing
# ---------------------------------------------------------------------------


def parse_species_predictions(
    raw: Dict[str, Any],
) -> List[SpeciesPrediction]:
    """Parse the SageMaker response into :class:`SpeciesPrediction` objects.

    Expected response format::

        {
            "predictions": [
                {
                    "species_name": "กุ้ง",
                    "estimated_catch_kg": 120.5,
                    "confidence": 0.82
                },
                ...
            ]
        }
    """
    predictions: List[SpeciesPrediction] = []
    for item in raw.get("predictions", []):
        predictions.append(
            SpeciesPrediction(
                species_name=item["species_name"],
                estimated_catch_kg=max(0.0, float(item["estimated_catch_kg"])),
                confidence=max(0.0, min(1.0, float(item["confidence"]))),
            )
        )
    return predictions


def parse_confidence_interval(
    raw: Dict[str, Any],
) -> ConfidenceInterval:
    """Parse confidence interval from SageMaker response.

    Expected keys: ``confidence_lower``, ``confidence_upper``,
    ``confidence_level``.  Enforces ``lower ≤ upper`` invariant.
    """
    lower = float(raw.get("confidence_lower", 0.0))
    upper = float(raw.get("confidence_upper", 0.0))
    level = float(raw.get("confidence_level", 0.95))

    # Enforce invariant: lower ≤ upper  (Property 20 / Requirement 4.4)
    if lower > upper:
        lower, upper = upper, lower

    return ConfidenceInterval(lower=lower, upper=upper, confidence_level=level)


# ---------------------------------------------------------------------------
# High-level predict function
# ---------------------------------------------------------------------------


def predict(
    *,
    area_id: str,
    ndvi_history: List[Optional[float]],
    sst_history: List[Optional[float]],
    chl_a_history: List[Optional[float]],
    season: SeasonData,
    species: Optional[List[str]] = None,
    sagemaker_client=None,
    endpoint_name: Optional[str] = None,
) -> YieldPrediction:
    """Run the full prediction pipeline.

    1. Preprocess features.
    2. Invoke SageMaker.
    3. Parse response into domain objects.

    Returns a :class:`YieldPrediction` ready for storage.
    """
    features = preprocess_features(
        ndvi_history=ndvi_history,
        sst_history=sst_history,
        chl_a_history=chl_a_history,
        season=season,
    )

    raw = invoke_sagemaker(
        features,
        area_id,
        species=species,
        sagemaker_client=sagemaker_client,
        endpoint_name=endpoint_name,
    )

    predictions = parse_species_predictions(raw)
    confidence = parse_confidence_interval(raw)

    # Revenue forecasts are handled by the revenue module (Task 8.2)
    forecast_7day = RevenueForecast(
        estimated_revenue_thb=float(raw.get("forecast_7day", {}).get("estimated_revenue_thb", 0.0)),
        confidence_lower=float(raw.get("forecast_7day", {}).get("confidence_lower", 0.0)),
        confidence_upper=float(raw.get("forecast_7day", {}).get("confidence_upper", 0.0)),
    )
    forecast_30day = RevenueForecast(
        estimated_revenue_thb=float(raw.get("forecast_30day", {}).get("estimated_revenue_thb", 0.0)),
        confidence_lower=float(raw.get("forecast_30day", {}).get("confidence_lower", 0.0)),
        confidence_upper=float(raw.get("forecast_30day", {}).get("confidence_upper", 0.0)),
    )

    # Enforce confidence_lower ≤ confidence_upper on forecasts
    if forecast_7day.confidence_lower > forecast_7day.confidence_upper:
        forecast_7day = RevenueForecast(
            estimated_revenue_thb=forecast_7day.estimated_revenue_thb,
            confidence_lower=forecast_7day.confidence_upper,
            confidence_upper=forecast_7day.confidence_lower,
        )
    if forecast_30day.confidence_lower > forecast_30day.confidence_upper:
        forecast_30day = RevenueForecast(
            estimated_revenue_thb=forecast_30day.estimated_revenue_thb,
            confidence_lower=forecast_30day.confidence_upper,
            confidence_upper=forecast_30day.confidence_lower,
        )

    return YieldPrediction(
        area_id=area_id,
        predictions=predictions,
        forecast_7day=forecast_7day,
        forecast_30day=forecast_30day,
        confidence_interval=confidence,
        model_version=MODEL_VERSION,
        predicted_at=datetime.utcnow(),
    )
