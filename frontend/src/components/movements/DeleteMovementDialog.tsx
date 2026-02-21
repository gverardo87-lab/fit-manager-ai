// src/components/movements/DeleteMovementDialog.tsx
"use client";

/**
 * Dialog di conferma eliminazione movimento.
 *
 * Solo movimenti manuali arrivano qui (quelli di sistema
 * hanno il bottone Elimina disabilitato nella tabella).
 */

import { Loader2 } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useDeleteMovement } from "@/hooks/useMovements";
import type { CashMovement } from "@/types/api";

interface DeleteMovementDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  movement: CashMovement | null;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

export function DeleteMovementDialog({
  open,
  onOpenChange,
  movement,
}: DeleteMovementDialogProps) {
  const deleteMutation = useDeleteMovement();

  if (!movement) return null;

  const handleConfirm = () => {
    deleteMutation.mutate(movement.id, {
      onSuccess: () => onOpenChange(false),
    });
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Eliminare questo movimento?</AlertDialogTitle>
          <AlertDialogDescription>
            Stai per eliminare il movimento{" "}
            <span className="font-semibold">
              {movement.tipo} di {formatCurrency(movement.importo)}
            </span>
            {movement.note && (
              <>
                {" "}({movement.note})
              </>
            )}
            . Questa azione non puo' essere annullata.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteMutation.isPending}>
            Annulla
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={deleteMutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Elimina
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
