/**
 * Raster Data Generators (MVP / Demo mode)
 *
 * สร้าง global raster ขนาด 720x360 สำหรับ FSI, SST, Chl-a
 * ใน production จะถูกแทนที่ด้วย tile server (TiTiler) หรือ MVT endpoints
 *
 * Reference: documents/research/03-methodology.md §3.2
 */

// ---------------------------------------------------------------------------
// Noise helpers (Perlin-like fBm)
// ---------------------------------------------------------------------------

function hash(x: number, y: number): number {
  const h = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return h - Math.floor(h);
}

function smoothNoise(x: number, y: number): number {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy);
  const b = hash(ix + 1, iy);
  const c = hash(ix, iy + 1);
  const d = hash(ix + 1, iy + 1);
  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
}

function fbm(x: number, y: number): number {
  let v = 0;
  let a = 0.5;
  let f = 1;
  for (let i = 0; i < 4; i++) {
    v += a * smoothNoise(x * f, y * f);
    a *= 0.5;
    f *= 2;
  }
  return v;
}

// ---------------------------------------------------------------------------
// Value functions (MVP — replaced by real satellite data in production)
// ---------------------------------------------------------------------------

/**
 * FSI value approximation using noise + hotspots.
 *
 * In production, this would be replaced by:
 *   fetch('/api/fsi/latest?bbox=...').then(fsi => ...)
 */
export function computeFSI(lat: number, lng: number): number {
  const n = fbm(lat * 1.5, lng * 1.5);
  let base = n * 0.5 + 0.25;

  // Hotspots (coastal areas with known fishing activity)
  const spots: Array<[number, number, number, number]> = [
    [10, 100, 8, 0.3],    // Gulf of Thailand
    [15, 115, 12, 0.15],  // South China Sea
    [-5, 42, 10, 0.12],   // East Africa
    [-10, -78, 8, 0.2],   // Peru upwelling
    [55, 3, 8, 0.15],     // North Sea
    [35, 135, 10, 0.15],  // Japan coast
    [15, -18, 8, 0.18],   // West Africa
    [5, 75, 15, 0.1],     // Arabian Sea
  ];

  for (const [sLat, sLng, radius, weight] of spots) {
    const dist = Math.sqrt((lat - sLat) ** 2 + (lng - sLng) ** 2);
    base += Math.max(0, 1 - dist / radius) * weight;
  }

  base += (hash(lat * 30, lng * 30) - 0.5) * 0.06;
  return Math.max(0, Math.min(1, base));
}

/**
 * SST normalized [0, 1]. To convert to °C: temp = 15 + value * 20
 */
export function computeSST(lat: number, lng: number): number {
  const equatorDist = Math.abs(lat) / 90;
  const base = 1 - equatorDist * 0.8;
  const noise = fbm(lat * 0.8, lng * 0.8) * 0.2 - 0.1;
  return Math.max(0, Math.min(1, base + noise + (hash(lat * 20, lng * 20) - 0.5) * 0.05));
}

/**
 * Chlorophyll-a normalized [0, 1]. To convert: chla = value * 10 mg/m³
 */
export function computeChla(lat: number, lng: number): number {
  const noise = fbm(lat * 2, lng * 2);
  let base = noise * 0.3;

  const coasts: Array<[number, number, number]> = [
    [10, 100, 10], [15, 115, 12], [-5, 42, 10], [35, 135, 10],
    [55, 3, 8], [15, -18, 8], [-10, -78, 8], [5, 75, 15],
    [40, -70, 8], [30, -90, 6],
  ];

  for (const [sLat, sLng, radius] of coasts) {
    const dist = Math.sqrt((lat - sLat) ** 2 + (lng - sLng) ** 2);
    base += Math.max(0, 1 - dist / radius) * 0.4;
  }

  base += (hash(lat * 25, lng * 25) - 0.5) * 0.08;
  return Math.max(0, Math.min(1, base));
}

// ---------------------------------------------------------------------------
// Color ramps
// ---------------------------------------------------------------------------

type Stop = [number, number, number, number]; // [t, r, g, b]
type RGBA = [number, number, number, number];

function interpRamp(stops: Stop[], v: number): RGBA {
  let i = 0;
  while (i < stops.length - 1 && stops[i + 1][0] < v) i++;
  if (i >= stops.length - 1) {
    const last = stops[stops.length - 1];
    return [last[1], last[2], last[3], 200];
  }
  const [t0, r0, g0, b0] = stops[i];
  const [t1, r1, g1, b1] = stops[i + 1];
  const f = (v - t0) / (t1 - t0);
  return [
    Math.round(r0 + (r1 - r0) * f),
    Math.round(g0 + (g1 - g0) * f),
    Math.round(b0 + (b1 - b0) * f),
    Math.round(120 + v * 80),
  ];
}

export function fsiColor(v: number): RGBA {
  const stops: Stop[] = [
    [0, 4, 15, 60], [0.1, 8, 40, 100], [0.2, 12, 65, 130],
    [0.3, 0, 110, 135], [0.4, 0, 150, 155], [0.5, 0, 180, 170],
    [0.6, 15, 200, 180], [0.7, 40, 212, 190], [0.8, 80, 220, 150],
    [0.9, 200, 210, 40], [1, 255, 237, 74],
  ];
  return interpRamp(stops, v);
}

export function sstColor(v: number): RGBA {
  const stops: Stop[] = [
    [0, 30, 60, 180], [0.15, 50, 100, 200], [0.3, 80, 150, 220],
    [0.45, 180, 200, 100], [0.6, 230, 220, 60], [0.75, 240, 180, 40],
    [0.85, 230, 120, 30], [1, 200, 40, 30],
  ];
  return interpRamp(stops, v);
}

export function chlaColor(v: number): RGBA {
  const stops: Stop[] = [
    [0, 5, 20, 60], [0.15, 10, 40, 100], [0.3, 10, 80, 120],
    [0.45, 20, 130, 100], [0.6, 60, 160, 60], [0.75, 140, 190, 40],
    [0.85, 200, 210, 50], [1, 240, 230, 80],
  ];
  return interpRamp(stops, v);
}

// ---------------------------------------------------------------------------
// Canvas renderer
// ---------------------------------------------------------------------------

export interface RasterResult {
  url: string;       // data URL
  pixelCount: number; // number of non-transparent pixels
}

export function renderRaster(
  valueFn: (lat: number, lng: number) => number,
  colorFn: (v: number) => RGBA,
  width = 720,
  height = 360
): RasterResult {
  if (typeof document === "undefined") {
    return { url: "", pixelCount: 0 };
  }

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return { url: "", pixelCount: 0 };

  const img = ctx.createImageData(width, height);
  let count = 0;

  for (let py = 0; py < height; py++) {
    for (let px = 0; px < width; px++) {
      const lng = -180 + (px / width) * 360;
      const lat = 90 - (py / height) * 180;
      const v = valueFn(lat, lng);
      const [r, g, b, a] = colorFn(v);
      const idx = (py * width + px) * 4;
      img.data[idx] = r;
      img.data[idx + 1] = g;
      img.data[idx + 2] = b;
      img.data[idx + 3] = a;
      if (v > 0.02) count++;
    }
  }

  ctx.putImageData(img, 0, 0);
  return { url: canvas.toDataURL("image/png"), pixelCount: count };
}

// ---------------------------------------------------------------------------
// Lunar phase calculation (ephem port)
// ---------------------------------------------------------------------------

export interface LunarPhase {
  phase: number; // 0–1 (0 = new, 0.5 = full)
  name: string;
  illumination: number; // 0–1
}

export function calculateLunarPhase(date = new Date()): LunarPhase {
  // Known new moon: Jan 6, 2000 18:14 UTC
  const knownNew = new Date(2000, 0, 6, 18, 14, 0).getTime();
  const synodicMonth = 29.53058770576; // days
  const daysSince = (date.getTime() - knownNew) / (1000 * 60 * 60 * 24);
  const cycles = daysSince / synodicMonth;
  const phase = cycles - Math.floor(cycles); // 0–1
  const illumination = (1 - Math.cos(phase * 2 * Math.PI)) / 2;

  let name: string;
  if (phase < 0.03 || phase > 0.97) name = "New Moon";
  else if (phase < 0.22) name = "Waxing Crescent";
  else if (phase < 0.28) name = "First Quarter";
  else if (phase < 0.47) name = "Waxing Gibbous";
  else if (phase < 0.53) name = "Full Moon";
  else if (phase < 0.72) name = "Waning Gibbous";
  else if (phase < 0.78) name = "Last Quarter";
  else name = "Waning Crescent";

  return { phase, name, illumination };
}
