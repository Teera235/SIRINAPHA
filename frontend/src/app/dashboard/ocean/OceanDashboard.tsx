"use client";

/**
 * OceanDashboard — Full-screen GFW-style fisheries dashboard
 *
 * Composed from modular sub-components in this folder.
 * Theme: dark + cyan accent inspired by Global Fishing Watch [ref 1].
 *
 * Reference: documents/research/04-design-specification.md
 */

import { useEffect, useMemo, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Menu } from "lucide-react";

import { oceanColors, MAP_STYLES, layout } from "./theme";
import {
  computeFSI,
  computeSST,
  computeChla,
  fsiColor,
  sstColor,
  chlaColor,
  renderRaster,
} from "./raster-generators";
import { MANGROVE_ALERTS, type MangroveAlertFeature } from "./mangrove-alerts";
import { oceanPointPopupHTML, mangroveAlertPopupHTML } from "./map-popups";
import LayerControlSidebar from "./LayerControlSidebar";
import TimelineBar from "./TimelineBar";
import {
  CoordinatesPanel,
  StatusBadge,
  MapStyleSwitcher,
} from "./StatusPanels";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OceanDashboard() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const rasterUrls = useRef<{ fsi: string; sst: string; chla: string }>({
    fsi: "",
    sst: "",
    chla: "",
  });
  const popupRef = useRef<mapboxgl.Popup | null>(null);

  // Layer visibility
  const [fsiVisible, setFsiVisible] = useState(true);
  const [sstVisible, setSstVisible] = useState(false);
  const [chlaVisible, setChlaVisible] = useState(false);
  const [mangroveVisible, setMangroveVisible] = useState(true);

  // Map state
  const [pixelCount, setPixelCount] = useState(0);
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mapStyleId, setMapStyleId] = useState("dark-v11");
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number } | null>(null);

  // Responsive state
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const check = () => {
      const mobile = window.innerWidth < layout.mobileBreakpoint;
      setIsMobile(mobile);
      if (mobile) setSidebarOpen(false);
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  const sidebarOffset = useMemo(
    () => (isMobile ? 0 : layout.sidebarWidth),
    [isMobile]
  );

  // -------------------------------------------------------------------------
  // Map setup
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    if (!MAPBOX_TOKEN) {
      setError("ไม่พบ NEXT_PUBLIC_MAPBOX_TOKEN — กรุณาตั้งค่าใน .env.local");
      setLoading(false);
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;
    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [100.5, 10],
      zoom: 4,
      projection: "mercator" as never,
    });
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("load", () => {
      // Generate global rasters (MVP only — replace with tile server in prod)
      const fsi = renderRaster(computeFSI, fsiColor);
      const sst = renderRaster(computeSST, sstColor);
      const chla = renderRaster(computeChla, chlaColor);
      setPixelCount(fsi.pixelCount);
      rasterUrls.current = { fsi: fsi.url, sst: sst.url, chla: chla.url };

      addAllLayers(map, "#151d2e");
      wireUpInteractions(map);
      map.getCanvas().style.cursor = "crosshair";
      setReady(true);
      setLoading(false);
    });

    map.on("error", (e) => setError(String(e.error?.message ?? e)));
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -------------------------------------------------------------------------
  // Layer management
  // -------------------------------------------------------------------------

  function cleanupLayers(m: mapboxgl.Map) {
    const layerIds = [
      "fsi-raster", "fsi-land-mask", "fsi-landuse-mask", "fsi-landcover-mask",
      "sst-raster", "sst-land-mask", "sst-landuse-mask", "sst-landcover-mask",
      "chla-raster", "chla-land-mask", "chla-landuse-mask", "chla-landcover-mask",
      "mangrove-alerts-circle", "mangrove-alerts-label",
    ];
    for (const id of layerIds) if (m.getLayer(id)) m.removeLayer(id);

    const sourceIds = [
      "fsi-global", "sst-global", "chla-global",
      "ne-land-50m", "ne-land-50m-sst", "ne-land-50m-chla",
      "terrain-v2", "terrain-v2-sst", "terrain-v2-chla",
      "mangrove-alerts",
    ];
    for (const id of sourceIds) if (m.getSource(id)) m.removeSource(id);
  }

  function addLandMask(m: mapboxgl.Map, prefix: string, landColor: string) {
    const neSrcId = prefix === "fsi" ? "ne-land-50m" : `ne-land-50m-${prefix}`;
    const terrSrcId = prefix === "fsi" ? "terrain-v2" : `terrain-v2-${prefix}`;

    try {
      if (!m.getSource(neSrcId)) {
        m.addSource(neSrcId, {
          type: "geojson",
          data: "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_land.geojson",
        });
      }
      m.addLayer({
        id: `${prefix}-land-mask`,
        type: "fill",
        source: neSrcId,
        paint: { "fill-color": landColor, "fill-opacity": 1 },
      });
    } catch {}

    try {
      m.addLayer({
        id: `${prefix}-landuse-mask`,
        type: "fill",
        source: "composite",
        "source-layer": "landuse",
        paint: { "fill-color": landColor, "fill-opacity": 1 },
      });
    } catch {}

    try {
      if (!m.getSource(terrSrcId)) {
        m.addSource(terrSrcId, { type: "vector", url: "mapbox://mapbox.mapbox-terrain-v2" });
      }
      m.addLayer({
        id: `${prefix}-landcover-mask`,
        type: "fill",
        source: terrSrcId,
        "source-layer": "landcover",
        paint: { "fill-color": landColor, "fill-opacity": 1 },
      });
    } catch {}
  }

  function addRasterLayer(
    m: mapboxgl.Map,
    id: string,
    sourceId: string,
    url: string,
    landColor: string,
    visible: boolean
  ) {
    m.addSource(sourceId, {
      type: "image",
      url,
      coordinates: [
        [-180, 85],
        [180, 85],
        [180, -85],
        [-180, -85],
      ],
    });
    m.addLayer({
      id,
      type: "raster",
      source: sourceId,
      paint: { "raster-opacity": 0.85, "raster-fade-duration": 0 },
      layout: { visibility: visible ? "visible" : "none" },
    });
    addLandMask(m, id.replace("-raster", ""), landColor);

    const maskPrefix = id.replace("-raster", "");
    const maskIds = [`${maskPrefix}-land-mask`, `${maskPrefix}-landuse-mask`, `${maskPrefix}-landcover-mask`];
    const v = visible ? "visible" : "none";
    for (const mid of maskIds) {
      try { m.setLayoutProperty(mid, "visibility", v); } catch {}
    }
  }

  function addMangroveLayer(m: mapboxgl.Map, visible: boolean) {
    if (!m.getSource("mangrove-alerts")) {
      m.addSource("mangrove-alerts", { type: "geojson", data: MANGROVE_ALERTS });
    }
    m.addLayer({
      id: "mangrove-alerts-circle",
      type: "circle",
      source: "mangrove-alerts",
      paint: {
        "circle-radius": 8,
        "circle-color": ["match", ["get", "level"], "critical", oceanColors.danger, oceanColors.warning],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#fff",
        "circle-opacity": 0.9,
      },
      layout: { visibility: visible ? "visible" : "none" },
    });
    m.addLayer({
      id: "mangrove-alerts-label",
      type: "symbol",
      source: "mangrove-alerts",
      layout: {
        "text-field": ["get", "nameT"],
        "text-size": 11,
        "text-offset": [0, 1.8],
        "text-anchor": "top",
        visibility: visible ? "visible" : "none",
      },
      paint: {
        "text-color": "#fff",
        "text-halo-color": "#000",
        "text-halo-width": 1,
      },
    });
  }

  function addAllLayers(m: mapboxgl.Map, landColor: string) {
    cleanupLayers(m);
    const urls = rasterUrls.current;
    addRasterLayer(m, "fsi-raster", "fsi-global", urls.fsi, landColor, fsiVisible);
    addRasterLayer(m, "sst-raster", "sst-global", urls.sst, landColor, sstVisible);
    addRasterLayer(m, "chla-raster", "chla-global", urls.chla, landColor, chlaVisible);
    addMangroveLayer(m, mangroveVisible);

    // Move labels/roads on top
    const style = m.getStyle();
    if (!style?.layers) return;
    for (const l of style.layers) {
      if (l.type === "symbol") {
        try { m.moveLayer(l.id); } catch {}
      }
    }
    for (const l of style.layers) {
      if (l.type === "line" && (l.id.includes("admin") || l.id.includes("border") || l.id.includes("road"))) {
        try { m.moveLayer(l.id); } catch {}
      }
    }
  }

  function setLayerVisibility(m: mapboxgl.Map, prefix: string, visible: boolean) {
    const v = visible ? "visible" : "none";
    const ids = [
      `${prefix}-raster`,
      `${prefix}-land-mask`,
      `${prefix}-landuse-mask`,
      `${prefix}-landcover-mask`,
    ];
    for (const id of ids) {
      try { m.setLayoutProperty(id, "visibility", v); } catch {}
    }
  }

  // -------------------------------------------------------------------------
  // Interactions
  // -------------------------------------------------------------------------

  function wireUpInteractions(m: mapboxgl.Map) {
    // Track cursor for coordinates panel
    m.on("mousemove", (e) => {
      setCursorCoords({ lat: e.lngLat.lat, lng: e.lngLat.lng });
    });
    m.on("mouseout", () => setCursorCoords(null));

    // Mangrove alert popup
    m.on("click", "mangrove-alerts-circle", (e) => {
      e.originalEvent.stopPropagation();
      const feature = e.features?.[0];
      if (!feature?.properties) return;
      const coords = (feature.geometry as GeoJSON.Point).coordinates.slice() as [number, number];

      if (popupRef.current) popupRef.current.remove();
      popupRef.current = new mapboxgl.Popup({
        closeButton: true,
        maxWidth: `${layout.popupMaxWidth}px`,
        className: "fsi-popup",
      })
        .setLngLat(coords)
        .setHTML(mangroveAlertPopupHTML(feature.properties as MangroveAlertFeature))
        .addTo(m);
    });

    m.on("mouseenter", "mangrove-alerts-circle", () => {
      m.getCanvas().style.cursor = "pointer";
    });
    m.on("mouseleave", "mangrove-alerts-circle", () => {
      m.getCanvas().style.cursor = "crosshair";
    });

    // Ocean click — FSI / SST / Chl-a at clicked point
    m.on("click", (e) => {
      const mangroveHits = m.queryRenderedFeatures(e.point, { layers: ["mangrove-alerts-circle"] });
      if (mangroveHits.length > 0) return;

      const { lat, lng } = e.lngLat;
      if (popupRef.current) popupRef.current.remove();
      popupRef.current = new mapboxgl.Popup({
        closeButton: true,
        maxWidth: `${layout.popupMaxWidth}px`,
        className: "fsi-popup",
      })
        .setLngLat(e.lngLat)
        .setHTML(
          oceanPointPopupHTML({
            lat,
            lng,
            fsiNormalized: computeFSI(lat, lng),
            sstNormalized: computeSST(lat, lng),
            chlaNormalized: computeChla(lat, lng),
          })
        )
        .addTo(m);
    });
  }

  // -------------------------------------------------------------------------
  // React -> Map effects
  // -------------------------------------------------------------------------

  useEffect(() => {
    const m = mapRef.current;
    if (!m || !ready) return;
    setLayerVisibility(m, "fsi", fsiVisible);
  }, [fsiVisible, ready]);

  useEffect(() => {
    const m = mapRef.current;
    if (!m || !ready) return;
    setLayerVisibility(m, "sst", sstVisible);
  }, [sstVisible, ready]);

  useEffect(() => {
    const m = mapRef.current;
    if (!m || !ready) return;
    setLayerVisibility(m, "chla", chlaVisible);
  }, [chlaVisible, ready]);

  useEffect(() => {
    const m = mapRef.current;
    if (!m || !ready) return;
    const v = mangroveVisible ? "visible" : "none";
    try { m.setLayoutProperty("mangrove-alerts-circle", "visibility", v); } catch {}
    try { m.setLayoutProperty("mangrove-alerts-label", "visibility", v); } catch {}
  }, [mangroveVisible, ready]);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  function switchMapStyle(styleId: string) {
    const m = mapRef.current;
    if (!m || styleId === mapStyleId) return;
    setMapStyleId(styleId);
    setReady(false);
    m.setStyle(`mapbox://styles/mapbox/${styleId}`);
    m.once("idle", () => {
      const cfg = MAP_STYLES.find((s) => s.id === styleId);
      try {
        addAllLayers(m, cfg?.landColor ?? "#151d2e");
      } catch (e) {
        console.warn("Re-adding layers after style change failed:", e);
      }
      setReady(true);
    });
  }

  function handleSearch(rawQuery: string) {
    const m = mapRef.current;
    if (!m) return;

    // Try parsing as lat,lng
    const parts = rawQuery.replace(/[,;]/g, " ").trim().split(/\s+/);
    if (parts.length >= 2) {
      const lat = parseFloat(parts[0]);
      const lng = parseFloat(parts[1]);
      if (
        Number.isFinite(lat) && Number.isFinite(lng) &&
        lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
      ) {
        m.flyTo({ center: [lng, lat], zoom: 8, duration: 1500 });
        return;
      }
    }

    // Fall back to Mapbox Geocoding
    fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(rawQuery)}.json?access_token=${MAPBOX_TOKEN}&limit=1`
    )
      .then((r) => r.json())
      .then((data) => {
        if (data.features?.[0]) {
          const [lng, lat] = data.features[0].center;
          m.flyTo({ center: [lng, lat], zoom: 8, duration: 1500 });
        }
      })
      .catch(() => {});
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100vh",
        overflow: "hidden",
        background: oceanColors.surface,
        color: oceanColors.textPrimary,
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      {/* Map canvas */}
      <div ref={mapContainer} style={{ position: "absolute", inset: 0, zIndex: 0 }} />

      {/* Loading overlay */}
      {loading && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            zIndex: 50,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(15, 23, 42, 0.85)",
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                width: 32,
                height: 32,
                border: `3px solid ${oceanColors.teal}`,
                borderTopColor: "transparent",
                borderRadius: "50%",
                animation: "sirinapha-spin 1s linear infinite",
                margin: "0 auto 12px",
              }}
            />
            <div style={{ color: oceanColors.textSecondary, fontSize: 13 }}>
              กำลังโหลดแผนที่และข้อมูลดาวเทียม...
            </div>
          </div>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div
          style={{
            position: "absolute",
            top: 12,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 100,
            background: oceanColors.surface3,
            border: `1px solid ${oceanColors.danger}`,
            padding: "12px 20px",
            borderRadius: 6,
            color: oceanColors.danger,
            maxWidth: 480,
            textAlign: "center",
            fontSize: 13,
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Mobile menu button */}
      {isMobile && !sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          aria-label="เปิดเมนู"
          style={{
            position: "absolute",
            top: 12,
            left: 12,
            zIndex: 20,
            background: "rgba(13, 27, 42, 0.9)",
            border: `1px solid ${oceanColors.borderDefault}`,
            borderRadius: 4,
            padding: 8,
            color: oceanColors.textPrimary,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backdropFilter: "blur(8px)",
            WebkitBackdropFilter: "blur(8px)",
          }}
        >
          <Menu size={20} />
        </button>
      )}

      {/* Mobile overlay to close sidebar */}
      {isMobile && sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "absolute",
            inset: 0,
            zIndex: 25,
            background: "rgba(0, 0, 0, 0.5)",
          }}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <LayerControlSidebar
        fsiVisible={fsiVisible}
        sstVisible={sstVisible}
        chlaVisible={chlaVisible}
        mangroveVisible={mangroveVisible}
        onToggleFSI={setFsiVisible}
        onToggleSST={setSstVisible}
        onToggleChla={setChlaVisible}
        onToggleMangrove={setMangroveVisible}
        onSearch={handleSearch}
        pixelCount={pixelCount}
        isMobile={isMobile}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Top-right status badge */}
      <StatusBadge count={MANGROVE_ALERTS.features.length} label="พื้นที่ติดตาม" />

      {/* Map style switcher */}
      <MapStyleSwitcher
        current={mapStyleId}
        options={MAP_STYLES}
        onChange={switchMapStyle}
      />

      {/* Bottom-left panels */}
      <CoordinatesPanel
        coords={cursorCoords}
        sidebarOffset={sidebarOffset}
        isMobile={isMobile}
      />

      {/* Timeline */}
      <TimelineBar
        selectedMonth={selectedMonth}
        onMonthChange={setSelectedMonth}
        sidebarOffset={sidebarOffset}
        isMobile={isMobile}
      />

      {/* Global keyframes */}
      <style jsx global>{`
        @keyframes sirinapha-spin {
          to { transform: rotate(360deg); }
        }
        @keyframes sirinapha-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.3); }
        }
      `}</style>
    </div>
  );
}
