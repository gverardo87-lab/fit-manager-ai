"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation } from "@tanstack/react-query"
import { Loader2, Dumbbell, Sparkles } from "lucide-react"
import type { AxiosError } from "axios"

import apiClient from "@/lib/api-client"
import { register } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

const setupSchema = z.object({
  nome: z.string().min(1, "Il nome e' obbligatorio").max(100),
  cognome: z.string().min(1, "Il cognome e' obbligatorio").max(100),
  email: z
    .string()
    .min(1, "L'email e' obbligatoria")
    .email("Inserisci un'email valida"),
  password: z
    .string()
    .min(8, "La password deve avere almeno 8 caratteri")
    .max(128),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Le password non coincidono",
  path: ["confirmPassword"],
})

type SetupFormValues = z.infer<typeof setupSchema>

export default function SetupPage() {
  const router = useRouter()
  const [serverError, setServerError] = useState<string | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    apiClient
      .get<{ needs_setup: boolean }>("/auth/setup-status")
      .then(({ data }) => {
        if (!data.needs_setup) {
          router.replace("/login")
        } else {
          setChecking(false)
        }
      })
      .catch(() => {
        setChecking(false)
      })
  }, [router])

  const form = useForm<SetupFormValues>({
    resolver: zodResolver(setupSchema),
    defaultValues: {
      nome: "",
      cognome: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  })

  const registerMutation = useMutation({
    mutationFn: (values: SetupFormValues) =>
      register({
        nome: values.nome,
        cognome: values.cognome,
        email: values.email,
        password: values.password,
      }),
    onSuccess: () => {
      router.push("/")
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const detail = error.response?.data?.detail
      if (error.response?.status === 409) {
        setServerError(detail || "Email gia' registrata")
      } else {
        setServerError(detail || "Errore durante la creazione dell'account")
      }
    },
  })

  function onSubmit(values: SetupFormValues) {
    setServerError(null)
    registerMutation.mutate(values)
  }

  if (checking) {
    return (
      <div className="bg-mesh-login flex min-h-screen items-center justify-center">
        <Loader2 className="text-primary h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="bg-mesh-login relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
      <div className="pointer-events-none absolute -left-20 -top-20 h-80 w-80 rounded-full bg-primary/8 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -right-20 h-80 w-80 rounded-full bg-primary/6 blur-3xl" />

      <Card className="relative w-full max-w-sm shadow-lg sm:max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10">
            <Dumbbell className="text-primary h-7 w-7" />
          </div>
          <div className="flex items-center justify-center gap-2">
            <Sparkles className="text-primary h-5 w-5" />
            <CardTitle className="text-2xl font-bold tracking-tight">
              Benvenuto in ProFit AI Studio
            </CardTitle>
          </div>
          <CardDescription>
            Configura il tuo account per iniziare a gestire clienti, contratti e allenamenti.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="nome"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nome</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Mario"
                          autoComplete="given-name"
                          disabled={registerMutation.isPending}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="cognome"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Cognome</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Rossi"
                          autoComplete="family-name"
                          disabled={registerMutation.isPending}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

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
                        disabled={registerMutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Minimo 8 caratteri"
                        autoComplete="new-password"
                        disabled={registerMutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="confirmPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Conferma password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Ripeti la password"
                        autoComplete="new-password"
                        disabled={registerMutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {serverError && (
                <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {serverError}
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={registerMutation.isPending}
              >
                {registerMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creazione in corso...
                  </>
                ) : (
                  "Crea account e inizia"
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
