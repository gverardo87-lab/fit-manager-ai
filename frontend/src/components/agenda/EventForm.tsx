// src/components/agenda/EventForm.tsx
"use client";

/**
 * Form evento — creazione e modifica.
 *
 * Campi:
 * - Titolo, Categoria, Stato
 * - Cliente (opzionale, solo per PT e CONSULENZA)
 * - Data/Ora inizio e fine (DatePicker + Input time)
 * - Note
 *
 * Le date vengono combinate con gli orari in stringhe ISO per il backend.
 */

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format } from "date-fns";
import { Loader2, Trash2 } from "lucide-react";

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
import { useClients } from "@/hooks/useClients";
import { EVENT_CATEGORIES, EVENT_STATUSES } from "@/types/api";
import { CATEGORY_LABELS } from "./calendar-setup";
import type { CalendarEvent } from "./calendar-setup";

// ── Zod schema ──

const eventSchema = z
  .object({
    titolo: z.string().min(1, "Titolo obbligatorio").max(200),
    categoria: z.string().min(1, "Categoria obbligatoria"),
    stato: z.string().min(1, "Stato obbligatorio"),
    id_cliente: z.number().gt(0).optional(),
    data_inizio_date: z.date({ message: "Data inizio obbligatoria" }),
    ora_inizio: z.string().min(1, "Ora inizio obbligatoria"),
    data_fine_date: z.date({ message: "Data fine obbligatoria" }),
    ora_fine: z.string().min(1, "Ora fine obbligatoria"),
    note: z.string().max(500).optional(),
  })
  .refine(
    (data) => {
      const start = combineDateAndTime(data.data_inizio_date, data.ora_inizio);
      const end = combineDateAndTime(data.data_fine_date, data.ora_fine);
      return end > start;
    },
    { message: "La fine deve essere dopo l'inizio", path: ["ora_fine"] }
  );

export type EventFormValues = z.infer<typeof eventSchema>;

/** Combina Date + "HH:MM" in un singolo Date object. */
function combineDateAndTime(date: Date, time: string): Date {
  const [hours, minutes] = time.split(":").map(Number);
  const result = new Date(date);
  result.setHours(hours, minutes, 0, 0);
  return result;
}

/** Converte Date in stringa ISO senza timezone per il backend. */
function toISOLocal(date: Date): string {
  return format(date, "yyyy-MM-dd'T'HH:mm:ss");
}

// ── Valori di submit finali (per il backend) ──

export interface EventSubmitPayload {
  titolo: string;
  categoria: string;
  stato: string;
  id_cliente?: number | null;
  data_inizio: string;
  data_fine: string;
  note?: string | null;
}

interface EventFormProps {
  event?: CalendarEvent | null;
  defaultStart?: Date;
  defaultEnd?: Date;
  onSubmit: (values: EventSubmitPayload) => void;
  onDelete?: () => void;
  isPending: boolean;
}

export function EventForm({
  event,
  defaultStart,
  defaultEnd,
  onSubmit,
  onDelete,
  isPending,
}: EventFormProps) {
  const isEdit = !!event;
  const { data: clientsData } = useClients({ pageSize: 200 });

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<EventFormValues>({
    resolver: zodResolver(eventSchema),
    defaultValues: {
      titolo: event?.title ?? "",
      categoria: event?.categoria ?? "PT",
      stato: event?.stato ?? "Programmato",
      id_cliente: event?.id_cliente ?? undefined,
      data_inizio_date: event?.start ?? defaultStart ?? new Date(),
      ora_inizio: event?.start
        ? format(event.start, "HH:mm")
        : defaultStart
          ? format(defaultStart, "HH:mm")
          : "09:00",
      data_fine_date: event?.end ?? defaultEnd ?? new Date(),
      ora_fine: event?.end
        ? format(event.end, "HH:mm")
        : defaultEnd
          ? format(defaultEnd, "HH:mm")
          : "10:00",
      note: event?.note ?? "",
    },
  });

  const categoria = watch("categoria");
  const showClientSelect = categoria === "PT" || categoria === "CONSULENZA";

  const handleFormSubmit = (values: EventFormValues) => {
    const start = combineDateAndTime(values.data_inizio_date, values.ora_inizio);
    const end = combineDateAndTime(values.data_fine_date, values.ora_fine);

    onSubmit({
      titolo: values.titolo,
      categoria: values.categoria,
      stato: values.stato,
      id_cliente: showClientSelect ? values.id_cliente ?? null : null,
      data_inizio: toISOLocal(start),
      data_fine: toISOLocal(end),
      note: values.note || null,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      {/* ── Titolo ── */}
      <div className="space-y-2">
        <Label htmlFor="titolo">Titolo *</Label>
        <Input id="titolo" placeholder="es. PT con Mario" {...register("titolo")} />
        {errors.titolo && (
          <p className="text-sm text-destructive">{errors.titolo.message}</p>
        )}
      </div>

      {/* ── Categoria + Stato ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Categoria *</Label>
          <Controller
            control={control}
            name="categoria"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={isEdit}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Categoria..." />
                </SelectTrigger>
                <SelectContent>
                  {EVENT_CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {CATEGORY_LABELS[cat]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.categoria && (
            <p className="text-sm text-destructive">
              {errors.categoria.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label>Stato *</Label>
          <Controller
            control={control}
            name="stato"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Stato..." />
                </SelectTrigger>
                <SelectContent>
                  {EVENT_STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.stato && (
            <p className="text-sm text-destructive">{errors.stato.message}</p>
          )}
        </div>
      </div>

      {/* ── Cliente (solo PT / CONSULENZA) ── */}
      {showClientSelect && (
        <div className="space-y-2">
          <Label>Cliente</Label>
          <Controller
            control={control}
            name="id_cliente"
            render={({ field }) => (
              <Select
                value={field.value?.toString() ?? ""}
                onValueChange={(v) => field.onChange(v ? parseInt(v, 10) : undefined)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona cliente..." />
                </SelectTrigger>
                <SelectContent>
                  {clientsData?.items.map((client) => (
                    <SelectItem key={client.id} value={client.id.toString()}>
                      {client.cognome} {client.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      )}

      {/* ── Data Inizio + Ora Inizio ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Data Inizio *</Label>
          <Controller
            control={control}
            name="data_inizio_date"
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                placeholder="Inizio..."
              />
            )}
          />
          {errors.data_inizio_date && (
            <p className="text-sm text-destructive">
              {errors.data_inizio_date.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="ora_inizio">Ora Inizio *</Label>
          <Input id="ora_inizio" type="time" {...register("ora_inizio")} />
          {errors.ora_inizio && (
            <p className="text-sm text-destructive">
              {errors.ora_inizio.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Data Fine + Ora Fine ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Data Fine *</Label>
          <Controller
            control={control}
            name="data_fine_date"
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                placeholder="Fine..."
              />
            )}
          />
          {errors.data_fine_date && (
            <p className="text-sm text-destructive">
              {errors.data_fine_date.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="ora_fine">Ora Fine *</Label>
          <Input id="ora_fine" type="time" {...register("ora_fine")} />
          {errors.ora_fine && (
            <p className="text-sm text-destructive">
              {errors.ora_fine.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Note ── */}
      <div className="space-y-2">
        <Label htmlFor="note">Note</Label>
        <Textarea
          id="note"
          placeholder="Note aggiuntive..."
          rows={3}
          {...register("note")}
        />
        {errors.note && (
          <p className="text-sm text-destructive">{errors.note.message}</p>
        )}
      </div>

      {/* ── Azioni ── */}
      <div className="flex gap-3">
        {isEdit && onDelete && (
          <Button
            type="button"
            variant="outline"
            className="text-destructive hover:text-destructive"
            onClick={onDelete}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Elimina
          </Button>
        )}
        <Button type="submit" className="flex-1" disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isEdit ? "Salva Modifiche" : "Crea Evento"}
        </Button>
      </div>
    </form>
  );
}
