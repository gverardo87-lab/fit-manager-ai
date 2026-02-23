// src/components/clients/ClientsTable.tsx
"use client";

/**
 * Tabella clienti — colonne: Nome, Contatti, Stato, Azioni.
 *
 * Include filtro client-side istantaneo: con <100 clienti per pagina,
 * il filtraggio locale e' piu' reattivo di una chiamata API.
 *
 * Il DropdownMenu nelle azioni offre "Modifica" e "Elimina".
 */

import { useState, useMemo } from "react";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Mail,
  Phone,
  Search,
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
import type { Client } from "@/types/api";

interface ClientsTableProps {
  clients: Client[];
  onEdit: (client: Client) => void;
  onDelete: (client: Client) => void;
}

export function ClientsTable({ clients, onEdit, onDelete }: ClientsTableProps) {
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
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
          <p className="text-muted-foreground">
            {search ? "Nessun risultato per la ricerca" : "Nessun cliente trovato"}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead className="hidden sm:table-cell">Contatti</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((client) => (
                <TableRow key={client.id}>
                  {/* ── Nome ── */}
                  <TableCell className="font-medium">
                    {client.cognome} {client.nome}
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
                        <span className="italic">Nessun contatto</span>
                      )}
                    </div>
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
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
