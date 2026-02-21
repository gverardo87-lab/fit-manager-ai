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

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    } else {
      setChecked(true);
    }
  }, [router]);

  // Non renderizzare nulla finche' non abbiamo verificato l'auth
  if (!checked) return null;

  return <>{children}</>;
}
