import type { NextConfig } from "next";

// Kudos attachments (phase 03) are served from Supabase Storage's public
// object URL, not a static asset. Without this, `next/image` throws on the
// first Storage-hosted attachment and takes all of `/kudos` down with it —
// see plans/260907-0822-viet-kudo/phase-03-schema-rls-storage-and-image-host.md.
// Derived from NEXT_PUBLIC_SUPABASE_URL (falls back to the local dev URL) so
// local, CI, and any future hosted project all read from one source of truth.
const supabaseUrl = new URL(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321",
);

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [new URL(`${supabaseUrl.origin}/storage/v1/object/public/**`)],
  },
};

export default nextConfig;
