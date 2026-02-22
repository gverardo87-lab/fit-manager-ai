// src/components/agenda/DeleteEventDialog.tsx
"use client";

/**
 * Dialog di conferma eliminazione evento.
 *
 * Azione MEDIA (non critica come un contratto CASCADE).
 * Mostra titolo e date dell'evento per evitare errori.
 */

import { Loader2 } from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

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
import { useDeleteEvent } from "@/hooks/useAgenda";
import type { CalendarEvent } from "./calendar-setup";

interface DeleteEventDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event: CalendarEvent | null;
}

export function DeleteEventDialog({
  open,
  onOpenChange,
  event,
}: DeleteEventDialogProps) {
  const deleteMutation = useDeleteEvent();

  if (!event) return null;

  const handleConfirm = () => {
    deleteMutation.mutate(event.id, {
      onSuccess: () => onOpenChange(false),
    });
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Eliminare questo evento?</AlertDialogTitle>
          <AlertDialogDescription>
            Stai per eliminare{" "}
            <span className="font-semibold">{event.title}</span>
            {" "}del{" "}
            <span className="font-semibold">
              {format(event.start, "dd MMMM yyyy, HH:mm", { locale: it })}
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
