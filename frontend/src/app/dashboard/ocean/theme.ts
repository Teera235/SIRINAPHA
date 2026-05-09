/**
 * Ocean Dashboard Theme Tokens
 *
 * Single source of truth for all colors, typography, and spacing
 * used across the Global-Fishing-Watch-style dashboard.
 *
 * Reference: documents/research/appendix-b-color-tokens.md
 */

// ---------------------------------------------------------------------------
// Color tokens
// ---------------------------------------------------------------------------

// Tuned to match Global Fishing Watch visual language [ref 1]
export const oceanColors = {
  // Core dark palette (GFW uses deep navy with subtle blue tint)
  deepest: "#020617",
  deep: "#0a1e33",
  panel: "#0c1d32",
  surface: "#0f223a",
  surface2: "#162a44",
  surface3: "#1d3454",
  land: "#0e2238",

  // Borders
  borderSubtle: "#182a42",
  borderDefault: "#24374f",
  borderLight: "#35496a",

  // Accents — GFW activity green
  cyan: "#22d3a0",          // primary activity green
  cyanGlow: "rgba(34, 211, 160, 0.4)",
  teal: "#4ade80",           // secondary bright green
  tealGlow: "rgba(74, 222, 128, 0.5)",
  lime: "#88e896",
  sky: "#40c4ff",
  purple: "#b388ff",
  amber: "#ffab00",
  red: "#ff1744",

  // Data layers
  layerFSI: "#22d3a0",
  layerNDVI: "#4ade80",
  layerSST: "#ff6e40",
  layerChla: "#40c4ff",
  layerLunar: "#b388ff",
  layerSeason: "#ffd740",
  layerVessel: "#06b6d4",

  // Status
  success: "#22c55e",
  warning: "#ffab00",
  alert: "#ea580c",
  danger: "#ff1744",
  info: "#3b82f6",

  // Text
  textBright: "#ffffff",
  textPrimary: "#e2e8f0",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  textDisabled: "#475569",
  textFaded: "#334155",
} as const;

// ---------------------------------------------------------------------------
// FSI Zone colors
// ---------------------------------------------------------------------------

export const FSI_ZONES = {
  green: {
    color: "#00e5ff",
    glow: "rgba(0, 229, 255, 0.4)",
    label: "เหมาะสมมาก",
    labelEn: "Highly Suitable",
    min: 0.7,
    max: 1.0,
  },
  yellow: {
    color: "#ffab00",
    glow: "rgba(255, 171, 0, 0.4)",
    label: "เหมาะสมปานกลาง",
    labelEn: "Moderate",
    min: 0.4,
    max: 0.7,
  },
  red: {
    color: "#ff1744",
    glow: "rgba(255, 23, 68, 0.4)",
    label: "ไม่เหมาะสม",
    labelEn: "Not Suitable",
    min: 0.0,
    max: 0.4,
  },
} as const;

export type FSIZone = keyof typeof FSI_ZONES;

export function classifyFSI(value: number): FSIZone {
  if (value >= 0.7) return "green";
  if (value >= 0.4) return "yellow";
  return "red";
}

// ---------------------------------------------------------------------------
// NDVI Health colors
// ---------------------------------------------------------------------------

export const NDVI_HEALTH = {
  healthy: {
    color: "#16a34a",
    label: "สมบูรณ์",
    labelEn: "Healthy",
    min: 0.6,
  },
  moderate: {
    color: "#ca8a04",
    label: "ปานกลาง",
    labelEn: "Moderate",
    min: 0.4,
  },
  degraded: {
    color: "#ea580c",
    label: "เสื่อมโทรม",
    labelEn: "Degraded",
    min: 0.2,
  },
  critical: {
    color: "#dc2626",
    label: "วิกฤต",
    labelEn: "Critical",
    min: -1.0,
  },
} as const;

// ---------------------------------------------------------------------------
// Gradient ramps (CSS linear-gradient strings)
// ---------------------------------------------------------------------------

export const gradients = {
  // GFW-style activity heatmap — dark navy to teal/green to lime
  fsi: "linear-gradient(to right, #0a1e33, #0c2844, #0e3c56, #115668, #147a78, #1a9b7c, #2ec078, #62d669, #a8e053, #d4e64a)",
  sst: "linear-gradient(to right, #1e3cb4, #5096dc, #b4dc64, #f0b428, #c82820)",
  chla: "linear-gradient(to right, #051440, #0a5078, #148050, #8cbe28, #f0e650)",
  ndvi: "linear-gradient(to right, #8b4513, #deb887, #f4e4c1, #9acd32, #228b22, #006400)",
} as const;

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

export const layout = {
  iconRailWidth: 50,
  sidebarWidth: 320,
  sidebarWidthTablet: 280,
  timelineHeight: 92,
  headerHeight: 56,
  popupMaxWidth: 320,
  mobileBreakpoint: 768,
} as const;

// ---------------------------------------------------------------------------
// Typography
// ---------------------------------------------------------------------------

export const typography = {
  fontSans: "Inter, system-ui, sans-serif",
  fontMono: "'Roboto Mono', 'Courier New', monospace",
} as const;

// ---------------------------------------------------------------------------
// Map basemap styles
// ---------------------------------------------------------------------------

export const MAP_STYLES = [
  { id: "dark-v11", label: "Dark", landColor: "#151d2e" },
  { id: "light-v11", label: "Light", landColor: "#e8e8e8" },
  { id: "outdoors-v12", label: "Terrain", landColor: "#d4d0c8" },
  { id: "navigation-night-v1", label: "Nav Night", landColor: "#1a1a2e" },
] as const;
