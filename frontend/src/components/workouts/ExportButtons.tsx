// src/components/workouts/ExportButtons.tsx
"use client";

/**
 * Bottoni export: Scarica Excel + Stampa/PDF.
 *
 * Raccoglie gli id_esercizio dalle sessioni per pre-fetch immagini
 * e li passa a exportWorkoutExcel insieme ai dati scheda.
 */

import { useMemo, useState } from "react";
import { Download, Printer, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { exportWorkoutExcel } from "@/lib/export-workout";
import type { SessionCardData } from "./SessionCard";

interface SafetyExportData {
  clientNome: string;
  conditionNames: string[];
  rows: { condizione: string; severita: string; esercizi: string[] }[];
}

interface ExportButtonsProps {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  durata_settimane?: number;
  sessioni_per_settimana?: number;
  sessioni: SessionCardData[];
  safety?: SafetyExportData;
}

export function ExportButtons({ nome, obiettivo, livello, clientNome, durata_settimane, sessioni_per_settimana, sessioni, safety }: ExportButtonsProps) {
  const [exporting, setExporting] = useState(false);

  // Raccogli tutti gli id_esercizio unici per pre-fetch immagini
  const exerciseIds = useMemo(() => {
    const ids = new Set<number>();
    for (const s of sessioni) {
      for (const ex of s.esercizi) {
        ids.add(ex.id_esercizio);
      }
    }
    return [...ids];
  }, [sessioni]);

  const handleExcel = async () => {
    setExporting(true);
    try {
      await exportWorkoutExcel({ nome, obiettivo, livello, clientNome, durata_settimane, sessioni_per_settimana, sessioni, safety, exerciseIds });
    } finally {
      setExporting(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="flex gap-2" data-print-hide>
      <Button variant="outline" size="sm" onClick={handleExcel} disabled={exporting}>
        {exporting ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Download className="mr-1.5 h-4 w-4" />
        )}
        Excel
      </Button>
      <Button variant="outline" size="sm" onClick={handlePrint}>
        <Printer className="mr-1.5 h-4 w-4" />
        Stampa
      </Button>
    </div>
  );
}
