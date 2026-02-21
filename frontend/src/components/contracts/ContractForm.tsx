// src/components/contracts/ContractForm.tsx
"use client";

/**
 * Form contratto — creazione e modifica.
 *
 * Sfide relazionali risolte:
 * - id_cliente: Select popolato da useClients() → nome visibile, id inviato
 * - Date: DatePicker (Popover + Calendar) con formattazione italiana
 * - Acconto: campo condizionale, visibile solo in creazione
 * - Metodo acconto: appare solo quando acconto > 0 (allineato al backend)
 */

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format, parseISO } from "date-fns";
import { Loader2 } from "lucide-react";

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
import { DatePicker } from "@/components/ui/date-picker";
import { useClients } from "@/hooks/useClients";
import type { Contract } from "@/types/api";
import { PAYMENT_METHODS } from "@/types/api";

// ── Zod schema (allineato a api/schemas/financial.py ContractCreate) ──

const contractSchema = z
  .object({
    id_cliente: z.number({ error: "Seleziona un cliente" }).gt(0),
    tipo_pacchetto: z.string().min(1, "Tipo pacchetto obbligatorio").max(100),
    crediti_totali: z.number().int().min(1, "Minimo 1 credito").max(1000),
    prezzo_totale: z.number().min(0).max(1_000_000),
    data_inizio: z.date({ error: "Data inizio obbligatoria" }),
    data_scadenza: z.date({ error: "Data scadenza obbligatoria" }),
    acconto: z.number().min(0).max(1_000_000).optional(),
    metodo_acconto: z.string().optional(),
    note: z.string().max(500).optional(),
  })
  .refine((data) => data.data_scadenza > data.data_inizio, {
    message: "La scadenza deve essere dopo la data inizio",
    path: ["data_scadenza"],
  })
  .refine(
    (data) => !data.acconto || data.acconto <= data.prezzo_totale,
    {
      message: "L'acconto non puo' superare il prezzo totale",
      path: ["acconto"],
    }
  )
  .refine(
    (data) => !data.acconto || data.acconto === 0 || data.metodo_acconto,
    {
      message: "Metodo pagamento obbligatorio con acconto",
      path: ["metodo_acconto"],
    }
  );

export type ContractFormValues = z.infer<typeof contractSchema>;

interface ContractFormProps {
  contract?: Contract | null;
  onSubmit: (values: ContractFormValues) => void;
  isPending: boolean;
}

export function ContractForm({
  contract,
  onSubmit,
  isPending,
}: ContractFormProps) {
  const isEdit = !!contract;
  const { data: clientsData } = useClients({ pageSize: 200 });

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ContractFormValues>({
    resolver: zodResolver(contractSchema),
    defaultValues: {
      id_cliente: contract?.id_cliente ?? undefined,
      tipo_pacchetto: contract?.tipo_pacchetto ?? "",
      crediti_totali: contract?.crediti_totali ?? 10,
      prezzo_totale: contract?.prezzo_totale ?? 0,
      data_inizio: contract?.data_inizio
        ? parseISO(contract.data_inizio)
        : undefined,
      data_scadenza: contract?.data_scadenza
        ? parseISO(contract.data_scadenza)
        : undefined,
      acconto: 0,
      metodo_acconto: undefined,
      note: contract?.note ?? "",
    },
  });

  const accontoValue = watch("acconto") ?? 0;

  const handleFormSubmit = (values: ContractFormValues) => {
    // Converti Date in string ISO per il backend
    const payload = {
      ...values,
      data_inizio: format(values.data_inizio, "yyyy-MM-dd") as unknown as Date,
      data_scadenza: format(values.data_scadenza, "yyyy-MM-dd") as unknown as Date,
      note: values.note || undefined,
      acconto: values.acconto || 0,
      metodo_acconto: values.metodo_acconto || undefined,
    };
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      {/* ── Cliente (Select relazionale) ── */}
      <div className="space-y-2">
        <Label>Cliente *</Label>
        <Controller
          control={control}
          name="id_cliente"
          render={({ field }) => (
            <Select
              value={field.value?.toString() ?? ""}
              onValueChange={(v) => field.onChange(parseInt(v, 10))}
              disabled={isEdit}
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
        {errors.id_cliente && (
          <p className="text-sm text-destructive">
            {errors.id_cliente.message}
          </p>
        )}
      </div>

      {/* ── Tipo Pacchetto / Crediti ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="tipo_pacchetto">Tipo Pacchetto *</Label>
          <Input id="tipo_pacchetto" {...register("tipo_pacchetto")} />
          {errors.tipo_pacchetto && (
            <p className="text-sm text-destructive">
              {errors.tipo_pacchetto.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="crediti_totali">Crediti *</Label>
          <Input
            id="crediti_totali"
            type="number"
            {...register("crediti_totali", { valueAsNumber: true })}
          />
          {errors.crediti_totali && (
            <p className="text-sm text-destructive">
              {errors.crediti_totali.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Prezzo Totale ── */}
      <div className="space-y-2">
        <Label htmlFor="prezzo_totale">Prezzo Totale (EUR) *</Label>
        <Input
          id="prezzo_totale"
          type="number"
          step="0.01"
          {...register("prezzo_totale", { valueAsNumber: true })}
        />
        {errors.prezzo_totale && (
          <p className="text-sm text-destructive">
            {errors.prezzo_totale.message}
          </p>
        )}
      </div>

      {/* ── Date ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Data Inizio *</Label>
          <Controller
            control={control}
            name="data_inizio"
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                placeholder="Inizio..."
              />
            )}
          />
          {errors.data_inizio && (
            <p className="text-sm text-destructive">
              {errors.data_inizio.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label>Data Scadenza *</Label>
          <Controller
            control={control}
            name="data_scadenza"
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                placeholder="Scadenza..."
              />
            )}
          />
          {errors.data_scadenza && (
            <p className="text-sm text-destructive">
              {errors.data_scadenza.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Acconto (solo in creazione) ── */}
      {!isEdit && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="acconto">Acconto (EUR)</Label>
              <Input
                id="acconto"
                type="number"
                step="0.01"
                {...register("acconto", { valueAsNumber: true })}
              />
              {errors.acconto && (
                <p className="text-sm text-destructive">
                  {errors.acconto.message}
                </p>
              )}
            </div>
            {accontoValue > 0 && (
              <div className="space-y-2">
                <Label>Metodo Pagamento</Label>
                <Select
                  value={watch("metodo_acconto") ?? ""}
                  onValueChange={(v) =>
                    setValue("metodo_acconto", v, { shouldValidate: true })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Metodo..." />
                  </SelectTrigger>
                  <SelectContent>
                    {PAYMENT_METHODS.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.metodo_acconto && (
                  <p className="text-sm text-destructive">
                    {errors.metodo_acconto.message}
                  </p>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Note ── */}
      <div className="space-y-2">
        <Label htmlFor="note">Note</Label>
        <Input id="note" {...register("note")} />
        {errors.note && (
          <p className="text-sm text-destructive">{errors.note.message}</p>
        )}
      </div>

      {/* ── Submit ── */}
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isEdit ? "Salva Modifiche" : "Crea Contratto"}
      </Button>
    </form>
  );
}
