"use client";

/**
 * YieldSummary — สรุปการทำนายผลผลิตสัตว์น้ำ
 *
 * แสดงการทำนายแยกตามชนิดสัตว์น้ำพร้อมค่าความเชื่อมั่น
 * และแนวโน้มรายได้ 7 วัน / 30 วัน
 *
 * Requirements: 9.4
 */

import type { YieldPrediction } from "@/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface YieldSummaryProps {
  prediction: YieldPrediction;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTHB(amount: number): string {
  return amount.toLocaleString("th-TH");
}

function confidenceBar(confidence: number): string {
  if (confidence >= 0.8) return "bg-green-500";
  if (confidence >= 0.6) return "bg-yellow-500";
  return "bg-red-500";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function YieldSummary({ prediction }: YieldSummaryProps) {
  return (
    <div className="bg-white rounded-lg shadow p-3 md:p-4 space-y-3">
      {/* Species predictions */}
      <div>
        <p className="text-xs text-gray-500 mb-2">ชนิดสัตว์น้ำที่คาดว่าจะจับได้</p>
        <div className="space-y-2">
          {prediction.predictions.map((sp) => (
            <div key={sp.species_name} className="flex items-center gap-2">
              <span className="text-sm font-medium w-20 shrink-0">
                {sp.species_name}
              </span>
              <div className="flex-1">
                <div className="flex items-center justify-between text-xs text-gray-600 mb-0.5">
                  <span>{sp.estimated_catch_kg} กก.</span>
                  <span>ความเชื่อมั่น {(sp.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${confidenceBar(sp.confidence)}`}
                    style={{ width: `${sp.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Revenue forecasts */}
      <div className="border-t pt-3 grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-gray-500">📅 รายได้ 7 วัน (คาดการณ์)</p>
          <p className="text-lg font-bold text-gray-800">
            ฿{formatTHB(prediction.forecast_7day.estimated_revenue_thb)}
          </p>
          <p className="text-xs text-gray-400">
            ฿{formatTHB(prediction.forecast_7day.confidence_lower)} –{" "}
            ฿{formatTHB(prediction.forecast_7day.confidence_upper)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">📅 รายได้ 30 วัน (คาดการณ์)</p>
          <p className="text-lg font-bold text-gray-800">
            ฿{formatTHB(prediction.forecast_30day.estimated_revenue_thb)}
          </p>
          <p className="text-xs text-gray-400">
            ฿{formatTHB(prediction.forecast_30day.confidence_lower)} –{" "}
            ฿{formatTHB(prediction.forecast_30day.confidence_upper)}
          </p>
        </div>
      </div>

      {/* Model info */}
      <p className="text-xs text-gray-400 text-right border-t pt-1">
        โมเดล {prediction.model_version} •{" "}
        {new Date(prediction.predicted_at).toLocaleString("th-TH", {
          dateStyle: "medium",
          timeStyle: "short",
        })}
      </p>
    </div>
  );
}
