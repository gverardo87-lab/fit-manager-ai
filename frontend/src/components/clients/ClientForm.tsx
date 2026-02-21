// src/components/clients/ClientForm.tsx
"use client";

/**
 * Form cliente — usato sia per creazione che per modifica.
 *
 * Validazione: zod schema allineato ai vincoli del backend (ClientCreate).
 * Il form si adatta in base alla prop `client`:
 * - null → modalita' creazione (campi vuoti, testo "Nuovo Cliente")
 * - Client → modalita' modifica (campi precompilati, testo "Modifica Cliente")
 */

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
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
import type { Client } from "@/types/api";

// ── Zod schema (allineato a api/routers/clients.py ClientCreate) ──

const clientSchema = z.object({
  nome: z.string().min(1, "Nome obbligatorio").max(100),
  cognome: z.string().min(1, "Cognome obbligatorio").max(100),
  telefono: z
    .string()
    .refine(
      (val) => val === "" || /^[+]?[0-9\s\-()]{6,20}$/.test(val),
      { message: "Telefono non valido" }
    )
    .optional(),
  email: z
    .string()
    .refine(
      (val) => val === "" || /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(val),
      { message: "Email non valida" }
    )
    .optional(),
  data_nascita: z.string().optional(),
  sesso: z.enum(["Uomo", "Donna", "Altro"]).optional(),
  stato: z.enum(["Attivo", "Inattivo"]),
});

export type ClientFormValues = z.infer<typeof clientSchema>;

interface ClientFormProps {
  client?: Client | null;
  onSubmit: (values: ClientFormValues) => void;
  isPending: boolean;
}

export function ClientForm({ client, onSubmit, isPending }: ClientFormProps) {
  const isEdit = !!client;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ClientFormValues>({
    resolver: zodResolver(clientSchema),
    defaultValues: {
      nome: client?.nome ?? "",
      cognome: client?.cognome ?? "",
      telefono: client?.telefono ?? "",
      email: client?.email ?? "",
      data_nascita: client?.data_nascita ?? "",
      sesso: (client?.sesso as ClientFormValues["sesso"]) ?? undefined,
      stato: (client?.stato as "Attivo" | "Inattivo") ?? "Attivo",
    },
  });

  const handleFormSubmit = (values: ClientFormValues) => {
    // Converti stringhe vuote in undefined per il backend
    const cleaned = {
      ...values,
      telefono: values.telefono || undefined,
      email: values.email || undefined,
      data_nascita: values.data_nascita || undefined,
      sesso: values.sesso || undefined,
    };
    onSubmit(cleaned);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      {/* ── Nome / Cognome ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="nome">Nome *</Label>
          <Input id="nome" {...register("nome")} />
          {errors.nome && (
            <p className="text-sm text-destructive">{errors.nome.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="cognome">Cognome *</Label>
          <Input id="cognome" {...register("cognome")} />
          {errors.cognome && (
            <p className="text-sm text-destructive">
              {errors.cognome.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Email / Telefono ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...register("email")} />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="telefono">Telefono</Label>
          <Input id="telefono" {...register("telefono")} />
          {errors.telefono && (
            <p className="text-sm text-destructive">
              {errors.telefono.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Data Nascita / Sesso ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="data_nascita">Data di Nascita</Label>
          <Input id="data_nascita" type="date" {...register("data_nascita")} />
        </div>
        <div className="space-y-2">
          <Label>Sesso</Label>
          <Select
            value={watch("sesso") ?? ""}
            onValueChange={(v) =>
              setValue("sesso", v as ClientFormValues["sesso"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleziona..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Uomo">Uomo</SelectItem>
              <SelectItem value="Donna">Donna</SelectItem>
              <SelectItem value="Altro">Altro</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* ── Stato ── */}
      <div className="space-y-2">
        <Label>Stato</Label>
        <Select
          value={watch("stato")}
          onValueChange={(v) =>
            setValue("stato", v as "Attivo" | "Inattivo", {
              shouldValidate: true,
            })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Attivo">Attivo</SelectItem>
            <SelectItem value="Inattivo">Inattivo</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* ── Submit ── */}
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isEdit ? "Salva Modifiche" : "Crea Cliente"}
      </Button>
    </form>
  );
}
