// src/app/(dashboard)/schede/page.tsx
"use client";

/**
 * Pagina lista Schede Allenamento.
 *
 * Layout:
 * - Header con titolo + conteggio + "Nuova Scheda"
 * - KPI cards (totale, per obiettivo, per livello)
 * - Tabella con nome, cliente, obiettivo, livello, sessioni, data
 * - Click riga → /schede/[id]
 */

import { useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  ClipboardList,
  Target,
  TrendingUp,
  Users,
  Trash2,
  Copy,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { TemplateSelector } from "@/components/workouts/TemplateSelector";
import { useWorkouts, useDeleteWorkout, useDuplicateWorkout, type WorkoutFilters } from "@/hooks/useWorkouts";
import { OBIETTIVI_SCHEDA, LIVELLI_SCHEDA, type WorkoutPlan } from "@/types/api";

// ════════════════════════════════════════════════════════════
// COSTANTI UI
// ════════════════════════════════════════════════════════════

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza",
  ipertrofia: "Ipertrofia",
  resistenza: "Resistenza",
  dimagrimento: "Dimagrimento",
  generale: "Generale",
};

const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante",
  intermedio: "Intermedio",
  avanzato: "Avanzato",
};

const OBIETTIVO_COLORS: Record<string, string> = {
  forza: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  ipertrofia: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  resistenza: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  dimagrimento: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  generale: "bg-zinc-100 text-zinc-700 dark:bg-zinc-900/30 dark:text-zinc-400",
};

const LIVELLO_COLORS: Record<string, string> = {
  beginner: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  intermedio: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  avanzato: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

const NONE_VALUE = "__none__";

// ════════════════════════════════════════════════════════════
// PAGE COMPONENT
// ════════════════════════════════════════════════════════════

export default function SchedePage() {
  const router = useRouter();
  const [filters, setFilters] = useState<WorkoutFilters>({});
  const { data, isLoading, isError, refetch } = useWorkouts(filters);
  const deleteWorkout = useDeleteWorkout();
  const duplicateWorkout = useDuplicateWorkout();

  const [templateSelectorOpen, setTemplateSelectorOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<WorkoutPlan | null>(null);

  const workouts = data?.items ?? [];

  // KPI
  const kpi = useMemo(() => {
    const total = workouts.length;
    const byObiettivo = workouts.reduce<Record<string, number>>((acc, w) => {
      acc[w.obiettivo] = (acc[w.obiettivo] ?? 0) + 1;
      return acc;
    }, {});
    const byLivello = workouts.reduce<Record<string, number>>((acc, w) => {
      acc[w.livello] = (acc[w.livello] ?? 0) + 1;
      return acc;
    }, {});
    const withClient = workouts.filter((w) => w.id_cliente).length;
    return { total, byObiettivo, byLivello, withClient };
  }, [workouts]);

  const updateFilter = useCallback((key: keyof WorkoutFilters, value: string) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === NONE_VALUE || !value) {
        delete next[key];
      } else {
        (next as Record<string, string>)[key] = value;
      }
      return next;
    });
  }, []);

  const handleDelete = useCallback((plan: WorkoutPlan) => {
    setDeleteTarget(plan);
  }, []);

  const confirmDelete = useCallback(() => {
    if (!deleteTarget) return;
    deleteWorkout.mutate(deleteTarget.id, {
      onSuccess: () => setDeleteTarget(null),
    });
  }, [deleteTarget, deleteWorkout]);

  const handleDuplicate = useCallback((plan: WorkoutPlan) => {
    duplicateWorkout.mutate({ id: plan.id });
  }, [duplicateWorkout]);

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
            <ClipboardList className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Schede Allenamento</h1>
            {data && (
              <p className="text-sm text-muted-foreground">
                {data.total} sched{data.total === 1 ? "a" : "e"} nel tuo archivio
              </p>
            )}
          </div>
        </div>
        <Button onClick={() => setTemplateSelectorOpen(true)}>
          <Plus className="h-4 w-4 sm:mr-2" />
          <span className="hidden sm:inline">Nuova Scheda</span>
        </Button>
      </div>

      {/* ── KPI Cards ── */}
      {data && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <KpiCard
            label="Totale Schede"
            value={kpi.total}
            icon={<ClipboardList className="h-4 w-4" />}
            gradient="from-teal-50 to-teal-100 dark:from-teal-950/30 dark:to-teal-900/20"
            border="border-teal-200 dark:border-teal-800"
          />
          <KpiCard
            label="Assegnate"
            value={kpi.withClient}
            icon={<Users className="h-4 w-4" />}
            gradient="from-blue-50 to-blue-100 dark:from-blue-950/30 dark:to-blue-900/20"
            border="border-blue-200 dark:border-blue-800"
          />
          <div className="rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-amber-100 p-4 dark:border-amber-800 dark:from-amber-950/30 dark:to-amber-900/20">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Target className="h-4 w-4" />
              Per Obiettivo
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(kpi.byObiettivo).map(([ob, count]) => (
                <Badge key={ob} variant="outline" className="text-xs">
                  {OBIETTIVO_LABELS[ob] ?? ob}: {count}
                </Badge>
              ))}
              {Object.keys(kpi.byObiettivo).length === 0 && (
                <span className="text-xs text-muted-foreground">—</span>
              )}
            </div>
          </div>
          <div className="rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 to-violet-100 p-4 dark:border-violet-800 dark:from-violet-950/30 dark:to-violet-900/20">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <TrendingUp className="h-4 w-4" />
              Per Livello
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(kpi.byLivello).map(([lv, count]) => (
                <Badge key={lv} variant="outline" className="text-xs">
                  {LIVELLO_LABELS[lv] ?? lv}: {count}
                </Badge>
              ))}
              {Object.keys(kpi.byLivello).length === 0 && (
                <span className="text-xs text-muted-foreground">—</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Filter Bar ── */}
      <div className="flex flex-wrap gap-2">
        <Select value={filters.obiettivo ?? NONE_VALUE} onValueChange={(v) => updateFilter("obiettivo", v)}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Obiettivo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE_VALUE}>Tutti</SelectItem>
            {OBIETTIVI_SCHEDA.map((o) => (
              <SelectItem key={o} value={o}>{OBIETTIVO_LABELS[o] ?? o}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filters.livello ?? NONE_VALUE} onValueChange={(v) => updateFilter("livello", v)}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Livello" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE_VALUE}>Tutti</SelectItem>
            {LIVELLI_SCHEDA.map((l) => (
              <SelectItem key={l} value={l}>{LIVELLO_LABELS[l] ?? l}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(filters.obiettivo || filters.livello) && (
          <Button variant="ghost" size="sm" onClick={() => setFilters({})} className="text-muted-foreground">
            Rimuovi filtri
          </Button>
        )}
      </div>

      {/* ── Content ── */}
      {isLoading && <TableSkeleton />}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">Errore nel caricamento delle schede.</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Riprova
          </Button>
        </div>
      )}

      {data && workouts.length === 0 && (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/40" />
          <p className="mt-4 text-lg font-medium">Nessuna scheda</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Crea la tua prima scheda allenamento partendo da un template.
          </p>
          <Button className="mt-4" onClick={() => setTemplateSelectorOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nuova Scheda
          </Button>
        </div>
      )}

      {data && workouts.length > 0 && (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead className="hidden sm:table-cell">Cliente</TableHead>
                <TableHead>Obiettivo</TableHead>
                <TableHead className="hidden md:table-cell">Livello</TableHead>
                <TableHead className="hidden lg:table-cell text-center">Sessioni</TableHead>
                <TableHead className="hidden lg:table-cell">Data</TableHead>
                <TableHead className="w-[80px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {workouts.map((plan) => (
                <TableRow
                  key={plan.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => router.push(`/schede/${plan.id}`)}
                >
                  <TableCell className="font-medium">{plan.nome}</TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">
                    {plan.client_nome && plan.client_cognome
                      ? `${plan.client_nome} ${plan.client_cognome}`
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <Badge className={`text-xs ${OBIETTIVO_COLORS[plan.obiettivo] ?? ""}`}>
                      {OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    <Badge variant="outline" className={`text-xs ${LIVELLO_COLORS[plan.livello] ?? ""}`}>
                      {LIVELLO_LABELS[plan.livello] ?? plan.livello}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden lg:table-cell text-center tabular-nums">
                    {plan.sessioni.length}
                  </TableCell>
                  <TableCell className="hidden lg:table-cell text-muted-foreground text-sm">
                    {plan.created_at ? new Date(plan.created_at).toLocaleDateString("it-IT") : "—"}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        onClick={() => handleDuplicate(plan)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(plan)}
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

      {/* ── Template Selector ── */}
      <TemplateSelector
        open={templateSelectorOpen}
        onOpenChange={setTemplateSelectorOpen}
      />

      {/* ── Delete Confirm ── */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare la scheda?</AlertDialogTitle>
            <AlertDialogDescription>
              La scheda &ldquo;{deleteTarget?.nome}&rdquo; verra' eliminata. Questa azione non e' reversibile.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SHARED UI
// ════════════════════════════════════════════════════════════

function KpiCard({
  label, value, icon, gradient, border,
}: {
  label: string; value: number; icon: React.ReactNode; gradient: string; border: string;
}) {
  return (
    <div className={`rounded-xl border ${border} bg-gradient-to-br ${gradient} p-4`}>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">{icon}{label}</div>
      <p className="mt-1 text-2xl font-extrabold tracking-tighter tabular-nums">{value}</p>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}
