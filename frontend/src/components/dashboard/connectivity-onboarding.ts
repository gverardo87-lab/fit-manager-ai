import type { InstallationConnectivityProfile } from "@/types/api";

export type ConnectivityOnboardingPromptId =
  | "configure-trusted-devices"
  | "configure-public-portal";

export interface ConnectivityOnboardingPrompt {
  id: ConnectivityOnboardingPromptId;
  title: string;
  description: string;
  ctaLabel: string;
}

export function getConnectivityOnboardingPrompt(
  profile: InstallationConnectivityProfile,
): ConnectivityOnboardingPrompt | null {
  switch (profile) {
    case "local_only":
      return {
        id: "configure-trusted-devices",
        title: "Configura l'accesso da tablet e altri dispositivi",
        description:
          "Il CRM e pronto a restare solo locale. Se vuoi usarlo anche fuori studio, il passo successivo e il profilo Dispositivi fidati in Connettivita.",
        ctaLabel: "Apri Connettivita",
      };
    case "trusted_devices":
      return {
        id: "configure-public-portal",
        title: "Completa il portale pubblico per l'anamnesi",
        description:
          "L'accesso remoto del trainer e gia pronto. Se vuoi inviare link anamnesi ai clienti senza Tailscale, completa ora il profilo Portale pubblico.",
        ctaLabel: "Completa Portale Pubblico",
      };
    default:
      return null;
  }
}
