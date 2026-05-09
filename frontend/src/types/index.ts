/**
 * SIRINAPHA: Baan-Pla Link — Shared TypeScript Interfaces and Constants
 *
 * Data models for the Baan-Pla Link platform covering FSI Engine,
 * Mangrove Monitor, Yield Predictor, Restoration Planner, Delivery System,
 * and User Management.
 *
 * Requirements: 3.1, 3.7, 2.2, 7.1
 */

// ---------------------------------------------------------------------------
// GeoJSON primitives
// ---------------------------------------------------------------------------

/** Minimal GeoJSON Polygon type (avoids @types/geojson dependency) */
export interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: number[][][];
}

// ---------------------------------------------------------------------------
// Geo primitives
// ---------------------------------------------------------------------------

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface SeasonData {
  season: string;
  month: number;
  is_monsoon: boolean;
}

// ---------------------------------------------------------------------------
// FSI Engine (Requirements 3.1, 3.7, 3.9, 3.10)
// ---------------------------------------------------------------------------

/** Raw input values for FSI calculation */
export interface FSIInput {
  sst: number; // °C
  chl_a: number; // mg/m³
  depth: number; // meters
  lunar_phase: number; // 0.0 (new moon) – 1.0 (full moon)
  ndvi: number; // -1.0 to 1.0
  season: SeasonData;
}

/** Component scores produced by the scoring functions (each 0.0–1.0) */
export interface FSIComponentScores {
  sst_score: number;
  chl_a_score: number;
  depth_score: number;
  lunar_score: number;
  ndvi_score: number;
  season_score: number;
}

/** Data completeness metadata when some sources are unavailable */
export interface FSIDataCompleteness {
  available_sources: string[];
  missing_sources: string[];
  is_complete: boolean;
}

/** Full FSI calculation result */
export interface FSIResult {
  location: GeoPoint;
  fsi_value: number; // 0.0–1.0
  zone: "green" | "yellow" | "red";
  component_scores: FSIComponentScores;
  data_completeness: FSIDataCompleteness;
  calculated_at: Date;
}

/** JSON serialisation format for API responses (Requirement 11.1) */
export interface FSIJson {
  fsi_value: number;
  zone: string;
  location: { lat: number; lng: number };
  component_scores: Record<string, number>;
  calculated_at: string; // ISO 8601
  data_completeness: {
    available_sources: string[];
    missing_sources: string[];
  };
}

/** GeoJSON serialisation format for map display (Requirement 11.2) */
export interface FSIGeoJSON {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number]; // [lng, lat]
  };
  properties: {
    fsi_value: number;
    zone: string;
    component_scores: Record<string, number>;
    calculated_at: string;
    data_completeness: {
      available_sources: string[];
      missing_sources: string[];
    };
  };
}

// ---------------------------------------------------------------------------
// Mangrove Monitor (Requirements 2.1, 2.2, 2.4, 2.5)
// ---------------------------------------------------------------------------

export type HealthLevel = "healthy" | "moderate" | "degraded" | "critical";

export interface NDVIResult {
  location: GeoPoint;
  ndvi_value: number; // -1.0 to 1.0
  health_level: HealthLevel;
  timestamp: Date;
  sentinel2_scene_id: string;
}

export type AlertLevel = "warning" | "critical";

export interface MangroveAlert {
  id: string;
  area_id: string;
  alert_level: AlertLevel;
  ndvi_current: number;
  ndvi_6month_avg: number;
  change_percent: number; // > 20% = warning, > 40% = critical
  detected_at: Date;
  geometry: GeoJSONPolygon;
}

// ---------------------------------------------------------------------------
// Yield Predictor (Requirements 4.1–4.4)
// ---------------------------------------------------------------------------

export interface SpeciesPrediction {
  species_name: string; // Thai name
  estimated_catch_kg: number;
  confidence: number; // 0.0–1.0
}

export interface RevenueForecast {
  estimated_revenue_thb: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface YieldPrediction {
  area_id: string;
  predictions: SpeciesPrediction[];
  forecast_7day: RevenueForecast;
  forecast_30day: RevenueForecast;
  confidence_interval: {
    lower: number;
    upper: number;
    confidence_level: number; // e.g. 0.95
  };
  model_version: string;
  predicted_at: Date;
}

// ---------------------------------------------------------------------------
// Restoration Planner (Requirements 5.1–5.6)
// ---------------------------------------------------------------------------

export interface NDVITimeSeries {
  timestamps: Date[];
  values: number[];
}

export interface SoilData {
  type: string;
  ph: number;
  salinity: number;
}

export interface TidalData {
  min_m: number;
  max_m: number;
  mean_m: number;
}

export interface RestorationSite {
  site_id: string;
  geometry: GeoJSONPolygon;
  area_rai: number; // Thai unit
  ndvi_history: NDVITimeSeries;
  soil_condition: SoilData;
  tidal_range: TidalData;
  carbon_potential_tco2_year: number;
  expected_survival_rate: number; // 0.0–1.0
  priority_rank: number;
}

// ---------------------------------------------------------------------------
// Blue Carbon MRV (Requirements 8.1–8.5)
// ---------------------------------------------------------------------------

export interface RevenueSharing {
  private_sector: number; // 63%
  cooperative: number; // 20%
  government: number; // 10%
  mrv_fee: number; // 7%
}

export interface CarbonReport {
  period: { start: Date; end: Date };
  total_area_rai: number;
  avg_ndvi: number;
  total_co2_tons: number;
  revenue_sharing: RevenueSharing;
}

// ---------------------------------------------------------------------------
// Delivery System (Requirements 6.1–6.8)
// ---------------------------------------------------------------------------

export type DeliveryChannel = "line" | "sms" | "web";
export type MessageType = "daily_fsi" | "alert" | "report";
export type DeliveryStatus = "pending" | "sent" | "failed" | "fallback_sms";

export interface DeliveryMessageContent {
  thai_text: string;
  fsi_summary?: FSIJson;
  alert?: MangroveAlert;
}

export interface DeliveryMessage {
  recipient_id: string;
  channel: DeliveryChannel;
  message_type: MessageType;
  content: DeliveryMessageContent;
  sent_at?: Date;
  status: DeliveryStatus;
}

// ---------------------------------------------------------------------------
// User Management (Requirements 7.1–7.5)
// ---------------------------------------------------------------------------

export type UserType = "Fisherman" | "Community_Rep" | "Corporate_Partner";
export type MembershipTier = "Silver" | "Gold";

export interface UserProfile {
  id: string; // Supabase Auth UID
  user_type: UserType;
  display_name: string;
  // Fisherman-specific
  fishing_area_ids?: string[];
  preferred_channel: "line" | "sms";
  line_user_id?: string;
  phone_number?: string;
  // Community_Rep-specific
  responsible_area_ids?: string[];
  // Corporate_Partner-specific
  company_name?: string;
  membership_tier?: MembershipTier;
}

// ---------------------------------------------------------------------------
// Constants (Requirements 3.1, 3.7, 2.2)
// ---------------------------------------------------------------------------

/** FSI formula weights — must sum to 1.0 */
export const FSI_WEIGHTS = {
  sst: 0.25,
  chl_a: 0.25,
  depth: 0.15,
  lunar: 0.1,
  ndvi: 0.25,
  season: 0.1,
} as const;

/** FSI zone classification thresholds */
export const FSI_ZONES = {
  green: { min: 0.7, max: 1.0, label: "เหมาะสมมาก" },
  yellow: { min: 0.4, max: 0.7, label: "เหมาะสมปานกลาง" },
  red: { min: 0.0, max: 0.4, label: "ไม่เหมาะสม" },
} as const;

/** NDVI health classification thresholds */
export const NDVI_THRESHOLDS = {
  healthy: { min: 0.6, max: 1.0 },
  moderate: { min: 0.4, max: 0.6 },
  degraded: { min: 0.2, max: 0.4 },
  critical: { min: -1.0, max: 0.2 },
} as const;
