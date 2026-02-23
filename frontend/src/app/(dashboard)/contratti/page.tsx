// src/app/(dashboard)/contratti/page.tsx
"use client";

/**
 * Pagina Contratti — lista con tabella enriched, creazione e modifica via Sheet.
 *
 * Il backend restituisce ContractListResponse con nome cliente e KPI rate
 * gia' calcolati (batch fetch, zero N+1). Nessuna query clienti separata.
 */

import { useState } from "react";
import { Plus, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ContractsTable } from "@/components/contracts/ContractsTable";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { ContractDetailSheet } from "@/components/contracts/ContractDetailSheet";
import { DeleteContractDialog } from "@/components/contracts/DeleteContractDialog";
import { useContracts } from "@/hooks/useContracts";
import type { ContractListItem } from "@/types/api";

export default function ContrattiPage() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<ContractListItem | null>(
    null
  );

  const { data: contractsData, isLoading, isError, refetch } = useContracts();

  // ── Handlers ──

  const handleNewContract = () => {
    setSelectedContract(null);
    setSheetOpen(true);
  };

  const handleManage = (contract: ContractListItem) => {
    setSelectedContract(contract);
    setDetailOpen(true);
  };

  const handleEdit = (contract: ContractListItem) => {
    setSelectedContract(contract);
    setSheetOpen(true);
  };

  const handleDelete = (contract: ContractListItem) => {
    setSelectedContract(contract);
    setDeleteOpen(true);
  };

  // Nome cliente derivato dal backend (zero clientMap)
  const clientName = selectedContract
    ? `${selectedContract.client_cognome} ${selectedContract.client_nome}`
    : undefined;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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
          <Plus className="h-4 w-4 sm:mr-2" />
          <span className="hidden sm:inline">Nuovo Contratto</span>
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
          onManage={handleManage}
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

      {/* ── Sheet master-detail (pagamenti + dettagli) ── */}
      <ContractDetailSheet
        open={detailOpen}
        onOpenChange={setDetailOpen}
        contractId={selectedContract?.id ?? null}
        clientName={clientName}
      />

      {/* ── Dialog elimina ── */}
      <DeleteContractDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        contract={selectedContract}
        clientName={clientName}
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
