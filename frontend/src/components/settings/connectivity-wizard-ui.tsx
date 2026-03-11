"use client";

import { CheckCircle2, Globe, Laptop, ShieldCheck, Wifi } from "lucide-react";

import type { InstallationConnectivityProfile } from "@/types/api";
import { StatusBadge } from "@/components/settings/connectivity-status-ui";
import type {
  ConnectivityWizardStep,
  ConnectivityWizardStepState,
} from "@/components/settings/connectivity-wizard-state";
import { mapConnectivityProfile, toneClasses, type Tone } from "@/components/settings/system-status-utils";

function mapWizardStepTone(stepState: ConnectivityWizardStepState): Tone {
  switch (stepState) {
    case "complete":
      return "good";
    case "current":
      return "warning";
    default:
      return "neutral";
  }
}

function mapWizardStepLabel(stepState: ConnectivityWizardStepState) {
  switch (stepState) {
    case "complete":
      return "Completato";
    case "current":
      return "Adesso";
    default:
      return "In attesa";
  }
}

function getStepIcon(stepId: ConnectivityWizardStep["id"]) {
  switch (stepId) {
    case "choose_profile":
      return ShieldCheck;
    case "prepare_tailscale":
      return Wifi;
    case "apply_profile":
      return Laptop;
    case "enable_funnel":
      return Globe;
    case "verify":
      return CheckCircle2;
  }
}

export function ConnectivityProfilePicker({
  selectedProfile,
  onSelect,
}: {
  selectedProfile: InstallationConnectivityProfile;
  onSelect: (profile: InstallationConnectivityProfile) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {(
        ["local_only", "trusted_devices", "public_portal"] as InstallationConnectivityProfile[]
      ).map((profile) => {
        const meta = mapConnectivityProfile(profile);
        const isSelected = selectedProfile === profile;
        return (
          <button
            key={profile}
            type="button"
            onClick={() => onSelect(profile)}
            className={`rounded-xl border p-4 text-left transition-colors ${
              isSelected
                ? "border-teal-500 bg-teal-50 dark:border-teal-700 dark:bg-teal-950/30"
                : "bg-background hover:bg-muted/40"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <p className="text-sm font-semibold text-foreground">{meta.label}</p>
                <p className="text-sm text-muted-foreground">{meta.description}</p>
              </div>
              {isSelected ? <StatusBadge label="Scelto" tone="good" /> : null}
            </div>
          </button>
        );
      })}
    </div>
  );
}

export function ConnectivityWizardStepper({
  steps,
}: {
  steps: ConnectivityWizardStep[];
}) {
  return (
    <div className="grid gap-3 xl:grid-cols-5">
      {steps.map((step, index) => {
        const Icon = getStepIcon(step.id);
        const tone = mapWizardStepTone(step.state);
        return (
          <div key={step.id} className={`rounded-xl border p-4 ${toneClasses[tone]}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-current/20 text-xs font-semibold">
                  {index + 1}
                </span>
                <Icon className="h-4 w-4" />
              </div>
              <StatusBadge label={mapWizardStepLabel(step.state)} tone={tone} />
            </div>
            <p className="mt-3 text-sm font-semibold">{step.title}</p>
            <p className="mt-1 text-sm opacity-90">{step.description}</p>
          </div>
        );
      })}
    </div>
  );
}

export function ConnectivityWizardSuccessState() {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
        <div className="space-y-1">
          <p className="font-semibold">Percorso completato</p>
          <p>
            FitManager risulta configurato e verificato per il profilo scelto. Puoi rieseguire
            la verifica finale ogni volta che cambi rete, DNS o Funnel.
          </p>
        </div>
      </div>
    </div>
  );
}
