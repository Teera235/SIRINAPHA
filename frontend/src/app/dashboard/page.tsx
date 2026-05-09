"use client";

/**
 * SIRINAPHA Ocean Data Platform — Full-screen map dashboard
 *
 * Style: Global Fishing Watch inspired (dark theme + cyan accent)
 * See: documents/research/04-design-specification.md
 *
 * The OceanDashboard component is loaded dynamically (SSR disabled) because
 * Mapbox GL JS depends on `window` / `document`.
 */

import dynamic from "next/dynamic";

const OceanDashboard = dynamic(() => import("./ocean"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-screen bg-[#0f172a] flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-teal-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">กำลังโหลดแผนที่...</p>
      </div>
    </div>
  ),
});

export default function DashboardPage() {
  return <OceanDashboard />;
}
