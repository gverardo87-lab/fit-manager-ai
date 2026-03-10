// src/components/clients/anamnesi/AnamnesiSteps.tsx
"use client";

/**
 * Step 1-3 del questionario anamnesi v2 (Chiara).
 * Step 1: Stile di Vita — Step 2: Obiettivo — Step 3: Esperienza Sportiva.
 *
 * Step 4-6 in AnamnesiStepsSalute.tsx per rispettare il limite 300 LOC.
 */

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AnamnesiData } from "@/types/api";
import {
  ORE_SEDUTO, ORE_SEDUTO_LABELS,
  SPOSTAMENTO, SPOSTAMENTO_LABELS,
  ORE_SONNO, ORE_SONNO_LABELS,
  QUALITA_SONNO, QUALITA_SONNO_LABELS,
  FUMO_OPTIONS, FUMO_LABELS,
  ALCOL_OPTIONS, ALCOL_LABELS,
  OBIETTIVI_PRINCIPALI, OBIETTIVI_PRINCIPALI_LABELS,
  FREQUENZA_SETTIMANALE, FREQUENZA_LABELS,
  LUOGO_ALLENAMENTO, LUOGO_LABELS,
  ESPERIENZA_DURATA, ESPERIENZA_LABELS,
} from "@/types/api";

// Re-export step 4-6 from sibling file
export {
  StepSalute,
  StepAlimentazione,
  StepLogistica,
} from "./AnamnesiStepsSalute";

// ════════════════════════════════════════════════════════════
// SHARED SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

export interface StepProps {
  data: AnamnesiData;
  onChange: (updates: Partial<AnamnesiData>) => void;
}

function SelectField({ label, value, onValueChange, options, labels }: {
  label: string;
  value: string;
  onValueChange: (v: string) => void;
  options: readonly string[];
  labels: Record<string, string>;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent position="popper" sideOffset={4}>
          {options.map((o) => (
            <SelectItem key={o} value={o}>{labels[o]}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function SliderField({ label, value, onChange, min, max, hint }: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  hint?: string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">{label}</label>
        <span className="text-sm font-semibold text-primary">{value}/{max}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-primary"
      />
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 1: STILE DI VITA
// ════════════════════════════════════════════════════════════

export function StepStileVita({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Informazioni sulla tua quotidianit&agrave; e abitudini.
      </p>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Professione</label>
        <Input
          value={data.professione ?? ""}
          onChange={(e) => onChange({ professione: e.target.value || null })}
          placeholder="Es. impiegata, insegnante, libera professionista..."
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Ore seduto/a al giorno" value={data.ore_seduto}
          onValueChange={(v) => onChange({ ore_seduto: v })}
          options={ORE_SEDUTO} labels={ORE_SEDUTO_LABELS} />
        <SelectField label="Come ti sposti" value={data.spostamento}
          onValueChange={(v) => onChange({ spostamento: v })}
          options={SPOSTAMENTO} labels={SPOSTAMENTO_LABELS} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Ore di sonno medie" value={data.ore_sonno}
          onValueChange={(v) => onChange({ ore_sonno: v })}
          options={ORE_SONNO} labels={ORE_SONNO_LABELS} />
        <SelectField label="Qualita' del sonno" value={data.qualita_sonno}
          onValueChange={(v) => onChange({ qualita_sonno: v })}
          options={QUALITA_SONNO} labels={QUALITA_SONNO_LABELS} />
      </div>

      <SliderField label="Livello di stress percepito" value={data.livello_stress}
        onChange={(v) => onChange({ livello_stress: v })} min={1} max={5}
        hint="1 = molto basso, 5 = molto alto" />

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Fumo" value={data.fumo}
          onValueChange={(v) => onChange({ fumo: v })}
          options={FUMO_OPTIONS} labels={FUMO_LABELS} />
        <SelectField label="Alcol" value={data.alcol}
          onValueChange={(v) => onChange({ alcol: v })}
          options={ALCOL_OPTIONS} labels={ALCOL_LABELS} />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Passi giornalieri (stima)</label>
        <Input
          value={data.passi_giornalieri ?? ""}
          onChange={(e) => onChange({ passi_giornalieri: e.target.value || null })}
          placeholder="Es. 3000, 5000-8000..."
        />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 2: OBIETTIVO E MOTIVAZIONE
// ════════════════════════════════════════════════════════════

export function StepObiettivo({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Cosa ti ha portato qui e cosa vorresti ottenere.
      </p>

      <SelectField label="Obiettivo principale" value={data.obiettivo_principale}
        onValueChange={(v) => onChange({ obiettivo_principale: v })}
        options={OBIETTIVI_PRINCIPALI} labels={OBIETTIVI_PRINCIPALI_LABELS} />

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Obiettivi secondari</label>
        <Textarea
          value={data.obiettivi_secondari ?? ""}
          onChange={(e) => onChange({ obiettivi_secondari: e.target.value || null })}
          placeholder="Hai altri obiettivi oltre a quello principale?"
          rows={2}
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Perch&eacute; proprio adesso?</label>
        <Textarea
          value={data.perche_adesso ?? ""}
          onChange={(e) => onChange({ perche_adesso: e.target.value || null })}
          placeholder="Cosa ti ha spinto a iniziare questo percorso?"
          rows={2}
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Come ti vedi tra 3 mesi?</label>
        <Textarea
          value={data.cosa_3_mesi ?? ""}
          onChange={(e) => onChange({ cosa_3_mesi: e.target.value || null })}
          placeholder="Descrivi il risultato che vorresti raggiungere..."
          rows={2}
        />
      </div>

      <SliderField label="Impegno che puoi dedicare" value={data.impegno}
        onChange={(v) => onChange({ impegno: v })} min={1} max={10}
        hint="1 = il minimo, 10 = il massimo possibile" />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 3: ESPERIENZA SPORTIVA
// ════════════════════════════════════════════════════════════

export function StepEsperienza({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        La tua esperienza con l&apos;allenamento.
      </p>

      <div className="flex items-center justify-between rounded-lg border p-3">
        <span className="text-sm font-medium">Ti alleni attualmente?</span>
        <Switch
          checked={data.si_allena}
          onCheckedChange={(v) => onChange({ si_allena: v })}
        />
      </div>

      {data.si_allena && (
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField label="Quante volte a settimana?" value={data.frequenza_settimanale}
            onValueChange={(v) => onChange({ frequenza_settimanale: v })}
            options={FREQUENZA_SETTIMANALE} labels={FREQUENZA_LABELS} />
          <SelectField label="Dove ti alleni?" value={data.luogo_allenamento}
            onValueChange={(v) => onChange({ luogo_allenamento: v })}
            options={LUOGO_ALLENAMENTO} labels={LUOGO_LABELS} />
        </div>
      )}

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Tipo di allenamento preferito</label>
        <Input
          value={data.tipo_preferito ?? ""}
          onChange={(e) => onChange({ tipo_preferito: e.target.value || null })}
          placeholder="Es. pesi, corsa, yoga, nuoto, crossfit..."
        />
      </div>

      <SelectField label="Da quanto tempo ti alleni?" value={data.esperienza_durata}
        onValueChange={(v) => onChange({ esperienza_durata: v })}
        options={ESPERIENZA_DURATA} labels={ESPERIENZA_LABELS} />

      <div className="flex items-center justify-between rounded-lg border p-3">
        <span className="text-sm font-medium">Hai mai avuto un personal trainer?</span>
        <Switch
          checked={data.esperienza_pt}
          onCheckedChange={(v) => onChange({ esperienza_pt: v })}
        />
      </div>

      {data.esperienza_pt && (
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Com&apos;&egrave; stata l&apos;esperienza?</label>
          <Textarea
            value={data.feedback_pt ?? ""}
            onChange={(e) => onChange({ feedback_pt: e.target.value || null })}
            placeholder="Cosa ti e' piaciuto e cosa no?"
            rows={2}
          />
        </div>
      )}
    </div>
  );
}
