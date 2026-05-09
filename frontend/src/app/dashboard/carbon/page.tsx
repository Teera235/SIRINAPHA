"use client";

/**
 * Blue Carbon MRV Report — สำหรับ Corporate Partners
 *
 * แสดงรายงาน Blue Carbon ตามระดับสมาชิก (Silver/Gold)
 * ประกอบด้วยพื้นที่, NDVI เฉลี่ย, CO2 ที่กักเก็บ และส่วนแบ่งรายได้
 *
 * Requirements: 8.4, 7.5
 */

import { useState } from "react";
import type { CarbonReport, MembershipTier } from "@/types";

// ---------------------------------------------------------------------------
// Demo data — replaced by Supabase queries in production
// ---------------------------------------------------------------------------

const DEMO_REPORTS: (CarbonReport & { site_name: string })[] = [
  {
    site_name: "ป่าชายเลนมหาชัย เขต A",
    period: {
      start: new Date("2024-01-01"),
      end: new Date("2024-06-30"),
    },
    total_area_rai: 125,
    avg_ndvi: 0.62,
    total_co2_tons: 487.5,
    revenue_sharing: {
      private_sector: 0.63,
      cooperative: 0.2,
      government: 0.1,
      mrv_fee: 0.07,
    },
  },
  {
    site_name: "ป่าชายเลนมหาชัย เขต B",
    period: {
      start: new Date("2024-01-01"),
      end: new Date("2024-06-30"),
    },
    total_area_rai: 89,
    avg_ndvi: 0.55,
    total_co2_tons: 312.0,
    revenue_sharing: {
      private_sector: 0.63,
      cooperative: 0.2,
      government: 0.1,
      mrv_fee: 0.07,
    },
  },
  {
    site_name: "ป่าชายเลนระนอง เขต C",
    period: {
      start: new Date("2024-01-01"),
      end: new Date("2024-06-30"),
    },
    total_area_rai: 210,
    avg_ndvi: 0.68,
    total_co2_tons: 756.0,
    revenue_sharing: {
      private_sector: 0.63,
      cooperative: 0.2,
      government: 0.1,
      mrv_fee: 0.07,
    },
  },
];

// Gold tier sees all reports; Silver sees only first 2
function filterByTier(
  reports: typeof DEMO_REPORTS,
  tier: MembershipTier
): typeof DEMO_REPORTS {
  if (tier === "Gold") return reports;
  // Silver: limited access — only Mahachai data
  return reports.filter((r) => r.site_name.includes("มหาชัย"));
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTHB(amount: number): string {
  return amount.toLocaleString("th-TH", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

const CARBON_PRICE_THB_PER_TON = 350; // approximate market price

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function CarbonReportPage() {
  const [tier, setTier] = useState<MembershipTier>("Gold");
  const reports = filterByTier(DEMO_REPORTS, tier);

  const totalCO2 = reports.reduce((sum, r) => sum + r.total_co2_tons, 0);
  const totalArea = reports.reduce((sum, r) => sum + r.total_area_rai, 0);
  const totalRevenue = totalCO2 * CARBON_PRICE_THB_PER_TON;

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-emerald-700 text-white px-4 py-3 md:px-6 md:py-4 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg md:text-xl font-bold">
              🌿 รายงาน Blue Carbon MRV
            </h1>
            <p className="text-emerald-200 text-xs md:text-sm">
              ข้อมูลคาร์บอนเครดิตจากป่าชายเลน — สำหรับพันธมิตรองค์กร
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="tier-select" className="text-xs text-emerald-200">
              ระดับสมาชิก:
            </label>
            <select
              id="tier-select"
              value={tier}
              onChange={(e) => setTier(e.target.value as MembershipTier)}
              className="text-sm bg-emerald-600 border border-emerald-500 rounded px-2 py-1 text-white"
            >
              <option value="Silver">Silver</option>
              <option value="Gold">Gold</option>
            </select>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-4 md:px-6 md:py-6 space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-xs text-gray-500">🌳 พื้นที่ป่าชายเลนรวม</p>
            <p className="text-2xl font-bold text-gray-800">
              {formatTHB(totalArea)} ไร่
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-xs text-gray-500">💨 CO₂ ที่กักเก็บรวม</p>
            <p className="text-2xl font-bold text-emerald-700">
              {formatTHB(totalCO2)} tCO₂
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-xs text-gray-500">💰 มูลค่าคาร์บอนเครดิต (ประมาณ)</p>
            <p className="text-2xl font-bold text-gray-800">
              ฿{formatTHB(totalRevenue)}
            </p>
            <p className="text-xs text-gray-400">
              @฿{CARBON_PRICE_THB_PER_TON}/tCO₂
            </p>
          </div>
        </div>

        {/* Report table */}
        <section className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-4 py-3 border-b">
            <h2 className="text-base font-semibold text-gray-800">
              📋 รายละเอียดตามพื้นที่
            </h2>
            {tier === "Silver" && (
              <p className="text-xs text-orange-600 mt-1">
                ⚠️ สมาชิก Silver เห็นเฉพาะข้อมูลพื้นที่มหาชัย —{" "}
                <span className="underline">อัปเกรดเป็น Gold</span>{" "}
                เพื่อดูข้อมูลทั้งหมด
              </p>
            )}
          </div>

          {/* Responsive table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs">
                <tr>
                  <th className="text-left px-4 py-2">พื้นที่</th>
                  <th className="text-left px-4 py-2">ช่วงเวลา</th>
                  <th className="text-right px-4 py-2">พื้นที่ (ไร่)</th>
                  <th className="text-right px-4 py-2">NDVI เฉลี่ย</th>
                  <th className="text-right px-4 py-2">CO₂ (tCO₂)</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {reports.map((report, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{report.site_name}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {report.period.start.toLocaleDateString("th-TH", {
                        month: "short",
                        year: "numeric",
                      })}{" "}
                      –{" "}
                      {report.period.end.toLocaleDateString("th-TH", {
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {formatTHB(report.total_area_rai)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {report.avg_ndvi.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-emerald-700">
                      {formatTHB(report.total_co2_tons)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Revenue sharing breakdown */}
        <section className="bg-white rounded-lg shadow p-4">
          <h2 className="text-base font-semibold text-gray-800 mb-3">
            💰 สัดส่วนการแบ่งรายได้คาร์บอนเครดิต
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <RevenueCard
              label="ภาคเอกชน"
              percent={63}
              amount={totalRevenue * 0.63}
              color="bg-blue-500"
            />
            <RevenueCard
              label="สหกรณ์ชุมชน"
              percent={20}
              amount={totalRevenue * 0.2}
              color="bg-green-500"
            />
            <RevenueCard
              label="ภาครัฐ"
              percent={10}
              amount={totalRevenue * 0.1}
              color="bg-purple-500"
            />
            <RevenueCard
              label="ค่าบริการ MRV"
              percent={7}
              amount={totalRevenue * 0.07}
              color="bg-gray-500"
            />
          </div>
        </section>
      </div>
    </main>
  );
}

// ---------------------------------------------------------------------------
// Sub-component
// ---------------------------------------------------------------------------

function RevenueCard({
  label,
  percent,
  amount,
  color,
}: {
  label: string;
  percent: number;
  amount: number;
  color: string;
}) {
  return (
    <div className="border rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className={`w-3 h-3 rounded-full ${color}`} />
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <p className="text-lg font-bold text-gray-800">{percent}%</p>
      <p className="text-xs text-gray-500">
        ≈ ฿{amount.toLocaleString("th-TH", { maximumFractionDigits: 0 })}
      </p>
    </div>
  );
}
