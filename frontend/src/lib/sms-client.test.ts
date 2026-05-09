/**
 * Unit tests for SMS client
 *
 * Tests SMS sending and message formatting.
 *
 * Requirements: 6.3, 6.8
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { formatForSms } from "./sms-client";

// ---------------------------------------------------------------------------
// formatForSms
// ---------------------------------------------------------------------------

describe("formatForSms", () => {
  it("returns short text unchanged", () => {
    const text = "📊 FSI มหาชัย: 0.67";
    expect(formatForSms(text)).toBe(text);
  });

  it("truncates text longer than 1600 chars", () => {
    const longText = "ก".repeat(2000);
    const result = formatForSms(longText);
    expect(result.length).toBe(1600);
    expect(result.endsWith("...")).toBe(true);
  });

  it("returns text at exactly 1600 chars unchanged", () => {
    const text = "ก".repeat(1600);
    expect(formatForSms(text)).toBe(text);
  });

  it("preserves Thai characters", () => {
    const text = "สรุป FSI วันนี้: มหาชัย 0.67 (เหมาะสมปานกลาง)";
    expect(formatForSms(text)).toBe(text);
  });
});
