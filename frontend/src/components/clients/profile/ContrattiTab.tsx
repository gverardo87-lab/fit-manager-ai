// src/components/clients/profile/ContrattiTab.tsx
"use client";

import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { FileText } from "lucide-react";
import { useClientContracts } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import { TabSkeleton, EmptyTab } from "./ProfileShared";
import type { ContractListItem } from "@/types/api";

export function ContrattiTab({ clientId }: { clientId: number }) {
  const router = useRouter();
  const { data, isLoading } = useClientContracts(clientId);

  if (isLoading) return <TabSkeleton />;

  const contracts = data?.items ?? [];

  if (contracts.length === 0) {
    return (
      <EmptyTab
        icon={FileText}
        message="Nessun contratto attivo"
        hint="Il contratto definisce il pacchetto, i crediti e il piano pagamento."
        action={{ label: "Vai a Contratti", href: `/contratti?new=1&cliente=${clientId}` }}
      />
    );
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Pacchetto</TableHead>
            <TableHead>Finanze</TableHead>
            <TableHead className="text-center">Crediti</TableHead>
            <TableHead>Stato</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contracts.map((c: ContractListItem) => {
            const prezzo = c.prezzo_totale ?? 0;
            return (
              <TableRow key={c.id} className="cursor-pointer hover:bg-muted/50" onClick={() => router.push(`/contratti/${c.id}?from=clienti-${clientId}`)}>
                <TableCell className="font-medium">{c.tipo_pacchetto ?? "—"}</TableCell>
                <TableCell>
                  {prezzo > 0 ? (
                    <span className="text-sm tabular-nums">
                      {formatCurrency(c.totale_versato)} / {formatCurrency(prezzo)}
                    </span>
                  ) : "—"}
                </TableCell>
                <TableCell className="text-center">
                  <span className="font-mono text-sm">{c.crediti_usati}/{c.crediti_totali ?? 0}</span>
                </TableCell>
                <TableCell>
                  {c.chiuso ? (
                    <Badge variant="secondary">Chiuso</Badge>
                  ) : c.ha_rate_scadute ? (
                    <Badge className="bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400">
                      Rate in Ritardo
                    </Badge>
                  ) : (
                    <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
                      Attivo
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
