// src/components/workouts/BuilderHeader.tsx
"use client";

/**
 * Header del builder schede: nome editabile inline, selettori cliente/obiettivo/livello,
 * undo/redo, export, salva. Include i banner di ritorno al contesto di provenienza.
 */

import { useState, useCallback } from "react";
import { ArrowLeft, Pencil, Check, X, Undo2, Redo2, Save, FlaskConical } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ExportButtons } from "@/components/workouts/ExportButtons";
import { OBIETTIVO_LABELS, LIVELLO_LABELS } from "@/lib/builder-utils";
import type { SafetyExportData } from "@/lib/export-workout-pdf";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import { OBIETTIVI_SCHEDA, LIVELLI_SCHEDA, type WorkoutPlan } from "@/types/api";

interface BuilderHeaderProps {
  plan: WorkoutPlan;
  clients: { id: number; nome: string; cognome: string }[];
  clientNome?: string;
  totalVolume: number | null;
  isDirty: boolean;
  isSaving: boolean;
  lastSavedLabel: string | null;
  canUndo: boolean;
  canRedo: boolean;
  sessions: SessionCardData[];
  safetyExportData?: SafetyExportData;
  exportLogoDataUrl: string | null;
  fromParam: string | null;
  onUndo: () => void;
  onRedo: () => void;
  onSave: () => void;
  onGoBack: () => void;
  onNavigate: (href: string) => void;
  onUpdatePlan: (updates: Record<string, unknown>) => void;
  onLogoChange: (value: string | null) => void;
  showAdvanced: boolean;
  onToggleAdvanced: () => void;
  hasSessions: boolean;
}

export function BuilderHeader({
  plan, clients, clientNome, totalVolume,
  isDirty, isSaving, lastSavedLabel, canUndo, canRedo,
  sessions, safetyExportData, exportLogoDataUrl, fromParam,
  onUndo, onRedo, onSave, onGoBack, onNavigate, onUpdatePlan, onLogoChange,
  showAdvanced, onToggleAdvanced, hasSessions,
}: BuilderHeaderProps) {
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = useCallback((field: string, value: string) => {
    setEditingField(field);
    setEditValue(value);
  }, []);

  const saveEdit = useCallback(() => {
    if (!editingField) return;
    const v = editValue.trim();
    if (v && v !== String((plan as unknown as Record<string, unknown>)[editingField] ?? "")) {
      onUpdatePlan({ [editingField]: v });
    }
    setEditingField(null);
  }, [plan, editingField, editValue, onUpdatePlan]);

  const cancelEdit = useCallback(() => setEditingField(null), []);

  const returnClientId = fromParam?.startsWith("clienti-") ? fromParam.slice(8) : null;
  const returnToAllenamenti = fromParam === "allenamenti";
  const returnToMonitoraggio = fromParam === "monitoraggio" || fromParam?.startsWith("monitoraggio-");
  const returnMonitoraggioClientId = fromParam?.startsWith("monitoraggio-") ? fromParam.slice(14) : null;

  return (
    <>
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" data-print-hide>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => onGoBack()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            {editingField === "nome" ? (
              <div className="flex items-center gap-1">
                <Input value={editValue} onChange={(e) => setEditValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && saveEdit()} className="h-8 text-lg font-bold" autoFocus />
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={saveEdit}><Check className="h-4 w-4" /></Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={cancelEdit}><X className="h-4 w-4" /></Button>
              </div>
            ) : (
              <button onClick={() => startEdit("nome", plan.nome)} className="flex items-center gap-2 text-xl font-extrabold tracking-tight hover:text-primary transition-colors group/name">
                {plan.nome}
                <Pencil className="h-3.5 w-3.5 text-muted-foreground/40 group-hover/name:text-muted-foreground/70 transition-opacity" />
              </button>
            )}
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Select value={plan.id_cliente ? String(plan.id_cliente) : "__none__"} onValueChange={(v) => onUpdatePlan({ id_cliente: v === "__none__" ? null : Number(v) })}>
                <SelectTrigger size="sm" className="w-[180px] text-xs"><SelectValue placeholder="Assegna cliente" /></SelectTrigger>
                <SelectContent position="popper" sideOffset={4}>
                  <SelectItem value="__none__">Nessun cliente</SelectItem>
                  {clients.map((c) => (<SelectItem key={c.id} value={String(c.id)}>{c.nome} {c.cognome}</SelectItem>))}
                </SelectContent>
              </Select>
              {plan.id_cliente && clientNome && (
                <button onClick={() => onNavigate(`/clienti/${plan.id_cliente}`)} className="text-xs text-primary hover:underline">Vai al profilo</button>
              )}
              <Select value={plan.obiettivo} onValueChange={(v) => onUpdatePlan({ obiettivo: v })}>
                <SelectTrigger className="h-6 w-auto text-xs border-0 bg-transparent p-0 font-medium">
                  <Badge variant="outline" className="text-xs cursor-pointer">{OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}</Badge>
                </SelectTrigger>
                <SelectContent>{OBIETTIVI_SCHEDA.map((o) => (<SelectItem key={o} value={o}>{OBIETTIVO_LABELS[o]}</SelectItem>))}</SelectContent>
              </Select>
              <Select value={plan.livello} onValueChange={(v) => onUpdatePlan({ livello: v })}>
                <SelectTrigger className="h-6 w-auto text-xs border-0 bg-transparent p-0 font-medium">
                  <Badge variant="outline" className="text-xs cursor-pointer">{LIVELLO_LABELS[plan.livello] ?? plan.livello}</Badge>
                </SelectTrigger>
                <SelectContent>{LIVELLI_SCHEDA.map((l) => (<SelectItem key={l} value={l}>{LIVELLO_LABELS[l]}</SelectItem>))}</SelectContent>
              </Select>
              {totalVolume != null && (
                <Badge variant="outline" className="text-xs font-semibold tabular-nums tracking-tight">Vol. totale: {totalVolume.toLocaleString("it-IT")} kg</Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isDirty && lastSavedLabel && <span className="hidden sm:inline text-[11px] text-muted-foreground/60 font-medium">Salvata alle {lastSavedLabel}</span>}
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={onUndo} disabled={!canUndo} title="Annulla (Ctrl/Cmd+Z)"><Undo2 className="h-4 w-4" /></Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={onRedo} disabled={!canRedo} title="Ripeti (Ctrl/Cmd+Shift+Z)"><Redo2 className="h-4 w-4" /></Button>
          {hasSessions && (
            <Button variant={showAdvanced ? "default" : "outline"} size="icon" className="h-8 w-8" onClick={onToggleAdvanced} title={showAdvanced ? "Nascondi analisi avanzata" : "Mostra analisi avanzata"}>
              <FlaskConical className="h-4 w-4" />
            </Button>
          )}
          <ExportButtons nome={plan.nome} obiettivo={plan.obiettivo} livello={plan.livello} clientNome={clientNome} durata_settimane={plan.durata_settimane} sessioni_per_settimana={plan.sessioni_per_settimana} sessioni={sessions} safety={safetyExportData} logoDataUrl={exportLogoDataUrl} onLogoChange={onLogoChange} />
          {isDirty && (
            <Button onClick={onSave} disabled={isSaving}>
              <Save className="mr-1.5 h-4 w-4" />{isSaving ? "Salvataggio..." : "Salva"}
            </Button>
          )}
        </div>
      </div>

      {/* Return banners */}
      {returnClientId && (
        <div className="rounded-lg border border-primary/15 bg-primary/[0.03] px-4 py-2 flex items-center gap-2" data-print-hide>
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <button onClick={() => onNavigate(`/clienti/${returnClientId}?tab=schede`)} className="text-sm text-primary hover:underline">Torna al profilo cliente</button>
        </div>
      )}
      {returnToAllenamenti && (
        <div className="rounded-lg border border-primary/15 bg-primary/[0.03] px-4 py-2 flex items-center gap-2" data-print-hide>
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <button onClick={() => onNavigate("/allenamenti")} className="text-sm text-primary hover:underline">Torna agli allenamenti</button>
        </div>
      )}
      {returnToMonitoraggio && (
        <div className="rounded-lg border border-primary/15 bg-primary/[0.03] px-4 py-2 flex items-center gap-2" data-print-hide>
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <button onClick={() => onNavigate(returnMonitoraggioClientId ? `/monitoraggio/${returnMonitoraggioClientId}` : "/monitoraggio")} className="text-sm text-primary hover:underline">Torna al monitoraggio</button>
        </div>
      )}
    </>
  );
}
