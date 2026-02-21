// src/components/clients/ClientsTable.tsx
"use client";

/**
 * Tabella clienti — colonne: Nome, Contatti, Stato, Azioni.
 *
 * Componente puro: riceve dati e callback, zero logica di business.
 * Il DropdownMenu nelle azioni offre "Modifica" e "Elimina".
 */

import { MoreHorizontal, Pencil, Trash2, Mail, Phone } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  if (clients.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
        <p className="text-muted-foreground">Nessun cliente trovato</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>Contatti</TableHead>
            <TableHead>Stato</TableHead>
            <TableHead className="w-[80px]">Azioni</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clients.map((client) => (
            <TableRow key={client.id}>
              {/* ── Nome ── */}
              <TableCell className="font-medium">
                {client.cognome} {client.nome}
              </TableCell>

              {/* ── Contatti ── */}
              <TableCell>
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
  );
}
