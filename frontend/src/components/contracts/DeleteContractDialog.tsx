// src/components/contracts/DeleteContractDialog.tsx
"use client";

/**
 * Dialog di conferma eliminazione contratto.
 *
 * 2 livelli:
 * - Livello 1 (nessun blocco): conferma semplice
 * - Livello 2 (rate pendenti o crediti residui): avviso dettagliato
 *   + checkbox conferma forzata + opzione mantieni pagamenti
 */

import { useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";

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
import { Checkbox } from "@/components/ui/checkbox";
import { useDeleteContract } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import type { Contract } from "@/types/api";

interface DeleteContractDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contract: Contract | null;
  clientName?: string;
  onDeleted?: () => void;
}

export function DeleteContractDialog({
  open,
  onOpenChange,
  contract,
  clientName,
  onDeleted,
}: DeleteContractDialogProps) {
  const deleteMutation = useDeleteContract();
  const [forceConfirmed, setForceConfirmed] = useState(false);
  const [keepPayments, setKeepPayments] = useState(true);

  if (!contract) return null;

  // Rileva condizioni bloccanti dai dati gia' disponibili
  const ratePendenti =
    "rate_totali" in contract && "rate_pagate" in contract
      ? (contract as Contract & { rate_totali: number; rate_pagate: number }).rate_totali -
        (contract as Contract & { rate_totali: number; rate_pagate: number }).rate_pagate
      : 0;
  const importoNonRiscosso = (contract.prezzo_totale ?? 0) - (contract.totale_versato ?? 0);
  const creditiResidui = (contract.crediti_totali ?? 0) - (contract.crediti_usati ?? 0);
  const hasPagamenti = (contract.totale_versato ?? 0) > 0;
  const needsForce = ratePendenti > 0 || creditiResidui > 0;

  const handleConfirm = () => {
    deleteMutation.mutate(
      {
        id: contract.id,
        force: needsForce || undefined,
        keepPayments: needsForce && hasPagamenti && keepPayments ? true : undefined,
      },
      { onSuccess: () => { onOpenChange(false); onDeleted?.(); } },
    );
  };

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      setForceConfirmed(false);
      setKeepPayments(true);
    }
    onOpenChange(isOpen);
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Eliminare questo contratto?</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3">
              <p>
                Stai per eliminare il contratto{" "}
                <span className="font-semibold">{contract.tipo_pacchetto}</span>
                {clientName && (
                  <> di <span className="font-semibold">{clientName}</span></>
                )}
                .
              </p>

              {needsForce ? (
                <div className="rounded-md border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950/50">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
                    <div className="space-y-1 text-sm">
                      <p className="font-medium text-amber-800 dark:text-amber-200">
                        Questo contratto ha obbligazioni attive
                      </p>
                      <ul className="list-disc pl-4 text-amber-700 dark:text-amber-300">
                        {ratePendenti > 0 && (
                          <li>
                            {ratePendenti} {ratePendenti === 1 ? "rata non saldata" : "rate non saldate"}
                            {importoNonRiscosso > 0 && ` (${formatCurrency(importoNonRiscosso)} non riscossi)`}
                          </li>
                        )}
                        {creditiResidui > 0 && (
                          <li>
                            {creditiResidui} {creditiResidui === 1 ? "credito residuo" : "crediti residui"} (sedute PT non consumate)
                          </li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">
                  Verranno eliminate anche tutte le rate associate. Questa azione non
                  puo&apos; essere annullata.
                </p>
              )}
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        {needsForce && (
          <div className="space-y-2">
            <div
              className="flex items-center gap-2 rounded-md border px-3 py-2 cursor-pointer"
              onClick={() => setForceConfirmed((v) => !v)}
            >
              <Checkbox
                checked={forceConfirmed}
                onClick={(e) => e.stopPropagation()}
                onCheckedChange={(checked) => setForceConfirmed(checked === true)}
              />
              <span className="text-sm select-none">
                Confermo l&apos;eliminazione forzata di questo contratto
              </span>
            </div>

            {hasPagamenti && (
              <div
                className="flex items-center gap-2 rounded-md border px-3 py-2 cursor-pointer"
                onClick={() => setKeepPayments((v) => !v)}
              >
                <Checkbox
                  checked={keepPayments}
                  onClick={(e) => e.stopPropagation()}
                  onCheckedChange={(checked) => setKeepPayments(checked === true)}
                />
                <span className="text-sm select-none">
                  Mantieni i {formatCurrency(contract.totale_versato ?? 0)} gia&apos; incassati nel registro di cassa
                </span>
              </div>
            )}
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteMutation.isPending}>
            Annulla
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={deleteMutation.isPending || (needsForce && !forceConfirmed)}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {needsForce ? "Elimina forzatamente" : "Elimina"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
