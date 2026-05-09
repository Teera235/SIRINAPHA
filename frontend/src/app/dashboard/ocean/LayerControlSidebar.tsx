"use client";

/**
 * Layer Control Sidebar — GFW-style
 *
 * Left sidebar with:
 * - Brand header
 * - Search (coordinates or place name)
 * - Data layer toggles with gradient legends
 * - Coastal monitoring toggles
 *
 * Reference: documents/research/04-design-specification.md §4.4.1
 */

import { useState } from "react";
import { Menu, Search, X } from "lucide-react";
import { oceanColors, gradients } from "./theme";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface LayerControlSidebarProps {
  fsiVisible: boolean;
  sstVisible: boolean;
  chlaVisible: boolean;
  mangroveVisible: boolean;
  onToggleFSI: (v: boolean) => void;
  onToggleSST: (v: boolean) => void;
  onToggleChla: (v: boolean) => void;
  onToggleMangrove: (v: boolean) => void;
  onSearch: (query: string) => void;
  pixelCount: number;
  isMobile?: boolean;
  isOpen?: boolean;
  onClose?: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LayerControlSidebar(props: LayerControlSidebarProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    props.onSearch(query);
  };

  const containerStyle: React.CSSProperties = props.isMobile
    ? {
        position: "absolute",
        top: 0,
        left: 0,
        width: "min(320px, 85vw)",
        height: "100%",
        background: oceanColors.surface,
        borderRight: `1px solid ${oceanColors.borderDefault}`,
        zIndex: 30,
        display: props.isOpen ? "flex" : "none",
        flexDirection: "column",
        overflowY: "auto",
        boxShadow: "4px 0 24px rgba(0, 0, 0, 0.5)",
      }
    : {
        position: "absolute",
        top: 0,
        left: 0,
        width: 320,
        height: "100%",
        background: oceanColors.surface,
        borderRight: `1px solid ${oceanColors.borderDefault}`,
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
      };

  return (
    <aside style={containerStyle} aria-label="Map layer controls">
      {/* Brand header */}
      <header
        style={{
          padding: 20,
          borderBottom: `1px solid ${oceanColors.borderDefault}`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: oceanColors.textBright,
            letterSpacing: 2,
          }}
        >
          SIRINAPHA
        </span>
        {props.isMobile && props.onClose ? (
          <button
            onClick={props.onClose}
            aria-label="ปิดเมนู"
            style={{
              color: oceanColors.textMuted,
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: 4,
            }}
          >
            <X size={18} />
          </button>
        ) : (
          <Menu size={18} color={oceanColors.textMuted} />
        )}
      </header>

      {/* Body */}
      <div style={{ padding: 20, flex: 1 }}>
        {/* Search */}
        <form onSubmit={handleSubmit} style={{ marginBottom: 24, display: "flex", gap: 4 }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ค้นหาสถานที่หรือพิกัด..."
            aria-label="ค้นหาสถานที่"
            style={{
              flex: 1,
              padding: "8px 10px",
              fontSize: 12,
              background: oceanColors.surface3,
              border: `1px solid ${oceanColors.borderDefault}`,
              borderRadius: 4,
              color: oceanColors.textPrimary,
              outline: "none",
            }}
          />
          <button
            type="submit"
            aria-label="ค้นหา"
            style={{
              padding: "8px 10px",
              background: oceanColors.borderDefault,
              border: `1px solid ${oceanColors.borderLight}`,
              borderRadius: 4,
              color: oceanColors.textSecondary,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
            }}
          >
            <Search size={14} />
          </button>
        </form>

        {/* Section: Data Layers */}
        <SectionLabel>Data Layers</SectionLabel>

        <LayerToggle
          label="Global Fishery Suitability (FSI)"
          checked={props.fsiVisible}
          onChange={props.onToggleFSI}
          accent="#3b82f6"
          gradient={gradients.fsi}
          legendLeft="0.0 Low"
          legendMid="0.5"
          legendRight="1.0 High"
          footnote={`${props.pixelCount.toLocaleString()} pixels · 0.5° global`}
        />

        <div style={{ height: 16 }} />

        <LayerToggle
          label="Sea Surface Temperature (SST)"
          checked={props.sstVisible}
          onChange={props.onToggleSST}
          accent={oceanColors.layerSST}
          gradient={gradients.sst}
          legendLeft="15°C Cold"
          legendMid="25°C"
          legendRight="35°C Warm"
        />

        <div style={{ height: 16 }} />

        <LayerToggle
          label="Chlorophyll-a (MODIS)"
          checked={props.chlaVisible}
          onChange={props.onToggleChla}
          accent={oceanColors.success}
          gradient={gradients.chla}
          legendLeft="Low"
          legendMid="Med"
          legendRight="High"
        />

        <div style={{ height: 28 }} />

        {/* Section: Coastal Monitoring */}
        <SectionLabel>Coastal Monitoring</SectionLabel>

        <SimpleToggle
          label="Mangrove Alerts (NDVI)"
          checked={props.mangroveVisible}
          onChange={props.onToggleMangrove}
          accent={oceanColors.success}
        />

        <SimpleToggle
          label="Vessel Presence (AIS)"
          checked={false}
          onChange={() => {}}
          accent={oceanColors.layerVessel}
          disabled
          badge="Phase 2"
        />
      </div>

      {/* Footer */}
      <footer
        style={{
          padding: "12px 20px",
          borderTop: `1px solid ${oceanColors.borderDefault}`,
          fontSize: 10,
          color: oceanColors.textDisabled,
          flexShrink: 0,
        }}
      >
        <div>© NOAA · NASA · ESA · CARTO</div>
        <div style={{ marginTop: 2 }}>SIRINAPHA Baan-Pla Link v0.1</div>
      </footer>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 10,
        color: oceanColors.textMuted,
        textTransform: "uppercase",
        letterSpacing: 2,
        marginBottom: 16,
        fontWeight: 600,
      }}
    >
      {children}
    </div>
  );
}

interface LayerToggleProps {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  accent: string;
  gradient: string;
  legendLeft: string;
  legendMid: string;
  legendRight: string;
  footnote?: string;
}

function LayerToggle(p: LayerToggleProps) {
  return (
    <div>
      <label
        style={{
          display: "flex",
          alignItems: "center",
          cursor: "pointer",
          marginBottom: 8,
        }}
      >
        <input
          type="checkbox"
          checked={p.checked}
          onChange={(e) => p.onChange(e.target.checked)}
          style={{ width: 18, height: 18, accentColor: p.accent, cursor: "pointer" }}
        />
        <span style={{ marginLeft: 12, fontSize: 13, color: oceanColors.textPrimary }}>
          {p.label}
        </span>
      </label>
      <div
        style={{
          marginLeft: 30,
          height: 10,
          borderRadius: 3,
          background: p.gradient,
          opacity: p.checked ? 1 : 0.4,
          transition: "opacity 200ms",
        }}
      />
      <div
        style={{
          marginLeft: 30,
          display: "flex",
          justifyContent: "space-between",
          fontSize: 10,
          color: oceanColors.textMuted,
          marginTop: 4,
        }}
      >
        <span>{p.legendLeft}</span>
        <span>{p.legendMid}</span>
        <span>{p.legendRight}</span>
      </div>
      {p.footnote && (
        <div
          style={{
            marginLeft: 30,
            fontSize: 10,
            color: oceanColors.textDisabled,
            marginTop: 4,
            fontFamily: "monospace",
          }}
        >
          {p.footnote}
        </div>
      )}
    </div>
  );
}

interface SimpleToggleProps {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  accent: string;
  disabled?: boolean;
  badge?: string;
}

function SimpleToggle(p: SimpleToggleProps) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        cursor: p.disabled ? "not-allowed" : "pointer",
        marginBottom: 10,
        opacity: p.disabled ? 0.5 : 1,
      }}
    >
      <input
        type="checkbox"
        checked={p.checked}
        onChange={(e) => p.onChange(e.target.checked)}
        disabled={p.disabled}
        style={{
          width: 16,
          height: 16,
          accentColor: p.accent,
          cursor: p.disabled ? "not-allowed" : "pointer",
        }}
      />
      <span style={{ marginLeft: 12, fontSize: 13, color: oceanColors.textPrimary, flex: 1 }}>
        {p.label}
      </span>
      {p.badge && (
        <span
          style={{
            fontSize: 9,
            padding: "2px 6px",
            background: oceanColors.surface3,
            color: oceanColors.textMuted,
            borderRadius: 3,
            border: `1px solid ${oceanColors.borderDefault}`,
            letterSpacing: 0.5,
          }}
        >
          {p.badge}
        </span>
      )}
    </label>
  );
}
