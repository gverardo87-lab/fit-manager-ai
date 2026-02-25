// src/components/clients/anamnesi/AnamnesiSummary.tsx
"use client";

/**
 * Vista read-only dell'anamnesi compilata.
 *
 * 4 card sezione (2x2 desktop, stack mobile) con indicatori colorati:
 * - Emerald + CheckCircle: nessun problema
 * - Red + AlertCircle: problema segnalato con dettaglio
 * - Badge per valori stile di vita
 */

import {
  CheckCircle2,
  AlertCircle,
  Pencil,
  Bone,
  Stethoscope,
  Heart,
  Target,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AnamnesiData, AnamnesiQuestion } from "@/types/api";
import {
  LIVELLI_ATTIVITA_LABELS,
  ORE_SONNO_LABELS,
  LIVELLI_STRESS_LABELS,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function QuestionRow({ label, value }: { label: string; value: AnamnesiQuestion }) {
  if (value.presente) {
    return (
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
        <div>
          <span className="text-sm font-medium text-red-700 dark:text-red-400">{label}</span>
          {value.dettaglio && (
            <p className="text-xs text-muted-foreground mt-0.5">{value.dettaglio}</p>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
      <span className="text-sm text-muted-foreground">{label}</span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge variant="outline" className="text-xs">{value}</Badge>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════

interface AnamnesiSummaryProps {
  data: AnamnesiData;
  onEdit: () => void;
}

export function AnamnesiSummary({ data, onEdit }: AnamnesiSummaryProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          Compilata il {data.data_compilazione}
          {data.data_ultimo_aggiornamento !== data.data_compilazione && (
            <> &middot; Aggiornata il {data.data_ultimo_aggiornamento}</>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={onEdit}>
          <Pencil className="mr-1.5 h-3.5 w-3.5" />
          Modifica
        </Button>
      </div>

      {/* 4 Card Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Step 1: Muscoloscheletrico */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Bone className="h-4 w-4 text-primary" />
              Muscoloscheletrico
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuestionRow label="Infortuni attuali" value={data.infortuni_attuali} />
            <QuestionRow label="Infortuni pregressi" value={data.infortuni_pregressi} />
            <QuestionRow label="Interventi chirurgici" value={data.interventi_chirurgici} />
            <QuestionRow label="Dolori cronici" value={data.dolori_cronici} />
          </CardContent>
        </Card>

        {/* Step 2: Condizioni Mediche */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Stethoscope className="h-4 w-4 text-primary" />
              Condizioni Mediche
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuestionRow label="Patologie diagnosticate" value={data.patologie} />
            <QuestionRow label="Farmaci regolari" value={data.farmaci} />
            <QuestionRow label="Problemi cardiovascolari" value={data.problemi_cardiovascolari} />
            <QuestionRow label="Problemi respiratori" value={data.problemi_respiratori} />
          </CardContent>
        </Card>

        {/* Step 3: Stile di Vita */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Heart className="h-4 w-4 text-primary" />
              Stile di Vita
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <InfoRow label="Attivita' fisica" value={LIVELLI_ATTIVITA_LABELS[data.livello_attivita] ?? data.livello_attivita} />
            <InfoRow label="Sonno" value={ORE_SONNO_LABELS[data.ore_sonno] ?? data.ore_sonno} />
            <InfoRow label="Stress" value={LIVELLI_STRESS_LABELS[data.livello_stress] ?? data.livello_stress} />
            <QuestionRow label="Dieta particolare" value={data.dieta_particolare} />
          </CardContent>
        </Card>

        {/* Step 4: Obiettivi e Limitazioni */}
        <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Target className="h-4 w-4 text-primary" />
              Obiettivi e Limitazioni
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {data.obiettivi_specifici ? (
              <div>
                <span className="font-medium">Obiettivi:</span>
                <p className="text-muted-foreground mt-0.5">{data.obiettivi_specifici}</p>
              </div>
            ) : (
              <p className="text-muted-foreground italic">Nessun obiettivo specificato</p>
            )}
            {data.limitazioni_funzionali ? (
              <div>
                <span className="font-medium">Limitazioni:</span>
                <p className="text-muted-foreground mt-0.5">{data.limitazioni_funzionali}</p>
              </div>
            ) : (
              <p className="text-muted-foreground italic">Nessuna limitazione specificata</p>
            )}
            {data.note && (
              <div>
                <span className="font-medium">Note:</span>
                <p className="text-muted-foreground mt-0.5">{data.note}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
