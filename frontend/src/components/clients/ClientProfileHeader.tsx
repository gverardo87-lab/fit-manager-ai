// src/components/clients/ClientProfileHeader.tsx
"use client";

/**
 * Header persistente per la pagina profilo cliente.
 *
 * Layout: Indietro | Avatar + Nome + Badge Stato | Contatti | Modifica
 */

import Link from "next/link";
import {
  ArrowLeft,
  Mail,
  Phone,
  Pencil,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClientEnriched } from "@/types/api";

interface ClientProfileHeaderProps {
  client: ClientEnriched;
  onEdit: () => void;
}

export function ClientProfileHeader({ client, onEdit }: ClientProfileHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      {/* ── Left: back + avatar + identity ── */}
      <div className="flex items-center gap-4">
        <Link
          href="/clienti"
          className="flex h-9 w-9 items-center justify-center rounded-lg border bg-background transition-colors hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>

        {/* Avatar */}
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-lg font-semibold text-primary">
          {client.cognome[0]}
          {client.nome[0]}
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold">
              {client.cognome} {client.nome}
            </h1>
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
          </div>

          {/* Contatti inline */}
          <div className="mt-0.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
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
          </div>
        </div>
      </div>

      {/* ── Right: edit button ── */}
      <Button variant="outline" size="sm" onClick={onEdit}>
        <Pencil className="mr-2 h-4 w-4" />
        Modifica
      </Button>
    </div>
  );
}
