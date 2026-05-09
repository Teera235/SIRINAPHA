"use client";

/**
 * FSIMap — Global Fishing Watch style
 *
 * แผนที่เต็มจอ dark theme พร้อม sidebar layer controls ด้านซ้าย
 * และ legend + timeline ด้านล่าง
 */

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { FSIResult, GeoPoint } from "@/types";
import { FSI_ZONES } from "@/types";
import {
  Layers,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  Fish,
  Leaf,
  Thermometer,
  Waves,
  Moon,
  Calendar,
  Info,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Zone colours — cyan/teal palette like GFW
// ---------------------------------------------------------------------------

const ZONE_COLORS: Record<string, string> = {
  green: "#00e5ff",   // bright cyan
  yellow: "#ffab00",  // amber
  red: "#ff1744",     // red
};

const ZONE_GLOW: Record<string, string> = {
  green: "rgba(0, 229, 255, 0.4)",
  yellow: "rgba(255, 171, 0, 0.4)",
  red: "rgba(255, 23, 68, 0.4)",
};

const ZONE_LABELS: Record<string, string> = {
  green: FSI_ZONES.green.label,
  yellow: FSI_ZONES.yellow.label,
  red: FSI_ZONES.red.label,
};

// ---------------------------------------------------------------------------
// Layer definitions
// ---------------------------------------------------------------------------

interface LayerDef {
  id: string;
  label: string;
  icon: React.ComponentType<{
    size?: number;
    className?: string;
    style?: React.CSSProperties;
  }>;
  color: string;
  defaultOn: boolean;
}

const LAYERS: LayerDef[] = [
  { id: "fsi", label: "ดัชนี FSI", icon: Fish, color: "#00e5ff", defaultOn: true },
  { id: "ndvi", label: "สุขภาพป่าชายเลน (NDVI)", icon: Leaf, color: "#69f0ae", defaultOn: false },
  { id: "sst", label: "อุณหภูมิผิวน้ำ (SST)", icon: Thermometer, color: "#ff6e40", defaultOn: false },
  { id: "chl_a", label: "คลอโรฟิลล์-เอ (Chl-a)", icon: Waves, color: "#40c4ff", defaultOn: false },
  { id: "lunar", label: "ข้างขึ้นข้างแรม", icon: Moon, color: "#b388ff", defaultOn: false },
  { id: "season", label: "ฤดูกาล", icon: Calendar, color: "#ffd740", defaultOn: false },
];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface FSIMapProps {
  fsiResults: FSIResult[];
  onAreaSelect?: (point: GeoPoint) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function FSIMap({ fsiResults, onAreaSelect }: FSIMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);
  const [activeLayers, setActiveLayers] = useState<Set<string>>(
    new Set(LAYERS.filter((l) => l.defaultOn).map((l) => l.id))
  );
  const [selectedResult, setSelectedResult] = useState<FSIResult | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleLayer = (id: string) => {
    setActiveLayers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Init map
  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    const map = L.map(mapRef.current, {
      center: [11.5, 99.5],
      zoom: 6,
      zoomControl: false,
      attributionControl: false,
    });

    // Dark tile layer (CartoDB Dark Matter)
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
        maxZoom: 18,
        subdomains: "abcd",
      }
    ).addTo(map);

    // Zoom control top-right
    L.control.zoom({ position: "topright" }).addTo(map);

    leafletMap.current = map;

    return () => {
      map.remove();
      leafletMap.current = null;
    };
  }, []);

  // Update markers
  useEffect(() => {
    const map = leafletMap.current;
    if (!map) return;

    // Clear markers
    map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) map.removeLayer(layer);
    });

    if (!activeLayers.has("fsi")) return;

    fsiResults.forEach((result) => {
      const color = ZONE_COLORS[result.zone] ?? "#6b7280";
      const glow = ZONE_GLOW[result.zone] ?? "rgba(107,114,128,0.4)";
      const label = ZONE_LABELS[result.zone] ?? result.zone;

      // Outer glow circle
      L.circleMarker([result.location.lat, result.location.lng], {
        radius: 20,
        fillColor: glow,
        color: "transparent",
        fillOpacity: 0.6,
      }).addTo(map);

      // Inner marker
      const marker = L.circleMarker(
        [result.location.lat, result.location.lng],
        {
          radius: 8,
          fillColor: color,
          color: color,
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        }
      ).addTo(map);

      // Dark popup
      const popup = L.popup({
        className: "dark-popup",
        closeButton: true,
        maxWidth: 280,
      }).setContent(`
        <div style="font-family:Inter,sans-serif;color:#e0e0e0;font-size:13px">
          <div style="font-size:11px;color:#90a4ae;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">
            📍 ${result.location.lat.toFixed(4)}, ${result.location.lng.toFixed(4)}
          </div>
          <div style="font-size:22px;font-weight:700;color:${color};margin-bottom:4px">
            FSI ${result.fsi_value.toFixed(2)}
          </div>
          <div style="font-size:12px;color:${color};margin-bottom:10px">${label}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;font-size:11px">
            <span style="color:#78909c">🌡️ SST</span><span style="text-align:right">${result.component_scores.sst_score.toFixed(2)}</span>
            <span style="color:#78909c">🧪 Chl-a</span><span style="text-align:right">${result.component_scores.chl_a_score.toFixed(2)}</span>
            <span style="color:#78909c">🌊 ความลึก</span><span style="text-align:right">${result.component_scores.depth_score.toFixed(2)}</span>
            <span style="color:#78909c">🌙 จันทร์</span><span style="text-align:right">${result.component_scores.lunar_score.toFixed(2)}</span>
            <span style="color:#78909c">🌿 NDVI</span><span style="text-align:right">${result.component_scores.ndvi_score.toFixed(2)}</span>
            <span style="color:#78909c">📅 ฤดูกาล</span><span style="text-align:right">${result.component_scores.season_score.toFixed(2)}</span>
          </div>
          ${!result.data_completeness.is_complete
            ? `<div style="margin-top:8px;padding:4px 8px;background:rgba(255,171,0,0.15);border-radius:2px;font-size:11px;color:#ffab00">
                ⚠️ ข้อมูลไม่สมบูรณ์ — ขาด: ${result.data_completeness.missing_sources.join(", ")}
              </div>`
            : ""
          }
        </div>
      `);

      marker.bindPopup(popup);
      marker.on("click", () => {
        setSelectedResult(result);
        onAreaSelect?.({ lat: result.location.lat, lng: result.location.lng });
      });
    });

    if (fsiResults.length > 0) {
      const bounds = L.latLngBounds(
        fsiResults.map((r) => [r.location.lat, r.location.lng] as [number, number])
      );
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 9 });
    }
  }, [fsiResults, activeLayers, onAreaSelect]);

  return (
    <div className="relative w-full h-[500px] md:h-[600px] rounded-sm overflow-hidden border border-gray-800">
      {/* Map */}
      <div ref={mapRef} className="absolute inset-0 z-0" />

      {/* Left sidebar — layer controls (GFW style) */}
      <div
        className={`absolute top-0 left-0 bottom-0 z-[1000] transition-all duration-300 ${
          sidebarOpen ? "w-64" : "w-10"
        }`}
      >
        {/* Toggle button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute top-3 right-[-32px] z-[1001] w-8 h-8 bg-[#1a2332] border border-[#2a3a4e] rounded-r flex items-center justify-center text-[#90a4ae] hover:text-white transition-colors"
        >
          {sidebarOpen ? <ChevronDown size={14} className="rotate-90" /> : <ChevronRight size={14} />}
        </button>

        {sidebarOpen && (
          <div className="h-full bg-[#0d1b2a]/95 backdrop-blur-sm border-r border-[#1b2838] overflow-y-auto">
            {/* Header */}
            <div className="px-4 py-3 border-b border-[#1b2838] flex items-center gap-2">
              <Layers size={14} className="text-[#00e5ff]" />
              <span className="text-xs font-semibold text-[#90a4ae] uppercase tracking-widest">
                ชั้นข้อมูล
              </span>
            </div>

            {/* Layer toggles */}
            <div className="py-2">
              {LAYERS.map((layer) => {
                const active = activeLayers.has(layer.id);
                const Icon = layer.icon;
                return (
                  <button
                    key={layer.id}
                    onClick={() => toggleLayer(layer.id)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                      active
                        ? "bg-[#1a2332] text-white"
                        : "text-[#546e7a] hover:bg-[#1a2332]/50 hover:text-[#90a4ae]"
                    }`}
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{
                        backgroundColor: active ? layer.color : "transparent",
                        border: `2px solid ${active ? layer.color : "#546e7a"}`,
                      }}
                    />
                    <Icon size={14} style={{ color: active ? layer.color : "#546e7a" }} />
                    <span className="text-xs font-medium">{layer.label}</span>
                    {active ? (
                      <Eye size={12} className="ml-auto text-[#546e7a]" />
                    ) : (
                      <EyeOff size={12} className="ml-auto text-[#37474f]" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Info section */}
            <div className="px-4 py-3 border-t border-[#1b2838]">
              <div className="flex items-center gap-2 mb-2">
                <Info size={12} className="text-[#546e7a]" />
                <span className="text-[10px] text-[#546e7a] uppercase tracking-wider">
                  FSI Scale
                </span>
              </div>
              {/* Gradient bar */}
              <div className="h-2 rounded-full mb-1.5"
                style={{ background: "linear-gradient(to right, #ff1744, #ffab00, #00e5ff)" }}
              />
              <div className="flex justify-between text-[10px] text-[#546e7a]">
                <span>0.0 ไม่เหมาะสม</span>
                <span>1.0 เหมาะสมมาก</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom timeline bar (GFW style) */}
      <div className="absolute bottom-0 left-0 right-0 z-[1000] bg-[#0d1b2a]/90 backdrop-blur-sm border-t border-[#1b2838] px-4 py-2">
        <div className="flex items-center gap-4">
          <div className="text-[10px] text-[#546e7a] uppercase tracking-wider shrink-0">
            ข้อมูลล่าสุด
          </div>
          <div className="flex-1 h-1.5 bg-[#1a2332] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: "85%",
                background: "linear-gradient(to right, #00e5ff, #00e5ff)",
                boxShadow: "0 0 8px rgba(0,229,255,0.5)",
              }}
            />
          </div>
          <div className="text-xs text-[#90a4ae] font-mono shrink-0">
            {new Date().toLocaleDateString("th-TH", { day: "numeric", month: "short", year: "numeric" })}
          </div>
        </div>
      </div>

      {/* Top-right info badge */}
      <div className="absolute top-3 right-14 z-[1000] bg-[#0d1b2a]/90 backdrop-blur-sm border border-[#1b2838] rounded px-3 py-1.5 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-[#00e5ff] animate-pulse" />
        <span className="text-[11px] text-[#90a4ae] font-medium">
          {fsiResults.length} พื้นที่
        </span>
      </div>

      {/* Attribution */}
      <div className="absolute bottom-10 right-2 z-[1000] text-[9px] text-[#37474f]">
        © CARTO · SIRINAPHA Baan-Pla Link
      </div>
    </div>
  );
}
