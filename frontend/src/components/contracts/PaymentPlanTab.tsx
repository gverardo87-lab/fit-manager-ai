// src/components/contracts/PaymentPlanTab.tsx
"use client";

/**
 * Tab Piano Pagamenti — Advanced Billing Engine.
 *
 * Tre stati:
 * A) Nessuna rata → form per generare piano automatico
 * B) Rate esistenti → lista card premium con:
 *    - Dropdown Modifica/Elimina (nascosto su SALDATE)
 *    - Alert scadenze overdue
 *    - Financial Mismatch Alert (somma rate ≠ importo da saldare)
 * C) Bottone "+ Aggiungi Rata" per rate manuali fuori piano
 */

import { useState } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Banknote,
  Plus,
  CalendarClock,
  MoreVertical,
  Pencil,
  Trash2,
  Undo2,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { DatePicker } from "@/components/ui/date-picker";
import {
  useGeneratePaymentPlan,
  usePayRate,
  useCreateRate,
  useDeleteRate,
} from "@/hooks/useRates";
import { RateEditDialog } from "./RateEditDialog";
import { RateUnpayDialog } from "./RateUnpayDialog";
import type { Rate, ContractWithRates } from "@/types/api";
import { PAYMENT_METHODS, PLAN_FREQUENCIES } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface PaymentPlanTabProps {
  contract: ContractWithRates;
}

// ════════════════════════════════════════════════════════════
// Componente principale
// ════════════════════════════════════════════════════════════

export function PaymentPlanTab({ contract }: PaymentPlanTabProps) {
  const rates = contract.rate ?? [];
  const hasRates = rates.length > 0;

  return hasRates ? (
    <RatesList rates={rates} contract={contract} />
  ) : (
    <GeneratePlanForm contract={contract} />
  );
}

// ════════════════════════════════════════════════════════════
// Caso A: Nessuna rata → form per generare piano
// ════════════════════════════════════════════════════════════

function GeneratePlanForm({ contract }: { contract: ContractWithRates }) {
  // Importo dal backend: prezzo - acconto - rate saldate (unica fonte di verita')
  const remaining = contract.importo_da_rateizzare;

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
      importo_da_rateizzare: remaining,
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
            value={formatCurrency(remaining)}
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

function RatesList({
  rates,
  contract,
}: {
  rates: Rate[];
  contract: ContractWithRates;
}) {
  const [editRate, setEditRate] = useState<Rate | null>(null);
  const [deleteRate, setDeleteRate] = useState<Rate | null>(null);
  const [unpayRate, setUnpayRate] = useState<Rate | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const deleteMutation = useDeleteRate();

  // Ordina: scadute prima, poi pendenti/parziali, poi saldate
  const sorted = [...rates].sort((a, b) => {
    const aWeight = rateWeight(a);
    const bWeight = rateWeight(b);
    if (aWeight !== bWeight) return aWeight - bWeight;
    return new Date(a.data_scadenza).getTime() - new Date(b.data_scadenza).getTime();
  });

  // Tutti i valori dal backend — zero calcoli frontend
  const overdueCount = contract.rate_scadute;
  const prezzoTotale = contract.prezzo_totale ?? 0;
  const versato = contract.totale_versato;
  const daRateizzare = contract.importo_da_rateizzare;
  const sommaRatePendenti = contract.somma_rate_pendenti;
  const mancante = contract.importo_disallineamento;
  const hasMismatch = !contract.piano_allineato;

  return (
    <div className="space-y-3">
      {/* ── Breakdown Finanziario ── */}
      <div className="rounded-lg border bg-zinc-50/80 p-4 dark:bg-zinc-800/30">
        <table className="w-full text-sm">
          <tbody>
            <tr>
              <td className="py-0.5 text-muted-foreground">Prezzo totale</td>
              <td className="py-0.5 text-right font-semibold tabular-nums">
                {formatCurrency(prezzoTotale)}
              </td>
            </tr>
            {versato > 0 && (
              <tr>
                <td className="py-0.5 text-muted-foreground">Totale versato</td>
                <td className="py-0.5 text-right font-semibold tabular-nums text-emerald-700 dark:text-emerald-400">
                  &minus;{formatCurrency(versato)}
                </td>
              </tr>
            )}
            <tr className="border-t">
              <td className="pt-1 font-medium">Ancora da incassare</td>
              <td className="pt-1 text-right font-bold tabular-nums">
                {formatCurrency(daRateizzare)}
              </td>
            </tr>
            <tr>
              <td className="py-0.5 text-muted-foreground">Rate pendenti</td>
              <td className={`py-0.5 text-right font-semibold tabular-nums ${
                hasMismatch
                  ? "text-amber-700 dark:text-amber-400"
                  : "text-emerald-700 dark:text-emerald-400"
              }`}>
                {formatCurrency(sommaRatePendenti)}
                {!hasMismatch && " ✓"}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Mismatch Alert — linguaggio chiaro */}
      {hasMismatch && (
        <Alert variant={mancante > 0 ? "destructive" : "default"}>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Piano rate da allineare</AlertTitle>
          <AlertDescription>
            {mancante > 0
              ? `Le rate pendenti coprono ${formatCurrency(sommaRatePendenti)} su ${formatCurrency(daRateizzare)} da incassare. Mancano ${formatCurrency(mancante)}.`
              : `Le rate pendenti superano il dovuto di ${formatCurrency(Math.abs(mancante))}. Aggiusta gli importi.`
            }
            {" "}Rigenera il piano per allinearlo.
          </AlertDescription>
        </Alert>
      )}

      {/* Alert banner per rate scadute */}
      {overdueCount > 0 && (
        <div className="flex items-center gap-2.5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-900/50 dark:bg-red-950/30">
          <AlertCircle className="h-4.5 w-4.5 shrink-0 text-red-600 dark:text-red-400" />
          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            {overdueCount} rat{overdueCount === 1 ? "a scaduta" : "e scadute"} — azione richiesta
          </p>
        </div>
      )}

      <ScrollArea className="max-h-[50vh]">
        <div className="space-y-2.5 pr-4">
          {sorted.map((rate) => (
            <RateCard
              key={rate.id}
              rate={rate}
              onEdit={setEditRate}
              onDelete={setDeleteRate}
              onUnpay={setUnpayRate}
            />
          ))}
        </div>
      </ScrollArea>

      {/* ── Bottone Aggiungi Rata ── */}
      {showAddForm ? (
        <AddRateForm
          contractId={contract.id}
          onClose={() => setShowAddForm(false)}
        />
      ) : (
        <Button
          variant="outline"
          size="sm"
          className="w-full border-dashed"
          onClick={() => setShowAddForm(true)}
        >
          <Plus className="mr-2 h-4 w-4" />
          Aggiungi Rata
        </Button>
      )}

      {/* ── Edit Dialog ── */}
      <RateEditDialog
        rate={editRate}
        open={editRate !== null}
        onOpenChange={(open) => { if (!open) setEditRate(null); }}
      />

      {/* ── Unpay Dialog (conferma con "ANNULLA") ── */}
      <RateUnpayDialog
        rate={unpayRate}
        open={unpayRate !== null}
        onOpenChange={(open) => { if (!open) setUnpayRate(null); }}
      />

      {/* ── Delete Confirm ── */}
      <AlertDialog
        open={deleteRate !== null}
        onOpenChange={(open) => { if (!open) setDeleteRate(null); }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare questa rata?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteRate?.descrizione ?? `Rata #${deleteRate?.id}`} —{" "}
              {deleteRate ? formatCurrency(deleteRate.importo_previsto) : ""}
              . Questa azione e' irreversibile.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>
              Annulla
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-white hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (!deleteRate) return;
                deleteMutation.mutate(deleteRate.id, {
                  onSuccess: () => setDeleteRate(null),
                });
              }}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

/** Peso per ordinamento: scadute (0) → pendenti (1) → parziali (2) → saldate (3) */
function rateWeight(rate: Rate): number {
  if (rate.stato === "SALDATA") return 3;
  if (rate.is_scaduta) return 0;
  if (rate.stato === "PARZIALE") return 2;
  return 1;
}

// ════════════════════════════════════════════════════════════
// Rate Card — design premium con dropdown azioni
// ════════════════════════════════════════════════════════════

function RateCard({
  rate,
  onEdit,
  onDelete,
  onUnpay,
}: {
  rate: Rate;
  onEdit: (rate: Rate) => void;
  onDelete: (rate: Rate) => void;
  onUnpay: (rate: Rate) => void;
}) {
  const payMutation = usePayRate();
  const [showPayForm, setShowPayForm] = useState(false);

  const isSaldata = rate.stato === "SALDATA";
  const isOverdue = rate.is_scaduta;
  const overdueDays = rate.giorni_ritardo;

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
            {/* ── Alert scaduta intelligente: giorni di ritardo ── */}
            {isOverdue && (
              <p className={`text-[11px] font-bold mt-0.5 ${
                overdueDays > 30
                  ? "text-red-700 dark:text-red-400"
                  : "text-amber-700 dark:text-amber-400"
              }`}>
                Scaduta da {overdueDays} giorn{overdueDays === 1 ? "o" : "i"}
              </p>
            )}
          </div>
        </div>

        {/* ── Importo + badge + azioni ── */}
        <div className="flex items-center gap-2 shrink-0">
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

          {/* ── Dropdown azioni ── */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreVertical className="h-4 w-4" />
                <span className="sr-only">Azioni rata</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(rate)}>
                <Pencil className="mr-2 h-4 w-4" />
                Modifica
              </DropdownMenuItem>
              {rate.importo_saldato > 0 ? (
                <DropdownMenuItem
                  onClick={() => onUnpay(rate)}
                  className="text-destructive focus:text-destructive"
                >
                  <Undo2 className="mr-2 h-4 w-4" />
                  Revoca Pagamento
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={() => onDelete(rate)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Elimina
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* ── Storico pagamenti (PARZIALE e SALDATA) ── */}
      {rate.pagamenti.length > 0 && (
        <PaymentHistory rate={rate} />
      )}

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
          {isOverdue
            ? `Paga Ora — ${overdueDays}g di ritardo`
            : "Segna come Pagata"
          }
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
  const residuo = rate.importo_residuo;
  const [importo, setImporto] = useState(residuo);
  const [metodo, setMetodo] = useState("CONTANTI");

  // Smart default: scadenza passata → usa data_scadenza, futura → oggi
  const scadenza = parseISO(rate.data_scadenza);
  const oggi = new Date();
  const smartDefault = scadenza <= oggi ? scadenza : oggi;
  const [dataPagamento, setDataPagamento] = useState<Date>(smartDefault);

  const isPartial = importo > 0 && importo < residuo - 0.01;
  const exceedsResiduo = importo > residuo + 0.01;
  const canPay = !payMutation.isPending && importo > 0 && !exceedsResiduo;

  const handlePay = () => {
    payMutation.mutate(
      {
        rateId: rate.id,
        importo,
        metodo,
        data_pagamento: format(dataPagamento, "yyyy-MM-dd"),
      },
      { onSuccess: onCancel }
    );
  };

  return (
    <div className="mt-3 space-y-3 rounded-lg border bg-zinc-50/80 p-4 dark:bg-zinc-800/50">
      {/* Quick buttons */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-full border px-3 py-1 text-xs font-medium hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          onClick={() => setImporto(residuo)}
        >
          Tutto ({formatCurrency(residuo)})
        </button>
        {residuo >= 2 && (
          <button
            type="button"
            className="rounded-full border px-3 py-1 text-xs font-medium hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            onClick={() => setImporto(Math.round(residuo / 2 * 100) / 100)}
          >
            50%
          </button>
        )}
        <span className="ml-auto text-[11px] text-muted-foreground">
          Residuo: {formatCurrency(residuo)}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Importo</Label>
          <Input
            type="number"
            step="0.01"
            min="0.01"
            max={residuo}
            value={importo}
            onChange={(e) => setImporto(parseFloat(e.target.value) || 0)}
          />
          {exceedsResiduo && (
            <p className="text-[11px] text-destructive">
              Supera il residuo di {formatCurrency(residuo)}
            </p>
          )}
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
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Data Pagamento</Label>
          <DatePicker
            value={dataPagamento}
            onChange={(d) => { if (d) setDataPagamento(d); }}
          />
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={handlePay}
          disabled={!canPay}
          className="flex-1"
        >
          {payMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          {isPartial ? `Paga ${formatCurrency(importo)} (parziale)` : `Paga ${formatCurrency(importo)}`}
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

// ════════════════════════════════════════════════════════════
// Form aggiunta rata manuale
// ════════════════════════════════════════════════════════════

function AddRateForm({
  contractId,
  onClose,
}: {
  contractId: number;
  onClose: () => void;
}) {
  const createMutation = useCreateRate();
  const [importo, setImporto] = useState("");
  const [descrizione, setDescrizione] = useState("");
  const [dataScadenza, setDataScadenza] = useState<Date | undefined>(undefined);

  const handleCreate = () => {
    if (!dataScadenza || !importo) return;

    createMutation.mutate(
      {
        id_contratto: contractId,
        importo_previsto: parseFloat(importo),
        data_scadenza: format(dataScadenza, "yyyy-MM-dd"),
        descrizione: descrizione.trim() || undefined,
      },
      { onSuccess: onClose }
    );
  };

  return (
    <div className="space-y-3 rounded-lg border border-dashed bg-zinc-50/50 p-4 dark:bg-zinc-800/30">
      <p className="text-sm font-semibold">Nuova Rata Manuale</p>
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">Importo</Label>
          <Input
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0,00"
            value={importo}
            onChange={(e) => setImporto(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Data Scadenza</Label>
          <DatePicker
            value={dataScadenza}
            onChange={setDataScadenza}
            placeholder="Seleziona..."
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Descrizione</Label>
          <Input
            placeholder="es. Rata extra"
            value={descrizione}
            onChange={(e) => setDescrizione(e.target.value)}
          />
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={handleCreate}
          disabled={createMutation.isPending || !importo || !dataScadenza}
          className="flex-1"
        >
          {createMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          Crea Rata
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onClose}
          disabled={createMutation.isPending}
        >
          Annulla
        </Button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Storico Pagamenti — timeline cronologica per rata
// ════════════════════════════════════════════════════════════

function PaymentHistory({ rate }: { rate: Rate }) {
  const [expanded, setExpanded] = useState(false);
  const payments = rate.pagamenti;
  const isSaldata = rate.stato === "SALDATA";

  // Mostra max 2 pagamenti, espandibile
  const visible = expanded ? payments : payments.slice(0, 2);
  const hiddenCount = payments.length - 2;

  return (
    <div className="mt-2 space-y-1">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {payments.length === 1 ? "Pagamento" : `${payments.length} Pagamenti`}
      </p>
      <div className="space-y-0.5">
        {visible.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
          >
            <CheckCircle2 className={`h-3 w-3 shrink-0 ${
              isSaldata ? "text-emerald-500" : "text-amber-500"
            }`} />
            <span className="tabular-nums font-semibold">
              {formatCurrency(p.importo)}
            </span>
            {p.metodo && (
              <span className="text-muted-foreground/70">{p.metodo}</span>
            )}
            <span className="ml-auto shrink-0">
              {format(parseISO(p.data_pagamento), "dd MMM yyyy", { locale: it })}
            </span>
          </div>
        ))}
      </div>
      {hiddenCount > 0 && !expanded && (
        <button
          type="button"
          className="text-[11px] text-primary hover:underline"
          onClick={() => setExpanded(true)}
        >
          Mostra altr{hiddenCount === 1 ? "o" : "i"} {hiddenCount}
        </button>
      )}
      {/* Totale versato / previsto */}
      {payments.length > 1 && (
        <div className="flex items-center gap-1 border-t pt-1 text-[11px] text-muted-foreground">
          <span>Totale versato:</span>
          <span className="tabular-nums font-semibold">
            {formatCurrency(rate.importo_saldato)} / {formatCurrency(rate.importo_previsto)}
          </span>
        </div>
      )}
    </div>
  );
}
