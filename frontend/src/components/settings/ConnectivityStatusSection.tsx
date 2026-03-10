"use client";

import { useState } from "react";
import { Loader2, Network, RefreshCw, Wifi, WifiOff } from "lucide-react";

import { useApplyConnectivityConfig } from "@/hooks/useConnectivityConfig";
import { useConnectivityStatus } from "@/hooks/useConnectivityStatus";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  ErrorState,
  LoadingState,
  PublicPortalHint,
  StatusBadge,
  SummaryItem,
} from "@/components/settings/connectivity-status-ui";
import {
  mapConnectivityCheckStatus,
  mapConnectivityProfile,
  type Tone,
} from "@/components/settings/system-status-utils";

function resolveNextActionTone(actionCode: string): Tone {
  switch (actionCode) {
    case "ready":
      return "good";
    case "grant_tailscale_access":
      return "critical";
    default:
      return "warning";
  }
}

export function ConnectivityStatusSection() {
  const { data, isLoading, isError, isFetching, refetch } = useConnectivityStatus();
  const applyConfig = useApplyConnectivityConfig();
  const [baseUrlDraft, setBaseUrlDraft] = useState("");
  const [userEditedBaseUrl, setUserEditedBaseUrl] = useState(false);
  const [showPublicPortalConfig, setShowPublicPortalConfig] = useState(false);
  const suggestedBaseUrl =
    data?.public_base_url ?? (data?.tailscale_dns_name ? `https://${data.tailscale_dns_name}` : "");

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError || !data) {
    return <ErrorState isRetrying={isFetching} onRetry={() => void refetch()} />;
  }

  const profile = mapConnectivityProfile(data.profile);
  const nextActionTone = resolveNextActionTone(data.next_recommended_action_code);
  const checks = data.checks.map((check) => ({
    ...check,
    badge: mapConnectivityCheckStatus(check.status),
  }));
  const effectiveBaseUrlDraft = userEditedBaseUrl ? baseUrlDraft : suggestedBaseUrl;
  const normalizedBaseUrl = effectiveBaseUrlDraft.trim();
  const publicPortalConfigVisible = data.profile === "public_portal" || showPublicPortalConfig;

  const saveProfile = (
    profileToApply: "local_only" | "trusted_devices" | "public_portal",
  ) => {
    applyConfig.mutate(
      {
        profile: profileToApply,
        public_base_url: profileToApply === "public_portal" ? normalizedBaseUrl || null : null,
      },
      {
        onSuccess: (response) => {
          setBaseUrlDraft(response.public_base_url ?? "");
          setUserEditedBaseUrl(false);
          setShowPublicPortalConfig(response.profile === "public_portal");
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Network className="h-5 w-5 text-teal-600" />
              <CardTitle>Connettivita</CardTitle>
            </div>
            <CardDescription>
              Surface read-only per capire se il PC e pronto a restare solo locale, aprirsi ai
              dispositivi fidati o arrivare al portale clienti pubblico.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge label={profile.label} tone={data.profile === "local_only" ? "neutral" : "good"} />
            <Button variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
              {isFetching ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Aggiorna
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-xl border border-teal-200/70 bg-teal-50/70 p-4 text-sm text-teal-900 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-100">
          <div className="flex items-start gap-3">
            {data.profile === "local_only" ? (
              <WifiOff className="mt-0.5 h-4 w-4 shrink-0" />
            ) : (
              <Wifi className="mt-0.5 h-4 w-4 shrink-0" />
            )}
            <div className="space-y-1">
              <p className="font-semibold">{profile.label}</p>
              <p>{profile.description}</p>
              <div className="pt-1">
                <StatusBadge label={data.next_recommended_action_label} tone={nextActionTone} />
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <SummaryItem
            label="Nodo Tailscale"
            value={data.tailscale_dns_name ?? "Non rilevato"}
            badge={
              data.tailscale_connected
                ? { label: "Connesso", tone: "good" }
                : data.tailscale_cli_installed
                  ? { label: "Da collegare", tone: "warning" }
                  : { label: "Non installato", tone: "neutral" }
            }
          />
          <SummaryItem
            label="IP Tailscale"
            value={data.tailscale_ip ?? "Non disponibile"}
          />
          <SummaryItem
            label="Base URL pubblica"
            value={data.public_base_url ?? "Non configurata"}
            badge={
              data.public_portal_enabled
                ? data.public_base_url_matches_dns === false
                  ? { label: "Da allineare", tone: "warning" }
                  : { label: "Attiva", tone: "good" }
                : { label: "Non richiesta", tone: "neutral" }
            }
          />
        </div>

        <div className="rounded-xl border bg-background/80 p-4">
          <div className="space-y-4">
            <div>
              <p className="text-sm font-semibold text-foreground">Applica profilo FitManager</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Qui salvi solo la configurazione dell&apos;app. Login Tailscale e attivazione Funnel
                restano nel client ufficiale, ma FitManager puo preparare il proprio runtime.
              </p>
            </div>

            {publicPortalConfigVisible ? (
              <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
                <div className="space-y-2">
                  <label className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                    Base URL pubblica
                  </label>
                  <Input
                    value={effectiveBaseUrlDraft}
                    onChange={(event) => {
                      setBaseUrlDraft(event.target.value);
                      setUserEditedBaseUrl(true);
                    }}
                    placeholder="https://nome-macchina.tailnet.ts.net"
                  />
                  <p className="text-xs text-muted-foreground">
                    Suggerita: {suggestedBaseUrl || "nessun DNS Tailscale rilevato"}
                  </p>
                </div>
                <div className="flex items-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setBaseUrlDraft(suggestedBaseUrl);
                      setUserEditedBaseUrl(false);
                    }}
                    disabled={applyConfig.isPending || !suggestedBaseUrl}
                  >
                    Usa DNS rilevato
                  </Button>
                </div>
              </div>
            ) : (
              <PublicPortalHint onConfigure={() => setShowPublicPortalConfig(true)} />
            )}

            <div className="flex flex-wrap gap-2">
              <Button
                variant={data.profile === "local_only" ? "default" : "outline"}
                size="sm"
                disabled={applyConfig.isPending}
                onClick={() => saveProfile("local_only")}
              >
                {applyConfig.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Solo locale
              </Button>
              <Button
                variant={data.profile === "trusted_devices" ? "default" : "outline"}
                size="sm"
                disabled={applyConfig.isPending}
                onClick={() => saveProfile("trusted_devices")}
              >
                {applyConfig.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Dispositivi fidati
              </Button>
              <Button
                variant={data.profile === "public_portal" ? "default" : "outline"}
                size="sm"
                disabled={applyConfig.isPending || !normalizedBaseUrl}
                onClick={() => saveProfile("public_portal")}
              >
                {applyConfig.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Portale pubblico
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          {checks.map((check) => (
            <div key={check.code} className="rounded-xl border bg-background/80 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-foreground">{check.label}</p>
                  <p className="text-sm text-muted-foreground">{check.detail}</p>
                </div>
                <StatusBadge label={check.badge.label} tone={check.badge.tone} />
              </div>
            </div>
          ))}
        </div>

        {data.missing_requirements.length > 0 ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
            <div className="space-y-2">
              <p className="font-semibold">Cosa manca per il profilo successivo</p>
              <ul className="space-y-2">
                {data.missing_requirements.map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 rounded-full bg-current opacity-70" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200">
            <p className="font-semibold">Nessun requisito aperto</p>
            <p className="mt-1">
              La surface read-only non segnala blocchi ulteriori. Il passo successivo puo essere il
              wizard guidato o la validazione rete sul PC del cliente.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
