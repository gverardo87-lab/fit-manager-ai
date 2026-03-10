// src/components/workouts/BuilderSaveBar.tsx
"use client";

/**
 * Barra di salvataggio sticky (fissata in basso) per il builder schede.
 * Mostra stato dirty, issue di salvataggio con navigazione,
 * e bottoni undo/redo/salva.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Clock3, Save, Undo2, Redo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { type SaveIssue, type SaveIssueCategory, SAVE_ISSUE_CATEGORY_LABELS } from "@/lib/builder-utils";

interface BuilderSaveBarProps {
  isDirty: boolean;
  isSaving: boolean;
  lastSavedLabel: string | null;
  saveIssues: SaveIssue[];
  canUndo: boolean;
  canRedo: boolean;
  onSave: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onClearIssues: () => void;
}

export function BuilderSaveBar({
  isDirty,
  isSaving,
  lastSavedLabel,
  saveIssues,
  canUndo,
  canRedo,
  onSave,
  onUndo,
  onRedo,
  onClearIssues,
}: BuilderSaveBarProps) {
  const [issuesExpanded, setIssuesExpanded] = useIssuesExpanded(saveIssues);
  const highlightedNodeRef = useRef<HTMLElement | null>(null);
  const highlightTimeoutRef = useRef<number | null>(null);

  const saveCriticalCount = useMemo(
    () => saveIssues.filter((i) => i.level === "critical").length,
    [saveIssues],
  );
  const saveWarningCount = useMemo(
    () => saveIssues.filter((i) => i.level === "warning").length,
    [saveIssues],
  );
  const visibleIssues = useMemo(
    () => (issuesExpanded ? saveIssues : saveIssues.slice(0, 3)),
    [saveIssues, issuesExpanded],
  );
  const hiddenCount = Math.max(0, saveIssues.length - 3);

  const categoryCounts = useMemo(() => {
    const counts: Partial<Record<SaveIssueCategory, number>> = {};
    for (const issue of saveIssues) {
      counts[issue.category] = (counts[issue.category] ?? 0) + 1;
    }
    return (Object.entries(counts) as Array<[SaveIssueCategory, number]>).sort((a, b) => b[1] - a[1]);
  }, [saveIssues]);

  const issueHasTarget = useCallback((issue: SaveIssue) => (
    issue.sessionId != null || issue.sessionNumber != null || issue.blockId != null || issue.exerciseRowId != null
  ), []);

  const jumpToIssue = useCallback((issue: SaveIssue) => {
    const selectors: string[] = [];
    if (issue.exerciseRowId != null) selectors.push(`[data-workout-exercise-id="${issue.exerciseRowId}"]`);
    if (issue.blockId != null) selectors.push(`[data-workout-block-id="${issue.blockId}"]`);
    if (issue.sessionId != null) selectors.push(`[data-workout-session-id="${issue.sessionId}"]`);
    if (issue.sessionNumber != null) selectors.push(`[data-workout-session-number="${issue.sessionNumber}"]`);

    let target: HTMLElement | null = null;
    for (const selector of selectors) {
      const found = document.querySelector(selector);
      if (found instanceof HTMLElement) { target = found; break; }
    }
    if (!target) return;

    highlightedNodeRef.current?.classList.remove("ring-2", "ring-primary", "ring-offset-2", "ring-offset-background");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("ring-2", "ring-primary", "ring-offset-2", "ring-offset-background");
    highlightedNodeRef.current = target;

    if (highlightTimeoutRef.current) window.clearTimeout(highlightTimeoutRef.current);
    highlightTimeoutRef.current = window.setTimeout(() => {
      target.classList.remove("ring-2", "ring-primary", "ring-offset-2", "ring-offset-background");
    }, 1800);
  }, []);

  const firstNavigable = useMemo(() => saveIssues.find(issueHasTarget), [saveIssues, issueHasTarget]);

  if (!isDirty && saveIssues.length === 0) return null;

  return (
    <div className="fixed bottom-3 left-1/2 z-40 w-[calc(100%-1.5rem)] max-w-2xl -translate-x-1/2" data-print-hide>
      <div className="rounded-xl border bg-background/95 px-3 py-2 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex items-center gap-2">
          <Clock3 className="h-4 w-4 text-primary shrink-0" />
          <div className="min-w-0 flex-1">
            {isDirty ? (
              <>
                <p className="text-sm font-medium">Modifiche non salvate</p>
                <p className="text-[11px] text-muted-foreground truncate">
                  Ctrl+S / Cmd+S per salvare
                  {lastSavedLabel ? ` • Ultimo salvataggio alle ${lastSavedLabel}` : ""}
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-medium">Salvataggio completato con avvisi</p>
                <p className="text-[11px] text-muted-foreground truncate">
                  Clicca un avviso per andare direttamente al punto da rivedere
                </p>
              </>
            )}
          </div>
          {isDirty ? (
            <div className="flex items-center gap-1">
              <Button variant="outline" size="icon" className="h-8 w-8" onClick={onUndo} disabled={!canUndo} title="Annulla">
                <Undo2 className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" className="h-8 w-8" onClick={onRedo} disabled={!canRedo} title="Ripeti">
                <Redo2 className="h-4 w-4" />
              </Button>
              <Button onClick={onSave} disabled={isSaving} className="h-8">
                <Save className="mr-1.5 h-4 w-4" />
                {isSaving ? "Salvataggio..." : "Salva"}
              </Button>
            </div>
          ) : (
            <Button variant="ghost" size="sm" className="h-8" onClick={onClearIssues}>Chiudi</Button>
          )}
        </div>
        {saveIssues.length > 0 && (
          <div className={`mt-2 rounded-md border px-2 py-1.5 ${
            saveCriticalCount > 0
              ? "border-red-300 bg-red-50/80 dark:border-red-900 dark:bg-red-950/30"
              : "border-amber-300 bg-amber-50/80 dark:border-amber-900 dark:bg-amber-950/30"
          }`}>
            <p className={`text-[11px] font-medium ${
              saveCriticalCount > 0 ? "text-red-700 dark:text-red-300" : "text-amber-700 dark:text-amber-300"
            }`}>
              {saveCriticalCount > 0
                ? `Salvataggio bloccato: ${saveCriticalCount} errore critico.`
                : `Salvataggio assistito: ${saveWarningCount} avviso/i non bloccante/i.`}
            </p>
            {categoryCounts.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {categoryCounts.map(([category, count]) => (
                  <span key={category} className="inline-flex items-center rounded border border-current/20 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    {SAVE_ISSUE_CATEGORY_LABELS[category]}: {count}
                  </span>
                ))}
              </div>
            )}
            <ul className="mt-1 space-y-0.5">
              {visibleIssues.map((issue, idx) => (
                <li key={`${issue.level}-${idx}`} className="text-[10px] text-muted-foreground">
                  {issueHasTarget(issue) ? (
                    <button type="button" onClick={() => jumpToIssue(issue)} className="text-left hover:text-foreground hover:underline">
                      • {issue.message}
                    </button>
                  ) : (
                    <>• {issue.message}</>
                  )}
                </li>
              ))}
              {!issuesExpanded && hiddenCount > 0 && (
                <li className="text-[10px] text-muted-foreground">• +{hiddenCount} altri avvisi</li>
              )}
            </ul>
            {saveIssues.length > 3 && (
              <button type="button" onClick={() => setIssuesExpanded((prev) => !prev)} className="mt-1 text-[10px] font-medium text-primary hover:underline">
                {issuesExpanded ? "Mostra meno avvisi" : `Mostra tutti gli avvisi (${saveIssues.length})`}
              </button>
            )}
            {firstNavigable && (
              <button type="button" onClick={() => jumpToIssue(firstNavigable)} className="mt-1 block text-[10px] font-medium text-primary hover:underline">
                Vai al primo punto da rivedere
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Hook locale per gestire expanded con auto-reset ──

function useIssuesExpanded(saveIssues: SaveIssue[]): [boolean, React.Dispatch<React.SetStateAction<boolean>>] {
  const [expanded, setExpanded] = useState(false);
  const criticalCount = saveIssues.filter((i) => i.level === "critical").length;
  const prevCriticalRef = useRef(criticalCount);

  useEffect(() => {
    // Auto-expand only on transition from 0 to >0
    if (criticalCount > 0 && prevCriticalRef.current === 0) {
      const timer = setTimeout(() => setExpanded(true), 0);
      prevCriticalRef.current = criticalCount;
      return () => clearTimeout(timer);
    }
    prevCriticalRef.current = criticalCount;
  }, [criticalCount]);

  return [expanded, setExpanded];
}
