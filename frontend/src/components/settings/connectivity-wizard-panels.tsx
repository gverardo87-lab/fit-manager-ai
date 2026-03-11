"use client";

import { Copy, ExternalLink, Loader2, RefreshCw } from "lucide-react";

import type { InstallationConnectivityProfile } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PublicPortalHint } from "@/components/settings/connectivity-status-ui";

export function PrepareTailscalePanel({
  isRefreshing,
  onRefresh,
  requiresDns,
}: {
  isRefreshing: boolean;
  onRefresh: () => void;
  requiresDns: boolean;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold text-foreground">Prepara Tailscale</p>
        <p className="text-sm text-muted-foreground">
          FitManager non gestisce il login Tailscale. Installa o apri il client ufficiale,
          accedi con l&apos;account del trainer e poi aggiorna lo stato qui.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border bg-background/80 p-4 text-sm">
          <p className="font-semibold text-foreground">Client ufficiale</p>
          <p className="mt-1 text-muted-foreground">
            Installa Tailscale sul PC del trainer e completa l&apos;accesso con il client
            ufficiale.
          </p>
        </div>
        <div className="rounded-xl border bg-background/80 p-4 text-sm">
          <p className="font-semibold text-foreground">DNS richiesto</p>
          <p className="mt-1 text-muted-foreground">
            {requiresDns
              ? "Per il portale pubblico serve anche un DNS `ts.net` rilevabile dal prodotto."
              : "Per i dispositivi fidati basta un nodo Tailscale connesso."}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button asChild variant="outline" size="sm">
          <a href="https://tailscale.com/download" target="_blank" rel="noreferrer">
            <ExternalLink className="mr-2 h-4 w-4" />
            Scarica Tailscale
          </a>
        </Button>
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={isRefreshing}>
          {isRefreshing ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Aggiorna stato
        </Button>
      </div>
    </div>
  );
}

export function ApplyProfilePanel({
  isApplying,
  isRefreshing,
  normalizedBaseUrl,
  onApply,
  onRefresh,
  onUseDetectedDns,
  publicPortalConfigVisible,
  selectedProfile,
  setShowPublicPortalConfig,
  suggestedBaseUrl,
  effectiveBaseUrlDraft,
  onBaseUrlChange,
}: {
  isApplying: boolean;
  isRefreshing: boolean;
  normalizedBaseUrl: string;
  onApply: () => void;
  onRefresh: () => void;
  onUseDetectedDns: () => void;
  publicPortalConfigVisible: boolean;
  selectedProfile: InstallationConnectivityProfile;
  setShowPublicPortalConfig: (open: boolean) => void;
  suggestedBaseUrl: string;
  effectiveBaseUrlDraft: string;
  onBaseUrlChange: (value: string) => void;
}) {
  const applyLabel =
    selectedProfile === "trusted_devices"
      ? "Salva profilo dispositivi fidati"
      : selectedProfile === "public_portal"
        ? "Salva profilo portale pubblico"
        : "Salva profilo locale";

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold text-foreground">Configura FitManager</p>
        <p className="text-sm text-muted-foreground">
          Il prodotto salva solo la propria configurazione runtime. Tailscale e Funnel restano
          nel client ufficiale.
        </p>
      </div>

      {selectedProfile === "public_portal" ? (
        publicPortalConfigVisible ? (
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
            <div className="space-y-2">
              <label className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Base URL pubblica
              </label>
              <Input
                value={effectiveBaseUrlDraft}
                onChange={(event) => onBaseUrlChange(event.target.value)}
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
                onClick={onUseDetectedDns}
                disabled={isApplying || !suggestedBaseUrl}
              >
                Usa DNS rilevato
              </Button>
            </div>
          </div>
        ) : (
          <PublicPortalHint onConfigure={() => setShowPublicPortalConfig(true)} />
        )
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          onClick={onApply}
          disabled={isApplying || (selectedProfile === "public_portal" && !normalizedBaseUrl)}
        >
          {isApplying ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {applyLabel}
        </Button>
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={isRefreshing}>
          {isRefreshing ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Rileggi stato macchina
        </Button>
      </div>
    </div>
  );
}

export function EnableFunnelPanel({
  funnelCommand,
  isRefreshing,
  onCopyCommand,
  onRefresh,
}: {
  funnelCommand: string;
  isRefreshing: boolean;
  onCopyCommand: () => void;
  onRefresh: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold text-foreground">Attiva il tunnel pubblico</p>
        <p className="text-sm text-muted-foreground">
          Esegui il comando nel client Tailscale ufficiale o in un terminale con Tailscale
          configurato sul PC del trainer. Poi torna qui e aggiorna lo stato.
        </p>
      </div>
      <div className="rounded-xl border bg-muted/30 p-4">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Comando suggerito
        </p>
        <p className="mt-2 rounded-lg bg-background px-3 py-2 font-mono text-sm text-foreground">
          {funnelCommand}
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={onCopyCommand}>
          <Copy className="mr-2 h-4 w-4" />
          Copia comando
        </Button>
        <Button asChild variant="outline" size="sm">
          <a href="https://tailscale.com/kb/1223/funnel" target="_blank" rel="noreferrer">
            <ExternalLink className="mr-2 h-4 w-4" />
            Guida Funnel
          </a>
        </Button>
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={isRefreshing}>
          {isRefreshing ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Aggiorna stato
        </Button>
      </div>
    </div>
  );
}
