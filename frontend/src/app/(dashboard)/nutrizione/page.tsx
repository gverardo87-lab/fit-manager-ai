// src/app/(dashboard)/nutrizione/page.tsx
"use client";

/**
 * Pagina Nutrizione — lista piani alimentari cross-client.
 *
 * Pattern identico a /schede:
 * - KPI cards (totale, attivi, clienti con piano)
 * - Filter: Select cliente + chip Attivi/Tutti
 * - Tabella piani con link a /nutrizione/[id]
 * - Sheet creazione nuovo piano
 */

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { UtensilsCrossed, Plus, CheckCircle2 } from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useClients } from "@/hooks/useClients";
import { useAllNutritionPlans } from "@/hooks/useNutrition";
import { NutritionPlanSheet } from "@/components/nutrition/NutritionPlanSheet";
import { usePageReveal } from "@/lib/page-reveal";
import type { NutritionPlan, ClientEnriched, ClientEnrichedListResponse } from "@/types/api";

// ── KPI card ──────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div className="rounded-lg border bg-card px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold tabular-nums">{value}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

// ── Pagina ─────────────────────────────────────────────────────────────────

export default function NutrizionePage() {
  const router = useRouter();
  const { ready } = usePageReveal();

  const [clientFilter, setClientFilter] = useState<string>("__all__");
  const [soloAttivi, setSoloAttivi] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);

  const { data: clients = [] } = useClients();
  const { data: plans = [], isLoading } = useAllNutritionPlans();

  // Filtro client-side
  const filtered = useMemo(() => {
    let result = plans;
    if (clientFilter !== "__all__") result = result.filter((p) => p.id_cliente === parseInt(clientFilter));
    if (soloAttivi) result = result.filter((p) => p.attivo);
    return result;
  }, [plans, clientFilter, soloAttivi]);

  // KPI
  const kpi = useMemo(() => ({
    totale: plans.length,
    attivi: plans.filter((p) => p.attivo).length,
    clienti: new Set(plans.map((p) => p.id_cliente)).size,
  }), [plans]);

  const clientsList: ClientEnriched[] = Array.isArray(clients) ? clients : (clients as ClientEnrichedListResponse)?.items ?? [];

  return (
    <div
      className="space-y-6"
      style={{ opacity: ready ? 1 : 0, transition: "opacity 0.3s ease" }}
    >
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Nutrizione</h1>
          <p className="text-sm text-muted-foreground">Piani alimentari personalizzati per i clienti</p>
        </div>
        <Button onClick={() => setSheetOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          <span className="hidden sm:inline">Nuovo Piano</span>
        </Button>
      </div>

      {/* ── KPI ── */}
      <div className="grid grid-cols-3 gap-3">
        <KpiCard label="Piani totali" value={kpi.totale} />
        <KpiCard label="Piani attivi" value={kpi.attivi} />
        <KpiCard label="Clienti" value={kpi.clienti} sub="con almeno 1 piano" />
      </div>

      {/* ── Filtri ── */}
      <div className="flex flex-wrap items-center gap-2">
        <Select value={clientFilter} onValueChange={setClientFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Tutti i clienti" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Tutti i clienti</SelectItem>
            {clientsList.map((c: { id: number; nome: string; cognome: string }) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.cognome} {c.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <button
          onClick={() => setSoloAttivi(!soloAttivi)}
          className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            soloAttivi
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          <CheckCircle2 className="h-3 w-3" />
          Solo attivi
        </button>

        {(clientFilter !== "__all__" || soloAttivi) && (
          <button
            onClick={() => { setClientFilter("__all__"); setSoloAttivi(false); }}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Rimuovi filtri
          </button>
        )}
      </div>

      {/* ── Tabella ── */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-16">
          <UtensilsCrossed className="h-10 w-10 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">
            {plans.length === 0 ? "Nessun piano alimentare ancora" : "Nessun risultato per i filtri selezionati"}
          </p>
          {plans.length === 0 && (
            <Button variant="outline" size="sm" onClick={() => setSheetOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Crea il primo piano
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome piano</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead className="hidden sm:table-cell text-center">kcal/die</TableHead>
                <TableHead className="hidden md:table-cell text-center">Pasti</TableHead>
                <TableHead className="hidden sm:table-cell">Date</TableHead>
                <TableHead>Stato</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((p: NutritionPlan) => (
                <TableRow
                  key={p.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => router.push(`/nutrizione/${p.id}`)}
                >
                  <TableCell className="font-medium">{p.nome}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {p.client_cognome} {p.client_nome}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-center tabular-nums">
                    {p.obiettivo_calorico ?? "—"}
                  </TableCell>
                  <TableCell className="hidden md:table-cell text-center tabular-nums">
                    {p.num_pasti ?? 0}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-xs text-muted-foreground">
                    {p.data_inizio
                      ? format(new Date(p.data_inizio), "dd MMM yy", { locale: it })
                      : "—"}
                    {p.data_fine
                      ? ` → ${format(new Date(p.data_fine), "dd MMM yy", { locale: it })}`
                      : ""}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={`text-xs ${p.attivo ? "border-emerald-500 text-emerald-600" : "text-muted-foreground"}`}
                    >
                      {p.attivo ? "Attivo" : "Inattivo"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* ── Sheet nuovo piano ── */}
      <NutritionPlanSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        clientId={clientFilter !== "__all__" ? parseInt(clientFilter) : null}
        plan={null}
      />
    </div>
  );
}
