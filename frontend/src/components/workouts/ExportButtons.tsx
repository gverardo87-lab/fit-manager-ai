// src/components/workouts/ExportButtons.tsx
"use client";

/**
 * Bottoni export: scarica clinico + anteprima + gestione logo cliente.
 *
 * Clinico: scarica file HTML locale (stile ex-Excel, con fotografie esercizi).
 * Anteprima: usa la WorkoutPreview stampabile attuale.
 * Il logo viene salvato dal parent e riutilizzato in preview/export.
 */

import { useRef, useState, type ChangeEvent } from "react";
import { Download, ImagePlus, Loader2, Printer, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { downloadWorkoutClinicalHtml, type SafetyExportData } from "@/lib/export-workout-pdf";
import type { SessionCardData } from "./SessionCard";

const MAX_LOGO_SIZE_MB = 2;
const MAX_LOGO_SIZE_BYTES = MAX_LOGO_SIZE_MB * 1024 * 1024;

interface ExportButtonsProps {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  durata_settimane?: number;
  sessioni_per_settimana?: number;
  sessioni: SessionCardData[];
  safety?: SafetyExportData;
  logoDataUrl?: string | null;
  onLogoChange?: (value: string | null) => void;
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export function ExportButtons({
  nome,
  obiettivo,
  livello,
  clientNome,
  durata_settimane,
  sessioni_per_settimana,
  sessioni,
  safety,
  logoDataUrl,
  onLogoChange,
}: ExportButtonsProps) {
  const [exportingClinical, setExportingClinical] = useState(false);
  const [exportingPreview, setExportingPreview] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClinicalPdf = async () => {
    setExportingClinical(true);
    try {
      await downloadWorkoutClinicalHtml({
        nome,
        obiettivo,
        livello,
        clientNome,
        durata_settimane,
        sessioni_per_settimana,
        sessioni,
        safety,
        logoDataUrl,
      });
    } finally {
      setExportingClinical(false);
    }
  };

  const handlePreviewPdf = () => {
    setExportingPreview(true);
    try {
      window.print();
    } finally {
      setExportingPreview(false);
    }
  };

  const handlePickLogo = () => {
    inputRef.current?.click();
  };

  const handleLogoSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Seleziona un file immagine valido (PNG, JPG, WEBP, SVG).");
      return;
    }
    if (file.size > MAX_LOGO_SIZE_BYTES) {
      toast.error(`Logo troppo pesante (max ${MAX_LOGO_SIZE_MB} MB).`);
      return;
    }

    setUploadingLogo(true);
    try {
      const dataUrl = await fileToDataUrl(file);
      onLogoChange?.(dataUrl);
      toast.success("Logo aggiornato per l'export PDF.");
    } catch {
      toast.error("Impossibile leggere il file logo.");
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleRemoveLogo = () => {
    onLogoChange?.(null);
    toast.success("Logo rimosso.");
  };

  return (
    <div className="flex gap-2" data-print-hide>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/svg+xml"
        className="hidden"
        onChange={handleLogoSelected}
      />

      <Button variant="outline" size="sm" onClick={handleClinicalPdf} disabled={exportingClinical}>
        {exportingClinical ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Download className="mr-1.5 h-4 w-4" />
        )}
        Scarica Clinico
      </Button>

      <Button variant="outline" size="sm" onClick={handlePreviewPdf} disabled={exportingPreview}>
        {exportingPreview ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Printer className="mr-1.5 h-4 w-4" />
        )}
        Anteprima
      </Button>

      <Button variant="outline" size="sm" onClick={handlePickLogo} disabled={uploadingLogo}>
        {uploadingLogo ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <ImagePlus className="mr-1.5 h-4 w-4" />
        )}
        {logoDataUrl ? "Cambia logo" : "Logo"}
      </Button>

      {logoDataUrl && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={handleRemoveLogo}
          title="Rimuovi logo"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
