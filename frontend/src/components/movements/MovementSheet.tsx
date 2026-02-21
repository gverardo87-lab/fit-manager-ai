// src/components/movements/MovementSheet.tsx
"use client";

/**
 * Sheet per creazione nuovo movimento manuale.
 * Auto-chiusura su successo via onSuccess callback.
 */

import { format } from "date-fns";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { MovementForm, type MovementFormValues } from "./MovementForm";
import { useCreateMovement } from "@/hooks/useMovements";

interface MovementSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MovementSheet({ open, onOpenChange }: MovementSheetProps) {
  const createMutation = useCreateMovement();

  const handleSubmit = (values: MovementFormValues) => {
    createMutation.mutate(
      {
        tipo: values.tipo,
        importo: values.importo,
        categoria: values.categoria ?? null,
        metodo: values.metodo ?? null,
        data_effettiva: format(values.data_effettiva, "yyyy-MM-dd"),
        note: values.note ?? null,
      },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Nuovo Movimento</SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <MovementForm
            onSubmit={handleSubmit}
            isPending={createMutation.isPending}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
