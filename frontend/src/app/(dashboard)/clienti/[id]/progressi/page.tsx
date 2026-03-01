// src/app/(dashboard)/clienti/[id]/progressi/page.tsx
"use client";

/**
 * Pagina dedicata Progressi Fisici.
 *
 * Promossa da tab a pagina full-width per dare spazio a:
 * misurazioni, obiettivi, analisi clinica, body map, chart, comparazione.
 *
 * Back button: torna al profilo cliente.
 */

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, TrendingUp } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { ProgressiTab } from "@/components/clients/ProgressiTab";
import { useClient } from "@/hooks/useClients";

export default function ProgressiPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);

  const { data: client, isLoading } = useClient(clientId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <p className="text-lg font-medium">Cliente non trovato</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/clienti/${clientId}`}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-white shadow-sm transition-colors hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">
            Progressi Fisici
          </h1>
          <p className="text-sm text-muted-foreground">
            {client.nome} {client.cognome}
          </p>
        </div>
        <TrendingUp className="h-8 w-8 text-teal-500/50" />
      </div>

      {/* Content */}
      <ProgressiTab
        clientId={clientId}
        sesso={client.sesso}
        dataNascita={client.data_nascita}
      />
    </div>
  );
}
