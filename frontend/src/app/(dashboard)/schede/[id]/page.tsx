// src/app/(dashboard)/schede/[id]/page.tsx
"use client";

/**
 * Pagina builder/editor scheda allenamento — orchestratore.
 * Compone i sotto-componenti e i custom hook estratti.
 */

import { use, useState, useCallback, useMemo, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { SessionCard, type SessionCardData } from "@/components/workouts/SessionCard";
import { ExerciseSelector } from "@/components/workouts/ExerciseSelector";
import { ScientificAnalysisTab } from "@/components/workouts/ScientificAnalysisTab";
import { BuilderHeader } from "@/components/workouts/BuilderHeader";
import { BuilderSafetyCard } from "@/components/workouts/BuilderSafetyCard";
import { BuilderSaveBar } from "@/components/workouts/BuilderSaveBar";

import { useWorkout, useUpdateWorkout, useUpdateWorkoutSessions } from "@/hooks/useWorkouts";
import { useClients } from "@/hooks/useClients";
import { useExercises, useExerciseSafetyMap } from "@/hooks/useExercises";
import { useLatestMeasurement } from "@/hooks/useMeasurements";
import { useBuilderState } from "@/hooks/useBuilderState";
import { useBuilderHandlers } from "@/hooks/useBuilderHandlers";

import { PATTERN_TO_1RM } from "@/lib/derived-metrics";
import { CATEGORY_ORDER } from "@/lib/builder-utils";
import { SECTION_CATEGORIES } from "@/lib/workout-templates";
import { resolveBackNavigation } from "@/lib/url-state";
import type { SafetyConditionDetail } from "@/types/api";
import type { SafetyExportData } from "@/lib/export-workout-pdf";

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export default function SchedaDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: idStr } = use(params);
  const fromParam = useSearchParams().get("from");
  const id = parseInt(idStr, 10);
  const router = useRouter();

  // ── Data hooks ──
  const { data: plan, isLoading, isError } = useWorkout(isNaN(id) ? null : id);
  const updateWorkout = useUpdateWorkout();
  const updateSessions = useUpdateWorkoutSessions();
  const { data: clientsData } = useClients();
  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);
  const exerciseData = useExercises();
  const allExercises = useMemo(() => exerciseData.data?.items ?? [], [exerciseData.data]);
  const exerciseMap = useMemo(() => new Map(allExercises.map((e) => [e.id, e])), [allExercises]);
  const { data: safetyMap } = useExerciseSafetyMap(plan?.id_cliente ?? null);
  const safetyEntries = safetyMap?.entries;

  // Client demographics
  const planClienteId = plan?.id_cliente ?? null;
  const assignedClient = useMemo(() => (planClienteId ? clients.find((c) => c.id === planClienteId) : undefined), [clients, planClienteId]);
  const clientSesso = useMemo(() => { const s = assignedClient?.sesso; return s === "Uomo" ? "M" : s === "Donna" ? "F" : null; }, [assignedClient?.sesso]);
  const clientDataNascita = assignedClient?.data_nascita ?? null;
  const clientNome = plan?.client_nome && plan?.client_cognome ? `${plan.client_nome} ${plan.client_cognome}` : undefined;

  // 1RM measurements
  const { data: latestMeasurement } = useLatestMeasurement(plan?.id_cliente ?? null);
  const oneRMByPattern = useMemo(() => {
    if (!latestMeasurement) return null;
    const map: Record<string, number> = {};
    for (const [pattern, metricId] of Object.entries(PATTERN_TO_1RM)) {
      const val = latestMeasurement.valori.find((v) => v.id_metrica === metricId);
      if (val) map[pattern] = val.valore;
    }
    return Object.keys(map).length > 0 ? map : null;
  }, [latestMeasurement]);

  // ── Builder state (sessions, history, save, shortcuts) ──
  const builder = useBuilderState({
    id, plan, exerciseMap, oneRMByPattern,
    updateSessionsMutate: (vars, opts) => updateSessions.mutate(vars, opts),
    isSaving: updateSessions.isPending,
  });

  // ── Builder handlers (session/exercise/block CRUD + selector) ──
  const handlers = useBuilderHandlers({
    applySessionsChange: builder.applySessionsChange,
    sessions: builder.sessions,
    exerciseMap,
    obiettivo: plan?.obiettivo ?? "generale",
  });

  // ── Navigation ──
  const isDirtyRef = builder.isDirtyRef;
  const goBack = useCallback(() => {
    if (isDirtyRef.current && !window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    const nav = resolveBackNavigation(fromParam, { href: "/schede", label: "" }, { tab: "schede" });
    router.push(nav.href);
  // eslint-disable-next-line react-hooks/exhaustive-deps -- isDirtyRef is a stable ref
  }, [router, fromParam]);

  const guardedNavigate = useCallback((href: string) => {
    if (isDirtyRef.current && !window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    router.push(href);
  // eslint-disable-next-line react-hooks/exhaustive-deps -- isDirtyRef is a stable ref
  }, [router]);

  // ── View state ──
  const [activeView, setActiveView] = useState<"sessioni" | "analisi">("sessioni");
  const [showAdvanced, setShowAdvanced] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem("fitmanager.builder.showAdvanced") === "1";
  });
  useEffect(() => {
    window.localStorage.setItem("fitmanager.builder.showAdvanced", showAdvanced ? "1" : "0");
  }, [showAdvanced]);

  // If advanced is toggled off while on analisi, reset view
  const effectiveView = !showAdvanced && activeView === "analisi" ? "sessioni" : activeView;

  // ── Safety computed data (for SafetyCard + ExportButtons) ──
  const { safetyStats, safetyConditionStats, groupedConditions, uniqueConditionsForMap } = useSafetyData(safetyEntries, safetyMap?.condition_count ?? 0, builder.sessions);
  const safetyExportData = useSafetyExportData(safetyMap, safetyEntries, builder.sessions);

  // ── Used exercise IDs (for "In scheda" badge) ──
  const usedExerciseIds = useMemo(() => {
    const ids = new Set<number>();
    for (const s of builder.sessions) {
      for (const e of s.esercizi) ids.add(e.id_esercizio);
      for (const b of s.blocchi) { for (const e of b.esercizi) ids.add(e.id_esercizio); }
    }
    return ids;
  }, [builder.sessions]);

  // ── Loading / Error ──
  if (isLoading) {
    return (<div className="space-y-6"><Skeleton className="h-10 w-64" /><div className="grid gap-6 lg:grid-cols-2"><Skeleton className="h-96" /><Skeleton className="h-96" /></div></div>);
  }
  if (isError || !plan) {
    return (<div className="flex flex-col items-center justify-center py-20"><p className="text-destructive">Scheda non trovata.</p><Button variant="outline" className="mt-4" onClick={() => router.push("/schede")}>Torna alle schede</Button></div>);
  }

  return (
    <div className="space-y-6">
      <BuilderHeader
        plan={plan} clients={clients} clientNome={clientNome} totalVolume={builder.totalVolume}
        isDirty={builder.isDirty} isSaving={updateSessions.isPending} lastSavedLabel={builder.lastSavedLabel}
        canUndo={builder.canUndo} canRedo={builder.canRedo} sessions={builder.sessions}
        safetyExportData={safetyExportData} exportLogoDataUrl={builder.exportLogoDataUrl} fromParam={fromParam}
        onUndo={builder.handleUndo} onRedo={builder.handleRedo} onSave={builder.handleSave}
        onGoBack={goBack} onNavigate={guardedNavigate}
        onUpdatePlan={(updates) => updateWorkout.mutate({ id: plan.id, ...updates })}
        onLogoChange={builder.handleLogoChange}
        showAdvanced={showAdvanced} onToggleAdvanced={() => setShowAdvanced((v) => !v)} hasSessions={builder.sessions.length > 0}
      />

      <div className="space-y-3">
          {safetyMap && safetyMap.condition_count > 0 && (
            <BuilderSafetyCard safetyMap={safetyMap} safetyStats={safetyStats} safetyConditionStats={safetyConditionStats} groupedConditions={groupedConditions} uniqueConditionsForMap={uniqueConditionsForMap} clientId={plan.id_cliente} onNavigateToClient={(cid) => guardedNavigate(`/clienti/${cid}`)} />
          )}

          {builder.sessions.length > 0 && showAdvanced && (
            <div className="flex items-center gap-1 rounded-xl bg-muted/40 p-1 ring-1 ring-border/30">
              {(["sessioni", "analisi"] as const).map((tab) => (
                <button key={tab} type="button" onClick={() => setActiveView(tab)} className={`flex-1 text-xs font-semibold py-1.5 px-4 rounded-lg transition-all duration-200 ${activeView === tab ? "bg-background shadow-sm text-foreground ring-1 ring-border/50" : "text-muted-foreground/70 hover:text-foreground hover:bg-background/50"}`}>
                  {tab === "sessioni" ? "Sessioni" : "Analisi Scientifica"}
                </button>
              ))}
            </div>
          )}

          {effectiveView === "sessioni" && (
            <>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {builder.sessions.map((session) => (
                  <div key={session.id} className="min-w-[340px] max-w-[460px] flex-1">
                    <SessionCard session={session} boardView safetyMap={safetyEntries} exerciseMap={exerciseMap} schedaId={id} parentFrom={fromParam} oneRMByPattern={oneRMByPattern}
                      onUpdateSession={handlers.handleUpdateSession} onDeleteSession={handlers.handleDeleteSession} onDuplicateSession={handlers.handleDuplicateSession}
                      onAddExercise={handlers.handleAddExercise} onUpdateExercise={handlers.handleUpdateExercise} onDeleteExercise={handlers.handleDeleteExercise}
                      onReplaceExercise={handlers.handleReplaceExercise} onQuickReplace={handlers.handleQuickReplace}
                      onAddBlock={handlers.handleAddBlock} onUpdateBlock={handlers.handleUpdateBlock} onDeleteBlock={handlers.handleDeleteBlock} onDuplicateBlock={handlers.handleDuplicateBlock}
                      onAddExerciseToBlock={handlers.handleAddExerciseToBlock} onUpdateExerciseInBlock={handlers.handleUpdateExerciseInBlock}
                      onDeleteExerciseFromBlock={handlers.handleDeleteExerciseFromBlock} onReplaceExerciseInBlock={handlers.handleReplaceExerciseInBlock}
                      onQuickReplaceInBlock={handlers.handleQuickReplaceInBlock} onClearSection={handlers.handleClearSection}
                    />
                  </div>
                ))}
              </div>
              {/* Add session — dashed placeholder card (Trello-style) */}
              <div className="min-w-[340px] max-w-[460px]">
                <button
                  onClick={handlers.handleAddSession}
                  className="w-full rounded-xl border-2 border-dashed border-muted-foreground/15 bg-muted/20 py-10 flex flex-col items-center gap-2.5 text-muted-foreground/60 hover:border-primary/30 hover:bg-primary/[0.03] hover:text-primary transition-all duration-300 group"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-muted/60 group-hover:bg-primary/10 group-hover:ring-1 group-hover:ring-primary/20 transition-all duration-300">
                    <Plus className="h-5 w-5" />
                  </div>
                  <span className="text-sm font-medium tracking-tight">Aggiungi Sessione</span>
                </button>
              </div>
            </>
          )}

          {effectiveView === "analisi" && builder.sessions.length > 0 && (
            <ScientificAnalysisTab
              sessions={builder.sessions.map((s) => ({ nome_sessione: s.nome_sessione, esercizi: s.esercizi.map((e) => ({ id_esercizio: e.id_esercizio, serie: e.serie, carico_kg: e.carico_kg })) }))}
              exerciseMap={exerciseMap} livello={plan.livello} obiettivo={plan.obiettivo}
              sessioniPerSettimana={plan.sessioni_per_settimana} safetyMap={safetyEntries ?? null}
              clientSesso={clientSesso} clientDataNascita={clientDataNascita}
            />
          )}
      </div>

      <ExerciseSelector open={handlers.selectorOpen} onOpenChange={handlers.setSelectorOpen} onSelect={handlers.handleExerciseSelected}
        categoryFilter={handlers.selectorContext?.sezione ? SECTION_CATEGORIES[handlers.selectorContext.sezione] : undefined}
        safetyMap={safetyEntries} schedaId={id} usedExerciseIds={usedExerciseIds}
        feasibilityDetails={builder.smartPlanPackage?.feasibility_details}
      />

      <BuilderSaveBar isDirty={builder.isDirty} isSaving={updateSessions.isPending} lastSavedLabel={builder.lastSavedLabel} saveIssues={builder.saveIssues}
        canUndo={builder.canUndo} canRedo={builder.canRedo}
        onSave={builder.handleSave} onUndo={builder.handleUndo} onRedo={builder.handleRedo} onClearIssues={() => {}}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// LOCAL HOOKS — Safety computed data
// ════════════════════════════════════════════════════════════

type SafetyEntries = Record<string, { severity: string; conditions: SafetyConditionDetail[] }>;
interface GroupedCondition { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }

function useSafetyData(safetyEntries: SafetyEntries | undefined, conditionCount: number, sessions: SessionCardData[]) {
  const safetyStats = useMemo(() => {
    if (!safetyEntries) return { avoid: 0, caution: 0, modify: 0, total: 0 };
    const exerciseIds = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) exerciseIds.add(e.id_esercizio);
      for (const b of s.blocchi) { for (const e of b.esercizi) exerciseIds.add(e.id_esercizio); }
    }
    let avoid = 0, caution = 0, modify = 0;
    for (const [exId, entry] of Object.entries(safetyEntries)) {
      if (!exerciseIds.has(Number(exId))) continue;
      if (entry.severity === "avoid") avoid++; else if (entry.severity === "caution") caution++; else modify++;
    }
    return { avoid, caution, modify, total: avoid + caution + modify };
  }, [safetyEntries, sessions]);

  const safetyConditionStats = useMemo(() => {
    if (!safetyEntries) return { detected: conditionCount, mapped: 0, bodyTagged: 0, planImpacted: 0 };
    const planExIds = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) planExIds.add(e.id_esercizio);
      for (const b of s.blocchi) { for (const e of b.esercizi) planExIds.add(e.id_esercizio); }
    }
    const mapped = new Set<number>(), bodyTagged = new Set<number>(), planImpacted = new Set<number>();
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      for (const c of entry.conditions) {
        mapped.add(c.id);
        if (c.body_tags.length > 0) bodyTagged.add(c.id);
        if (planExIds.has(Number(exIdStr))) planImpacted.add(c.id);
      }
    }
    return { detected: conditionCount, mapped: mapped.size, bodyTagged: bodyTagged.size, planImpacted: planImpacted.size };
  }, [safetyEntries, conditionCount, sessions]);

  const groupedConditions = useMemo(() => {
    if (!safetyEntries) return new Map<string, GroupedCondition[]>();
    const exNameMap = new Map<number, string>();
    for (const s of sessions) {
      for (const ex of s.esercizi) exNameMap.set(ex.id_esercizio, ex.esercizio_nome);
      for (const b of s.blocchi) { for (const ex of b.esercizi) exNameMap.set(ex.id_esercizio, ex.esercizio_nome); }
    }
    const condMap = new Map<number, SafetyConditionDetail & { worstSeverity: string; exercises: Map<number, { nome: string; severity: string }> }>();
    const sevRank: Record<string, number> = { avoid: 2, modify: 1, caution: 0 };
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      const exId = Number(exIdStr), exName = exNameMap.get(exId);
      if (!exName) continue;
      for (const cond of entry.conditions) {
        const existing = condMap.get(cond.id);
        if (!existing) {
          const exercises = new Map<number, { nome: string; severity: string }>();
          exercises.set(exId, { nome: exName, severity: cond.severita });
          condMap.set(cond.id, { ...cond, worstSeverity: cond.severita, exercises });
        } else {
          if ((sevRank[cond.severita] ?? 0) > (sevRank[existing.worstSeverity] ?? 0)) existing.worstSeverity = cond.severita;
          existing.exercises.set(exId, { nome: exName, severity: cond.severita });
        }
      }
    }
    const groups = new Map<string, GroupedCondition[]>();
    for (const cond of condMap.values()) {
      if (!groups.has(cond.categoria)) groups.set(cond.categoria, []);
      groups.get(cond.categoria)!.push({ nome: cond.nome, worstSeverity: cond.worstSeverity, exercises: Array.from(cond.exercises.values()) });
    }
    const sorted = new Map<string, GroupedCondition[]>();
    for (const cat of CATEGORY_ORDER) { if (groups.has(cat)) sorted.set(cat, groups.get(cat)!); }
    return sorted;
  }, [safetyEntries, sessions]);

  const uniqueConditionsForMap = useMemo(() => {
    if (!safetyEntries) return [];
    const seen = new Map<number, SafetyConditionDetail>();
    const sevRank: Record<string, number> = { avoid: 2, modify: 1, caution: 0 };
    for (const entry of Object.values(safetyEntries)) {
      for (const c of entry.conditions) {
        const ex = seen.get(c.id);
        if (!ex || (sevRank[c.severita] ?? 0) > (sevRank[ex.severita] ?? 0)) seen.set(c.id, c);
      }
    }
    return Array.from(seen.values()).filter((c) => c.body_tags.length > 0);
  }, [safetyEntries]);

  return { safetyStats, safetyConditionStats, groupedConditions, uniqueConditionsForMap };
}

function useSafetyExportData(
  safetyMap: { client_nome: string; condition_names: string[]; condition_count: number } | undefined,
  safetyEntries: SafetyEntries | undefined,
  sessions: SessionCardData[],
): SafetyExportData | undefined {
  return useMemo(() => {
    if (!safetyMap || !safetyEntries || safetyMap.condition_count === 0) return undefined;
    const exNameMap = new Map<number, string>();
    for (const s of sessions) {
      for (const ex of s.esercizi) exNameMap.set(ex.id_esercizio, ex.esercizio_nome);
      for (const b of s.blocchi) { for (const ex of b.esercizi) exNameMap.set(ex.id_esercizio, ex.esercizio_nome); }
    }
    const condMap = new Map<number, { nome: string; severita: string; esercizi: Set<string> }>();
    const sevRank: Record<string, number> = { avoid: 2, modify: 1, caution: 0 };
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      const exName = exNameMap.get(Number(exIdStr));
      if (!exName) continue;
      for (const cond of entry.conditions) {
        const existing = condMap.get(cond.id);
        if (!existing) { condMap.set(cond.id, { nome: cond.nome, severita: cond.severita, esercizi: new Set([exName]) }); }
        else { existing.esercizi.add(exName); if ((sevRank[cond.severita] ?? 0) > (sevRank[existing.severita] ?? 0)) existing.severita = cond.severita; }
      }
    }
    return {
      clientNome: safetyMap.client_nome, conditionNames: safetyMap.condition_names,
      rows: Array.from(condMap.values())
        .sort((a, b) => { const order: Record<string, number> = { avoid: 0, caution: 1, modify: 2 }; return (order[a.severita] ?? 3) - (order[b.severita] ?? 3); })
        .map((c) => ({ condizione: c.nome, severita: c.severita, esercizi: Array.from(c.esercizi) })),
    };
  }, [safetyMap, safetyEntries, sessions]);
}
