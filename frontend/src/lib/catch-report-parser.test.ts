/**
 * Unit tests for catch report parser
 *
 * Tests parsing of Thai-language catch report messages from fishermen.
 *
 * Requirements: 6.7
 */

import { describe, it, expect } from "vitest";
import { parseCatchReport, type ParsedCatchReport } from "./catch-report-parser";

// ---------------------------------------------------------------------------
// Valid catch reports
// ---------------------------------------------------------------------------

describe("parseCatchReport — valid inputs", () => {
  it("parses a single species report", () => {
    const result = parseCatchReport("ผลจับ ปลาทู 5");
    expect(result).not.toBeNull();
    expect(result!.species).toHaveLength(1);
    expect(result!.species[0]).toEqual({ name: "ปลาทู", weight_kg: 5 });
    expect(result!.total_kg).toBe(5);
  });

  it("parses multiple species", () => {
    const result = parseCatchReport("ผลจับ ปลาทู 5 กุ้ง 3");
    expect(result).not.toBeNull();
    expect(result!.species).toHaveLength(2);
    expect(result!.species[0]).toEqual({ name: "ปลาทู", weight_kg: 5 });
    expect(result!.species[1]).toEqual({ name: "กุ้ง", weight_kg: 3 });
    expect(result!.total_kg).toBe(8);
  });

  it("parses decimal weights", () => {
    const result = parseCatchReport("ผลจับ ปลากะพง 2.5");
    expect(result).not.toBeNull();
    expect(result!.species[0].weight_kg).toBe(2.5);
    expect(result!.total_kg).toBe(2.5);
  });

  it("handles alternative keyword 'จับได้'", () => {
    const result = parseCatchReport("จับได้ ปลาทู 10");
    expect(result).not.toBeNull();
    expect(result!.species[0]).toEqual({ name: "ปลาทู", weight_kg: 10 });
  });

  it("handles alternative keyword 'รายงานผลจับ'", () => {
    const result = parseCatchReport("รายงานผลจับ ปลาทู 7 ปลาหมึก 2");
    expect(result).not.toBeNull();
    expect(result!.species).toHaveLength(2);
    expect(result!.total_kg).toBe(9);
  });

  it("handles English keyword 'catch'", () => {
    const result = parseCatchReport("catch ปลาทู 5");
    expect(result).not.toBeNull();
    expect(result!.species[0].name).toBe("ปลาทู");
  });

  it("handles extra whitespace", () => {
    const result = parseCatchReport("  ผลจับ   ปลาทู   5   กุ้ง   3  ");
    expect(result).not.toBeNull();
    expect(result!.species).toHaveLength(2);
    expect(result!.total_kg).toBe(8);
  });

  it("sets catch_date to today", () => {
    const result = parseCatchReport("ผลจับ ปลาทู 5");
    expect(result).not.toBeNull();
    const today = new Date().toISOString().split("T")[0];
    expect(result!.catch_date).toBe(today);
  });

  it("parses three species", () => {
    const result = parseCatchReport("ผลจับ ปลาทู 5 กุ้ง 3 ปู 2");
    expect(result).not.toBeNull();
    expect(result!.species).toHaveLength(3);
    expect(result!.total_kg).toBe(10);
  });
});

// ---------------------------------------------------------------------------
// Invalid / non-catch messages
// ---------------------------------------------------------------------------

describe("parseCatchReport — invalid inputs", () => {
  it("returns null for empty string", () => {
    expect(parseCatchReport("")).toBeNull();
  });

  it("returns null for whitespace-only string", () => {
    expect(parseCatchReport("   ")).toBeNull();
  });

  it("returns null for unrelated message", () => {
    expect(parseCatchReport("สวัสดีครับ")).toBeNull();
  });

  it("returns null for keyword without data", () => {
    expect(parseCatchReport("ผลจับ")).toBeNull();
  });

  it("returns null for keyword with only species name (no weight)", () => {
    expect(parseCatchReport("ผลจับ ปลาทู")).toBeNull();
  });

  it("returns null for keyword with only numbers", () => {
    expect(parseCatchReport("ผลจับ 5 3")).toBeNull();
  });
});
