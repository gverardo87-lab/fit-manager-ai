// src/components/movements/MovementSheet.tsx
"use client";

/**
 * Sheet per creazione nuovo movimento manuale.
 * Auto-chiusura su successo via onSuccess callback (con conferma se dirty).
 */

import { useCallback, useRef, useState } from "react";
import { format } from "date-fns";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
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
import { MovementForm, type MovementFormValues } from "./MovementForm";
import { useCreateMovement, usePreviewCreateMovement } from "@/hooks/useMovements";
import type { MovementManualCreate } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface MovementSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MovementSheet({ open, onOpenChange }: MovementSheetProps) {
  const createMutation = useCreateMovement();
  const previewMutation = usePreviewCreateMovement();
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewData, setPreviewData] = useState<Awaited<ReturnType<typeof previewMutation.mutateAsync>> | null>(null);
  const [pendingPayload, setPendingPayload] = useState<MovementManualCreate | null>(null);

  // Protezione chiusura accidentale
  const dirtyRef = useRef(false);
  const handleDirtyChange = useCallback((d: boolean) => { dirtyRef.current = d; }, []);
  const guardedOpenChange = useCallback((newOpen: boolean) => {
    if (!newOpen && dirtyRef.current) {
      if (!window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    }
    dirtyRef.current = false;
    setPreviewOpen(false);
    setPreviewData(null);
    setPendingPayload(null);
    onOpenChange(newOpen);
  }, [onOpenChange]);

  const buildPayload = (values: MovementFormValues): MovementManualCreate => ({
    tipo: values.tipo,
    importo: values.importo,
    categoria: values.categoria ?? null,
    metodo: values.metodo ?? null,
    data_effettiva: format(values.data_effettiva, "yyyy-MM-dd"),
    note: values.note ?? null,
  });

  const handleSubmit = (values: MovementFormValues) => {
    const payload = buildPayload(values);
    previewMutation.mutate(payload, {
      onSuccess: (data) => {
        setPendingPayload(payload);
        setPreviewData(data);
        setPreviewOpen(true);
      },
    });
  };

  const handleConfirmCreate = () => {
    if (!pendingPayload) return;
    createMutation.mutate(pendingPayload, {
      onSuccess: () => {
        dirtyRef.current = false;
        setPreviewOpen(false);
        setPreviewData(null);
        setPendingPayload(null);
        onOpenChange(false);
      },
    });
  };

  return (
    <>
      <Sheet open={open} onOpenChange={guardedOpenChange}>
        <SheetContent className="overflow-y-auto sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Nuovo Movimento</SheetTitle>
          </SheetHeader>
          <div className="mt-6">
            <MovementForm
              onSubmit={handleSubmit}
              isPending={createMutation.isPending || previewMutation.isPending}
              onDirtyChange={handleDirtyChange}
            />
          </div>
        </SheetContent>
      </Sheet>

      <AlertDialog
        open={previewOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && createMutation.isPending) return;
          setPreviewOpen(nextOpen);
          if (!nextOpen) {
            setPreviewData(null);
            setPendingPayload(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Conferma con anteprima impatto</AlertDialogTitle>
            <AlertDialogDescription>
              Verifica l&apos;effetto sul saldo prima di registrare il movimento.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {previewData && (
            <div className="space-y-2 rounded-md border bg-muted/30 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span>Saldo attuale</span>
                <span className="font-semibold tabular-nums">
                  {formatCurrency(previewData.saldo_attuale_before)} {"->"} {formatCurrency(previewData.saldo_attuale_after)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Saldo previsto</span>
                <span className="font-semibold tabular-nums">
                  {formatCurrency(previewData.saldo_previsto_before)} {"->"} {formatCurrency(previewData.saldo_previsto_after)}
                </span>
              </div>
              <div className="flex items-center justify-between border-t pt-2">
                <span>Delta netto</span>
                <span
                  className={`font-bold tabular-nums ${
                    previewData.delta_netto >= 0
                      ? "text-emerald-600 dark:text-emerald-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {previewData.delta_netto >= 0 ? "+" : ""}
                  {formatCurrency(previewData.delta_netto)}
                </span>
              </div>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel disabled={createMutation.isPending}>
              Annulla
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmCreate}
              disabled={createMutation.isPending || !previewData || !pendingPayload}
            >
              {createMutation.isPending ? "Registrazione..." : "Conferma e registra"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
