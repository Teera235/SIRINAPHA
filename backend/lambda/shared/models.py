"""
SIRINAPHA: Baan-Pla Link — Shared Python Data Models and Constants

Dataclasses mirroring the TypeScript interfaces for use in AWS Lambda
functions (Data Pipeline, Mangrove Monitor, FSI Engine, Yield Predictor,
Restoration Planner).

Requirements: 3.1, 3.7, 2.2, 7.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class HealthLevel(str, Enum):
    """NDVI-based mangrove health classification (Requirement 2.2)."""

    HEALTHY = "healthy"
    MODERATE = "moderate"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class AlertLevel(str, Enum):
    """Mangrove alert severity (Requirements 2.4, 2.5)."""

    WARNING = "warning"
    CRITICAL = "critical"


class FSIZone(str, Enum):
    """FSI zone classification (Requirement 3.7)."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class DeliveryChannel(str, Enum):
    """Message delivery channel."""

    LINE = "line"
    SMS = "sms"
    WEB = "web"


class MessageType(str, Enum):
    """Delivery message type."""

    DAILY_FSI = "daily_fsi"
    ALERT = "alert"
    REPORT = "report"


class DeliveryStatus(str, Enum):
    """Delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    FALLBACK_SMS = "fallback_sms"


class UserType(str, Enum):
    """User type (Requirement 7.1)."""

    FISHERMAN = "Fisherman"
    COMMUNITY_REP = "Community_Rep"
    CORPORATE_PARTNER = "Corporate_Partner"


class MembershipTier(str, Enum):
    """Corporate partner membership tier."""

    SILVER = "Silver"
    GOLD = "Gold"


# ---------------------------------------------------------------------------
# Geo primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeoPoint:
    """A geographic coordinate."""

    lat: float
    lng: float


@dataclass(frozen=True)
class SeasonData:
    """Seasonal information for FSI calculation."""

    season: str
    month: int
    is_monsoon: bool


# ---------------------------------------------------------------------------
# FSI Engine (Requirements 3.1, 3.7, 3.9, 3.10)
# ---------------------------------------------------------------------------


@dataclass
class FSIInput:
    """Raw input values for FSI calculation."""

    sst: float  # °C
    chl_a: float  # mg/m³
    depth: float  # meters
    lunar_phase: float  # 0.0 (new moon) – 1.0 (full moon)
    ndvi: float  # -1.0 to 1.0
    season: SeasonData


@dataclass(frozen=True)
class FSIComponentScores:
    """Individual component scores (each 0.0–1.0)."""

    sst_score: float
    chl_a_score: float
    depth_score: float
    lunar_score: float
    ndvi_score: float
    season_score: float


@dataclass(frozen=True)
class FSIDataCompleteness:
    """Tracks which data sources were available for an FSI calculation."""

    available_sources: List[str]
    missing_sources: List[str]
    is_complete: bool


@dataclass
class FSIResult:
    """Full FSI calculation result."""

    location: GeoPoint
    fsi_value: float  # 0.0–1.0
    zone: FSIZone
    component_scores: FSIComponentScores
    data_completeness: FSIDataCompleteness
    calculated_at: datetime


@dataclass
class FSIJson:
    """JSON serialisation format for API responses (Requirement 11.1)."""

    fsi_value: float
    zone: str
    location: Dict[str, float]  # {"lat": ..., "lng": ...}
    component_scores: Dict[str, float]
    calculated_at: str  # ISO 8601
    data_completeness: Dict[str, List[str]]


@dataclass
class FSIGeoJSON:
    """GeoJSON serialisation format for map display (Requirement 11.2)."""

    type: str = "Feature"
    geometry: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mangrove Monitor (Requirements 2.1, 2.2, 2.4, 2.5)
# ---------------------------------------------------------------------------


@dataclass
class NDVIResult:
    """Result of an NDVI calculation for a location."""

    location: GeoPoint
    ndvi_value: float  # -1.0 to 1.0
    health_level: HealthLevel
    timestamp: datetime
    sentinel2_scene_id: str


@dataclass
class MangroveAlert:
    """Alert generated when mangrove NDVI drops significantly."""

    id: str
    area_id: str
    alert_level: AlertLevel
    ndvi_current: float
    ndvi_6month_avg: float
    change_percent: float  # > 20% = warning, > 40% = critical
    detected_at: datetime
    geometry: Dict[str, Any]  # GeoJSON Polygon


# ---------------------------------------------------------------------------
# Yield Predictor (Requirements 4.1–4.4)
# ---------------------------------------------------------------------------


@dataclass
class SpeciesPrediction:
    """Prediction for a single species."""

    species_name: str  # Thai name
    estimated_catch_kg: float
    confidence: float  # 0.0–1.0


@dataclass
class RevenueForecast:
    """Revenue forecast for a time period."""

    estimated_revenue_thb: float
    confidence_lower: float
    confidence_upper: float


@dataclass
class ConfidenceInterval:
    """Confidence interval for a prediction."""

    lower: float
    upper: float
    confidence_level: float  # e.g. 0.95


@dataclass
class YieldPrediction:
    """Yield prediction result for a fishing area."""

    area_id: str
    predictions: List[SpeciesPrediction]
    forecast_7day: RevenueForecast
    forecast_30day: RevenueForecast
    confidence_interval: ConfidenceInterval
    model_version: str
    predicted_at: datetime


# ---------------------------------------------------------------------------
# Restoration Planner (Requirements 5.1–5.6)
# ---------------------------------------------------------------------------


@dataclass
class NDVITimeSeries:
    """NDVI values over time for a location."""

    timestamps: List[datetime]
    values: List[float]


@dataclass
class SoilData:
    """Soil condition data for a restoration site."""

    type: str
    ph: float
    salinity: float


@dataclass
class TidalData:
    """Tidal range data for a restoration site."""

    min_m: float
    max_m: float
    mean_m: float


@dataclass
class RestorationSite:
    """Candidate site for mangrove restoration."""

    site_id: str
    geometry: Dict[str, Any]  # GeoJSON Polygon
    area_rai: float  # Thai unit
    ndvi_history: NDVITimeSeries
    soil_condition: SoilData
    tidal_range: TidalData
    carbon_potential_tco2_year: float
    expected_survival_rate: float  # 0.0–1.0
    priority_rank: int


# ---------------------------------------------------------------------------
# Blue Carbon MRV (Requirements 8.1–8.5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RevenueSharing:
    """Carbon credit revenue sharing breakdown (Requirement 8.5)."""

    private_sector: float  # 63%
    cooperative: float  # 20%
    government: float  # 10%
    mrv_fee: float  # 7%


@dataclass
class CarbonReport:
    """Blue Carbon MRV report for a period."""

    period: Dict[str, date]  # {"start": ..., "end": ...}
    total_area_rai: float
    avg_ndvi: float
    total_co2_tons: float
    revenue_sharing: RevenueSharing


# ---------------------------------------------------------------------------
# Delivery System (Requirements 6.1–6.8)
# ---------------------------------------------------------------------------


@dataclass
class DeliveryMessageContent:
    """Content payload for a delivery message."""

    thai_text: str
    fsi_summary: Optional[FSIJson] = None
    alert: Optional[MangroveAlert] = None


@dataclass
class DeliveryMessage:
    """A message to be delivered to a user."""

    recipient_id: str
    channel: DeliveryChannel
    message_type: MessageType
    content: DeliveryMessageContent
    sent_at: Optional[datetime] = None
    status: DeliveryStatus = DeliveryStatus.PENDING


# ---------------------------------------------------------------------------
# User Management (Requirements 7.1–7.5)
# ---------------------------------------------------------------------------


@dataclass
class UserProfile:
    """User profile supporting all three user types."""

    id: str  # Supabase Auth UID
    user_type: UserType
    display_name: str
    preferred_channel: str = "line"  # "line" | "sms"
    # Fisherman-specific
    fishing_area_ids: Optional[List[str]] = None
    line_user_id: Optional[str] = None
    phone_number: Optional[str] = None
    # Community_Rep-specific
    responsible_area_ids: Optional[List[str]] = None
    # Corporate_Partner-specific
    company_name: Optional[str] = None
    membership_tier: Optional[MembershipTier] = None


# ---------------------------------------------------------------------------
# Constants (Requirements 3.1, 3.7, 2.2)
# ---------------------------------------------------------------------------

FSI_WEIGHTS: Dict[str, float] = {
    "sst": 0.25,
    "chl_a": 0.25,
    "depth": 0.15,
    "lunar": 0.10,
    "ndvi": 0.25,
    "season": 0.10,
}
"""FSI formula weights — must sum to 1.0 (Requirement 3.1)."""

FSI_ZONES: Dict[str, Dict[str, float]] = {
    "green": {"min": 0.7, "max": 1.0},
    "yellow": {"min": 0.4, "max": 0.7},
    "red": {"min": 0.0, "max": 0.4},
}
"""FSI zone classification thresholds (Requirement 3.7)."""

NDVI_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "healthy": {"min": 0.6, "max": 1.0},
    "moderate": {"min": 0.4, "max": 0.6},
    "degraded": {"min": 0.2, "max": 0.4},
    "critical": {"min": -1.0, "max": 0.2},
}
"""NDVI health classification thresholds (Requirement 2.2)."""
