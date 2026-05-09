/**
 * Auth Helper Functions
 *
 * Provides utilities for user authentication, profile retrieval,
 * and role-based access checks for the Baan-Pla Link platform.
 *
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
 */

import { SupabaseClient } from "@supabase/supabase-js";
import type { UserType, MembershipTier } from "@/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UserProfileRow {
  id: string;
  user_type: UserType;
  display_name: string;
  preferred_channel: "line" | "sms";
  line_user_id: string | null;
  phone_number: string | null;
  company_name: string | null;
  membership_tier: MembershipTier | null;
  created_at: string;
}

export interface UserWithAreas extends UserProfileRow {
  fishing_area_ids: string[];
  responsible_area_ids: string[];
}

// ---------------------------------------------------------------------------
// Current user helpers
// ---------------------------------------------------------------------------

/**
 * Get the currently authenticated Supabase Auth user (JWT-level).
 * Returns null when no valid session exists.
 */
export async function getCurrentUser(client: SupabaseClient) {
  const {
    data: { user },
    error,
  } = await client.auth.getUser();
  if (error || !user) return null;
  return user;
}

/**
 * Fetch the full user profile row from the `users` table, including
 * associated fishing_area_ids and responsible_area_ids from junction tables.
 */
export async function getUserProfile(
  client: SupabaseClient,
  userId: string
): Promise<UserWithAreas | null> {
  // Fetch base profile
  const { data: profile, error } = await client
    .from("users")
    .select("*")
    .eq("id", userId)
    .single();

  if (error || !profile) return null;

  // Fetch fishing area associations
  const { data: fishingAreas } = await client
    .from("user_fishing_areas")
    .select("area_id")
    .eq("user_id", userId);

  // Fetch responsible area associations (Community_Rep uses the same junction
  // table pattern — we store responsible areas in user_fishing_areas for
  // Community_Rep as well, or we can add a separate table. For simplicity
  // we use a dedicated query on user_fishing_areas since the schema uses
  // the same junction table.)
  const fishingAreaIds = (fishingAreas ?? []).map(
    (r: { area_id: string }) => r.area_id
  );

  // For Community_Rep, responsible_area_ids are stored in user_fishing_areas
  // (same junction table, different semantic meaning based on user_type)
  const responsibleAreaIds =
    profile.user_type === "Community_Rep" ? fishingAreaIds : [];
  const actualFishingAreaIds =
    profile.user_type === "Fisherman" ? fishingAreaIds : [];

  return {
    ...profile,
    fishing_area_ids: actualFishingAreaIds,
    responsible_area_ids: responsibleAreaIds,
  } as UserWithAreas;
}

// ---------------------------------------------------------------------------
// Role checks
// ---------------------------------------------------------------------------

/**
 * Check whether a user has a specific user type.
 */
export function hasRole(
  profile: UserProfileRow | UserWithAreas,
  role: UserType
): boolean {
  return profile.user_type === role;
}

/**
 * Check whether a Corporate_Partner has the required membership tier.
 * Gold tier includes access to everything Silver has.
 */
export function hasTierAccess(
  profile: UserProfileRow | UserWithAreas,
  requiredTier: MembershipTier
): boolean {
  if (profile.user_type !== "Corporate_Partner") return false;
  if (!profile.membership_tier) return false;
  if (requiredTier === "Silver") {
    return profile.membership_tier === "Silver" || profile.membership_tier === "Gold";
  }
  // Gold required — only Gold qualifies
  return profile.membership_tier === "Gold";
}

/**
 * Return the set of area IDs a user is allowed to access.
 * - Fisherman → fishing_area_ids
 * - Community_Rep → responsible_area_ids
 * - Corporate_Partner → all areas (filtered by tier at the data level)
 */
export function getAllowedAreaIds(
  profile: UserWithAreas
): string[] | "all" {
  switch (profile.user_type) {
    case "Fisherman":
      return profile.fishing_area_ids;
    case "Community_Rep":
      return profile.responsible_area_ids;
    case "Corporate_Partner":
      return "all";
    default:
      return [];
  }
}
