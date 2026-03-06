// src/components/auth/AuthGuard.tsx
"use client";

/**
 * AuthGuard — protezione client-side per le rotte autenticate.
 *
 * Il middleware Next.js (Edge) e' il primo livello di protezione,
 * ma in Next.js 16 la convenzione `middleware.ts` e' deprecata
 * e potrebbe non intercettare tutte le richieste.
 *
 * Questo componente aggiunge un secondo livello:
 * - Controlla la presenza del cookie JWT
 * - Se assente, redirect immediato a /login
 * - Se presente, renderizza i children normalmente
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const authenticated = isAuthenticated();

  useEffect(() => {
    if (!authenticated) router.replace("/login");
  }, [authenticated, router]);

  // Non renderizzare nulla finche' non abbiamo verificato l'auth
  if (!authenticated) return null;

  return <>{children}</>;
}
