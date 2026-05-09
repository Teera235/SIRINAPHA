/**
 * Unit tests for LINE webhook route handler
 *
 * Tests signature verification and event parsing.
 *
 * Requirements: 6.2, 6.7
 */

import { describe, it, expect } from "vitest";
import crypto from "crypto";
import { verifySignature } from "@/lib/line-client";

// ---------------------------------------------------------------------------
// verifySignature
// ---------------------------------------------------------------------------

describe("verifySignature", () => {
  const channelSecret = "test-channel-secret-12345";

  it("returns true for valid signature", () => {
    const body = JSON.stringify({ events: [] });
    const expectedSignature = crypto
      .createHmac("SHA256", channelSecret)
      .update(body)
      .digest("base64");

    expect(verifySignature(body, expectedSignature, channelSecret)).toBe(true);
  });

  it("returns false for invalid signature", () => {
    const body = JSON.stringify({ events: [] });
    expect(verifySignature(body, "invalid-signature", channelSecret)).toBe(
      false
    );
  });

  it("returns false for tampered body", () => {
    const originalBody = JSON.stringify({ events: [] });
    const signature = crypto
      .createHmac("SHA256", channelSecret)
      .update(originalBody)
      .digest("base64");

    const tamperedBody = JSON.stringify({ events: [{ type: "message" }] });
    expect(verifySignature(tamperedBody, signature, channelSecret)).toBe(false);
  });

  it("returns false for empty signature", () => {
    const body = JSON.stringify({ events: [] });
    expect(verifySignature(body, "", channelSecret)).toBe(false);
  });

  it("handles empty body", () => {
    const body = "";
    const signature = crypto
      .createHmac("SHA256", channelSecret)
      .update(body)
      .digest("base64");

    expect(verifySignature(body, signature, channelSecret)).toBe(true);
  });

  it("handles different channel secrets", () => {
    const body = JSON.stringify({ events: [] });
    const sig1 = crypto
      .createHmac("SHA256", "secret-1")
      .update(body)
      .digest("base64");
    const sig2 = crypto
      .createHmac("SHA256", "secret-2")
      .update(body)
      .digest("base64");

    expect(sig1).not.toBe(sig2);
    expect(verifySignature(body, sig1, "secret-1")).toBe(true);
    expect(verifySignature(body, sig1, "secret-2")).toBe(false);
  });
});
