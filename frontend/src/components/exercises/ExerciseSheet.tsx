// src/components/exercises/ExerciseSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare esercizi custom.
 * Pattern identico a ClientSheet.
 */

import { useCallback, useRef } from "react";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useCreateExercise, useUpdateExercise } from "@/hooks/useExercises";
import { ExerciseForm } from "./ExerciseForm";
import type { Exercise, ExerciseCreate, ExerciseUpdate } from "@/types/api";

interface ExerciseSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  exercise?: Exercise | null;
}

export function ExerciseSheet({ open, onOpenChange, exercise }: ExerciseSheetProps) {
  const isEdit = !!exercise;
  const createMutation = useCreateExercise();
  const updateMutation = useUpdateExercise();
  const isPending = createMutation.isPending || updateMutation.isPending;

  // Protezione chiusura accidentale
  const dirtyRef = useRef(false);
  const handleDirtyChange = useCallback((d: boolean) => { dirtyRef.current = d; }, []);
  const guardedOpenChange = useCallback((newOpen: boolean) => {
    if (!newOpen && dirtyRef.current) {
      if (!window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    }
    dirtyRef.current = false;
    onOpenChange(newOpen);
  }, [onOpenChange]);

  const handleSubmit = (values: Record<string, unknown>) => {
    if (isEdit) {
      updateMutation.mutate(
        { id: exercise.id, ...values } as unknown as ExerciseUpdate & { id: number },
        { onSuccess: () => { dirtyRef.current = false; onOpenChange(false); } }
      );
    } else {
      createMutation.mutate(values as unknown as ExerciseCreate, {
        onSuccess: () => { dirtyRef.current = false; onOpenChange(false); },
      });
    }
  };

  return (
    <Sheet open={open} onOpenChange={guardedOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>
            {isEdit ? "Modifica Esercizio" : "Nuovo Esercizio"}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <ExerciseForm
            key={exercise?.id ?? "new"}
            exercise={exercise}
            onSubmit={handleSubmit}
            isPending={isPending}
            onDirtyChange={handleDirtyChange}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
