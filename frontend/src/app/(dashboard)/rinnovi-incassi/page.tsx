"use client";

/**
 * Rinnovi & Incassi — pagina operativa actionable.
 *
 * Due sezioni:
 * 1. Contratti da rinnovare (in scadenza / scaduti con crediti)
 * 2. Rate in ritardo (con pagamento inline)
 *
 * Zero read-only: ogni riga ha un'azione primaria.
 */

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  CreditCard,
  HandCoins,
  Loader2,
  RefreshCw,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { useOverdueRates, useExpiringContracts } from "@/hooks/useDashboard";
import { usePayRate } from "@/hooks/useRates";
import { usePageReveal } from "@/lib/page-reveal";
import { formatCurrency, formatShortDate } from "@/lib/format";
import type { ExpiringContractItem, OverdueRateItem } from "@/types/api";

const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;

// ════════════════════════════════════════════════════════════
// Componente: Card rinnovo contratto
// ════════════════════════════════════════════════════════════

function RenewalCard({
  item,
  onRenew,
}: {
  item: ExpiringContractItem;
  onRenew: (item: ExpiringContractItem) => void;
}) {
  const isExpired = item.giorni_rimasti <= 0;
  const daysLabel = isExpired
    ? `Scaduto da ${Math.abs(item.giorni_rimasti)} giorni`
    : item.giorni_rimasti === 1
      ? "Scade domani"
      : `Scade tra ${item.giorni_rimasti} giorni`;

  return (
    <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/clienti/${item.client_id}`}
              className="truncate text-sm font-semibold hover:underline"
            >
              {item.client_nome} {item.client_cognome}
            </Link>
            <Badge variant={isExpired ? "destructive" : "outline"} className="text-xs">
              {daysLabel}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.tipo_pacchetto} · {item.crediti_residui}/{item.crediti_totali} crediti residui
            {item.prezzo_totale ? ` · ${formatCurrency(item.prezzo_totale)}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" asChild variant="outline">
            <Link href={`/contratti/${item.contract_id}`}>
              Dettaglio
            </Link>
          </Button>
          <Button size="sm" onClick={() => onRenew(item)}>
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Rinnova
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// Componente: Card rata in ritardo con pagamento inline
// ════════════════════════════════════════════════════════════

function OverdueRateCard({ item }: { item: OverdueRateItem }) {
  const payRate = usePayRate();
  const [method, setMethod] = useState("CONTANTI");
  const isPaying = payRate.isPending;

  const handlePay = () => {
    payRate.mutate({
      rateId: item.rate_id,
      importo: item.importo_residuo,
      metodo: method,
      data_pagamento: new Date().toISOString().split("T")[0],
    });
  };

  return (
    <Card className={`transition-all duration-200 ${isPaying ? "scale-[0.98] opacity-50" : "hover:-translate-y-0.5 hover:shadow-lg"}`}>
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/clienti/${item.client_id}`}
              className="truncate text-sm font-semibold hover:underline"
            >
              {item.client_nome} {item.client_cognome}
            </Link>
            <Badge variant="destructive" className="text-xs">
              {item.giorni_ritardo === 1
                ? "1 giorno di ritardo"
                : `${item.giorni_ritardo} giorni di ritardo`}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.tipo_pacchetto} · Scadenza {formatShortDate(item.data_scadenza)}
            {item.importo_saldato > 0
              ? ` · Versato ${formatCurrency(item.importo_saldato)}/${formatCurrency(item.importo_previsto)}`
              : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="whitespace-nowrap text-base font-bold text-destructive tabular-nums">
            {formatCurrency(item.importo_residuo)}
          </span>
          <Select value={method} onValueChange={setMethod} disabled={isPaying}>
            <SelectTrigger className="h-8 w-[110px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper">
              {PAYMENT_METHODS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m === "CONTANTI" ? "Contanti" : m === "POS" ? "POS" : "Bonifico"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" onClick={handlePay} disabled={isPaying}>
            {isPaying ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <CreditCard className="mr-1.5 h-3.5 w-3.5" />
            )}
            Incassa
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// Page
// ════════════════════════════════════════════════════════════

export default function RinnoviIncassiPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const overdueQuery = useOverdueRates();
  const expiringQuery = useExpiringContracts();

  // Sheet rinnovo contratto
  const [renewSheet, setRenewSheet] = useState(false);
  const [renewItem, setRenewItem] = useState<ExpiringContractItem | null>(null);

  const overdueItems = overdueQuery.data?.items ?? [];
  const expiringItems = expiringQuery.data?.items ?? [];
  const isLoading = overdueQuery.isLoading || expiringQuery.isLoading;
  const totalActions = overdueItems.length + expiringItems.length;

  const handleRenew = (item: ExpiringContractItem) => {
    setRenewItem(item);
    setRenewSheet(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={revealClass(0)} style={revealStyle(0)}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Rinnovi &amp; Incassi</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {totalActions === 0
                ? "Nessuna azione richiesta. Tutto in ordine!"
                : `${totalActions} ${totalActions === 1 ? "azione richiesta" : "azioni richieste"}`}
            </p>
          </div>
          {totalActions > 0 && (
            <div className="flex gap-2">
              {expiringItems.length > 0 && (
                <Badge variant="outline" className="gap-1.5 border-amber-300 bg-amber-50 text-amber-700">
                  <RefreshCw className="h-3 w-3" />
                  {expiringItems.length} da rinnovare
                </Badge>
              )}
              {overdueItems.length > 0 && (
                <Badge variant="outline" className="gap-1.5 border-red-300 bg-red-50 text-red-700">
                  <AlertTriangle className="h-3 w-3" />
                  {overdueItems.length} da incassare
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Empty state */}
      {totalActions === 0 && (
        <Card className={revealClass(60)} style={revealStyle(60)}>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <BadgeCheck className="h-12 w-12 text-emerald-500" />
            <h2 className="mt-4 text-lg font-semibold">Tutto in regola</h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Nessun contratto da rinnovare e nessuna rata in ritardo.
              Torna piu&apos; tardi o controlla i{" "}
              <Link href="/contratti" className="font-medium text-primary hover:underline">
                contratti
              </Link>.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Sezione: Contratti da rinnovare */}
      {expiringItems.length > 0 && (
        <section className={revealClass(60)} style={revealStyle(60)}>
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 text-amber-600" />
                <CardTitle className="text-base">
                  Contratti da rinnovare
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({expiringItems.length})
                  </span>
                </CardTitle>
              </div>
              <p className="text-xs text-muted-foreground">
                Contratti in scadenza o scaduti con crediti residui. Clicca &quot;Rinnova&quot; per creare un nuovo contratto pre-compilato.
              </p>
            </CardHeader>
            <CardContent className="space-y-2 pt-0">
              {expiringItems.map((item) => (
                <RenewalCard key={item.contract_id} item={item} onRenew={handleRenew} />
              ))}
            </CardContent>
          </Card>
        </section>
      )}

      {/* Sezione: Rate in ritardo */}
      {overdueItems.length > 0 && (
        <section className={revealClass(120)} style={revealStyle(120)}>
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <HandCoins className="h-4 w-4 text-red-600" />
                <CardTitle className="text-base">
                  Incassi in ritardo
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({overdueItems.length})
                  </span>
                </CardTitle>
              </div>
              <p className="text-xs text-muted-foreground">
                Rate scadute non saldate. Seleziona il metodo e incassa direttamente.
              </p>
            </CardHeader>
            <CardContent className="space-y-2 pt-0">
              {overdueItems.map((item) => (
                <OverdueRateCard key={item.rate_id} item={item} />
              ))}
            </CardContent>
          </Card>
        </section>
      )}

      {/* Quick links */}
      {totalActions > 0 && (
        <div className={`flex flex-wrap gap-2 ${revealClass(180)}`} style={revealStyle(180)}>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/contratti">
              Tutti i contratti
              <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/cassa">
              Libro mastro
              <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      )}

      {/* Sheet rinnovo — pre-compilato con dati del contratto scadente */}
      <ContractSheet
        open={renewSheet}
        onOpenChange={setRenewSheet}
        contract={null}
        renewContractId={renewItem?.contract_id}
        renewalDefaults={renewItem ? {
          id_cliente: renewItem.client_id,
          tipo_pacchetto: renewItem.tipo_pacchetto ?? "",
          crediti_totali: renewItem.crediti_totali,
          prezzo_totale: renewItem.prezzo_totale ?? 0,
        } : undefined}
      />
    </div>
  );
}
