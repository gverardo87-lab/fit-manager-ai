// src/lib/providers.tsx
/**
 * React Query Provider — wrapper "use client" per Next.js App Router.
 *
 * Next.js App Router rende i componenti Server Components di default.
 * React Query ha bisogno di un contesto React (client-side), quindi
 * lo isoliamo in questo wrapper "use client" che viene usato nel layout.
 *
 * DevTools: visibili solo in development (process.env.NODE_ENV !== "production").
 */

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, type ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  // useState garantisce che ogni utente abbia la sua istanza QueryClient
  // (importante per SSR/App Router per evitare data sharing tra utenti)
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Non refetchare automaticamente quando la finestra torna in focus
            // (evita chiamate inutili durante lo sviluppo)
            refetchOnWindowFocus: false,
            // Retry 1 volta su errore (default React Query e' 3)
            retry: 1,
            // Dati considerati "freschi" per 30 secondi
            staleTime: 30_000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
