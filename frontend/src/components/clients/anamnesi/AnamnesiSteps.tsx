// src/components/clients/anamnesi/AnamnesiSteps.tsx
"use client";

/**
 * 4 step del questionario anamnesi + sub-componente QuestionToggle riusabile.
 * Ogni step riceve la porzione di dati rilevante + callback onChange.
 */

import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AnamnesiData, AnamnesiQuestion } from "@/types/api";
import {
  LIVELLI_ATTIVITA,
  LIVELLI_ATTIVITA_LABELS,
  ORE_SONNO,
  ORE_SONNO_LABELS,
  LIVELLI_STRESS,
  LIVELLI_STRESS_LABELS,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// QUESTION TOGGLE (riusabile per ogni domanda si/no + dettaglio)
// ════════════════════════════════════════════════════════════

function QuestionToggle({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: AnamnesiQuestion;
  onChange: (v: AnamnesiQuestion) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-2 rounded-lg border p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium leading-snug">{label}</span>
        <Switch
          checked={value.presente}
          onCheckedChange={(checked) =>
            onChange({ presente: checked, dettaglio: checked ? value.dettaglio : null })
          }
        />
      </div>
      {value.presente && (
        <Textarea
          value={value.dettaglio ?? ""}
          onChange={(e) => onChange({ ...value, dettaglio: e.target.value || null })}
          placeholder={placeholder ?? "Descrivi nel dettaglio..."}
          rows={2}
          className="mt-1 text-sm"
        />
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP PROPS
// ════════════════════════════════════════════════════════════

interface StepProps {
  data: AnamnesiData;
  onChange: (updates: Partial<AnamnesiData>) => void;
}

// ════════════════════════════════════════════════════════════
// STEP 1: MUSCOLOSCHELETRICO
// ════════════════════════════════════════════════════════════

export function StepMuscoloscheletrico({ data, onChange }: StepProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Informazioni su infortuni, interventi chirurgici e dolori cronici.
      </p>
      <QuestionToggle
        label="Hai infortuni attuali?"
        value={data.infortuni_attuali}
        onChange={(v) => onChange({ infortuni_attuali: v })}
        placeholder="Es. distorsione caviglia destra, tendinite spalla sinistra..."
      />
      <QuestionToggle
        label="Hai avuto infortuni pregressi?"
        value={data.infortuni_pregressi}
        onChange={(v) => onChange({ infortuni_pregressi: v })}
        placeholder="Es. frattura polso destro 2020, frattura ginocchio sinistro, strappo quadricipite..."
      />
      <QuestionToggle
        label="Hai subito interventi chirurgici?"
        value={data.interventi_chirurgici}
        onChange={(v) => onChange({ interventi_chirurgici: v })}
        placeholder="Es. artroscopia ginocchio destro 2019, ernia discale lombare..."
      />
      <QuestionToggle
        label="Hai dolori cronici?"
        value={data.dolori_cronici}
        onChange={(v) => onChange({ dolori_cronici: v })}
        placeholder="Es. lombalgia cronica, cervicalgia, gonalgia ginocchio destro..."
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 2: CONDIZIONI MEDICHE
// ════════════════════════════════════════════════════════════

export function StepCondizioniMediche({ data, onChange }: StepProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Patologie diagnosticate, farmaci e condizioni cardiovascolari/respiratorie.
      </p>
      <QuestionToggle
        label="Hai patologie diagnosticate?"
        value={data.patologie}
        onChange={(v) => onChange({ patologie: v })}
        placeholder="Es. diabete tipo 2, ipertensione, artrosi..."
      />
      <QuestionToggle
        label="Assumi farmaci regolarmente?"
        value={data.farmaci}
        onChange={(v) => onChange({ farmaci: v })}
        placeholder="Es. antipertensivi, antinfiammatori, integratori prescritti..."
      />
      <QuestionToggle
        label="Hai problemi cardiovascolari?"
        value={data.problemi_cardiovascolari}
        onChange={(v) => onChange({ problemi_cardiovascolari: v })}
        placeholder="Es. aritmia, ipertensione, cardiopatia..."
      />
      <QuestionToggle
        label="Hai problemi respiratori?"
        value={data.problemi_respiratori}
        onChange={(v) => onChange({ problemi_respiratori: v })}
        placeholder="Es. asma, BPCO, apnea notturna..."
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 3: STILE DI VITA
// ════════════════════════════════════════════════════════════

export function StepStileVita({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Abitudini quotidiane che influenzano la programmazione dell&apos;allenamento.
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {/* Livello attivita' */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Livello di attivita' fisica</label>
          <Select
            value={data.livello_attivita}
            onValueChange={(v) => onChange({ livello_attivita: v })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper" sideOffset={4}>
              {LIVELLI_ATTIVITA.map((l) => (
                <SelectItem key={l} value={l}>{LIVELLI_ATTIVITA_LABELS[l]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Ore sonno */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Ore di sonno medie</label>
          <Select
            value={data.ore_sonno}
            onValueChange={(v) => onChange({ ore_sonno: v })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper" sideOffset={4}>
              {ORE_SONNO.map((o) => (
                <SelectItem key={o} value={o}>{ORE_SONNO_LABELS[o]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Livello stress */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Livello di stress percepito</label>
          <Select
            value={data.livello_stress}
            onValueChange={(v) => onChange({ livello_stress: v })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper" sideOffset={4}>
              {LIVELLI_STRESS.map((s) => (
                <SelectItem key={s} value={s}>{LIVELLI_STRESS_LABELS[s]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <QuestionToggle
        label="Segui una dieta particolare?"
        value={data.dieta_particolare}
        onChange={(v) => onChange({ dieta_particolare: v })}
        placeholder="Es. vegana, chetogenica, ipocalorica prescritta..."
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 4: OBIETTIVI E LIMITAZIONI
// ════════════════════════════════════════════════════════════

export function StepObiettivi({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Obiettivi del cliente e limitazioni da considerare nella programmazione.
      </p>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Obiettivi specifici</label>
        <Textarea
          value={data.obiettivi_specifici ?? ""}
          onChange={(e) => onChange({ obiettivi_specifici: e.target.value || null })}
          placeholder="Es. perdere 5kg, migliorare postura, preparazione maratona..."
          rows={3}
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Limitazioni funzionali note</label>
        <Textarea
          value={data.limitazioni_funzionali ?? ""}
          onChange={(e) => onChange({ limitazioni_funzionali: e.target.value || null })}
          placeholder="Es. non puo' fare squat profondi, evitare carichi sopra la testa..."
          rows={3}
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Note aggiuntive</label>
        <Textarea
          value={data.note ?? ""}
          onChange={(e) => onChange({ note: e.target.value || null })}
          placeholder="Altre informazioni utili per la programmazione..."
          rows={3}
        />
      </div>
    </div>
  );
}
