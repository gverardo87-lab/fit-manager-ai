// src/components/movements/MovementForm.tsx
"use client";

/**
 * Form creazione movimento manuale.
 *
 * Campi: Tipo, Importo, Categoria, Metodo, Data, Note.
 * Validazione Zod + react-hook-form.
 */

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { format } from "date-fns";
import { Loader2 } from "lucide-react";

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
import { DatePicker } from "@/components/ui/date-picker";
import { PAYMENT_METHODS, MOVEMENT_TYPES } from "@/types/api";

// ── Categorie manuali comuni per PT ──

const MOVEMENT_CATEGORIES = [
  "Sessione",
  "Affitto",
  "Attrezzatura",
  "Marketing",
  "Assicurazione",
  "Utenze",
  "Formazione",
  "Trasporto",
  "Altro",
] as const;

// ── Schema Zod ──

const movementSchema = z.object({
  tipo: z.enum(MOVEMENT_TYPES),
  importo: z.number({ error: "Importo richiesto" }).positive("Deve essere > 0"),
  categoria: z.string().optional(),
  metodo: z.string().optional(),
  data_effettiva: z.date({ error: "Data richiesta" }),
  note: z.string().max(500).optional(),
});

export type MovementFormValues = z.infer<typeof movementSchema>;

// ── Props ──

interface MovementFormProps {
  onSubmit: (values: MovementFormValues) => void;
  isPending: boolean;
}

// ── Component ──

export function MovementForm({ onSubmit, isPending }: MovementFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<MovementFormValues>({
    resolver: zodResolver(movementSchema),
    defaultValues: {
      tipo: "USCITA",
      importo: undefined,
      categoria: undefined,
      metodo: undefined,
      data_effettiva: new Date(),
      note: "",
    },
  });

  const tipoValue = watch("tipo");
  const dataValue = watch("data_effettiva");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {/* ── Tipo ── */}
      <div className="space-y-2">
        <Label>Tipo Movimento</Label>
        <Select
          value={tipoValue}
          onValueChange={(v) => setValue("tipo", v as "ENTRATA" | "USCITA")}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {MOVEMENT_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {t === "ENTRATA" ? "Entrata" : "Uscita"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.tipo && (
          <p className="text-xs text-destructive">{errors.tipo.message}</p>
        )}
      </div>

      {/* ── Importo + Data ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="importo">Importo</Label>
          <Input
            id="importo"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0,00"
            {...register("importo", { valueAsNumber: true })}
          />
          {errors.importo && (
            <p className="text-xs text-destructive">{errors.importo.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label>Data Effettiva</Label>
          <DatePicker
            value={dataValue}
            onChange={(d) => d && setValue("data_effettiva", d)}
            placeholder="Seleziona data..."
          />
          {errors.data_effettiva && (
            <p className="text-xs text-destructive">
              {errors.data_effettiva.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Categoria + Metodo ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Categoria</Label>
          <Select
            value={watch("categoria") ?? ""}
            onValueChange={(v) => setValue("categoria", v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleziona..." />
            </SelectTrigger>
            <SelectContent>
              {MOVEMENT_CATEGORIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Metodo Pagamento</Label>
          <Select
            value={watch("metodo") ?? ""}
            onValueChange={(v) => setValue("metodo", v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleziona..." />
            </SelectTrigger>
            <SelectContent>
              {PAYMENT_METHODS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* ── Note ── */}
      <div className="space-y-2">
        <Label htmlFor="note">Note</Label>
        <Textarea
          id="note"
          placeholder="Descrizione del movimento..."
          rows={3}
          {...register("note")}
        />
        {errors.note && (
          <p className="text-xs text-destructive">{errors.note.message}</p>
        )}
      </div>

      {/* ── Submit ── */}
      <Button type="submit" disabled={isPending} className="w-full">
        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        Registra Movimento
      </Button>
    </form>
  );
}
