// src/components/contracts/ContractDetailSheet.tsx
"use client";

/**
 * Sheet Master-Detail per gestione contratto.
 *
 * Layout:
 * 1. Hero Section persistente — 4 KPI finanziari a colpo d'occhio
 * 2. Tabs — Piano Pagamenti (default) + Dettagli contratto
 *
 * Usa useContract(id) per caricare contratto + rate in una sola chiamata.
 */

import { isPast, parseISO } from "date-fns";
import {
  Wallet,
  TrendingUp,
  CircleDollarSign,
  Receipt,
} from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { ContractForm, type ContractFormValues } from "./ContractForm";
import { PaymentPlanTab } from "./PaymentPlanTab";
import { useContract, useUpdateContract } from "@/hooks/useContracts";
import type { ContractUpdate, ContractWithRates } from "@/types/api";

// ── Formattazione valuta centralizzata ──

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

// ════════════════════════════════════════════════════════════
// Props & Component
// ════════════════════════════════════════════════════════════

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

        <div className="mt-6 space-y-6">
          {isLoading && <DetailSkeleton />}

          {contract && (
            <>
              {/* ── Hero Section: KPI finanziari ── */}
              <FinancialHero contract={contract} />

              {/* ── Tabs ── */}
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
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ════════════════════════════════════════════════════════════
// Hero Section — 4 KPI cards
// ════════════════════════════════════════════════════════════

function FinancialHero({ contract }: { contract: ContractWithRates }) {
  const totale = contract.prezzo_totale ?? 0;
  const versato = contract.totale_versato;
  const residuo = Math.max(0, totale - versato);
  const percentuale = totale > 0 ? Math.round((versato / totale) * 100) : 0;

  const rates = contract.rate ?? [];
  const ratePagate = rates.filter((r) => r.stato === "SALDATA").length;
  const rateTotali = rates.length;
  const rateScadute = rates.filter(
    (r) => r.stato !== "SALDATA" && isPast(parseISO(r.data_scadenza))
  ).length;

  return (
    <div className="rounded-xl border bg-gradient-to-br from-zinc-50 to-zinc-100/50 p-5 dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="grid grid-cols-2 gap-4">
        {/* ── Valore Contratto ── */}
        <div className="flex items-start gap-3 rounded-lg border bg-white p-3.5 shadow-sm dark:bg-zinc-900">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-100 dark:bg-violet-900/30">
            <Wallet className="h-4.5 w-4.5 text-violet-600 dark:text-violet-400" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
              Valore Contratto
            </p>
            <p className="text-lg font-bold tracking-tight">
              {formatCurrency(totale)}
            </p>
          </div>
        </div>

        {/* ── Avanzamento Finanziario ── */}
        <div className="flex flex-col gap-2 rounded-lg border bg-white p-3.5 shadow-sm dark:bg-zinc-900">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
              <TrendingUp className="h-4.5 w-4.5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
                Versato
              </p>
              <p className="text-lg font-bold tracking-tight text-emerald-700 dark:text-emerald-400">
                {formatCurrency(versato)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Progress value={percentuale} className="h-1.5 flex-1" />
            <span className="text-xs font-semibold tabular-nums text-muted-foreground">
              {percentuale}%
            </span>
          </div>
        </div>

        {/* ── Importo Residuo ── */}
        <div className="flex items-start gap-3 rounded-lg border bg-white p-3.5 shadow-sm dark:bg-zinc-900">
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
            residuo > 0
              ? "bg-amber-100 dark:bg-amber-900/30"
              : "bg-emerald-100 dark:bg-emerald-900/30"
          }`}>
            <CircleDollarSign className={`h-4.5 w-4.5 ${
              residuo > 0
                ? "text-amber-600 dark:text-amber-400"
                : "text-emerald-600 dark:text-emerald-400"
            }`} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
              Residuo
            </p>
            <p className={`text-lg font-bold tracking-tight ${
              residuo > 0
                ? "text-amber-700 dark:text-amber-400"
                : "text-emerald-700 dark:text-emerald-400"
            }`}>
              {formatCurrency(residuo)}
            </p>
          </div>
        </div>

        {/* ── Stato Rate ── */}
        <div className="flex items-start gap-3 rounded-lg border bg-white p-3.5 shadow-sm dark:bg-zinc-900">
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
            rateScadute > 0
              ? "bg-red-100 dark:bg-red-900/30"
              : "bg-blue-100 dark:bg-blue-900/30"
          }`}>
            <Receipt className={`h-4.5 w-4.5 ${
              rateScadute > 0
                ? "text-red-600 dark:text-red-400"
                : "text-blue-600 dark:text-blue-400"
            }`} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
              Stato Rate
            </p>
            {rateTotali > 0 ? (
              <div>
                <p className="text-lg font-bold tracking-tight">
                  {ratePagate}
                  <span className="text-sm font-normal text-muted-foreground">
                    {" "}/ {rateTotali}
                  </span>
                </p>
                {rateScadute > 0 && (
                  <p className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                    {rateScadute} scadut{rateScadute === 1 ? "a" : "e"}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm font-medium text-muted-foreground">
                Piano non generato
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Skeleton
// ════════════════════════════════════════════════════════════

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-40 w-full rounded-xl" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  );
}
