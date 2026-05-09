"use client";

/**
 * NDVIChart — กราฟแนวโน้ม NDVI ย้อนหลัง (SVG)
 *
 * แสดงค่า NDVI เป็นอนุกรมเวลาพร้อมเส้นเกณฑ์สุขภาพ
 * ใช้ SVG เพื่อลดขนาด bundle (ไม่ต้องพึ่ง chart library)
 *
 * Requirements: 9.2
 */

import { NDVI_THRESHOLDS } from "@/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface NDVIDataPoint {
  date: string;
  value: number;
}

interface NDVIChartProps {
  data: NDVIDataPoint[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getHealthColor(ndvi: number): string {
  if (ndvi >= NDVI_THRESHOLDS.healthy.min) return "#16a34a";
  if (ndvi >= NDVI_THRESHOLDS.moderate.min) return "#ca8a04";
  if (ndvi >= NDVI_THRESHOLDS.degraded.min) return "#ea580c";
  return "#dc2626";
}

function getHealthLabel(ndvi: number): string {
  if (ndvi >= NDVI_THRESHOLDS.healthy.min) return "สมบูรณ์";
  if (ndvi >= NDVI_THRESHOLDS.moderate.min) return "ปานกลาง";
  if (ndvi >= NDVI_THRESHOLDS.degraded.min) return "เสื่อมโทรม";
  return "วิกฤต";
}

// ---------------------------------------------------------------------------
// Chart constants
// ---------------------------------------------------------------------------

const CHART_W = 600;
const CHART_H = 250;
const PAD = { top: 20, right: 20, bottom: 40, left: 50 };
const PLOT_W = CHART_W - PAD.left - PAD.right;
const PLOT_H = CHART_H - PAD.top - PAD.bottom;

// NDVI range for y-axis
const Y_MIN = 0;
const Y_MAX = 1;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function NDVIChart({ data }: NDVIChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4 text-center text-gray-500">
        ไม่มีข้อมูล NDVI
      </div>
    );
  }

  const xScale = (i: number) => PAD.left + (i / (data.length - 1)) * PLOT_W;
  const yScale = (v: number) =>
    PAD.top + PLOT_H - ((v - Y_MIN) / (Y_MAX - Y_MIN)) * PLOT_H;

  // Build polyline path
  const linePath = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${xScale(i)} ${yScale(d.value)}`)
    .join(" ");

  // Area fill under the line
  const areaPath = `${linePath} L ${xScale(data.length - 1)} ${yScale(Y_MIN)} L ${xScale(0)} ${yScale(Y_MIN)} Z`;

  // Threshold lines
  const thresholds = [
    { value: 0.6, label: "สมบูรณ์", color: "#16a34a" },
    { value: 0.4, label: "ปานกลาง", color: "#ca8a04" },
    { value: 0.2, label: "เสื่อมโทรม", color: "#ea580c" },
  ];

  const latestValue = data[data.length - 1]?.value ?? 0;

  return (
    <div className="bg-white rounded-lg shadow p-3 md:p-4">
      {/* Current status badge */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className="inline-block w-3 h-3 rounded-full"
          style={{ backgroundColor: getHealthColor(latestValue) }}
        />
        <span className="text-sm font-medium">
          ค่าล่าสุด: {latestValue.toFixed(2)} — {getHealthLabel(latestValue)}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full h-auto"
        role="img"
        aria-label="กราฟแนวโน้ม NDVI ป่าชายเลน"
      >
        {/* Threshold reference lines */}
        {thresholds.map((t) => (
          <g key={t.value}>
            <line
              x1={PAD.left}
              y1={yScale(t.value)}
              x2={PAD.left + PLOT_W}
              y2={yScale(t.value)}
              stroke={t.color}
              strokeWidth={1}
              strokeDasharray="4 3"
              opacity={0.5}
            />
            <text
              x={PAD.left + PLOT_W + 2}
              y={yScale(t.value) + 3}
              fontSize={9}
              fill={t.color}
            >
              {t.value}
            </text>
          </g>
        ))}

        {/* Area fill */}
        <path d={areaPath} fill="#16a34a" opacity={0.1} />

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke="#16a34a"
          strokeWidth={2.5}
          strokeLinejoin="round"
        />

        {/* Data points */}
        {data.map((d, i) => (
          <circle
            key={d.date}
            cx={xScale(i)}
            cy={yScale(d.value)}
            r={4}
            fill={getHealthColor(d.value)}
            stroke="#fff"
            strokeWidth={1.5}
          >
            <title>
              {d.date}: NDVI {d.value.toFixed(2)} ({getHealthLabel(d.value)})
            </title>
          </circle>
        ))}

        {/* Y-axis */}
        <line
          x1={PAD.left}
          y1={PAD.top}
          x2={PAD.left}
          y2={PAD.top + PLOT_H}
          stroke="#d1d5db"
          strokeWidth={1}
        />
        {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((v) => (
          <text
            key={v}
            x={PAD.left - 8}
            y={yScale(v) + 4}
            textAnchor="end"
            fontSize={10}
            fill="#6b7280"
          >
            {v.toFixed(1)}
          </text>
        ))}
        <text
          x={12}
          y={PAD.top + PLOT_H / 2}
          textAnchor="middle"
          fontSize={11}
          fill="#374151"
          transform={`rotate(-90, 12, ${PAD.top + PLOT_H / 2})`}
        >
          ค่า NDVI
        </text>

        {/* X-axis labels */}
        {data.map((d, i) => {
          // Show every other label on small datasets, every 3rd on larger
          const step = data.length > 8 ? 3 : 2;
          if (i % step !== 0 && i !== data.length - 1) return null;
          return (
            <text
              key={d.date}
              x={xScale(i)}
              y={PAD.top + PLOT_H + 18}
              textAnchor="middle"
              fontSize={9}
              fill="#6b7280"
            >
              {d.date}
            </text>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-600">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-ndvi-healthy inline-block" />
          สมบูรณ์ (&gt;0.6)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-ndvi-moderate inline-block" />
          ปานกลาง (0.4–0.6)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-ndvi-degraded inline-block" />
          เสื่อมโทรม (0.2–0.4)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-ndvi-critical inline-block" />
          วิกฤต (&lt;0.2)
        </span>
      </div>
    </div>
  );
}
