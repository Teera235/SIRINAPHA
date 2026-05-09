/**
 * Unit tests for auth helper functions
 *
 * Tests role checks, tier access, and allowed area ID logic
 * for all 3 user types.
 *
 * Requirements: 7.1, 7.4, 7.5
 */

import { describe, it, expect } from "vitest";
import {
  hasRole,
  hasTierAccess,
  getAllowedAreaIds,
  type UserWithAreas,
} from "./auth";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeFisherman(overrides?: Partial<UserWithAreas>): UserWithAreas {
  return {
    id: "fisher-001",
    user_type: "Fisherman",
    display_name: "สมชาย",
    preferred_channel: "line",
    line_user_id: "U1234",
    phone_number: null,
    company_name: null,
    membership_tier: null,
    created_at: "2024-01-01T00:00:00Z",
    fishing_area_ids: ["area-a", "area-b"],
    responsible_area_ids: [],
    ...overrides,
  };
}

function makeCommunityRep(overrides?: Partial<UserWithAreas>): UserWithAreas {
  return {
    id: "rep-001",
    user_type: "Community_Rep",
    display_name: "สมหญิง",
    preferred_channel: "line",
    line_user_id: null,
    phone_number: null,
    company_name: null,
    membership_tier: null,
    created_at: "2024-01-01T00:00:00Z",
    fishing_area_ids: [],
    responsible_area_ids: ["area-c", "area-d"],
    ...overrides,
  };
}

function makeCorporatePartner(
  overrides?: Partial<UserWithAreas>
): UserWithAreas {
  return {
    id: "corp-001",
    user_type: "Corporate_Partner",
    display_name: "Thai Union",
    preferred_channel: "line",
    line_user_id: null,
    phone_number: null,
    company_name: "Thai Union Group",
    membership_tier: "Gold",
    created_at: "2024-01-01T00:00:00Z",
    fishing_area_ids: [],
    responsible_area_ids: [],
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// hasRole
// ---------------------------------------------------------------------------

describe("hasRole", () => {
  it("returns true when user_type matches", () => {
    expect(hasRole(makeFisherman(), "Fisherman")).toBe(true);
    expect(hasRole(makeCommunityRep(), "Community_Rep")).toBe(true);
    expect(hasRole(makeCorporatePartner(), "Corporate_Partner")).toBe(true);
  });

  it("returns false when user_type does not match", () => {
    expect(hasRole(makeFisherman(), "Community_Rep")).toBe(false);
    expect(hasRole(makeCommunityRep(), "Corporate_Partner")).toBe(false);
    expect(hasRole(makeCorporatePartner(), "Fisherman")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// hasTierAccess
// ---------------------------------------------------------------------------

describe("hasTierAccess", () => {
  it("Gold tier has access to Silver-required resources", () => {
    const gold = makeCorporatePartner({ membership_tier: "Gold" });
    expect(hasTierAccess(gold, "Silver")).toBe(true);
  });

  it("Gold tier has access to Gold-required resources", () => {
    const gold = makeCorporatePartner({ membership_tier: "Gold" });
    expect(hasTierAccess(gold, "Gold")).toBe(true);
  });

  it("Silver tier has access to Silver-required resources", () => {
    const silver = makeCorporatePartner({ membership_tier: "Silver" });
    expect(hasTierAccess(silver, "Silver")).toBe(true);
  });

  it("Silver tier does NOT have access to Gold-required resources", () => {
    const silver = makeCorporatePartner({ membership_tier: "Silver" });
    expect(hasTierAccess(silver, "Gold")).toBe(false);
  });

  it("returns false for non-Corporate_Partner users", () => {
    expect(hasTierAccess(makeFisherman(), "Silver")).toBe(false);
    expect(hasTierAccess(makeCommunityRep(), "Gold")).toBe(false);
  });

  it("returns false when membership_tier is null", () => {
    const noTier = makeCorporatePartner({ membership_tier: null });
    expect(hasTierAccess(noTier, "Silver")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// getAllowedAreaIds
// ---------------------------------------------------------------------------

describe("getAllowedAreaIds", () => {
  it("Fisherman gets their fishing_area_ids", () => {
    const fisher = makeFisherman({
      fishing_area_ids: ["area-1", "area-2"],
    });
    expect(getAllowedAreaIds(fisher)).toEqual(["area-1", "area-2"]);
  });

  it("Community_Rep gets their responsible_area_ids", () => {
    const rep = makeCommunityRep({
      responsible_area_ids: ["area-3"],
    });
    expect(getAllowedAreaIds(rep)).toEqual(["area-3"]);
  });

  it('Corporate_Partner gets "all"', () => {
    expect(getAllowedAreaIds(makeCorporatePartner())).toBe("all");
  });

  it("Fisherman with no areas gets empty array", () => {
    const fisher = makeFisherman({ fishing_area_ids: [] });
    expect(getAllowedAreaIds(fisher)).toEqual([]);
  });
});
