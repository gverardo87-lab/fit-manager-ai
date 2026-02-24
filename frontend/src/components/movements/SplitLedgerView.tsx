// src/components/movements/SplitLedgerView.tsx
"use client";

/**
 * Vista Split Entrate & Uscite — orchestratore del terzo tab Cassa.
 *
 * Architettura:
 * - Stato locale filtri (dataDa, dataA, idCliente, categoria)
 * - 2 chiamate useMovements (tipo=ENTRATA, tipo=USCITA) — cachate indipendentemente
 * - Filtro categoria client-side (dataset piccolo per un trainer)
 * - Layout: grid 1 col (mobile) → 2 col (desktop)
 *
 * Default: primo e ultimo giorno del mese corrente.
 */

import { useState, useMemo } from "react";
import { format } from "date-fns";

import { Skeleton } from "@/components/ui/skeleton";
import { AdvancedFilters, type FiltersState } from "./AdvancedFilters";
import { LedgerColumn } from "./LedgerColumn";
import { useMovements } from "@/hooks/useMovements";
import { useClients } from "@/hooks/useClients";

// ── Helpers ──

function startOfMonth(): Date {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function endOfMonth(): Date {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

function toISODate(d: Date | undefined): string | undefined {
  if (!d) return undefined;
  return format(d, "yyyy-MM-dd");
}

// ════════════════════════════════════════════════════════════
// Componente
// ════════════════════════════════════════════════════════════

export function SplitLedgerView() {
  // ── Filtri ──
  const [filters, setFilters] = useState<FiltersState>({
    dataDa: startOfMonth(),
    dataA: endOfMonth(),
    idCliente: undefined,
    categoria: undefined,
  });

  // ── Data fetching ──
  const sharedParams = {
    data_da: toISODate(filters.dataDa),
    data_a: toISODate(filters.dataA),
    id_cliente: filters.idCliente,
    pageSize: 200,
  };

  const {
    data: entrateData,
    isLoading: entrateLoading,
  } = useMovements({ ...sharedParams, tipo: "ENTRATA" });

  const {
    data: usciteData,
    isLoading: usciteLoading,
  } = useMovements({ ...sharedParams, tipo: "USCITA" });

  // Clienti per il dropdown filtro
  const { data: clientiData } = useClients();
  const clienti = useMemo(
    () =>
      (clientiData?.items ?? []).map((c) => ({
        id: c.id,
        nome: c.nome,
        cognome: c.cognome,
      })),
    [clientiData],
  );

  // ── Categorie uniche (estratte da entrambi i dataset) ──
  const categorie = useMemo(() => {
    const allMovements = [
      ...(entrateData?.items ?? []),
      ...(usciteData?.items ?? []),
    ];
    const set = new Set<string>();
    for (const m of allMovements) {
      if (m.categoria) set.add(m.categoria);
    }
    return Array.from(set).sort();
  }, [entrateData, usciteData]);

  // ── Filtro categoria client-side ──
  const entrateFiltered = useMemo(() => {
    const items = entrateData?.items ?? [];
    if (!filters.categoria) return items;
    return items.filter((m) => m.categoria === filters.categoria);
  }, [entrateData, filters.categoria]);

  const usciteFiltered = useMemo(() => {
    const items = usciteData?.items ?? [];
    if (!filters.categoria) return items;
    return items.filter((m) => m.categoria === filters.categoria);
  }, [usciteData, filters.categoria]);

  return (
    <div className="space-y-5">
      {/* ── Barra filtri ── */}
      <AdvancedFilters
        filters={filters}
        onFilterChange={setFilters}
        clienti={clienti}
        categorie={categorie}
      />

      {/* ── Due colonne ── */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Colonna Entrate */}
        {entrateLoading ? (
          <ColumnSkeleton />
        ) : (
          <LedgerColumn
            movements={entrateFiltered}
            label="Entrate"
            variant="income"
          />
        )}

        {/* Colonna Uscite */}
        {usciteLoading ? (
          <ColumnSkeleton />
        ) : (
          <LedgerColumn
            movements={usciteFiltered}
            label="Uscite"
            variant="expense"
          />
        )}
      </div>
    </div>
  );
}

// ── Skeleton colonna ──

function ColumnSkeleton() {
  return (
    <div className="rounded-xl border p-5 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-7 w-28" />
        </div>
      </div>
      <Skeleton className="h-3 w-24" />
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-1">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2 w-full" />
        </div>
      ))}
    </div>
  );
}
