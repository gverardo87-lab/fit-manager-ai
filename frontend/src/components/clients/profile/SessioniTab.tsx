// src/components/clients/profile/SessioniTab.tsx
"use client";

import { format } from "date-fns";
import { it } from "date-fns/locale";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Calendar } from "lucide-react";
import { useClientEvents, type EventHydrated } from "@/hooks/useAgenda";
import { TabSkeleton, EmptyTab } from "./ProfileShared";

export function SessioniTab({ clientId }: { clientId: number }) {
  const { data, isLoading } = useClientEvents(clientId);

  if (isLoading) return <TabSkeleton />;

  const events = data?.items ?? [];

  if (events.length === 0) {
    return (
      <EmptyTab
        icon={Calendar}
        message="Nessuna sessione registrata"
        hint="Le sessioni si creano dall'Agenda e vengono collegate automaticamente."
        action={{ label: "Apri Agenda", href: `/agenda?newEvent=1&clientId=${clientId}` }}
      />
    );
  }

  const sorted = [...events].sort(
    (a, b) => b.data_inizio.getTime() - a.data_inizio.getTime()
  );

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Titolo</TableHead>
            <TableHead>Categoria</TableHead>
            <TableHead>Stato</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((e: EventHydrated) => (
            <TableRow key={e.id}>
              <TableCell className="tabular-nums">
                {format(e.data_inizio, "dd MMM yyyy HH:mm", { locale: it })}
              </TableCell>
              <TableCell className="font-medium">{e.titolo ?? "—"}</TableCell>
              <TableCell>
                <Badge variant="outline">{e.categoria}</Badge>
              </TableCell>
              <TableCell>
                <Badge
                  variant="secondary"
                  className={
                    e.stato === "Completato"
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                      : e.stato === "Cancellato"
                      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                      : ""
                  }
                >
                  {e.stato}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
