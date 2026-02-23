// src/components/contracts/ContractsTable.tsx
"use client";

/**
 * Tabella contratti enriched — colonne: Cliente, Pacchetto, Importo, Crediti, Scadenza, Rate, Azioni.
 *
 * Il nome cliente arriva direttamente dal backend (ContractListResponse)
 * grazie al batch fetch. Niente piu' clientMap lato frontend.
 *
 * Colonna Rate: badge con stato pagamento derivato dalle rate:
 * - ha_rate_scadute → rosso "Scaduto"
 * - totale_versato >= prezzo_totale → verde "Saldato"
 * - altrimenti → blu "In corso (X/Y)"
 */

import { useState, useMemo } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Search,
  CreditCard,
  Settings2,
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
import type { ContractListItem } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface ContractsTableProps {
  contracts: ContractListItem[];
  onManage: (contract: ContractListItem) => void;
  onEdit: (contract: ContractListItem) => void;
  onDelete: (contract: ContractListItem) => void;
}

function formatCurrencyNullable(amount: number | null): string {
  if (amount == null) return "—";
  return formatCurrency(amount);
}

function getPaymentBadge(contract: ContractListItem) {
  // Priorita' 1: contratto chiuso
  if (contract.chiuso) {
    return <Badge variant="secondary">Chiuso</Badge>;
  }

  // Priorita' 2: rate scadute non pagate
  if (contract.ha_rate_scadute) {
    return (
      <Badge className="bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400">
        Scaduto
      </Badge>
    );
  }

  // Priorita' 3: tutto pagato
  if (
    contract.prezzo_totale &&
    contract.totale_versato >= contract.prezzo_totale - 0.01
  ) {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
        Saldato
      </Badge>
    );
  }

  // Priorita' 4: in corso con progress rate
  if (contract.rate_totali > 0) {
    return (
      <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400">
        In corso ({contract.rate_pagate}/{contract.rate_totali})
      </Badge>
    );
  }

  // Nessuna rata creata
  return (
    <Badge className="bg-zinc-100 text-zinc-600 hover:bg-zinc-100 dark:bg-zinc-800 dark:text-zinc-400">
      Nessuna rata
    </Badge>
  );
}

export function ContractsTable({
  contracts,
  onManage,
  onEdit,
  onDelete,
}: ContractsTableProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return contracts;

    const q = search.toLowerCase();
    return contracts.filter((c) => {
      const clientName = `${c.client_cognome} ${c.client_nome}`.toLowerCase();
      return (
        clientName.includes(q) ||
        c.tipo_pacchetto?.toLowerCase().includes(q)
      );
    });
  }, [contracts, search]);

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
                <TableHead className="hidden md:table-cell">Pacchetto</TableHead>
                <TableHead className="text-right">Importo</TableHead>
                <TableHead className="hidden lg:table-cell text-center">Crediti</TableHead>
                <TableHead className="hidden md:table-cell">Scadenza</TableHead>
                <TableHead>Rate</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((contract) => (
                <TableRow key={contract.id}>
                  {/* ── Cliente ── */}
                  <TableCell className="font-medium">
                    {contract.client_cognome} {contract.client_nome}
                  </TableCell>

                  {/* ── Pacchetto (hidden mobile) ── */}
                  <TableCell className="hidden md:table-cell">{contract.tipo_pacchetto ?? "—"}</TableCell>

                  {/* ── Importo (versato / totale) ── */}
                  <TableCell className="text-right">
                    <div className="flex flex-col items-end">
                      <span className="font-medium">
                        {formatCurrencyNullable(contract.prezzo_totale)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        <CreditCard className="mr-1 inline h-3 w-3" />
                        {formatCurrency(contract.totale_versato)} versati
                      </span>
                    </div>
                  </TableCell>

                  {/* ── Crediti (hidden mobile/tablet) ── */}
                  <TableCell className="hidden lg:table-cell text-center">
                    <span className="font-mono text-sm">
                      {contract.crediti_usati}/{contract.crediti_totali ?? 0}
                    </span>
                  </TableCell>

                  {/* ── Scadenza (hidden mobile) ── */}
                  <TableCell className="hidden md:table-cell">
                    {contract.data_scadenza
                      ? format(parseISO(contract.data_scadenza), "dd MMM yyyy", { locale: it })
                      : "—"}
                  </TableCell>

                  {/* ── Rate (payment badge) ── */}
                  <TableCell>{getPaymentBadge(contract)}</TableCell>

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
                        <DropdownMenuItem onClick={() => onManage(contract)}>
                          <Settings2 className="mr-2 h-4 w-4" />
                          Gestisci
                        </DropdownMenuItem>
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
