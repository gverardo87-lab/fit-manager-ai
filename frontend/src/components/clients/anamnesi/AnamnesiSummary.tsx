// src/components/clients/anamnesi/AnamnesiSummary.tsx
"use client";

/**
 * Vista read-only dell'anamnesi compilata (v2 — 6 sezioni).
 *
 * 6 card sezione (2x3 desktop, stack mobile) con indicatori colorati:
 * - Emerald + CheckCircle: nessun problema
 * - Red + AlertCircle: problema segnalato con dettaglio
 * - Badge per valori select
 */

import {
  AlertCircle,
  Pencil,
  Heart,
  Target,
  Dumbbell,
  ShieldCheck,
  Apple,
  MapPin,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AnamnesiData } from "@/types/api";
import {
  ORE_SEDUTO_LABELS, SPOSTAMENTO_LABELS,
  ORE_SONNO_LABELS, QUALITA_SONNO_LABELS,
  FUMO_LABELS, ALCOL_LABELS,
  OBIETTIVI_PRINCIPALI_LABELS,
  FREQUENZA_LABELS, LUOGO_LABELS, ESPERIENZA_LABELS,
  DOLORI_LABELS, PATOLOGIE_OPTION_LABELS,
  FARMACI_LABELS, CERTIFICATO_LABELS,
  ALIMENTAZIONE_LABELS, RAPPORTO_CIBO_LABELS,
  PREFERENZA_LUOGO_LABELS, SEDUTE_LABELS, FRENI_LABELS,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge variant="outline" className="text-xs">{value}</Badge>
    </div>
  );
}

function TextRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-sm font-medium">{label}:</span>
      <p className="text-sm text-muted-foreground mt-0.5">{value}</p>
    </div>
  );
}

function ChipList({ items, labels }: { items: string[]; labels: Record<string, string> }) {
  if (items.length === 0) return <span className="text-sm text-muted-foreground italic">Nessuno</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <Badge key={item} variant="secondary" className="text-xs">
          {labels[item] ?? item}
        </Badge>
      ))}
    </div>
  );
}

const cardClass = "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg";

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

      {/* 6 Card Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Step 1: Stile di Vita */}
        <Card className={cardClass}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Heart className="h-4 w-4 text-primary" />
              Stile di Vita
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <TextRow label="Professione" value={data.professione} />
            <InfoRow label="Ore seduto/a" value={ORE_SEDUTO_LABELS[data.ore_seduto] ?? data.ore_seduto} />
            <InfoRow label="Spostamento" value={SPOSTAMENTO_LABELS[data.spostamento] ?? data.spostamento} />
            <InfoRow label="Sonno" value={ORE_SONNO_LABELS[data.ore_sonno] ?? data.ore_sonno} />
            <InfoRow label="Qualita' sonno" value={QUALITA_SONNO_LABELS[data.qualita_sonno] ?? data.qualita_sonno} />
            <InfoRow label="Stress" value={`${data.livello_stress}/5`} />
            <InfoRow label="Fumo" value={FUMO_LABELS[data.fumo] ?? data.fumo} />
            <InfoRow label="Alcol" value={ALCOL_LABELS[data.alcol] ?? data.alcol} />
            {data.passi_giornalieri && <InfoRow label="Passi/giorno" value={data.passi_giornalieri} />}
          </CardContent>
        </Card>

        {/* Step 2: Obiettivo e Motivazione */}
        <Card className={cardClass}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Target className="h-4 w-4 text-primary" />
              Obiettivo e Motivazione
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <InfoRow label="Obiettivo" value={OBIETTIVI_PRINCIPALI_LABELS[data.obiettivo_principale] ?? data.obiettivo_principale} />
            <TextRow label="Secondari" value={data.obiettivi_secondari} />
            <TextRow label="Perche' adesso" value={data.perche_adesso} />
            <TextRow label="Tra 3 mesi" value={data.cosa_3_mesi} />
            <InfoRow label="Impegno" value={`${data.impegno}/10`} />
          </CardContent>
        </Card>

        {/* Step 3: Esperienza Sportiva */}
        <Card className={cardClass}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Dumbbell className="h-4 w-4 text-primary" />
              Esperienza Sportiva
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <InfoRow label="Si allena" value={data.si_allena ? "Si" : "No"} />
            {data.si_allena && (
              <>
                <InfoRow label="Frequenza" value={FREQUENZA_LABELS[data.frequenza_settimanale] ?? data.frequenza_settimanale} />
                <InfoRow label="Dove" value={LUOGO_LABELS[data.luogo_allenamento] ?? data.luogo_allenamento} />
              </>
            )}
            {data.tipo_preferito && <TextRow label="Tipo preferito" value={data.tipo_preferito} />}
            <InfoRow label="Esperienza" value={ESPERIENZA_LABELS[data.esperienza_durata] ?? data.esperienza_durata} />
            <InfoRow label="PT precedente" value={data.esperienza_pt ? "Si" : "No"} />
            <TextRow label="Feedback PT" value={data.feedback_pt} />
          </CardContent>
        </Card>

        {/* Step 4: Salute e Sicurezza */}
        <Card className={cardClass}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Salute e Sicurezza
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <span className="text-sm font-medium">Dolori attuali:</span>
              <div className="mt-1"><ChipList items={data.dolori_attuali} labels={DOLORI_LABELS} /></div>
              {data.dolori_attuali_altro && <p className="text-xs text-muted-foreground mt-1">Altro: {data.dolori_attuali_altro}</p>}
            </div>
            {data.infortuni_importanti.presente && (
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                <div>
                  <span className="text-sm font-medium text-red-700 dark:text-red-400">Infortuni importanti</span>
                  {data.infortuni_importanti.dettaglio && <p className="text-xs text-muted-foreground mt-0.5">{data.infortuni_importanti.dettaglio}</p>}
                </div>
              </div>
            )}
            {data.patologie.presente && (
              <div>
                <div className="flex items-start gap-2">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                  <span className="text-sm font-medium text-red-700 dark:text-red-400">Patologie</span>
                </div>
                <div className="mt-1 ml-6"><ChipList items={data.patologie_lista} labels={PATOLOGIE_OPTION_LABELS} /></div>
                {data.patologie_altro && <p className="text-xs text-muted-foreground mt-1 ml-6">Altro: {data.patologie_altro}</p>}
              </div>
            )}
            <InfoRow label="Farmaci" value={FARMACI_LABELS[data.farmaci_risposta] ?? data.farmaci_risposta} />
            <TextRow label="Dettaglio farmaci" value={data.farmaci_dettaglio} />
            {data.limitazioni_mediche.presente && (
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                <div>
                  <span className="text-sm font-medium text-amber-700 dark:text-amber-400">Limitazioni mediche</span>
                  {data.limitazioni_mediche.dettaglio && <p className="text-xs text-muted-foreground mt-0.5">{data.limitazioni_mediche.dettaglio}</p>}
                </div>
              </div>
            )}
            <InfoRow label="Certificato sportivo" value={CERTIFICATO_LABELS[data.certificato_sportivo] ?? data.certificato_sportivo} />
          </CardContent>
        </Card>

        {/* Step 5: Alimentazione */}
        <Card className={cardClass}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Apple className="h-4 w-4 text-primary" />
              Alimentazione
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <InfoRow label="Tipo" value={ALIMENTAZIONE_LABELS[data.tipo_alimentazione] ?? data.tipo_alimentazione} />
            {data.intolleranze && <TextRow label="Intolleranze" value={data.intolleranze} />}
            <InfoRow label="Serenita' cibo" value={`${data.serenita_cibo}/10`} />
            <TextRow label="Messaggio" value={data.messaggio_alimentazione} />
            <InfoRow label="Rapporto complesso" value={RAPPORTO_CIBO_LABELS[data.rapporto_complesso_alimentazione] ?? data.rapporto_complesso_alimentazione} />
          </CardContent>
        </Card>

        {/* Step 6: Logistica */}
        <Card className={cardClass}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <MapPin className="h-4 w-4 text-primary" />
              Logistica e Note
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <InfoRow label="Luogo" value={PREFERENZA_LUOGO_LABELS[data.preferenza_luogo] ?? data.preferenza_luogo} />
            <InfoRow label="Sedute/sett" value={SEDUTE_LABELS[data.sedute_settimana] ?? data.sedute_settimana} />
            {data.giorni_orari_preferiti && <TextRow label="Giorni/orari" value={data.giorni_orari_preferiti} />}
            <div>
              <span className="text-sm font-medium">Freni passati:</span>
              <div className="mt-1"><ChipList items={data.freni_passato} labels={FRENI_LABELS} /></div>
              {data.freni_altro && <p className="text-xs text-muted-foreground mt-1">Altro: {data.freni_altro}</p>}
            </div>
            <TextRow label="Note" value={data.note_finali} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
