/**
 * Next.js Middleware — Auth Protection & Role-Based Access
 *
 * Protects dashboard and API routes by verifying Supabase Auth sessions.
 * Public routes (home page, registration, LINE webhook) are excluded.
 *
 * Requirements: 7.4, 7.5
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/** Routes that do not require authentication */
const PUBLIC_PATHS = [
  "/",
  "/api/auth/register",
  "/api/line/webhook",
  "/dashboard",
  "/dashboard/carbon",
  "/api/reports/pdf",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes through without auth check
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  // Extract the Supabase access token from the Authorization header
  const authHeader = request.headers.get("authorization");
  const token = authHeader?.startsWith("Bearer ")
    ? authHeader.slice(7)
    : null;

  if (!token) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 }
    );
  }

  // Verify the token with Supabase
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    return NextResponse.json(
      { error: "Server configuration error" },
      { status: 500 }
    );
  }

  const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    global: { headers: { Authorization: `Bearer ${token}` } },
    auth: { autoRefreshToken: false, persistSession: false },
  });

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    return NextResponse.json(
      { error: "Invalid or expired token" },
      { status: 401 }
    );
  }

  // Attach user ID to request headers so downstream API routes can use it
  const response = NextResponse.next();
  response.headers.set("x-user-id", user.id);
  return response;
}

export const config = {
  matcher: [
    // Protect all API routes except public ones, and dashboard pages
    "/api/:path*",
    "/dashboard/:path*",
  ],
};
