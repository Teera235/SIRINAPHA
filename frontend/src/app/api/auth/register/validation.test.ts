/**
 * Unit tests for registration validation logic
 *
 * Tests validation for all 3 user types: Fisherman, Community_Rep,
 * Corporate_Partner.
 *
 * Requirements: 7.1, 7.2, 7.3
 */

import { describe, it, expect } from "vitest";
import { validateRegistrationRequest } from "./validation";

// ---------------------------------------------------------------------------
// Valid registrations
// ---------------------------------------------------------------------------

describe("validateRegistrationRequest — valid inputs", () => {
  it("accepts a valid Fisherman registration", () => {
    const result = validateRegistrationRequest({
      user_type: "Fisherman",
      display_name: "สมชาย",
      line_user_id: "U1234abc",
      preferred_channel: "line",
      fishing_area_ids: ["area-1"],
    });
    expect(result.valid).toBe(true);
    expect(result.data?.user_type).toBe("Fisherman");
  });

  it("accepts Fisherman with sms preferred_channel", () => {
    const result = validateRegistrationRequest({
      user_type: "Fisherman",
      display_name: "สมชาย",
      line_user_id: "U1234abc",
      preferred_channel: "sms",
      fishing_area_ids: ["area-1", "area-2"],
    });
    expect(result.valid).toBe(true);
  });

  it("accepts a valid Community_Rep registration", () => {
    const result = validateRegistrationRequest({
      user_type: "Community_Rep",
      display_name: "สมหญิง",
      email: "rep@example.com",
      password: "securePass123",
      responsible_area_ids: ["area-c"],
    });
    expect(result.valid).toBe(true);
    expect(result.data?.user_type).toBe("Community_Rep");
  });

  it("accepts a valid Corporate_Partner registration (Silver)", () => {
    const result = validateRegistrationRequest({
      user_type: "Corporate_Partner",
      display_name: "Thai Union",
      email: "corp@example.com",
      password: "securePass123",
      company_name: "Thai Union Group",
      membership_tier: "Silver",
    });
    expect(result.valid).toBe(true);
    expect(result.data?.user_type).toBe("Corporate_Partner");
  });

  it("accepts a valid Corporate_Partner registration (Gold)", () => {
    const result = validateRegistrationRequest({
      user_type: "Corporate_Partner",
      display_name: "CPF",
      email: "cpf@example.com",
      password: "securePass123",
      company_name: "Charoen Pokphand Foods",
      membership_tier: "Gold",
    });
    expect(result.valid).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Missing / invalid base fields
// ---------------------------------------------------------------------------

describe("validateRegistrationRequest — base field errors", () => {
  it("rejects null body", () => {
    const result = validateRegistrationRequest(null);
    expect(result.valid).toBe(false);
    expect(result.error).toContain("Request body is required");
  });

  it("rejects missing user_type", () => {
    const result = validateRegistrationRequest({ display_name: "Test" });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("user_type");
  });

  it("rejects missing display_name", () => {
    const result = validateRegistrationRequest({ user_type: "Fisherman" });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("display_name");
  });

  it("rejects invalid user_type", () => {
    const result = validateRegistrationRequest({
      user_type: "Admin",
      display_name: "Test",
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("user_type must be one of");
  });

  it("rejects empty display_name", () => {
    const result = validateRegistrationRequest({
      user_type: "Fisherman",
      display_name: "   ",
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("display_name");
  });
});

// ---------------------------------------------------------------------------
// Fisherman-specific validation
// ---------------------------------------------------------------------------

describe("validateRegistrationRequest — Fisherman errors", () => {
  it("rejects missing line_user_id", () => {
    const result = validateRegistrationRequest({
      user_type: "Fisherman",
      display_name: "สมชาย",
      preferred_channel: "line",
      fishing_area_ids: ["area-1"],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("line_user_id");
  });

  it("rejects empty fishing_area_ids", () => {
    const result = validateRegistrationRequest({
      user_type: "Fisherman",
      display_name: "สมชาย",
      line_user_id: "U1234",
      preferred_channel: "line",
      fishing_area_ids: [],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("fishing_area_ids");
  });

  it("rejects invalid preferred_channel", () => {
    const result = validateRegistrationRequest({
      user_type: "Fisherman",
      display_name: "สมชาย",
      line_user_id: "U1234",
      preferred_channel: "email",
      fishing_area_ids: ["area-1"],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("preferred_channel");
  });
});

// ---------------------------------------------------------------------------
// Community_Rep-specific validation
// ---------------------------------------------------------------------------

describe("validateRegistrationRequest — Community_Rep errors", () => {
  it("rejects missing email", () => {
    const result = validateRegistrationRequest({
      user_type: "Community_Rep",
      display_name: "สมหญิง",
      password: "pass123",
      responsible_area_ids: ["area-c"],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("email");
  });

  it("rejects missing password", () => {
    const result = validateRegistrationRequest({
      user_type: "Community_Rep",
      display_name: "สมหญิง",
      email: "rep@example.com",
      responsible_area_ids: ["area-c"],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("password");
  });

  it("rejects empty responsible_area_ids", () => {
    const result = validateRegistrationRequest({
      user_type: "Community_Rep",
      display_name: "สมหญิง",
      email: "rep@example.com",
      password: "pass123",
      responsible_area_ids: [],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("responsible_area_ids");
  });
});

// ---------------------------------------------------------------------------
// Corporate_Partner-specific validation
// ---------------------------------------------------------------------------

describe("validateRegistrationRequest — Corporate_Partner errors", () => {
  it("rejects missing email", () => {
    const result = validateRegistrationRequest({
      user_type: "Corporate_Partner",
      display_name: "Corp",
      password: "pass123",
      company_name: "Corp Inc",
      membership_tier: "Silver",
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("email");
  });

  it("rejects missing company_name", () => {
    const result = validateRegistrationRequest({
      user_type: "Corporate_Partner",
      display_name: "Corp",
      email: "corp@example.com",
      password: "pass123",
      membership_tier: "Silver",
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("company_name");
  });

  it("rejects invalid membership_tier", () => {
    const result = validateRegistrationRequest({
      user_type: "Corporate_Partner",
      display_name: "Corp",
      email: "corp@example.com",
      password: "pass123",
      company_name: "Corp Inc",
      membership_tier: "Platinum",
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("membership_tier");
  });

  it("rejects missing membership_tier", () => {
    const result = validateRegistrationRequest({
      user_type: "Corporate_Partner",
      display_name: "Corp",
      email: "corp@example.com",
      password: "pass123",
      company_name: "Corp Inc",
    });
    expect(result.valid).toBe(false);
    expect(result.error).toContain("membership_tier");
  });
});
