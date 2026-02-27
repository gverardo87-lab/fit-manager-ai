// src/components/workouts/SortableExerciseRow.tsx
"use client";

/**
 * Singola riga esercizio sortabile dentro una SessionCard.
 *
 * Due layout:
 * - compact=false (default): grid completo con serie/rip/riposo inputs
 * - compact=true: riga semplificata per avviamento/stretching (nome + rip + delete)
 */

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2 } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import type { WorkoutExerciseRow } from "@/types/api";

interface SortableExerciseRowProps {
  exercise: WorkoutExerciseRow;
  /** Layout compatto per avviamento/stretching */
  compact?: boolean;
  onUpdate: (updates: Partial<WorkoutExerciseRow>) => void;
  onDelete: () => void;
  onReplace: () => void;
}

export function SortableExerciseRow({
  exercise,
  compact = false,
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

        {/* Nome esercizio */}
        <button
          onClick={onReplace}
          className="flex items-center gap-1 text-left text-xs truncate hover:text-primary transition-colors"
          title={`${exercise.esercizio_nome} — clicca per sostituire`}
        >
          <span className="truncate">{exercise.esercizio_nome}</span>
        </button>

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

      {/* Nome esercizio (cliccabile per sostituire) */}
      <button
        onClick={onReplace}
        className="flex items-center gap-1 text-left text-sm truncate hover:text-primary transition-colors"
        title={`${exercise.esercizio_nome} — clicca per sostituire`}
      >
        <span className="truncate">{exercise.esercizio_nome}</span>
      </button>

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
