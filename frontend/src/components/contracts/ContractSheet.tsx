// src/components/contracts/ContractSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare un contratto.
 *
 * Pattern da ClientSheet: apre da destra, contiene il form,
 * si chiude su successo della mutation (con conferma se dirty).
 */

import { useCallback, useRef } from "react";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ContractForm, type ContractSubmitPayload } from "./ContractForm";
import { useCreateContract, useUpdateContract } from "@/hooks/useContracts";
import type { Contract } from "@/types/api";

interface ContractSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contract?: Contract | null;
  defaultClientId?: number;
}

export function ContractSheet({
  open,
  onOpenChange,
  contract,
  defaultClientId,
}: ContractSheetProps) {
  const isEdit = !!contract;
  const createMutation = useCreateContract();
  const updateMutation = useUpdateContract();

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

  const handleSubmit = (values: ContractSubmitPayload) => {
    if (isEdit) {
      const { id_cliente, acconto, metodo_acconto, ...updatePayload } = values;
      updateMutation.mutate(
        { id: contract.id, ...updatePayload },
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
            {isEdit ? "Modifica Contratto" : "Nuovo Contratto"}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <ContractForm
            key={contract?.id ?? "new"}
            contract={contract}
            defaultClientId={defaultClientId}
            onSubmit={handleSubmit}
            isPending={isPending}
            onDirtyChange={handleDirtyChange}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
