/**
 * Mangrove Alert sample data (MVP)
 *
 * In production, replace with: GET /api/alerts/mangrove
 * which queries `mangrove_alerts` table in Supabase.
 *
 * Reference: documents/research/03-methodology.md §3.3
 */

export interface MangroveAlertFeature {
  name: string;
  nameT: string;
  level: "critical" | "warning";
  detail: string;
  ndvi: number;
}

export const MANGROVE_ALERTS: GeoJSON.FeatureCollection<
  GeoJSON.Point,
  MangroveAlertFeature
> = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [100.28, 13.55] },
      properties: {
        name: "Mahachai",
        nameT: "มหาชัย",
        level: "critical",
        detail: "NDVI ลดลง 40% — พื้นที่ป่าชายเลนถูกบุกรุก",
        ndvi: -0.4,
      },
    },
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [98.63, 9.97] },
      properties: {
        name: "Ranong",
        nameT: "ระนอง",
        level: "warning",
        detail: "NDVI ลดลง 15% — การกัดเซาะชายฝั่งเพิ่มขึ้น",
        ndvi: -0.15,
      },
    },
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [99.18, 10.49] },
      properties: {
        name: "Chumphon",
        nameT: "ชุมพร",
        level: "critical",
        detail: "NDVI ลดลง 35% — น้ำเสียจากบ่อกุ้ง",
        ndvi: -0.35,
      },
    },
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [100.60, 7.19] },
      properties: {
        name: "Songkhla",
        nameT: "สงขลา",
        level: "warning",
        detail: "NDVI ลดลง 12% — การขยายตัวของเมือง",
        ndvi: -0.12,
      },
    },
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [98.92, 8.07] },
      properties: {
        name: "Krabi",
        nameT: "กระบี่",
        level: "critical",
        detail: "NDVI ลดลง 28% — การท่องเที่ยวรุกล้ำพื้นที่",
        ndvi: -0.28,
      },
    },
  ],
};

export const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
] as const;
