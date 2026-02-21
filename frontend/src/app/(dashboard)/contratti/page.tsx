// src/app/(dashboard)/contratti/page.tsx
"use client";

/**
 * Pagina Contratti — lista con tabella, creazione e modifica via Sheet.
 *
 * Complessita' relazionale:
 * - Carica sia contratti che clienti (per risolvere id_cliente → nome)
 * - Costruisce una Map<id, nome> per la tabella
 * - Il form usa useClients() internamente per il Select
 */

import { useState, useMemo } from "react";
import { Plus, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ContractsTable } from "@/components/contracts/ContractsTable";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { DeleteContractDialog } from "@/components/contracts/DeleteContractDialog";
import { useContracts } from "@/hooks/useContracts";
import { useClients } from "@/hooks/useClients";
import type { Contract } from "@/types/api";

export default function ContrattiPage() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<Contract | null>(
    null
  );

  const { data: contractsData, isLoading, isError, refetch } = useContracts();
  const { data: clientsData } = useClients({ pageSize: 200 });

  // Mappa id → "Cognome Nome" per la tabella
  const clientMap = useMemo(() => {
    const map = new Map<number, string>();
    if (clientsData?.items) {
      for (const c of clientsData.items) {
        map.set(c.id, `${c.cognome} ${c.nome}`);
      }
    }
    return map;
  }, [clientsData]);

  // ── Handlers ──

  const handleNewContract = () => {
    setSelectedContract(null);
    setSheetOpen(true);
  };

  const handleEdit = (contract: Contract) => {
    setSelectedContract(contract);
    setSheetOpen(true);
  };

  const handleDelete = (contract: Contract) => {
    setSelectedContract(contract);
    setDeleteOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-100 dark:bg-violet-900/30">
            <FileText className="h-5 w-5 text-violet-600 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Contratti</h1>
            {contractsData && (
              <p className="text-sm text-muted-foreground">
                {contractsData.total} contratt
                {contractsData.total !== 1 ? "i" : "o"} totali
              </p>
            )}
          </div>
        </div>
        <Button onClick={handleNewContract}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Contratto
        </Button>
      </div>

      {/* ── Contenuto ── */}
      {isLoading && <TableSkeleton />}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">
            Errore nel caricamento dei contratti.
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

      {contractsData && (
        <ContractsTable
          contracts={contractsData.items}
          clientMap={clientMap}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      {/* ── Sheet crea/modifica ── */}
      <ContractSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        contract={selectedContract}
      />

      {/* ── Dialog elimina ── */}
      <DeleteContractDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        contract={selectedContract}
        clientName={
          selectedContract
            ? clientMap.get(selectedContract.id_cliente)
            : undefined
        }
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
