// src/components/clients/anamnesi/AnamnesiStepsSalute.tsx
"use client";

/**
 * Step 4-6 del questionario anamnesi v2 (Chiara).
 * Step 4: Salute e Sicurezza — Step 5: Alimentazione — Step 6: Logistica e Note.
 */

import { Checkbox } from "@/components/ui/checkbox";
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
import type { AnamnesiData, AnamnesiQuestion } from "@/types/api";
import {
  DOLORI_OPTIONS, DOLORI_LABELS,
  PATOLOGIE_OPTIONS, PATOLOGIE_OPTION_LABELS,
  FARMACI_OPTIONS, FARMACI_LABELS,
  CERTIFICATO_OPTIONS, CERTIFICATO_LABELS,
  ALIMENTAZIONE_OPTIONS, ALIMENTAZIONE_LABELS,
  RAPPORTO_CIBO_OPTIONS, RAPPORTO_CIBO_LABELS,
  PREFERENZA_LUOGO, PREFERENZA_LUOGO_LABELS,
  SEDUTE_OPTIONS, SEDUTE_LABELS,
  FRENI_OPTIONS, FRENI_LABELS,
} from "@/types/api";
import type { StepProps } from "./AnamnesiSteps";

// ════════════════════════════════════════════════════════════
// SHARED SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function CheckboxGroup({ options, labels, selected: selectedRaw, onChange, altroValue, onAltroChange }: {
  options: readonly string[];
  labels: Record<string, string>;
  selected: string[];
  onChange: (v: string[]) => void;
  altroValue?: string | null;
  onAltroChange?: (v: string | null) => void;
}) {
  const selected = selectedRaw ?? [];
  const toggle = (opt: string) => {
    onChange(
      selected.includes(opt)
        ? selected.filter((s) => s !== opt)
        : [...selected, opt],
    );
  };

  return (
    <div className="space-y-2">
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((opt) => (
          <div
            key={opt}
            onClick={() => toggle(opt)}
            className="flex items-center gap-2 rounded-md border p-2 cursor-pointer hover:bg-muted/50 transition-colors"
          >
            <Checkbox
              checked={selected.includes(opt)}
              onClick={(e) => e.stopPropagation()}
              onCheckedChange={() => toggle(opt)}
            />
            <span className="text-sm">{labels[opt]}</span>
          </div>
        ))}
      </div>
      {onAltroChange && (
        <Input
          value={altroValue ?? ""}
          onChange={(e) => onAltroChange(e.target.value || null)}
          placeholder="Altro (specifica)..."
          className="mt-1"
        />
      )}
    </div>
  );
}

function QuestionToggle({ label, value, onChange, placeholder }: {
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

// ════════════════════════════════════════════════════════════
// STEP 4: SALUTE E SICUREZZA
// ════════════════════════════════════════════════════════════

export function StepSalute({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Informazioni importanti per la tua sicurezza durante l&apos;allenamento.
      </p>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Hai dolori in qualche zona del corpo?</label>
        <CheckboxGroup
          options={DOLORI_OPTIONS}
          labels={DOLORI_LABELS}
          selected={data.dolori_attuali}
          onChange={(v) => onChange({ dolori_attuali: v })}
          altroValue={data.dolori_attuali_altro}
          onAltroChange={(v) => onChange({ dolori_attuali_altro: v })}
        />
      </div>

      <QuestionToggle
        label="Hai avuto infortuni importanti?"
        value={data.infortuni_importanti}
        onChange={(v) => onChange({ infortuni_importanti: v })}
        placeholder="Es. fratture, distorsioni gravi, strappi muscolari..."
      />

      <div className="space-y-2 rounded-lg border p-3">
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium leading-snug">Hai patologie diagnosticate?</span>
          <Switch
            checked={data.patologie.presente}
            onCheckedChange={(checked) => {
              onChange({
                patologie: { presente: checked, dettaglio: data.patologie.dettaglio },
                patologie_lista: checked ? data.patologie_lista : [],
                patologie_altro: checked ? data.patologie_altro : null,
              });
            }}
          />
        </div>
        {data.patologie.presente && (
          <CheckboxGroup
            options={PATOLOGIE_OPTIONS}
            labels={PATOLOGIE_OPTION_LABELS}
            selected={data.patologie_lista}
            onChange={(v) => onChange({ patologie_lista: v })}
            altroValue={data.patologie_altro}
            onAltroChange={(v) => onChange({ patologie_altro: v })}
          />
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Assumi farmaci?" value={data.farmaci_risposta}
          onValueChange={(v) => onChange({ farmaci_risposta: v })}
          options={FARMACI_OPTIONS} labels={FARMACI_LABELS} />
        <SelectField label="Certificato sportivo" value={data.certificato_sportivo}
          onValueChange={(v) => onChange({ certificato_sportivo: v })}
          options={CERTIFICATO_OPTIONS} labels={CERTIFICATO_LABELS} />
      </div>

      {data.farmaci_risposta === "si" && (
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Quali farmaci?</label>
          <Textarea
            value={data.farmaci_dettaglio ?? ""}
            onChange={(e) => onChange({ farmaci_dettaglio: e.target.value || null })}
            placeholder="Es. antipertensivi, antinfiammatori, insulina..."
            rows={2}
          />
        </div>
      )}

      <QuestionToggle
        label="Hai limitazioni mediche per l'allenamento?"
        value={data.limitazioni_mediche}
        onChange={(v) => onChange({ limitazioni_mediche: v })}
        placeholder="Es. non posso fare squat profondi, evitare carichi sopra la testa..."
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 5: ALIMENTAZIONE
// ════════════════════════════════════════════════════════════

export function StepAlimentazione({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Il rapporto con l&apos;alimentazione e' parte del percorso.
      </p>

      <SelectField label="Come definiresti la tua alimentazione?" value={data.tipo_alimentazione}
        onValueChange={(v) => onChange({ tipo_alimentazione: v })}
        options={ALIMENTAZIONE_OPTIONS} labels={ALIMENTAZIONE_LABELS} />

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Intolleranze o allergie alimentari</label>
        <Input
          value={data.intolleranze ?? ""}
          onChange={(e) => onChange({ intolleranze: e.target.value || null })}
          placeholder="Es. lattosio, glutine, frutta secca..."
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Serenita' nel rapporto col cibo e col corpo</label>
          <span className="text-sm font-semibold text-primary">{data.serenita_cibo}/10</span>
        </div>
        <input
          type="range" min={1} max={10}
          value={data.serenita_cibo}
          onChange={(e) => onChange({ serenita_cibo: Number(e.target.value) })}
          className="w-full accent-primary"
        />
        <p className="text-xs text-muted-foreground">1 = molto difficile, 10 = totale serenita'</p>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">C&apos;e' qualcosa che vuoi dirmi sull&apos;alimentazione?</label>
        <Textarea
          value={data.messaggio_alimentazione ?? ""}
          onChange={(e) => onChange({ messaggio_alimentazione: e.target.value || null })}
          placeholder="Qualsiasi cosa che ritieni utile condividere..."
          rows={2}
        />
      </div>

      <SelectField
        label="Hai un rapporto complesso con l'alimentazione?"
        value={data.rapporto_complesso_alimentazione}
        onValueChange={(v) => onChange({ rapporto_complesso_alimentazione: v })}
        options={RAPPORTO_CIBO_OPTIONS} labels={RAPPORTO_CIBO_LABELS}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// STEP 6: LOGISTICA E NOTE
// ════════════════════════════════════════════════════════════

export function StepLogistica({ data, onChange }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Organizzazione pratica e ultime informazioni.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Dove preferisci allenarti?" value={data.preferenza_luogo}
          onValueChange={(v) => onChange({ preferenza_luogo: v })}
          options={PREFERENZA_LUOGO} labels={PREFERENZA_LUOGO_LABELS} />
        <SelectField label="Quante sedute a settimana?" value={data.sedute_settimana}
          onValueChange={(v) => onChange({ sedute_settimana: v })}
          options={SEDUTE_OPTIONS} labels={SEDUTE_LABELS} />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Giorni e orari preferiti</label>
        <Input
          value={data.giorni_orari_preferiti ?? ""}
          onChange={(e) => onChange({ giorni_orari_preferiti: e.target.value || null })}
          placeholder="Es. lunedi' e giovedi' mattina, sera dopo le 18..."
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Cosa ti ha frenato in passato?</label>
        <CheckboxGroup
          options={FRENI_OPTIONS}
          labels={FRENI_LABELS}
          selected={data.freni_passato}
          onChange={(v) => onChange({ freni_passato: v })}
          altroValue={data.freni_altro}
          onAltroChange={(v) => onChange({ freni_altro: v })}
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Note finali</label>
        <Textarea
          value={data.note_finali ?? ""}
          onChange={(e) => onChange({ note_finali: e.target.value || null })}
          placeholder="Qualsiasi cosa tu voglia aggiungere..."
          rows={3}
        />
      </div>

      <div
        onClick={() => onChange({ consenso_privacy: !data.consenso_privacy })}
        className="flex items-start gap-3 rounded-lg border p-3 cursor-pointer hover:bg-muted/50 transition-colors"
      >
        <Checkbox
          checked={data.consenso_privacy}
          onClick={(e) => e.stopPropagation()}
          onCheckedChange={(checked) => onChange({ consenso_privacy: !!checked })}
          className="mt-0.5"
        />
        <span className="text-sm leading-snug">
          Acconsento al trattamento dei miei dati personali per la finalita' di
          personalizzazione del programma di allenamento.
        </span>
      </div>
    </div>
  );
}
