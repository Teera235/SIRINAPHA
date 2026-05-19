"use client";

/**
 * OverviewPanel — Satarana-style data cards in sidebar
 *
 * Shows current ocean conditions, FSI health distribution,
 * and 7-day forecast in a scrollable panel.
 */

import { oceanColors } from "./theme";
import { computeFSI, computeSST, computeChla, calculateLunarPhase } from "./raster-generators";

// ---------------------------------------------------------------------------
// Mock data (replace with real API in production)
// ---------------------------------------------------------------------------

const AREAS = [
  { id: "mahachai", name: "มหาชัย", lat: 13.55, lng: 100.28 },
  { id: "ranong", name: "ระนอง", lat: 9.97, lng: 98.63 },
  { id: "chumphon", name: "ชุมพร", lat: 10.49, lng: 99.18 },
];

function generateForecast() {
  const days: Array<{ date: string; sst: string; chla: string; fsi: string }> = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() + i);
    const dateStr = d.toLocaleDateString("th-TH", { month: "short", day: "numeric" });
    days.push({
      date: dateStr,
      sst: (27 + Math.random() * 3).toFixed(1),
      chla: (0.5 + Math.random() * 4).toFixed(1),
      fsi: (0.4 + Math.random() * 0.5).toFixed(2),
    });
  }
  return days;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface OverviewPanelProps {
  visible: boolean;
}

export default function OverviewPanel({ visible }: OverviewPanelProps) {
  if (!visible) return null;

  const lunar = calculateLunarPhase();
  const area = AREAS[0]; // Default to Mahachai
  const fsiVal = computeFSI(area.lat, area.lng);
  const sstVal = computeSST(area.lat, area.lng);
  const chlaVal = computeChla(area.lat, area.lng);

  const sstC = (15 + sstVal * 20).toFixed(1);
  const chlaMg = (chlaVal * 10).toFixed(1);
  const forecast = generateForecast();

  // FSI zone distribution (simulated)
  const greenPct = 35;
  const yellowPct = 45;
  const redPct = 20;

  return (
    <div style={{ padding: "0 16px 16px", display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Current Conditions Card */}
      <div style={cardStyle}>
        <div style={cardHeaderStyle}>สภาพทะเลปัจจุบัน</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
          <MetricBox
            icon={<ThermIcon />}
            label="SST"
            value={`${sstC}`}
            unit="C"
            sub={`ช่วงเหมาะสม 27-30`}
          />
          <MetricBox
            icon={<DropIcon />}
            label="Chl-a"
            value={`${chlaMg}`}
            unit="mg/m3"
            sub={`ช่วงเหมาะสม 0.5-5.0`}
          />
          <MetricBox
            icon={<WindIcon />}
            label="Lunar"
            value={`${(lunar.illumination * 100).toFixed(0)}%`}
            unit=""
            sub={lunar.name}
          />
          <MetricBox
            icon={<WaveIcon />}
            label="FSI"
            value={fsiVal.toFixed(2)}
            unit=""
            sub={fsiVal >= 0.7 ? "เหมาะสมมาก" : fsiVal >= 0.4 ? "ปานกลาง" : "ไม่เหมาะสม"}
            highlight={fsiVal >= 0.7 ? oceanColors.cyan : fsiVal >= 0.4 ? oceanColors.amber : oceanColors.red}
          />
        </div>
      </div>

      {/* Health Distribution Card */}
      <div style={cardStyle}>
        <div style={cardHeaderStyle}>FSI Distribution</div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 12 }}>
          {/* Simple donut-like ring */}
          <div style={{ position: "relative", width: 64, height: 64, flexShrink: 0 }}>
            <svg viewBox="0 0 36 36" style={{ width: 64, height: 64, transform: "rotate(-90deg)" }}>
              <circle cx="18" cy="18" r="14" fill="none" stroke={oceanColors.surface3} strokeWidth="4" />
              <circle cx="18" cy="18" r="14" fill="none" stroke={oceanColors.cyan} strokeWidth="4"
                strokeDasharray={`${greenPct * 0.88} 88`} strokeDashoffset="0" />
              <circle cx="18" cy="18" r="14" fill="none" stroke={oceanColors.amber} strokeWidth="4"
                strokeDasharray={`${yellowPct * 0.88} 88`} strokeDashoffset={`${-greenPct * 0.88}`} />
              <circle cx="18" cy="18" r="14" fill="none" stroke={oceanColors.red} strokeWidth="4"
                strokeDasharray={`${redPct * 0.88} 88`} strokeDashoffset={`${-(greenPct + yellowPct) * 0.88}`} />
            </svg>
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: oceanColors.textPrimary }}>{greenPct}%</span>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12 }}>
            <LegendRow color={oceanColors.cyan} label="เหมาะสมมาก" value={`${greenPct}%`} />
            <LegendRow color={oceanColors.amber} label="ปานกลาง" value={`${yellowPct}%`} />
            <LegendRow color={oceanColors.red} label="ไม่เหมาะสม" value={`${redPct}%`} />
          </div>
        </div>
      </div>

      {/* 7-Day Forecast Card */}
      <div style={cardStyle}>
        <div style={cardHeaderStyle}>พยากรณ์ 7 วัน</div>
        <div style={{ marginTop: 8 }}>
          {/* Table header */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 50px 50px 50px", gap: 4, fontSize: 10, color: oceanColors.textMuted, marginBottom: 6, paddingBottom: 6, borderBottom: `1px solid ${oceanColors.borderSubtle}` }}>
            <span>วันที่</span>
            <span style={{ textAlign: "right" }}>SST</span>
            <span style={{ textAlign: "right" }}>Chl-a</span>
            <span style={{ textAlign: "right" }}>FSI</span>
          </div>
          {/* Rows */}
          {forecast.map((row, i) => (
            <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 50px 50px 50px", gap: 4, fontSize: 11, color: oceanColors.textSecondary, padding: "4px 0", borderBottom: i < forecast.length - 1 ? `1px solid ${oceanColors.borderSubtle}` : "none" }}>
              <span style={{ color: oceanColors.textPrimary }}>{row.date}</span>
              <span style={{ textAlign: "right", fontFamily: "monospace" }}>{row.sst}</span>
              <span style={{ textAlign: "right", fontFamily: "monospace" }}>{row.chla}</span>
              <span style={{ textAlign: "right", fontFamily: "monospace", color: parseFloat(row.fsi) >= 0.7 ? oceanColors.cyan : parseFloat(row.fsi) >= 0.4 ? oceanColors.amber : oceanColors.red }}>{row.fsi}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Area selector hint */}
      <div style={{ fontSize: 11, color: oceanColors.textMuted, textAlign: "center", padding: "8px 0" }}>
        คลิกบนแผนที่เพื่อดูข้อมูลจุดที่ต้องการ
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MetricBox({ icon, label, value, unit, sub, highlight }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  unit: string;
  sub: string;
  highlight?: string;
}) {
  return (
    <div style={{ background: oceanColors.surface2, borderRadius: 8, padding: "10px 12px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <span style={{ color: oceanColors.textMuted }}>{icon}</span>
        <span style={{ fontSize: 10, color: oceanColors.textMuted, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 3 }}>
        <span style={{ fontSize: 22, fontWeight: 700, color: highlight || oceanColors.textPrimary, fontFamily: "monospace" }}>{value}</span>
        {unit && <span style={{ fontSize: 11, color: oceanColors.textMuted }}>{unit}</span>}
      </div>
      <div style={{ fontSize: 10, color: oceanColors.textDisabled, marginTop: 2 }}>{sub}</div>
    </div>
  );
}

function LegendRow({ color, label, value }: { color: string; label: string; value: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
      <span style={{ color: oceanColors.textSecondary, flex: 1 }}>{label}</span>
      <span style={{ color: oceanColors.textPrimary, fontWeight: 600, fontFamily: "monospace" }}>{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Icons (inline SVG, 14px)
// ---------------------------------------------------------------------------

function ThermIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
    </svg>
  );
}

function DropIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    </svg>
  );
}

function WindIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="10" /><path d="M12 2a7 7 0 0 0 0 20 10 10 0 0 1 0-20z" fill="currentColor" fillOpacity="0.2" />
    </svg>
  );
}

function WaveIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M2 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0" /><path d="M2 17c2-2 4-2 6 0s4 2 6 0 4-2 6 0" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  background: oceanColors.panel,
  border: `1px solid ${oceanColors.borderSubtle}`,
  borderRadius: 10,
  padding: 16,
};

const cardHeaderStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: oceanColors.textPrimary,
  textTransform: "uppercase",
  letterSpacing: 0.5,
};
