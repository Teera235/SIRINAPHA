"use client";

/**
 * OceanConditions — แสดงสภาพทะเลปัจจุบัน
 *
 * แสดง SST, Chl-a และสถานะข้างขึ้นข้างแรม
 * ใช้ภาษาไทยที่เข้าใจง่ายสำหรับชาวประมง
 *
 * Requirements: 9.3
 */

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OceanConditionsProps {
  sst: number; // °C
  chlA: number; // mg/m³
  lunarPhase: number; // 0.0 (เดือนมืด) – 1.0 (เต็มดวง)
  updatedAt: string; // ISO 8601
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSSTStatus(sst: number): { label: string; color: string; emoji: string } {
  if (sst >= 27 && sst <= 30) {
    return { label: "เหมาะสม", color: "text-green-600", emoji: "✅" };
  }
  if (sst >= 24 && sst < 27) {
    return { label: "เย็นเล็กน้อย", color: "text-yellow-600", emoji: "🌡️" };
  }
  if (sst > 30 && sst <= 33) {
    return { label: "อุ่นเล็กน้อย", color: "text-yellow-600", emoji: "🌡️" };
  }
  return { label: "ไม่เหมาะสม", color: "text-red-600", emoji: "⚠️" };
}

function getChlAStatus(chlA: number): { label: string; color: string; emoji: string } {
  if (chlA >= 0.5 && chlA <= 5.0) {
    return { label: "อุดมสมบูรณ์", color: "text-green-600", emoji: "✅" };
  }
  if (chlA < 0.5) {
    return { label: "แพลงก์ตอนน้อย", color: "text-yellow-600", emoji: "📉" };
  }
  return { label: "แพลงก์ตอนมากเกิน", color: "text-red-600", emoji: "⚠️" };
}

function getLunarInfo(phase: number): { label: string; emoji: string; fishingNote: string } {
  if (phase <= 0.1) {
    return { label: "เดือนมืด (แรม)", emoji: "🌑", fishingNote: "ดีมากสำหรับทำประมง" };
  }
  if (phase <= 0.3) {
    return { label: "จันทร์เสี้ยว", emoji: "🌒", fishingNote: "ดีสำหรับทำประมง" };
  }
  if (phase <= 0.5) {
    return { label: "ข้างขึ้น", emoji: "🌓", fishingNote: "ปานกลาง" };
  }
  if (phase <= 0.7) {
    return { label: "เกือบเต็มดวง", emoji: "🌔", fishingNote: "ไม่ค่อยดี" };
  }
  if (phase <= 0.9) {
    return { label: "พระจันทร์เต็มดวง", emoji: "🌕", fishingNote: "ไม่เหมาะสม" };
  }
  return { label: "ข้างแรม", emoji: "🌖", fishingNote: "ปานกลาง" };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OceanConditions({
  sst,
  chlA,
  lunarPhase,
  updatedAt,
}: OceanConditionsProps) {
  const sstStatus = getSSTStatus(sst);
  const chlAStatus = getChlAStatus(chlA);
  const lunar = getLunarInfo(lunarPhase);

  return (
    <div className="bg-white rounded-lg shadow p-3 md:p-4 space-y-3">
      {/* SST */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500">🌡️ อุณหภูมิผิวน้ำทะเล (SST)</p>
          <p className="text-xl font-bold text-gray-800">{sst.toFixed(1)}°C</p>
        </div>
        <span className={`text-sm font-medium ${sstStatus.color}`}>
          {sstStatus.emoji} {sstStatus.label}
        </span>
      </div>

      {/* Chl-a */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500">🧪 คลอโรฟิลล์-เอ (Chl-a)</p>
          <p className="text-xl font-bold text-gray-800">
            {chlA.toFixed(1)} mg/m³
          </p>
        </div>
        <span className={`text-sm font-medium ${chlAStatus.color}`}>
          {chlAStatus.emoji} {chlAStatus.label}
        </span>
      </div>

      {/* Lunar phase */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500">🌙 สถานะข้างขึ้นข้างแรม</p>
          <p className="text-xl font-bold text-gray-800">
            {lunar.emoji} {lunar.label}
          </p>
        </div>
        <span className="text-sm font-medium text-blue-600">
          {lunar.fishingNote}
        </span>
      </div>

      {/* Updated timestamp */}
      <p className="text-xs text-gray-400 text-right pt-1 border-t">
        อัปเดต:{" "}
        {new Date(updatedAt).toLocaleString("th-TH", {
          dateStyle: "medium",
          timeStyle: "short",
        })}
      </p>
    </div>
  );
}
