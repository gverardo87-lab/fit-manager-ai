// src/components/contracts/ContractDetailSheet.tsx
"use client";

/**
 * Sheet Master-Detail per gestione contratto.
 *
 * Largo (max-w-2xl) con due tab:
 * - Dettagli: form di modifica contratto (ContractForm)
 * - Piano Pagamenti: generazione piano + pagamento rate (PaymentPlanTab)
 *
 * Usa useContract(id) per caricare contratto + rate in una sola chiamata.
 */

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ContractForm, type ContractFormValues } from "./ContractForm";
import { PaymentPlanTab } from "./PaymentPlanTab";
import { useContract, useUpdateContract } from "@/hooks/useContracts";
import type { Contract, ContractUpdate } from "@/types/api";

interface ContractDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contractId: number | null;
  clientName?: string;
}

export function ContractDetailSheet({
  open,
  onOpenChange,
  contractId,
  clientName,
}: ContractDetailSheetProps) {
  const { data: contract, isLoading } = useContract(open ? contractId : null);
  const updateMutation = useUpdateContract();

  const handleUpdateSubmit = (values: ContractFormValues) => {
    if (!contractId) return;
    const { id_cliente, acconto, metodo_acconto, ...updatePayload } = values;
    updateMutation.mutate(
      { id: contractId, ...updatePayload } as unknown as ContractUpdate & { id: number },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle>
            Gestione Contratto
            {clientName && (
              <span className="ml-2 text-base font-normal text-muted-foreground">
                — {clientName}
              </span>
            )}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6">
          {isLoading && <DetailSkeleton />}

          {contract && (
            <Tabs defaultValue="payments" className="w-full">
              <TabsList className="w-full">
                <TabsTrigger value="payments" className="flex-1">
                  Piano Pagamenti
                </TabsTrigger>
                <TabsTrigger value="details" className="flex-1">
                  Dettagli
                </TabsTrigger>
              </TabsList>

              <TabsContent value="payments" className="mt-4">
                <PaymentPlanTab contract={contract} />
              </TabsContent>

              <TabsContent value="details" className="mt-4">
                <ContractForm
                  key={contract.id}
                  contract={contract}
                  onSubmit={handleUpdateSubmit}
                  isPending={updateMutation.isPending}
                />
              </TabsContent>
            </Tabs>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  );
}
