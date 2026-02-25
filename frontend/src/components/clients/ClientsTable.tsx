// src/components/clients/ClientsTable.tsx
"use client";

/**
 * Tabella clienti enriched — 7 colonne responsive con dati da batch queries.
 *
 * Colonne:
 * - Nome (sempre) — cognome nome + icona nota interna
 * - Contatti (hidden sm) — email + telefono con icone
 * - Finanze (hidden md) — progress bar versato/totale
 * - Crediti (hidden lg) — badge emerald/zinc
 * - Ultimo Evento (hidden lg) — data formattata o "Mai"
 * - Stato (sempre) — badge Attivo/Inattivo
 * - Azioni (sempre) — dropdown Modifica/Elimina
 *
 * Filtro client-side istantaneo su nome/email.
 */

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Mail,
  Phone,
  Search,
  StickyNote,
  Users,
  Plus,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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
import { formatCurrency, formatShortDate, getFinanceBarColor } from "@/lib/format";
import type { ClientEnriched } from "@/types/api";

// ── Component ──

interface ClientsTableProps {
  clients: ClientEnriched[];
  onEdit: (client: ClientEnriched) => void;
  onDelete: (client: ClientEnriched) => void;
  onNewClient?: () => void;
}

export function ClientsTable({ clients, onEdit, onDelete, onNewClient }: ClientsTableProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return clients;

    const q = search.toLowerCase();
    return clients.filter(
      (c) =>
        c.nome.toLowerCase().includes(q) ||
        c.cognome.toLowerCase().includes(q) ||
        c.email?.toLowerCase().includes(q)
    );
  }, [clients, search]);

  return (
    <div className="space-y-4">
      {/* ── Barra ricerca ── */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Cerca cliente per nome o email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* ── Tabella o empty state ── */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Users className="h-6 w-6 text-muted-foreground/50" />
          </div>
          <div className="text-center">
            <p className="font-medium text-muted-foreground">
              {search ? "Nessun risultato per la ricerca" : "Nessun cliente nel portafoglio"}
            </p>
            {!search && (
              <p className="mt-1 text-sm text-muted-foreground/70">
                Aggiungi il primo cliente per iniziare
              </p>
            )}
          </div>
          {!search && onNewClient && (
            <Button variant="outline" size="sm" onClick={onNewClient} className="mt-1">
              <Plus className="mr-2 h-4 w-4" />
              Nuovo Cliente
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead className="hidden sm:table-cell">Contatti</TableHead>
                <TableHead className="hidden md:table-cell">Finanze</TableHead>
                <TableHead className="hidden lg:table-cell text-center">Crediti</TableHead>
                <TableHead className="hidden lg:table-cell">Ultimo Evento</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((client) => {
                const hasContracts = client.contratti_attivi > 0;
                const prezzo = client.prezzo_totale_attivo;
                const versato = client.totale_versato;
                const ratio = prezzo > 0 ? versato / prezzo : 0;

                return (
                  <TableRow key={client.id}>
                    {/* ── Nome + nota + dot rate scadute ── */}
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-1.5">
                        <Link href={`/clienti/${client.id}`} className="hover:underline">
                          {client.cognome} {client.nome}
                        </Link>
                        {client.ha_rate_scadute && (
                          <span className="h-2 w-2 shrink-0 rounded-full bg-red-500" title="Rate scadute" />
                        )}
                        {client.note_interne && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <StickyNote className="h-3.5 w-3.5 shrink-0 text-amber-500/70" />
                              </TooltipTrigger>
                              <TooltipContent side="right" className="max-w-[250px]">
                                <p className="whitespace-pre-line text-xs line-clamp-4">
                                  {client.note_interne}
                                </p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </TableCell>

                    {/* ── Contatti (hidden su mobile) ── */}
                    <TableCell className="hidden sm:table-cell">
                      <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                        {client.email && (
                          <span className="flex items-center gap-1.5">
                            <Mail className="h-3.5 w-3.5" />
                            {client.email}
                          </span>
                        )}
                        {client.telefono && (
                          <span className="flex items-center gap-1.5">
                            <Phone className="h-3.5 w-3.5" />
                            {client.telefono}
                          </span>
                        )}
                        {!client.email && !client.telefono && (
                          <span className="italic">—</span>
                        )}
                      </div>
                    </TableCell>

                    {/* ── Finanze (hidden md) — progress bar ── */}
                    <TableCell className="hidden md:table-cell">
                      {hasContracts ? (
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
                      ) : (
                        <span className="text-sm italic text-muted-foreground">—</span>
                      )}
                    </TableCell>

                    {/* ── Crediti (hidden lg) ── */}
                    <TableCell className="hidden lg:table-cell text-center">
                      <Badge
                        variant="secondary"
                        className={
                          client.crediti_residui > 0
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                            : ""
                        }
                      >
                        {client.crediti_residui}
                      </Badge>
                    </TableCell>

                    {/* ── Ultimo Evento (hidden lg) ── */}
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                      {client.ultimo_evento_data ? (
                        formatShortDate(client.ultimo_evento_data)
                      ) : (
                        <span className="italic">Mai</span>
                      )}
                    </TableCell>

                    {/* ── Stato ── */}
                    <TableCell>
                      <Badge
                        variant={client.stato === "Attivo" ? "default" : "secondary"}
                        className={
                          client.stato === "Attivo"
                            ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400"
                            : ""
                        }
                      >
                        {client.stato}
                      </Badge>
                    </TableCell>

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
                          <DropdownMenuItem onClick={() => onEdit(client)}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Modifica
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => onDelete(client)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Elimina
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
