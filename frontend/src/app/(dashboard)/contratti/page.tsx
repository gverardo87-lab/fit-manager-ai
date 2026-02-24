// src/app/(dashboard)/contratti/page.tsx
"use client";

/**
 * Pagina Contratti — CRM-grade con KPI, tabella enriched, filtri.
 *
 * Architettura:
 * - useContracts() carica contratti enriched + KPI aggregati (React Query)
 * - KPI cards config-driven (pattern identico a CLIENTI_KPI / CASSA_KPI)
 * - Filtro stato via Select (backend-driven) + ricerca testo (client-side in tabella)
 * - ContractSheet per crea/modifica, ContractDetailSheet per master-detail
 */

import { useState } from "react";
import {
  Plus,
  FileText,
  Wallet,
  Receipt,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ContractsTable } from "@/components/contracts/ContractsTable";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { ContractDetailSheet } from "@/components/contracts/ContractDetailSheet";
import { DeleteContractDialog } from "@/components/contracts/DeleteContractDialog";
import { useContracts } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import type { ContractListItem, ContractListResponse } from "@/types/api";

// ── KPI Config (pattern CLIENTI_KPI) ──

interface ContrattiKpiDef {
  key: string;
  label: string;
  icon: LucideIcon;
  format: "number" | "currency";
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

const CONTRATTI_KPI: ContrattiKpiDef[] = [
  {
    key: "attivi",
    label: "Attivi",
    icon: FileText,
    format: "number",
    borderColor: "border-l-violet-500",
    gradient: "from-violet-50/80 to-white dark:from-violet-950/40 dark:to-zinc-900",
    iconBg: "bg-violet-100 dark:bg-violet-900/30",
    iconColor: "text-violet-600 dark:text-violet-400",
    valueColor: "text-violet-700 dark:text-violet-400",
  },
  {
    key: "fatturato",
    label: "Fatturato",
    icon: Receipt,
    format: "currency",
    borderColor: "border-l-blue-500",
    gradient: "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    valueColor: "text-blue-700 dark:text-blue-400",
  },
  {
    key: "incassato",
    label: "Incassato",
    icon: Wallet,
    format: "currency",
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "rate_scadute",
    label: "Rate Scadute",
    icon: AlertTriangle,
    format: "number",
    // Colori condizionali — impostati a runtime
    borderColor: "",
    gradient: "",
    iconBg: "",
    iconColor: "",
    valueColor: "",
  },
];

function getKpiValue(key: string, data: ContractListResponse): number {
  switch (key) {
    case "attivi": return data.kpi_attivi;
    case "fatturato": return data.kpi_fatturato;
    case "incassato": return data.kpi_incassato;
    case "rate_scadute": return data.kpi_rate_scadute;
    default: return 0;
  }
}

// ── Page Component ──

export default function ContrattiPage() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<ContractListItem | null>(null);
  const [statoFilter, setStatoFilter] = useState("all");

  const chiusoParam = statoFilter === "all"
    ? undefined
    : statoFilter === "chiusi";

  const { data: contractsData, isLoading, isError, refetch } = useContracts({
    chiuso: chiusoParam,
  });

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
      {/* ── Header gradient ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 to-violet-200 dark:from-violet-900/40 dark:to-violet-800/30">
            <FileText className="h-5 w-5 text-violet-600 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Contratti</h1>
            {contractsData && (
              <p className="text-sm text-muted-foreground">
                {contractsData.total} contratt{contractsData.total !== 1 ? "i" : "o"} nel portafoglio
              </p>
            )}
          </div>
        </div>
        <Button onClick={handleNewContract}>
          <Plus className="h-4 w-4 sm:mr-2" />
          <span className="hidden sm:inline">Nuovo Contratto</span>
        </Button>
      </div>

      {/* ── KPI Cards ── */}
      {contractsData && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {CONTRATTI_KPI.map((kpi) => {
            const value = getKpiValue(kpi.key, contractsData);
            const isAlert = kpi.key === "rate_scadute";
            const hasAlert = isAlert && value > 0;

            const borderColor = isAlert
              ? (hasAlert ? "border-l-red-500" : "border-l-zinc-300")
              : kpi.borderColor;
            const gradient = isAlert
              ? (hasAlert
                  ? "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900"
                  : "from-zinc-50/80 to-white dark:from-zinc-900/40 dark:to-zinc-900")
              : kpi.gradient;
            const iconBg = isAlert
              ? (hasAlert ? "bg-red-100 dark:bg-red-900/30" : "bg-zinc-100 dark:bg-zinc-800/30")
              : kpi.iconBg;
            const iconColor = isAlert
              ? (hasAlert ? "text-red-600 dark:text-red-400" : "text-zinc-500 dark:text-zinc-400")
              : kpi.iconColor;
            const valueColor = isAlert
              ? (hasAlert ? "text-red-700 dark:text-red-400" : "text-zinc-700 dark:text-zinc-400")
              : kpi.valueColor;

            const Icon = kpi.icon;

            return (
              <div
                key={kpi.key}
                className={`flex items-start gap-3 rounded-xl border border-l-4 ${borderColor} bg-gradient-to-br ${gradient} p-3 shadow-sm transition-shadow hover:shadow-md sm:p-4`}
              >
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
                  <Icon className={`h-4 w-4 ${iconColor}`} />
                </div>
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                    {kpi.label}
                  </p>
                  <p className={`text-xl font-bold tracking-tight sm:text-2xl ${valueColor}`}>
                    {kpi.format === "currency" ? formatCurrency(value) : value}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Filtro stato ── */}
      {contractsData && (
        <div className="flex items-center gap-3">
          <Select value={statoFilter} onValueChange={setStatoFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Tutti gli stati" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti</SelectItem>
              <SelectItem value="attivi">Attivi</SelectItem>
              <SelectItem value="chiusi">Chiusi</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

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
          onNewContract={handleNewContract}
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

// ── Skeleton per KPI + tabella ──

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
