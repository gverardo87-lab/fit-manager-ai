// src/app/(dashboard)/schede/[id]/page.tsx
"use client";

/**
 * Pagina builder/editor scheda allenamento.
 *
 * Layout split: editor a sinistra, preview live a destra (solo desktop).
 * Sessioni con esercizi ordinabili via drag & drop.
 * Salvataggio via full-replace sessioni.
 */

import { use, useState, useCallback, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Save,
  Plus,
  Pencil,
  Check,
  X,
  Shield,
  ShieldAlert,
  AlertTriangle,
  ChevronDown,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { SessionCard, parseAvgReps, type SessionCardData } from "@/components/workouts/SessionCard";
import { ExerciseSelector } from "@/components/workouts/ExerciseSelector";
import { WorkoutPreview } from "@/components/workouts/WorkoutPreview";
import { ExportButtons } from "@/components/workouts/ExportButtons";
import {
  useWorkout,
  useUpdateWorkout,
  useUpdateWorkoutSessions,
} from "@/hooks/useWorkouts";
import { useClients } from "@/hooks/useClients";
import { useExercises, useExerciseSafetyMap } from "@/hooks/useExercises";
import { useLatestMeasurement } from "@/hooks/useMeasurements";
import { PATTERN_TO_1RM } from "@/lib/derived-metrics";
import {
  OBIETTIVI_SCHEDA,
  LIVELLI_SCHEDA,
  type WorkoutExerciseRow,
  type WorkoutSessionInput,
  type Exercise,
  type SafetyConditionDetail,
} from "@/types/api";
import {
  SECTION_CATEGORIES,
  getSectionForCategory,
  getSmartDefaults,
  type TemplateSection,
} from "@/lib/workout-templates";
import { RiskBodyMap } from "@/components/workouts/RiskBodyMap";

// ════════════════════════════════════════════════════════════
// LABELS
// ════════════════════════════════════════════════════════════

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza", ipertrofia: "Ipertrofia", resistenza: "Resistenza",
  dimagrimento: "Dimagrimento", generale: "Generale",
};
const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante", intermedio: "Intermedio", avanzato: "Avanzato",
};

const CONDITION_CATEGORY_LABELS: Record<string, string> = {
  orthopedic: "Ortopedico",
  cardiovascular: "Cardiovascolare",
  metabolic: "Metabolico",
  neurological: "Neurologico",
  respiratory: "Respiratorio",
  special: "Speciale",
};

const CATEGORY_ORDER = ["orthopedic", "cardiovascular", "metabolic", "neurological", "respiratory", "special"];

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function SchedaDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: idStr } = use(params);
  const id = parseInt(idStr, 10);
  const router = useRouter();

  const { data: plan, isLoading, isError } = useWorkout(isNaN(id) ? null : id);
  const updateWorkout = useUpdateWorkout();
  const updateSessions = useUpdateWorkoutSessions();
  const { data: clientsData } = useClients();
  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  // Exercise map per preview
  const exerciseData = useExercises();
  const allExercises = useMemo(() => exerciseData.data?.items ?? [], [exerciseData.data]);
  const exerciseMap = useMemo(
    () => new Map(allExercises.map((e) => [e.id, e])),
    [allExercises],
  );

  // Safety map: anamnesi × condizioni mediche (lazy, solo con cliente assegnato)
  const { data: safetyMap } = useExerciseSafetyMap(plan?.id_cliente ?? null);
  const safetyEntries = safetyMap?.entries;

  // 1RM: ultima misurazione forza cliente (lazy, solo con cliente assegnato)
  const { data: latestMeasurement } = useLatestMeasurement(plan?.id_cliente ?? null);
  const oneRMByPattern = useMemo(() => {
    if (!latestMeasurement) return null;
    const map: Record<string, number> = {};
    for (const [pattern, metricId] of Object.entries(PATTERN_TO_1RM)) {
      const val = latestMeasurement.valori.find(v => v.id_metrica === metricId);
      if (val) map[pattern] = val.valore;
    }
    return Object.keys(map).length > 0 ? map : null;
  }, [latestMeasurement]);

  // Safety overview panel
  const [safetyExpanded, setSafetyExpanded] = useState(false);

  // Local state per editing
  const [sessions, setSessions] = useState<SessionCardData[]>([]);
  const [isDirty, setIsDirty] = useState(false);

  // Header inline editing
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  // Exercise selector
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectorContext, setSelectorContext] = useState<{
    sessionId: number;
    exerciseId?: number;
    sezione?: TemplateSection;
  } | null>(null);

  // Sync server → local
  useEffect(() => {
    if (plan) {
      setSessions(
        plan.sessioni.map((s) => ({
          id: s.id,
          numero_sessione: s.numero_sessione,
          nome_sessione: s.nome_sessione,
          focus_muscolare: s.focus_muscolare,
          durata_minuti: s.durata_minuti,
          note: s.note,
          esercizi: [...s.esercizi],
        })),
      );
      setIsDirty(false);
    }
  }, [plan]);

  // Client name
  const clientNome = plan?.client_nome && plan?.client_cognome
    ? `${plan.client_nome} ${plan.client_cognome}`
    : undefined;

  // Volume totale scheda (solo esercizi principali con carico)
  const totalVolume = useMemo(() => {
    let total = 0;
    for (const session of sessions) {
      for (const ex of session.esercizi) {
        if (getSectionForCategory(ex.esercizio_categoria) !== "principale") continue;
        if (!ex.carico_kg || ex.carico_kg <= 0) continue;
        total += ex.serie * parseAvgReps(ex.ripetizioni) * ex.carico_kg;
      }
    }
    return total > 0 ? Math.round(total) : null;
  }, [sessions]);

  // Safety stats: conteggi avoid/caution sugli esercizi nella scheda corrente
  const safetyStats = useMemo(() => {
    if (!safetyEntries) return { avoid: 0, caution: 0, total: 0 };
    const exerciseIds = new Set(sessions.flatMap((s) => s.esercizi.map((e) => e.id_esercizio)));
    let avoid = 0;
    let caution = 0;
    for (const [exId, entry] of Object.entries(safetyEntries)) {
      if (!exerciseIds.has(Number(exId))) continue;
      if (entry.severity === "avoid") avoid++;
      else caution++;
    }
    return { avoid, caution, total: avoid + caution };
  }, [safetyEntries, sessions]);

  // Condizioni raggruppate per categoria + esercizi coinvolti (per pannello espanso)
  const groupedConditions = useMemo(() => {
    if (!safetyEntries) return new Map<string, { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }[]>();

    // Mappa esercizio_id → nome (dagli esercizi nella scheda corrente)
    const exerciseNameMap = new Map<number, string>();
    for (const s of sessions) {
      for (const ex of s.esercizi) {
        exerciseNameMap.set(ex.id_esercizio, ex.esercizio_nome);
      }
    }

    // Raccolta condizioni uniche con worst severity + esercizi coinvolti
    const condMap = new Map<number, SafetyConditionDetail & { worstSeverity: string; exercises: Map<number, { nome: string; severity: string }> }>();
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      const exId = Number(exIdStr);
      const exName = exerciseNameMap.get(exId);
      if (!exName) continue; // esercizio non nella scheda corrente

      for (const cond of entry.conditions) {
        const existing = condMap.get(cond.id);
        if (!existing) {
          const exercises = new Map<number, { nome: string; severity: string }>();
          exercises.set(exId, { nome: exName, severity: cond.severita });
          condMap.set(cond.id, { ...cond, worstSeverity: cond.severita, exercises });
        } else {
          if (cond.severita === "avoid" && existing.worstSeverity !== "avoid") {
            existing.worstSeverity = "avoid";
          }
          existing.exercises.set(exId, { nome: exName, severity: cond.severita });
        }
      }
    }

    // Raggruppa per categoria
    const groups = new Map<string, { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }[]>();
    for (const cond of condMap.values()) {
      const cat = cond.categoria;
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push({
        nome: cond.nome,
        worstSeverity: cond.worstSeverity,
        exercises: Array.from(cond.exercises.values()),
      });
    }

    // Ordina per CATEGORY_ORDER
    const sorted = new Map<string, { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }[]>();
    for (const cat of CATEGORY_ORDER) {
      if (groups.has(cat)) sorted.set(cat, groups.get(cat)!);
    }
    return sorted;
  }, [safetyEntries, sessions]);

  // Condizioni uniche con body_tags per Risk Body Map
  const uniqueConditionsForMap = useMemo(() => {
    if (!safetyEntries) return [];
    const seen = new Map<number, SafetyConditionDetail>();
    for (const entry of Object.values(safetyEntries)) {
      for (const cond of entry.conditions) {
        if (!seen.has(cond.id)) {
          seen.set(cond.id, cond);
        } else if (cond.severita === "avoid") {
          seen.set(cond.id, cond); // worst severity wins
        }
      }
    }
    return Array.from(seen.values()).filter((c) => c.body_tags.length > 0);
  }, [safetyEntries]);

  // Set di exercise ID gia' usati nella scheda (per badge "In scheda" nel selector)
  const usedExerciseIds = useMemo(() => {
    const ids = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) {
        ids.add(e.id_esercizio);
      }
    }
    return ids;
  }, [sessions]);

  // Guardia modifiche non salvate (chiusura tab / refresh)
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  // Dati safety per export Excel
  const safetyExportData = useMemo(() => {
    if (!safetyMap || !safetyEntries || safetyMap.condition_count === 0) return undefined;

    // Mappa esercizio_id → nome (dalla scheda corrente)
    const exerciseNameMap = new Map<number, string>();
    for (const s of sessions) {
      for (const ex of s.esercizi) {
        exerciseNameMap.set(ex.id_esercizio, ex.esercizio_nome);
      }
    }

    // Condizioni uniche → esercizi coinvolti
    const condMap = new Map<number, { nome: string; severita: string; esercizi: Set<string> }>();
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      const exName = exerciseNameMap.get(Number(exIdStr));
      if (!exName) continue;
      for (const cond of entry.conditions) {
        const existing = condMap.get(cond.id);
        if (!existing) {
          condMap.set(cond.id, { nome: cond.nome, severita: cond.severita, esercizi: new Set([exName]) });
        } else {
          existing.esercizi.add(exName);
          if (cond.severita === "avoid") existing.severita = "avoid";
        }
      }
    }

    return {
      clientNome: safetyMap.client_nome,
      conditionNames: safetyMap.condition_names,
      rows: Array.from(condMap.values())
        .sort((a, b) => (a.severita === "avoid" ? -1 : 1) - (b.severita === "avoid" ? -1 : 1))
        .map((c) => ({ condizione: c.nome, severita: c.severita, esercizi: Array.from(c.esercizi) })),
    };
  }, [safetyMap, safetyEntries, sessions]);

  // ── Handlers sessioni ──

  const handleUpdateSession = useCallback((sessionId: number, updates: Partial<SessionCardData>) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, ...updates } : s)),
    );
    setIsDirty(true);
  }, []);

  const handleDeleteSession = useCallback((sessionId: number) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== sessionId);
      return filtered.map((s, idx) => ({ ...s, numero_sessione: idx + 1 }));
    });
    setIsDirty(true);
  }, []);

  const handleAddSession = useCallback(() => {
    const newId = -(Date.now()); // ID temporaneo negativo
    setSessions((prev) => [
      ...prev,
      {
        id: newId,
        numero_sessione: prev.length + 1,
        nome_sessione: `Sessione ${prev.length + 1}`,
        focus_muscolare: null,
        durata_minuti: 60,
        note: null,
        esercizi: [],
      },
    ]);
    setIsDirty(true);
  }, []);

  const handleDuplicateSession = useCallback((sessionId: number) => {
    const source = sessions.find((s) => s.id === sessionId);
    if (!source) return;
    const now = Date.now();
    setSessions((prev) => [
      ...prev,
      {
        ...source,
        id: -now,
        numero_sessione: prev.length + 1,
        nome_sessione: `${source.nome_sessione} (copia)`,
        esercizi: source.esercizi.map((e, idx) => ({
          ...e,
          id: -(now + idx + 1),
          ordine: idx + 1,
        })),
      },
    ]);
    setIsDirty(true);
  }, [sessions]);

  // ── Handlers esercizi ──

  const handleAddExercise = useCallback((sessionId: number, sezione?: TemplateSection) => {
    setSelectorContext({ sessionId, sezione });
    setSelectorOpen(true);
  }, []);

  const handleReplaceExercise = useCallback((sessionId: number, exerciseId: number) => {
    // Deduce la sezione dall'esercizio che si sta sostituendo
    const session = sessions.find((s) => s.id === sessionId);
    const exercise = session?.esercizi.find((e) => e.id === exerciseId);
    const sezione = exercise ? getSectionForCategory(exercise.esercizio_categoria) : undefined;
    setSelectorContext({ sessionId, exerciseId, sezione });
    setSelectorOpen(true);
  }, [sessions]);

  const handleExerciseSelected = useCallback((exercise: Exercise) => {
    if (!selectorContext) return;

    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== selectorContext.sessionId) return s;

        if (selectorContext.exerciseId) {
          // Replace
          return {
            ...s,
            esercizi: s.esercizi.map((e) =>
              e.id === selectorContext.exerciseId
                ? {
                    ...e,
                    id_esercizio: exercise.id,
                    esercizio_nome: exercise.nome,
                    esercizio_categoria: exercise.categoria,
                    esercizio_attrezzatura: exercise.attrezzatura,
                  }
                : e,
            ),
          };
        } else {
          // Add new — smart defaults basati su obiettivo + esercizio
          const newId = -(Date.now());
          const section = getSectionForCategory(exercise.categoria);
          const defaults = getSmartDefaults(exercise, plan?.obiettivo ?? "generale", section);
          return {
            ...s,
            esercizi: [
              ...s.esercizi,
              {
                id: newId,
                id_esercizio: exercise.id,
                esercizio_nome: exercise.nome,
                esercizio_categoria: exercise.categoria,
                esercizio_attrezzatura: exercise.attrezzatura,
                ordine: s.esercizi.length + 1,
                serie: defaults.serie,
                ripetizioni: defaults.ripetizioni,
                tempo_riposo_sec: defaults.tempo_riposo_sec,
                tempo_esecuzione: null,
                carico_kg: null,
                note: null,
              },
            ],
          };
        }
      }),
    );
    setSelectorContext(null);
    setIsDirty(true);
  }, [selectorContext]);

  const handleUpdateExercise = useCallback(
    (sessionId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                esercizi: s.esercizi.map((e) =>
                  e.id === exerciseId ? { ...e, ...updates } : e,
                ),
              }
            : s,
        ),
      );
      setIsDirty(true);
    },
    [],
  );

  const handleDeleteExercise = useCallback((sessionId: number, exerciseId: number) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              esercizi: s.esercizi
                .filter((e) => e.id !== exerciseId)
                .map((e, idx) => ({ ...e, ordine: idx + 1 })),
            }
          : s,
      ),
    );
    setIsDirty(true);
  }, []);

  const handleQuickReplace = useCallback((sessionId: number, exerciseId: number, newExerciseId: number) => {
    const newEx = exerciseMap.get(newExerciseId);
    if (!newEx) return;
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        return {
          ...s,
          esercizi: s.esercizi.map((e) =>
            e.id === exerciseId
              ? {
                  ...e,
                  id_esercizio: newEx.id,
                  esercizio_nome: newEx.nome,
                  esercizio_categoria: newEx.categoria,
                  esercizio_attrezzatura: newEx.attrezzatura,
                }
              : e,
          ),
        };
      }),
    );
    setIsDirty(true);
  }, [exerciseMap]);

  // ── Save ──

  const handleSave = useCallback(() => {
    if (!plan) return;

    const sessionsInput: WorkoutSessionInput[] = sessions.map((s) => ({
      nome_sessione: s.nome_sessione,
      focus_muscolare: s.focus_muscolare,
      durata_minuti: s.durata_minuti,
      note: s.note,
      esercizi: s.esercizi.map((e) => ({
        id_esercizio: e.id_esercizio,
        ordine: e.ordine,
        serie: e.serie,
        ripetizioni: e.ripetizioni,
        tempo_riposo_sec: e.tempo_riposo_sec,
        tempo_esecuzione: e.tempo_esecuzione,
        carico_kg: e.carico_kg,
        note: e.note,
      })),
    }));

    updateSessions.mutate(
      { id: plan.id, sessions: sessionsInput },
      { onSuccess: () => setIsDirty(false) },
    );
  }, [plan, sessions, updateSessions]);

  // ── Inline metadata editing ──

  const startEdit = useCallback((field: string, value: string) => {
    setEditingField(field);
    setEditValue(value);
  }, []);

  const saveEdit = useCallback(() => {
    if (!plan || !editingField) return;
    const v = editValue.trim();
    if (v && v !== String((plan as unknown as Record<string, unknown>)[editingField] ?? "")) {
      updateWorkout.mutate({ id: plan.id, [editingField]: v });
    }
    setEditingField(null);
  }, [plan, editingField, editValue, updateWorkout]);

  const cancelEdit = useCallback(() => setEditingField(null), []);

  // ── Loading / Error ──

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (isError || !plan) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-destructive">Scheda non trovata.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/schede")}>
          Torna alle schede
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" data-print-hide>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.push("/schede")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            {editingField === "nome" ? (
              <div className="flex items-center gap-1">
                <Input
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                  className="h-8 text-lg font-bold"
                  autoFocus
                />
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={saveEdit}>
                  <Check className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={cancelEdit}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <button
                onClick={() => startEdit("nome", plan.nome)}
                className="flex items-center gap-2 text-xl font-bold tracking-tight hover:text-primary transition-colors"
              >
                {plan.nome}
                <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            )}
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Select
                value={plan.id_cliente ? String(plan.id_cliente) : "__none__"}
                onValueChange={(v) => {
                  const newClientId = v === "__none__" ? null : Number(v);
                  updateWorkout.mutate({ id: plan.id, id_cliente: newClientId });
                }}
              >
                <SelectTrigger size="sm" className="w-[180px] text-xs">
                  <SelectValue placeholder="Assegna cliente" />
                </SelectTrigger>
                <SelectContent position="popper" sideOffset={4}>
                  <SelectItem value="__none__">Nessun cliente</SelectItem>
                  {clients.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.nome} {c.cognome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {plan.id_cliente && clientNome && (
                <Link
                  href={`/clienti/${plan.id_cliente}`}
                  className="text-xs text-primary hover:underline"
                >
                  Vai al profilo
                </Link>
              )}
              <Select
                value={plan.obiettivo}
                onValueChange={(v) => updateWorkout.mutate({ id: plan.id, obiettivo: v })}
              >
                <SelectTrigger className="h-6 w-auto text-xs border-0 bg-transparent p-0 font-medium">
                  <Badge variant="outline" className="text-xs cursor-pointer">
                    {OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}
                  </Badge>
                </SelectTrigger>
                <SelectContent>
                  {OBIETTIVI_SCHEDA.map((o) => (
                    <SelectItem key={o} value={o}>{OBIETTIVO_LABELS[o]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={plan.livello}
                onValueChange={(v) => updateWorkout.mutate({ id: plan.id, livello: v })}
              >
                <SelectTrigger className="h-6 w-auto text-xs border-0 bg-transparent p-0 font-medium">
                  <Badge variant="outline" className="text-xs cursor-pointer">
                    {LIVELLO_LABELS[plan.livello] ?? plan.livello}
                  </Badge>
                </SelectTrigger>
                <SelectContent>
                  {LIVELLI_SCHEDA.map((l) => (
                    <SelectItem key={l} value={l}>{LIVELLO_LABELS[l]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {totalVolume != null && (
                <Badge variant="outline" className="text-xs tabular-nums">
                  Vol. totale: {totalVolume.toLocaleString("it-IT")} kg
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <ExportButtons
            nome={plan.nome}
            obiettivo={plan.obiettivo}
            livello={plan.livello}
            clientNome={clientNome}
            durata_settimane={plan.durata_settimane}
            sessioni_per_settimana={plan.sessioni_per_settimana}
            sessioni={sessions}
            safety={safetyExportData}
          />
          {isDirty && (
            <Button onClick={handleSave} disabled={updateSessions.isPending}>
              <Save className="mr-1.5 h-4 w-4" />
              {updateSessions.isPending ? "Salvataggio..." : "Salva"}
            </Button>
          )}
        </div>
      </div>

      {/* ── Split Layout ── */}
      <div className="grid gap-6 lg:grid-cols-2 print:block">
        {/* Editor (sinistra) */}
        <div className="space-y-3" data-print-hide>
          {/* Safety Overview Panel — dashboard clinica collapsibile */}
          {safetyMap && safetyMap.condition_count > 0 && (
            <Collapsible open={safetyExpanded} onOpenChange={setSafetyExpanded}>
              <Card className={`border-l-4 ${safetyStats.avoid > 0 ? "border-l-red-500" : "border-l-amber-400"} transition-all duration-200`}>
                <CardContent className="p-4 space-y-3">
                  {/* Header — sempre visibile */}
                  <CollapsibleTrigger asChild>
                    <button className="flex items-center justify-between w-full text-left group">
                      <div className="flex items-center gap-2">
                        <Shield className={`h-4.5 w-4.5 ${safetyStats.avoid > 0 ? "text-red-500" : "text-amber-500"}`} />
                        <div>
                          <span className="text-sm font-semibold">Profilo Clinico</span>
                          <span className="text-sm text-muted-foreground"> — {safetyMap.client_nome}</span>
                        </div>
                      </div>
                      <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${safetyExpanded ? "rotate-180" : ""}`} />
                    </button>
                  </CollapsibleTrigger>

                  {/* KPI mini-row */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="rounded-lg bg-muted/50 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums">{safetyMap.condition_count}</div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Condizioni</div>
                    </div>
                    <div className="rounded-lg bg-red-50 dark:bg-red-950/30 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums text-red-600 dark:text-red-400">{safetyStats.avoid}</div>
                      <div className="text-[10px] text-red-600/70 dark:text-red-400/70 uppercase tracking-wider">Evitare</div>
                    </div>
                    <div className="rounded-lg bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums text-amber-600 dark:text-amber-400">{safetyStats.caution}</div>
                      <div className="text-[10px] text-amber-600/70 dark:text-amber-400/70 uppercase tracking-wider">Cautela</div>
                    </div>
                  </div>

                  {/* Badge condizioni */}
                  <div className="flex flex-wrap gap-1.5">
                    {safetyMap.condition_names.map((name) => (
                      <Badge key={name} variant="outline" className="text-[11px] font-normal">
                        {name}
                      </Badge>
                    ))}
                  </div>

                  {/* Pannello espanso — Risk Body Map + condizioni raggruppate */}
                  <CollapsibleContent className="space-y-3">
                    <Separator />
                    {/* Risk Body Map */}
                    {uniqueConditionsForMap.length > 0 && (
                      <div className="flex flex-col items-center">
                        <RiskBodyMap conditions={uniqueConditionsForMap} />
                        <div className="flex items-center gap-3 mt-1">
                          <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
                            <span className="h-2 w-2 rounded-full bg-red-500" /> Evitare
                          </span>
                          <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
                            <span className="h-2 w-2 rounded-full bg-amber-500" /> Cautela
                          </span>
                        </div>
                      </div>
                    )}
                    {Array.from(groupedConditions.entries()).map(([categoria, conditions]) => (
                      <div key={categoria}>
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                          {CONDITION_CATEGORY_LABELS[categoria] ?? categoria}
                        </div>
                        <div className="space-y-2.5">
                          {conditions.map((cond) => (
                            <div key={cond.nome}>
                              <div className="flex items-center gap-2 text-xs">
                                {cond.worstSeverity === "avoid" ? (
                                  <ShieldAlert className="h-3.5 w-3.5 shrink-0 text-red-500" />
                                ) : (
                                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-500" />
                                )}
                                <span className="flex-1 font-medium">{cond.nome}</span>
                                <span className={`text-[10px] font-medium ${cond.worstSeverity === "avoid" ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"}`}>
                                  {cond.worstSeverity === "avoid" ? "Evitare" : "Cautela"}
                                </span>
                              </div>
                              {/* Esercizi coinvolti */}
                              {cond.exercises.length > 0 && (
                                <div className="ml-5.5 mt-1 flex flex-wrap gap-1">
                                  {cond.exercises.map((ex) => (
                                    <span
                                      key={ex.nome}
                                      className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] ${
                                        ex.severity === "avoid"
                                          ? "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400"
                                          : "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                                      }`}
                                    >
                                      {ex.nome}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                    {plan.id_cliente && (
                      <Link
                        href={`/clienti/${plan.id_cliente}`}
                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-1"
                      >
                        Vai al profilo di {safetyMap.client_nome.split(" ")[0]}
                      </Link>
                    )}
                  </CollapsibleContent>
                </CardContent>
              </Card>
            </Collapsible>
          )}

          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              safetyMap={safetyEntries}
              exerciseMap={exerciseMap}
              schedaId={id}
              oneRMByPattern={oneRMByPattern}
              onUpdateSession={handleUpdateSession}
              onDeleteSession={handleDeleteSession}
              onDuplicateSession={handleDuplicateSession}
              onAddExercise={handleAddExercise}
              onUpdateExercise={handleUpdateExercise}
              onDeleteExercise={handleDeleteExercise}
              onReplaceExercise={handleReplaceExercise}
              onQuickReplace={handleQuickReplace}
            />
          ))}

          <Button
            variant="outline"
            className="w-full"
            onClick={handleAddSession}
          >
            <Plus className="mr-2 h-4 w-4" />
            Aggiungi Sessione
          </Button>
        </div>

        {/* Preview (destra, solo desktop + stampa) */}
        <div className="hidden lg:block print:block space-y-4 sticky top-6 workout-preview-container">
          <WorkoutPreview
            nome={plan.nome}
            obiettivo={plan.obiettivo}
            livello={plan.livello}
            clientNome={clientNome}
            durata_settimane={plan.durata_settimane}
            sessioni_per_settimana={plan.sessioni_per_settimana}
            sessioni={sessions}
            note={plan.note}
            exerciseMap={exerciseMap}
          />
        </div>
      </div>

      {/* Exercise Selector Dialog */}
      <ExerciseSelector
        open={selectorOpen}
        onOpenChange={setSelectorOpen}
        onSelect={handleExerciseSelected}
        categoryFilter={
          selectorContext?.sezione
            ? SECTION_CATEGORIES[selectorContext.sezione]
            : undefined
        }
        safetyMap={safetyEntries}
        schedaId={id}
        usedExerciseIds={usedExerciseIds}
      />
    </div>
  );
}
