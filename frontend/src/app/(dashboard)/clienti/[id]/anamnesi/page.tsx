// src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx
"use client";

/**
 * Pagina dedicata Anamnesi.
 *
 * Promossa da tab a pagina full-width.
 * Tre stati: nessuna anamnesi → empty CTA, legacy → ricompila CTA, strutturata → summary + edit.
 * Il wizard vive come Dialog controllato da useState locale.
 *
 * Back button: torna al profilo cliente.
 */

import { use, useState } from "react";
import Link from "next/link";
import { ArrowLeft, HeartPulse, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AnamnesiSummary } from "@/components/clients/anamnesi/AnamnesiSummary";
import { AnamnesiWizard } from "@/components/clients/anamnesi/AnamnesiWizard";
import { isStructuredAnamnesi } from "@/components/clients/anamnesi/anamnesi-helpers";
import { useClient } from "@/hooks/useClients";
import type { AnamnesiData } from "@/types/api";

export default function AnamnesiPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);

  const { data: client, isLoading } = useClient(clientId);
  const [wizardOpen, setWizardOpen] = useState(false);

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

  const anamnesi = client.anamnesi ?? null;

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
          <h1 className="text-2xl font-bold tracking-tight">Anamnesi</h1>
          <p className="text-sm text-muted-foreground">
            {client.nome} {client.cognome}
          </p>
        </div>
        <HeartPulse className="h-8 w-8 text-rose-500/50" />
      </div>

      {/* Content: 3-state rendering */}
      <AnamnesiContent
        anamnesi={anamnesi}
        onOpenWizard={() => setWizardOpen(true)}
      />

      {/* Wizard Dialog */}
      <AnamnesiWizard
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        clientId={clientId}
        existing={anamnesi}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// ANAMNESI CONTENT (3-state)
// ════════════════════════════════════════════════════════════

function AnamnesiContent({
  anamnesi,
  onOpenWizard,
}: {
  anamnesi: AnamnesiData | Record<string, unknown> | null;
  onOpenWizard: () => void;
}) {
  // Nessuna anamnesi
  if (!anamnesi) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <HeartPulse className="h-10 w-10 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">
          Nessuna anamnesi compilata per questo cliente
        </p>
        <Button variant="outline" size="sm" onClick={onOpenWizard}>
          <Plus className="mr-2 h-4 w-4" />
          Compila Anamnesi
        </Button>
      </div>
    );
  }

  // Anamnesi formato vecchio (legacy dict)
  if (!isStructuredAnamnesi(anamnesi as Record<string, unknown>)) {
    const legacyNote = (anamnesi as Record<string, unknown>).note;
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <HeartPulse className="h-10 w-10 text-amber-500/50" />
        <p className="text-sm text-muted-foreground">
          Anamnesi in formato precedente — ricompila per il nuovo questionario
        </p>
        {typeof legacyNote === "string" && legacyNote && (
          <p className="text-xs text-muted-foreground italic max-w-md text-center">
            Nota precedente: {legacyNote}
          </p>
        )}
        <Button variant="outline" size="sm" onClick={onOpenWizard}>
          <Plus className="mr-2 h-4 w-4" />
          Ricompila Anamnesi
        </Button>
      </div>
    );
  }

  // Anamnesi strutturata
  return <AnamnesiSummary data={anamnesi as AnamnesiData} onEdit={onOpenWizard} />;
}
