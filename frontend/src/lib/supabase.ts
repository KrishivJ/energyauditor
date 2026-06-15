// Supabase browser client — used ONLY for auth (signup / login / token
// refresh). The app never queries Postgres or Storage directly from the
// browser; all data goes through the FastAPI backend (see lib/api.ts), which
// verifies the access token and scopes every query to the signed-in user.
//
// Only the public anon key is exposed here — never the service-role key.

import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  // Fail loud in dev rather than producing confusing 401s later.
  throw new Error(
    "Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY — copy frontend/.env.example to .env.local and fill them in.",
  );
}

export const supabase = createClient(url, anonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true, // handles the email-confirm / reset redirect
  },
});
