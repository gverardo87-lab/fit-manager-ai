// src/app/(dashboard)/clienti/page.tsx
"use client";

/**
 * Pagina Clienti — CRM-grade con KPI, tabella enriched, filtri.
 *
 * Architettura:
 * - useClients() carica clienti enriched + KPI aggregati (React Query)
 * - KPI cards config-driven (pattern identico a CASSA_KPI)
 * - Filtro stato via Select (backend-driven) + ricerca testo (client-side)
 * - ClientSheet per il form a comparsa (crea/modifica)
 * - DeleteClientDialog per conferma eliminazione
 */

import { useState } from "react";
import {
  Plus,
  Users,
  UserX,
  CreditCard,
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
import { ClientsTable } from "@/components/clients/ClientsTable";
import { ClientSheet } from "@/components/clients/ClientSheet";
import { DeleteClientDialog } from "@/components/clients/DeleteClientDialog";
import { useClients } from "@/hooks/useClients";
import type { ClientEnriched } from "@/types/api";

// ── KPI Config (pattern CASSA_KPI) ──

interface ClientiKpiDef {
  key: string;
  label: string;
  icon: LucideIcon;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

const CLIENTI_KPI: ClientiKpiDef[] = [
  {
    key: "attivi",
    label: "Attivi",
    icon: Users,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "inattivi",
    label: "Inattivi",
    icon: UserX,
    borderColor: "border-l-zinc-400",
    gradient: "from-zinc-50/80 to-white dark:from-zinc-900/40 dark:to-zinc-900",
    iconBg: "bg-zinc-100 dark:bg-zinc-800/30",
    iconColor: "text-zinc-500 dark:text-zinc-400",
    valueColor: "text-zinc-700 dark:text-zinc-400",
  },
  {
    key: "con_crediti",
    label: "Con Crediti",
    icon: CreditCard,
    borderColor: "border-l-blue-500",
    gradient: "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    valueColor: "text-blue-700 dark:text-blue-400",
  },
  {
    key: "rate_scadute",
    label: "Rate Scadute",
    icon: AlertTriangle,
    // Colori condizionali — impostati a runtime
    borderColor: "",
    gradient: "",
    iconBg: "",
    iconColor: "",
    valueColor: "",
  },
];

function getKpiValue(key: string, kpi: { kpi_attivi: number; kpi_inattivi: number; kpi_con_crediti: number; kpi_rate_scadute: number }): number {
  switch (key) {
    case "attivi": return kpi.kpi_attivi;
    case "inattivi": return kpi.kpi_inattivi;
    case "con_crediti": return kpi.kpi_con_crediti;
    case "rate_scadute": return kpi.kpi_rate_scadute;
    default: return 0;
  }
}

// ── Page Component ──

export default function ClientiPage() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<ClientEnriched | null>(null);
  const [statoFilter, setStatoFilter] = useState("all");

  const { data, isLoading, isError, refetch } = useClients({
    stato: statoFilter === "all" ? undefined : statoFilter,
  });

  // ── Handlers ──

  const handleNewClient = () => {
    setSelectedClient(null);
    setSheetOpen(true);
  };

  const handleEdit = (client: ClientEnriched) => {
    setSelectedClient(client);
    setSheetOpen(true);
  };

  const handleDelete = (client: ClientEnriched) => {
    setSelectedClient(client);
    setDeleteOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* ── Header gradient ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/40 dark:to-blue-800/30">
            <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Clienti</h1>
            {data && (
              <p className="text-sm text-muted-foreground">
                {data.total} client{data.total !== 1 ? "i" : "e"} nel tuo portafoglio
              </p>
            )}
          </div>
        </div>
        <Button onClick={handleNewClient}>
          <Plus className="h-4 w-4 sm:mr-2" />
          <span className="hidden sm:inline">Nuovo Cliente</span>
        </Button>
      </div>

      {/* ── KPI Cards ── */}
      {data && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {CLIENTI_KPI.map((kpi) => {
            const value = getKpiValue(kpi.key, data);
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
                    {value}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Filtro stato ── */}
      {data && (
        <div className="flex items-center gap-3">
          <Select value={statoFilter} onValueChange={setStatoFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Tutti gli stati" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti</SelectItem>
              <SelectItem value="Attivo">Attivi</SelectItem>
              <SelectItem value="Inattivo">Inattivi</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

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
          onNewClient={handleNewClient}
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
