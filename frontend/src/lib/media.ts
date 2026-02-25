// src/lib/media.ts
/**
 * Helper per costruire URL media a runtime.
 *
 * Riusa lo stesso pattern hostname-detection di api-client.ts:
 * - localhost:3000 → localhost:8000 (prod)
 * - localhost:3001 → localhost:8001 (dev)
 * - 192.168.x.x:3000 → 192.168.x.x:8000 (LAN)
 * - 100.x.x.x:3000 → 100.x.x.x:8000 (Tailscale)
 */

/**
 * Base URL del server API (senza /api).
 * Usato per costruire URL ai file media serviti da StaticFiles.
 */
export function getMediaBaseUrl(): string {
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    const apiPort = port === "3001" ? "8001" : "8000";
    return `http://${hostname}:${apiPort}`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

/**
 * Costruisce URL completo per un media a partire dal path relativo.
 * Es: "/media/exercises/42/abc123.jpg" → "http://localhost:8000/media/exercises/42/abc123.jpg"
 *
 * Ritorna null se il path e' null/undefined.
 */
export function getMediaUrl(relativePath: string | null | undefined): string | null {
  if (!relativePath) return null;
  return `${getMediaBaseUrl()}${relativePath}`;
}
