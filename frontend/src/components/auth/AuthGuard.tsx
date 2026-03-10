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
 *
 * NOTA: useState(false) + useEffect e' il pattern corretto qui.
 * isAuthenticated() legge document.cookie (browser-only API).
 * Chiamarla durante SSR causa hydration mismatch perche' il server
 * non ha cookie → render null, ma il client ha cookie → render children.
 * Con useState(false) entrambi partono da null → match → effect lato
 * client verifica e setta checked=true.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      setChecked(true);
    } else {
      router.replace("/login");
    }
  }, [router]);

  if (!checked) return null;

  return <>{children}</>;
}
