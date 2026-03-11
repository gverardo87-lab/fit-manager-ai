"use client";

import { Loader2, RefreshCw, ShieldAlert } from "lucide-react";

import type { InstallationConnectivityVerifyResponse } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  mapConnectivityCheckStatus,
  mapConnectivityVerifyStatus,
  toneClasses,
  type Tone,
} from "@/components/settings/system-status-utils";

export function StatusBadge({ label, tone }: { label: string; tone: Tone }) {
  return (
    <Badge variant="outline" className={toneClasses[tone]}>
      {label}
    </Badge>
  );
}

export function LoadingState() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-80" />
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-24 w-full rounded-xl" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function ErrorState({
  isRetrying,
  onRetry,
}: {
  isRetrying: boolean;
  onRetry: () => void;
}) {
  return (
    <Card className="border-destructive/40">
      <CardHeader>
        <div className="flex items-center gap-2 text-destructive">
          <ShieldAlert className="h-5 w-5" />
          <CardTitle>Connettivita non leggibile</CardTitle>
        </div>
        <CardDescription>
          Non sono riuscito a leggere lo stato locale di Tailscale e del portale pubblico. Prima
          del wizard vero serve una surface affidabile, altrimenti il setup remoto resta opaco.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="outline" size="sm" onClick={onRetry} disabled={isRetrying}>
          {isRetrying ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Riprova
        </Button>
      </CardContent>
    </Card>
  );
}

export function SummaryItem({
  label,
  value,
  badge,
}: {
  label: string;
  value: string;
  badge?: { label: string; tone: Tone };
}) {
  return (
    <div className="rounded-xl border bg-background/80 p-4">
      <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-foreground">{value}</p>
        {badge ? <StatusBadge label={badge.label} tone={badge.tone} /> : null}
      </div>
    </div>
  );
}

export function PublicPortalHint({
  onConfigure,
}: {
  onConfigure: () => void;
}) {
  return (
    <div className="rounded-xl border border-dashed bg-background/60 p-4">
      <div className="space-y-3">
        <div>
          <p className="text-sm font-semibold text-foreground">Portale pubblico opzionale</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Mostra la base URL pubblica solo quando vuoi davvero preparare i link anamnesi.
            Tailscale e Funnel restano gestiti dal client ufficiale.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onConfigure}>
          Configura portale pubblico
        </Button>
      </div>
    </div>
  );
}

export function VerificationStatePanel({
  verification,
  disabled = false,
  isVerifying,
  onVerify,
}: {
  verification?: InstallationConnectivityVerifyResponse;
  disabled?: boolean;
  isVerifying: boolean;
  onVerify: () => void;
}) {
  const verificationBadge = verification
    ? mapConnectivityVerifyStatus(verification.status)
    : { label: "Da eseguire", tone: "neutral" as const };

  return (
    <div className="rounded-xl border bg-background/80 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-foreground">Verifica finale</p>
            <StatusBadge label={verificationBadge.label} tone={verificationBadge.tone} />
          </div>
          {verification ? (
            <>
              <p className="text-sm text-muted-foreground">{verification.summary}</p>
              {verification.status !== "ready" ? (
                <p className="text-xs text-muted-foreground">
                  Prossimo passo: {verification.next_recommended_action_label}
                </p>
              ) : null}
              {verification.verified_public_origin ? (
                <p className="text-xs text-muted-foreground">
                  Target controllato: {verification.verified_public_origin}
                </p>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              La configurazione e stata salvata, ma non e ancora stata verificata end-to-end.
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onVerify}
          disabled={isVerifying || disabled}
        >
          {isVerifying ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Verifica configurazione
        </Button>
      </div>

      {verification ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-3">
          {verification.checks.map((check) => {
            const badge = mapConnectivityCheckStatus(check.status);
            return (
              <div key={check.code} className="rounded-xl border bg-background/80 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-foreground">{check.label}</p>
                    <p className="text-sm text-muted-foreground">{check.detail}</p>
                  </div>
                  <StatusBadge label={badge.label} tone={badge.tone} />
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
