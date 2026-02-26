// src/components/workouts/ExportButtons.tsx
"use client";

/**
 * Bottoni export: Scarica Excel + Stampa/PDF.
 */

import { Download, Printer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { exportWorkoutExcel } from "@/lib/export-workout";
import type { SessionCardData } from "./SessionCard";

interface ExportButtonsProps {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  sessioni: SessionCardData[];
  aiCommentary?: string | null;
}

export function ExportButtons({ nome, obiettivo, livello, clientNome, sessioni, aiCommentary }: ExportButtonsProps) {
  const handleExcel = async () => {
    await exportWorkoutExcel({ nome, obiettivo, livello, clientNome, sessioni, aiCommentary });
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="flex gap-2" data-print-hide>
      <Button variant="outline" size="sm" onClick={handleExcel}>
        <Download className="mr-1.5 h-4 w-4" />
        Excel
      </Button>
      <Button variant="outline" size="sm" onClick={handlePrint}>
        <Printer className="mr-1.5 h-4 w-4" />
        Stampa
      </Button>
    </div>
  );
}
