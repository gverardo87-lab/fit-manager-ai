// src/components/clients/profile/NutrizioneTab.tsx
"use client";

/**
 * Tab Nutrizione nel profilo cliente.
 *
 * Layout:
 * - Nessun piano: empty state con CTA "Crea piano alimentare"
 * - Piano attivo: hero card con target macro + media calcolata + delta
 * - Lista piani: cards con stato attivo/inattivo + azioni
 * - Click su piano → espande dettaglio con pasti e componenti
 *
 * > 300 LOC: diviso in NutrizioneTab (shell + lista) + PlanDetailPanel (espanso)
 */

import { useState } from "react";
import { UtensilsCrossed, Plus, ChevronDown, ChevronUp, Trash2, CheckCircle2, Circle } from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

import {
  useNutritionSummary,
  useNutritionPlans,
  useNutritionPlan,
  useDeleteNutritionPlan,
  useUpdateNutritionPlan,
} from "@/hooks/useNutrition";
import { TabSkeleton } from "./ProfileShared";
import { NutritionPlanSheet } from "@/components/nutrition/NutritionPlanSheet";
import { PlanDetailPanel } from "@/components/nutrition/PlanDetailPanel";
import type { NutritionPlan } from "@/types/api";

// ── Helpers ──────────────────────────────────────────────────────────────

function MacroBadge({ label, value, unit = "g", colorClass = "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" }: {
  label: string; value: number | null; unit?: string; colorClass?: string;
}) {
  if (value == null) return null;
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${colorClass}`}>
      <span className="opacity-70">{label}</span>
      <span className="font-semibold">{Math.round(value)}{unit}</span>
    </span>
  );
}

// ── Componente principale ─────────────────────────────────────────────────

interface NutrizioneTabProps {
  clientId: number;
}

export function NutrizioneTab({ clientId }: NutrizioneTabProps) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editPlan, setEditPlan] = useState<NutritionPlan | null>(null);
  const [expandedPlanId, setExpandedPlanId] = useState<number | null>(null);

  const { data: summary, isLoading: summaryLoading } = useNutritionSummary(clientId);
  const { data: plans, isLoading: plansLoading } = useNutritionPlans(clientId);
  const deletePlan = useDeleteNutritionPlan(clientId);
  const updatePlan = useUpdateNutritionPlan(clientId);

  const isLoading = summaryLoading || plansLoading;
  if (isLoading) return <TabSkeleton />;

  const planList = plans ?? [];

  // ── Empty state ────────────────────────────────────────────────────────
  if (planList.length === 0) {
    return (
      <>
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
          <UtensilsCrossed className="h-10 w-10 text-muted-foreground/30" />
          <p className="text-sm font-medium text-muted-foreground">Nessun piano alimentare</p>
          <p className="text-xs text-muted-foreground/70">Crea il primo piano nutrizionale per questo cliente</p>
          <Button variant="outline" size="sm" onClick={() => { setEditPlan(null); setSheetOpen(true); }}>
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

  const activePlan = summary?.piano_attivo ?? null;

  return (
    <div className="space-y-4">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Piani alimentari ({planList.length})
        </h3>
        <Button variant="outline" size="sm" onClick={() => { setEditPlan(null); setSheetOpen(true); }}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo piano
        </Button>
      </div>

      {/* ── Hero piano attivo ──────────────────────────────────────────── */}
      {summary?.ha_piano_attivo && activePlan && (
        <Card className="border-l-4 border-l-emerald-500 bg-gradient-to-br from-emerald-50/50 to-transparent dark:from-emerald-900/10">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                Piano attivo — {activePlan.nome}
              </CardTitle>
              {activePlan.data_inizio && (
                <span className="text-xs text-muted-foreground">
                  dal {format(new Date(activePlan.data_inizio), "d MMM yyyy", { locale: it })}
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* Target macro */}
            {(activePlan.obiettivo_calorico || activePlan.proteine_g_target) && (
              <div className="flex flex-wrap gap-1.5">
                <span className="text-xs text-muted-foreground">Target:</span>
                <MacroBadge label="kcal" value={activePlan.obiettivo_calorico} unit="" colorClass="bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300" />
                <MacroBadge label="P" value={activePlan.proteine_g_target} colorClass="bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300" />
                <MacroBadge label="C" value={activePlan.carboidrati_g_target} colorClass="bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300" />
                <MacroBadge label="G" value={activePlan.grassi_g_target} colorClass="bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" />
              </div>
            )}
            {/* Media calcolata */}
            {summary.media_kcal_die && (
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className="text-xs text-muted-foreground">Media/die:</span>
                <MacroBadge label="kcal" value={summary.media_kcal_die} unit="" colorClass="bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300" />
                <MacroBadge label="P" value={summary.media_proteine_g_die} colorClass="bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300" />
                <MacroBadge label="C" value={summary.media_carboidrati_g_die} colorClass="bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300" />
                <MacroBadge label="G" value={summary.media_grassi_g_die} colorClass="bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" />
                {summary.delta_kcal != null && (
                  <span className={`text-xs font-medium ${summary.delta_kcal < -100 ? "text-red-500" : summary.delta_kcal > 100 ? "text-emerald-600" : "text-muted-foreground"}`}>
                    ({summary.delta_kcal > 0 ? "+" : ""}{Math.round(summary.delta_kcal)} kcal vs target)
                  </span>
                )}
              </div>
            )}
            {activePlan.note_cliniche && (
              <p className="text-xs text-muted-foreground border-t pt-2 mt-1">{activePlan.note_cliniche}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Lista piani ────────────────────────────────────────────────── */}
      <div className="space-y-2">
        {planList.map((plan) => (
          <PlanRow
            key={plan.id}
            plan={plan}
            clientId={clientId}
            isExpanded={expandedPlanId === plan.id}
            onToggleExpand={() => setExpandedPlanId(expandedPlanId === plan.id ? null : plan.id)}
            onEdit={() => { setEditPlan(plan); setSheetOpen(true); }}
            onDelete={() => deletePlan.mutate(plan.id)}
            onToggleActive={() => updatePlan.mutate({ planId: plan.id, payload: { attivo: !plan.attivo } })}
          />
        ))}
      </div>

      <NutritionPlanSheet
        open={sheetOpen}
        onOpenChange={(v) => { setSheetOpen(v); if (!v) setEditPlan(null); }}
        clientId={clientId}
        plan={editPlan}
      />
    </div>
  );
}

// ── Riga piano ────────────────────────────────────────────────────────────

interface PlanRowProps {
  plan: NutritionPlan;
  clientId: number;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onToggleActive: () => void;
}

function PlanRow({ plan, clientId, isExpanded, onToggleExpand, onEdit, onDelete, onToggleActive }: PlanRowProps) {
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      {/* Header riga */}
      <div className="flex items-center gap-3 px-4 py-3">
        <button onClick={onToggleActive} className="shrink-0 text-muted-foreground hover:text-foreground transition-colors">
          {plan.attivo
            ? <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            : <Circle className="h-4 w-4" />}
        </button>
        <button className="flex-1 text-left" onClick={onToggleExpand}>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium">{plan.nome}</span>
            {plan.attivo && <Badge variant="outline" className="text-[10px] border-emerald-200 text-emerald-700 bg-emerald-50">Attivo</Badge>}
            {plan.obiettivo_calorico && (
              <span className="text-xs text-muted-foreground">{plan.obiettivo_calorico} kcal target</span>
            )}
          </div>
          {plan.data_inizio && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {format(new Date(plan.data_inizio), "d MMM yyyy", { locale: it })}
              {plan.data_fine && ` → ${format(new Date(plan.data_fine), "d MMM yyyy", { locale: it })}`}
            </p>
          )}
        </button>

        {/* Azioni */}
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={onEdit}>
            Modifica
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive">
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Elimina piano alimentare?</AlertDialogTitle>
                <AlertDialogDescription>
                  Questa azione elimina &quot;{plan.nome}&quot; con tutti i pasti e componenti. Non reversibile.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annulla</AlertDialogCancel>
                <AlertDialogAction onClick={onDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                  Elimina
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <button onClick={onToggleExpand} className="p-1 text-muted-foreground hover:text-foreground transition-colors">
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Dettaglio espanso */}
      {isExpanded && (
        <div className="border-t bg-muted/20 px-4 py-3">
          <PlanDetailPanel planId={plan.id} clientId={clientId} />
        </div>
      )}
    </div>
  );
}
