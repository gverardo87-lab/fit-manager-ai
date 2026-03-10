// src/components/clients/profile/MovimentiTab.tsx
"use client";

import { format } from "date-fns";
import { it } from "date-fns/locale";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Wallet } from "lucide-react";
import { useMovements } from "@/hooks/useMovements";
import { formatCurrency } from "@/lib/format";
import { TabSkeleton, EmptyTab } from "./ProfileShared";
import type { CashMovement } from "@/types/api";

export function MovimentiTab({ clientId }: { clientId: number }) {
  const { data, isLoading } = useMovements({ id_cliente: clientId });

  if (isLoading) return <TabSkeleton />;

  const movements = data?.items ?? [];

  if (movements.length === 0) {
    return (
      <EmptyTab
        icon={Wallet}
        message="Nessun movimento registrato"
        hint="I movimenti vengono creati automaticamente dai pagamenti delle rate o manualmente dalla Cassa."
        action={{ label: "Vai a Cassa", href: "/cassa" }}
      />
    );
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Importo</TableHead>
            <TableHead>Metodo</TableHead>
            <TableHead className="hidden sm:table-cell">Note</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {movements.map((m: CashMovement) => (
            <TableRow key={m.id}>
              <TableCell className="tabular-nums">
                {m.data_effettiva
                  ? format(new Date(m.data_effettiva + "T00:00:00"), "dd MMM yyyy", { locale: it })
                  : "—"}
              </TableCell>
              <TableCell>
                <Badge
                  variant="outline"
                  className={
                    m.tipo === "ENTRATA"
                      ? "border-emerald-300 text-emerald-700 dark:border-emerald-700 dark:text-emerald-400"
                      : "border-red-300 text-red-700 dark:border-red-700 dark:text-red-400"
                  }
                >
                  {m.tipo}
                </Badge>
              </TableCell>
              <TableCell className="font-medium tabular-nums">
                {formatCurrency(m.importo)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {m.metodo ?? "—"}
              </TableCell>
              <TableCell className="hidden sm:table-cell text-sm text-muted-foreground truncate max-w-[200px]">
                {m.note ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
