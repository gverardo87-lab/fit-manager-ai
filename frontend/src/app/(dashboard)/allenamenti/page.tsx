// src/app/(dashboard)/allenamenti/page.tsx
"use client";

/**
 * Pagina Monitoraggio Allenamenti.
 *
 * Visualizza programmi attivati con griglia settimane x sessioni,
 * compliance %, registrazione/rimozione esecuzioni.
 *
 * Data flow:
 * - useWorkouts() → tutti i piani (filtra client-side a quelli con id_cliente)
 * - useWorkoutLogs(planId) → log per ogni piano visibile
 * - useClients() → filtro per cliente
 * - Status derivato client-side da date (zero campo DB)
 */

import { useState, useMemo, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  Activity,
  ClipboardList,
  CalendarDays,
  Check,
  Trash2,
  Plus,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
  getComplianceColor,
  getComplianceTextColor,
  isWeekPastOrCurrent,
  isWeekFuture,
  formatShortDate,
  formatDateRange,
  type ProgramStatus,
  type WeekSlot,
} from "@/lib/workout-monitoring";

// ════════════════════════════════════════════════════════════
// FILTRO STATUS
// ════════════════════════════════════════════════════════════

const STATUS_FILTERS: { value: "tutti" | ProgramStatus; label: string }[] = [
  { value: "tutti", label: "Tutti" },
  { value: "attivo", label: "Attivi" },
  { value: "da_attivare", label: "Da attivare" },
  { value: "completato", label: "Completati" },
];

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function AllenamentiPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialClientId = searchParams.get("idCliente");

  const { data: workoutsData, isLoading: loadingWorkouts } = useWorkouts();
  const { data: clientsData } = useClients();

  // Filtri
  const [clientFilter, setClientFilter] = useState<string>(initialClientId ?? "__all__");
  const [statusFilter, setStatusFilter] = useState<"tutti" | ProgramStatus>("tutti");

  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  // Solo piani con cliente assegnato
  const plansWithClient = useMemo(() => {
    const all = workoutsData?.items ?? [];
    return all.filter((p) => p.id_cliente !== null);
  }, [workoutsData]);

  // Filtro client-side
  const filteredPlans = useMemo(() => {
    let result = plansWithClient;

    // Filtro cliente
    if (clientFilter !== "__all__") {
      const cid = Number(clientFilter);
      result = result.filter((p) => p.id_cliente === cid);
    }

    // Filtro status
    if (statusFilter !== "tutti") {
      result = result.filter((p) => getProgramStatus(p) === statusFilter);
    }

    return result;
  }, [plansWithClient, clientFilter, statusFilter]);

  if (loadingWorkouts) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Activity className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Programmi Allenamento</h1>
            <p className="text-sm text-muted-foreground">Monitora aderenza e progresso</p>
          </div>
        </div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Activity className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Programmi Allenamento</h1>
          <p className="text-sm text-muted-foreground">Monitora aderenza e progresso</p>
        </div>
      </div>

      {/* Filtri */}
      <div className="flex flex-wrap gap-3 items-center">
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
          {STATUS_FILTERS.map((sf) => (
            <Button
              key={sf.value}
              variant={statusFilter === sf.value ? "default" : "outline"}
              size="sm"
              className="text-xs"
              onClick={() => setStatusFilter(sf.value)}
            >
              {sf.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Cards */}
      {filteredPlans.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-16">
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
        <div className="space-y-4">
          {filteredPlans.map((plan) => (
            <ProgramCard key={plan.id} plan={plan} />
          ))}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PROGRAM CARD
// ════════════════════════════════════════════════════════════

function ProgramCard({ plan }: { plan: WorkoutPlan }) {
  const status = getProgramStatus(plan);
  const [activateOpen, setActivateOpen] = useState(false);
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

  // Compliance
  const expected = weeks.filter(isWeekPastOrCurrent).length * plan.sessioni.length;
  const completed = logGrid.size;
  const compliance = computeCompliance(expected, completed);

  const clientName = plan.client_nome && plan.client_cognome
    ? `${plan.client_nome} ${plan.client_cognome}`
    : "—";

  return (
    <>
      <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-lg font-bold tracking-tight">{plan.nome}</h3>
                <Badge className={STATUS_COLORS[status]}>
                  {STATUS_LABELS[status]}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground flex-wrap">
                <Link
                  href={`/clienti/${plan.id_cliente}`}
                  className="text-primary hover:underline font-medium"
                  onClick={(e) => e.stopPropagation()}
                >
                  {clientName}
                </Link>
                <span>•</span>
                <Badge variant="outline" className="text-xs">{plan.obiettivo}</Badge>
                <Badge variant="outline" className="text-xs">{plan.livello}</Badge>
              </div>
              {plan.data_inizio && plan.data_fine && (
                <p className="text-xs text-muted-foreground tabular-nums">
                  <CalendarDays className="inline h-3 w-3 mr-1" />
                  {formatDateRange(plan.data_inizio, plan.data_fine)}
                </p>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Griglia solo per piani attivati */}
          {status !== "da_attivare" && weeks.length > 0 && (
            <ComplianceGrid
              plan={plan}
              weeks={weeks}
              logGrid={logGrid}
            />
          )}

          {/* Barra compliance */}
          {status !== "da_attivare" && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Compliance</span>
                <span className={`font-bold tabular-nums ${getComplianceTextColor(compliance)}`}>
                  {compliance}% ({completed}/{expected})
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${getComplianceColor(compliance)}`}
                  style={{ width: `${compliance}%` }}
                />
              </div>
            </div>
          )}

          {/* Azioni */}
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => setActivateOpen(true)}
            >
              <CalendarDays className="mr-1.5 h-3.5 w-3.5" />
              {status === "da_attivare" ? "Attiva programma" : "Modifica date"}
            </Button>
            <Link href={`/schede/${plan.id}`}>
              <Button variant="ghost" size="sm" className="text-xs text-primary">
                Vai alla Scheda →
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <ActivateDialog
        open={activateOpen}
        onOpenChange={setActivateOpen}
        plan={plan}
      />
    </>
  );
}

// ════════════════════════════════════════════════════════════
// COMPLIANCE GRID
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
  return (
    <div className="overflow-x-auto -mx-6 px-6">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-20 text-xs">Settimana</TableHead>
            {plan.sessioni.map((s) => (
              <TableHead key={s.id} className="text-xs text-center min-w-[100px]">
                {s.nome_sessione}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {weeks.map((week) => (
            <TableRow key={week.weekNumber}>
              <TableCell className="text-xs text-muted-foreground tabular-nums whitespace-nowrap">
                <div>Sett. {week.weekNumber}</div>
                <div className="text-[10px]">
                  {formatShortDate(week.startDate)}
                </div>
              </TableCell>
              {plan.sessioni.map((session) => {
                const key = `${week.weekNumber}-${session.id}`;
                const log = logGrid.get(key);
                const pastOrCurrent = isWeekPastOrCurrent(week);
                const future = isWeekFuture(week);

                return (
                  <TableCell key={session.id} className="text-center p-1">
                    {log ? (
                      <LoggedCell log={log} clientId={plan.id_cliente!} />
                    ) : pastOrCurrent ? (
                      <EmptyPastCell
                        planId={plan.id}
                        sessionId={session.id}
                        clientId={plan.id_cliente!}
                        weekStart={week.startDate}
                      />
                    ) : future ? (
                      <div className="h-9 rounded bg-muted/30" />
                    ) : null}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// ── Cella: log presente ──

function LoggedCell({ log, clientId }: { log: WorkoutLog; clientId: number }) {
  const deleteLog = useDeleteWorkoutLog(clientId);
  const [open, setOpen] = useState(false);

  const logDate = new Date(log.data_esecuzione + "T00:00:00");
  const dateStr = format(logDate, "dd MMM", { locale: it });

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className="flex flex-col items-center justify-center h-9 w-full rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-950/50 transition-colors">
          <Check className="h-3.5 w-3.5" />
          <span className="text-[10px] tabular-nums">{dateStr}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-3 space-y-2">
        <div className="text-xs space-y-1">
          <div className="font-medium">{log.sessione_nome}</div>
          <div className="text-muted-foreground tabular-nums">
            {format(logDate, "dd MMMM yyyy", { locale: it })}
          </div>
          {log.note && (
            <div className="text-muted-foreground italic">{log.note}</div>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs text-destructive hover:text-destructive"
          onClick={() => {
            deleteLog.mutate(log.id);
            setOpen(false);
          }}
          disabled={deleteLog.isPending}
        >
          <Trash2 className="mr-1.5 h-3 w-3" />
          Rimuovi
        </Button>
      </PopoverContent>
    </Popover>
  );
}

// ── Cella: vuota (sett. passata/corrente) — clickable per registrare ──

function EmptyPastCell({
  planId,
  sessionId,
  clientId,
  weekStart,
}: {
  planId: number;
  sessionId: number;
  clientId: number;
  weekStart: Date;
}) {
  const createLog = useCreateWorkoutLog(clientId);
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState<Date | undefined>(weekStart);
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
        <button className="flex items-center justify-center h-9 w-full rounded border border-dashed border-muted-foreground/30 text-muted-foreground/40 hover:border-primary/50 hover:text-primary/60 transition-colors">
          <Plus className="h-3.5 w-3.5" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3 space-y-3">
        <div className="text-xs font-medium">Registra esecuzione</div>
        <DatePicker
          value={date}
          onChange={setDate}
          placeholder="Data esecuzione"
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
