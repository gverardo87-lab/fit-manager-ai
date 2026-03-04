// src/app/login/page.tsx
"use client";

/**
 * Login Page — UI SaaS moderna con shadcn/ui.
 *
 * Architettura:
 * - react-hook-form + zod per validazione client-side
 * - useMutation (React Query) per la chiamata API — zero useEffect
 * - auth.ts login() salva il JWT nel cookie
 * - useRouter redirect a / dopo login riuscito
 * - Errori dal backend (401, 403) mostrati inline
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Dumbbell } from "lucide-react";
import { AxiosError } from "axios";

import apiClient from "@/lib/api-client";
import { login } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

// ════════════════════════════════════════════════════════════
// VALIDAZIONE (Zod schema)
// ════════════════════════════════════════════════════════════

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "L'email e' obbligatoria")
    .email("Inserisci un'email valida"),
  password: z
    .string()
    .min(4, "La password deve avere almeno 4 caratteri"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export default function LoginPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  // Se non esiste nessun trainer, redirect al Setup Wizard
  useEffect(() => {
    apiClient
      .get<{ needs_setup: boolean }>("/auth/setup-status")
      .then(({ data }) => {
        if (data.needs_setup) router.replace("/setup");
      })
      .catch(() => {});
  }, [router]);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      router.push("/");
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const detail = error.response?.data?.detail;

      if (error.response?.status === 401) {
        setServerError(detail || "Email o password non corretti");
      } else if (error.response?.status === 403) {
        setServerError(detail || "Account disattivato");
      } else {
        setServerError("Errore di connessione. Riprova tra qualche secondo.");
      }
    },
  });

  function onSubmit(values: LoginFormValues) {
    setServerError(null);
    loginMutation.mutate(values);
  }

  return (
    <div className="bg-mesh-login relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      {/* Blob decorativi — profondità visiva, zero impatto layout */}
      <div className="pointer-events-none absolute -left-20 -top-20 h-80 w-80 rounded-full bg-primary/8 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -right-20 h-80 w-80 rounded-full bg-primary/6 blur-3xl" />

      <Card className="relative w-full max-w-sm shadow-lg sm:max-w-md">
        <CardHeader className="space-y-3 text-center">
          {/* Logo / Icona */}
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10">
            <Dumbbell className="h-7 w-7 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">
            ProFit AI Studio
          </CardTitle>
          <CardDescription>
            Accedi al tuo gestionale fitness
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {/* Email */}
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="nome@esempio.com"
                        autoComplete="email"
                        disabled={loginMutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Password */}
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="La tua password"
                        autoComplete="current-password"
                        disabled={loginMutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Errore dal server */}
              {serverError && (
                <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {serverError}
                </div>
              )}

              {/* Submit */}
              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Accesso in corso...
                  </>
                ) : (
                  "Accedi"
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
