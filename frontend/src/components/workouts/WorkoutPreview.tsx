// src/components/workouts/WorkoutPreview.tsx
"use client";

/**
 * Preview professionale stampabile della scheda allenamento.
 * Layout pulito con header, tabelle per sessione (3 sezioni), footer.
 * Lo stesso HTML e' usato per @media print.
 */

import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import type { SessionCardData } from "./SessionCard";
import type { WorkoutExerciseRow } from "@/types/api";

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza",
  ipertrofia: "Ipertrofia",
  resistenza: "Resistenza",
  dimagrimento: "Dimagrimento",
  generale: "Generale",
};

const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante",
  intermedio: "Intermedio",
  avanzato: "Avanzato",
};

const SECTION_PREVIEW_CONFIG: Record<TemplateSection, { label: string; color: string }> = {
  avviamento: { label: "Avviamento", color: "text-amber-600 dark:text-amber-400" },
  principale: { label: "Esercizio Principale", color: "text-primary" },
  stretching: { label: "Stretching & Mobilita", color: "text-cyan-600 dark:text-cyan-400" },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

interface WorkoutPreviewProps {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  durata_settimane: number;
  sessioni_per_settimana: number;
  sessioni: SessionCardData[];
  note?: string | null;
}

function groupBySection(esercizi: WorkoutExerciseRow[]) {
  const groups: Record<TemplateSection, WorkoutExerciseRow[]> = {
    avviamento: [],
    principale: [],
    stretching: [],
  };
  for (const ex of esercizi) {
    const section = getSectionForCategory(ex.esercizio_categoria);
    groups[section].push(ex);
  }
  return groups;
}

export function WorkoutPreview({
  nome,
  obiettivo,
  livello,
  clientNome,
  durata_settimane,
  sessioni_per_settimana,
  sessioni,
  note,
}: WorkoutPreviewProps) {
  return (
    <div className="workout-preview bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 rounded-lg border p-6 space-y-6">
      {/* ── Header ── */}
      <div className="border-l-4 border-primary pl-4">
        <h2 className="text-xl font-bold tracking-tight">{nome}</h2>
        {clientNome && (
          <p className="text-sm text-muted-foreground mt-0.5">{clientNome}</p>
        )}
        <div className="flex flex-wrap gap-2 mt-2">
          <Badge variant="outline" className="text-xs">
            {OBIETTIVO_LABELS[obiettivo] ?? obiettivo}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {LIVELLO_LABELS[livello] ?? livello}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {sessioni_per_settimana}x / settimana
          </Badge>
          <Badge variant="outline" className="text-xs">
            {durata_settimane} settimane
          </Badge>
        </div>
      </div>

      {/* ── Sessioni ── */}
      {sessioni.map((session) => (
        <SessionPreview key={session.id} session={session} />
      ))}

      {/* ── Note ── */}
      {note && (
        <div className="text-xs text-muted-foreground border-t pt-3">
          <p className="font-medium mb-1">Note:</p>
          <p>{note}</p>
        </div>
      )}

      {/* ── Footer ── */}
      <div className="flex items-center justify-between border-t pt-3 text-[10px] text-muted-foreground">
        <span>ProFit AI Studio</span>
        <span>{new Date().toLocaleDateString("it-IT")}</span>
      </div>
    </div>
  );
}

// ── Session sub-component ──

function SessionPreview({ session }: { session: SessionCardData }) {
  const grouped = useMemo(() => groupBySection(session.esercizi), [session.esercizi]);

  return (
    <div className="workout-session">
      <div className="flex items-center gap-2 mb-2">
        <span className="flex h-6 w-6 items-center justify-center rounded bg-primary/10 text-xs font-bold text-primary">
          {session.numero_sessione}
        </span>
        <h3 className="text-sm font-semibold">{session.nome_sessione}</h3>
        {session.focus_muscolare && (
          <span className="text-xs text-muted-foreground">
            — {session.focus_muscolare}
          </span>
        )}
      </div>

      {SECTION_ORDER.map((sectionKey) => {
        const exercises = grouped[sectionKey];
        if (exercises.length === 0) return null;
        const config = SECTION_PREVIEW_CONFIG[sectionKey];

        return (
          <div key={sectionKey} className="mb-2">
            <p className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${config.color}`}>
              {config.label}
            </p>
            <table className="w-full text-xs border-collapse">
              {sectionKey === "principale" && (
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="py-1 text-left font-medium w-8">#</th>
                    <th className="py-1 text-left font-medium">Esercizio</th>
                    <th className="py-1 text-center font-medium w-14">Serie</th>
                    <th className="py-1 text-center font-medium w-16">Rip</th>
                    <th className="py-1 text-center font-medium w-16">Riposo</th>
                    <th className="py-1 text-left font-medium w-24">Note</th>
                  </tr>
                </thead>
              )}
              <tbody>
                {exercises.map((ex, idx) => (
                  <tr key={ex.id} className="border-b border-dashed last:border-0">
                    <td className="py-1 text-muted-foreground">{idx + 1}</td>
                    <td className="py-1 font-medium">{ex.esercizio_nome}</td>
                    <td className="py-1 text-center tabular-nums">{ex.serie}</td>
                    <td className="py-1 text-center tabular-nums">{ex.ripetizioni}</td>
                    {sectionKey === "principale" && (
                      <>
                        <td className="py-1 text-center tabular-nums">{ex.tempo_riposo_sec}s</td>
                        <td className="py-1 text-muted-foreground truncate max-w-[100px]">
                          {ex.note ?? "—"}
                        </td>
                      </>
                    )}
                    {sectionKey !== "principale" && (
                      <td colSpan={2} className="py-1 text-muted-foreground truncate max-w-[100px]">
                        {ex.note ?? ""}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}

      {session.esercizi.length === 0 && (
        <p className="py-4 text-center text-xs text-muted-foreground italic">
          Nessun esercizio
        </p>
      )}
    </div>
  );
}
