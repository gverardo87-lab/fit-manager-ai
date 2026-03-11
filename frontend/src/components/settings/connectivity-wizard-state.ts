import type {
  InstallationConnectivityProfile,
  InstallationConnectivityStatusResponse,
  InstallationConnectivityVerifyResponse,
} from "@/types/api";

export type ConnectivityWizardStepId =
  | "choose_profile"
  | "prepare_tailscale"
  | "apply_profile"
  | "enable_funnel"
  | "verify";

export type ConnectivityWizardStepState = "complete" | "current" | "upcoming";

export interface ConnectivityWizardStep {
  id: ConnectivityWizardStepId;
  title: string;
  description: string;
  state: ConnectivityWizardStepState;
}

export interface ConnectivityWizardState {
  steps: ConnectivityWizardStep[];
  currentStepId: ConnectivityWizardStepId | null;
  allDone: boolean;
}

function isTargetProfileApplied(
  targetProfile: InstallationConnectivityProfile,
  status: InstallationConnectivityStatusResponse,
  hasUnsavedPublicBaseUrlDraft: boolean,
) {
  switch (targetProfile) {
    case "local_only":
      return status.profile === "local_only" && status.public_portal_enabled === false;
    case "trusted_devices":
      return status.profile === "trusted_devices" && status.public_portal_enabled === false;
    case "public_portal":
      return (
        status.public_portal_enabled === true &&
        Boolean(status.public_base_url) &&
        status.public_base_url_matches_dns !== false &&
        hasUnsavedPublicBaseUrlDraft === false
      );
  }
}

function isTargetProfileVerified(
  targetProfile: InstallationConnectivityProfile,
  verification?: InstallationConnectivityVerifyResponse,
) {
  return (
    verification?.status === "ready" &&
    verification.target_profile === targetProfile &&
    verification.effective_profile === targetProfile
  );
}

export function buildConnectivityWizardState({
  targetProfile,
  status,
  verification,
  hasUnsavedPublicBaseUrlDraft,
}: {
  targetProfile: InstallationConnectivityProfile;
  status: InstallationConnectivityStatusResponse;
  verification?: InstallationConnectivityVerifyResponse;
  hasUnsavedPublicBaseUrlDraft: boolean;
}): ConnectivityWizardState {
  const rawSteps = [
    {
      id: "choose_profile" as const,
      required: true,
      complete: true,
      title: "Scegli il profilo",
      description:
        targetProfile === "local_only"
          ? "Mantieni FitManager solo sul PC principale."
          : targetProfile === "trusted_devices"
            ? "Prepara l'accesso da tablet e altri dispositivi fidati."
            : "Prepara anche il portale pubblico per i link anamnesi.",
    },
    {
      id: "prepare_tailscale" as const,
      required: targetProfile !== "local_only",
      complete:
        targetProfile === "local_only"
          ? true
          : targetProfile === "public_portal"
            ? status.tailscale_connected && Boolean(status.tailscale_dns_name)
            : status.tailscale_connected,
      title: "Prepara Tailscale",
      description:
        targetProfile === "public_portal"
          ? "Installa Tailscale, accedi e assicurati che il DNS `ts.net` sia disponibile."
          : "Installa Tailscale e accedi con il client ufficiale sul PC del trainer.",
    },
    {
      id: "apply_profile" as const,
      required: true,
      complete: isTargetProfileApplied(targetProfile, status, hasUnsavedPublicBaseUrlDraft),
      title: "Configura FitManager",
      description:
        targetProfile === "public_portal"
          ? "Salva il profilo pubblico e allinea `PUBLIC_BASE_URL` al DNS rilevato."
          : "Salva il profilo desiderato senza toccare `.env` manualmente.",
    },
    {
      id: "enable_funnel" as const,
      required: targetProfile === "public_portal",
      complete: targetProfile !== "public_portal" ? true : status.funnel_enabled,
      title: "Attiva Funnel",
      description:
        "Esegui il comando `tailscale funnel --bg <porta>` dal client ufficiale per esporre il portale pubblico.",
    },
    {
      id: "verify" as const,
      required: true,
      complete: isTargetProfileVerified(targetProfile, verification),
      title: "Verifica finale",
      description:
        targetProfile === "public_portal"
          ? "Controlla che l'origine pubblica risponda davvero dall'esterno."
          : "Conferma che il profilo scelto sia davvero pronto all'uso.",
    },
  ];

  const requiredSteps = rawSteps.filter((step) => step.required);
  const firstIncomplete = requiredSteps.find((step) => !step.complete);

  const steps = rawSteps
    .filter((step) => step.required)
    .map((step) => ({
      id: step.id,
      title: step.title,
      description: step.description,
      state: step.complete
        ? ("complete" as const)
        : step.id === firstIncomplete?.id
          ? ("current" as const)
          : ("upcoming" as const),
    }));

  return {
    steps,
    currentStepId: firstIncomplete?.id ?? null,
    allDone: firstIncomplete == null,
  };
}
