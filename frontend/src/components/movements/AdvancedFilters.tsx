// src/components/movements/AdvancedFilters.tsx
"use client";

/**
 * Barra filtri avanzati per la vista Split Entrate & Uscite.
 *
 * Filtri:
 * - DatePicker Da / A (range date)
 * - Select Cliente (da useClients)
 * - Select Categoria (estratte dai movimenti caricati)
 * - Reset filtri
 *
 * Props-driven: nessuno stato interno, il padre gestisce tutto.
 */

import { RotateCcw, Filter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface FiltersState {
  dataDa: Date | undefined;
  dataA: Date | undefined;
  idCliente: number | undefined;
  categoria: string | undefined;
}

interface AdvancedFiltersProps {
  filters: FiltersState;
  onFilterChange: (filters: FiltersState) => void;
  clienti: { id: number; nome: string; cognome: string }[];
  categorie: string[];
}

export function AdvancedFilters({
  filters,
  onFilterChange,
  clienti,
  categorie,
}: AdvancedFiltersProps) {
  const update = (partial: Partial<FiltersState>) =>
    onFilterChange({ ...filters, ...partial });

  const hasActiveFilters =
    filters.idCliente !== undefined || filters.categoria !== undefined;

  const handleReset = () =>
    onFilterChange({
      dataDa: filters.dataDa,
      dataA: filters.dataA,
      idCliente: undefined,
      categoria: undefined,
    });

  return (
    <div className="rounded-xl border bg-muted/30 p-4">
    <div className="flex flex-wrap items-end gap-3">
      {/* ── Label filtri ── */}
      <div className="flex items-center gap-1.5 self-center pb-1 text-xs font-medium text-muted-foreground">
        <Filter className="h-3.5 w-3.5" />
        <span>Filtri</span>
      </div>

      {/* ── Range date ── */}
      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">Da</label>
        <div className="w-[180px]">
          <DatePicker
            value={filters.dataDa}
            onChange={(d) => update({ dataDa: d })}
            placeholder="Data inizio..."
          />
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">A</label>
        <div className="w-[180px]">
          <DatePicker
            value={filters.dataA}
            onChange={(d) => update({ dataA: d })}
            placeholder="Data fine..."
          />
        </div>
      </div>

      {/* ── Select Cliente ── */}
      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Cliente
        </label>
        <Select
          value={filters.idCliente !== undefined ? String(filters.idCliente) : "ALL"}
          onValueChange={(v) =>
            update({ idCliente: v === "ALL" ? undefined : parseInt(v, 10) })
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Tutti i clienti" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Tutti i clienti</SelectItem>
            {clienti.map((c) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.cognome} {c.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* ── Select Categoria ── */}
      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Categoria
        </label>
        <Select
          value={filters.categoria ?? "ALL"}
          onValueChange={(v) =>
            update({ categoria: v === "ALL" ? undefined : v })
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Tutte le categorie" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Tutte le categorie</SelectItem>
            {categorie.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* ── Reset ── */}
      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={handleReset}>
          <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
          Reset
        </Button>
      )}
    </div>
    </div>
  );
}
