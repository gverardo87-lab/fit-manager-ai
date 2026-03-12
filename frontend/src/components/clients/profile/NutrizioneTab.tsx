// src/components/clients/profile/NutrizioneTab.tsx
"use client";

/**
 * Tab Nutrizione nel profilo cliente.
 *
 * Pattern identico a SchedeTab: tabella semplice dei piani,
 * click su riga → /nutrizione/[id]?from=clienti-{clientId},
 * bottone "Nuovo piano" apre NutritionPlanSheet inline.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UtensilsCrossed, Plus } from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useNutritionPlans } from "@/hooks/useNutrition";
import { NutritionPlanSheet } from "@/components/nutrition/NutritionPlanSheet";
import { TabSkeleton } from "./ProfileShared";

interface NutrizioneTabProps {
  clientId: number;
}

export function NutrizioneTab({ clientId }: NutrizioneTabProps) {
  const router = useRouter();
  const [sheetOpen, setSheetOpen] = useState(false);
  const { data: plans, isLoading } = useNutritionPlans(clientId);

  if (isLoading) return <TabSkeleton />;

  const planList = plans ?? [];

  if (planList.length === 0) {
    return (
      <>
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
          <UtensilsCrossed className="h-10 w-10 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">Nessun piano alimentare</p>
          <p className="text-xs text-muted-foreground/70">Crea il primo piano nutrizionale per questo cliente</p>
          <Button variant="outline" size="sm" onClick={() => setSheetOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Crea Piano Alimentare
          </Button>
        </div>
        <NutritionPlanSheet
          open={sheetOpen}
          onOpenChange={setSheetOpen}
          clientId={clientId}
          plan={null}
        />
      </>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={() => setSheetOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo piano
        </Button>
      </div>
      <div className="rounded-lg border bg-white dark:bg-zinc-900">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead className="hidden sm:table-cell">Stato</TableHead>
              <TableHead className="hidden sm:table-cell">Target kcal</TableHead>
              <TableHead className="hidden md:table-cell">Inizio</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {planList.map((p) => (
              <TableRow
                key={p.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/nutrizione/${p.id}?from=clienti-${clientId}`)}
              >
                <TableCell className="font-medium">{p.nome}</TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Badge
                    variant="outline"
                    className={`text-xs ${p.attivo ? "border-emerald-200 text-emerald-700 bg-emerald-50" : ""}`}
                  >
                    {p.attivo ? "Attivo" : "Inattivo"}
                  </Badge>
                </TableCell>
                <TableCell className="hidden sm:table-cell tabular-nums text-sm text-muted-foreground">
                  {p.obiettivo_calorico ? `${p.obiettivo_calorico} kcal` : "—"}
                </TableCell>
                <TableCell className="hidden md:table-cell text-sm text-muted-foreground tabular-nums">
                  {p.data_inizio
                    ? format(new Date(p.data_inizio), "dd MMM yyyy", { locale: it })
                    : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex justify-end">
        <button
          className="text-xs text-primary hover:underline"
          onClick={() => router.push(`/nutrizione?idCliente=${clientId}`)}
        >
          Vedi tutti i piani →
        </button>
      </div>
      <NutritionPlanSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        clientId={clientId}
        plan={null}
      />
    </div>
  );
}
