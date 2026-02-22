// src/components/contracts/ContractSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare un contratto.
 *
 * Pattern identico a ClientSheet: apre da destra, contiene il form,
 * si chiude su successo della mutation.
 */

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
}

export function ContractSheet({
  open,
  onOpenChange,
  contract,
}: ContractSheetProps) {
  const isEdit = !!contract;
  const createMutation = useCreateContract();
  const updateMutation = useUpdateContract();

  const isPending = createMutation.isPending || updateMutation.isPending;

  const handleSubmit = (values: ContractSubmitPayload) => {
    if (isEdit) {
      const { id_cliente, acconto, metodo_acconto, ...updatePayload } = values;
      updateMutation.mutate(
        { id: contract.id, ...updatePayload },
        { onSuccess: () => onOpenChange(false) }
      );
    } else {
      createMutation.mutate(values, {
        onSuccess: () => onOpenChange(false),
      });
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
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
            onSubmit={handleSubmit}
            isPending={isPending}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
