// src/middleware.ts
/**
 * Edge Middleware — Route Protection.
 *
 * Intercetta TUTTE le richieste prima che raggiungano i componenti React.
 * Funziona al livello Edge (Vercel Edge Runtime / Node.js middleware),
 * quindi il redirect avviene PRIMA del rendering — nessun "flash" della pagina.
 *
 * Logica:
 * 1. Se l'utente NON ha il cookie token e accede a una rotta protetta → redirect /login
 * 2. Se l'utente HA il cookie token e accede a /login o /register → redirect /
 * 3. File statici, API routes e _next sono esclusi dal middleware
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Nome del cookie JWT (deve combaciare con api-client.ts e auth.ts)
const TOKEN_COOKIE = "fitmanager_token";

// Rotte pubbliche — accessibili senza autenticazione
const PUBLIC_ROUTES = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(TOKEN_COOKIE)?.value;

  const isPublicRoute = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));

  // Caso 1: utente NON autenticato su rotta protetta → redirect /login
  if (!token && !isPublicRoute) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl, 307);
  }

  // Caso 2: utente autenticato su /login o /register → redirect /
  if (token && isPublicRoute) {
    const homeUrl = new URL("/", request.url);
    return NextResponse.redirect(homeUrl, 307);
  }

  // Caso 3: tutto ok, prosegui
  return NextResponse.next();
}

// Matcher: escludi file statici, API routes, _next
export const config = {
  matcher: [
    /*
     * Matcha tutte le rotte TRANNE:
     * - _next/static (file statici Next.js)
     * - _next/image (ottimizzazione immagini)
     * - favicon.ico, sitemap.xml, robots.txt
     * - File con estensione (immagini, font, ecc.)
     */
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|.*\\..*).*)",
  ],
};
