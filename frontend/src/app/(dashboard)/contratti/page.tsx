// src/app/(dashboard)/contratti/page.tsx
"use client";

/**
 * Pagina Contratti — CRM-grade con KPI, FilterBar chip, tabella enriched.
 *
 * Architettura:
 * - useContracts() carica tutti i contratti enriched + KPI aggregati (React Query)
 * - KPI cards config-driven (pattern identico a CLIENTI_KPI / CASSA_KPI)
 * - FilterBar chip interattivi (pattern Agenda/Clienti): stato + situazione finanziaria
 * - Ricerca testo client-side nella tabella
 * - ContractSheet per crea/modifica, ContractDetailSheet per master-detail
 */

import { useState, useCallback, useMemo } from "react";
import { differenceInDays, parseISO, startOfToday } from "date-fns";
import {
  Plus,
  FileText,
  Wallet,
  Receipt,
  AlertTriangle,
  Eye,
  EyeOff,
  CheckCircle2,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ContractsTable } from "@/components/contracts/ContractsTable";
import { ContractSheet } from "@/components/contracts/ContractSheet";
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
    case "attivi": return data.kpi_attivi ?? 0;
    case "fatturato": return data.kpi_fatturato ?? 0;
    case "incassato": return data.kpi_incassato ?? 0;
    case "rate_scadute": return data.kpi_rate_scadute ?? 0;
    default: return 0;
  }
}

// ── Filter chip definitions (pattern Clienti/Agenda) ──

interface FilterChipDef {
  key: string;
  label: string;
  color: string;
  icon: LucideIcon;
}

const STATO_CHIPS: FilterChipDef[] = [
  { key: "attivi", label: "Attivi", color: "#8b5cf6", icon: FileText },
  { key: "chiusi", label: "Chiusi", color: "#a1a1aa", icon: FileText },
];

const SITUAZIONE_CHIPS: FilterChipDef[] = [
  { key: "insolventi", label: "Insolventi", color: "#dc2626", icon: ShieldAlert },
  { key: "rate_scadute", label: "Con Rate Scadute", color: "#ef4444", icon: AlertTriangle },
  { key: "saldati", label: "Saldati", color: "#10b981", icon: CheckCircle2 },
];

/** Classifica un contratto nella situazione finanziaria. */
function matchesSituazione(c: ContractListItem, key: string): boolean {
  const today = startOfToday();
  const isExpired = c.data_scadenza && differenceInDays(parseISO(c.data_scadenza), today) < 0;
  const isSaldato = c.prezzo_totale != null && c.totale_versato >= c.prezzo_totale - 0.01;

  switch (key) {
    case "insolventi":
      return c.ha_rate_scadute && !!isExpired && !c.chiuso;
    case "rate_scadute":
      // Rate in ritardo ma NON insolvente (contratto non ancora scaduto)
      return c.ha_rate_scadute && !isExpired && !c.chiuso;
    case "saldati":
      return isSaldato;
    default:
      return false;
  }
}

// ── Page Component ──

export default function ContrattiPage() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<ContractListItem | null>(null);

  // Filter state: Set<string> per ogni asse (pattern Clienti/Agenda)
  const [activeStati, setActiveStati] = useState<Set<string>>(
    () => new Set(STATO_CHIPS.map((c) => c.key))
  );
  const [activeSituazioni, setActiveSituazioni] = useState<Set<string>>(
    () => new Set(SITUAZIONE_CHIPS.map((c) => c.key))
  );

  const { data: contractsData, isLoading, isError, refetch } = useContracts();

  // ── Filter handlers (immutable Set toggle, pattern Clienti/Agenda) ──

  const handleToggleStato = useCallback((key: string) => {
    setActiveStati((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const handleToggleSituazione = useCallback((key: string) => {
    setActiveSituazioni((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  // ── Client-side filtering ──

  const filteredContracts = useMemo(() => {
    if (!contractsData) return [];

    return contractsData.items.filter((c) => {
      // Asse 1: stato (attivi = !chiuso, chiusi = chiuso)
      const statoKey = c.chiuso ? "chiusi" : "attivi";
      if (!activeStati.has(statoKey)) return false;

      // Asse 2: situazione (OR logic — passa se almeno un chip attivo matcha)
      const hasSituazioneFilters = activeSituazioni.size < SITUAZIONE_CHIPS.length;
      if (hasSituazioneFilters) {
        if (activeSituazioni.size === 0) return false;
        const matchesAny = SITUAZIONE_CHIPS.some(
          (chip) => activeSituazioni.has(chip.key) && matchesSituazione(c, chip.key)
        );
        if (!matchesAny) return false;
      }

      return true;
    });
  }, [contractsData, activeStati, activeSituazioni]);

  const isFiltered = activeStati.size < STATO_CHIPS.length || activeSituazioni.size < SITUAZIONE_CHIPS.length;

  // ── Handlers ──

  const handleNewContract = () => {
    setSelectedContract(null);
    setSheetOpen(true);
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
            <h1 className="text-2xl font-bold tracking-tight">
              Contratti
              {isFiltered && (
                <span className="text-muted-foreground/60 text-base font-normal"> (filtro attivo)</span>
              )}
            </h1>
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

      {/* ── FilterBar chip (pattern Clienti/Agenda) ── */}
      {contractsData && (
        <FilterBar
          activeStati={activeStati}
          onToggleStato={handleToggleStato}
          activeSituazioni={activeSituazioni}
          onToggleSituazione={handleToggleSituazione}
        />
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
          contracts={filteredContracts}
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

// ════════════════════════════════════════════════════════════
// FilterBar — chip interattivi (pattern Clienti/Agenda)
// ════════════════════════════════════════════════════════════

function FilterBar({
  activeStati,
  onToggleStato,
  activeSituazioni,
  onToggleSituazione,
}: {
  activeStati: Set<string>;
  onToggleStato: (key: string) => void;
  activeSituazioni: Set<string>;
  onToggleSituazione: (key: string) => void;
}) {
  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-3 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="flex flex-col gap-2">
        {/* Riga 1: Stato */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="w-14 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground sm:w-16">
            Stato:
          </span>
          {STATO_CHIPS.map((chip) => {
            const active = activeStati.has(chip.key);
            const Icon = active ? Eye : EyeOff;
            return (
              <button
                key={chip.key}
                type="button"
                onClick={() => onToggleStato(chip.key)}
                className={`flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-all duration-200 sm:gap-1.5 sm:px-3 sm:text-xs ${
                  active
                    ? "border-transparent shadow-sm"
                    : "border-dashed border-muted-foreground/30 opacity-40"
                }`}
                style={
                  active
                    ? { backgroundColor: chip.color + "20", color: chip.color }
                    : undefined
                }
              >
                <div
                  className="h-2.5 w-2.5 rounded-full transition-opacity"
                  style={{ backgroundColor: chip.color, opacity: active ? 1 : 0.3 }}
                />
                {chip.label}
                <Icon className="h-3 w-3" />
              </button>
            );
          })}
        </div>

        {/* Riga 2: Situazione */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="w-14 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground sm:w-16">
            Filtro:
          </span>
          {SITUAZIONE_CHIPS.map((chip) => {
            const active = activeSituazioni.has(chip.key);
            const Icon = active ? Eye : EyeOff;
            return (
              <button
                key={chip.key}
                type="button"
                onClick={() => onToggleSituazione(chip.key)}
                className={`flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-all duration-200 sm:gap-1.5 sm:px-3 sm:text-xs ${
                  active
                    ? "border-transparent shadow-sm"
                    : "border-dashed border-muted-foreground/30 opacity-40"
                }`}
                style={
                  active
                    ? { backgroundColor: chip.color + "20", color: chip.color }
                    : undefined
                }
              >
                <div
                  className="h-2.5 w-2.5 rounded-full transition-opacity"
                  style={{ backgroundColor: chip.color, opacity: active ? 1 : 0.3 }}
                />
                {chip.label}
                <Icon className="h-3 w-3" />
              </button>
            );
          })}
        </div>
      </div>
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
