// src/components/exercises/ExerciseForm.tsx
"use client";

/**
 * Form per creare/modificare un esercizio custom.
 * Zod schema per validazione client-side.
 * Campi organizzati in sezioni logiche.
 */

import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
} from "./exercise-constants";
import type { Exercise } from "@/types/api";

// ════════════════════════════════════════════════════════════
// ZOD SCHEMA
// ════════════════════════════════════════════════════════════

const exerciseSchema = z.object({
  nome: z.string().min(1, "Nome obbligatorio").max(200),
  nome_en: z.string().max(200).optional(),
  categoria: z.string().min(1, "Categoria obbligatoria"),
  pattern_movimento: z.string().min(1, "Pattern obbligatorio"),
  muscoli_primari: z.array(z.string()).min(1, "Seleziona almeno un muscolo"),
  muscoli_secondari: z.array(z.string()).optional(),
  attrezzatura: z.string().min(1, "Attrezzatura obbligatoria"),
  difficolta: z.string().min(1, "Difficolta' obbligatoria"),
  rep_range_forza: z.string().max(20).optional(),
  rep_range_ipertrofia: z.string().max(20).optional(),
  rep_range_resistenza: z.string().max(20).optional(),
  ore_recupero: z.coerce.number().int().min(1).max(96).optional(),
});

export type ExerciseFormValues = z.infer<typeof exerciseSchema>;

interface ExerciseFormProps {
  exercise?: Exercise | null;
  onSubmit: (values: ExerciseFormValues) => void;
  isPending: boolean;
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
    formState: { errors },
  } = useForm<ExerciseFormValues>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(exerciseSchema) as any,
    defaultValues: {
      nome: exercise?.nome ?? "",
      nome_en: exercise?.nome_en ?? "",
      categoria: exercise?.categoria ?? "",
      pattern_movimento: exercise?.pattern_movimento ?? "",
      muscoli_primari: exercise?.muscoli_primari ?? [],
      muscoli_secondari: exercise?.muscoli_secondari ?? [],
      attrezzatura: exercise?.attrezzatura ?? "",
      difficolta: exercise?.difficolta ?? "",
      rep_range_forza: exercise?.rep_range_forza ?? "",
      rep_range_ipertrofia: exercise?.rep_range_ipertrofia ?? "",
      rep_range_resistenza: exercise?.rep_range_resistenza ?? "",
      ore_recupero: exercise?.ore_recupero ?? 48,
    },
  });

  const muscoliPrimari = watch("muscoli_primari");
  const muscoliSecondari = watch("muscoli_secondari");

  const handleFormSubmit = (values: ExerciseFormValues) => {
    const cleaned = {
      ...values,
      nome_en: values.nome_en || undefined,
      rep_range_forza: values.rep_range_forza || undefined,
      rep_range_ipertrofia: values.rep_range_ipertrofia || undefined,
      rep_range_resistenza: values.rep_range_resistenza || undefined,
      muscoli_secondari: values.muscoli_secondari?.length ? values.muscoli_secondari : undefined,
    };
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
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Identita&apos;
        </h3>
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
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Classificazione
        </h3>
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

      {/* ── Muscoli Primari ── */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Muscoli Primari *
        </h3>
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
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Muscoli Secondari
        </h3>
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

      {/* ── Setup ── */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Setup
        </h3>
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
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Rep Ranges
        </h3>
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

      {/* ── Submit ── */}
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isEdit ? "Salva Modifiche" : "Crea Esercizio"}
      </Button>
    </form>
  );
}
