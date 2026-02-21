// src/app/(dashboard)/clienti/page.tsx
"use client";

/**
 * Pagina Clienti — lista con tabella, creazione e modifica via Sheet.
 *
 * Architettura:
 * - useClients() carica tutti i clienti (React Query)
 * - ClientsTable gestisce il filtro client-side (istantaneo)
 * - ClientSheet per il form a comparsa (crea/modifica)
 * - DeleteClientDialog per conferma eliminazione
 * - Toast (sonner) per feedback su ogni operazione
 */

import { useState } from "react";
import { Plus, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ClientsTable } from "@/components/clients/ClientsTable";
import { ClientSheet } from "@/components/clients/ClientSheet";
import { DeleteClientDialog } from "@/components/clients/DeleteClientDialog";
import { useClients } from "@/hooks/useClients";
import type { Client } from "@/types/api";

export default function ClientiPage() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);

  const { data, isLoading, isError, refetch } = useClients();

  // ── Handlers ──

  const handleNewClient = () => {
    setSelectedClient(null);
    setSheetOpen(true);
  };

  const handleEdit = (client: Client) => {
    setSelectedClient(client);
    setSheetOpen(true);
  };

  const handleDelete = (client: Client) => {
    setSelectedClient(client);
    setDeleteOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Clienti</h1>
            {data && (
              <p className="text-sm text-muted-foreground">
                {data.total} client{data.total !== 1 ? "i" : "e"} totali
              </p>
            )}
          </div>
        </div>
        <Button onClick={handleNewClient}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Cliente
        </Button>
      </div>

      {/* ── Contenuto ── */}
      {isLoading && <TableSkeleton />}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">
            Errore nel caricamento dei clienti.
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => refetch()}
          >
            Riprova
          </Button>
        </div>
      )}

      {data && (
        <ClientsTable
          clients={data.items}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      {/* ── Sheet crea/modifica ── */}
      <ClientSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        client={selectedClient}
      />

      {/* ── Dialog elimina ── */}
      <DeleteClientDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        client={selectedClient}
      />
    </div>
  );
}

// ── Skeleton per la tabella ──

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
