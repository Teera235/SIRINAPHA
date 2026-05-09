/**
 * Registration Request Validation
 *
 * Pure validation logic extracted for testability.
 * Used by the registration API route.
 *
 * Requirements: 7.1, 7.2, 7.3
 */

import type { UserType, MembershipTier } from "@/types";

// ---------------------------------------------------------------------------
// Request body types
// ---------------------------------------------------------------------------

export interface BaseRegistration {
  user_type: UserType;
  display_name: string;
}

export interface FishermanRegistration extends BaseRegistration {
  user_type: "Fisherman";
  line_user_id: string;
  phone_number?: string;
  preferred_channel: "line" | "sms";
  fishing_area_ids: string[];
}

export interface CommunityRepRegistration extends BaseRegistration {
  user_type: "Community_Rep";
  email: string;
  password: string;
  responsible_area_ids: string[];
}

export interface CorporatePartnerRegistration extends BaseRegistration {
  user_type: "Corporate_Partner";
  email: string;
  password: string;
  company_name: string;
  membership_tier: MembershipTier;
}

export type RegistrationRequest =
  | FishermanRegistration
  | CommunityRepRegistration
  | CorporatePartnerRegistration;

export interface ValidationResult {
  valid: boolean;
  error?: string;
  data?: RegistrationRequest;
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

const VALID_USER_TYPES: UserType[] = [
  "Fisherman",
  "Community_Rep",
  "Corporate_Partner",
];

export function validateRegistrationRequest(
  body: unknown
): ValidationResult {
  if (!body || typeof body !== "object") {
    return { valid: false, error: "Request body is required" };
  }

  const b = body as Record<string, unknown>;

  if (!b.user_type || !b.display_name) {
    return { valid: false, error: "user_type and display_name are required" };
  }

  if (typeof b.display_name !== "string" || b.display_name.trim() === "") {
    return { valid: false, error: "display_name must be a non-empty string" };
  }

  if (!VALID_USER_TYPES.includes(b.user_type as UserType)) {
    return {
      valid: false,
      error: `user_type must be one of: ${VALID_USER_TYPES.join(", ")}`,
    };
  }

  switch (b.user_type) {
    case "Fisherman":
      return validateFisherman(b);
    case "Community_Rep":
      return validateCommunityRep(b);
    case "Corporate_Partner":
      return validateCorporatePartner(b);
    default:
      return { valid: false, error: "Unknown user_type" };
  }
}

function validateFisherman(b: Record<string, unknown>): ValidationResult {
  if (!b.line_user_id || typeof b.line_user_id !== "string") {
    return { valid: false, error: "line_user_id is required for Fisherman" };
  }
  if (
    b.preferred_channel !== undefined &&
    b.preferred_channel !== "line" &&
    b.preferred_channel !== "sms"
  ) {
    return {
      valid: false,
      error: "preferred_channel must be 'line' or 'sms'",
    };
  }
  if (
    !b.fishing_area_ids ||
    !Array.isArray(b.fishing_area_ids) ||
    b.fishing_area_ids.length === 0
  ) {
    return {
      valid: false,
      error: "fishing_area_ids (non-empty array) is required for Fisherman",
    };
  }
  return { valid: true, data: b as unknown as FishermanRegistration };
}

function validateCommunityRep(b: Record<string, unknown>): ValidationResult {
  if (!b.email || typeof b.email !== "string") {
    return { valid: false, error: "email is required for Community_Rep" };
  }
  if (!b.password || typeof b.password !== "string") {
    return { valid: false, error: "password is required for Community_Rep" };
  }
  if (
    !b.responsible_area_ids ||
    !Array.isArray(b.responsible_area_ids) ||
    b.responsible_area_ids.length === 0
  ) {
    return {
      valid: false,
      error:
        "responsible_area_ids (non-empty array) is required for Community_Rep",
    };
  }
  return { valid: true, data: b as unknown as CommunityRepRegistration };
}

function validateCorporatePartner(
  b: Record<string, unknown>
): ValidationResult {
  if (!b.email || typeof b.email !== "string") {
    return {
      valid: false,
      error: "email is required for Corporate_Partner",
    };
  }
  if (!b.password || typeof b.password !== "string") {
    return {
      valid: false,
      error: "password is required for Corporate_Partner",
    };
  }
  if (!b.company_name || typeof b.company_name !== "string") {
    return {
      valid: false,
      error: "company_name is required for Corporate_Partner",
    };
  }
  if (b.membership_tier !== "Silver" && b.membership_tier !== "Gold") {
    return {
      valid: false,
      error: "membership_tier must be 'Silver' or 'Gold'",
    };
  }
  return {
    valid: true,
    data: b as unknown as CorporatePartnerRegistration,
  };
}
