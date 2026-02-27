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
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { SessionCard, type SessionCardData } from "@/components/workouts/SessionCard";
import { ExerciseSelector } from "@/components/workouts/ExerciseSelector";
import { WorkoutPreview } from "@/components/workouts/WorkoutPreview";
import { ExportButtons } from "@/components/workouts/ExportButtons";
import {
  useWorkout,
  useUpdateWorkout,
  useUpdateWorkoutSessions,
} from "@/hooks/useWorkouts";
import { useClients } from "@/hooks/useClients";
import { useExercises } from "@/hooks/useExercises";
import {
  OBIETTIVI_SCHEDA,
  LIVELLI_SCHEDA,
  type WorkoutExerciseRow,
  type WorkoutSessionInput,
  type Exercise,
} from "@/types/api";
import {
  SECTION_CATEGORIES,
  getSectionForCategory,
  type TemplateSection,
} from "@/lib/workout-templates";

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
          // Add new — defaults basati sulla sezione
          const newId = -(Date.now());
          const section = getSectionForCategory(exercise.categoria);
          const isComplementary = section !== "principale";
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
                serie: isComplementary ? 1 : 3,
                ripetizioni: isComplementary ? "30s" : "8-12",
                tempo_riposo_sec: isComplementary ? 0 : 90,
                tempo_esecuzione: null,
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
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <ExportButtons
            nome={plan.nome}
            obiettivo={plan.obiettivo}
            livello={plan.livello}
            clientNome={clientNome}
            sessioni={sessions}
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
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Editor (sinistra) */}
        <div className="space-y-4" data-print-hide>
          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onUpdateSession={handleUpdateSession}
              onDeleteSession={handleDeleteSession}
              onAddExercise={handleAddExercise}
              onUpdateExercise={handleUpdateExercise}
              onDeleteExercise={handleDeleteExercise}
              onReplaceExercise={handleReplaceExercise}
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

        {/* Preview (destra, solo desktop) */}
        <div className="hidden lg:block space-y-4 sticky top-6">
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
      />
    </div>
  );
}
