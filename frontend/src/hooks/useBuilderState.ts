// src/hooks/useBuilderState.ts
/**
 * State management core per il builder schede allenamento.
 * Gestisce: sessions, dirty tracking, undo/redo history con coalesce,
 * server sync, draft recovery, save pipeline, keyboard shortcuts.
 */

import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { toast } from "sonner";
import { useUnsavedChanges, loadDraft, clearDraft } from "@/hooks/useUnsavedChanges";
import { type SessionCardData, parseAvgReps } from "@/components/workouts/SessionCard";
import { serverBlockToCardData } from "@/components/workouts/BlockCard";
import { getStoredTrainer } from "@/lib/auth";
import { consumeSmartPlanPackage } from "@/lib/smart-plan-package-cache";
import { getSectionForCategory } from "@/lib/workout-templates";
import {
  type SaveIssue,
  HISTORY_LIMIT,
  COALESCE_DELAY_MS,
  WORKOUT_LOGO_STORAGE_PREFIX,
  cloneSessionsSnapshot,
  isEditableTarget,
  prepareSessionsInputForSave,
} from "@/lib/builder-utils";
import type { WorkoutPlan, WorkoutSessionInput, Exercise, TSPlanPackage } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface UseBuilderStateOptions {
  id: number;
  plan: WorkoutPlan | undefined;
  exerciseMap: Map<number, Exercise>;
  oneRMByPattern: Record<string, number> | null;
  updateSessionsMutate: (
    vars: { id: number; sessions: WorkoutSessionInput[] },
    opts: { onSuccess: (saved: WorkoutPlan) => void },
  ) => void;
  isSaving: boolean;
}

export interface BuilderState {
  sessions: SessionCardData[];
  isDirty: boolean;
  isDirtyRef: React.MutableRefObject<boolean>;
  canUndo: boolean;
  canRedo: boolean;
  saveIssues: SaveIssue[];
  lastSavedLabel: string | null;
  totalVolume: number | null;
  smartPlanPackage: TSPlanPackage | null;
  exportLogoDataUrl: string | null;
  // Core mutators
  applySessionsChange: (
    updater: (prev: SessionCardData[]) => SessionCardData[],
    options?: { trackHistory?: boolean; markDirty?: boolean; coalesceKey?: string },
  ) => void;
  sessionsRef: React.MutableRefObject<SessionCardData[]>;
  handleUndo: () => void;
  handleRedo: () => void;
  handleSave: () => void;
  handleLogoChange: (value: string | null) => void;
}

// ════════════════════════════════════════════════════════════
// HOOK
// ════════════════════════════════════════════════════════════

export function useBuilderState({
  id, plan, exerciseMap, oneRMByPattern, updateSessionsMutate, isSaving,
}: UseBuilderStateOptions): BuilderState {
  // ── Core state ──
  const [sessions, setSessions] = useState<SessionCardData[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [smartPlanPackage, setSmartPlanPackage] = useState<TSPlanPackage | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [saveIssues, setSaveIssues] = useState<SaveIssue[]>([]);
  const [historyPast, setHistoryPast] = useState<SessionCardData[][]>([]);
  const [historyFuture, setHistoryFuture] = useState<SessionCardData[][]>([]);

  // ── Refs ──
  const sessionsRef = useRef<SessionCardData[]>([]);
  const isDirtyRef = useRef(false);
  const coalesceTimerRef = useRef<number | null>(null);
  const coalesceKeyRef = useRef<string | null>(null);
  const coalesceBaseRef = useRef<SessionCardData[] | null>(null);
  const smartPlanPackageHydratedRef = useRef<number | null>(null);
  sessionsRef.current = sessions;
  isDirtyRef.current = isDirty;

  // ── Draft protection ──
  const draftKey = isNaN(id) ? undefined : `scheda-builder-${id}`;
  useUnsavedChanges({ dirty: isDirty, draftKey, draftData: sessions });

  // ── Export logo ──
  const logoStorageKey = useMemo(() => {
    const trainer = getStoredTrainer();
    return `${WORKOUT_LOGO_STORAGE_PREFIX}.${trainer?.id ?? "anonymous"}`;
  }, []);
  const [exportLogoDataUrl, setExportLogoDataUrl] = useState<string | null>(null);

  useEffect(() => {
    setExportLogoDataUrl(window.localStorage.getItem(logoStorageKey));
  }, [logoStorageKey]);

  const handleLogoChange = useCallback((value: string | null) => {
    setExportLogoDataUrl(value);
    if (value) window.localStorage.setItem(logoStorageKey, value);
    else window.localStorage.removeItem(logoStorageKey);
  }, [logoStorageKey]);

  // ── History & coalesce ──
  const clearCoalesceTimer = useCallback(() => {
    if (coalesceTimerRef.current) {
      window.clearTimeout(coalesceTimerRef.current);
      coalesceTimerRef.current = null;
    }
  }, []);

  const pushHistorySnapshot = useCallback((snapshot: SessionCardData[]) => {
    setHistoryPast((past) => [...past.slice(-(HISTORY_LIMIT - 1)), cloneSessionsSnapshot(snapshot)]);
    setHistoryFuture([]);
  }, []);

  const flushCoalescedHistory = useCallback(() => {
    clearCoalesceTimer();
    if (!coalesceBaseRef.current) return;
    pushHistorySnapshot(coalesceBaseRef.current);
    coalesceBaseRef.current = null;
    coalesceKeyRef.current = null;
  }, [clearCoalesceTimer, pushHistorySnapshot]);

  const scheduleCoalescedFlush = useCallback(() => {
    clearCoalesceTimer();
    coalesceTimerRef.current = window.setTimeout(() => flushCoalescedHistory(), COALESCE_DELAY_MS);
  }, [clearCoalesceTimer, flushCoalescedHistory]);

  const applySessionsChange = useCallback(
    (updater: (prev: SessionCardData[]) => SessionCardData[], options?: { trackHistory?: boolean; markDirty?: boolean; coalesceKey?: string }) => {
      const prev = sessionsRef.current;
      const next = updater(prev);
      if (next === prev) return;
      if (options?.trackHistory !== false) {
        const coalesceKey = options?.coalesceKey;
        if (coalesceKey) {
          if (coalesceKeyRef.current && coalesceKeyRef.current !== coalesceKey) flushCoalescedHistory();
          if (!coalesceBaseRef.current) coalesceBaseRef.current = cloneSessionsSnapshot(prev);
          coalesceKeyRef.current = coalesceKey;
          scheduleCoalescedFlush();
        } else {
          flushCoalescedHistory();
          pushHistorySnapshot(prev);
        }
      }
      sessionsRef.current = next;
      setSessions(next);
      if (options?.markDirty !== false) setIsDirty(true);
    },
    [flushCoalescedHistory, pushHistorySnapshot, scheduleCoalescedFlush],
  );

  // ── Undo / Redo ──
  const handleUndo = useCallback(() => {
    flushCoalescedHistory();
    const current = sessionsRef.current;
    setHistoryPast((past) => {
      if (past.length === 0) return past;
      const previous = cloneSessionsSnapshot(past[past.length - 1]);
      setHistoryFuture((future) => [cloneSessionsSnapshot(current), ...future].slice(0, HISTORY_LIMIT));
      sessionsRef.current = previous;
      setSessions(previous);
      setIsDirty(true);
      return past.slice(0, -1);
    });
  }, [flushCoalescedHistory]);

  const handleRedo = useCallback(() => {
    flushCoalescedHistory();
    const current = sessionsRef.current;
    setHistoryFuture((future) => {
      if (future.length === 0) return future;
      const next = cloneSessionsSnapshot(future[0]);
      setHistoryPast((past) => [...past.slice(-(HISTORY_LIMIT - 1)), cloneSessionsSnapshot(current)]);
      sessionsRef.current = next;
      setSessions(next);
      setIsDirty(true);
      return future.slice(1);
    });
  }, [flushCoalescedHistory]);

  // ── Server sync (protegge modifiche non salvate) ──
  useEffect(() => {
    if (plan && !isDirtyRef.current) {
      setSessions(plan.sessioni.map((s) => ({
        id: s.id, numero_sessione: s.numero_sessione, nome_sessione: s.nome_sessione,
        focus_muscolare: s.focus_muscolare, durata_minuti: s.durata_minuti, note: s.note,
        esercizi: [...s.esercizi], blocchi: (s.blocchi ?? []).map(serverBlockToCardData),
      })));
      clearCoalesceTimer();
      coalesceBaseRef.current = null;
      coalesceKeyRef.current = null;
      setHistoryPast([]);
      setHistoryFuture([]);
      const serverTs = plan.updated_at ?? plan.created_at;
      if (serverTs) {
        const parsed = new Date(serverTs);
        if (!Number.isNaN(parsed.getTime())) setLastSavedAt(parsed);
      }
    }
  }, [plan, clearCoalesceTimer]);

  // ── Smart plan package handoff ──
  useEffect(() => {
    if (!plan) return;
    if (smartPlanPackageHydratedRef.current === plan.id) return;
    smartPlanPackageHydratedRef.current = plan.id;
    setSmartPlanPackage(consumeSmartPlanPackage(plan.id));
  }, [plan]);

  // ── Draft recovery ──
  const draftRecoveredRef = useRef(false);
  useEffect(() => {
    if (plan && !isDirtyRef.current && !draftRecoveredRef.current && draftKey) {
      draftRecoveredRef.current = true;
      const saved = loadDraft<SessionCardData[]>(draftKey);
      if (saved && saved.ts > 0) {
        const ageMs = Date.now() - saved.ts;
        if (ageMs < 24 * 60 * 60 * 1000) {
          if (window.confirm("Sono state trovate modifiche non salvate. Vuoi recuperarle?")) {
            setSessions(saved.data);
            clearCoalesceTimer();
            coalesceBaseRef.current = null;
            coalesceKeyRef.current = null;
            setHistoryPast([]);
            setHistoryFuture([]);
            setIsDirty(true);
            return;
          }
        }
        clearDraft(draftKey);
      }
    }
  }, [plan, draftKey, clearCoalesceTimer]);

  // ── Reset save issues on new edit ──
  useEffect(() => {
    if (!isDirtyRef.current || saveIssues.length === 0) return;
    setSaveIssues([]);
  }, [sessions, saveIssues.length]);

  // ── Clear smart plan on dirty ──
  useEffect(() => {
    if (!isDirty || !smartPlanPackage) return;
    setSmartPlanPackage(null);
  }, [isDirty, smartPlanPackage]);

  // ── Cleanup ──
  useEffect(() => () => clearCoalesceTimer(), [clearCoalesceTimer]);

  // ── Save handler ──
  const handleSave = useCallback(() => {
    if (!plan) return;
    flushCoalescedHistory();
    const { sessionsInput, issues, criticalCount, warningCount } = prepareSessionsInputForSave(sessionsRef.current, exerciseMap, oneRMByPattern);
    setSaveIssues(issues);
    if (criticalCount > 0) return;
    updateSessionsMutate(
      { id: plan.id, sessions: sessionsInput },
      {
        onSuccess: (savedPlan) => {
          if (warningCount > 0) {
            const firstWarning = issues.find((i) => i.level === "warning")?.message;
            toast.warning(`Scheda salvata con ${warningCount} avvis${warningCount === 1 ? "o" : "i"}.${firstWarning ? ` ${firstWarning}` : ""}`);
          }
          setIsDirty(false);
          if (draftKey) clearDraft(draftKey);
          const serverTs = savedPlan.updated_at ?? savedPlan.created_at;
          const parsed = serverTs ? new Date(serverTs) : new Date();
          if (!Number.isNaN(parsed.getTime())) setLastSavedAt(parsed);
        },
      },
    );
  }, [plan, exerciseMap, oneRMByPattern, flushCoalescedHistory, updateSessionsMutate, draftKey]);

  // ── Keyboard shortcuts: Ctrl+S, Ctrl+Z, Ctrl+Shift+Z, Ctrl+Y ──
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      const key = event.key.toLowerCase();
      if (key === "s") {
        event.preventDefault();
        if (isDirty && !isSaving) handleSave();
        return;
      }
      if (isEditableTarget(event.target)) return;
      if (key === "z") {
        event.preventDefault();
        if (event.shiftKey) { if (historyFuture.length > 0) handleRedo(); }
        else if (historyPast.length > 0) handleUndo();
      } else if (key === "y") {
        event.preventDefault();
        if (historyFuture.length > 0) handleRedo();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isDirty, isSaving, handleSave, historyPast.length, historyFuture.length, handleUndo, handleRedo]);

  // ── Computed values ──
  const canUndo = historyPast.length > 0;
  const canRedo = historyFuture.length > 0;

  const lastSavedLabel = useMemo(() => {
    if (!lastSavedAt) return null;
    return lastSavedAt.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  }, [lastSavedAt]);

  const totalVolume = useMemo(() => {
    let total = 0;
    for (const session of sessions) {
      for (const ex of session.esercizi) {
        if (getSectionForCategory(ex.esercizio_categoria) !== "principale") continue;
        if (!ex.carico_kg || ex.carico_kg <= 0) continue;
        total += ex.serie * parseAvgReps(ex.ripetizioni) * ex.carico_kg;
      }
    }
    return total > 0 ? Math.round(total) : null;
  }, [sessions]);

  return {
    sessions, isDirty, isDirtyRef, canUndo, canRedo, saveIssues, lastSavedLabel,
    totalVolume, smartPlanPackage, exportLogoDataUrl,
    applySessionsChange, sessionsRef, handleUndo, handleRedo, handleSave, handleLogoChange,
  };
}
