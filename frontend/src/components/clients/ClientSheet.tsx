// src/components/clients/ClientSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare un cliente.
 *
 * Si apre da destra con animazione. Contiene il ClientForm.
 * La chiusura avviene:
 * - Su successo della mutation (form invia, API risponde 2xx)
 * - Su click fuori dallo sheet o su X (con conferma se dirty)
 */

import { useCallback, useRef } from "react";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ClientForm, type ClientFormValues } from "./ClientForm";
import { useCreateClient, useUpdateClient } from "@/hooks/useClients";
import type { Client, ClientUpdate } from "@/types/api";

interface ClientSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  client?: Client | null;
}

export function ClientSheet({ open, onOpenChange, client }: ClientSheetProps) {
  const isEdit = !!client;
  const createMutation = useCreateClient();
  const updateMutation = useUpdateClient();

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

  const handleSubmit = (values: ClientFormValues) => {
    if (isEdit) {
      updateMutation.mutate(
        { id: client.id, ...values } as ClientUpdate & { id: number },
        { onSuccess: () => { dirtyRef.current = false; onOpenChange(false); } }
      );
    } else {
      createMutation.mutate(values, {
        onSuccess: () => { dirtyRef.current = false; onOpenChange(false); },
      });
    }
  };

  return (
    <Sheet open={open} onOpenChange={guardedOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>
            {isEdit ? "Modifica Cliente" : "Nuovo Cliente"}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <ClientForm
            key={client?.id ?? "new"}
            client={client}
            onSubmit={handleSubmit}
            isPending={isPending}
            onDirtyChange={handleDirtyChange}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
