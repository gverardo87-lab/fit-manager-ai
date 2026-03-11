import { buildConnectivityWizardState } from "@/components/settings/connectivity-wizard-state";
import type {
  InstallationConnectivityStatusResponse,
  InstallationConnectivityVerifyResponse,
} from "@/types/api";

function buildStatus(
  overrides: Partial<InstallationConnectivityStatusResponse> = {},
): InstallationConnectivityStatusResponse {
  return {
    generated_at: "2026-03-11T14:00:00Z",
    profile: "local_only",
    tailscale_cli_installed: false,
    tailscale_version: null,
    tailscale_status: "not_installed",
    tailscale_connected: false,
    tailscale_ip: null,
    tailscale_dns_name: null,
    funnel_status: "not_enabled",
    funnel_enabled: false,
    public_portal_enabled: false,
    public_base_url: null,
    public_base_url_matches_dns: null,
    next_recommended_action_code: "install_tailscale",
    next_recommended_action_label: "Installa Tailscale",
    checks: [],
    missing_requirements: [],
    ...overrides,
  };
}

function buildVerification(
  overrides: Partial<InstallationConnectivityVerifyResponse> = {},
): InstallationConnectivityVerifyResponse {
  return {
    verified_at: "2026-03-11T14:05:00Z",
    target_profile: "local_only",
    effective_profile: "local_only",
    status: "ready",
    summary: "Configurazione verificata.",
    verified_public_origin: null,
    checks: [],
    next_recommended_action_code: "ready",
    next_recommended_action_label: "Nessuna azione richiesta",
    ...overrides,
  };
}

describe("buildConnectivityWizardState", () => {
  it("porta un profilo locale gia applicato allo step finale di verifica", () => {
    const wizard = buildConnectivityWizardState({
      targetProfile: "local_only",
      status: buildStatus({ profile: "local_only", public_portal_enabled: false }),
      hasUnsavedPublicBaseUrlDraft: false,
    });

    expect(wizard.currentStepId).toBe("verify");
    expect(wizard.allDone).toBe(false);
    expect(wizard.steps.map((step) => [step.id, step.state])).toEqual([
      ["choose_profile", "complete"],
      ["apply_profile", "complete"],
      ["verify", "current"],
    ]);
  });

  it("blocca il profilo dispositivi fidati sul setup Tailscale se il nodo non e connesso", () => {
    const wizard = buildConnectivityWizardState({
      targetProfile: "trusted_devices",
      status: buildStatus({
        profile: "local_only",
        tailscale_cli_installed: true,
        tailscale_status: "not_connected",
      }),
      hasUnsavedPublicBaseUrlDraft: false,
    });

    expect(wizard.currentStepId).toBe("prepare_tailscale");
    expect(wizard.steps.map((step) => [step.id, step.state])).toEqual([
      ["choose_profile", "complete"],
      ["prepare_tailscale", "current"],
      ["apply_profile", "upcoming"],
      ["verify", "upcoming"],
    ]);
  });

  it("porta il profilo pubblico allo step Funnel quando Tailscale e config sono gia pronti", () => {
    const wizard = buildConnectivityWizardState({
      targetProfile: "public_portal",
      status: buildStatus({
        profile: "public_portal",
        tailscale_cli_installed: true,
        tailscale_connected: true,
        tailscale_status: "ok",
        tailscale_dns_name: "chiara-device.tailnet.ts.net",
        public_portal_enabled: true,
        public_base_url: "https://chiara-device.tailnet.ts.net",
        public_base_url_matches_dns: true,
      }),
      hasUnsavedPublicBaseUrlDraft: false,
    });

    expect(wizard.currentStepId).toBe("enable_funnel");
    expect(wizard.steps.map((step) => [step.id, step.state])).toEqual([
      ["choose_profile", "complete"],
      ["prepare_tailscale", "complete"],
      ["apply_profile", "complete"],
      ["enable_funnel", "current"],
      ["verify", "upcoming"],
    ]);
  });

  it("mantiene lo step di apply attivo finche la base URL pubblica non e salvata davvero", () => {
    const wizard = buildConnectivityWizardState({
      targetProfile: "public_portal",
      status: buildStatus({
        profile: "public_portal",
        tailscale_cli_installed: true,
        tailscale_connected: true,
        tailscale_status: "ok",
        tailscale_dns_name: "chiara-device.tailnet.ts.net",
        public_portal_enabled: true,
        public_base_url: "https://chiara-device.tailnet.ts.net",
        public_base_url_matches_dns: true,
      }),
      hasUnsavedPublicBaseUrlDraft: true,
    });

    expect(wizard.currentStepId).toBe("apply_profile");
    expect(wizard.steps.map((step) => [step.id, step.state])).toEqual([
      ["choose_profile", "complete"],
      ["prepare_tailscale", "complete"],
      ["apply_profile", "current"],
      ["enable_funnel", "upcoming"],
      ["verify", "upcoming"],
    ]);
  });

  it("chiude il percorso quando il profilo pubblico e verificato davvero", () => {
    const wizard = buildConnectivityWizardState({
      targetProfile: "public_portal",
      status: buildStatus({
        profile: "public_portal",
        tailscale_cli_installed: true,
        tailscale_connected: true,
        tailscale_status: "ok",
        tailscale_dns_name: "chiara-device.tailnet.ts.net",
        funnel_enabled: true,
        funnel_status: "ok",
        public_portal_enabled: true,
        public_base_url: "https://chiara-device.tailnet.ts.net",
        public_base_url_matches_dns: true,
      }),
      verification: buildVerification({
        target_profile: "public_portal",
        effective_profile: "public_portal",
      }),
      hasUnsavedPublicBaseUrlDraft: false,
    });

    expect(wizard.currentStepId).toBeNull();
    expect(wizard.allDone).toBe(true);
    expect(wizard.steps.every((step) => step.state === "complete")).toBe(true);
  });
});
