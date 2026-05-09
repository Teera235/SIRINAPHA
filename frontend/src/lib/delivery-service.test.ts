/**
 * Unit tests for Delivery Service
 *
 * Tests message delivery orchestration, SMS fallback logic,
 * and delivery logging.
 *
 * Requirements: 6.2, 6.3, 6.8
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  deliverMessage,
  type DeliveryRecipient,
  type DeliveryRequest,
  type DeliveryResult,
} from "./delivery-service";
import type { SmsResult } from "./sms-client";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeFishermanRecipient(
  overrides?: Partial<DeliveryRecipient>
): DeliveryRecipient {
  return {
    user_id: "user-001",
    line_user_id: "U12345",
    phone_number: "+66812345678",
    preferred_channel: "line",
    ...overrides,
  };
}

function makeRequest(
  overrides?: Partial<DeliveryRequest>
): DeliveryRequest {
  return {
    recipient: makeFishermanRecipient(),
    message_type: "daily_fsi",
    thai_text: "📊 สรุป FSI วันนี้: มหาชัย 0.67",
    ...overrides,
  };
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

function createMockSmsSender(options?: { fails?: boolean }) {
  return vi.fn().mockImplementation(
    async (_to: string, _body: string): Promise<SmsResult> => {
      if (options?.fails) {
        return { success: false, error: "SMS send failed" };
      }
      return { success: true, sid: "SM123" };
    }
  );
}

function createMockSupabase() {
  return {
    from: vi.fn().mockReturnValue({
      insert: vi.fn().mockResolvedValue({ error: null }),
    }),
  } as any;
}

// ---------------------------------------------------------------------------
// LINE delivery (happy path)
// ---------------------------------------------------------------------------

describe("deliverMessage — LINE delivery", () => {
  it("delivers via LINE when preferred and available", async () => {
    const lineClient = createMockLineClient();
    const supabase = createMockSupabase();

    const result = await deliverMessage(makeRequest(), {
      lineClient,
      supabase,
    });

    expect(result.channel).toBe("line");
    expect(result.status).toBe("sent");
    expect(lineClient.pushMessage).toHaveBeenCalledTimes(1);
  });

  it("logs delivery to supabase", async () => {
    const lineClient = createMockLineClient();
    const supabase = createMockSupabase();

    await deliverMessage(makeRequest(), { lineClient, supabase });

    expect(supabase.from).toHaveBeenCalledWith("delivery_logs");
  });
});

// ---------------------------------------------------------------------------
// SMS fallback (Requirement 6.8)
// ---------------------------------------------------------------------------

describe("deliverMessage — SMS fallback", () => {
  it("falls back to SMS when LINE fails", async () => {
    const lineClient = createMockLineClient({ fails: true });
    const smsSender = createMockSmsSender();
    const supabase = createMockSupabase();

    const result = await deliverMessage(makeRequest(), {
      lineClient,
      smsSender,
      supabase,
    });

    expect(result.channel).toBe("sms");
    expect(result.status).toBe("fallback_sms");
    expect(smsSender).toHaveBeenCalledTimes(1);
  });

  it("reports failure when both LINE and SMS fail", async () => {
    const lineClient = createMockLineClient({ fails: true });
    const smsSender = createMockSmsSender({ fails: true });
    const supabase = createMockSupabase();

    const result = await deliverMessage(makeRequest(), {
      lineClient,
      smsSender,
      supabase,
    });

    expect(result.status).toBe("failed");
    expect(result.error).toBeDefined();
  });

  it("reports failure when LINE fails and no phone number", async () => {
    const lineClient = createMockLineClient({ fails: true });
    const supabase = createMockSupabase();

    const result = await deliverMessage(
      makeRequest({
        recipient: makeFishermanRecipient({ phone_number: null }),
      }),
      { lineClient, supabase }
    );

    expect(result.status).toBe("failed");
    expect(result.error).toContain("no phone number");
  });
});

// ---------------------------------------------------------------------------
// Direct SMS delivery
// ---------------------------------------------------------------------------

describe("deliverMessage — direct SMS", () => {
  it("sends via SMS when preferred channel is sms", async () => {
    const smsSender = createMockSmsSender();
    const supabase = createMockSupabase();

    const result = await deliverMessage(
      makeRequest({
        recipient: makeFishermanRecipient({
          preferred_channel: "sms",
          line_user_id: null,
        }),
      }),
      { smsSender, supabase }
    );

    expect(result.channel).toBe("sms");
    expect(result.status).toBe("sent");
    expect(smsSender).toHaveBeenCalledTimes(1);
  });

  it("sends via SMS when preferred is line but no line_user_id", async () => {
    const smsSender = createMockSmsSender();
    const supabase = createMockSupabase();

    const result = await deliverMessage(
      makeRequest({
        recipient: makeFishermanRecipient({ line_user_id: null }),
      }),
      { smsSender, supabase }
    );

    expect(result.channel).toBe("sms");
    expect(result.status).toBe("sent");
  });
});

// ---------------------------------------------------------------------------
// No delivery channel available
// ---------------------------------------------------------------------------

describe("deliverMessage — no channel", () => {
  it("fails when no line_user_id and no phone_number", async () => {
    const supabase = createMockSupabase();

    const result = await deliverMessage(
      makeRequest({
        recipient: makeFishermanRecipient({
          preferred_channel: "sms",
          line_user_id: null,
          phone_number: null,
        }),
      }),
      { supabase }
    );

    expect(result.status).toBe("failed");
    expect(result.error).toContain("No delivery channel available");
  });
});

// ---------------------------------------------------------------------------
// Content preview truncation
// ---------------------------------------------------------------------------

describe("deliverMessage — logging", () => {
  it("truncates content_preview to 200 chars in log", async () => {
    const lineClient = createMockLineClient();
    const supabase = createMockSupabase();
    const longText = "ก".repeat(300);

    await deliverMessage(
      makeRequest({ thai_text: longText }),
      { lineClient, supabase }
    );

    const insertCall = supabase.from("delivery_logs").insert;
    expect(insertCall).toHaveBeenCalledWith(
      expect.objectContaining({
        content_preview: expect.any(String),
      })
    );
    // Verify the content_preview is truncated
    const insertArg = insertCall.mock.calls[0][0];
    expect(insertArg.content_preview.length).toBeLessThanOrEqual(200);
  });
});
