// src/app/(dashboard)/monitoraggio/page.tsx
"use client";

/**
 * Panoramica Monitoraggio — Layout unificato a sezioni collapsibili.
 *
 * Sostituisce i 3 tab con sezioni stacked verticalmente per eliminare
 * la friction del tab-switching. L'utente vede tutto scorrendo.
 *
 * Sezione 1: Salute Clienti (readiness clinica)
 * Sezione 2: Qualita Programmi (analisi metodologica)
 * Sezione 3: Proiezioni (obiettivi aggregate)
 */

import { useState } from "react";
import {
  Activity,
  ChevronDown,
  HeartPulse,
  Rocket,
  Target,
} from "lucide-react";
import { usePageReveal } from "@/lib/page-reveal";

import { SaluteClientiTab } from "@/components/monitoraggio/SaluteClientiTab";
import { QualitaProgrammiTab } from "@/components/monitoraggio/QualitaProgrammiTab";
import { ProiezioniTab } from "@/components/monitoraggio/ProiezioniTab";

// ── Section config ──

interface SectionDef {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
}

const SECTIONS: SectionDef[] = [
  {
    id: "salute",
    title: "Salute Clienti",
    subtitle: "Readiness clinica e onboarding",
    icon: HeartPulse,
    iconBg: "bg-rose-100 dark:bg-rose-900/30",
    iconColor: "text-rose-600 dark:text-rose-400",
  },
  {
    id: "programmi",
    title: "Qualita Programmi",
    subtitle: "Analisi metodologica allenamento",
    icon: Target,
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
  },
  {
    id: "proiezioni",
    title: "Proiezioni",
    subtitle: "Trend obiettivi e alert rischio",
    icon: Rocket,
    iconBg: "bg-violet-100 dark:bg-violet-900/30",
    iconColor: "text-violet-600 dark:text-violet-400",
  },
];

const SECTION_CONTENT: Record<string, React.ComponentType> = {
  salute: SaluteClientiTab,
  programmi: QualitaProgrammiTab,
  proiezioni: ProiezioniTab,
};

export default function MonitoraggioPage() {
  const { revealClass, revealStyle } = usePageReveal();

  // "Salute Clienti" starts expanded (gateway to client portals), others collapsed
  const [collapsed, setCollapsed] = useState<Set<string>>(
    () => new Set(SECTIONS.filter((s) => s.id !== "salute").map((s) => s.id)),
  );

  const toggleSection = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div
        className={revealClass(0, "flex items-center gap-3")}
        style={revealStyle(0)}
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 to-teal-100 dark:from-violet-900/40 dark:to-teal-800/30">
          <Activity className="h-5 w-5 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Monitoraggio</h1>
          <p className="text-sm text-muted-foreground">
            Salute clienti, qualita programmi e proiezioni
          </p>
        </div>
      </div>

      {/* Stacked sections */}
      {SECTIONS.map((section, idx) => {
        const isOpen = !collapsed.has(section.id);
        const SectionContent = SECTION_CONTENT[section.id];
        const Icon = section.icon;

        return (
          <div
            key={section.id}
            className={revealClass(50 + idx * 50, "rounded-xl border bg-white dark:bg-zinc-900 overflow-hidden")}
            style={revealStyle(50 + idx * 50)}
          >
            {/* Section header — clickable to collapse/expand */}
            <button
              type="button"
              className="w-full flex items-center gap-3 p-4 text-left hover:bg-muted/30 transition-colors"
              onClick={() => toggleSection(section.id)}
            >
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${section.iconBg}`}>
                <Icon className={`h-4 w-4 ${section.iconColor}`} />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-sm font-semibold">{section.title}</h2>
                <p className="text-xs text-muted-foreground">{section.subtitle}</p>
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground/50 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
              />
            </button>

            {/* Section content */}
            {isOpen && (
              <div className="border-t px-4 pb-4 pt-4">
                <SectionContent />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
