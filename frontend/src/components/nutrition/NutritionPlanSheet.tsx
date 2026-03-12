// src/components/nutrition/NutritionPlanSheet.tsx
"use client";

/**
 * Sheet per creare / modificare un piano alimentare.
 *
 * Campi: nome, obiettivo calorico, target macro (P/C/G),
 *        note cliniche, date inizio/fine, stato attivo.
 *
 * Pattern: stessa struttura di ContractSheet / ClientSheet.
 */

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

import {
  useCreateNutritionPlan,
  useUpdateNutritionPlan,
} from "@/hooks/useNutrition";
import type { NutritionPlan } from "@/types/api";

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

// ── Props ─────────────────────────────────────────────────────────────────

interface NutritionPlanSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: number;
  plan: NutritionPlan | null;   // null = create mode
}

// ── Componente ────────────────────────────────────────────────────────────

export function NutritionPlanSheet({ open, onOpenChange, clientId, plan }: NutritionPlanSheetProps) {
  const isEdit = plan !== null;
  const create = useCreateNutritionPlan(clientId);
  const update = useUpdateNutritionPlan(clientId);
  const isPending = create.isPending || update.isPending;

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

  // Sync form quando si edita un piano esistente
  useEffect(() => {
    if (plan) {
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

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="mt-6 space-y-5">

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
              <Button type="submit" className="flex-1" disabled={isPending}>
                {isPending ? "Salvo..." : isEdit ? "Salva modifiche" : "Crea piano"}
              </Button>
            </div>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
