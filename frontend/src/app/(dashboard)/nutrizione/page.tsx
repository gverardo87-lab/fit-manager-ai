// src/app/(dashboard)/nutrizione/page.tsx
"use client";

/**
 * Pagina Nutrizione — lista piani alimentari cross-client.
 *
 * Design premium allineato a Cassa/Schede:
 * - Header con icon gradient container
 * - KPI config-driven con gradient cards + hover elevation
 * - Filtri chip + Select
 * - Tabella con badge semantici + azioni inline
 * - Empty state celebrativo
 * - Page reveal staggered
 */

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  UtensilsCrossed, Plus, CheckCircle2, Trash2,
  Apple, Users, Flame,
} from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { useClients } from "@/hooks/useClients";
import { useAllNutritionPlans, useDeleteNutritionPlanById } from "@/hooks/useNutrition";
import { NutritionPlanSheet } from "@/components/nutrition/NutritionPlanSheet";
import { usePageReveal } from "@/lib/page-reveal";
import type { NutritionPlan, ClientEnriched, ClientEnrichedListResponse } from "@/types/api";

// ── KPI config ────────────────────────────────────────────────────────────

type KpiDef = {
  key: "totale" | "attivi" | "clienti";
  label: string;
  sub?: string;
  icon: React.ComponentType<{ className?: string }>;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
};

const NUTRITION_KPI: KpiDef[] = [
  {
    key: "totale",
    label: "Piani totali",
    icon: Apple,
    borderColor: "border-l-teal-500",
    gradient: "from-teal-50/80 to-white dark:from-teal-950/40 dark:to-zinc-900",
    iconBg: "bg-teal-100 dark:bg-teal-900/30",
    iconColor: "text-teal-600 dark:text-teal-400",
    valueColor: "text-teal-700 dark:text-teal-400",
  },
  {
    key: "attivi",
    label: "Piani attivi",
    icon: Flame,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "clienti",
    label: "Clienti",
    sub: "con almeno 1 piano",
    icon: Users,
    borderColor: "border-l-blue-500",
    gradient: "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    valueColor: "text-blue-700 dark:text-blue-400",
  },
];

// ── Pagina ─────────────────────────────────────────────────────────────────

export default function NutrizionePage() {
  const router = useRouter();
  const { revealClass, revealStyle } = usePageReveal();

  const [clientFilter, setClientFilter] = useState<string>("__all__");
  const [soloAttivi, setSoloAttivi] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<NutritionPlan | null>(null);

  const { data: clients = [] } = useClients();
  const { data: plans = [], isLoading } = useAllNutritionPlans();
  const deletePlan = useDeleteNutritionPlanById();

  // Filtro client-side
  const filtered = useMemo(() => {
    let result = plans;
    if (clientFilter !== "__all__") result = result.filter((p) => p.id_cliente === parseInt(clientFilter));
    if (soloAttivi) result = result.filter((p) => p.attivo);
    return result;
  }, [plans, clientFilter, soloAttivi]);

  // KPI
  const kpi = useMemo(() => ({
    totale: plans.length,
    attivi: plans.filter((p) => p.attivo).length,
    clienti: new Set(plans.map((p) => p.id_cliente)).size,
  }), [plans]);

  const clientsList: ClientEnriched[] = Array.isArray(clients)
    ? clients
    : (clients as ClientEnrichedListResponse)?.items ?? [];

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div
        className={revealClass(0, "flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between")}
        style={revealStyle(0)}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
            <UtensilsCrossed className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Nutrizione</h1>
            <p className="text-sm text-muted-foreground">
              Piani alimentari personalizzati
              {plans.length > 0 && ` — ${plans.length} pian${plans.length === 1 ? "o" : "i"}`}
            </p>
          </div>
        </div>
        <Button onClick={() => setSheetOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          <span className="hidden sm:inline">Nuovo Piano</span>
        </Button>
      </div>

      {/* ── KPI ── */}
      <div
        className={revealClass(40, "grid grid-cols-1 gap-3 sm:grid-cols-3")}
        style={revealStyle(40)}
      >
        {NUTRITION_KPI.map((k) => {
          const Icon = k.icon;
          return (
            <div
              key={k.key}
              className={`flex items-start gap-3 rounded-xl border border-l-4 ${k.borderColor} bg-gradient-to-br ${k.gradient} p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg sm:h-10 sm:w-10 ${k.iconBg}`}>
                <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${k.iconColor}`} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70 sm:text-[11px]">
                  {k.label}
                </p>
                <AnimatedNumber
                  value={kpi[k.key]}
                  className={`text-xl font-extrabold tabular-nums tracking-tighter sm:text-3xl ${k.valueColor}`}
                />
                {k.sub && (
                  <p className="text-[10px] font-medium text-muted-foreground/60">{k.sub}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Filtri ── */}
      <div
        className={revealClass(80, "flex flex-wrap items-center gap-2")}
        style={revealStyle(80)}
      >
        <Select value={clientFilter} onValueChange={setClientFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Tutti i clienti" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Tutti i clienti</SelectItem>
            {clientsList.map((c: { id: number; nome: string; cognome: string }) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.cognome} {c.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <button
          onClick={() => setSoloAttivi(!soloAttivi)}
          className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            soloAttivi
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          <CheckCircle2 className="h-3 w-3" />
          Solo attivi
        </button>

        {(clientFilter !== "__all__" || soloAttivi) && (
          <button
            onClick={() => { setClientFilter("__all__"); setSoloAttivi(false); }}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Rimuovi filtri
          </button>
        )}
      </div>

      {/* ── Tabella ── */}
      <div className={revealClass(120)} style={revealStyle(120)}>
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-12 w-full rounded-lg" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-dashed p-12 text-center">
            <UtensilsCrossed className="mx-auto h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-lg font-medium">
              {plans.length === 0 ? "Nessun piano alimentare" : "Nessun risultato"}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {plans.length === 0
                ? "Crea il primo piano alimentare per un cliente."
                : "Nessun piano corrisponde ai filtri selezionati."}
            </p>
            {plans.length === 0 && (
              <Button className="mt-4" onClick={() => setSheetOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Nuovo Piano
              </Button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome piano</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead className="hidden sm:table-cell text-center">kcal/die</TableHead>
                  <TableHead className="hidden md:table-cell text-center">Pasti</TableHead>
                  <TableHead className="hidden sm:table-cell">Date</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((p: NutritionPlan) => (
                  <TableRow
                    key={p.id}
                    className="cursor-pointer transition-colors hover:bg-muted/50"
                    onClick={() => router.push(`/nutrizione/${p.id}`)}
                  >
                    <TableCell className="font-medium">{p.nome}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {p.client_cognome} {p.client_nome}
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-center tabular-nums">
                      {p.obiettivo_calorico ?? "—"}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-center tabular-nums">
                      {p.num_pasti ?? 0}
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-xs text-muted-foreground">
                      {p.data_inizio
                        ? format(new Date(p.data_inizio), "dd MMM yy", { locale: it })
                        : "—"}
                      {p.data_fine
                        ? ` → ${format(new Date(p.data_fine), "dd MMM yy", { locale: it })}`
                        : ""}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          p.attivo
                            ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400"
                            : "text-muted-foreground"
                        }`}
                      >
                        {p.attivo ? "Attivo" : "Inattivo"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => setDeleteTarget(p)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* ── Sheet nuovo piano ── */}
      <NutritionPlanSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        clientId={clientFilter !== "__all__" ? parseInt(clientFilter) : null}
        plan={null}
      />

      {/* ── Conferma eliminazione ── */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Elimina piano alimentare</AlertDialogTitle>
            <AlertDialogDescription>
              Vuoi eliminare il piano &quot;{deleteTarget?.nome}&quot;
              {deleteTarget && ` di ${deleteTarget.client_cognome} ${deleteTarget.client_nome}`}?
              Verranno eliminati anche tutti i pasti e gli alimenti associati.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => {
                if (deleteTarget) {
                  deletePlan.mutate({ clientId: deleteTarget.id_cliente, planId: deleteTarget.id });
                  setDeleteTarget(null);
                }
              }}
            >
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
