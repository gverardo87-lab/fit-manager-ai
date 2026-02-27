// src/components/workouts/SortableExerciseRow.tsx
"use client";

/**
 * Singola riga esercizio sortabile dentro una SessionCard.
 *
 * Due layout:
 * - compact=false (default): grid completo con serie/rip/riposo inputs
 * - compact=true: riga semplificata per avviamento/stretching (nome + rip + delete)
 *
 * Safety: icona cliccabile apre Popover ricco con condizioni dettagliate.
 */

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, ShieldAlert, AlertTriangle } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";

import type { WorkoutExerciseRow, ExerciseSafetyEntry } from "@/types/api";

interface SortableExerciseRowProps {
  exercise: WorkoutExerciseRow;
  /** Layout compatto per avviamento/stretching */
  compact?: boolean;
  /** Safety entry da anamnesi cliente (informativo) */
  safety?: ExerciseSafetyEntry;
  onUpdate: (updates: Partial<WorkoutExerciseRow>) => void;
  onDelete: () => void;
  onReplace: () => void;
}

function SafetyPopover({
  safety,
  exerciseName,
  iconSize,
}: {
  safety: ExerciseSafetyEntry;
  exerciseName: string;
  iconSize: string;
}) {
  const SafetyIcon = safety.severity === "avoid" ? ShieldAlert : AlertTriangle;
  const dotColor = safety.severity === "avoid" ? "bg-red-500" : "bg-amber-500";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className={`shrink-0 ${safety.severity === "avoid" ? "text-red-500" : "text-amber-500"} hover:scale-110 transition-transform`}
        >
          <SafetyIcon className={iconSize} />
        </button>
      </PopoverTrigger>
      <PopoverContent side="right" align="start" className="w-72 p-0">
        {/* Header */}
        <div className="px-3 py-2.5">
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full shrink-0 ${dotColor}`} />
            <span className="text-sm font-semibold truncate">{exerciseName}</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 ml-4">
            {safety.conditions.length} condizion{safety.conditions.length === 1 ? "e rilevante" : "i rilevanti"}
          </p>
        </div>
        <Separator />
        {/* Conditions list */}
        <div className="px-3 py-2 space-y-2.5">
          {safety.conditions.map((cond) => (
            <div key={cond.id}>
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] font-semibold uppercase tracking-wider ${cond.severita === "avoid" ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"}`}>
                  {cond.severita === "avoid" ? "Evitare" : "Cautela"}
                </span>
              </div>
              <p className="text-xs font-medium mt-0.5">{cond.nome}</p>
              {cond.nota && (
                <p className="text-[11px] text-muted-foreground leading-relaxed mt-0.5">{cond.nota}</p>
              )}
            </div>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

export function SortableExerciseRow({
  exercise,
  compact = false,
  safety,
  onUpdate,
  onDelete,
  onReplace,
}: SortableExerciseRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: exercise.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  if (compact) {
    return (
      <div
        ref={setNodeRef}
        style={style}
        className="grid grid-cols-[24px_1fr_60px_70px_32px] gap-2 items-center rounded-md px-1 py-1 hover:bg-muted/40 transition-colors"
      >
        {/* Drag handle */}
        <button
          {...attributes}
          {...listeners}
          className="flex items-center justify-center cursor-grab active:cursor-grabbing text-muted-foreground/50 hover:text-muted-foreground"
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>

        {/* Nome esercizio + safety icon */}
        <div className="flex items-center gap-1 min-w-0">
          {safety && (
            <SafetyPopover safety={safety} exerciseName={exercise.esercizio_nome} iconSize="h-3 w-3" />
          )}
          <button
            onClick={onReplace}
            className="text-left text-xs truncate hover:text-primary transition-colors"
            title={`${exercise.esercizio_nome} — clicca per sostituire`}
          >
            {exercise.esercizio_nome}
          </button>
        </div>

        {/* Serie */}
        <Input
          type="number"
          value={exercise.serie}
          onChange={(e) => onUpdate({ serie: parseInt(e.target.value) || 1 })}
          min={1}
          max={10}
          className="h-6 text-center text-xs px-1"
        />

        {/* Ripetizioni */}
        <Input
          value={exercise.ripetizioni}
          onChange={(e) => onUpdate({ ripetizioni: e.target.value })}
          className="h-6 text-center text-xs px-1"
          placeholder="30s"
        />

        {/* Delete */}
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground/50 hover:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="grid grid-cols-[24px_1fr_60px_70px_60px_32px] gap-2 items-center rounded-md px-1 py-1.5 hover:bg-muted/40 transition-colors"
    >
      {/* Drag handle */}
      <button
        {...attributes}
        {...listeners}
        className="flex items-center justify-center cursor-grab active:cursor-grabbing text-muted-foreground/50 hover:text-muted-foreground"
      >
        <GripVertical className="h-4 w-4" />
      </button>

      {/* Nome esercizio + safety icon */}
      <div className="flex items-center gap-1 min-w-0">
        {safety && (
          <SafetyPopover safety={safety} exerciseName={exercise.esercizio_nome} iconSize="h-3.5 w-3.5" />
        )}
        <button
          onClick={onReplace}
          className="text-left text-sm truncate hover:text-primary transition-colors"
          title={`${exercise.esercizio_nome} — clicca per sostituire`}
        >
          {exercise.esercizio_nome}
        </button>
      </div>

      {/* Serie */}
      <Input
        type="number"
        value={exercise.serie}
        onChange={(e) => onUpdate({ serie: parseInt(e.target.value) || 1 })}
        min={1}
        max={10}
        className="h-7 text-center text-xs px-1"
      />

      {/* Ripetizioni */}
      <Input
        value={exercise.ripetizioni}
        onChange={(e) => onUpdate({ ripetizioni: e.target.value })}
        className="h-7 text-center text-xs px-1"
        placeholder="8-12"
      />

      {/* Tempo riposo */}
      <Input
        type="number"
        value={exercise.tempo_riposo_sec}
        onChange={(e) => onUpdate({ tempo_riposo_sec: parseInt(e.target.value) || 0 })}
        min={0}
        max={300}
        step={15}
        className="h-7 text-center text-xs px-1"
      />

      {/* Delete */}
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-muted-foreground/50 hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
