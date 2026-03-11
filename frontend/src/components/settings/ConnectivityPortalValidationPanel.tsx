"use client";

import { useMemo, useState } from "react";
import {
  Check,
  Copy,
  ExternalLink,
  Link2,
  Loader2,
  TestTube2,
} from "lucide-react";

import { useClients, useCreateShareTokenForClient } from "@/hooks/useClients";
import { usePortalValidation } from "@/hooks/usePortalValidation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/settings/connectivity-status-ui";
import {
  mapConnectivityCheckStatus,
  mapConnectivityVerifyStatus,
} from "@/components/settings/system-status-utils";

export function ConnectivityPortalValidationPanel() {
  const { data: clientsData, isLoading: isLoadingClients } = useClients();
  const createShareToken = useCreateShareTokenForClient();
  const portalValidation = usePortalValidation();

  const clients = useMemo(
    () =>
      (clientsData?.items ?? [])
        .filter((client) => client.stato === "Attivo")
        .sort((left, right) =>
          `${left.cognome} ${left.nome}`.localeCompare(`${right.cognome} ${right.nome}`, "it"),
        ),
    [clientsData?.items],
  );

  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [generatedLink, setGeneratedLink] = useState<{
    token: string;
    url: string;
    clientName: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const effectiveSelectedClientId = selectedClientId ?? clients[0]?.id ?? null;
  const selectedClient = clients.find((client) => client.id === effectiveSelectedClientId) ?? null;
  const fullUrl = generatedLink
    ? generatedLink.url.startsWith("http")
      ? generatedLink.url
      : `${origin}${generatedLink.url}`
    : "";
  const validationBadge = portalValidation.data
    ? mapConnectivityVerifyStatus(portalValidation.data.status)
    : { label: "Da eseguire", tone: "neutral" as const };

  const handleClientChange = (value: string) => {
    setSelectedClientId(parseInt(value, 10));
    setGeneratedLink(null);
    setCopied(false);
    portalValidation.reset();
  };

  const handleGenerateLink = () => {
    if (!effectiveSelectedClientId) return;
    createShareToken.mutate(effectiveSelectedClientId, {
      onSuccess: (data) => {
        setGeneratedLink({
          token: data.token,
          url: data.url,
          clientName: data.client_name,
        });
        setCopied(false);
        portalValidation.reset();
      },
    });
  };

  const handleCopyLink = async () => {
    if (!fullUrl) return;
    try {
      await navigator.clipboard.writeText(fullUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const handleOpenLink = () => {
    if (!fullUrl) return;
    window.open(fullUrl, "_blank", "noopener,noreferrer");
  };

  const handleValidateLink = () => {
    if (!generatedLink || !fullUrl) return;
    portalValidation.mutate({
      token: generatedLink.token,
      public_url: fullUrl,
    });
  };

  return (
    <div className="space-y-4 rounded-xl border border-teal-200/70 bg-teal-50/40 p-4 dark:border-teal-900/60 dark:bg-teal-950/20">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <TestTube2 className="h-4 w-4 text-teal-700 dark:text-teal-300" />
          <p className="text-sm font-semibold text-foreground">Test guidato link anamnesi</p>
        </div>
        <p className="text-sm text-muted-foreground">
          Questo passaggio usa un link monouso reale. Scegli un cliente di prova, genera il link
          pubblico e lascia che FitManager verifichi sia la pagina pubblica sia il token anamnesi.
        </p>
      </div>

      <div className="rounded-xl border bg-background/80 p-4 text-sm text-muted-foreground">
        <p className="font-semibold text-foreground">Nota importante</p>
        <p className="mt-1">
          Il test sostituisce eventuali link anamnesi ancora aperti per il cliente scelto. Usa un
          cliente di prova o genera il link definitivo solo quando sei pronto a inviarlo davvero.
        </p>
      </div>

      {isLoadingClients ? (
        <div className="rounded-xl border bg-background/80 p-4 text-sm text-muted-foreground">
          Caricamento clienti disponibili...
        </div>
      ) : clients.length === 0 ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
          Nessun cliente attivo disponibile per il test. Crea prima almeno un cliente reale o di
          prova e poi torna qui.
        </div>
      ) : (
        <>
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
            <div className="space-y-2">
              <label className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Cliente di prova
              </label>
              <Select
                value={effectiveSelectedClientId ? String(effectiveSelectedClientId) : undefined}
                onValueChange={handleClientChange}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona un cliente" />
                </SelectTrigger>
                <SelectContent position="popper">
                  {clients.map((client) => (
                    <SelectItem key={client.id} value={String(client.id)}>
                      {client.cognome} {client.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedClient ? (
                <p className="text-xs text-muted-foreground">
                  Link di prova per {selectedClient.nome} {selectedClient.cognome}.
                </p>
              ) : null}
            </div>
            <div className="flex items-end">
              <Button
                size="sm"
                onClick={handleGenerateLink}
                disabled={!effectiveSelectedClientId || createShareToken.isPending}
              >
                {createShareToken.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Link2 className="mr-2 h-4 w-4" />
                )}
                Genera link di prova
              </Button>
            </div>
          </div>

          {generatedLink ? (
            <div className="space-y-4 rounded-xl border bg-background/80 p-4">
              <div className="space-y-2">
                <p className="text-sm font-semibold text-foreground">Link generato</p>
                <p className="text-sm text-muted-foreground">
                  Cliente selezionato: <span className="font-medium text-foreground">{generatedLink.clientName}</span>
                </p>
              </div>

              <div className="space-y-2">
                <Input value={fullUrl} readOnly className="text-xs font-mono" />
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" onClick={() => void handleCopyLink()}>
                    {copied ? (
                      <Check className="mr-2 h-4 w-4 text-emerald-500" />
                    ) : (
                      <Copy className="mr-2 h-4 w-4" />
                    )}
                    {copied ? "Copiato" : "Copia link"}
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleOpenLink}>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Apri link
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleValidateLink}
                    disabled={portalValidation.isPending}
                  >
                    {portalValidation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <TestTube2 className="mr-2 h-4 w-4" />
                    )}
                    Verifica link pubblico
                  </Button>
                </div>
              </div>

              <div className="rounded-xl border bg-background/80 p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-foreground">Esito test</p>
                      <StatusBadge label={validationBadge.label} tone={validationBadge.tone} />
                    </div>
                    {portalValidation.data ? (
                      <>
                        <p className="text-sm text-muted-foreground">{portalValidation.data.summary}</p>
                        {portalValidation.data.masked_client_name && portalValidation.data.masked_trainer_name ? (
                          <p className="text-xs text-muted-foreground">
                            Token verificato per {portalValidation.data.masked_client_name} con trainer{" "}
                            {portalValidation.data.masked_trainer_name}.
                          </p>
                        ) : null}
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        Dopo la generazione, esegui la verifica per controllare pagina pubblica e
                        token anamnesi reale.
                      </p>
                    )}
                  </div>
                </div>

                {portalValidation.data ? (
                  <div className="mt-4 grid gap-3 lg:grid-cols-3">
                    {portalValidation.data.checks.map((check) => {
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
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
