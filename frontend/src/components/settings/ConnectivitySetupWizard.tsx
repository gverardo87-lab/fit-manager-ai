"use client";

import { useMemo, useState } from "react";
import { Smartphone } from "lucide-react";
import { toast } from "sonner";

import type {
  InstallationConnectivityConfigResponse,
  InstallationConnectivityProfile,
  InstallationConnectivityStatusResponse,
  InstallationConnectivityVerifyResponse,
} from "@/types/api";
import { VerificationStatePanel } from "@/components/settings/connectivity-status-ui";
import {
  ConnectivityProfilePicker,
  ConnectivityWizardStepper,
  ConnectivityWizardSuccessState,
} from "@/components/settings/connectivity-wizard-ui";
import {
  ApplyProfilePanel,
  EnableFunnelPanel,
  PrepareTailscalePanel,
} from "@/components/settings/connectivity-wizard-panels";
import {
  buildConnectivityWizardState,
} from "@/components/settings/connectivity-wizard-state";
import { mapConnectivityProfile } from "@/components/settings/system-status-utils";

interface ConnectivitySetupWizardProps {
  status: InstallationConnectivityStatusResponse;
  verification?: InstallationConnectivityVerifyResponse;
  isApplying: boolean;
  isRefreshing: boolean;
  isVerifying: boolean;
  onApply: (
    profile: InstallationConnectivityProfile,
    publicBaseUrl: string | null,
    onSuccess?: (response: InstallationConnectivityConfigResponse) => void,
  ) => void;
  onRefresh: () => void;
  onResetVerification: () => void;
  onVerify: () => void;
}

export function ConnectivitySetupWizard({
  status,
  verification,
  isApplying,
  isRefreshing,
  isVerifying,
  onApply,
  onRefresh,
  onResetVerification,
  onVerify,
}: ConnectivitySetupWizardProps) {
  const [selectedProfile, setSelectedProfile] = useState<InstallationConnectivityProfile>(status.profile);
  const [baseUrlDraft, setBaseUrlDraft] = useState("");
  const [userEditedBaseUrl, setUserEditedBaseUrl] = useState(false);
  const [lastAppliedPublicBaseUrl, setLastAppliedPublicBaseUrl] = useState<string | null>(null);
  const [showPublicPortalConfig, setShowPublicPortalConfig] = useState(status.profile === "public_portal");

  const suggestedBaseUrl = useMemo(() => {
    return (
      status.public_base_url ??
      lastAppliedPublicBaseUrl ??
      (status.tailscale_dns_name ? `https://${status.tailscale_dns_name}` : "")
    );
  }, [lastAppliedPublicBaseUrl, status.public_base_url, status.tailscale_dns_name]);

  const effectiveBaseUrlDraft = userEditedBaseUrl ? baseUrlDraft : suggestedBaseUrl;
  const normalizedBaseUrl = effectiveBaseUrlDraft.trim();
  const publicPortalConfigVisible = selectedProfile === "public_portal" && showPublicPortalConfig;
  const hasUnsavedPublicBaseUrlDraft =
    selectedProfile === "public_portal" &&
    userEditedBaseUrl &&
    normalizedBaseUrl !== (status.public_base_url ?? "");
  const wizard = buildConnectivityWizardState({
    targetProfile: selectedProfile,
    status,
    verification,
    hasUnsavedPublicBaseUrlDraft,
  });
  const selectedProfileMeta = mapConnectivityProfile(selectedProfile);
  const currentStepId = wizard.currentStepId ?? "verify";
  const currentPort =
    typeof window !== "undefined" && window.location.port ? window.location.port : "3000";
  const funnelCommand = `tailscale funnel --bg ${currentPort}`;

  const applyProfile = () => {
    onApply(
      selectedProfile,
      selectedProfile === "public_portal" ? normalizedBaseUrl || null : null,
      (response) => {
        setSelectedProfile(response.profile);
        setLastAppliedPublicBaseUrl(response.public_base_url ?? null);
        setBaseUrlDraft("");
        setUserEditedBaseUrl(false);
        setShowPublicPortalConfig(response.profile === "public_portal");
      },
    );
  };

  const handleProfileSelect = (profile: InstallationConnectivityProfile) => {
    setSelectedProfile(profile);
    setShowPublicPortalConfig(profile === "public_portal");
    onResetVerification();
  };

  const handleUseDetectedDns = () => {
    setBaseUrlDraft("");
    setUserEditedBaseUrl(false);
    onResetVerification();
  };

  const copyFunnelCommand = async () => {
    try {
      await navigator.clipboard.writeText(funnelCommand);
      toast.success("Comando Tailscale copiato");
    } catch {
      toast.error("Impossibile copiare il comando");
    }
  };

  const renderCurrentStep = () => {
    switch (currentStepId) {
      case "prepare_tailscale":
        return (
          <PrepareTailscalePanel
            isRefreshing={isRefreshing}
            onRefresh={onRefresh}
            requiresDns={selectedProfile === "public_portal"}
          />
        );
      case "apply_profile":
        return (
          <ApplyProfilePanel
            isApplying={isApplying}
            isRefreshing={isRefreshing}
            normalizedBaseUrl={normalizedBaseUrl}
            onApply={applyProfile}
            onRefresh={onRefresh}
            onUseDetectedDns={handleUseDetectedDns}
            publicPortalConfigVisible={publicPortalConfigVisible}
            selectedProfile={selectedProfile}
            setShowPublicPortalConfig={setShowPublicPortalConfig}
            suggestedBaseUrl={suggestedBaseUrl}
            effectiveBaseUrlDraft={effectiveBaseUrlDraft}
            onBaseUrlChange={(value) => {
              setBaseUrlDraft(value);
              setUserEditedBaseUrl(true);
              onResetVerification();
            }}
          />
        );
      case "enable_funnel":
        return (
          <EnableFunnelPanel
            funnelCommand={funnelCommand}
            isRefreshing={isRefreshing}
            onCopyCommand={() => void copyFunnelCommand()}
            onRefresh={onRefresh}
          />
        );
      case "verify":
      default:
        return (
          <VerificationStatePanel
            verification={verification}
            disabled={isApplying || hasUnsavedPublicBaseUrlDraft}
            isVerifying={isVerifying}
            onVerify={onVerify}
          />
        );
    }
  };

  return (
    <div className="space-y-4 rounded-xl border bg-background/80 p-4">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Smartphone className="h-4 w-4 text-teal-600" />
          <p className="text-sm font-semibold text-foreground">Wizard guidato</p>
        </div>
        <p className="text-sm text-muted-foreground">
          Profilo scelto: <span className="font-medium text-foreground">{selectedProfileMeta.label}</span>.
          Il percorso resta locale-safe: puoi sempre tornare a `Solo locale`.
        </p>
      </div>

      <ConnectivityProfilePicker selectedProfile={selectedProfile} onSelect={handleProfileSelect} />

      <ConnectivityWizardStepper steps={wizard.steps} />

      {wizard.allDone ? (
        <ConnectivityWizardSuccessState />
      ) : (
        renderCurrentStep()
      )}
    </div>
  );
}
