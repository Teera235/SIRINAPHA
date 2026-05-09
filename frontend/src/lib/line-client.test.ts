/**
 * Unit tests for LINE Messaging API client
 *
 * Tests push message, reply message, and daily FSI summary delivery.
 *
 * Requirements: 6.2, 6.5
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  pushTextMessage,
  pushDailyFSISummary,
  pushMangroveAlert,
  replyTextMessage,
  type PushResult,
} from "./line-client";

// ---------------------------------------------------------------------------
// Mock LINE client
// ---------------------------------------------------------------------------

function createMockLineClient(options?: { pushFails?: boolean; replyFails?: boolean }) {
  return {
    pushMessage: vi.fn().mockImplementation(async () => {
      if (options?.pushFails) {
        throw new Error("LINE API push failed");
      }
      return {};
    }),
    replyMessage: vi.fn().mockImplementation(async () => {
      if (options?.replyFails) {
        throw new Error("LINE API reply failed");
      }
      return {};
    }),
  } as any;
}

// ---------------------------------------------------------------------------
// pushTextMessage
// ---------------------------------------------------------------------------

describe("pushTextMessage", () => {
  it("sends a text message successfully", async () => {
    const client = createMockLineClient();
    const result = await pushTextMessage("U12345", "สวัสดีครับ", client);

    expect(result.success).toBe(true);
    expect(result.error).toBeUndefined();
    expect(client.pushMessage).toHaveBeenCalledWith({
      to: "U12345",
      messages: [{ type: "text", text: "สวัสดีครับ" }],
    });
  });

  it("returns error when push fails", async () => {
    const client = createMockLineClient({ pushFails: true });
    const result = await pushTextMessage("U12345", "test", client);

    expect(result.success).toBe(false);
    expect(result.error).toContain("LINE API push failed");
  });

  it("handles non-Error exceptions gracefully", async () => {
    const client = {
      pushMessage: vi.fn().mockRejectedValue("string error"),
    } as any;
    const result = await pushTextMessage("U12345", "test", client);

    expect(result.success).toBe(false);
    expect(result.error).toBe("Unknown LINE API error");
  });
});

// ---------------------------------------------------------------------------
// pushDailyFSISummary
// ---------------------------------------------------------------------------

describe("pushDailyFSISummary", () => {
  it("sends FSI summary in Thai", async () => {
    const client = createMockLineClient();
    const thaiText = "📊 สรุป FSI วันนี้: มหาชัย 0.67 (เหมาะสมปานกลาง 🟡)";
    const result = await pushDailyFSISummary("U12345", thaiText, client);

    expect(result.success).toBe(true);
    expect(client.pushMessage).toHaveBeenCalledWith({
      to: "U12345",
      messages: [{ type: "text", text: thaiText }],
    });
  });

  it("returns error when delivery fails", async () => {
    const client = createMockLineClient({ pushFails: true });
    const result = await pushDailyFSISummary("U12345", "test", client);

    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// pushMangroveAlert
// ---------------------------------------------------------------------------

describe("pushMangroveAlert", () => {
  it("sends alert message successfully", async () => {
    const client = createMockLineClient();
    const alertText = "🔴 แจ้งเตือนป่าชายเลน — ระดับวิกฤต";
    const result = await pushMangroveAlert("U12345", alertText, client);

    expect(result.success).toBe(true);
    expect(client.pushMessage).toHaveBeenCalledWith({
      to: "U12345",
      messages: [{ type: "text", text: alertText }],
    });
  });
});

// ---------------------------------------------------------------------------
// replyTextMessage
// ---------------------------------------------------------------------------

describe("replyTextMessage", () => {
  it("replies to a message successfully", async () => {
    const client = createMockLineClient();
    const result = await replyTextMessage("reply-token-123", "ขอบคุณครับ", client);

    expect(result.success).toBe(true);
    expect(client.replyMessage).toHaveBeenCalledWith({
      replyToken: "reply-token-123",
      messages: [{ type: "text", text: "ขอบคุณครับ" }],
    });
  });

  it("returns error when reply fails", async () => {
    const client = createMockLineClient({ replyFails: true });
    const result = await replyTextMessage("reply-token-123", "test", client);

    expect(result.success).toBe(false);
    expect(result.error).toContain("LINE API reply failed");
  });
});
