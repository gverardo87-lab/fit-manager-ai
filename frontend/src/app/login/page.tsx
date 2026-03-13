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
import Image from "next/image";
import { Loader2, Eye, EyeOff, KeyRound } from "lucide-react";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

const resetSchema = z.object({
  email: z.string().min(1, "L'email e' obbligatoria").email("Inserisci un'email valida"),
  new_password: z.string().min(8, "La password deve avere almeno 8 caratteri"),
  confirm_password: z.string().min(1, "Conferma la password"),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Le password non corrispondono",
  path: ["confirm_password"],
});

type ResetFormValues = z.infer<typeof resetSchema>;

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export default function LoginPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);

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

  const resetForm = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { email: "", new_password: "", confirm_password: "" },
  });

  const resetMutation = useMutation({
    mutationFn: (data: { email: string; new_password: string }) =>
      apiClient.post("/auth/reset-password", data),
    onSuccess: () => {
      setResetSuccess(true);
      setResetError(null);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      setResetError(error.response?.data?.detail || "Errore durante il reset");
      setResetSuccess(false);
    },
  });

  function onResetSubmit(values: ResetFormValues) {
    setResetError(null);
    setResetSuccess(false);
    resetMutation.mutate({ email: values.email, new_password: values.new_password });
  }

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
        <CardHeader className="space-y-4 text-center">
          {/* Logo professionale */}
          <div className="mx-auto">
            <Image
              src="/logo_cb.png"
              alt="CB Chinesiologa"
              width={180}
              height={100}
              className="h-20 w-auto object-contain"
              priority
            />
          </div>
          <div>
            <CardTitle className="text-base font-semibold tracking-tight text-foreground/80">
              FitManager Studio+
            </CardTitle>
            <CardDescription className="mt-1">
              Accedi al tuo gestionale fitness
            </CardDescription>
          </div>
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
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="La tua password"
                          autoComplete="current-password"
                          disabled={loginMutation.isPending}
                          className="pr-10"
                          {...field}
                        />
                        <button
                          type="button"
                          tabIndex={-1}
                          onClick={() => setShowPassword((v) => !v)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-muted-foreground transition-colors"
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
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
              {/* Password dimenticata */}
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setResetOpen(true);
                    setResetSuccess(false);
                    setResetError(null);
                    resetForm.reset();
                  }}
                  className="text-xs text-muted-foreground hover:text-primary transition-colors"
                >
                  Password dimenticata?
                </button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* Dialog reset password */}
      <Dialog open={resetOpen} onOpenChange={setResetOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-primary" />
              Reimposta password
            </DialogTitle>
            <DialogDescription>
              Inserisci l&apos;email del tuo account e scegli una nuova password.
            </DialogDescription>
          </DialogHeader>

          {resetSuccess ? (
            <div className="space-y-3">
              <div className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
                Password aggiornata con successo! Ora puoi fare login.
              </div>
              <Button
                className="w-full"
                onClick={() => setResetOpen(false)}
              >
                Torna al login
              </Button>
            </div>
          ) : (
            <form onSubmit={resetForm.handleSubmit(onResetSubmit)} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input
                  type="email"
                  placeholder="nome@esempio.com"
                  {...resetForm.register("email")}
                />
                {resetForm.formState.errors.email && (
                  <p className="text-xs text-destructive">{resetForm.formState.errors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Nuova password</label>
                <Input
                  type="password"
                  placeholder="Minimo 8 caratteri"
                  {...resetForm.register("new_password")}
                />
                {resetForm.formState.errors.new_password && (
                  <p className="text-xs text-destructive">{resetForm.formState.errors.new_password.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Conferma password</label>
                <Input
                  type="password"
                  placeholder="Ripeti la password"
                  {...resetForm.register("confirm_password")}
                />
                {resetForm.formState.errors.confirm_password && (
                  <p className="text-xs text-destructive">{resetForm.formState.errors.confirm_password.message}</p>
                )}
              </div>

              {resetError && (
                <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {resetError}
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={resetMutation.isPending}
              >
                {resetMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Aggiornamento...
                  </>
                ) : (
                  "Reimposta password"
                )}
              </Button>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
