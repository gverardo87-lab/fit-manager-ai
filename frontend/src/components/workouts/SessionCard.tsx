// src/components/workouts/SessionCard.tsx
"use client";

/**
 * Card per una singola sessione di allenamento dentro il builder.
 *
 * 3 sezioni visive:
 * - Avviamento (warm-up)
 * - Esercizio Principale (strength)
 * - Stretching & Mobilita (cooldown)
 *
 * Ogni sezione ha drag & drop indipendente e + button dedicato.
 * La sezione viene determinata da esercizio_categoria.
 * Azioni sessione in overflow menu (⋮) per header compatto.
 */

import { useCallback, useMemo, useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Plus, Trash2, Pencil, Flame, Dumbbell, Heart, ShieldAlert, AlertTriangle, Copy, StickyNote, MoreVertical } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { SortableExerciseRow } from "./SortableExerciseRow";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import type { WorkoutExerciseRow, ExerciseSafetyEntry, Exercise } from "@/types/api";

export interface SessionCardData {
  id: number;
  numero_sessione: number;
  nome_sessione: string;
  focus_muscolare: string | null;
  durata_minuti: number;
  note: string | null;
  esercizi: WorkoutExerciseRow[];
}

interface SessionCardProps {
  session: SessionCardData;
  /** Safety map per-esercizio (da anamnesi cliente). Informativo, mai bloccante. */
  safetyMap?: Record<number, ExerciseSafetyEntry>;
  /** Mappa esercizi completi per pannello dettaglio inline */
  exerciseMap?: Map<number, Exercise>;
  /** ID scheda per deep-link ritorno dalla pagina esercizio */
  schedaId?: number;
  /** Mappa pattern_movimento → valore 1RM cliente (per badge % 1RM) */
  oneRMByPattern?: Record<string, number> | null;
  onUpdateSession: (sessionId: number, updates: Partial<SessionCardData>) => void;
  onDeleteSession: (sessionId: number) => void;
  onDuplicateSession?: (sessionId: number) => void;
  onAddExercise: (sessionId: number, sezione?: TemplateSection) => void;
  onUpdateExercise: (sessionId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => void;
  onDeleteExercise: (sessionId: number, exerciseId: number) => void;
  onReplaceExercise: (sessionId: number, exerciseId: number) => void;
  /** Quick-replace: sostituisci esercizio preservando serie/rip/riposo */
  onQuickReplace?: (sessionId: number, exerciseId: number, newExerciseId: number) => void;
}

// ── Sezione config ──

const SECTION_CONFIG: Record<TemplateSection, {
  label: string;
  icon: React.ReactNode;
  addLabel: string;
  color: string;
  borderColor: string;
}> = {
  avviamento: {
    label: "Avviamento",
    icon: <Flame className="h-3.5 w-3.5" />,
    addLabel: "Aggiungi Avviamento",
    color: "text-amber-600 dark:text-amber-400",
    borderColor: "border-l-amber-400",
  },
  principale: {
    label: "Esercizio Principale",
    icon: <Dumbbell className="h-3.5 w-3.5" />,
    addLabel: "Aggiungi Esercizio",
    color: "text-primary",
    borderColor: "border-l-primary",
  },
  stretching: {
    label: "Stretching & Mobilita",
    icon: <Heart className="h-3.5 w-3.5" />,
    addLabel: "Aggiungi Stretching",
    color: "text-cyan-600 dark:text-cyan-400",
    borderColor: "border-l-cyan-400",
  },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

/** Parsa range ripetizioni → media. "8-12" → 10, "5" → 5, "30s" → 0. */
export function parseAvgReps(reps: string): number {
  const range = reps.match(/^(\d+)\s*-\s*(\d+)$/);
  if (range) return (parseInt(range[1]) + parseInt(range[2])) / 2;
  const single = reps.match(/^(\d+)$/);
  if (single) return parseInt(single[1]);
  return 0;
}

export function SessionCard({
  session,
  safetyMap,
  exerciseMap,
  schedaId,
  oneRMByPattern,
  onUpdateSession,
  onDeleteSession,
  onDuplicateSession,
  onAddExercise,
  onUpdateExercise,
  onDeleteExercise,
  onReplaceExercise,
  onQuickReplace,
}: SessionCardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState(session.nome_sessione);
  const [showNotes, setShowNotes] = useState(!!session.note);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  // Raggruppa esercizi per sezione
  const groupedExercises = useMemo(() => {
    const groups: Record<TemplateSection, WorkoutExerciseRow[]> = {
      avviamento: [],
      principale: [],
      stretching: [],
    };
    for (const ex of session.esercizi) {
      const section = getSectionForCategory(ex.esercizio_categoria);
      groups[section].push(ex);
    }
    return groups;
  }, [session.esercizi]);

  // Volume sessione (solo sezione principale, solo se >= 1 esercizio ha carico)
  const sessionVolume = useMemo(() => {
    const principale = groupedExercises.principale;
    const withLoad = principale.filter((e) => e.carico_kg != null && e.carico_kg > 0);
    if (withLoad.length === 0) return null;
    const total = withLoad.reduce((sum, e) => {
      const reps = parseAvgReps(e.ripetizioni);
      return sum + e.serie * reps * (e.carico_kg ?? 0);
    }, 0);
    return Math.round(total);
  }, [groupedExercises.principale]);

  // Safety pills: contatori avoid/caution per questa sessione
  const sessionSafety = useMemo(() => {
    if (!safetyMap) return { avoid: 0, caution: 0 };
    let avoid = 0;
    let caution = 0;
    for (const ex of session.esercizi) {
      const entry = safetyMap[ex.id_esercizio];
      if (!entry) continue;
      if (entry.severity === "avoid") avoid++;
      else caution++;
    }
    return { avoid, caution };
  }, [safetyMap, session.esercizi]);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const activeEx = session.esercizi.find((e) => e.id === active.id);
      const overEx = session.esercizi.find((e) => e.id === over.id);
      if (!activeEx || !overEx) return;

      const activeSection = getSectionForCategory(activeEx.esercizio_categoria);
      const overSection = getSectionForCategory(overEx.esercizio_categoria);

      // Solo riordino dentro la stessa sezione
      if (activeSection !== overSection) return;

      const sectionExs = [...groupedExercises[activeSection]];
      const oldIdx = sectionExs.findIndex((e) => e.id === active.id);
      const newIdx = sectionExs.findIndex((e) => e.id === over.id);
      if (oldIdx === -1 || newIdx === -1) return;

      const reordered = arrayMove(sectionExs, oldIdx, newIdx);

      const fullList = [
        ...(activeSection === "avviamento" ? reordered : groupedExercises.avviamento),
        ...(activeSection === "principale" ? reordered : groupedExercises.principale),
        ...(activeSection === "stretching" ? reordered : groupedExercises.stretching),
      ].map((e, idx) => ({ ...e, ordine: idx + 1 }));

      onUpdateSession(session.id, { esercizi: fullList });
    },
    [session.esercizi, session.id, groupedExercises, onUpdateSession],
  );

  const handleNameSave = useCallback(() => {
    setIsEditingName(false);
    if (editName.trim() && editName !== session.nome_sessione) {
      onUpdateSession(session.id, { nome_sessione: editName.trim() });
    }
  }, [editName, session.id, session.nome_sessione, onUpdateSession]);

  return (
    <Card className="transition-all duration-200 hover:shadow-md">
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary">
          {session.numero_sessione}
        </div>
        <div className="flex-1 min-w-0 group">
          {isEditingName ? (
            <Input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onBlur={handleNameSave}
              onKeyDown={(e) => e.key === "Enter" && handleNameSave()}
              className="h-7 text-sm font-semibold"
              autoFocus
            />
          ) : (
            <button
              onClick={() => { setEditName(session.nome_sessione); setIsEditingName(true); }}
              className="flex items-center gap-1 text-sm font-semibold hover:text-primary transition-colors"
            >
              {session.nome_sessione}
              {/* Dot indicatore note sessione */}
              {session.note && (
                <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
              )}
              <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-100" />
            </button>
          )}
          {session.focus_muscolare && (
            <p className="text-xs text-muted-foreground truncate">{session.focus_muscolare}</p>
          )}
        </div>
        {/* Safety pills */}
        <div className="flex items-center gap-1 shrink-0">
          {sessionSafety.avoid > 0 && (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-red-100 dark:bg-red-950/40 px-1.5 py-0.5 text-[10px] font-medium text-red-700 dark:text-red-400">
              <ShieldAlert className="h-3 w-3" />
              {sessionSafety.avoid}
            </span>
          )}
          {sessionSafety.caution > 0 && (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-amber-100 dark:bg-amber-950/40 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-400">
              <AlertTriangle className="h-3 w-3" />
              {sessionSafety.caution}
            </span>
          )}
        </div>
        {/* Overflow menu (⋮) — note, duplica, elimina */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 text-muted-foreground">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setShowNotes(!showNotes)}>
              <StickyNote className="h-3.5 w-3.5 mr-2" />
              {session.note ? "Modifica note" : "Aggiungi note"}
            </DropdownMenuItem>
            {onDuplicateSession && (
              <DropdownMenuItem onClick={() => onDuplicateSession(session.id)}>
                <Copy className="h-3.5 w-3.5 mr-2" />
                Duplica sessione
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => onDeleteSession(session.id)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5 mr-2" />
              Elimina sessione
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>

      {/* Note sessione espandibili */}
      {showNotes && (
        <div className="px-6 pb-2">
          <Input
            value={session.note ?? ""}
            onChange={(e) => onUpdateSession(session.id, { note: e.target.value || null })}
            placeholder="Note sessione: RPE target, focus, indicazioni generali..."
            className="h-7 text-xs"
            autoFocus={!session.note}
          />
        </div>
      )}

      <CardContent className="pt-0 space-y-2">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          {SECTION_ORDER.map((sectionKey) => {
            const config = SECTION_CONFIG[sectionKey];
            const exercises = groupedExercises[sectionKey];
            const isPrincipale = sectionKey === "principale";

            return (
              <div key={sectionKey} className={`border-l-2 ${config.borderColor} pl-3`}>
                {/* Section header */}
                <div className={`flex items-center gap-1.5 mb-1 ${config.color}`}>
                  {config.icon}
                  <span className="text-[11px] font-semibold uppercase tracking-wider">
                    {config.label}
                  </span>
                  {exercises.length > 0 && (
                    <span className="text-[10px] text-muted-foreground ml-1">
                      ({exercises.length})
                    </span>
                  )}
                  {isPrincipale && sessionVolume != null && (
                    <span className="text-[10px] font-semibold text-muted-foreground ml-auto tabular-nums">
                      Vol: {sessionVolume.toLocaleString("it-IT")} kg
                    </span>
                  )}
                </div>

                {/* Exercise rows */}
                {exercises.length > 0 && (
                  <>
                    {/* Column header — allineato ai nuovi grid */}
                    <div className={`grid ${isPrincipale
                      ? "grid-cols-[20px_14px_1fr_44px_52px_52px_44px_24px]"
                      : "grid-cols-[20px_14px_1fr_44px_52px_24px]"
                    } gap-1 px-1 pb-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wider`}>
                      <span />
                      <span />
                      <span>Esercizio</span>
                      <span className="text-center">Serie</span>
                      <span className="text-center">Rip</span>
                      {isPrincipale && (
                        <>
                          <span className="text-center">Kg</span>
                          <span className="text-center">Riposo</span>
                        </>
                      )}
                      <span />
                    </div>

                    <SortableContext
                      items={exercises.map((e) => e.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <div className="space-y-0.5">
                        {exercises.map((exercise) => (
                          <SortableExerciseRow
                            key={exercise.id}
                            exercise={exercise}
                            compact={!isPrincipale}
                            safety={safetyMap?.[exercise.id_esercizio]}
                            safetyEntries={safetyMap}
                            exerciseData={exerciseMap?.get(exercise.id_esercizio)}
                            schedaId={schedaId}
                            oneRMByPattern={isPrincipale ? oneRMByPattern : undefined}
                            onUpdate={(updates) => onUpdateExercise(session.id, exercise.id, updates)}
                            onDelete={() => onDeleteExercise(session.id, exercise.id)}
                            onReplace={() => onReplaceExercise(session.id, exercise.id)}
                            onQuickReplace={onQuickReplace ? (newId) => onQuickReplace(session.id, exercise.id, newId) : undefined}
                          />
                        ))}
                      </div>
                    </SortableContext>
                  </>
                )}

                {/* Add button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-1 w-full text-xs text-muted-foreground hover:text-primary h-7"
                  onClick={() => onAddExercise(session.id, sectionKey)}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  {config.addLabel}
                </Button>
              </div>
            );
          })}
        </DndContext>
      </CardContent>
    </Card>
  );
}
