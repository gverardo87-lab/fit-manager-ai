// src/components/contracts/DeleteContractDialog.tsx
"use client";

/**
 * Dialog di conferma eliminazione contratto.
 *
 * Azione CRITICA: elimina il contratto e tutte le rate associate (CASCADE).
 * Mostra tipo pacchetto e nome cliente per evitare errori.
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
import { useDeleteContract } from "@/hooks/useContracts";
import type { Contract } from "@/types/api";

interface DeleteContractDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contract: Contract | null;
  clientName?: string;
}

export function DeleteContractDialog({
  open,
  onOpenChange,
  contract,
  clientName,
}: DeleteContractDialogProps) {
  const deleteMutation = useDeleteContract();

  if (!contract) return null;

  const handleConfirm = () => {
    deleteMutation.mutate(contract.id, {
      onSuccess: () => onOpenChange(false),
    });
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Eliminare questo contratto?</AlertDialogTitle>
          <AlertDialogDescription>
            Stai per eliminare il contratto{" "}
            <span className="font-semibold">
              {contract.tipo_pacchetto}
            </span>
            {clientName && (
              <>
                {" "}di <span className="font-semibold">{clientName}</span>
              </>
            )}
            . Verranno eliminate anche tutte le rate associate. Questa azione non
            puo' essere annullata.
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
