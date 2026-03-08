// src/app/public/anamnesi/[token]/page.tsx
"use client";

/**
 * Portale Clienti — Anamnesi Self-Service (v2).
 *
 * Pagina kiosk pubblica: nessun sidebar, nessuna auth.
 * Il cliente riceve il link via WhatsApp, compila il questionario
 * direttamente dal proprio smartphone.
 *
 * Flusso:
 *   1. Mount → GET /api/public/anamnesi/validate?token=X
 *   2. Token valido → wizard 6 step (riusa AnamnesiSteps)
 *   3. Submit → POST /api/public/anamnesi/submit
 *   4. Successo → pagina "Grazie"
 *   5. Errore → messaggio descrittivo (token scaduto / usato / non trovato)
 *
 * API: usa fetch() con URL relativo (/api/...) — Next.js proxy riscrive
 * verso il backend locale. Funziona sia su LAN che via Tailscale Funnel
 * senza modificare CORS o hardcodare IP.
 */

import { use, useCallback, useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Heart,
  Target,
  Dumbbell,
  ShieldCheck,
  Apple,
  MapPin,
  Save,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LogoIcon } from "@/components/ui/logo";
import {
  StepStileVita,
  StepObiettivo,
  StepEsperienza,
  StepSalute,
  StepAlimentazione,
  StepLogistica,
} from "@/components/clients/anamnesi/AnamnesiSteps";
import { getEmptyAnamnesi } from "@/components/clients/anamnesi/anamnesi-helpers";
import type { AnamnesiData, AnamnesiValidateResponse } from "@/types/api";

// ── Step definitions ─────────────────────────────────────────────────────────

const STEPS = [
  { title: "Stile di Vita", icon: Heart },
  { title: "Obiettivo", icon: Target },
  { title: "Esperienza", icon: Dumbbell },
  { title: "Salute", icon: ShieldCheck },
  { title: "Alimentazione", icon: Apple },
  { title: "Logistica", icon: MapPin },
] as const;

const STEP_COMPONENTS = [
  StepStileVita,
  StepObiettivo,
  StepEsperienza,
  StepSalute,
  StepAlimentazione,
  StepLogistica,
];

// ── API helpers (fetch relativo — Next.js proxy → backend) ───────────────────

async function validateToken(token: string): Promise<AnamnesiValidateResponse> {
  const res = await fetch(`/api/public/anamnesi/validate?token=${encodeURIComponent(token)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail ?? "Link non valido");
  }
  return res.json();
}

async function submitAnamnesi(token: string, anamnesi: AnamnesiData): Promise<void> {
  const res = await fetch("/api/public/anamnesi/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, anamnesi }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail ?? "Errore durante l'invio");
  }
}

// ── Page component ───────────────────────────────────────────────────────────

type Phase = "loading" | "form" | "success" | "error";

export default function PublicAnamnesiPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);

  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState("");
  const [info, setInfo] = useState<AnamnesiValidateResponse | null>(null);
  const [step, setStep] = useState(0);
  const [data, setData] = useState<AnamnesiData>(() => getEmptyAnamnesi());
  const [submitting, setSubmitting] = useState(false);
  const dirtyRef = useRef(false);

  // Valida token al mount
  useEffect(() => {
    validateToken(token)
      .then((res) => {
        setInfo(res);
        setPhase("form");
      })
      .catch((err: Error) => {
        setErrorMsg(err.message);
        setPhase("error");
      });
  }, [token]);

  // Protezione dati non salvati
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirtyRef.current && phase === "form") {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [phase]);

  const handleChange = useCallback((updates: Partial<AnamnesiData>) => {
    setData((prev) => ({ ...prev, ...updates }));
    dirtyRef.current = true;
  }, []);

  const handleSubmit = useCallback(async () => {
    setSubmitting(true);
    try {
      const now = new Date().toISOString().slice(0, 10);
      const payload: AnamnesiData = {
        ...data,
        data_compilazione: now,
        data_ultimo_aggiornamento: now,
      };
      await submitAnamnesi(token, payload);
      dirtyRef.current = false;
      setPhase("success");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Errore imprevisto");
      setPhase("error");
    } finally {
      setSubmitting(false);
    }
  }, [token, data]);

  const StepComponent = STEP_COMPONENTS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  return (
    <div className="min-h-screen bg-mesh-login flex flex-col items-center justify-start px-4 py-8 gap-6">

      {/* Logo + brand */}
      <div className="flex items-center gap-2 text-white">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20">
          <LogoIcon className="h-5 w-5 text-white" />
        </div>
        <span className="text-lg font-semibold tracking-tight">FitManager</span>
      </div>

      {/* ── Loading ── */}
      {phase === "loading" && (
        <Card className="w-full max-w-lg">
          <CardContent className="flex flex-col items-center gap-4 py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">Verifica del link in corso...</p>
          </CardContent>
        </Card>
      )}

      {/* ── Errore ── */}
      {phase === "error" && (
        <Card className="w-full max-w-lg">
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <XCircle className="h-12 w-12 text-red-500" />
            <div>
              <p className="font-semibold text-lg">Link non disponibile</p>
              <p className="text-sm text-muted-foreground mt-1">
                {errorMsg || "Il link potrebbe essere scaduto o gia' utilizzato."}
              </p>
            </div>
            <p className="text-xs text-muted-foreground max-w-sm">
              Contatta il tuo personal trainer per ricevere un nuovo link.
            </p>
          </CardContent>
        </Card>
      )}

      {/* ── Successo ── */}
      {phase === "success" && (
        <Card className="w-full max-w-lg">
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <CheckCircle2 className="h-14 w-14 text-emerald-500" />
            <div>
              <p className="font-bold text-xl">Questionario inviato!</p>
              <p className="text-sm text-muted-foreground mt-2">
                Grazie {info?.client_name}. Il tuo trainer ricevera' le informazioni
                e le utilizzera' per personalizzare il tuo programma.
              </p>
            </div>
            <p className="text-xs text-muted-foreground">Puoi chiudere questa pagina.</p>
          </CardContent>
        </Card>
      )}

      {/* ── Form wizard ── */}
      {phase === "form" && info && (
        <Card className="w-full max-w-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Questionario Anamnesi
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              {info.has_existing
                ? `Aggiorna il tuo questionario per ${info.trainer_name}`
                : `Compila il questionario per ${info.trainer_name}`}
            </p>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Stepper */}
            <div className="flex items-center justify-between gap-1">
              {STEPS.map((s, i) => {
                const Icon = s.icon;
                const isActive = i === step;
                const isDone = i < step;
                return (
                  <button
                    key={s.title}
                    onClick={() => setStep(i)}
                    className={`flex flex-1 flex-col items-center gap-1 rounded-lg p-1.5 text-xs transition-colors ${
                      isActive
                        ? "bg-primary/10 text-primary font-medium"
                        : isDone
                          ? "text-primary/60"
                          : "text-muted-foreground"
                    }`}
                  >
                    <div
                      className={`flex h-7 w-7 items-center justify-center rounded-full transition-colors ${
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : isDone
                            ? "bg-primary/20 text-primary"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <span className="hidden sm:block leading-none">{s.title}</span>
                  </button>
                );
              })}
            </div>

            {/* Step content */}
            <div className="py-1">
              <StepComponent data={data} onChange={handleChange} />
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between border-t pt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep((s) => s - 1)}
                disabled={isFirst}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Indietro
              </Button>

              <span className="text-xs text-muted-foreground">
                {step + 1} / {STEPS.length}
              </span>

              {isLast ? (
                <Button size="sm" onClick={handleSubmit} disabled={submitting}>
                  <Save className="mr-1.5 h-4 w-4" />
                  {submitting ? "Invio..." : "Invia"}
                </Button>
              ) : (
                <Button size="sm" onClick={() => setStep((s) => s + 1)}>
                  Avanti
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <p className="text-xs text-white/60 text-center max-w-sm">
        I tuoi dati vengono salvati direttamente sul dispositivo del tuo trainer.
        Nessun dato viene inviato a server esterni.
      </p>
    </div>
  );
}
