export interface MangroveZone {
  zoneId: string;
  zoneName: string;
  province: string;
  district: string;
  areaRai: number;
  currentNDVI: number;
  previousNDVI: number;
  deltaNDVI: number;
  healthStatus: "healthy" | "stressed" | "degraded";
  coordinates: [number, number][];
  centroid: [number, number];
  lastObservationDate: string;
}

export interface NDVIObservation {
  date: string;
  meanNDVI: number;
  minNDVI: number;
  maxNDVI: number;
  cloudCoverPct: number;
}

export interface DegradationAlert {
  alertId: string;
  zoneId: string;
  zoneName: string;
  detectedAt: string;
  alertType: "encroachment" | "deforestation" | "die_off" | "anomaly";
  severity: "low" | "medium" | "high" | "critical";
  deltaNDVI: number;
  affectedAreaRai: number;
  centroid: [number, number];
  isAcknowledged: boolean;
  acknowledgedBy: string | null;
  notes: string | null;
}

export interface FSIPoint {
  lat: number;
  lng: number;
  fsiScore: number;
  confidence: number;
  predictionDate: string;
  contributingFactors: {
    sst: number;
    chlorophyllA: number;
    ndviProximity: number;
    seasonality: number;
  };
}

export interface CatchLog {
  logId: string;
  fisherName: string;
  tripDate: string;
  fishingLocation: [number, number];
  totalWeightKg: number;
  fuelCostBaht: number;
  estimatedRevenueBaht: number;
  gearType: string;
  speciesComposition: { species: string; weightKg: number }[];
  usedFSIRecommendation: boolean;
}

export interface RestorationSite {
  siteId: string;
  zoneName: string;
  areaRai: number;
  priorityScore: number;
  estimatedSurvivalRate: number;
  carbonSequestrationPotential: number;
  status: "proposed" | "approved" | "planting" | "monitoring" | "established";
  coordinates: [number, number][];
  centroid: [number, number];
}

export interface CarbonCredit {
  creditId: string;
  siteName: string;
  measurementDate: string;
  biomassEstimateTon: number;
  co2EquivalentTon: number;
  verificationStatus: "measured" | "reported" | "verified" | "issued";
}

export interface EcosystemForecast {
  date: string;
  predictedCPUE: number;
  lowerBound: number;
  upperBound: number;
  ndviValue: number;
}
