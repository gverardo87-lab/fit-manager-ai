// src/components/clients/profile/SchedeTab.tsx
"use client";

import { format } from "date-fns";
import { it } from "date-fns/locale";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ClipboardList, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useClientWorkouts } from "@/hooks/useWorkouts";
import { getProgramStatus, STATUS_LABELS, STATUS_COLORS } from "@/lib/workout-monitoring";
import { TabSkeleton } from "./ProfileShared";
import type { WorkoutPlan } from "@/types/api";

interface SchedeTabProps {
  clientId: number;
  onNewScheda: () => void;
}

export function SchedeTab({ clientId, onNewScheda }: SchedeTabProps) {
  const router = useRouter();
  const { data, isLoading } = useClientWorkouts(clientId);

  if (isLoading) return <TabSkeleton />;

  const workouts = data?.items ?? [];

  if (workouts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <ClipboardList className="h-10 w-10 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">Nessuna scheda per questo cliente</p>
        <Button variant="outline" size="sm" onClick={onNewScheda}>
          <Plus className="mr-2 h-4 w-4" />
          Crea Scheda
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={onNewScheda}>
          <Plus className="mr-2 h-4 w-4" />
          Nuova Scheda
        </Button>
      </div>
      <div className="rounded-lg border bg-white dark:bg-zinc-900">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Obiettivo</TableHead>
              <TableHead className="hidden sm:table-cell">Livello</TableHead>
              <TableHead className="text-center hidden sm:table-cell">Sessioni</TableHead>
              <TableHead className="hidden sm:table-cell">Stato</TableHead>
              <TableHead className="hidden md:table-cell">Data</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {workouts.map((w: WorkoutPlan) => (
              <TableRow
                key={w.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/schede/${w.id}?from=clienti-${clientId}`)}
              >
                <TableCell className="font-medium">{w.nome}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">{w.obiettivo}</Badge>
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Badge variant="outline" className="text-xs">{w.livello}</Badge>
                </TableCell>
                <TableCell className="text-center hidden sm:table-cell tabular-nums">
                  {w.sessioni.length}
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  {(() => {
                    const status = getProgramStatus(w);
                    return (
                      <Badge className={`text-xs ${STATUS_COLORS[status]}`}>
                        {STATUS_LABELS[status]}
                      </Badge>
                    );
                  })()}
                </TableCell>
                <TableCell className="hidden md:table-cell text-sm text-muted-foreground tabular-nums">
                  {w.created_at
                    ? format(new Date(w.created_at), "dd MMM yyyy", { locale: it })
                    : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex justify-end">
        <Link
          href={`/allenamenti?idCliente=${clientId}`}
          className="text-xs text-primary hover:underline"
        >
          Vedi monitoraggio →
        </Link>
      </div>
    </div>
  );
}
