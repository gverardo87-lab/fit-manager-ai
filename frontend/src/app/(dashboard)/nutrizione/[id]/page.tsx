// src/app/(dashboard)/nutrizione/[id]/page.tsx
"use client";

/**
 * Dettaglio piano alimentare — full-page editor.
 *
 * Mostra:
 * - Header: nome piano + cliente + date + stato + bottone "Modifica"
 * - Target macro (se impostati) vs media calcolata
 * - PlanDetailPanel: giorni × pasti × alimenti (con add/delete inline)
 *
 * Pattern: identico a /schede/[id] per navigazione (back via ?from).
 * Usa GET /nutrition/plans/{plan_id} (no clientId richiesto).
 */

import { use, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Pencil, UtensilsCrossed, CalendarRange, User } from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { useNutritionPlanById } from "@/hooks/useNutrition";
import { PlanDetailPanel } from "@/components/nutrition/PlanDetailPanel";
import { NutritionPlanSheet } from "@/components/nutrition/NutritionPlanSheet";
import { useClients } from "@/hooks/useClients";
import { resolveBackNavigation } from "@/lib/url-state";

// ── Macro bar ─────────────────────────────────────────────────────────────

function MacroBar({
  label, actual, target, color,
}: { label: string; actual: number; target: number | null; color: string }) {
  const pct = target ? Math.min(100, Math.round((actual / target) * 100)) : null;
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="tabular-nums font-medium">
          {Math.round(actual)}g{target ? ` / ${target}g` : ""}
        </span>
      </div>
      {pct !== null && (
        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full ${color}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}

// ── Pagina ─────────────────────────────────────────────────────────────────

export default function NutritionPlanPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const planId = parseInt(id, 10);
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromParam = searchParams.get("from");

  const [editOpen, setEditOpen] = useState(false);

  const backNav = resolveBackNavigation(fromParam, { href: "/nutrizione", label: "Torna ai piani" });

  const { data: planDetail, isLoading } = useNutritionPlanById(planId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!planDetail) {
    return (
      <div className="flex flex-col items-center gap-3 py-16">
        <UtensilsCrossed className="h-10 w-10 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">Piano non trovato</p>
        <Button variant="outline" size="sm" onClick={() => router.push("/nutrizione")}>
          Torna ai piani
        </Button>
      </div>
    );
  }

  const clientId = planDetail.id_cliente;

  return (
    <div className="space-y-5">
      {/* ── Back ── */}
      <Button
        variant="ghost"
        size="sm"
        className="gap-1.5 text-muted-foreground hover:text-foreground -ml-2"
        onClick={() => router.push(backNav.href)}
      >
        <ArrowLeft className="h-4 w-4" />
        {backNav.label}
      </Button>

      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl font-bold truncate">{planDetail.nome}</h1>
            <Badge
              variant="outline"
              className={`text-xs shrink-0 ${planDetail.attivo ? "border-emerald-500 text-emerald-600" : "text-muted-foreground"}`}
            >
              {planDetail.attivo ? "Attivo" : "Inattivo"}
            </Badge>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <User className="h-3.5 w-3.5" />
              <ClientName clientId={clientId} />
            </span>
            {(planDetail.data_inizio || planDetail.data_fine) && (
              <span className="flex items-center gap-1">
                <CalendarRange className="h-3.5 w-3.5" />
                {planDetail.data_inizio
                  ? format(new Date(planDetail.data_inizio), "d MMM yyyy", { locale: it })
                  : "—"}
                {" → "}
                {planDetail.data_fine
                  ? format(new Date(planDetail.data_fine), "d MMM yyyy", { locale: it })
                  : "in corso"}
              </span>
            )}
          </div>
        </div>
        <Button variant="outline" size="sm" className="shrink-0" onClick={() => setEditOpen(true)}>
          <Pencil className="mr-2 h-3.5 w-3.5" />
          Modifica piano
        </Button>
      </div>

      {/* ── Target macro ── */}
      {(planDetail.obiettivo_calorico || planDetail.proteine_g_target) && (
        <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Target macro / die
            </p>
            {planDetail.totale_kcal != null && planDetail.totale_kcal > 0 && (
              <span className="text-xs text-muted-foreground">
                Media calcolata: <span className="font-medium text-foreground">{Math.round(planDetail.totale_kcal)} kcal</span>
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {planDetail.proteine_g_target && (
              <MacroBar
                label="Proteine"
                actual={planDetail.totale_proteine_g ?? 0}
                target={planDetail.proteine_g_target}
                color="bg-blue-500"
              />
            )}
            {planDetail.carboidrati_g_target && (
              <MacroBar
                label="Carboidrati"
                actual={planDetail.totale_carboidrati_g ?? 0}
                target={planDetail.carboidrati_g_target}
                color="bg-amber-500"
              />
            )}
            {planDetail.grassi_g_target && (
              <MacroBar
                label="Grassi"
                actual={planDetail.totale_grassi_g ?? 0}
                target={planDetail.grassi_g_target}
                color="bg-rose-400"
              />
            )}
          </div>
          {planDetail.note_cliniche && (
            <>
              <Separator className="my-1" />
              <p className="text-xs text-muted-foreground italic">{planDetail.note_cliniche}</p>
            </>
          )}
        </div>
      )}

      {/* ── Piano dettaglio (pasti + alimenti) ── */}
      <PlanDetailPanel planId={planId} clientId={clientId} />

      {/* ── Sheet modifica ── */}
      <NutritionPlanSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        clientId={clientId}
        plan={planDetail}
      />
    </div>
  );
}

// ── Client name helper ────────────────────────────────────────────────────

function ClientName({ clientId }: { clientId: number }) {
  const { data: clients } = useClients();
  const list = Array.isArray(clients) ? clients : (clients as { items?: { id: number; nome: string; cognome: string }[] })?.items ?? [];
  const client = list.find((c) => c.id === clientId);
  return <>{client ? `${client.cognome} ${client.nome}` : `Cliente #${clientId}`}</>;
}
