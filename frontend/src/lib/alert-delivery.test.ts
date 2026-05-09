/**
 * Unit tests for Mangrove Alert Delivery Pipeline
 *
 * Tests alert text formatting and delivery within 30-minute SLA.
 *
 * Requirements: 6.4
 */

import { describe, it, expect, vi } from "vitest";
import {
  formatAlertText,
  deliverMangroveAlert,
  type AlertDeliveryResult,
} from "./alert-delivery";
import type { MangroveAlert } from "@/types";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeAlert(overrides?: Partial<MangroveAlert>): MangroveAlert {
  return {
    id: "alert-001",
    area_id: "area-mahachai",
    alert_level: "warning",
    ndvi_current: 0.35,
    ndvi_6month_avg: 0.55,
    change_percent: -36.4,
    detected_at: new Date("2024-06-15T10:00:00Z"),
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [100.5, 13.5],
          [100.6, 13.5],
          [100.6, 13.6],
          [100.5, 13.6],
          [100.5, 13.5],
        ],
      ],
    },
    ...overrides,
  };
}

function createMockSupabase(users: any[] = []) {
  const insertFn = vi.fn().mockResolvedValue({ error: null });
  return {
    from: vi.fn().mockImplementation((table: string) => {
      if (table === "user_fishing_areas") {
        return {
          select: vi.fn().mockReturnValue({
            eq: vi.fn().mockResolvedValue({
              data: users.map((u) => ({ user_id: u.id })),
            }),
          }),
        };
      }
      if (table === "users") {
        return {
          select: vi.fn().mockReturnValue({
            in: vi.fn().mockReturnValue({
              eq: vi.fn().mockResolvedValue({ data: users }),
            }),
          }),
        };
      }
      if (table === "delivery_logs") {
        return { insert: insertFn };
      }
      return { insert: insertFn };
    }),
    _insertFn: insertFn,
  } as any;
}

function createMockLineClient(options?: { fails?: boolean }) {
  return {
    pushMessage: vi.fn().mockImplementation(async () => {
      if (options?.fails) throw new Error("LINE push failed");
      return {};
    }),
    replyMessage: vi.fn().mockResolvedValue({}),
  } as any;
}

// ---------------------------------------------------------------------------
// formatAlertText
// ---------------------------------------------------------------------------

describe("formatAlertText", () => {
  it("formats warning alert in Thai", () => {
    const text = formatAlertText(makeAlert());

    expect(text).toContain("🟡");
    expect(text).toContain("เตือนภัย");
    expect(text).toContain("area-mahachai");
    expect(text).toContain("0.350");
    expect(text).toContain("0.550");
    expect(text).toContain("36.4%");
  });

  it("formats critical alert in Thai", () => {
    const text = formatAlertText(
      makeAlert({ alert_level: "critical", change_percent: -45.0 })
    );

    expect(text).toContain("🔴");
    expect(text).toContain("วิกฤต");
    expect(text).toContain("45.0%");
  });

  it("includes action prompt", () => {
    const text = formatAlertText(makeAlert());
    expect(text).toContain("กรุณาตรวจสอบพื้นที่");
  });
});

// ---------------------------------------------------------------------------
// deliverMangroveAlert
// ---------------------------------------------------------------------------

describe("deliverMangroveAlert", () => {
  it("delivers to Community_Rep users via LINE", async () => {
    const users = [
      {
        id: "rep-001",
        line_user_id: "U_rep_001",
        phone_number: "+66899999999",
        preferred_channel: "line" as const,
        user_type: "Community_Rep",
      },
    ];
    const supabase = createMockSupabase(users);
    const lineClient = createMockLineClient();

    const result = await deliverMangroveAlert(makeAlert(), {
      supabase,
      lineClient,
    });

    expect(result.alert_id).toBe("alert-001");
    expect(result.recipients_notified).toBe(1);
    expect(result.recipients_failed).toBe(0);
    expect(result.delivered_within_sla).toBe(true);
  });

  it("handles no recipients gracefully", async () => {
    const supabase = createMockSupabase([]);
    const lineClient = createMockLineClient();

    const result = await deliverMangroveAlert(makeAlert(), {
      supabase,
      lineClient,
    });

    expect(result.recipients_notified).toBe(0);
    expect(result.recipients_failed).toBe(0);
    expect(result.delivered_within_sla).toBe(true);
  });

  it("reports delivery time in milliseconds", async () => {
    const supabase = createMockSupabase([]);
    const lineClient = createMockLineClient();

    const result = await deliverMangroveAlert(makeAlert(), {
      supabase,
      lineClient,
    });

    expect(result.delivery_time_ms).toBeGreaterThanOrEqual(0);
    // Should be very fast in tests (< 1 second)
    expect(result.delivery_time_ms).toBeLessThan(5000);
  });
});
