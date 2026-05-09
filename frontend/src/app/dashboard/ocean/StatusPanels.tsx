"use client";

/**
 * Status Panels — bottom-left floating chips
 *
 * - Coordinates display (real-time from cursor)
 * - Lunar phase indicator
 * - Top-right badge showing active areas
 *
 * Reference: documents/research/04-design-specification.md §4.4.5, §4.4.6, §4.4.7
 */

import { oceanColors } from "./theme";
import { calculateLunarPhase } from "./raster-generators";

// ---------------------------------------------------------------------------
// Coordinates Panel
// ---------------------------------------------------------------------------

export function CoordinatesPanel({
  coords,
  sidebarOffset,
  isMobile,
}: {
  coords: { lat: number; lng: number } | null;
  sidebarOffset: number;
  isMobile?: boolean;
}) {
  if (isMobile) return null; // hide on mobile

  return (
    <div
      style={{
        position: "absolute",
        bottom: 88,
        left: sidebarOffset + 8,
        zIndex: 10,
        display: "flex",
        gap: 8,
      }}
    >
      <div
        style={{
          background: "rgba(15, 23, 42, 0.9)",
          border: `1px solid ${oceanColors.borderDefault}`,
          borderRadius: 6,
          padding: "5px 12px",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          fontFamily: "monospace",
          fontSize: 11,
        }}
      >
        {coords ? (
          <span style={{ color: oceanColors.textSecondary }}>
            <span style={{ color: oceanColors.teal }}>{coords.lat.toFixed(4)}</span>
            <span style={{ color: oceanColors.textDisabled }}> N </span>
            <span style={{ color: oceanColors.teal }}>{coords.lng.toFixed(4)}</span>
            <span style={{ color: oceanColors.textDisabled }}> E</span>
          </span>
        ) : (
          <span style={{ color: oceanColors.textDisabled }}>เลื่อน cursor บนแผนที่</span>
        )}
      </div>

      <LunarChip />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Lunar Phase Chip
// ---------------------------------------------------------------------------

function LunarChip() {
  const lunar = calculateLunarPhase();

  return (
    <div
      style={{
        background: "rgba(15, 23, 42, 0.9)",
        border: `1px solid ${oceanColors.borderDefault}`,
        borderRadius: 6,
        padding: "5px 12px",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={oceanColors.layerLunar} strokeWidth="2" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <path
          d="M12 2a7 7 0 0 0 0 20 10 10 0 0 1 0-20z"
          fill={oceanColors.layerLunar}
          fillOpacity="0.3"
        />
      </svg>
      <span style={{ fontSize: 11, color: oceanColors.layerLunar, fontFamily: "monospace" }}>
        {lunar.name}
      </span>
      <span style={{ fontSize: 10, color: oceanColors.textDisabled }}>·</span>
      <span style={{ fontSize: 11, color: oceanColors.textSecondary, fontFamily: "monospace" }}>
        {(lunar.illumination * 100).toFixed(0)}%
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status Badge (top-right)
// ---------------------------------------------------------------------------

export function StatusBadge({ count, label }: { count: number; label: string }) {
  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        right: 56,
        zIndex: 10,
        background: "rgba(13, 27, 42, 0.9)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
        border: `1px solid ${oceanColors.borderSubtle}`,
        borderRadius: 4,
        padding: "6px 12px",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
      aria-live="polite"
    >
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: oceanColors.cyan,
          animation: "sirinapha-pulse 2s ease-in-out infinite",
        }}
      />
      <span style={{ fontSize: 11, color: oceanColors.textSecondary, fontWeight: 500 }}>
        {count} {label}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Map Style Switcher (top-right, below StatusBadge)
// ---------------------------------------------------------------------------

export function MapStyleSwitcher({
  current,
  options,
  onChange,
}: {
  current: string;
  options: ReadonlyArray<{ id: string; label: string }>;
  onChange: (id: string) => void;
}) {
  return (
    <div
      style={{
        position: "absolute",
        top: 50,
        right: 56,
        zIndex: 10,
        background: "rgba(13, 27, 42, 0.9)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
        border: `1px solid ${oceanColors.borderSubtle}`,
        borderRadius: 4,
        padding: 3,
        display: "flex",
        gap: 2,
      }}
    >
      {options.map((opt) => (
        <button
          key={opt.id}
          onClick={() => onChange(opt.id)}
          aria-pressed={current === opt.id}
          style={{
            padding: "4px 10px",
            fontSize: 10,
            fontWeight: 500,
            border: "none",
            borderRadius: 2,
            cursor: "pointer",
            background: current === opt.id ? oceanColors.surface2 : "transparent",
            color: current === opt.id ? oceanColors.cyan : oceanColors.textMuted,
            letterSpacing: 0.5,
            transition: "all 150ms",
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
