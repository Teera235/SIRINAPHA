/**
 * Supabase Client Configuration
 *
 * Provides browser-side and server-side Supabase clients for the
 * Baan-Pla Link platform. Uses @supabase/supabase-js v2.
 *
 * Requirements: 7.1, 7.2, 7.3
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

/**
 * Browser / public client — uses the anon key and respects RLS policies.
 * Safe to use in client components and API routes that act on behalf of
 * the authenticated user.
 */
export function createBrowserClient(): SupabaseClient {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables"
    );
  }
  return createClient(supabaseUrl, supabaseAnonKey);
}

/**
 * Server / admin client — uses the service role key and bypasses RLS.
 * Only use in trusted server-side contexts (API routes, server actions).
 */
export function createServerClient(): SupabaseClient {
  if (!supabaseUrl || !supabaseServiceRoleKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables"
    );
  }
  return createClient(supabaseUrl, supabaseServiceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

/**
 * Singleton browser client for convenience in client-side code.
 * Lazily initialised to avoid errors when env vars are missing at import time.
 */
let _browserClient: SupabaseClient | null = null;

export function getSupabaseBrowserClient(): SupabaseClient {
  if (!_browserClient) {
    _browserClient = createBrowserClient();
  }
  return _browserClient;
}
