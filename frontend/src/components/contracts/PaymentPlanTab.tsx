// src/components/contracts/PaymentPlanTab.tsx
"use client";

/**
 * Tab Piano Pagamenti — interattivita' finanziaria.
 *
 * Due stati:
 * A) Nessuna rata → form per generare piano automatico
 * B) Rate esistenti → lista con badge stato + bottone "Paga" per ogni rata
 *
 * Tutte le operazioni aggiornano la UI istantaneamente via invalidation.
 */

import { useState } from "react";
import { format, parseISO, isPast } from "date-fns";
import { it } from "date-fns/locale";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  Loader2,
  Banknote,
  Plus,
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
import { Separator } from "@/components/ui/separator";
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

  return (
    <div className="space-y-6">
      {/* ── Riepilogo finanziario ── */}
      <FinancialSummary contract={contract} />

      <Separator />

      {/* ── Contenuto condizionale ── */}
      {hasRates ? (
        <RatesList rates={rates} />
      ) : (
        <GeneratePlanForm contract={contract} />
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Riepilogo finanziario
// ════════════════════════════════════════════════════════════

function FinancialSummary({ contract }: { contract: ContractWithRates }) {
  const remaining =
    (contract.prezzo_totale ?? 0) - contract.totale_versato;

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="rounded-lg border bg-zinc-50 p-3 dark:bg-zinc-800/50">
        <p className="text-xs font-medium text-muted-foreground">
          Prezzo Totale
        </p>
        <p className="text-lg font-bold">
          {formatCurrency(contract.prezzo_totale ?? 0)}
        </p>
      </div>
      <div className="rounded-lg border bg-emerald-50 p-3 dark:bg-emerald-900/20">
        <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
          Versato
        </p>
        <p className="text-lg font-bold text-emerald-700 dark:text-emerald-400">
          {formatCurrency(contract.totale_versato)}
        </p>
      </div>
      <div className="rounded-lg border bg-amber-50 p-3 dark:bg-amber-900/20">
        <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
          Rimanente
        </p>
        <p className="text-lg font-bold text-amber-700 dark:text-amber-400">
          {formatCurrency(Math.max(0, remaining))}
        </p>
      </div>
    </div>
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
// Caso B: Rate esistenti → lista interattiva
// ════════════════════════════════════════════════════════════

function RatesList({ rates }: { rates: Rate[] }) {
  return (
    <ScrollArea className="max-h-[400px]">
      <div className="space-y-3 pr-4">
        {rates.map((rate) => (
          <RateCard key={rate.id} rate={rate} />
        ))}
      </div>
    </ScrollArea>
  );
}

function RateCard({ rate }: { rate: Rate }) {
  const payMutation = usePayRate();
  const [showPayForm, setShowPayForm] = useState(false);

  const isSaldata = rate.stato === "SALDATA";
  const isOverdue =
    !isSaldata && isPast(parseISO(rate.data_scadenza));

  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-center justify-between">
        {/* ── Info rata ── */}
        <div className="flex items-center gap-3">
          {isSaldata ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          ) : isOverdue ? (
            <AlertTriangle className="h-5 w-5 text-red-500" />
          ) : (
            <Clock className="h-5 w-5 text-amber-500" />
          )}
          <div>
            <p className="text-sm font-medium">
              {rate.descrizione ?? `Rata #${rate.id}`}
            </p>
            <p className="text-xs text-muted-foreground">
              Scadenza:{" "}
              {format(parseISO(rate.data_scadenza), "dd MMM yyyy", {
                locale: it,
              })}
            </p>
          </div>
        </div>

        {/* ── Importo + badge ── */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-bold">
              {formatCurrency(rate.importo_previsto)}
            </p>
            {rate.importo_saldato > 0 && !isSaldata && (
              <p className="text-xs text-muted-foreground">
                Versato: {formatCurrency(rate.importo_saldato)}
              </p>
            )}
          </div>
          <RateStatusBadge stato={rate.stato} isOverdue={isOverdue} />
        </div>
      </div>

      {/* ── Bottone Paga (solo se non saldata) ── */}
      {!isSaldata && !showPayForm && (
        <Button
          variant="outline"
          size="sm"
          className="mt-3 w-full"
          onClick={() => setShowPayForm(true)}
        >
          <Banknote className="mr-2 h-4 w-4" />
          Segna come Pagata
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
      <Badge className="bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400">
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

// ── Form pagamento inline ──

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
    <div className="mt-3 space-y-3 rounded-lg border bg-zinc-50 p-3 dark:bg-zinc-800/50">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Importo</Label>
          <Input
            type="number"
            step="0.01"
            value={importo}
            onChange={(e) => setImporto(parseFloat(e.target.value) || 0)}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Metodo</Label>
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
