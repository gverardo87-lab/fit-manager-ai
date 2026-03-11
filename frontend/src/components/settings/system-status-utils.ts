import type {
  InstallationConnectivityCheckStatus,
  InstallationConnectivityProfile,
  InstallationConnectivityVerifyStatus,
  InstallationConnectionStatus,
  InstallationLicenseStatus,
} from "@/types/api";

export type Tone = "good" | "warning" | "critical" | "neutral";

export const toneClasses: Record<Tone, string> = {
  good: "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300",
  warning: "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300",
  critical: "border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300",
  neutral: "border-slate-200 bg-slate-50 text-slate-800 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-300",
};

export function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (hours < 24) {
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours > 0 ? `${days}g ${remainingHours}h` : `${days}g`;
}

export function mapLicenseStatus(
  status: InstallationLicenseStatus,
): { label: string; tone: Tone } {
  switch (status) {
    case "valid":
      return { label: "Valida", tone: "good" };
    case "missing":
      return { label: "Assente", tone: "warning" };
    case "expired":
      return { label: "Scaduta", tone: "critical" };
    case "invalid":
      return { label: "Non valida", tone: "critical" };
    case "unconfigured":
      return { label: "Non configurata", tone: "warning" };
    default:
      return { label: status, tone: "neutral" };
  }
}

export function mapConnectionStatus(
  status: InstallationConnectionStatus,
): { label: string; tone: Tone } {
  return status === "connected"
    ? { label: "Connesso", tone: "good" }
    : { label: "Disconnesso", tone: "critical" };
}

export function mapConnectivityCheckStatus(
  status: InstallationConnectivityCheckStatus,
): { label: string; tone: Tone } {
  switch (status) {
    case "ok":
      return { label: "Pronto", tone: "good" };
    case "warning":
      return { label: "Da completare", tone: "warning" };
    case "critical":
      return { label: "Bloccante", tone: "critical" };
    default:
      return { label: "Non richiesto", tone: "neutral" };
  }
}

export function mapConnectivityVerifyStatus(
  status: InstallationConnectivityVerifyStatus,
): { label: string; tone: Tone } {
  switch (status) {
    case "ready":
      return { label: "Verificata", tone: "good" };
    case "partial":
      return { label: "Parziale", tone: "warning" };
    default:
      return { label: "Bloccata", tone: "critical" };
  }
}

export function mapConnectivityProfile(
  profile: InstallationConnectivityProfile,
): { label: string; description: string } {
  switch (profile) {
    case "public_portal":
      return {
        label: "Portale pubblico",
        description: "L'istanza e pronta per dispositivi fidati e link anamnesi pubblici.",
      };
    case "trusted_devices":
      return {
        label: "Dispositivi fidati",
        description: "Tailscale e pronto per accesso remoto autenticato, senza link pubblici.",
      };
    default:
      return {
        label: "Solo locale",
        description: "FitManager resta utilizzabile sul PC locale; accesso remoto non ancora pronto.",
      };
  }
}
