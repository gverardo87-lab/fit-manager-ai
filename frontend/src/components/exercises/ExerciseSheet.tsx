// src/components/exercises/ExerciseSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare esercizi custom.
 * Pattern identico a ClientSheet.
 */

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useCreateExercise, useUpdateExercise } from "@/hooks/useExercises";
import { ExerciseForm, type ExerciseFormValues } from "./ExerciseForm";
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

  const handleSubmit = (values: ExerciseFormValues) => {
    if (isEdit) {
      updateMutation.mutate(
        { id: exercise.id, ...values } as ExerciseUpdate & { id: number },
        { onSuccess: () => onOpenChange(false) }
      );
    } else {
      createMutation.mutate(values as ExerciseCreate, {
        onSuccess: () => onOpenChange(false),
      });
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
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
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
