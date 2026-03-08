// src/app/(dashboard)/monitoraggio/page.tsx
"use client";

/**
 * Panoramica Monitoraggio — Pagina unificata con 3 tab.
 *
 * Tab 1: Salute Clienti (ex MyPortal — readiness clinica)
 * Tab 2: Qualita Programmi (ex MyTrainer — analisi metodologica)
 * Tab 3: Proiezioni (worklist proiezioni obiettivi aggregate)
 *
 * Raccoglie in un unico punto le 3 dimensioni di monitoraggio.
 */

import { useState } from "react";
import {
  Activity,
  HeartPulse,
  Rocket,
  Target,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePageReveal } from "@/lib/page-reveal";

import { SaluteClientiTab } from "@/components/monitoraggio/SaluteClientiTab";
import { QualitaProgrammiTab } from "@/components/monitoraggio/QualitaProgrammiTab";
import { ProiezioniTab } from "@/components/monitoraggio/ProiezioniTab";

export default function MonitoraggioPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const [activeTab, setActiveTab] = useState("salute");

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div
        className={revealClass(0, "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between")}
        style={revealStyle(0)}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 to-teal-100 dark:from-violet-900/40 dark:to-teal-800/30">
            <Activity className="h-5 w-5 text-violet-600 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Monitoraggio</h1>
            <p className="text-sm text-muted-foreground">
              Panoramica salute clienti, qualita programmi e proiezioni
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className={revealClass(50)} style={revealStyle(50)}>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full overflow-x-auto">
            <TabsTrigger value="salute" className="gap-1.5">
              <HeartPulse className="h-4 w-4" />
              <span className="hidden sm:inline">Salute Clienti</span>
              <span className="sm:hidden">Salute</span>
            </TabsTrigger>
            <TabsTrigger value="programmi" className="gap-1.5">
              <Target className="h-4 w-4" />
              <span className="hidden sm:inline">Qualita Programmi</span>
              <span className="sm:hidden">Programmi</span>
            </TabsTrigger>
            <TabsTrigger value="proiezioni" className="gap-1.5">
              <Rocket className="h-4 w-4" />
              <span className="hidden sm:inline">Proiezioni</span>
              <span className="sm:hidden">Proiezioni</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="salute" className="mt-4">
            <SaluteClientiTab />
          </TabsContent>
          <TabsContent value="programmi" className="mt-4">
            <QualitaProgrammiTab />
          </TabsContent>
          <TabsContent value="proiezioni" className="mt-4">
            <ProiezioniTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
