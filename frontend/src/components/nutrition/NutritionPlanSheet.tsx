// src/components/nutrition/NutritionPlanSheet.tsx
"use client";

/**
 * Sheet per creare / modificare un piano alimentare.
 *
 * Create mode: mostra prima i template statici come punto di partenza rapido.
 * Selezionare un template pre-compila i macro target e le note cliniche.
 * L'utente può ignorare i template e compilare il form manualmente.
 *
 * Edit mode: solo il form (nessun template).
 */

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Check, Sparkles } from "lucide-react";

import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import {
  useCreateNutritionPlan,
  useUpdateNutritionPlan,
  usePlanTemplates,
} from "@/hooks/useNutrition";
import { useClients } from "@/hooks/useClients";
import type { NutritionPlan, NutritionPlanTemplate, ClientEnriched, ClientEnrichedListResponse } from "@/types/api";

// ── Schema validazione ────────────────────────────────────────────────────

const schema = z.object({
  nome: z.string().min(1, "Nome obbligatorio"),
  obiettivo_calorico: z.number().int().positive().nullable().optional(),
  proteine_g_target: z.number().int().positive().nullable().optional(),
  carboidrati_g_target: z.number().int().positive().nullable().optional(),
  grassi_g_target: z.number().int().positive().nullable().optional(),
  note_cliniche: z.string().nullable().optional(),
  data_inizio: z.string().nullable().optional(),
  data_fine: z.string().nullable().optional(),
  attivo: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

// ── Tag label → chip color ─────────────────────────────────────────────────

const TAG_COLOR: Record<string, string> = {
  uomo:       "bg-blue-50 text-blue-700 border-blue-200",
  donna:      "bg-pink-50 text-pink-700 border-pink-200",
  under30:    "bg-emerald-50 text-emerald-700 border-emerald-200",
  over30:     "bg-amber-50 text-amber-700 border-amber-200",
  sedentario: "bg-zinc-50 text-zinc-600 border-zinc-200",
  sedentaria: "bg-zinc-50 text-zinc-600 border-zinc-200",
  attivo:     "bg-teal-50 text-teal-700 border-teal-200",
  attiva:     "bg-teal-50 text-teal-700 border-teal-200",
  sportivo:   "bg-violet-50 text-violet-700 border-violet-200",
  sportiva:   "bg-violet-50 text-violet-700 border-violet-200",
};

// ── Template card ─────────────────────────────────────────────────────────

function TemplateCard({
  tmpl,
  selected,
  onSelect,
}: {
  tmpl: NutritionPlanTemplate;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-lg border p-3 transition-colors ${
        selected
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/40 hover:bg-muted/30"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate">{tmpl.nome}</div>
          <div className="text-xs text-muted-foreground mt-0.5">{tmpl.descrizione}</div>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {tmpl.tags.map((tag) => (
              <span
                key={tag}
                className={`rounded-full border px-2 py-0.5 text-xs font-medium ${TAG_COLOR[tag] ?? "bg-muted text-muted-foreground border-border"}`}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0 gap-1">
          {selected && <Check className="h-4 w-4 text-primary" />}
          <Badge variant="secondary" className="text-xs font-bold text-emerald-700 bg-emerald-50">
            {tmpl.obiettivo_calorico} kcal
          </Badge>
        </div>
      </div>
    </button>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────

interface NutritionPlanSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: number | null;   // null = selezione cliente dentro lo sheet
  plan: NutritionPlan | null;   // null = create mode
}

// ── Componente ────────────────────────────────────────────────────────────

export function NutritionPlanSheet({ open, onOpenChange, clientId, plan }: NutritionPlanSheetProps) {
  const isEdit = plan !== null;

  // Quando clientId è null (apertura da pagina globale) il trainer sceglie il cliente dentro lo sheet
  const [localClientId, setLocalClientId] = useState<number | null>(null);
  const effectiveClientId = clientId ?? localClientId;

  const { data: rawClients } = useClients();
  const clientsList: ClientEnriched[] = Array.isArray(rawClients)
    ? rawClients
    : (rawClients as ClientEnrichedListResponse)?.items ?? [];

  const create = useCreateNutritionPlan(effectiveClientId ?? 0);
  const update = useUpdateNutritionPlan(effectiveClientId ?? 0);
  const isPending = create.isPending || update.isPending;

  const { data: templates = [] } = usePlanTemplates();
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: "",
      obiettivo_calorico: null,
      proteine_g_target: null,
      carboidrati_g_target: null,
      grassi_g_target: null,
      note_cliniche: null,
      data_inizio: null,
      data_fine: null,
      attivo: true,
    },
  });

  // Reset stato locale quando lo sheet si chiude
  useEffect(() => {
    if (!open) {
      setLocalClientId(null);
      setSelectedTemplateId(null);
    }
  }, [open]);

  // Sync form quando si edita un piano esistente
  useEffect(() => {
    if (plan) {
      setSelectedTemplateId(null);
      form.reset({
        nome: plan.nome,
        obiettivo_calorico: plan.obiettivo_calorico,
        proteine_g_target: plan.proteine_g_target,
        carboidrati_g_target: plan.carboidrati_g_target,
        grassi_g_target: plan.grassi_g_target,
        note_cliniche: plan.note_cliniche,
        data_inizio: plan.data_inizio,
        data_fine: plan.data_fine,
        attivo: plan.attivo,
      });
    } else {
      setSelectedTemplateId(null);
      form.reset({
        nome: "",
        obiettivo_calorico: null,
        proteine_g_target: null,
        carboidrati_g_target: null,
        grassi_g_target: null,
        note_cliniche: null,
        data_inizio: null,
        data_fine: null,
        attivo: true,
      });
    }
  }, [plan, form]);

  const handleSelectTemplate = (tmpl: NutritionPlanTemplate) => {
    if (selectedTemplateId === tmpl.id) {
      // deseleziona — resetta macro
      setSelectedTemplateId(null);
      form.setValue("obiettivo_calorico", null);
      form.setValue("proteine_g_target", null);
      form.setValue("carboidrati_g_target", null);
      form.setValue("grassi_g_target", null);
      form.setValue("note_cliniche", null);
    } else {
      setSelectedTemplateId(tmpl.id);
      form.setValue("obiettivo_calorico", tmpl.obiettivo_calorico);
      form.setValue("proteine_g_target", tmpl.proteine_g_target);
      form.setValue("carboidrati_g_target", tmpl.carboidrati_g_target);
      form.setValue("grassi_g_target", tmpl.grassi_g_target);
      form.setValue("note_cliniche", tmpl.note_cliniche);
      // Pre-compila nome se vuoto
      if (!form.getValues("nome")) {
        form.setValue("nome", tmpl.nome);
      }
    }
  };

  const onSubmit = async (values: FormValues) => {
    const payload = {
      nome: values.nome,
      obiettivo_calorico: values.obiettivo_calorico || null,
      proteine_g_target: values.proteine_g_target || null,
      carboidrati_g_target: values.carboidrati_g_target || null,
      grassi_g_target: values.grassi_g_target || null,
      note_cliniche: values.note_cliniche || null,
      data_inizio: values.data_inizio || null,
      data_fine: values.data_fine || null,
      attivo: values.attivo,
    };

    if (isEdit && plan) {
      await update.mutateAsync({ planId: plan.id, payload });
    } else {
      await create.mutateAsync(payload);
    }
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{isEdit ? "Modifica piano" : "Nuovo piano alimentare"}</SheetTitle>
          <SheetDescription>
            {isEdit
              ? "Aggiorna nome, target macro e note del piano."
              : "Crea un piano alimentare personalizzato per il cliente."}
          </SheetDescription>
        </SheetHeader>

        {/* Selettore cliente — solo quando non passato come prop */}
        {!isEdit && clientId === null && (
          <div className="mt-5 space-y-1.5">
            <p className="text-sm font-medium">Cliente</p>
            <Select
              value={localClientId ? String(localClientId) : ""}
              onValueChange={(v) => setLocalClientId(Number(v))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona un cliente…" />
              </SelectTrigger>
              <SelectContent>
                {clientsList
                  .filter((c) => c.stato?.toLowerCase() !== "inattivo")
                  .sort((a, b) => a.cognome.localeCompare(b.cognome))
                  .map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.cognome} {c.nome}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Template picker — solo in create mode */}
        {!isEdit && templates.length > 0 && (
          <div className="mt-5 space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-500" />
              <p className="text-sm font-semibold">Parti da un modello</p>
              <span className="text-xs text-muted-foreground">(opzionale)</span>
            </div>
            <div className="grid grid-cols-1 gap-2 max-h-[280px] overflow-y-auto pr-0.5">
              {templates.map((tmpl) => (
                <TemplateCard
                  key={tmpl.id}
                  tmpl={tmpl}
                  selected={selectedTemplateId === tmpl.id}
                  onSelect={() => handleSelectTemplate(tmpl)}
                />
              ))}
            </div>
            <Separator className="mt-3" />
          </div>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="mt-5 space-y-5">

            {/* Nome */}
            <FormField control={form.control} name="nome" render={({ field }) => (
              <FormItem>
                <FormLabel>Nome piano</FormLabel>
                <FormControl>
                  <Input placeholder="Es. Piano ipocalorico estate 2026" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            {/* Target calorico */}
            <FormField control={form.control} name="obiettivo_calorico" render={({ field }) => (
              <FormItem>
                <FormLabel>Obiettivo calorico (kcal/die)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="Es. 1800"
                    {...field}
                    value={field.value ?? ""}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            {/* Target macro — griglia 3 colonne */}
            <div className="grid grid-cols-3 gap-3">
              <FormField control={form.control} name="proteine_g_target" render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs">Proteine (g)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="140"
                      {...field}
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="carboidrati_g_target" render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs">Carboidrati (g)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="180"
                      {...field}
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="grassi_g_target" render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs">Grassi (g)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="60"
                      {...field}
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </div>

            {/* Date */}
            <div className="grid grid-cols-2 gap-3">
              <FormField control={form.control} name="data_inizio" render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs">Data inizio</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} value={field.value ?? ""} onChange={(e) => field.onChange(e.target.value || null)} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="data_fine" render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs">Data fine</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} value={field.value ?? ""} onChange={(e) => field.onChange(e.target.value || null)} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </div>

            {/* Note cliniche */}
            <FormField control={form.control} name="note_cliniche" render={({ field }) => (
              <FormItem>
                <FormLabel>Note cliniche</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Indicazioni cliniche, intolleranze, preferenze alimentari..."
                    rows={3}
                    {...field}
                    value={field.value ?? ""}
                    onChange={(e) => field.onChange(e.target.value || null)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            {/* Piano attivo */}
            <FormField control={form.control} name="attivo" render={({ field }) => (
              <FormItem className="flex items-center gap-3 rounded-lg border p-3">
                <FormControl>
                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                </FormControl>
                <div>
                  <FormLabel className="text-sm font-medium">Piano attivo</FormLabel>
                  <p className="text-xs text-muted-foreground">Attivare questo piano disattiverà gli altri</p>
                </div>
              </FormItem>
            )} />

            {/* Footer */}
            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" className="flex-1" onClick={() => onOpenChange(false)}>
                Annulla
              </Button>
              <Button type="submit" className="flex-1" disabled={isPending || (!isEdit && effectiveClientId === null)}>
                {isPending ? "Salvo..." : isEdit ? "Salva modifiche" : "Crea piano"}
              </Button>
            </div>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
