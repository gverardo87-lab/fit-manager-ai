// src/components/movements/DeleteMovementDialog.tsx
"use client";

/**
 * Dialog di conferma eliminazione movimento.
 *
 * Solo movimenti manuali arrivano qui (quelli di sistema
 * hanno il bottone Elimina disabilitato nella tabella).
 */

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

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
import { useDeleteMovement, usePreviewDeleteMovement } from "@/hooks/useMovements";
import type { CashMovement, ImpactPreviewResponse } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface DeleteMovementDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  movement: CashMovement | null;
}

export function DeleteMovementDialog({
  open,
  onOpenChange,
  movement,
}: DeleteMovementDialogProps) {
  const deleteMutation = useDeleteMovement();
  const previewMutation = usePreviewDeleteMovement();
  const [preview, setPreview] = useState<ImpactPreviewResponse | null>(null);

  useEffect(() => {
    if (!open || !movement) {
      setPreview(null);
      return;
    }
    previewMutation.mutate(movement.id, {
      onSuccess: (data) => setPreview(data),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, movement?.id]);

  const handleConfirm = () => {
    if (!movement) return;
    deleteMutation.mutate(movement.id, {
      onSuccess: () => onOpenChange(false),
    });
  };

  if (!movement) return null;

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
            . Questa azione non puo&apos; essere annullata.
          </AlertDialogDescription>
        </AlertDialogHeader>

        {preview && (
          <div className="rounded-md border bg-muted/30 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span>Saldo attuale</span>
              <span className="font-semibold tabular-nums">
                {formatCurrency(preview.saldo_attuale_before)} {"->"} {formatCurrency(preview.saldo_attuale_after)}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between">
              <span>Saldo previsto</span>
              <span className="font-semibold tabular-nums">
                {formatCurrency(preview.saldo_previsto_before)} {"->"} {formatCurrency(preview.saldo_previsto_after)}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between border-t pt-2">
              <span>Delta netto</span>
              <span
                className={`font-bold tabular-nums ${
                  preview.delta_netto >= 0
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {preview.delta_netto >= 0 ? "+" : ""}
                {formatCurrency(preview.delta_netto)}
              </span>
            </div>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteMutation.isPending || previewMutation.isPending}>
            Annulla
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={deleteMutation.isPending || previewMutation.isPending || !preview}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {(deleteMutation.isPending || previewMutation.isPending) && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {previewMutation.isPending ? "Calcolo impatto..." : "Elimina"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
