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

import {
  Wallet,
  TrendingUp,
  CircleDollarSign,
  Receipt,
  HandCoins,
  AlertTriangle,
  CheckCircle2,
  Dumbbell,
  Clock,
  Target,
  CalendarCheck,
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
import { ContractForm, type ContractSubmitPayload } from "./ContractForm";
import { PaymentPlanTab } from "./PaymentPlanTab";
import { useContract, useUpdateContract } from "@/hooks/useContracts";
import type { ContractWithRates } from "@/types/api";

import { formatCurrency } from "@/lib/format";

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

  const handleUpdateSubmit = (values: ContractSubmitPayload) => {
    if (!contractId) return;
    const { id_cliente, acconto, metodo_acconto, ...updatePayload } = values;
    updateMutation.mutate(
      { id: contractId, ...updatePayload },
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
// Hero Section — 6 KPI cards (2 righe x 3)
// ════════════════════════════════════════════════════════════

function FinancialHero({ contract }: { contract: ContractWithRates }) {
  // Tutti i valori dal backend — zero calcoli frontend
  const totale = contract.prezzo_totale ?? 0;
  const acconto = contract.acconto;
  const versato = contract.totale_versato;
  const residuo = contract.residuo;
  const percentuale = contract.percentuale_versata;
  const ratePagate = contract.rate_pagate;
  const rateTotali = contract.rate_totali;
  const rateScadute = contract.rate_scadute;
  const daRateizzare = contract.importo_da_rateizzare;
  const pianoCoperto = contract.piano_allineato;
  const creditiTotali = contract.crediti_totali ?? 0;
  const programmate = contract.sedute_programmate;
  const completate = contract.sedute_completate;
  const creditiResidui = contract.crediti_residui;

  return (
    <div className="rounded-xl border bg-gradient-to-br from-zinc-50 to-zinc-100/50 p-5 dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="space-y-3">
        {/* ── Riga 1: Valore | Acconto | Da Rateizzare ── */}
        <div className="grid grid-cols-3 gap-3">
          <KpiCard
            icon={<Wallet className="h-4 w-4 text-violet-600 dark:text-violet-400" />}
            iconBg="bg-violet-100 dark:bg-violet-900/30"
            label="Valore Contratto"
            value={formatCurrency(totale)}
          />
          <KpiCard
            icon={<HandCoins className="h-4 w-4 text-blue-600 dark:text-blue-400" />}
            iconBg="bg-blue-100 dark:bg-blue-900/30"
            label="Acconto"
            value={acconto > 0 ? formatCurrency(acconto) : "—"}
            valueClass={acconto > 0 ? "text-blue-700 dark:text-blue-400" : "text-muted-foreground"}
          />
          <KpiCard
            icon={pianoCoperto
              ? <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              : <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            }
            iconBg={pianoCoperto
              ? "bg-emerald-100 dark:bg-emerald-900/30"
              : "bg-amber-100 dark:bg-amber-900/30"
            }
            label="Da Rateizzare"
            value={pianoCoperto ? "Piano completo" : formatCurrency(daRateizzare)}
            valueClass={pianoCoperto
              ? "text-emerald-700 dark:text-emerald-400 text-sm"
              : "text-amber-700 dark:text-amber-400"
            }
          />
        </div>

        {/* ── Riga 2: Versato (con progress) | Rate Pagate | Rate Scadute ── */}
        <div className="grid grid-cols-3 gap-3">
          {/* Versato — card piu' alta con progress bar */}
          <div className="flex flex-col gap-2 rounded-lg border bg-white p-3 shadow-sm dark:bg-zinc-900">
            <div className="flex items-start gap-2.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                  Versato
                </p>
                <p className="text-base font-bold tabular-nums tracking-tight text-emerald-700 dark:text-emerald-400">
                  {formatCurrency(versato)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Progress value={percentuale} className="h-1.5 flex-1" />
              <span className="text-[10px] font-semibold tabular-nums text-muted-foreground">
                {percentuale}%
              </span>
            </div>
          </div>

          <KpiCard
            icon={<Receipt className="h-4 w-4 text-blue-600 dark:text-blue-400" />}
            iconBg="bg-blue-100 dark:bg-blue-900/30"
            label="Rate Pagate"
            value={rateTotali > 0 ? `${ratePagate} / ${rateTotali}` : "—"}
            valueClass={ratePagate === rateTotali && rateTotali > 0
              ? "text-emerald-700 dark:text-emerald-400"
              : undefined
            }
            subtitle={rateTotali === 0 ? "Piano non generato" : undefined}
          />

          <KpiCard
            icon={<CircleDollarSign className={`h-4 w-4 ${
              rateScadute > 0
                ? "text-red-600 dark:text-red-400"
                : "text-emerald-600 dark:text-emerald-400"
            }`} />}
            iconBg={rateScadute > 0
              ? "bg-red-100 dark:bg-red-900/30"
              : "bg-emerald-100 dark:bg-emerald-900/30"
            }
            label="Residuo"
            value={formatCurrency(residuo)}
            valueClass={residuo > 0
              ? "text-amber-700 dark:text-amber-400"
              : "text-emerald-700 dark:text-emerald-400"
            }
            subtitle={rateScadute > 0
              ? `${rateScadute} scadut${rateScadute === 1 ? "a" : "e"}`
              : undefined
            }
            subtitleClass="text-red-600 dark:text-red-400"
          />
        </div>

        {/* ── Riga 3: Crediti Sedute (solo se il contratto ha crediti) ── */}
        {creditiTotali > 0 && (
          <div className="grid grid-cols-4 gap-3">
            <KpiCard
              icon={<Dumbbell className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />}
              iconBg="bg-indigo-100 dark:bg-indigo-900/30"
              label="Crediti Totali"
              value={`${creditiTotali}`}
            />
            <KpiCard
              icon={<Clock className="h-4 w-4 text-blue-600 dark:text-blue-400" />}
              iconBg="bg-blue-100 dark:bg-blue-900/30"
              label="Programmate"
              value={`${programmate}`}
              valueClass={programmate > 0 ? "text-blue-700 dark:text-blue-400" : undefined}
            />
            <KpiCard
              icon={<CalendarCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />}
              iconBg="bg-emerald-100 dark:bg-emerald-900/30"
              label="Completate"
              value={`${completate}`}
              valueClass={completate > 0 ? "text-emerald-700 dark:text-emerald-400" : undefined}
            />
            <KpiCard
              icon={<Target className={`h-4 w-4 ${
                creditiResidui > 0
                  ? "text-amber-600 dark:text-amber-400"
                  : "text-emerald-600 dark:text-emerald-400"
              }`} />}
              iconBg={creditiResidui > 0
                ? "bg-amber-100 dark:bg-amber-900/30"
                : "bg-emerald-100 dark:bg-emerald-900/30"
              }
              label="Residui"
              value={`${creditiResidui}`}
              valueClass={creditiResidui > 0
                ? "text-amber-700 dark:text-amber-400"
                : "text-emerald-700 dark:text-emerald-400"
              }
              subtitle={creditiResidui === 0 ? "Crediti esauriti" : undefined}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ── KPI Card compatta riusabile ──

function KpiCard({
  icon,
  iconBg,
  label,
  value,
  valueClass,
  subtitle,
  subtitleClass,
}: {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: string;
  valueClass?: string;
  subtitle?: string;
  subtitleClass?: string;
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border bg-white p-3 shadow-sm dark:bg-zinc-900">
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </p>
        <p className={`text-base font-bold tabular-nums tracking-tight ${valueClass ?? ""}`}>
          {value}
        </p>
        {subtitle && (
          <p className={`text-[10px] font-semibold ${subtitleClass ?? "text-muted-foreground"}`}>
            {subtitle}
          </p>
        )}
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
