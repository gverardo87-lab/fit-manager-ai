// src/components/contracts/PaymentPlanTab.tsx
"use client";

/**
 * Tab Piano Pagamenti — interattivita' finanziaria.
 *
 * Due stati:
 * A) Nessuna rata → form per generare piano automatico
 * B) Rate esistenti → lista card premium con alert scadenze
 *
 * Il riepilogo finanziario e' nella Hero Section (ContractDetailSheet),
 * qui mostriamo solo il contenuto operativo.
 */

import { useState } from "react";
import { format, parseISO, isPast } from "date-fns";
import { it } from "date-fns/locale";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  Banknote,
  Plus,
  CalendarClock,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DatePicker } from "@/components/ui/date-picker";
import { useGeneratePaymentPlan, usePayRate } from "@/hooks/useRates";
import type { Rate, ContractWithRates } from "@/types/api";
import { PAYMENT_METHODS, PLAN_FREQUENCIES } from "@/types/api";

interface PaymentPlanTabProps {
  contract: ContractWithRates;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

// ════════════════════════════════════════════════════════════
// Componente principale
// ════════════════════════════════════════════════════════════

export function PaymentPlanTab({ contract }: PaymentPlanTabProps) {
  const rates = contract.rate ?? [];
  const hasRates = rates.length > 0;

  return hasRates ? (
    <RatesList rates={rates} />
  ) : (
    <GeneratePlanForm contract={contract} />
  );
}

// ════════════════════════════════════════════════════════════
// Caso A: Nessuna rata → form per generare piano
// ════════════════════════════════════════════════════════════

function GeneratePlanForm({ contract }: { contract: ContractWithRates }) {
  const remaining =
    (contract.prezzo_totale ?? 0) - contract.totale_versato;

  const [numeroRate, setNumeroRate] = useState(3);
  const [frequenza, setFrequenza] = useState("MENSILE");
  const [dataPrimaRata, setDataPrimaRata] = useState<Date | undefined>(
    undefined
  );

  const generateMutation = useGeneratePaymentPlan();

  const handleGenerate = () => {
    if (!dataPrimaRata) return;

    generateMutation.mutate({
      contractId: contract.id,
      importo_da_rateizzare: Math.max(0, remaining),
      numero_rate: numeroRate,
      data_prima_rata: format(dataPrimaRata, "yyyy-MM-dd"),
      frequenza,
    });
  };

  return (
    <div className="space-y-5 rounded-lg border border-dashed p-6">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Plus className="h-5 w-5" />
        <p className="font-medium">Nessun piano rate configurato</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Importo da rateizzare</Label>
          <Input
            value={formatCurrency(Math.max(0, remaining))}
            disabled
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="numero_rate">Numero Rate</Label>
          <Input
            id="numero_rate"
            type="number"
            min={1}
            max={60}
            value={numeroRate}
            onChange={(e) => setNumeroRate(parseInt(e.target.value, 10) || 1)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Data Prima Rata</Label>
          <DatePicker
            value={dataPrimaRata}
            onChange={setDataPrimaRata}
            placeholder="Seleziona data..."
          />
        </div>
        <div className="space-y-2">
          <Label>Frequenza</Label>
          <Select value={frequenza} onValueChange={setFrequenza}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PLAN_FREQUENCIES.map((f) => (
                <SelectItem key={f} value={f}>
                  {f.charAt(0) + f.slice(1).toLowerCase()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Button
        onClick={handleGenerate}
        disabled={generateMutation.isPending || !dataPrimaRata}
        className="w-full"
      >
        {generateMutation.isPending && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        )}
        Genera Piano Pagamenti
      </Button>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Caso B: Rate esistenti → lista premium
// ════════════════════════════════════════════════════════════

function RatesList({ rates }: { rates: Rate[] }) {
  // Ordina: scadute prima, poi pendenti/parziali, poi saldate
  const sorted = [...rates].sort((a, b) => {
    const aWeight = rateWeight(a);
    const bWeight = rateWeight(b);
    if (aWeight !== bWeight) return aWeight - bWeight;
    return new Date(a.data_scadenza).getTime() - new Date(b.data_scadenza).getTime();
  });

  const overdueCount = rates.filter(
    (r) => r.stato !== "SALDATA" && isPast(parseISO(r.data_scadenza))
  ).length;

  return (
    <div className="space-y-3">
      {/* Alert banner per rate scadute */}
      {overdueCount > 0 && (
        <div className="flex items-center gap-2.5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-900/50 dark:bg-red-950/30">
          <AlertCircle className="h-4.5 w-4.5 shrink-0 text-red-600 dark:text-red-400" />
          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            {overdueCount} rat{overdueCount === 1 ? "a scaduta" : "e scadute"} — azione richiesta
          </p>
        </div>
      )}

      <ScrollArea className="max-h-[380px]">
        <div className="space-y-2.5 pr-4">
          {sorted.map((rate) => (
            <RateCard key={rate.id} rate={rate} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

/** Peso per ordinamento: scadute (0) → pendenti (1) → parziali (2) → saldate (3) */
function rateWeight(rate: Rate): number {
  if (rate.stato === "SALDATA") return 3;
  if (isPast(parseISO(rate.data_scadenza))) return 0;
  if (rate.stato === "PARZIALE") return 2;
  return 1;
}

// ════════════════════════════════════════════════════════════
// Rate Card — design premium
// ════════════════════════════════════════════════════════════

function RateCard({ rate }: { rate: Rate }) {
  const payMutation = usePayRate();
  const [showPayForm, setShowPayForm] = useState(false);

  const isSaldata = rate.stato === "SALDATA";
  const isOverdue = !isSaldata && isPast(parseISO(rate.data_scadenza));

  // Card border & bg cambiano in base allo stato
  const cardClasses = isOverdue
    ? "rounded-lg border-2 border-red-200 bg-red-50/50 p-4 dark:border-red-900/60 dark:bg-red-950/20"
    : isSaldata
      ? "rounded-lg border border-emerald-200/60 bg-emerald-50/30 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/10"
      : "rounded-lg border bg-white p-4 dark:bg-zinc-900";

  return (
    <div className={cardClasses}>
      <div className="flex items-center justify-between gap-3">
        {/* ── Icona + info ── */}
        <div className="flex items-center gap-3 min-w-0">
          <StatusIcon isSaldata={isSaldata} isOverdue={isOverdue} />
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">
              {rate.descrizione ?? `Rata #${rate.id}`}
            </p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <CalendarClock className={`h-3 w-3 ${
                isOverdue ? "text-red-500" : "text-muted-foreground"
              }`} />
              <p className={`text-xs ${
                isOverdue
                  ? "font-semibold text-red-600 dark:text-red-400"
                  : "text-muted-foreground"
              }`}>
                {format(parseISO(rate.data_scadenza), "dd MMMM yyyy", {
                  locale: it,
                })}
              </p>
            </div>
          </div>
        </div>

        {/* ── Importo + badge ── */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <p className={`text-sm font-bold tabular-nums ${
              isSaldata ? "text-emerald-700 dark:text-emerald-400" : ""
            }`}>
              {formatCurrency(rate.importo_previsto)}
            </p>
            {rate.importo_saldato > 0 && !isSaldata && (
              <p className="text-[11px] text-muted-foreground tabular-nums">
                Versato {formatCurrency(rate.importo_saldato)}
              </p>
            )}
          </div>
          <RateStatusBadge stato={rate.stato} isOverdue={isOverdue} />
        </div>
      </div>

      {/* ── Azione pagamento ── */}
      {!isSaldata && !showPayForm && (
        <Button
          variant={isOverdue ? "default" : "outline"}
          size="sm"
          className={`mt-3 w-full ${
            isOverdue
              ? "bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600"
              : ""
          }`}
          onClick={() => setShowPayForm(true)}
        >
          <Banknote className="mr-2 h-4 w-4" />
          {isOverdue ? "Paga Ora — Rata Scaduta" : "Segna come Pagata"}
        </Button>
      )}

      {/* ── Form pagamento inline ── */}
      {!isSaldata && showPayForm && (
        <PayRateForm
          rate={rate}
          payMutation={payMutation}
          onCancel={() => setShowPayForm(false)}
        />
      )}
    </div>
  );
}

// ── Icona stato ──

function StatusIcon({ isSaldata, isOverdue }: { isSaldata: boolean; isOverdue: boolean }) {
  if (isSaldata) {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
        <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
      </div>
    );
  }
  if (isOverdue) {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100 animate-pulse dark:bg-red-900/30">
        <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
      </div>
    );
  }
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
      <Clock className="h-4 w-4 text-amber-600 dark:text-amber-400" />
    </div>
  );
}

// ── Badge stato rata ──

function RateStatusBadge({
  stato,
  isOverdue,
}: {
  stato: string;
  isOverdue: boolean;
}) {
  if (stato === "SALDATA") {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
        Saldata
      </Badge>
    );
  }
  if (isOverdue) {
    return (
      <Badge variant="destructive" className="animate-pulse">
        Scaduta
      </Badge>
    );
  }
  if (stato === "PARZIALE") {
    return (
      <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400">
        Parziale
      </Badge>
    );
  }
  return (
    <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400">
      Pendente
    </Badge>
  );
}

// ════════════════════════════════════════════════════════════
// Form pagamento inline
// ════════════════════════════════════════════════════════════

function PayRateForm({
  rate,
  payMutation,
  onCancel,
}: {
  rate: Rate;
  payMutation: ReturnType<typeof usePayRate>;
  onCancel: () => void;
}) {
  const remaining = rate.importo_previsto - rate.importo_saldato;
  const [importo, setImporto] = useState(remaining);
  const [metodo, setMetodo] = useState("CONTANTI");

  const handlePay = () => {
    payMutation.mutate(
      {
        rateId: rate.id,
        importo,
        metodo,
        data_pagamento: format(new Date(), "yyyy-MM-dd"),
      },
      { onSuccess: onCancel }
    );
  };

  return (
    <div className="mt-3 space-y-3 rounded-lg border bg-zinc-50/80 p-4 dark:bg-zinc-800/50">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Importo</Label>
          <Input
            type="number"
            step="0.01"
            value={importo}
            onChange={(e) => setImporto(parseFloat(e.target.value) || 0)}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Metodo</Label>
          <Select value={metodo} onValueChange={setMetodo}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAYMENT_METHODS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={handlePay}
          disabled={payMutation.isPending || importo <= 0}
          className="flex-1"
        >
          {payMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          Conferma Pagamento
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCancel}
          disabled={payMutation.isPending}
        >
          Annulla
        </Button>
      </div>
    </div>
  );
}
