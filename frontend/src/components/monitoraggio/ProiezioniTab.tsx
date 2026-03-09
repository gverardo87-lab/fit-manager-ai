// src/components/monitoraggio/ProiezioniTab.tsx
"use client";

/**
 * Tab Proiezioni — Worklist aggregate proiezioni obiettivi.
 *
 * Mostra i clienti con obiettivi attivi come righe espandibili full-width.
 * Compact: nome + trend badges + status icon + CTA.
 * Expanded: trends dettagliati, proiezioni, risk flags, compliance.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  ChevronDown,
  Clock,
  Rocket,
  Search,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useClients } from "@/hooks/useClients";
import { useClientProjection } from "@/hooks/useDashboard";
import type { ClientProjectionResponse } from "@/types/api";

// ── Types ──

interface CardSummary {
  hasData: boolean;
  hasProjections: boolean;
  onTrackCount: number;
  lateCount: number;
  wrongDirectionCount: number;
  riskCount: number;
  complianceLow: boolean;
}

// ── Projection Row ──

function ProjectionClientRow({ clientId, nome, cognome, expanded, onToggle, onSummary }: {
  clientId: number;
  nome: string;
  cognome: string;
  expanded: boolean;
  onToggle: () => void;
  onSummary: (clientId: number, summary: CardSummary | null) => void;
}) {
  const { data, isLoading } = useClientProjection(clientId);
  const reportedRef = useRef<string>("");

  const dataKey = data
    ? `${data.has_measurements}-${data.has_goals}-${data.projections.length}-${data.risk_flags.length}-${data.compliance_pct}`
    : "none";

  useEffect(() => {
    if (dataKey === reportedRef.current) return;
    reportedRef.current = dataKey;
    if (!data || (!data.has_measurements && !data.has_goals)) {
      onSummary(clientId, null);
    } else {
      const projected = data.projections.filter((p) => p.status === "projected");
      const wrongDir = data.projections.filter((p) => p.status === "wrong_direction");
      const onTrack = projected.filter((p) => p.on_track);
      const late = projected.filter((p) => !p.on_track);
      onSummary(clientId, {
        hasData: true,
        hasProjections: projected.length > 0 || wrongDir.length > 0,
        onTrackCount: onTrack.length,
        lateCount: late.length,
        wrongDirectionCount: wrongDir.length,
        riskCount: data.risk_flags.length,
        complianceLow: data.has_active_plan && data.compliance_pct < 60,
      });
    }
  }, [dataKey, data, clientId, onSummary]);

  if (isLoading) {
    return <Skeleton className="h-14 rounded-xl" />;
  }

  if (!data || (!data.has_measurements && !data.has_goals)) {
    return null;
  }

  const projected = data.projections.filter((p) => p.status === "projected");
  const wrongDir = data.projections.filter((p) => p.status === "wrong_direction");
  const risks = data.risk_flags.length;

  // Border color by worst status
  let borderColor = "border-l-zinc-300";
  if (wrongDir.length > 0 || risks > 0) borderColor = "border-l-red-400";
  else if (projected.length > 0) borderColor = "border-l-emerald-400";
  else borderColor = "border-l-amber-400";

  // Status dot
  let statusDot = "bg-zinc-400";
  if (wrongDir.length > 0 || risks > 0) statusDot = "bg-red-500";
  else if (projected.some((p) => p.on_track)) statusDot = "bg-emerald-500";
  else if (projected.length > 0) statusDot = "bg-amber-500";

  return (
    <div className={`rounded-xl border border-l-4 ${borderColor} bg-white transition-all duration-200 shadow-sm dark:bg-zinc-900`}>
      {/* ── Compact Row ── */}
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-3 p-3 text-left sm:px-4"
      >
        <div className={`h-2 w-2 shrink-0 rounded-full ${statusDot}`} />

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{cognome} {nome}</p>
          {data.plan_name && (
            <p className="truncate text-xs text-muted-foreground">{data.plan_name}</p>
          )}
        </div>

        {/* Compact trend badges (desktop) */}
        <div className="hidden shrink-0 items-center gap-1.5 sm:flex">
          {data.trends.slice(0, 2).map((t) => (
            <Badge key={t.metric_id} variant="outline" className="gap-1 text-[10px]">
              {t.weekly_rate >= 0 ? (
                <TrendingUp className="h-2.5 w-2.5 text-emerald-500" />
              ) : (
                <TrendingDown className="h-2.5 w-2.5 text-red-500" />
              )}
              {t.metric_name}
            </Badge>
          ))}
          {data.trends.length > 2 && (
            <Badge variant="outline" className="text-[10px]">+{data.trends.length - 2}</Badge>
          )}
        </div>

        {/* Risk badge */}
        {risks > 0 && (
          <Badge variant="outline" className="shrink-0 border-red-200 bg-red-50 text-[10px] text-red-700 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-300">
            {risks} alert
          </Badge>
        )}

        {/* Compliance */}
        {data.compliance_pct > 0 && (
          <Badge variant="outline" className="hidden shrink-0 text-[10px] sm:inline-flex">
            {data.compliance_pct}%
          </Badge>
        )}

        {/* CTA */}
        <Link
          href={`/clienti/${clientId}/progressi`}
          onClick={(e) => e.stopPropagation()}
          className="shrink-0"
        >
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>

        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* ── Expanded Drill-Down ── */}
      {expanded && (
        <div className="border-t px-4 pb-4 pt-3">
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Left: trends */}
            <div className="space-y-2">
              {data.trends.length > 0 && (
                <div>
                  <p className="mb-1.5 text-[10px] font-medium uppercase text-muted-foreground">
                    Trend settimanali
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {data.trends.map((t) => (
                      <Badge key={t.metric_id} variant="outline" className="gap-1 text-[10px]">
                        {t.weekly_rate >= 0 ? (
                          <TrendingUp className="h-2.5 w-2.5 text-emerald-500" />
                        ) : (
                          <TrendingDown className="h-2.5 w-2.5 text-red-500" />
                        )}
                        {t.metric_name}: {t.weekly_rate >= 0 ? "+" : ""}{t.weekly_rate.toFixed(1)}/{t.unit !== "%" ? t.unit : "%"}/sett
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Risk flags */}
              {risks > 0 && (
                <div className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
                  <AlertTriangle className="h-3 w-3" />
                  {risks} alert clinico
                </div>
              )}
            </div>

            {/* Right: projections */}
            <div className="space-y-2">
              {data.projections.length > 0 && (
                <div>
                  <p className="mb-1.5 text-[10px] font-medium uppercase text-muted-foreground">
                    Proiezioni obiettivi
                  </p>
                  <div className="space-y-1">
                    {data.projections.map((p) => (
                      <ProjectionLine key={p.goal_id} proj={p} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bottom link */}
          <div className="mt-3 flex items-center justify-end border-t pt-3">
            <Link
              href={`/clienti/${clientId}/progressi`}
              className="text-xs text-muted-foreground hover:text-foreground hover:underline"
            >
              Progressi completi →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function ProjectionLine({ proj }: { proj: ClientProjectionResponse["projections"][0] }) {
  const statusIcon = {
    projected: <Rocket className="h-3 w-3 text-emerald-500" />,
    wrong_direction: <AlertTriangle className="h-3 w-3 text-red-500" />,
    plateau: <TrendingDown className="h-3 w-3 text-amber-500" />,
    insufficient_data: <Clock className="h-3 w-3 text-zinc-400" />,
    unreachable: <Clock className="h-3 w-3 text-zinc-400" />,
  }[proj.status] ?? <Target className="h-3 w-3 text-zinc-400" />;

  return (
    <div className="flex items-center gap-2 text-xs">
      {statusIcon}
      <span className="truncate font-medium">{proj.metric_name}</span>
      {proj.status === "projected" && proj.eta && (
        <Badge variant="outline" className={`ml-auto text-[9px] shrink-0 ${
          proj.on_track
            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300"
            : "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300"
        }`}>
          {proj.on_track ? "In tempo" : "In ritardo"}
        </Badge>
      )}
      {proj.status === "wrong_direction" && (
        <Badge variant="outline" className="ml-auto text-[9px] shrink-0 bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300">
          Direzione sbagliata
        </Badge>
      )}
    </div>
  );
}

// ── Tab Content ──

export function ProiezioniTab() {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { data: clientsData, isLoading: clientsLoading } = useClients();

  const [summaryMap, setSummaryMap] = useState<Map<number, CardSummary | null>>(new Map());

  const handleSummary = useCallback((clientId: number, summary: CardSummary | null) => {
    setSummaryMap((prev) => {
      const existing = prev.get(clientId);
      if (existing === summary) return prev;
      if (existing && summary && JSON.stringify(existing) === JSON.stringify(summary)) return prev;
      const next = new Map(prev);
      next.set(clientId, summary);
      return next;
    });
  }, []);

  const handleToggle = useCallback((clientId: number) => {
    setExpandedId((prev) => (prev === clientId ? null : clientId));
  }, []);

  const activeClients = useMemo(() => {
    if (!clientsData?.items) return [];
    const trimmed = search.trim().toLowerCase();
    return clientsData.items
      .filter((c) => c.stato?.toLowerCase() === "attivo")
      .filter((c) => {
        if (!trimmed) return true;
        const fullName = `${c.nome} ${c.cognome}`.toLowerCase();
        return fullName.includes(trimmed);
      })
      .sort((a, b) => `${a.cognome} ${a.nome}`.localeCompare(`${b.cognome} ${b.nome}`));
  }, [clientsData, search]);

  const kpi = useMemo(() => {
    let withData = 0;
    let onTrack = 0;
    let late = 0;
    let totalAlerts = 0;

    for (const s of summaryMap.values()) {
      if (!s) continue;
      withData++;
      if (s.onTrackCount > 0 && s.lateCount === 0 && s.wrongDirectionCount === 0) onTrack++;
      if (s.lateCount > 0 || s.wrongDirectionCount > 0 || s.complianceLow) late++;
      totalAlerts += s.riskCount;
      if (s.wrongDirectionCount > 0) totalAlerts += s.wrongDirectionCount;
    }

    return { withData, onTrack, late, totalAlerts };
  }, [summaryMap]);

  if (clientsLoading) {
    return (
      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-12 w-full rounded-xl" />
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-red-200 bg-red-50/80 px-3 py-2 dark:border-red-900/40 dark:bg-red-950/20">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            In ritardo
          </p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-red-700 dark:text-red-300">
            <AnimatedNumber value={kpi.late} />
          </p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-950/20">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Alert
          </p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-amber-700 dark:text-amber-300">
            <AnimatedNumber value={kpi.totalAlerts} />
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900">
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cerca cliente..."
            className="pl-9"
          />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {activeClients.length} client{activeClients.length === 1 ? "e" : "i"} attiv{activeClients.length === 1 ? "o" : "i"}
        </p>
      </div>

      {/* Row List or Empty */}
      {activeClients.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-16 text-center">
          <Rocket className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium">Nessun cliente attivo</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Crea un cliente e registra misurazioni + obiettivi per attivare le proiezioni
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {activeClients.map((c) => (
            <ProjectionClientRow
              key={c.id}
              clientId={c.id}
              nome={c.nome}
              cognome={c.cognome}
              expanded={expandedId === c.id}
              onToggle={() => handleToggle(c.id)}
              onSummary={handleSummary}
            />
          ))}
        </div>
      )}
    </div>
  );
}
