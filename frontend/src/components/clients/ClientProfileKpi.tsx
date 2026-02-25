// src/components/clients/ClientProfileKpi.tsx
"use client";

/**
 * 4 KPI card compatte per il profilo cliente.
 *
 * Crediti Residui | Contratti Attivi | Finanze (progress bar) | Ultimo Evento
 */

import {
  Target,
  FileText,
  Wallet,
  CalendarCheck,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency, formatShortDate, getFinanceBarColor } from "@/lib/format";
import type { ClientEnriched } from "@/types/api";

interface ClientProfileKpiProps {
  client: ClientEnriched;
}

export function ClientProfileKpi({ client }: ClientProfileKpiProps) {
  const prezzo = client.prezzo_totale_attivo;
  const versato = client.totale_versato;
  const ratio = prezzo > 0 ? versato / prezzo : 0;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {/* Crediti Residui */}
      <Card>
        <CardContent className="flex items-center gap-3 p-4">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
            client.crediti_residui > 0
              ? "bg-emerald-100 dark:bg-emerald-900/30"
              : "bg-zinc-100 dark:bg-zinc-800"
          }`}>
            <Target className={`h-5 w-5 ${
              client.crediti_residui > 0 ? "text-emerald-600" : "text-zinc-500"
            }`} />
          </div>
          <div>
            <p className="text-2xl font-bold tabular-nums">{client.crediti_residui}</p>
            <p className="text-xs text-muted-foreground">Crediti Residui</p>
          </div>
        </CardContent>
      </Card>

      {/* Contratti Attivi */}
      <Card>
        <CardContent className="flex items-center gap-3 p-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <FileText className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold tabular-nums">{client.contratti_attivi}</p>
            <p className="text-xs text-muted-foreground">Contratti Attivi</p>
          </div>
        </CardContent>
      </Card>

      {/* Finanze */}
      <Card>
        <CardContent className="flex items-center gap-3 p-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
            <Wallet className="h-5 w-5 text-amber-600" />
          </div>
          <div className="min-w-0 flex-1">
            {prezzo > 0 ? (
              <>
                <div className="flex items-baseline gap-1 text-sm">
                  <span className="font-bold tabular-nums">{formatCurrency(versato)}</span>
                  <span className="text-xs text-muted-foreground">/ {formatCurrency(prezzo)}</span>
                </div>
                <div className="mt-1 h-1.5 w-full rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className={`h-1.5 rounded-full transition-all ${getFinanceBarColor(ratio)}`}
                    style={{ width: `${Math.min(ratio * 100, 100)}%` }}
                  />
                </div>
              </>
            ) : (
              <>
                <p className="text-sm font-medium text-muted-foreground">—</p>
                <p className="text-xs text-muted-foreground">Finanze</p>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Ultimo Evento */}
      <Card>
        <CardContent className="flex items-center gap-3 p-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
            <CalendarCheck className="h-5 w-5 text-zinc-500" />
          </div>
          <div>
            <p className="text-sm font-bold">
              {client.ultimo_evento_data
                ? formatShortDate(client.ultimo_evento_data)
                : "Mai"}
            </p>
            <p className="text-xs text-muted-foreground">Ultimo Evento</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
