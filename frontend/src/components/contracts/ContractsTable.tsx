// src/components/contracts/ContractsTable.tsx
"use client";

/**
 * Tabella contratti enriched — colonne: Cliente, Pacchetto, Finanze, Crediti, Scadenza, Rate, Azioni.
 *
 * Il nome cliente arriva direttamente dal backend (ContractListResponse)
 * grazie al batch fetch. Niente piu' clientMap lato frontend.
 *
 * Colonna Finanze: progress bar versato/totale con 3 livelli colore
 *   (emerald >=80%, amber >=40%, red <40%) — pattern identico a ClientsTable.
 *
 * Colonna Rate: badge con stato pagamento derivato dalle rate (7 livelli):
 * - chiuso → grigio "Chiuso"
 * - scaduto + rate non pagate → rosso intenso "Insolvente"
 * - ha_rate_scadute → rosso "Rate in Ritardo"
 * - data_scadenza < oggi → amber "Scaduto" (contratto oltre termine)
 * - totale_versato >= prezzo_totale → verde "Saldato"
 * - rate_totali > 0 → blu "In corso (X/Y)"
 * - default → grigio "Nessuna rata"
 */

import { useState, useMemo } from "react";
import Link from "next/link";
import { format, parseISO, differenceInDays, startOfToday } from "date-fns";
import { it } from "date-fns/locale";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Search,
  FileText,
  Plus,
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
  onEdit: (contract: ContractListItem) => void;
  onDelete: (contract: ContractListItem) => void;
  onNewContract?: () => void;
}

/** Colore progress bar finanze (pattern identico a ClientsTable). */
function getFinanceBarColor(ratio: number): string {
  if (ratio >= 0.8) return "bg-emerald-500";
  if (ratio >= 0.4) return "bg-amber-500";
  return "bg-red-500";
}

function getPaymentBadge(contract: ContractListItem) {
  // Priorita' 1: contratto chiuso
  if (contract.chiuso) {
    return <Badge variant="secondary">Chiuso</Badge>;
  }

  // Priorita' 2: scaduto + rate non pagate — caso peggiore (insolvente)
  const isExpired = contract.data_scadenza &&
    differenceInDays(parseISO(contract.data_scadenza), startOfToday()) < 0;
  if (contract.ha_rate_scadute && isExpired) {
    return (
      <Badge className="bg-red-600 text-white hover:bg-red-600 dark:bg-red-700 dark:text-red-100">
        Insolvente
      </Badge>
    );
  }

  // Priorita' 3: rate scadute, ma contratto ancora in corso
  if (contract.ha_rate_scadute) {
    return (
      <Badge className="bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400">
        Rate in Ritardo
      </Badge>
    );
  }

  // Priorita' 4: contratto oltre data_scadenza (termine scaduto, rate ok)
  if (isExpired) {
    return (
      <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400">
        Scaduto
      </Badge>
    );
  }

  // Priorita' 5: tutto pagato
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

  // Priorita' 6: in corso con progress rate
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

/** Classe CSS per urgenza colonna scadenza. */
function getScadenzaStyle(contract: ContractListItem): string {
  if (!contract.data_scadenza || contract.chiuso) return "";
  const days = differenceInDays(parseISO(contract.data_scadenza), startOfToday());
  if (days < 0) return "text-red-600 font-medium";
  if (days <= 7) return "text-amber-600 font-medium";
  if (days <= 30) return "text-amber-500";
  return "";
}

export function ContractsTable({
  contracts,
  onEdit,
  onDelete,
  onNewContract,
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
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-12">
          <FileText className="h-12 w-12 text-muted-foreground/30" />
          <p className="text-lg font-medium">
            {search ? "Nessun risultato" : "Nessun contratto"}
          </p>
          <p className="text-sm text-muted-foreground">
            {search
              ? "Prova a cercare con un termine diverso"
              : "Inizia aggiungendo il primo contratto per un cliente"}
          </p>
          {!search && onNewContract && (
            <Button size="sm" onClick={onNewContract} className="mt-1">
              <Plus className="mr-2 h-4 w-4" />
              Nuovo Contratto
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead className="hidden md:table-cell">Pacchetto</TableHead>
                <TableHead className="hidden sm:table-cell">Finanze</TableHead>
                <TableHead className="hidden lg:table-cell text-center">Crediti</TableHead>
                <TableHead className="hidden md:table-cell">Scadenza</TableHead>
                <TableHead>Rate</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((contract) => (
                <TableRow key={contract.id}>
                  {/* ── Cliente (link a scheda contratto) ── */}
                  <TableCell className="font-medium">
                    <Link href={`/contratti/${contract.id}`} className="hover:underline">
                      {contract.client_cognome} {contract.client_nome}
                    </Link>
                  </TableCell>

                  {/* ── Pacchetto (hidden mobile) ── */}
                  <TableCell className="hidden md:table-cell">{contract.tipo_pacchetto ?? "—"}</TableCell>

                  {/* ── Finanze (hidden mobile) — progress bar ── */}
                  <TableCell className="hidden sm:table-cell">
                    {contract.prezzo_totale ? (() => {
                      const prezzo = contract.prezzo_totale!;
                      const versato = contract.totale_versato;
                      const ratio = prezzo > 0 ? versato / prezzo : 0;
                      return (
                        <div className="w-28 space-y-1">
                          <div className="flex items-baseline justify-between text-[11px]">
                            <span className="font-semibold tabular-nums">
                              {formatCurrency(versato)}
                            </span>
                            <span className="text-muted-foreground">
                              / {formatCurrency(prezzo)}
                            </span>
                          </div>
                          <div className="h-1.5 w-full rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div
                              className={`h-1.5 rounded-full transition-all ${getFinanceBarColor(ratio)}`}
                              style={{ width: `${Math.min(ratio * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })() : (
                      <span className="text-sm italic text-muted-foreground">—</span>
                    )}
                  </TableCell>

                  {/* ── Crediti (hidden mobile/tablet) ── */}
                  <TableCell className="hidden lg:table-cell text-center">
                    <span className="font-mono text-sm">
                      {contract.crediti_usati}/{contract.crediti_totali ?? 0}
                    </span>
                  </TableCell>

                  {/* ── Scadenza (hidden mobile) — color-coded per urgenza ── */}
                  <TableCell className={`hidden md:table-cell ${getScadenzaStyle(contract)}`}>
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
                        <DropdownMenuItem asChild>
                          <Link href={`/contratti/${contract.id}`}>
                            <FileText className="mr-2 h-4 w-4" />
                            Dettagli
                          </Link>
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
