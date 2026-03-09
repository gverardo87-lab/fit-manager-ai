// src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx
"use client";

/**
 * Pagina dedicata Anamnesi.
 *
 * Promossa da tab a pagina full-width.
 * Tre stati: nessuna anamnesi → empty CTA, legacy → ricompila CTA, strutturata → summary + edit.
 * Il wizard vive come Dialog controllato da useState locale.
 *
 * Back button: torna al profilo cliente.
 */

import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  Copy,
  ExternalLink,
  HeartPulse,
  Link2,
  Loader2,
  Plus,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { AnamnesiSummary } from "@/components/clients/anamnesi/AnamnesiSummary";
import { AnamnesiWizard } from "@/components/clients/anamnesi/AnamnesiWizard";
import { isStructuredAnamnesi } from "@/components/clients/anamnesi/anamnesi-helpers";
import { useClient, useCreateShareToken } from "@/hooks/useClients";
import type { AnamnesiData, ShareTokenResponse } from "@/types/api";

// ════════════════════════════════════════════════════════════
// PAGE COMPONENT
// ════════════════════════════════════════════════════════════

export default function AnamnesiPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const fromParam = searchParams.get("from");

  const backNav = useMemo(() => {
    if (fromParam?.startsWith("monitoraggio-")) {
      const cId = fromParam.replace("monitoraggio-", "");
      return { href: `/monitoraggio/${cId}`, label: "Portale Cliente" };
    }
    return { href: `/clienti/${clientId}`, label: "Profilo" };
  }, [fromParam, clientId]);

  const { data: client, isLoading } = useClient(clientId);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const autoOpenWizardConsumedRef = useRef(false);

  const shouldAutoOpenWizard = searchParams.get("startWizard") === "1";

  useEffect(() => {
    if (!shouldAutoOpenWizard || autoOpenWizardConsumedRef.current) return;
    autoOpenWizardConsumedRef.current = true;

    // Consuma il flag dall'URL per evitare riaperture involontarie
    const params = new URLSearchParams(searchParams.toString());
    params.delete("startWizard");
    const qs = params.toString();
    router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });

    const rafId = window.requestAnimationFrame(() => setWizardOpen(true));
    return () => window.cancelAnimationFrame(rafId);
  }, [shouldAutoOpenWizard, searchParams, router, pathname]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <p className="text-lg font-medium">Cliente non trovato</p>
      </div>
    );
  }

  const anamnesi = client.anamnesi ?? null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={backNav.href}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-white shadow-sm transition-colors hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800"
          title={`Torna a ${backNav.label}`}
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">Anamnesi</h1>
          <p className="text-sm text-muted-foreground">
            {client.nome} {client.cognome}
          </p>
        </div>
        {/* Bottone Invia Questionario — sempre visibile */}
        <Button variant="outline" size="sm" onClick={() => setShareOpen(true)}>
          <Link2 className="mr-1.5 h-4 w-4" />
          <span className="hidden sm:inline">Invia Questionario</span>
          <span className="sm:hidden">Invia</span>
        </Button>
        <HeartPulse className="hidden sm:block h-8 w-8 text-rose-500/50" />
      </div>

      {/* Content: 3-state rendering */}
      <AnamnesiContent
        anamnesi={anamnesi}
        onOpenWizard={() => setWizardOpen(true)}
        onOpenShare={() => setShareOpen(true)}
      />

      {/* Wizard Dialog */}
      <AnamnesiWizard
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        clientId={clientId}
        existing={anamnesi}
      />

      {/* Share Dialog */}
      <ShareAnamnesiDialog
        open={shareOpen}
        onOpenChange={setShareOpen}
        clientId={clientId}
        clientName={`${client.nome} ${client.cognome}`}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// ANAMNESI CONTENT (3-state)
// ════════════════════════════════════════════════════════════

function AnamnesiContent({
  anamnesi,
  onOpenWizard,
  onOpenShare,
}: {
  anamnesi: AnamnesiData | Record<string, unknown> | null;
  onOpenWizard: () => void;
  onOpenShare: () => void;
}) {
  // Nessuna anamnesi
  if (!anamnesi) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <HeartPulse className="h-10 w-10 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">
          Nessuna anamnesi compilata per questo cliente
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onOpenWizard}>
            <Plus className="mr-2 h-4 w-4" />
            Compila tu
          </Button>
          <Button variant="outline" size="sm" onClick={onOpenShare}>
            <Link2 className="mr-2 h-4 w-4" />
            Invia al cliente
          </Button>
        </div>
      </div>
    );
  }

  // Anamnesi formato vecchio (legacy dict)
  if (!isStructuredAnamnesi(anamnesi as Record<string, unknown>)) {
    const legacyNote = (anamnesi as Record<string, unknown>).note;
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <HeartPulse className="h-10 w-10 text-amber-500/50" />
        <p className="text-sm text-muted-foreground">
          Anamnesi in formato precedente — ricompila per il nuovo questionario
        </p>
        {typeof legacyNote === "string" && legacyNote && (
          <p className="text-xs text-muted-foreground italic max-w-md text-center">
            Nota precedente: {legacyNote}
          </p>
        )}
        <Button variant="outline" size="sm" onClick={onOpenWizard}>
          <Plus className="mr-2 h-4 w-4" />
          Ricompila Anamnesi
        </Button>
      </div>
    );
  }

  // Anamnesi strutturata
  return <AnamnesiSummary data={anamnesi as AnamnesiData} onEdit={onOpenWizard} />;
}

// ════════════════════════════════════════════════════════════
// SHARE DIALOG — genera link monouso
// ════════════════════════════════════════════════════════════

function ShareAnamnesiDialog({
  open,
  onOpenChange,
  clientId,
  clientName,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: number;
  clientName: string;
}) {
  const createToken = useCreateShareToken(clientId);
  const [result, setResult] = useState<ShareTokenResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const isLocalhost =
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1");

  // Reset stato quando si chiude
  const handleOpenChange = useCallback((v: boolean) => {
    if (!v) {
      setResult(null);
      setCopied(false);
    }
    onOpenChange(v);
  }, [onOpenChange]);

  const handleGenerate = useCallback(() => {
    createToken.mutate(undefined, {
      onSuccess: (data) => setResult(data),
    });
  }, [createToken]);

  const fullUrl = result
    ? result.url.startsWith("http")
      ? result.url
      : `${typeof window !== "undefined" ? window.location.origin : ""}${result.url}`
    : "";

  const handleCopy = useCallback(() => {
    if (!fullUrl) return;
    navigator.clipboard.writeText(fullUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [fullUrl]);

  const handleWhatsApp = useCallback(() => {
    if (!fullUrl) return;
    const text = encodeURIComponent(
      `Ciao! Per completare il tuo profilo fitness, compila questo breve questionario:\n${fullUrl}\n\nIl link e' valido per 48 ore.`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  }, [fullUrl]);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invia Questionario Anamnesi</DialogTitle>
          <DialogDescription>
            Genera un link monouso per <strong>{clientName}</strong>.
            Il cliente compila il questionario direttamente dal proprio smartphone.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Warning localhost — link non funziona dal cellulare (nascosto se PUBLIC_BASE_URL configurato) */}
          {isLocalhost && !(result?.url.startsWith("http")) && (
            <div className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30 p-3 text-xs text-amber-800 dark:text-amber-300">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-medium">Stai usando localhost</p>
                <p>
                  Il link generato funziona solo su questo PC. Per inviarlo al cliente,
                  accedi al CRM tramite{" "}
                  <strong>IP LAN</strong> (es.{" "}
                  <code className="font-mono bg-amber-100 dark:bg-amber-900/50 px-1 rounded">
                    192.168.1.23:3000
                  </code>
                  ) o Tailscale.
                </p>
              </div>
            </div>
          )}
          {!result ? (
            <>
              <div className="rounded-lg border bg-muted/40 p-3 text-xs text-muted-foreground space-y-1">
                <p>• Il link e' <strong>monouso</strong>: dopo l&apos;invio non puo' essere riutilizzato</p>
                <p>• Scade dopo <strong>48 ore</strong> dalla generazione</p>
                <p>• I dati vengono salvati direttamente nel profilo cliente</p>
                <p>• Il link funziona solo mentre FitManager e' aperto</p>
              </div>
              <Button
                className="w-full"
                onClick={handleGenerate}
                disabled={createToken.isPending}
              >
                {createToken.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Link2 className="mr-2 h-4 w-4" />
                )}
                {createToken.isPending ? "Generazione..." : "Genera Link"}
              </Button>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Link generato</p>
                <div className="flex gap-2">
                  <Input
                    value={fullUrl}
                    readOnly
                    className="text-xs font-mono"
                    onClick={(e) => (e.target as HTMLInputElement).select()}
                  />
                  <Button size="icon" variant="outline" onClick={handleCopy} title="Copia link">
                    {copied ? (
                      <Check className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Scade:{" "}
                  {new Date(result.expires_at).toLocaleString("it-IT", {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>

              <div className="flex gap-2">
                <Button className="flex-1 bg-[#25D366] hover:bg-[#1ebe5d] text-white" onClick={handleWhatsApp}>
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Invia su WhatsApp
                </Button>
                <Button variant="outline" className="flex-1" onClick={handleCopy}>
                  {copied ? (
                    <><Check className="mr-2 h-4 w-4 text-emerald-500" />Copiato!</>
                  ) : (
                    <><Copy className="mr-2 h-4 w-4" />Copia link</>
                  )}
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
