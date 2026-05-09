/**
 * Map popup HTML builders
 *
 * Produces sanitized HTML strings for Mapbox popups.
 * Uses inline styles because Mapbox popups live outside React tree.
 *
 * Reference: documents/research/04-design-specification.md §4.4.4
 */

import { classifyFSI, FSI_ZONES, oceanColors } from "./theme";
import type { MangroveAlertFeature } from "./mangrove-alerts";

// ---------------------------------------------------------------------------
// Escape helper (prevent XSS in popup content)
// ---------------------------------------------------------------------------

function esc(s: string | number): string {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ---------------------------------------------------------------------------
// Ocean click popup — shows FSI, SST, Chl-a at clicked coordinate
// ---------------------------------------------------------------------------

export function oceanPointPopupHTML(params: {
  lat: number;
  lng: number;
  fsiNormalized: number;
  sstNormalized: number;
  chlaNormalized: number;
}): string {
  const { lat, lng, fsiNormalized, sstNormalized, chlaNormalized } = params;

  const sstCelsius = (15 + sstNormalized * 20).toFixed(1);
  const chlaMg = (chlaNormalized * 10).toFixed(2);
  const zone = classifyFSI(fsiNormalized);
  const zoneInfo = FSI_ZONES[zone];

  const depthApprox = Math.round(20 + fsiNormalized * 80);
  const lunarApprox = (0.3 + fsiNormalized * 0.4).toFixed(2);
  const seasonApprox = (0.4 + fsiNormalized * 0.3).toFixed(2);

  return `<div style="font-family:${oceanColors.textPrimary};padding:6px;min-width:220px;color:${oceanColors.textPrimary}">
    <div style="font-size:10px;color:${oceanColors.textMuted};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;font-family:monospace">
      ${esc(lat.toFixed(4))}° N, ${esc(lng.toFixed(4))}° E
    </div>
    <div style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px;align-items:center">
      <div style="font-size:11px;color:${oceanColors.textMuted}">FSI</div>
      <div>
        <span style="font-size:22px;font-weight:800;color:${zoneInfo.color};font-family:monospace">${esc(fsiNormalized.toFixed(3))}</span>
        <span style="font-size:11px;color:${zoneInfo.color};margin-left:6px">${esc(zoneInfo.label)}</span>
      </div>
      <div style="font-size:11px;color:${oceanColors.textMuted}">SST</div>
      <div>
        <span style="font-size:16px;font-weight:700;color:${oceanColors.amber};font-family:monospace">${esc(sstCelsius)}</span>
        <span style="font-size:11px;color:${oceanColors.textSecondary};margin-left:4px">°C</span>
      </div>
      <div style="font-size:11px;color:${oceanColors.textMuted}">Chl-a</div>
      <div>
        <span style="font-size:16px;font-weight:700;color:${oceanColors.layerNDVI};font-family:monospace">${esc(chlaMg)}</span>
        <span style="font-size:11px;color:${oceanColors.textSecondary};margin-left:4px">mg/m³</span>
      </div>
    </div>
    <div style="margin-top:8px;padding-top:6px;border-top:1px solid ${oceanColors.borderDefault};font-size:10px;color:${oceanColors.textDisabled};font-family:monospace">
      Depth: ~${esc(depthApprox)}m · Lunar: ${esc(lunarApprox)} · Season: ${esc(seasonApprox)}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Mangrove alert popup
// ---------------------------------------------------------------------------

export function mangroveAlertPopupHTML(p: MangroveAlertFeature): string {
  const levelText = p.level === "critical" ? "วิกฤต" : "เตือนภัย";
  const levelColor = p.level === "critical" ? oceanColors.danger : oceanColors.warning;
  const levelEmoji = p.level === "critical" ? "🚨" : "⚠️";

  return `<div style="font-family:Inter,system-ui,sans-serif;padding:4px;color:${oceanColors.textPrimary}">
    <div style="font-weight:700;font-size:14px;margin-bottom:4px;color:${oceanColors.textBright}">
      ${esc(p.nameT)} <span style="color:${oceanColors.textMuted};font-weight:400">(${esc(p.name)})</span>
    </div>
    <div style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;color:#fff;background:${levelColor};margin-bottom:6px">
      ${levelEmoji} ${levelText}
    </div>
    <div style="font-size:12px;color:${oceanColors.textPrimary};margin-top:4px;line-height:1.5">
      ${esc(p.detail)}
    </div>
    <div style="font-size:11px;color:${oceanColors.textMuted};margin-top:4px;font-family:monospace">
      Δ NDVI: ${esc(p.ndvi)}
    </div>
  </div>`;
}
