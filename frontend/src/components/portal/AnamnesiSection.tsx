"use client";

/**
 * AnamnesiSection — Stato anamnesi + flag chiave + CTA wizard.
 */

import { useState, useMemo } from "react";
import Link from "next/link";
import { ChevronDown, FileText, Plus, RefreshCw, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { ClientEnriched, ClinicalReadinessClientItem } from "@/types/api";

interface AnamnesiSectionProps {
  client: ClientEnriched;
  anamnesiState: "missing" | "legacy" | "structured";
  readinessItem: ClinicalReadinessClientItem | null;
  clientId: number;
}

const STATE_CONFIG: Record<string, { label: string; icon: typeof CheckCircle; color: string; border: string; badgeClass: string }> = {
  structured: {
    label: "Compilata",
    icon: CheckCircle,
    color: "text-emerald-500",
    border: "border-l-emerald-500",
    badgeClass: "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  },
  legacy: {
    label: "Legacy",
    icon: AlertCircle,
    color: "text-amber-500",
    border: "border-l-amber-500",
    badgeClass: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  },
  missing: {
    label: "Mancante",
    icon: XCircle,
    color: "text-red-500",
    border: "border-l-red-500",
    badgeClass: "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
};

interface AnamnesiFlag {
  label: string;
  present: boolean;
}

function extractFlags(anamnesi: Record<string, unknown> | null): AnamnesiFlag[] {
  if (!anamnesi) return [];
  const flags: AnamnesiFlag[] = [];

  // v2 fields (questionario Chiara) — checked first
  const v2Fields: [string, string][] = [
    ["dolori_attuali", "Dolori attuali"],
    ["infortuni_importanti", "Infortuni importanti"],
    ["patologie", "Patologie"],
    ["limitazioni_mediche", "Limitazioni mediche"],
  ];

  // v1 fields (legacy structured) — fallback
  const v1Fields: [string, string][] = [
    ["infortuni_attuali", "Infortuni attuali"],
    ["problemi_cardiovascolari", "Problemi cardiovascolari"],
    ["problemi_respiratori", "Problemi respiratori"],
    ["interventi_chirurgici", "Interventi chirurgici"],
  ];

  const fieldsToCheck = "obiettivo_principale" in anamnesi ? v2Fields : v1Fields;

  for (const [key, label] of fieldsToCheck) {
    if (key in anamnesi) {
      const value = anamnesi[key];
      const present = typeof value === "boolean"
        ? value
        : typeof value === "object" && value !== null && !Array.isArray(value)
          ? !!(value as Record<string, unknown>).presente
          : typeof value === "string"
            ? value.length > 0 && value !== "no" && value !== "nessuno"
            : Array.isArray(value) ? value.length > 0 : !!value;
      flags.push({ label, present });
    }
  }

  return flags;
}

export function AnamnesiSection({
  client,
  anamnesiState,
  readinessItem,
  clientId,
}: AnamnesiSectionProps) {
  const [open, setOpen] = useState(true);

  const config = STATE_CONFIG[anamnesiState];
  const StateIcon = config.icon;

  // Parse anamnesi — typed as AnamnesiData | null on ClientEnriched
  const anamnesiData = useMemo((): Record<string, unknown> | null => {
    if (!client.anamnesi) return null;
    try {
      if (typeof client.anamnesi === "string") {
        return JSON.parse(client.anamnesi) as Record<string, unknown>;
      }
      // AnamnesiData → cast via unknown to Record for generic flag extraction
      return client.anamnesi as unknown as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [client.anamnesi]);

  const flags = useMemo(() => extractFlags(anamnesiData), [anamnesiData]);
  const activeFlags = flags.filter((f) => f.present);

  // Last update
  const lastUpdate = useMemo(() => {
    if (!anamnesiData) return null;
    const date = anamnesiData.data_compilazione ?? anamnesiData.data_aggiornamento;
    if (typeof date !== "string") return null;
    try {
      return new Date(date).toLocaleDateString("it-IT", { day: "numeric", month: "long", year: "numeric" });
    } catch {
      return null;
    }
  }, [anamnesiData]);

  const ctaLabel = anamnesiState === "missing" ? "Compila Anamnesi" : "Aggiorna Anamnesi";
  const ctaIcon = anamnesiState === "missing" ? Plus : RefreshCw;
  const CtaIcon = ctaIcon;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className={`rounded-xl border border-l-4 ${config.border} bg-white shadow-sm dark:bg-zinc-900`}>
        <CollapsibleTrigger asChild>
          <button type="button" className="flex w-full items-center justify-between p-4 text-left">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-violet-500" />
              <h2 className="text-sm font-semibold">Anamnesi</h2>
              <Badge variant="outline" className={`text-[10px] ${config.badgeClass}`}>
                {config.label}
              </Badge>
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {/* State card */}
            <div className="rounded-lg border p-3">
              <div className="flex items-center gap-2">
                <StateIcon className={`h-4 w-4 ${config.color}`} />
                <div>
                  <p className="text-xs font-semibold">
                    {anamnesiState === "missing"
                      ? "Anamnesi non ancora compilata"
                      : anamnesiState === "legacy"
                        ? "Anamnesi in formato legacy — aggiornamento consigliato"
                        : "Anamnesi strutturata"}
                  </p>
                  {lastUpdate && (
                    <p className="text-[10px] text-muted-foreground">
                      Ultimo aggiornamento: {lastUpdate}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Clinical flags */}
            {flags.length > 0 && (
              <div className="rounded-lg border p-3">
                <p className="mb-2 text-xs font-semibold">Flag Clinici</p>
                <div className="flex flex-wrap gap-1.5">
                  {flags.map((flag) => (
                    <Badge
                      key={flag.label}
                      variant="outline"
                      className={`text-[10px] ${
                        flag.present
                          ? "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                          : "border-zinc-200 bg-zinc-50 text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400"
                      }`}
                    >
                      {flag.present ? "!" : "—"} {flag.label}
                    </Badge>
                  ))}
                </div>
                {activeFlags.length > 0 && (
                  <p className="mt-2 text-[10px] text-amber-600 dark:text-amber-400">
                    {activeFlags.length} condizion{activeFlags.length === 1 ? "e" : "i"} rilevat{activeFlags.length === 1 ? "a" : "e"}
                  </p>
                )}
              </div>
            )}

            {/* Readiness info */}
            {readinessItem && (
              <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">Readiness Score</p>
                  <span className="text-sm font-extrabold tabular-nums">{readinessItem.readiness_score}%</span>
                </div>
                {readinessItem.next_action_label && (
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    Prossima azione: <span className="font-medium">{readinessItem.next_action_label}</span>
                  </p>
                )}
              </div>
            )}

            {/* CTA */}
            <div className="flex justify-end">
              <Link href={`/clienti/${clientId}/anamnesi?startWizard=1`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <CtaIcon className="h-3.5 w-3.5" />
                  {ctaLabel}
                </Button>
              </Link>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
