"use client";

/**
 * Timeline Bar — bottom of screen
 *
 * Shows play button, month slider, and current selected date.
 *
 * Reference: documents/research/04-design-specification.md §4.4.3
 */

import { Play, Pause } from "lucide-react";
import { useState } from "react";
import { oceanColors } from "./theme";
import { MONTHS } from "./mangrove-alerts";

interface TimelineBarProps {
  selectedMonth: number;
  onMonthChange: (m: number) => void;
  year?: number;
  sidebarOffset: number;
  isMobile?: boolean;
}

export default function TimelineBar(p: TimelineBarProps) {
  const [playing, setPlaying] = useState(false);
  const year = p.year ?? new Date().getFullYear();
  const monthLabel = `${MONTHS[p.selectedMonth]} ${year}`;

  const containerStyle: React.CSSProperties = {
    position: "absolute",
    bottom: 0,
    left: p.isMobile ? 0 : p.sidebarOffset,
    right: 0,
    height: p.isMobile ? 64 : 80,
    zIndex: 10,
    display: "flex",
    alignItems: "center",
    padding: p.isMobile ? "0 12px" : "0 24px",
    borderTop: `1px solid ${oceanColors.borderDefault}`,
    background: "rgba(15, 23, 42, 0.92)",
    backdropFilter: "blur(10px)",
    WebkitBackdropFilter: "blur(10px)",
  };

  return (
    <div style={containerStyle} role="region" aria-label="Timeline controls">
      {/* Play/Pause button */}
      <button
        onClick={() => setPlaying(!playing)}
        aria-label={playing ? "หยุด" : "เล่น"}
        style={{
          width: p.isMobile ? 36 : 40,
          height: p.isMobile ? 36 : 40,
          borderRadius: "50%",
          background: oceanColors.info,
          color: oceanColors.textBright,
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginRight: p.isMobile ? 12 : 16,
          flexShrink: 0,
          boxShadow: "0 2px 8px rgba(59, 130, 246, 0.4)",
        }}
      >
        {playing ? <Pause size={16} /> : <Play size={16} style={{ marginLeft: 2 }} />}
      </button>

      {/* Slider area */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 11,
            color: oceanColors.textMuted,
            marginBottom: 6,
          }}
        >
          <span style={{ fontFamily: "monospace" }}>JAN {year}</span>
          <span
            style={{
              color: oceanColors.teal,
              fontWeight: 700,
              fontSize: p.isMobile ? 12 : 14,
              fontFamily: "monospace",
              letterSpacing: 1,
            }}
          >
            {monthLabel}
          </span>
          <span style={{ fontFamily: "monospace" }}>DEC {year}</span>
        </div>

        <input
          type="range"
          min={0}
          max={11}
          step={1}
          value={p.selectedMonth}
          onChange={(e) => p.onMonthChange(Number(e.target.value))}
          aria-label="เลือกเดือน"
          style={{
            width: "100%",
            accentColor: oceanColors.teal,
            cursor: "pointer",
          }}
        />
      </div>
    </div>
  );
}
