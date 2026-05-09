"use client";

/**
 * AlertPanel — แสดงการแจ้งเตือนป่าชายเลน
 *
 * แสดงรายการแจ้งเตือนทั้งหมดพร้อมระดับความรุนแรง
 * (เตือนภัย / วิกฤต) และรายละเอียดการเปลี่ยนแปลง NDVI
 *
 * Requirements: 9.5
 */

import type { MangroveAlert } from "@/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AlertPanelProps {
  alerts: MangroveAlert[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function alertStyle(level: MangroveAlert["alert_level"]) {
  if (level === "critical") {
    return {
      bg: "bg-red-50 border-red-300",
      badge: "bg-red-600 text-white",
      label: "🔴 วิกฤต",
    };
  }
  return {
    bg: "bg-yellow-50 border-yellow-300",
    badge: "bg-yellow-500 text-white",
    label: "🟡 เตือนภัย",
  };
}

function timeAgo(date: Date): string {
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 60) return `${diffMin} นาทีที่แล้ว`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} ชั่วโมงที่แล้ว`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay} วันที่แล้ว`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AlertPanel({ alerts }: AlertPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4 text-center text-gray-500">
        ✅ ไม่มีการแจ้งเตือนในขณะนี้
      </div>
    );
  }

  // Sort: critical first, then by detected_at descending
  const sorted = [...alerts].sort((a, b) => {
    if (a.alert_level !== b.alert_level) {
      return a.alert_level === "critical" ? -1 : 1;
    }
    return b.detected_at.getTime() - a.detected_at.getTime();
  });

  return (
    <div className="bg-white rounded-lg shadow p-3 md:p-4 space-y-2 max-h-80 overflow-y-auto">
      <p className="text-xs text-gray-500">
        ทั้งหมด {alerts.length} รายการ
      </p>

      {sorted.map((alert) => {
        const style = alertStyle(alert.alert_level);
        return (
          <div
            key={alert.id}
            className={`border rounded-lg p-3 ${style.bg}`}
          >
            <div className="flex items-center justify-between mb-1">
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${style.badge}`}
              >
                {style.label}
              </span>
              <span className="text-xs text-gray-500">
                {timeAgo(alert.detected_at)}
              </span>
            </div>

            <p className="text-sm font-medium text-gray-800">
              พื้นที่: {alert.area_id}
            </p>

            <div className="grid grid-cols-3 gap-2 mt-1 text-xs text-gray-600">
              <div>
                <p className="text-gray-400">NDVI ปัจจุบัน</p>
                <p className="font-semibold">{alert.ndvi_current.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-400">เฉลี่ย 6 เดือน</p>
                <p className="font-semibold">
                  {alert.ndvi_6month_avg.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-gray-400">ลดลง</p>
                <p className="font-semibold text-red-600">
                  {alert.change_percent.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
