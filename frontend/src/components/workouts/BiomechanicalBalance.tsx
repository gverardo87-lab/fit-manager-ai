// src/components/workouts/BiomechanicalBalance.tsx
"use client";

/**
 * Sezione 2: Equilibrio Biomeccanico — Due livelli.
 *
 * 2A — Profilo di Carico: distribuzione volume per dimensione di movimento.
 *       Puro frontend, aggrega da exerciseMap (zero API call).
 *
 * 2B — Rapporti di Forza: 5 balance ratios dal backend con spiegazione clinica.
 *       Dati: TSAnalisiPiano.dettaglio_rapporti.
 *
 * Fonti: NSCA 2016 cap.17, Sahrmann 2002, Schoenfeld 2017.
 */

import { useState, useMemo } from "react";
import { ChevronDown, Scale, BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  aggregateWeeklyDemand,
  detectDemandConcentration,
  DIMENSION_LABELS,
  PRIMARY_DIMENSIONS,
  type DemandProfile,
  type PrimaryDimension,
} from "@/lib/demand-aggregation";
import { PatternRadarChart } from "./PatternRadarChart";
import type { Exercise, TSAnalisiPiano, TSDettaglioRapporto } from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface BiomechanicalBalanceProps {
  analysis: TSAnalisiPiano;
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number }>;
  }>;
  exerciseMap: Map<number, Exercise>;
}

// ════════════════════════════════════════════════════════════
// SPIEGAZIONI RAPPORTI (testo statico, 3 fonti)
// ════════════════════════════════════════════════════════════

const RATIO_EXPLANATIONS: Record<string, { meaning: string; action: string }> = {
  "Push : Pull": {
    meaning:
      "Il rapporto tra volume di spinta e trazione. Uno squilibrio puo' portare a protrazione scapolare e sovraccarico della cuffia dei rotatori.",
    action:
      "Aggiungi serie di trazione orizzontale (row, face pull) o riduci serie di push.",
  },
  "Push Orizz : Push Vert": {
    meaning:
      "Bilancia lavoro petto (orizzontale) e spalle (verticale). Un eccesso orizzontale sottostimola i deltoidi.",
    action: "Aggiungi serie di push verticale (OHP, push press) o riduci panca.",
  },
  "Pull Orizz : Pull Vert": {
    meaning:
      "Bilancia spessore (row) e larghezza (pulldown) del dorso. Tolleranza ampia: il pull orizzontale recluta piu' massa.",
    action: "Aggiungi serie di pull verticale (lat pulldown, trazioni) se troppo basso.",
  },
  "Quad : Ham": {
    meaning:
      "Stabilita' del ginocchio e prevenzione ACL. Range 1.0-1.5 accettabile (NSCA 2016).",
    action: "Aggiungi leg curl o Romanian deadlift per femorali, o riduci leg extension.",
  },
  "Anteriore : Posteriore": {
    meaning:
      "Prevenzione upper/lower cross syndrome (Janda 1983). La catena posteriore dovrebbe predominare leggermente.",
    action: "Aggiungi lavoro per dorsali, deltoide posteriore e femorali.",
  },
};

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function BiomechanicalBalance({
  analysis,
  sessions,
  exerciseMap,
}: BiomechanicalBalanceProps) {
  const [isOpen, setIsOpen] = useState(true);
  const rapporti = analysis.dettaglio_rapporti;
  const squilibri = rapporti.filter((r) => !r.in_tolleranza).length;

  // 2A: Demand profile settimanale
  const weeklyProfile = useMemo(
    () => aggregateWeeklyDemand(sessions, exerciseMap),
    [sessions, exerciseMap],
  );
  const concentrations = useMemo(
    () => detectDemandConcentration(weeklyProfile),
    [weeklyProfile],
  );

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4 border-l-blue-500/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="h-4 w-4 text-blue-600" />
                <CardTitle className="text-sm font-semibold">
                  Equilibrio Biomeccanico
                </CardTitle>
                {squilibri > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {squilibri} squilibr{squilibri === 1 ? "io" : "i"}
                  </Badge>
                )}
                {concentrations.length > 0 && (
                  <Badge className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                    {concentrations.length} concentrazion{concentrations.length === 1 ? "e" : "i"}
                  </Badge>
                )}
                {squilibri === 0 && concentrations.length === 0 && (
                  <Badge className="text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    Bilanciato
                  </Badge>
                )}
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 px-4 pb-4 space-y-4">
            {/* 2A — Profilo di Carico */}
            <DemandProfileSection profile={weeklyProfile} concentrations={concentrations} />

            {/* Separatore */}
            <div className="border-t border-border/50" />

            {/* 2B — Rapporti di Forza */}
            <ForceRatiosSection rapporti={rapporti} weeklyProfile={weeklyProfile} />
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// 2A — PROFILO DI CARICO
// ════════════════════════════════════════════════════════════

function DemandProfileSection({
  profile,
  concentrations,
}: {
  profile: DemandProfile;
  concentrations: Array<{ dimension: PrimaryDimension; percentage: number }>;
}) {
  if (profile.totalSeries === 0) return null;
  const concentrationSet = new Set(concentrations.map((c) => c.dimension));

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <BarChart3 className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Profilo di Carico
        </span>
      </div>

      {/* Radar Chart */}
      <PatternRadarChart profile={profile} concentrations={concentrations} />

      {/* Barre dettaglio con serie */}
      <div className="space-y-1">
        {PRIMARY_DIMENSIONS.map((dim) => {
          const pct = profile.distribution[dim];
          const isConcentrated = concentrationSet.has(dim);
          const barColor = isConcentrated
            ? "bg-amber-500"
            : pct > 0
              ? "bg-primary"
              : "bg-muted";

          return (
            <div key={dim} className="flex items-center gap-2">
              <span className="text-[10px] w-28 shrink-0 truncate text-muted-foreground">
                {DIMENSION_LABELS[dim]}
              </span>
              <div className="flex-1 h-2.5 bg-muted/40 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${barColor}`}
                  style={{ width: `${Math.round(pct * 100)}%` }}
                />
              </div>
              <span
                className={`text-[10px] font-mono tabular-nums w-8 text-right shrink-0 ${
                  isConcentrated ? "text-amber-600 font-bold" : "text-muted-foreground"
                }`}
              >
                {Math.round(pct * 100)}%
              </span>
            </div>
          );
        })}
      </div>

      {concentrations.length > 0 && (
        <p className="text-[10px] text-amber-600 dark:text-amber-400">
          Concentrazione:{" "}
          {concentrations
            .map(
              (c) =>
                `${DIMENSION_LABELS[c.dimension]} (${Math.round(c.percentage * 100)}%)`,
            )
            .join(", ")}
          . Valuta di diversificare i pattern.
        </p>
      )}

      {concentrations.length === 0 && profile.totalSeries > 0 && (
        <p className="text-[10px] text-emerald-600 dark:text-emerald-400">
          Distribuzione bilanciata — nessuna concentrazione rilevata.
        </p>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 2B — RAPPORTI DI FORZA
// ════════════════════════════════════════════════════════════

function ForceRatiosSection({
  rapporti,
  weeklyProfile,
}: {
  rapporti: TSDettaglioRapporto[];
  weeklyProfile: DemandProfile;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Scale className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Rapporti di Forza
        </span>
      </div>

      <div className="space-y-1">
        {rapporti.map((r) => (
          <RatioRow key={r.nome} ratio={r} weeklyProfile={weeklyProfile} />
        ))}
      </div>

      <p className="text-[10px] text-muted-foreground">
        Fonti: NSCA 2016, Sahrmann 2002, Alentorn-Geli 2009.
      </p>
    </div>
  );
}

function RatioRow({
  ratio,
  weeklyProfile,
}: {
  ratio: TSDettaglioRapporto;
  weeklyProfile: DemandProfile;
}) {
  const [expanded, setExpanded] = useState(false);
  const explanation = RATIO_EXPLANATIONS[ratio.nome];

  // Barra posizionale: mostra il valore nel range di tolleranza
  const rangeMin = Math.max(0, ratio.target - ratio.tolleranza * 2);
  const rangeMax = ratio.target + ratio.tolleranza * 2;
  const range = rangeMax - rangeMin;
  const valuePct = Math.min(100, Math.max(0, ((ratio.valore - rangeMin) / range) * 100));
  const targetPct = ((ratio.target - rangeMin) / range) * 100;
  const tolMinPct = ((ratio.target - ratio.tolleranza - rangeMin) / range) * 100;
  const tolMaxPct = ((ratio.target + ratio.tolleranza - rangeMin) / range) * 100;

  return (
    <div
      className={`rounded transition-colors ${
        expanded ? "bg-muted/20" : "hover:bg-muted/10"
      }`}
    >
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-3 py-1.5 flex items-center gap-2"
      >
        <span className="text-[11px] font-medium w-36 shrink-0 truncate">{ratio.nome}</span>

        <Badge
          className={`text-[10px] px-1.5 py-0 ${
            ratio.in_tolleranza
              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
          }`}
        >
          {ratio.valore.toFixed(2)}
        </Badge>

        {/* Barra posizionale */}
        <div className="flex-1 h-3 bg-muted/40 rounded-full relative overflow-hidden">
          {/* Zona tolleranza */}
          <div
            className="absolute inset-y-0 bg-emerald-200/40 dark:bg-emerald-900/30"
            style={{ left: `${tolMinPct}%`, width: `${tolMaxPct - tolMinPct}%` }}
          />
          {/* Linea target */}
          <div
            className="absolute inset-y-0 w-0.5 bg-emerald-600/60"
            style={{ left: `${targetPct}%` }}
          />
          {/* Indicatore valore */}
          <div
            className={`absolute top-0.5 w-2 h-2 rounded-full ${
              ratio.in_tolleranza ? "bg-emerald-600" : "bg-red-500"
            }`}
            style={{ left: `calc(${valuePct}% - 4px)` }}
          />
        </div>

        <span className="text-[10px] text-muted-foreground w-14 text-right shrink-0">
          tgt {ratio.target.toFixed(2)}
        </span>

        <ChevronDown
          className={`h-3 w-3 text-muted-foreground transition-transform shrink-0 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {expanded && (
        <div className="px-3 pb-2 space-y-1.5">
          {/* Volume dettaglio */}
          <div className="text-[10px] text-muted-foreground flex gap-4">
            <span>Numeratore: {ratio.volume_numeratore} serie</span>
            <span>Denominatore: {ratio.volume_denominatore} serie</span>
            <span>Tolleranza: ±{ratio.tolleranza.toFixed(2)}</span>
          </div>

          {/* Spiegazione clinica */}
          {explanation && (
            <div className="text-[10px] space-y-0.5">
              <p className="text-muted-foreground">{explanation.meaning}</p>
              {!ratio.in_tolleranza && (
                <p className="text-primary font-medium">{explanation.action}</p>
              )}
            </div>
          )}

          {/* Cross-reference con demand profile */}
          {ratio.nome === "Push : Pull" && weeklyProfile.totalSeries > 0 && (
            <div className="text-[10px] text-muted-foreground">
              Profilo di carico: spinta{" "}
              {Math.round(
                ((weeklyProfile.distribution.push_h ?? 0) +
                  (weeklyProfile.distribution.push_v ?? 0)) *
                  100,
              )}
              % — trazione{" "}
              {Math.round(
                ((weeklyProfile.distribution.pull_h ?? 0) +
                  (weeklyProfile.distribution.pull_v ?? 0)) *
                  100,
              )}
              %
            </div>
          )}

          {/* Fonte */}
          <p className="text-[9px] text-muted-foreground italic">{ratio.fonte}</p>
        </div>
      )}
    </div>
  );
}
