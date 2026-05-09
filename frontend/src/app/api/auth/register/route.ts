/**
 * User Registration API Route
 *
 * POST /api/auth/register
 *
 * Handles registration for all 3 user types:
 * - Fisherman: registers via LINE (line_user_id required), stores fishing_area_ids
 * - Community_Rep: registers via web (email required), stores responsible_area_ids
 * - Corporate_Partner: registers via web (email required), stores company_name + membership_tier
 *
 * Requirements: 7.1, 7.2, 7.3
 */

import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase";
import { validateRegistrationRequest } from "./validation";

// ---------------------------------------------------------------------------
// POST handler
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validation = validateRegistrationRequest(body);

    if (!validation.valid || !validation.data) {
      return NextResponse.json(
        { error: validation.error },
        { status: 400 }
      );
    }

    const data = validation.data;
    const supabase = createServerClient();

    // ----- Step 1: Create Supabase Auth user -----
    // Fisherman registers via LINE (no email/password — we create a user
    // keyed by their LINE user ID). Community_Rep and Corporate_Partner
    // register via email/password.

    let authUserId: string;

    if (data.user_type === "Fisherman") {
      // For LINE-based registration we create an auth user with a
      // deterministic email derived from the LINE user ID so Supabase Auth
      // can track the identity. The password is auto-generated since
      // fishermen authenticate via LINE OAuth, not email/password.
      const lineEmail = `${data.line_user_id}@line.baan-pla.local`;
      const autoPassword = crypto.randomUUID();

      const { data: authData, error: authError } =
        await supabase.auth.admin.createUser({
          email: lineEmail,
          password: autoPassword,
          email_confirm: true,
          user_metadata: {
            user_type: "Fisherman",
            line_user_id: data.line_user_id,
          },
        });

      if (authError) {
        return NextResponse.json(
          { error: `Auth error: ${authError.message}` },
          { status: 400 }
        );
      }
      authUserId = authData.user.id;
    } else {
      // Community_Rep or Corporate_Partner — email/password registration
      const { data: authData, error: authError } =
        await supabase.auth.admin.createUser({
          email: data.email,
          password: data.password,
          email_confirm: true,
          user_metadata: { user_type: data.user_type },
        });

      if (authError) {
        return NextResponse.json(
          { error: `Auth error: ${authError.message}` },
          { status: 400 }
        );
      }
      authUserId = authData.user.id;
    }

    // ----- Step 2: Insert user profile row -----
    const profileRow: Record<string, unknown> = {
      id: authUserId,
      user_type: data.user_type,
      display_name: data.display_name,
      preferred_channel:
        data.user_type === "Fisherman" ? data.preferred_channel ?? "line" : "line",
    };

    if (data.user_type === "Fisherman") {
      profileRow.line_user_id = data.line_user_id;
      if (data.phone_number) {
        profileRow.phone_number = data.phone_number;
      }
    }

    if (data.user_type === "Corporate_Partner") {
      profileRow.company_name = data.company_name;
      profileRow.membership_tier = data.membership_tier;
    }

    const { error: profileError } = await supabase
      .from("users")
      .insert(profileRow);

    if (profileError) {
      // Rollback: delete the auth user we just created
      await supabase.auth.admin.deleteUser(authUserId);
      return NextResponse.json(
        { error: `Profile error: ${profileError.message}` },
        { status: 400 }
      );
    }

    // ----- Step 3: Insert area associations -----
    let areaIds: string[] = [];

    if (data.user_type === "Fisherman") {
      areaIds = data.fishing_area_ids;
    } else if (data.user_type === "Community_Rep") {
      areaIds = data.responsible_area_ids;
    }

    if (areaIds.length > 0) {
      const areaRows = areaIds.map((areaId) => ({
        user_id: authUserId,
        area_id: areaId,
      }));

      const { error: areaError } = await supabase
        .from("user_fishing_areas")
        .insert(areaRows);

      if (areaError) {
        // Rollback profile and auth user
        await supabase.from("users").delete().eq("id", authUserId);
        await supabase.auth.admin.deleteUser(authUserId);
        return NextResponse.json(
          { error: `Area association error: ${areaError.message}` },
          { status: 400 }
        );
      }
    }

    return NextResponse.json(
      {
        message: "ลงทะเบียนสำเร็จ (Registration successful)",
        user_id: authUserId,
        user_type: data.user_type,
      },
      { status: 201 }
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json(
      { error: `Registration failed: ${message}` },
      { status: 500 }
    );
  }
}
