// src/components/exercises/ExerciseForm.tsx
"use client";

/**
 * Form per creare/modificare un esercizio custom.
 * Zod schema per validazione client-side.
 * Campi organizzati in sezioni logiche (v2: biomeccanica, esecuzione, coaching).
 */

import { Loader2, Plus, X } from "lucide-react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  CATEGORY_OPTIONS,
  PATTERN_OPTIONS,
  EQUIPMENT_OPTIONS,
  DIFFICULTY_OPTIONS,
  MUSCLE_OPTIONS,
  FORCE_TYPE_OPTIONS,
  LATERAL_PATTERN_OPTIONS,
} from "./exercise-constants";
import type { Exercise } from "@/types/api";

// ════════════════════════════════════════════════════════════
// ZOD SCHEMA
// ════════════════════════════════════════════════════════════

const exerciseSchema = z.object({
  // Identita'
  nome: z.string().min(1, "Nome obbligatorio").max(200),
  nome_en: z.string().max(200).optional(),

  // Classificazione
  categoria: z.string().min(1, "Categoria obbligatoria"),
  pattern_movimento: z.string().min(1, "Pattern obbligatorio"),
  force_type: z.string().optional(),
  lateral_pattern: z.string().optional(),

  // Muscoli
  muscoli_primari: z.array(z.string()).min(1, "Seleziona almeno un muscolo"),
  muscoli_secondari: z.array(z.string()).optional(),

  // Setup
  attrezzatura: z.string().min(1, "Attrezzatura obbligatoria"),
  difficolta: z.string().min(1, "Difficolta' obbligatoria"),
  rep_range_forza: z.string().max(20).optional(),
  rep_range_ipertrofia: z.string().max(20).optional(),
  rep_range_resistenza: z.string().max(20).optional(),
  ore_recupero: z.coerce.number().int().min(1).max(96).optional(),

  // Descrizioni (v2)
  descrizione_anatomica: z.string().optional(),
  descrizione_biomeccanica: z.string().optional(),

  // Esecuzione (v2)
  setup: z.string().optional(),
  esecuzione: z.string().optional(),
  respirazione: z.string().optional(),
  tempo_consigliato: z.string().max(20).optional(),

  // Coaching (v2)
  coaching_cues: z.array(z.object({ value: z.string() })).optional(),
  note_sicurezza: z.string().optional(),
  controindicazioni: z.array(z.object({ value: z.string() })).optional(),

  // Errori comuni (v2)
  errori_comuni: z.array(z.object({
    errore: z.string(),
    correzione: z.string(),
  })).optional(),
});

export type ExerciseFormValues = z.infer<typeof exerciseSchema>;

interface ExerciseFormProps {
  exercise?: Exercise | null;
  onSubmit: (values: Record<string, unknown>) => void;
  isPending: boolean;
}

// ════════════════════════════════════════════════════════════
// SECTION HEADER
// ════════════════════════════════════════════════════════════

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
      {children}
    </h3>
  );
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function ExerciseForm({ exercise, onSubmit, isPending }: ExerciseFormProps) {
  const isEdit = !!exercise;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    control,
    formState: { errors },
  } = useForm<ExerciseFormValues>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(exerciseSchema) as any,
    defaultValues: {
      nome: exercise?.nome ?? "",
      nome_en: exercise?.nome_en ?? "",
      categoria: exercise?.categoria ?? "",
      pattern_movimento: exercise?.pattern_movimento ?? "",
      force_type: exercise?.force_type ?? "",
      lateral_pattern: exercise?.lateral_pattern ?? "",
      muscoli_primari: exercise?.muscoli_primari ?? [],
      muscoli_secondari: exercise?.muscoli_secondari ?? [],
      attrezzatura: exercise?.attrezzatura ?? "",
      difficolta: exercise?.difficolta ?? "",
      rep_range_forza: exercise?.rep_range_forza ?? "",
      rep_range_ipertrofia: exercise?.rep_range_ipertrofia ?? "",
      rep_range_resistenza: exercise?.rep_range_resistenza ?? "",
      ore_recupero: exercise?.ore_recupero ?? 48,
      descrizione_anatomica: exercise?.descrizione_anatomica ?? "",
      descrizione_biomeccanica: exercise?.descrizione_biomeccanica ?? "",
      setup: exercise?.setup ?? "",
      esecuzione: exercise?.esecuzione ?? "",
      respirazione: exercise?.respirazione ?? "",
      tempo_consigliato: exercise?.tempo_consigliato ?? "",
      coaching_cues: exercise?.coaching_cues?.length
        ? exercise.coaching_cues.map((c) => ({ value: c }))
        : [],
      note_sicurezza: exercise?.note_sicurezza ?? "",
      controindicazioni: exercise?.controindicazioni?.length
        ? exercise.controindicazioni.map((c) => ({ value: c }))
        : [],
      errori_comuni: exercise?.errori_comuni?.length
        ? exercise.errori_comuni.map((e) => ({ errore: e.errore, correzione: e.correzione }))
        : [],
    },
  });

  const muscoliPrimari = watch("muscoli_primari");
  const muscoliSecondari = watch("muscoli_secondari");

  // Dynamic field arrays
  const { fields: cueFields, append: appendCue, remove: removeCue } =
    useFieldArray({ control, name: "coaching_cues" });
  const { fields: errorFields, append: appendError, remove: removeError } =
    useFieldArray({ control, name: "errori_comuni" });
  const { fields: controFields, append: appendContro, remove: removeContro } =
    useFieldArray({ control, name: "controindicazioni" });

  const handleFormSubmit = (values: ExerciseFormValues) => {
    // Clean optional strings: empty → undefined
    const clean = (s: string | undefined) => s?.trim() || undefined;

    const cleaned: Record<string, unknown> = {
      nome: values.nome,
      nome_en: clean(values.nome_en),
      categoria: values.categoria,
      pattern_movimento: values.pattern_movimento,
      force_type: clean(values.force_type),
      lateral_pattern: clean(values.lateral_pattern),
      muscoli_primari: values.muscoli_primari,
      muscoli_secondari: values.muscoli_secondari?.length ? values.muscoli_secondari : undefined,
      attrezzatura: values.attrezzatura,
      difficolta: values.difficolta,
      rep_range_forza: clean(values.rep_range_forza),
      rep_range_ipertrofia: clean(values.rep_range_ipertrofia),
      rep_range_resistenza: clean(values.rep_range_resistenza),
      ore_recupero: values.ore_recupero,
      descrizione_anatomica: clean(values.descrizione_anatomica),
      descrizione_biomeccanica: clean(values.descrizione_biomeccanica),
      setup: clean(values.setup),
      esecuzione: clean(values.esecuzione),
      respirazione: clean(values.respirazione),
      tempo_consigliato: clean(values.tempo_consigliato),
      note_sicurezza: clean(values.note_sicurezza),
      // Convert {value} wrappers → flat arrays, filter empty
      coaching_cues: values.coaching_cues
        ?.map((c) => c.value.trim())
        .filter(Boolean),
      controindicazioni: values.controindicazioni
        ?.map((c) => c.value.trim())
        .filter(Boolean),
      // errori_comuni: filter pairs with both fields filled
      errori_comuni: values.errori_comuni
        ?.filter((e) => e.errore.trim() && e.correzione.trim())
        .map((e) => ({ errore: e.errore.trim(), correzione: e.correzione.trim() })),
    };

    // Remove keys with undefined/empty arrays
    for (const key of Object.keys(cleaned)) {
      const val = cleaned[key];
      if (val === undefined) delete cleaned[key];
      if (Array.isArray(val) && val.length === 0) delete cleaned[key];
    }

    onSubmit(cleaned);
  };

  const toggleMuscle = (field: "muscoli_primari" | "muscoli_secondari", muscle: string) => {
    const current = field === "muscoli_primari" ? muscoliPrimari : muscoliSecondari ?? [];
    const updated = current.includes(muscle)
      ? current.filter((m) => m !== muscle)
      : [...current, muscle];
    setValue(field, updated, { shouldValidate: true });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* ── Identita' ── */}
      <div>
        <SectionHeader>Identita&apos;</SectionHeader>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="nome">Nome *</Label>
            <Input id="nome" {...register("nome")} placeholder="es. Curl Martello" />
            {errors.nome && <p className="text-sm text-destructive">{errors.nome.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="nome_en">Nome EN</Label>
            <Input id="nome_en" {...register("nome_en")} placeholder="es. Hammer Curl" />
          </div>
        </div>
      </div>

      {/* ── Classificazione ── */}
      <div>
        <SectionHeader>Classificazione</SectionHeader>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <Label>Categoria *</Label>
            <Select
              value={watch("categoria")}
              onValueChange={(v) => setValue("categoria", v, { shouldValidate: true })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona..." />
              </SelectTrigger>
              <SelectContent>
                {CATEGORY_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.categoria && <p className="text-sm text-destructive">{errors.categoria.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Pattern *</Label>
            <Select
              value={watch("pattern_movimento")}
              onValueChange={(v) => setValue("pattern_movimento", v, { shouldValidate: true })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona..." />
              </SelectTrigger>
              <SelectContent>
                {PATTERN_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.pattern_movimento && <p className="text-sm text-destructive">{errors.pattern_movimento.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Difficolta&apos; *</Label>
            <Select
              value={watch("difficolta")}
              onValueChange={(v) => setValue("difficolta", v, { shouldValidate: true })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona..." />
              </SelectTrigger>
              <SelectContent>
                {DIFFICULTY_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.difficolta && <p className="text-sm text-destructive">{errors.difficolta.message}</p>}
          </div>
        </div>
      </div>

      {/* ── Biomeccanica (v2) ── */}
      <div>
        <SectionHeader>Biomeccanica</SectionHeader>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Tipo di Forza</Label>
            <Select
              value={watch("force_type") || ""}
              onValueChange={(v) => setValue("force_type", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Opzionale..." />
              </SelectTrigger>
              <SelectContent>
                {FORCE_TYPE_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Pattern Laterale</Label>
            <Select
              value={watch("lateral_pattern") || ""}
              onValueChange={(v) => setValue("lateral_pattern", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Opzionale..." />
              </SelectTrigger>
              <SelectContent>
                {LATERAL_PATTERN_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* ── Muscoli Primari ── */}
      <div>
        <SectionHeader>Muscoli Primari *</SectionHeader>
        <div className="flex flex-wrap gap-2">
          {MUSCLE_OPTIONS.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => toggleMuscle("muscoli_primari", m.value)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                muscoliPrimari.includes(m.value)
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:border-primary/50"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        {errors.muscoli_primari && (
          <p className="mt-1 text-sm text-destructive">{errors.muscoli_primari.message}</p>
        )}
      </div>

      {/* ── Muscoli Secondari ── */}
      <div>
        <SectionHeader>Muscoli Secondari</SectionHeader>
        <div className="flex flex-wrap gap-2">
          {MUSCLE_OPTIONS.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => toggleMuscle("muscoli_secondari", m.value)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                (muscoliSecondari ?? []).includes(m.value)
                  ? "border-violet-400 bg-violet-50 text-violet-600 dark:bg-violet-900/20 dark:text-violet-400"
                  : "border-border text-muted-foreground hover:border-violet-300"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Setup & Attrezzatura ── */}
      <div>
        <SectionHeader>Setup</SectionHeader>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Attrezzatura *</Label>
            <Select
              value={watch("attrezzatura")}
              onValueChange={(v) => setValue("attrezzatura", v, { shouldValidate: true })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona..." />
              </SelectTrigger>
              <SelectContent>
                {EQUIPMENT_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.attrezzatura && <p className="text-sm text-destructive">{errors.attrezzatura.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="ore_recupero">Ore Recupero</Label>
            <Input
              id="ore_recupero"
              type="number"
              {...register("ore_recupero")}
              min={1}
              max={96}
            />
          </div>
        </div>
      </div>

      {/* ── Rep Ranges ── */}
      <div>
        <SectionHeader>Rep Ranges</SectionHeader>
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-2">
            <Label htmlFor="rep_range_forza" className="text-xs">Forza</Label>
            <Input
              id="rep_range_forza"
              {...register("rep_range_forza")}
              placeholder="3-6"
              className="text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rep_range_ipertrofia" className="text-xs">Ipertrofia</Label>
            <Input
              id="rep_range_ipertrofia"
              {...register("rep_range_ipertrofia")}
              placeholder="6-12"
              className="text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rep_range_resistenza" className="text-xs">Resistenza</Label>
            <Input
              id="rep_range_resistenza"
              {...register("rep_range_resistenza")}
              placeholder="15-20"
              className="text-sm"
            />
          </div>
        </div>
      </div>

      {/* ── Descrizioni (v2) ── */}
      <div>
        <SectionHeader>Descrizioni</SectionHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="descrizione_anatomica">Anatomia</Label>
            <Textarea
              id="descrizione_anatomica"
              {...register("descrizione_anatomica")}
              placeholder="Descrizione dei muscoli coinvolti e del loro ruolo..."
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="descrizione_biomeccanica">Biomeccanica</Label>
            <Textarea
              id="descrizione_biomeccanica"
              {...register("descrizione_biomeccanica")}
              placeholder="Analisi delle leve articolari e della curva di resistenza..."
              rows={3}
            />
          </div>
        </div>
      </div>

      {/* ── Esecuzione (v2) ── */}
      <div>
        <SectionHeader>Esecuzione</SectionHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="setup_desc">Posizione Iniziale</Label>
            <Textarea
              id="setup_desc"
              {...register("setup")}
              placeholder="Descrivi la posizione di partenza..."
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="esecuzione">Movimento</Label>
            <Textarea
              id="esecuzione"
              {...register("esecuzione")}
              placeholder="Descrivi il movimento step by step..."
              rows={3}
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="respirazione">Respirazione</Label>
              <Input
                id="respirazione"
                {...register("respirazione")}
                placeholder="es. Espira in fase concentrica"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tempo_consigliato">Tempo</Label>
              <Input
                id="tempo_consigliato"
                {...register("tempo_consigliato")}
                placeholder="es. 3-1-2-0"
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Coaching Cues (v2) ── */}
      <div>
        <SectionHeader>Coaching Cues</SectionHeader>
        <div className="space-y-2">
          {cueFields.map((field, index) => (
            <div key={field.id} className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground w-5 text-right">{index + 1}.</span>
              <Input
                {...register(`coaching_cues.${index}.value`)}
                placeholder="es. Petto in fuori, scapole addotte"
                className="text-sm"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0"
                onClick={() => removeCue(index)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => appendCue({ value: "" })}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Aggiungi cue
          </Button>
        </div>
      </div>

      {/* ── Errori Comuni (v2) ── */}
      <div>
        <SectionHeader>Errori Comuni</SectionHeader>
        <div className="space-y-3">
          {errorFields.map((field, index) => (
            <div key={field.id} className="flex items-start gap-2 rounded-md border p-3">
              <div className="flex-1 space-y-2">
                <Input
                  {...register(`errori_comuni.${index}.errore`)}
                  placeholder="Errore (es. Schiena inarcata)"
                  className="text-sm border-red-200 focus-visible:border-red-400"
                />
                <Input
                  {...register(`errori_comuni.${index}.correzione`)}
                  placeholder="Correzione (es. Attiva il core prima di spingere)"
                  className="text-sm border-green-200 focus-visible:border-green-400"
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0 mt-1"
                onClick={() => removeError(index)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => appendError({ errore: "", correzione: "" })}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Aggiungi errore
          </Button>
        </div>
      </div>

      {/* ── Sicurezza (v2) ── */}
      <div>
        <SectionHeader>Sicurezza</SectionHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="note_sicurezza">Note di Sicurezza</Label>
            <Textarea
              id="note_sicurezza"
              {...register("note_sicurezza")}
              placeholder="Precauzioni e avvertenze per l'esecuzione..."
              rows={2}
            />
          </div>
          <div>
            <Label className="mb-2 block">Controindicazioni</Label>
            <div className="space-y-2">
              {controFields.map((field, index) => (
                <div key={field.id} className="flex items-center gap-2">
                  <Input
                    {...register(`controindicazioni.${index}.value`)}
                    placeholder="es. Ernia del disco, Lesione cuffia rotatori"
                    className="text-sm"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={() => removeContro(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => appendContro({ value: "" })}
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                Aggiungi controindicazione
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Submit ── */}
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isEdit ? "Salva Modifiche" : "Crea Esercizio"}
      </Button>
    </form>
  );
}
