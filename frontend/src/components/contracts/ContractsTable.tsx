// src/components/contracts/ContractsTable.tsx
"use client";

/**
 * Tabella contratti — colonne: Cliente, Pacchetto, Importo, Crediti, Scadenza, Stato, Azioni.
 *
 * Il nome cliente viene risolto dalla mappa clientMap (id → nome),
 * passata dal parent che ha gia' caricato i clienti.
 *
 * Filtro client-side istantaneo su pacchetto e nome cliente.
 */

import { useState, useMemo } from "react";
import { format, parseISO, isPast } from "date-fns";
import { it } from "date-fns/locale";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Search,
  CreditCard,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Contract } from "@/types/api";

interface ContractsTableProps {
  contracts: Contract[];
  clientMap: Map<number, string>;
  onEdit: (contract: Contract) => void;
  onDelete: (contract: Contract) => void;
}

function formatCurrency(amount: number | null): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

function getStatusBadge(contract: Contract) {
  if (contract.chiuso) {
    return (
      <Badge variant="secondary">Chiuso</Badge>
    );
  }
  if (contract.data_scadenza && isPast(parseISO(contract.data_scadenza))) {
    return (
      <Badge className="bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400">
        Scaduto
      </Badge>
    );
  }
  if (contract.stato_pagamento === "SALDATO") {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
        Saldato
      </Badge>
    );
  }
  if (contract.stato_pagamento === "PARZIALE") {
    return (
      <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400">
        Parziale
      </Badge>
    );
  }
  return (
    <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400">
      Attivo
    </Badge>
  );
}

export function ContractsTable({
  contracts,
  clientMap,
  onEdit,
  onDelete,
}: ContractsTableProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return contracts;

    const q = search.toLowerCase();
    return contracts.filter((c) => {
      const clientName = clientMap.get(c.id_cliente) ?? "";
      return (
        clientName.toLowerCase().includes(q) ||
        c.tipo_pacchetto?.toLowerCase().includes(q)
      );
    });
  }, [contracts, clientMap, search]);

  return (
    <div className="space-y-4">
      {/* ── Barra ricerca ── */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Cerca per cliente o pacchetto..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
          <p className="text-muted-foreground">
            {search ? "Nessun risultato per la ricerca" : "Nessun contratto trovato"}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Pacchetto</TableHead>
                <TableHead className="text-right">Importo</TableHead>
                <TableHead className="text-center">Crediti</TableHead>
                <TableHead>Scadenza</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((contract) => (
                <TableRow key={contract.id}>
                  {/* ── Cliente ── */}
                  <TableCell className="font-medium">
                    {clientMap.get(contract.id_cliente) ?? `Cliente #${contract.id_cliente}`}
                  </TableCell>

                  {/* ── Pacchetto ── */}
                  <TableCell>{contract.tipo_pacchetto ?? "—"}</TableCell>

                  {/* ── Importo (versato / totale) ── */}
                  <TableCell className="text-right">
                    <div className="flex flex-col items-end">
                      <span className="font-medium">
                        {formatCurrency(contract.prezzo_totale)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        <CreditCard className="mr-1 inline h-3 w-3" />
                        {formatCurrency(contract.totale_versato)} versati
                      </span>
                    </div>
                  </TableCell>

                  {/* ── Crediti (usati / totali) ── */}
                  <TableCell className="text-center">
                    <span className="font-mono text-sm">
                      {contract.crediti_usati}/{contract.crediti_totali ?? 0}
                    </span>
                  </TableCell>

                  {/* ── Scadenza ── */}
                  <TableCell>
                    {contract.data_scadenza
                      ? format(parseISO(contract.data_scadenza), "dd MMM yyyy", { locale: it })
                      : "—"}
                  </TableCell>

                  {/* ── Stato ── */}
                  <TableCell>{getStatusBadge(contract)}</TableCell>

                  {/* ── Azioni ── */}
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">Azioni</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onEdit(contract)}>
                          <Pencil className="mr-2 h-4 w-4" />
                          Modifica
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => onDelete(contract)}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Elimina
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
