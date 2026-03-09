// src/app/(dashboard)/allenamenti/page.tsx
"use client";

/**
 * Pagina Monitoraggio Allenamenti — v2 (redesign premium).
 *
 * Visualizza programmi attivati con griglia settimane x sessioni,
 * compliance %, registrazione/rimozione esecuzioni.
 *
 * v2: KPI hero cards, program card gradient, celle 4 stati,
 * settimana corrente highlight, smart date suggestion,
 * DatePicker vincolato a settimana, filtri chip con conteggio.
 *
 * Data flow:
 * - useWorkouts() → tutti i piani (filtra client-side a quelli con id_cliente)
 * - useWorkoutLogs(planId) → log per ogni piano visibile
 * - useClients() → filtro per cliente
 * - Status derivato client-side da date (zero campo DB)
 */

import { useState, useMemo, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { loadFilters, saveFilters, getUrlParams, syncUrlParams } from "@/lib/url-state";
import { usePageReveal } from "@/lib/page-reveal";
import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  Activity,
  ArrowLeft,
  ClipboardList,
  CalendarDays,
  Check,
  ChevronDown,
  Trash2,
  Plus,
  User,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { DatePicker } from "@/components/ui/date-picker";

import { useWorkouts, useUpdateWorkout, useWorkoutLogs, useCreateWorkoutLog, useDeleteWorkoutLog } from "@/hooks/useWorkouts";
import { useClients } from "@/hooks/useClients";
import { toISOLocal } from "@/lib/format";
import type { WorkoutPlan, WorkoutLog } from "@/types/api";
import {
  getProgramStatus,
  STATUS_LABELS,
  STATUS_COLORS,
  computeWeeks,
  matchLogsToGrid,
  computeCompliance,
  computeExpected,
  getComplianceColor,
  getComplianceTextColor,
  isWeekPastOrCurrent,
  isWeekFuture,
  isCurrentWeek,
  suggestSessionDate,
  formatShortDate,
  formatDateRange,
  type ProgramStatus,
  type WeekSlot,
} from "@/lib/workout-monitoring";

// ════════════════════════════════════════════════════════════
// KPI CONFIG (pattern Dashboard/Clienti)
// ════════════════════════════════════════════════════════════

interface MonitoringKpiDef {
  key: string;
  label: string;
  icon: LucideIcon;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

const MONITORING_KPI: MonitoringKpiDef[] = [
  {
    key: "attivi",
    label: "Programmi Attivi",
    icon: Activity,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "da_attivare",
    label: "Da Attivare",
    icon: AlertTriangle,
    borderColor: "border-l-amber-500",
    gradient: "from-amber-50/80 to-white dark:from-amber-950/40 dark:to-zinc-900",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
    iconColor: "text-amber-600 dark:text-amber-400",
    valueColor: "text-amber-700 dark:text-amber-400",
  },
];

// ════════════════════════════════════════════════════════════
// STATUS FILTER CHIPS
// ════════════════════════════════════════════════════════════

const STATUS_CHIP_COLORS: Record<"tutti" | ProgramStatus, string> = {
  tutti: "#71717a",      // zinc-500
  attivo: "#10b981",     // emerald-500
  da_attivare: "#f59e0b", // amber-500
  completato: "#a1a1aa",  // zinc-400
};

const STATUS_FILTER_LABELS: Record<"tutti" | ProgramStatus, string> = {
  tutti: "Tutti",
  attivo: "Attivi",
  da_attivare: "Da attivare",
  completato: "Completati",
};

// ════════════════════════════════════════════════════════════
// CARD STYLES PER STATUS
// ════════════════════════════════════════════════════════════

const STATUS_CARD_BORDER: Record<ProgramStatus, string> = {
  attivo: "border-l-emerald-500",
  da_attivare: "border-l-amber-500",
  completato: "border-l-zinc-400",
};

const STATUS_CARD_GRADIENT: Record<ProgramStatus, string> = {
  attivo: "from-emerald-50/30 to-white dark:from-emerald-950/20 dark:to-zinc-900",
  da_attivare: "from-amber-50/30 to-white dark:from-amber-950/20 dark:to-zinc-900",
  completato: "from-zinc-50/30 to-white dark:from-zinc-900/20 dark:to-zinc-900",
};

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function AllenamentiPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const router = useRouter();
  const initialClientId = getUrlParams().get("idCliente");

  const { data: workoutsData, isLoading: loadingWorkouts } = useWorkouts();
  const { data: clientsData } = useClients();

  // Filter state (sessionStorage → URL → default)
  const [clientFilter, setClientFilter] = useState<string>(() => {
    if (initialClientId) return initialClientId;
    const saved = loadFilters("allenamenti");
    if (saved?.clientFilter) return saved.clientFilter as string;
    return "__all__";
  });
  const [statusFilter, setStatusFilter] = useState<"tutti" | ProgramStatus>(() => {
    const saved = loadFilters("allenamenti");
    if (saved?.statusFilter) return saved.statusFilter as "tutti" | ProgramStatus;
    const s = getUrlParams().get("status");
    if (s && ["attivo", "da_attivare", "completato"].includes(s)) return s as ProgramStatus;
    return "tutti";
  });

  // ── Sync filtri → sessionStorage + URL (feedback visivo) ──
  useEffect(() => {
    saveFilters("allenamenti", {
      clientFilter: clientFilter !== "__all__" ? clientFilter : null,
      statusFilter: statusFilter !== "tutti" ? statusFilter : null,
    });
    const params = new URLSearchParams();
    if (clientFilter !== "__all__") params.set("idCliente", clientFilter);
    if (statusFilter !== "tutti") params.set("status", statusFilter);
    syncUrlParams(window.location.pathname, params);
  }, [clientFilter, statusFilter]);

  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  // Solo piani con cliente assegnato
  const plansWithClient = useMemo(() => {
    const all = workoutsData?.items ?? [];
    return all.filter((p) => p.id_cliente !== null);
  }, [workoutsData]);

  // Conteggi per status (per chip e KPI)
  const statusCounts = useMemo(() => {
    const counts = { attivo: 0, da_attivare: 0, completato: 0 };
    for (const p of plansWithClient) {
      const s = getProgramStatus(p);
      counts[s]++;
    }
    return counts;
  }, [plansWithClient]);

  // KPI values
  const kpiValues: Record<string, number> = {
    attivi: statusCounts.attivo,
    da_attivare: statusCounts.da_attivare,
  };

  // Filtro client-side
  const filteredPlans = useMemo(() => {
    let result = plansWithClient;

    if (clientFilter !== "__all__") {
      const cid = Number(clientFilter);
      result = result.filter((p) => p.id_cliente === cid);
    }

    if (statusFilter !== "tutti") {
      result = result.filter((p) => getProgramStatus(p) === statusFilter);
    }

    return result;
  }, [plansWithClient, clientFilter, statusFilter]);

  // Conteggi per chip filtro (basati su piani filtrati per cliente)
  const chipCounts = useMemo(() => {
    const base = clientFilter === "__all__"
      ? plansWithClient
      : plansWithClient.filter((p) => p.id_cliente === Number(clientFilter));
    const counts: Record<string, number> = { tutti: base.length };
    for (const p of base) {
      const s = getProgramStatus(p);
      counts[s] = (counts[s] ?? 0) + 1;
    }
    return counts;
  }, [plansWithClient, clientFilter]);

  if (loadingWorkouts) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
            <Activity className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Monitoraggio Allenamenti</h1>
            <p className="text-sm text-muted-foreground">Monitora aderenza e progresso dei programmi</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header con icona gradient ── */}
      <div data-guide="monitoraggio-header" className={revealClass(0, "flex items-center gap-3")} style={revealStyle(0)}>
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
          <Activity className="h-5 w-5 text-teal-600 dark:text-teal-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Monitoraggio Allenamenti</h1>
          <p className="text-sm text-muted-foreground">Monitora aderenza e progresso dei programmi</p>
        </div>
      </div>

      {/* ── Banner ritorno al cliente ── */}
      {initialClientId && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-2 flex items-center gap-2">
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <Link
            href={`/clienti/${initialClientId}?tab=schede`}
            className="text-sm text-primary hover:underline"
          >
            Torna al profilo cliente
          </Link>
        </div>
      )}

      {/* ── KPI Hero Cards ── */}
      <div className={revealClass(50, "grid grid-cols-2 gap-4")} style={revealStyle(50)}>
        {MONITORING_KPI.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div
              key={kpi.key}
              className={`flex items-start gap-2 rounded-xl border border-l-4 ${kpi.borderColor} bg-gradient-to-br ${kpi.gradient} p-3 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg sm:gap-3 sm:p-4`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg sm:h-10 sm:w-10 ${kpi.iconBg}`}>
                <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${kpi.iconColor}`} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-semibold tracking-widest text-muted-foreground/70 uppercase sm:text-[11px]">
                  {kpi.label}
                </p>
                <p className={`text-xl font-extrabold tracking-tighter tabular-nums sm:text-3xl ${kpi.valueColor}`}>
                  {kpiValues[kpi.key] ?? 0}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Filtri ── */}
      <div className={revealClass(100, "flex flex-wrap gap-3 items-center")} style={revealStyle(100)}>
        <Select value={clientFilter} onValueChange={setClientFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Tutti i clienti" />
          </SelectTrigger>
          <SelectContent position="popper" sideOffset={4}>
            <SelectItem value="__all__">Tutti i clienti</SelectItem>
            {clients
              .filter((c) => plansWithClient.some((p) => p.id_cliente === c.id))
              .map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nome} {c.cognome}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>

        <div className="flex gap-1.5">
          {(["tutti", "attivo", "da_attivare", "completato"] as const).map((key) => {
            const active = statusFilter === key;
            const color = STATUS_CHIP_COLORS[key];
            const count = chipCounts[key] ?? 0;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setStatusFilter(key)}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-[11px] font-medium transition-all duration-200 sm:px-3 sm:text-xs ${
                  active
                    ? "border-transparent shadow-sm"
                    : "border-dashed border-muted-foreground/30 opacity-50"
                }`}
                style={
                  active
                    ? { backgroundColor: color + "20", color }
                    : undefined
                }
              >
                <div
                  className="h-2 w-2 rounded-full transition-opacity"
                  style={{ backgroundColor: color, opacity: active ? 1 : 0.3 }}
                />
                {STATUS_FILTER_LABELS[key]}
                <span className="tabular-nums opacity-70">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Cards ── */}
      {filteredPlans.length === 0 ? (
        <div className={revealClass(150, "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-16")} style={revealStyle(150)}>
          <ClipboardList className="h-10 w-10 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">
            {plansWithClient.length === 0
              ? "Nessuna scheda assegnata a un cliente"
              : "Nessun programma corrisponde ai filtri"}
          </p>
          <Button variant="outline" size="sm" onClick={() => router.push("/schede")}>
            <Plus className="mr-2 h-4 w-4" />
            Vai alle Schede
          </Button>
        </div>
      ) : (
        <div className={revealClass(150, "space-y-4")} style={revealStyle(150)}>
          {filteredPlans.map((plan) => (
            <ProgramCard key={plan.id} plan={plan} />
          ))}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PROGRAM CARD (premium)
// ════════════════════════════════════════════════════════════

function ProgramCard({ plan }: { plan: WorkoutPlan }) {
  const status = getProgramStatus(plan);
  const [activateOpen, setActivateOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const { data: logsData } = useWorkoutLogs(plan.id);
  const logs = logsData?.items ?? [];

  const sessionIds = useMemo(
    () => plan.sessioni.map((s) => s.id),
    [plan.sessioni],
  );

  const weeks = useMemo(() => {
    if (!plan.data_inizio || !plan.data_fine) return [];
    return computeWeeks(plan.data_inizio, plan.data_fine);
  }, [plan.data_inizio, plan.data_fine]);

  const logGrid = useMemo(
    () => matchLogsToGrid(logs, weeks, sessionIds),
    [logs, weeks, sessionIds],
  );

  const expected = computeExpected(weeks, plan.sessioni.length);
  const completed = logGrid.size;
  const compliance = computeCompliance(expected, completed);

  const clientName = plan.client_nome && plan.client_cognome
    ? `${plan.client_nome} ${plan.client_cognome}`
    : "—";

  // "da_attivare" non ha griglia — layout semplice senza collapsible
  const hasGrid = status !== "da_attivare" && weeks.length > 0;

  return (
    <>
      <div className={`rounded-xl border transition-all duration-200 ${
        status === "da_attivare"
          ? `border-l-4 ${STATUS_CARD_BORDER[status]} bg-gradient-to-br ${STATUS_CARD_GRADIENT[status]} shadow-sm hover:-translate-y-0.5 hover:shadow-lg`
          : status === "attivo" && compliance < 60
            ? `border-l-4 border-l-red-400 bg-gradient-to-br from-red-50/20 to-white dark:from-red-950/10 dark:to-zinc-900 shadow-sm hover:-translate-y-0.5 hover:shadow-lg`
            : status === "completato"
              ? "bg-zinc-50/50 dark:bg-zinc-900/50"
              : `border-l-4 ${STATUS_CARD_BORDER[status]} bg-white dark:bg-zinc-900`
      }`}>
        {/* ── Compact header (sempre visibile, clickable per espandere) ── */}
        <button
          type="button"
          className="w-full text-left p-3 sm:p-4"
          onClick={() => hasGrid && setExpanded((v) => !v)}
          style={{ cursor: hasGrid ? "pointer" : "default" }}
        >
          <div className="flex items-center gap-3">
            {/* Info principale */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-bold tracking-tight truncate">{plan.nome}</h3>
                <Badge className={`text-[10px] ${STATUS_COLORS[status]}`}>
                  {STATUS_LABELS[status]}
                </Badge>
              </div>
              <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
                <User className="h-3 w-3 shrink-0" />
                <Link
                  href={`/clienti/${plan.id_cliente}`}
                  className="text-primary hover:underline font-medium truncate"
                  onClick={(e) => e.stopPropagation()}
                >
                  {clientName}
                </Link>
                <span className="text-muted-foreground/40 hidden sm:inline">•</span>
                <span className="hidden sm:inline capitalize">{plan.obiettivo}</span>
                <span className="text-muted-foreground/40 hidden sm:inline">•</span>
                <span className="hidden sm:inline capitalize">{plan.livello}</span>
              </div>
            </div>

            {/* Compliance mini-bar (solo per piani con griglia) */}
            {hasGrid && (
              <div className="flex items-center gap-2.5 shrink-0">
                <div className="hidden sm:flex items-center gap-2 w-28">
                  <div className="h-1.5 flex-1 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${getComplianceColor(compliance)}`}
                      style={{ width: `${compliance}%` }}
                    />
                  </div>
                  <span className={`text-xs font-bold tabular-nums ${getComplianceTextColor(compliance)}`}>
                    {compliance}%
                  </span>
                </div>
                <ChevronDown className={`h-4 w-4 text-muted-foreground/50 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`} />
              </div>
            )}

            {/* CTA per "da_attivare" (inline, senza drill-down) */}
            {status === "da_attivare" && (
              <Button
                variant="outline"
                size="sm"
                className="text-xs shrink-0"
                onClick={(e) => { e.stopPropagation(); setActivateOpen(true); }}
              >
                <CalendarDays className="mr-1.5 h-3.5 w-3.5" />
                Attiva
              </Button>
            )}
          </div>
        </button>

        {/* ── Expanded content (drill-down) ── */}
        {expanded && hasGrid && (
          <div className="border-t px-3 pb-3 pt-3 space-y-4 sm:px-4 sm:pb-4">
            {/* Date range */}
            {plan.data_inizio && plan.data_fine && (
              <p className="flex items-center gap-1 text-xs text-muted-foreground tabular-nums">
                <CalendarDays className="h-3 w-3" />
                {formatDateRange(plan.data_inizio, plan.data_fine)}
                <span className="text-muted-foreground/50 ml-1">
                  ({weeks.length} sett.)
                </span>
              </p>
            )}

            {/* Griglia */}
            <ComplianceGrid
              plan={plan}
              weeks={weeks}
              logGrid={logGrid}
            />

            {/* Barra compliance dettagliata */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-muted-foreground">Aderenza</span>
                <span className={`font-extrabold tabular-nums ${getComplianceTextColor(compliance)}`}>
                  {compliance}%
                </span>
              </div>
              <div className="relative h-2.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${getComplianceColor(compliance)}`}
                  style={{ width: `${compliance}%` }}
                />
              </div>
              <div className="text-[10px] text-muted-foreground tabular-nums">
                {completed} di {expected} sessioni completate
              </div>
            </div>

            {/* Azioni */}
            <div className="flex items-center justify-between pt-1">
              <Button
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => setActivateOpen(true)}
              >
                <CalendarDays className="mr-1.5 h-3.5 w-3.5" />
                Modifica date
              </Button>
              <Link href={`/schede/${plan.id}?from=allenamenti`}>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  Vai alla Scheda →
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>

      <ActivateDialog
        open={activateOpen}
        onOpenChange={setActivateOpen}
        plan={plan}
      />
    </>
  );
}

// ════════════════════════════════════════════════════════════
// COMPLIANCE GRID (premium)
// ════════════════════════════════════════════════════════════

function ComplianceGrid({
  plan,
  weeks,
  logGrid,
}: {
  plan: WorkoutPlan;
  weeks: WeekSlot[];
  logGrid: Map<string, WorkoutLog>;
}) {
  const totalSessions = plan.sessioni.length;

  return (
    <div className="overflow-x-auto -mx-4 px-4 sm:-mx-5 sm:px-5">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-24 text-xs font-semibold">Settimana</TableHead>
            {plan.sessioni.map((s) => (
              <TableHead key={s.id} className="text-xs text-center min-w-[110px] font-semibold">
                {s.nome_sessione}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {weeks.map((week) => {
            const current = isCurrentWeek(week);
            const past = isWeekPastOrCurrent(week) && !current;
            const future = isWeekFuture(week);

            return (
              <TableRow
                key={week.weekNumber}
                className={current ? "bg-primary/5 dark:bg-primary/10" : "hover:bg-transparent"}
              >
                <TableCell className="text-xs text-muted-foreground tabular-nums whitespace-nowrap py-2">
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium">Sett. {week.weekNumber}</span>
                    {current && (
                      <Badge variant="outline" className="text-[9px] px-1 py-0 border-primary/30 text-primary">
                        Corrente
                      </Badge>
                    )}
                  </div>
                  <div className="text-[10px] text-muted-foreground/70">
                    {formatShortDate(week.startDate)} — {formatShortDate(week.endDate)}
                  </div>
                </TableCell>
                {plan.sessioni.map((session, sessionIndex) => {
                  const key = `${week.weekNumber}-${session.id}`;
                  const log = logGrid.get(key);

                  return (
                    <TableCell key={session.id} className="text-center p-1.5">
                      {log ? (
                        <LoggedCell log={log} clientId={plan.id_cliente!} />
                      ) : past ? (
                        <MissedCell
                          planId={plan.id}
                          sessionId={session.id}
                          clientId={plan.id_cliente!}
                          week={week}
                          sessionIndex={sessionIndex}
                          totalSessions={totalSessions}
                        />
                      ) : current ? (
                        <PendingCell
                          planId={plan.id}
                          sessionId={session.id}
                          clientId={plan.id_cliente!}
                          week={week}
                          sessionIndex={sessionIndex}
                          totalSessions={totalSessions}
                        />
                      ) : future ? (
                        <div className="flex items-center justify-center h-12 rounded-lg bg-muted/20 opacity-40">
                          <span className="text-[10px] text-muted-foreground">—</span>
                        </div>
                      ) : null}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

// ── Cella: log presente (completata) ──

function LoggedCell({ log, clientId }: { log: WorkoutLog; clientId: number }) {
  const deleteLog = useDeleteWorkoutLog(clientId);
  const [open, setOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const logDate = new Date(log.data_esecuzione + "T00:00:00");
  const dateStr = format(logDate, "dd MMM", { locale: it });

  return (
    <Popover open={open} onOpenChange={(o) => { setOpen(o); if (!o) setConfirmDelete(false); }}>
      <PopoverTrigger asChild>
        <button className="flex flex-col items-center justify-center h-12 w-full rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/50 dark:border-emerald-800/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors">
          <Check className="h-4 w-4" />
          <span className="text-[10px] font-medium tabular-nums">{dateStr}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-60 p-3 space-y-2">
        <div className="text-xs space-y-1">
          <div className="font-semibold">{log.sessione_nome}</div>
          <div className="text-muted-foreground tabular-nums">
            {format(logDate, "dd MMMM yyyy", { locale: it })}
          </div>
          {log.note && (
            <div className="text-muted-foreground italic border-l-2 border-muted pl-2">{log.note}</div>
          )}
        </div>
        {!confirmDelete ? (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs text-destructive hover:text-destructive"
            onClick={() => setConfirmDelete(true)}
            disabled={deleteLog.isPending}
          >
            <Trash2 className="mr-1.5 h-3 w-3" />
            Rimuovi
          </Button>
        ) : (
          <div className="space-y-1.5">
            <p className="text-xs text-muted-foreground text-center">Confermi la rimozione?</p>
            <div className="flex gap-1.5">
              <Button variant="outline" size="sm" className="h-7 flex-1 text-xs" onClick={() => setConfirmDelete(false)}>
                Annulla
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="h-7 flex-1 text-xs"
                onClick={() => { deleteLog.mutate(log.id); setOpen(false); }}
                disabled={deleteLog.isPending}
              >
                Conferma
              </Button>
            </div>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}

// ── Cella: mancata (settimana passata, nessun log) ──

function MissedCell({
  planId,
  sessionId,
  clientId,
  week,
  sessionIndex,
  totalSessions,
}: {
  planId: number;
  sessionId: number;
  clientId: number;
  week: WeekSlot;
  sessionIndex: number;
  totalSessions: number;
}) {
  const createLog = useCreateWorkoutLog(clientId);
  const [open, setOpen] = useState(false);
  const suggestedDate = suggestSessionDate(week, sessionIndex, totalSessions);
  const [date, setDate] = useState<Date | undefined>(suggestedDate);
  const [note, setNote] = useState("");

  const handleSubmit = useCallback(() => {
    if (!date) return;
    const dateStr = toISOLocal(date).slice(0, 10);
    createLog.mutate(
      {
        id_scheda: planId,
        id_sessione: sessionId,
        data_esecuzione: dateStr,
        note: note.trim() || null,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setNote("");
        },
      },
    );
  }, [date, note, planId, sessionId, createLog]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className="flex flex-col items-center justify-center h-12 w-full rounded-lg bg-red-50/50 dark:bg-red-950/20 border border-dashed border-red-300/50 dark:border-red-800/30 text-red-400 dark:text-red-500/60 hover:bg-red-50 dark:hover:bg-red-950/30 hover:border-red-300 dark:hover:border-red-700/50 transition-colors">
          <span className="text-[10px] font-medium">Mancata</span>
          <Plus className="h-3 w-3 mt-0.5 opacity-60" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3 space-y-3">
        <div className="text-xs font-semibold">Registra esecuzione retroattiva</div>
        <DatePicker
          value={date}
          onChange={setDate}
          placeholder="Data esecuzione"
          minDate={week.startDate}
          maxDate={week.endDate}
        />
        <Input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Nota (opzionale)"
          className="h-8 text-xs"
        />
        <Button
          size="sm"
          className="w-full text-xs"
          onClick={handleSubmit}
          disabled={!date || createLog.isPending}
        >
          <Check className="mr-1.5 h-3 w-3" />
          {createLog.isPending ? "Registrazione..." : "Registra"}
        </Button>
      </PopoverContent>
    </Popover>
  );
}

// ── Cella: pendente (settimana corrente, non ancora dovuta) ──

function PendingCell({
  planId,
  sessionId,
  clientId,
  week,
  sessionIndex,
  totalSessions,
}: {
  planId: number;
  sessionId: number;
  clientId: number;
  week: WeekSlot;
  sessionIndex: number;
  totalSessions: number;
}) {
  const createLog = useCreateWorkoutLog(clientId);
  const [open, setOpen] = useState(false);
  const suggestedDate = suggestSessionDate(week, sessionIndex, totalSessions);
  const [date, setDate] = useState<Date | undefined>(suggestedDate);
  const [note, setNote] = useState("");

  const handleSubmit = useCallback(() => {
    if (!date) return;
    const dateStr = toISOLocal(date).slice(0, 10);
    createLog.mutate(
      {
        id_scheda: planId,
        id_sessione: sessionId,
        data_esecuzione: dateStr,
        note: note.trim() || null,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setNote("");
        },
      },
    );
  }, [date, note, planId, sessionId, createLog]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className="flex flex-col items-center justify-center h-12 w-full rounded-lg border border-dashed border-primary/40 text-primary/50 hover:border-primary hover:text-primary hover:bg-primary/5 transition-colors">
          <Plus className="h-4 w-4" />
          <span className="text-[10px] font-medium mt-0.5">Registra</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3 space-y-3">
        <div className="text-xs font-semibold">Registra esecuzione</div>
        <DatePicker
          value={date}
          onChange={setDate}
          placeholder="Data esecuzione"
          minDate={week.startDate}
          maxDate={week.endDate}
        />
        <Input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Nota (opzionale)"
          className="h-8 text-xs"
        />
        <Button
          size="sm"
          className="w-full text-xs"
          onClick={handleSubmit}
          disabled={!date || createLog.isPending}
        >
          <Check className="mr-1.5 h-3 w-3" />
          {createLog.isPending ? "Registrazione..." : "Registra"}
        </Button>
      </PopoverContent>
    </Popover>
  );
}

// ════════════════════════════════════════════════════════════
// ACTIVATE DIALOG
// ════════════════════════════════════════════════════════════

function ActivateDialog({
  open,
  onOpenChange,
  plan,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  plan: WorkoutPlan;
}) {
  const updateWorkout = useUpdateWorkout();

  const [dataInizio, setDataInizio] = useState<Date | undefined>(
    plan.data_inizio ? new Date(plan.data_inizio + "T00:00:00") : undefined,
  );
  const [dataFine, setDataFine] = useState<Date | undefined>(
    plan.data_fine ? new Date(plan.data_fine + "T00:00:00") : undefined,
  );

  // Sync state quando le date del piano cambiano
  const handleOpen = useCallback((v: boolean) => {
    if (v) {
      setDataInizio(plan.data_inizio ? new Date(plan.data_inizio + "T00:00:00") : undefined);
      setDataFine(plan.data_fine ? new Date(plan.data_fine + "T00:00:00") : undefined);
    }
    onOpenChange(v);
  }, [plan.data_inizio, plan.data_fine, onOpenChange]);

  const isValid = dataInizio && dataFine && dataFine > dataInizio;

  const handleSubmit = useCallback(() => {
    if (!isValid) return;
    const inizio = toISOLocal(dataInizio).slice(0, 10);
    const fine = toISOLocal(dataFine).slice(0, 10);
    updateWorkout.mutate(
      { id: plan.id, data_inizio: inizio, data_fine: fine },
      { onSuccess: () => onOpenChange(false) },
    );
  }, [isValid, dataInizio, dataFine, plan.id, updateWorkout, onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {plan.data_inizio ? "Modifica date programma" : "Attiva programma"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{plan.nome}</span>
            {" — "}
            {plan.client_nome} {plan.client_cognome}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium">Data inizio</label>
              <DatePicker
                value={dataInizio}
                onChange={setDataInizio}
                placeholder="Inizio"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium">Data fine</label>
              <DatePicker
                value={dataFine}
                onChange={setDataFine}
                placeholder="Fine"
              />
            </div>
          </div>

          {dataInizio && dataFine && dataFine <= dataInizio && (
            <p className="text-xs text-destructive">
              La data fine deve essere successiva alla data inizio
            </p>
          )}

          {isValid && (
            <p className="text-xs text-muted-foreground">
              Durata: {computeWeeks(
                toISOLocal(dataInizio).slice(0, 10),
                toISOLocal(dataFine).slice(0, 10),
              ).length} settimane
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annulla
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || updateWorkout.isPending}>
            {updateWorkout.isPending ? "Salvataggio..." : plan.data_inizio ? "Aggiorna" : "Attiva"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
