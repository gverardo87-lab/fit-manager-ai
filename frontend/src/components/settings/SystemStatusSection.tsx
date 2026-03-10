"use client";

import {
  Activity,
  CloudOff,
  HardDriveDownload,
  Loader2,
  RefreshCw,
  ServerCog,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Wifi,
} from "lucide-react";

import { useSystemHealth } from "@/hooks/useSystemHealth";
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
import { formatDateTime } from "@/lib/format";
import {
  formatUptime,
  mapConnectionStatus,
  mapLicenseStatus,
  toneClasses,
  type Tone,
} from "@/components/settings/system-status-utils";
import type {
  InstallationHealthResponse,
} from "@/types/api";

function StatusBadge({ label, tone }: { label: string; tone: Tone }) {
  return (
    <Badge variant="outline" className={toneClasses[tone]}>
      {label}
    </Badge>
  );
}

function StatusItem({
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

function LoadingState() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-72" />
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-24 w-full rounded-xl" />
        ))}
      </CardContent>
    </Card>
  );
}

function ErrorState({
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
          <CardTitle>Stato installazione non disponibile</CardTitle>
        </div>
        <CardDescription>
          Non sono riuscito a leggere lo stato runtime locale. Prima del go-live questo pannello deve
          restare affidabile, altrimenti perdi visibilita su licenza, ambiente e salute dell&apos;istanza.
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

function Advisory({ health }: { health: InstallationHealthResponse }) {
  if (!health.license_enforcement_enabled) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
        <div className="flex items-start gap-3">
          <ShieldOff className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="space-y-1">
            <p className="font-semibold">Protezione licenza non attiva</p>
            <p>
              Questa istanza sta girando senza enforcement runtime della licenza. In produzione la base
              sicura resta: backend con <code>LICENSE_ENFORCEMENT_ENABLED=true</code> oppure avvio da
              <code>installer/launcher.bat</code>.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (health.status !== "ok" || health.db !== "connected" || health.catalog !== "connected") {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="space-y-1">
            <p className="font-semibold">Istanza non completamente sana</p>
            <p>
              Uno dei layer locali non risponde come atteso. Prima di distribuire o aggiornare, la regola
              deve restare: DB business e catalog entrambi connessi e health globale su <code>ok</code>.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200">
      <div className="flex items-start gap-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
        <div className="space-y-1">
          <p className="font-semibold">Installazione leggibile e governabile</p>
          <p>
            Versione, runtime, salute DB e protezione licenza sono ora verificabili dalla UI. Questo e il
            primo mattone pratico per distinguere FitManager come software locale affidabile, non opaco.
          </p>
        </div>
      </div>
    </div>
  );
}

export function SystemStatusSection() {
  const { data, isLoading, isError, isFetching, refetch } = useSystemHealth();

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError || !data) {
    return <ErrorState isRetrying={isFetching} onRetry={() => void refetch()} />;
  }

  const license = mapLicenseStatus(data.license_status);
  const db = mapConnectionStatus(data.db);
  const catalog = mapConnectionStatus(data.catalog);
  const healthTone: Tone = data.status === "ok" ? "good" : "critical";
  const portalTone: Tone = data.public_portal_enabled
    ? data.public_base_url_configured
      ? "good"
      : "warning"
    : "neutral";

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <ServerCog className="h-5 w-5 text-teal-600" />
              <CardTitle>Stato installazione</CardTitle>
            </div>
            <CardDescription>
              Questo pannello rende verificabile la qualita della tua istanza locale: versione, protezione,
              runtime e salute dei due database che sostengono il CRM.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge
              label={data.status === "ok" ? "Istanza sana" : "Istanza degradata"}
              tone={healthTone}
            />
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
        <Advisory health={data} />

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <StatusItem
            label="Versione applicazione"
            value={data.version}
            badge={{
              label: data.distribution_mode === "installer" ? "Installer" : "Sorgente",
              tone: "neutral",
            }}
          />
          <StatusItem
            label="Ambiente runtime"
            value={data.app_mode === "production" ? "Produzione" : "Sviluppo"}
            badge={{
              label: data.app_mode === "production" ? "Prod" : "Dev",
              tone: data.app_mode === "production" ? "good" : "warning",
            }}
          />
          <StatusItem
            label="Protezione licenza"
            value={data.license_enforcement_enabled ? "Enforcement attivo" : "Enforcement disattivo"}
            badge={{
              label: data.license_enforcement_enabled ? "Protetto" : "Da attivare",
              tone: data.license_enforcement_enabled ? "good" : "critical",
            }}
          />
          <StatusItem label="Licenza installata" value={license.label} badge={license} />
          <StatusItem label="Database business" value={db.label} badge={db} />
          <StatusItem label="Catalogo scientifico" value={catalog.label} badge={catalog} />
          <StatusItem
            label="Portale pubblico"
            value={data.public_portal_enabled ? "Abilitato" : "Disattivo"}
            badge={{
              label: data.public_base_url_configured ? "Base URL pronta" : "Base URL mancante",
              tone: portalTone,
            }}
          />
          <StatusItem label="Avvio istanza" value={formatDateTime(data.started_at)} />
          <StatusItem label="Uptime" value={formatUptime(data.uptime_seconds)} />
        </div>

        <div className="grid gap-3 rounded-xl border bg-muted/30 p-4 md:grid-cols-3">
          <div className="flex items-start gap-3">
            <CloudOff className="mt-0.5 h-4 w-4 text-teal-700 dark:text-teal-300" />
            <div className="space-y-1">
              <p className="text-sm font-semibold">Zero dipendenza cloud</p>
              <p className="text-xs text-muted-foreground">
                Salute, licenza e dati restano leggibili localmente, senza phone-home.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <HardDriveDownload className="mt-0.5 h-4 w-4 text-teal-700 dark:text-teal-300" />
            <div className="space-y-1">
              <p className="text-sm font-semibold">Installazione supportabile</p>
              <p className="text-xs text-muted-foreground">
                Il supporto puo partire da versione, runtime e stato DB prima ancora di toccare i backup.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            {data.public_portal_enabled ? (
              <Wifi className="mt-0.5 h-4 w-4 text-teal-700 dark:text-teal-300" />
            ) : (
              <Activity className="mt-0.5 h-4 w-4 text-teal-700 dark:text-teal-300" />
            )}
            <div className="space-y-1">
              <p className="text-sm font-semibold">Surface leggibile</p>
              <p className="text-xs text-muted-foreground">
                Se attivi il portale pubblico, questo pannello ti dice subito se la base URL e pronta.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
