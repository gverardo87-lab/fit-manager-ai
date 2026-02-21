// src/components/clients/DeleteClientDialog.tsx
"use client";

/**
 * Dialog di conferma eliminazione cliente.
 *
 * Azione distruttiva → richiede conferma esplicita (Manifesto: regola conferme).
 * Mostra nome completo del cliente per evitare errori.
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
import { useDeleteClient } from "@/hooks/useClients";
import type { Client } from "@/types/api";

interface DeleteClientDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  client: Client | null;
}

export function DeleteClientDialog({
  open,
  onOpenChange,
  client,
}: DeleteClientDialogProps) {
  const deleteMutation = useDeleteClient();

  if (!client) return null;

  const handleConfirm = () => {
    deleteMutation.mutate(client.id, {
      onSuccess: () => onOpenChange(false),
    });
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Eliminare questo cliente?</AlertDialogTitle>
          <AlertDialogDescription>
            Stai per eliminare{" "}
            <span className="font-semibold">
              {client.nome} {client.cognome}
            </span>
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
