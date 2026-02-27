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
import { Plus, Trash2, Pencil, Flame, Dumbbell, Heart, ShieldAlert, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

import { SortableExerciseRow } from "./SortableExerciseRow";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import type { WorkoutExerciseRow, ExerciseSafetyEntry } from "@/types/api";

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
  onUpdateSession: (sessionId: number, updates: Partial<SessionCardData>) => void;
  onDeleteSession: (sessionId: number) => void;
  onAddExercise: (sessionId: number, sezione?: TemplateSection) => void;
  onUpdateExercise: (sessionId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => void;
  onDeleteExercise: (sessionId: number, exerciseId: number) => void;
  onReplaceExercise: (sessionId: number, exerciseId: number) => void;
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

export function SessionCard({
  session,
  safetyMap,
  onUpdateSession,
  onDeleteSession,
  onAddExercise,
  onUpdateExercise,
  onDeleteExercise,
  onReplaceExercise,
}: SessionCardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState(session.nome_sessione);

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

      // Trova a quale sezione appartengono
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

      // Ricostruisci lista completa: avviamento → principale → stretching
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
      <CardHeader className="flex flex-row items-center gap-3 pb-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-sm font-bold text-primary">
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
              <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-100" />
            </button>
          )}
          {session.focus_muscolare && (
            <p className="text-xs text-muted-foreground truncate">{session.focus_muscolare}</p>
          )}
        </div>
        {/* Safety pills */}
        <div className="flex items-center gap-1.5 shrink-0">
          {sessionSafety.avoid > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-100 dark:bg-red-950/40 px-2 py-0.5 text-[11px] font-medium text-red-700 dark:text-red-400">
              <ShieldAlert className="h-3 w-3" />
              {sessionSafety.avoid}
            </span>
          )}
          {sessionSafety.caution > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 dark:bg-amber-950/40 px-2 py-0.5 text-[11px] font-medium text-amber-700 dark:text-amber-400">
              <AlertTriangle className="h-3 w-3" />
              {sessionSafety.caution}
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-destructive"
          onClick={() => onDeleteSession(session.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </CardHeader>

      <CardContent className="pt-0 space-y-3">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          {SECTION_ORDER.map((sectionKey) => {
            const config = SECTION_CONFIG[sectionKey];
            const exercises = groupedExercises[sectionKey];

            return (
              <div key={sectionKey} className={`border-l-2 ${config.borderColor} pl-3`}>
                {/* Section header */}
                <div className={`flex items-center gap-1.5 mb-1.5 ${config.color}`}>
                  {config.icon}
                  <span className="text-[11px] font-semibold uppercase tracking-wider">
                    {config.label}
                  </span>
                  {exercises.length > 0 && (
                    <span className="text-[10px] text-muted-foreground ml-1">
                      ({exercises.length})
                    </span>
                  )}
                </div>

                {/* Exercise rows */}
                {exercises.length > 0 && (
                  <>
                    {/* Column header solo per principale */}
                    {sectionKey === "principale" && (
                      <div className="grid grid-cols-[24px_1fr_60px_70px_60px_32px] gap-2 px-1 pb-1 text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                        <span />
                        <span>Esercizio</span>
                        <span className="text-center">Serie</span>
                        <span className="text-center">Rip</span>
                        <span className="text-center">Riposo</span>
                        <span />
                      </div>
                    )}

                    <SortableContext
                      items={exercises.map((e) => e.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <div className="space-y-0.5">
                        {exercises.map((exercise) => (
                          <SortableExerciseRow
                            key={exercise.id}
                            exercise={exercise}
                            compact={sectionKey !== "principale"}
                            safety={safetyMap?.[exercise.id_esercizio]}
                            safetyEntries={safetyMap}
                            onUpdate={(updates) => onUpdateExercise(session.id, exercise.id, updates)}
                            onDelete={() => onDeleteExercise(session.id, exercise.id)}
                            onReplace={() => onReplaceExercise(session.id, exercise.id)}
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
