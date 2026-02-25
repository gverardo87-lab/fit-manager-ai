// src/components/clients/anamnesi/AnamnesiWizard.tsx
"use client";

/**
 * Wizard multi-step per compilazione anamnesi cliente.
 *
 * 4 step: Muscoloscheletrico → Condizioni Mediche → Stile di Vita → Obiettivi.
 * Stepper progress + navigazione Indietro/Avanti/Salva.
 * Pre-popolamento se anamnesi esistente (modifica).
 */

import { useState, useCallback, useEffect } from "react";
import {
  Bone,
  Stethoscope,
  Heart,
  Target,
  ArrowLeft,
  ArrowRight,
  Save,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

import { useUpdateAnamnesi } from "@/hooks/useClients";
import type { AnamnesiData } from "@/types/api";
import { getEmptyAnamnesi } from "./anamnesi-helpers";
import {
  StepMuscoloscheletrico,
  StepCondizioniMediche,
  StepStileVita,
  StepObiettivi,
} from "./AnamnesiSteps";

// ════════════════════════════════════════════════════════════
// STEP DEFINITIONS
// ════════════════════════════════════════════════════════════

const STEPS = [
  { title: "Muscoloscheletrico", icon: Bone },
  { title: "Condizioni Mediche", icon: Stethoscope },
  { title: "Stile di Vita", icon: Heart },
  { title: "Obiettivi", icon: Target },
] as const;

const STEP_COMPONENTS = [
  StepMuscoloscheletrico,
  StepCondizioniMediche,
  StepStileVita,
  StepObiettivi,
];

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface AnamnesiWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: number;
  existing: AnamnesiData | null;
}

export function AnamnesiWizard({
  open,
  onOpenChange,
  clientId,
  existing,
}: AnamnesiWizardProps) {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<AnamnesiData>(() => existing ?? getEmptyAnamnesi());
  const updateAnamnesi = useUpdateAnamnesi();

  // Sync state quando il dialog si apre (modifica o nuova compilazione)
  useEffect(() => {
    if (open) {
      setData(existing ?? getEmptyAnamnesi());
      setStep(0);
    }
  }, [open, existing]);

  const handleChange = useCallback((updates: Partial<AnamnesiData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  }, []);

  const handleSave = useCallback(() => {
    const now = new Date().toISOString().slice(0, 10);
    const payload: AnamnesiData = {
      ...data,
      data_compilazione: existing?.data_compilazione ?? now,
      data_ultimo_aggiornamento: now,
    };

    updateAnamnesi.mutate(
      { id: clientId, anamnesi: payload },
      { onSuccess: () => onOpenChange(false) },
    );
  }, [data, existing, clientId, updateAnamnesi, onOpenChange]);

  const StepComponent = STEP_COMPONENTS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Anamnesi Cliente</DialogTitle>
          <DialogDescription>
            Compila il questionario per personalizzare la programmazione.
          </DialogDescription>
        </DialogHeader>

        {/* ── Stepper ── */}
        <div className="flex items-center justify-between gap-1 px-1">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const isActive = i === step;
            const isDone = i < step;
            return (
              <button
                key={s.title}
                onClick={() => setStep(i)}
                className={`flex flex-1 flex-col items-center gap-1 rounded-lg p-2 text-xs transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary font-medium"
                    : isDone
                      ? "text-primary/60"
                      : "text-muted-foreground"
                }`}
              >
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : isDone
                        ? "bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <span className="hidden sm:block">{s.title}</span>
              </button>
            );
          })}
        </div>

        {/* ── Step Content ── */}
        <div className="flex-1 overflow-y-auto py-2 px-1">
          <StepComponent data={data} onChange={handleChange} />
        </div>

        {/* ── Navigation ── */}
        <div className="flex items-center justify-between border-t pt-3">
          <Button
            variant="outline"
            onClick={() => setStep((s) => s - 1)}
            disabled={isFirst}
          >
            <ArrowLeft className="mr-1.5 h-4 w-4" />
            Indietro
          </Button>

          <span className="text-xs text-muted-foreground">
            {step + 1} di {STEPS.length}
          </span>

          {isLast ? (
            <Button onClick={handleSave} disabled={updateAnamnesi.isPending}>
              <Save className="mr-1.5 h-4 w-4" />
              {updateAnamnesi.isPending ? "Salvataggio..." : "Salva"}
            </Button>
          ) : (
            <Button onClick={() => setStep((s) => s + 1)}>
              Avanti
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
