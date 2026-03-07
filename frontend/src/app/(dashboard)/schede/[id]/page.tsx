// src/app/(dashboard)/schede/[id]/page.tsx
"use client";

/**
 * Pagina builder/editor scheda allenamento.
 *
 * Layout split: editor a sinistra, preview live a destra (solo desktop).
 * Sessioni con esercizi ordinabili via drag & drop.
 * Salvataggio via full-replace sessioni.
 */

import { use, useState, useCallback, useEffect, useMemo, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Clock3,
  Plus,
  Pencil,
  Undo2,
  Redo2,
  Check,
  X,
  Shield,
  ShieldAlert,
  AlertTriangle,
  Info as InfoIcon,
  ChevronDown,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { SessionCard, parseAvgReps, type SessionCardData } from "@/components/workouts/SessionCard";
import { createBlockCardData, serverBlockToCardData, type BlockCardData } from "@/components/workouts/BlockCard";
import { ExerciseSelector } from "@/components/workouts/ExerciseSelector";
import { WorkoutPreview } from "@/components/workouts/WorkoutPreview";
import { ExportButtons } from "@/components/workouts/ExportButtons";
import {
  useWorkout,
  useUpdateWorkout,
  useUpdateWorkoutSessions,
} from "@/hooks/useWorkouts";
import { useUnsavedChanges, loadDraft, clearDraft } from "@/hooks/useUnsavedChanges";
import { useClients } from "@/hooks/useClients";
import { useExercises, useExerciseSafetyMap } from "@/hooks/useExercises";
import { useLatestMeasurement } from "@/hooks/useMeasurements";
import { toast } from "sonner";
import { PATTERN_TO_1RM } from "@/lib/derived-metrics";
import { getStoredTrainer } from "@/lib/auth";
import { consumeSmartPlanPackage } from "@/lib/smart-plan-package-cache";
import {
  OBIETTIVI_SCHEDA,
  LIVELLI_SCHEDA,
  type WorkoutExerciseRow,
  type WorkoutSessionInput,
  type Exercise,
  type SafetyConditionDetail,
  type BlockType,
  type TSAnalisiPiano,
  type TSPlanPackage,
} from "@/types/api";
import {
  SECTION_CATEGORIES,
  getSectionForCategory,
  getSmartDefaults,
  type TemplateSection,
} from "@/lib/workout-templates";
import { RiskBodyMap } from "@/components/workouts/RiskBodyMap";
import { SmartAnalysisPanel } from "@/components/workouts/SmartAnalysisPanel";
import { MuscleMapPanel } from "@/components/workouts/MuscleMapPanel";

// ════════════════════════════════════════════════════════════
// LABELS
// ════════════════════════════════════════════════════════════

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza", ipertrofia: "Ipertrofia", resistenza: "Resistenza",
  dimagrimento: "Dimagrimento", generale: "Generale",
};
const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante", intermedio: "Intermedio", avanzato: "Avanzato",
};

const CONDITION_CATEGORY_LABELS: Record<string, string> = {
  orthopedic: "Ortopedico",
  cardiovascular: "Cardiovascolare",
  metabolic: "Metabolico",
  neurological: "Neurologico",
  respiratory: "Respiratorio",
  special: "Speciale",
};

const CATEGORY_ORDER = ["orthopedic", "cardiovascular", "metabolic", "neurological", "respiratory", "special"];
const WORKOUT_LOGO_STORAGE_PREFIX = "fitmanager.workout.logo";

type SaveIssueLevel = "warning" | "critical";
type SaveIssueCategory = "draft" | "normalization" | "safety" | "integrity";

interface SaveIssue {
  level: SaveIssueLevel;
  category: SaveIssueCategory;
  message: string;
  sessionId?: number;
  sessionNumber?: number;
  blockId?: number;
  exerciseRowId?: number;
}

const SAVE_ISSUE_CATEGORY_LABELS: Record<SaveIssueCategory, string> = {
  draft: "Bozza",
  normalization: "Normalizzazione",
  safety: "Sicurezza",
  integrity: "Integrita",
};

const VALID_BLOCK_TYPES: Set<BlockType> = new Set([
  "circuit",
  "superset",
  "tabata",
  "amrap",
  "emom",
  "for_time",
]);
const HIGH_LOAD_WARNING_KG = 150;
const HISTORY_LIMIT = 60;
const COALESCE_DELAY_MS = 700;

const SESSION_COALESCE_FIELDS = new Set<keyof SessionCardData>([
  "nome_sessione",
  "focus_muscolare",
  "durata_minuti",
  "note",
]);
const EXERCISE_COALESCE_FIELDS = new Set<keyof WorkoutExerciseRow>([
  "serie",
  "ripetizioni",
  "tempo_riposo_sec",
  "tempo_esecuzione",
  "carico_kg",
  "note",
]);
const BLOCK_COALESCE_FIELDS = new Set<keyof BlockCardData>([
  "nome",
  "giri",
  "durata_lavoro_sec",
  "durata_riposo_sec",
  "durata_blocco_sec",
  "note",
]);

function cloneSessionsSnapshot(input: SessionCardData[]): SessionCardData[] {
  if (typeof structuredClone === "function") {
    return structuredClone(input);
  }
  return JSON.parse(JSON.stringify(input)) as SessionCardData[];
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return (
    target.isContentEditable ||
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT"
  );
}

function trimOrNull(value: string | null | undefined, maxLength: number): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.slice(0, maxLength);
}

function clampInt(value: number, min: number, max: number, fallback: number): number {
  if (!Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, Math.round(value)));
}

function clampOptionalInt(value: number | null | undefined, min: number, max: number): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  return Math.min(max, Math.max(min, Math.round(value)));
}

function clampOptionalFloat(value: number | null | undefined, min: number, max: number): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  return Math.min(max, Math.max(min, value));
}

function sanitizeExerciseForSave(
  ex: WorkoutExerciseRow,
  ordine: number,
  issues: SaveIssue[],
  contextLabel: string,
  exerciseMap: Map<number, Exercise>,
  oneRMByPattern?: Record<string, number> | null,
  location?: Pick<SaveIssue, "sessionId" | "sessionNumber" | "blockId" | "exerciseRowId">,
): WorkoutSessionInput["esercizi"][number] | null {
  if (!ex.id_esercizio || !exerciseMap.has(ex.id_esercizio)) {
    issues.push({
      level: "warning",
      category: "integrity",
      message: `${contextLabel}: esercizio non valido rimosso dal salvataggio.`,
      ...location,
    });
    return null;
  }

  const serie = clampInt(ex.serie, 1, 10, 3);
  const tempoRiposo = clampInt(ex.tempo_riposo_sec, 0, 300, 90);
  const caricoKg = clampOptionalFloat(ex.carico_kg, 0, 500);
  const ripRaw = (ex.ripetizioni ?? "").trim();
  const ripetizioni = (ripRaw || "8-12").slice(0, 20);

  if (!ripRaw) {
    issues.push({
      level: "warning",
      category: "normalization",
      message: `${contextLabel}: ripetizioni mancanti, applicato default 8-12.`,
      ...location,
    });
  }

  if (caricoKg != null && caricoKg >= HIGH_LOAD_WARNING_KG) {
    issues.push({
      level: "warning",
      category: "safety",
      message: `${contextLabel}: carico elevato (${caricoKg} kg), verifica sicurezza e progressione.`,
      ...location,
    });
  }

  const exData = exerciseMap.get(ex.id_esercizio);
  const pattern = exData?.pattern_movimento;
  if (caricoKg != null && oneRMByPattern && pattern) {
    const oneRM = oneRMByPattern[pattern];
    if (oneRM && oneRM > 0) {
      const percent = Math.round((caricoKg / oneRM) * 100);
      if (percent > 105) {
        issues.push({
          level: "warning",
          category: "safety",
          message: `${contextLabel}: carico ${percent}% 1RM, controlla che sia intenzionale.`,
          ...location,
        });
      }
    }
  }

  return {
    id_esercizio: ex.id_esercizio,
    ordine,
    serie,
    ripetizioni,
    tempo_riposo_sec: tempoRiposo,
    tempo_esecuzione: trimOrNull(ex.tempo_esecuzione, 20),
    carico_kg: caricoKg,
    note: trimOrNull(ex.note, 500),
  };
}

function prepareSessionsInputForSave(
  sessions: SessionCardData[],
  exerciseMap: Map<number, Exercise>,
  oneRMByPattern?: Record<string, number> | null,
): { sessionsInput: WorkoutSessionInput[]; issues: SaveIssue[]; criticalCount: number; warningCount: number } {
  const issues: SaveIssue[] = [];
  if (sessions.length === 0) {
    issues.push({
      level: "critical",
      category: "integrity",
      message: "Serve almeno una sessione per salvare la scheda.",
    });
    return { sessionsInput: [], issues, criticalCount: 1, warningCount: 0 };
  }

  const sessionsInput: WorkoutSessionInput[] = sessions.map((s, si) => {
    const sessionLabel = `Sessione ${si + 1}`;
    const sessionNumber = s.numero_sessione > 0 ? s.numero_sessione : si + 1;

    const nomeSessione = (s.nome_sessione ?? "").trim() || sessionLabel;
    if ((s.nome_sessione ?? "").trim() === "") {
      issues.push({
        level: "warning",
        category: "normalization",
        message: `${sessionLabel}: nome mancante, applicato "${nomeSessione}".`,
        sessionId: s.id,
        sessionNumber,
      });
    }

    const durataMinuti = clampInt(s.durata_minuti, 15, 180, 60);
    if (durataMinuti !== s.durata_minuti) {
      issues.push({
        level: "warning",
        category: "normalization",
        message: `${sessionLabel}: durata fuori range, normalizzata a ${durataMinuti} min.`,
        sessionId: s.id,
        sessionNumber,
      });
    }

    const esercizi = s.esercizi
      .map((ex, idx) =>
        sanitizeExerciseForSave(
          ex,
          idx + 1,
          issues,
          sessionLabel,
          exerciseMap,
          oneRMByPattern,
          { sessionId: s.id, sessionNumber, exerciseRowId: ex.id },
        ),
      )
      .filter((ex): ex is WorkoutSessionInput["esercizi"][number] => ex !== null);

    const blocchi: NonNullable<WorkoutSessionInput["blocchi"]> = [];
    for (const [bi, b] of s.blocchi.entries()) {
      const blockLabel = (b.nome ?? "").trim() || `Blocco ${bi + 1}`;
      const tipoBlocco = VALID_BLOCK_TYPES.has(b.tipo_blocco) ? b.tipo_blocco : "circuit";

      if (tipoBlocco !== b.tipo_blocco) {
        issues.push({
          level: "warning",
          category: "integrity",
          message: `${sessionLabel}: tipo blocco non valido, convertito in "circuit".`,
          sessionId: s.id,
          sessionNumber,
          blockId: b.id,
        });
      }

      const eserciziBlocco = b.esercizi
        .map((ex, ei) =>
          sanitizeExerciseForSave(
            ex,
            ei + 1,
            issues,
            `${sessionLabel} • ${blockLabel}`,
            exerciseMap,
            oneRMByPattern,
            { sessionId: s.id, sessionNumber, blockId: b.id, exerciseRowId: ex.id },
          ),
        )
        .filter((ex): ex is WorkoutSessionInput["esercizi"][number] => ex !== null);

      if (eserciziBlocco.length === 0) {
        issues.push({
          level: "warning",
          category: "draft",
          message: `${sessionLabel}: ${blockLabel} non salvato perche vuoto.`,
          sessionId: s.id,
          sessionNumber,
          blockId: b.id,
        });
        continue;
      }

      blocchi.push({
        tipo_blocco: tipoBlocco,
        ordine: blocchi.length + 1,
        nome: trimOrNull(b.nome, 100),
        giri: clampInt(b.giri, 1, 20, 3),
        durata_lavoro_sec: clampOptionalInt(b.durata_lavoro_sec, 5, 600),
        durata_riposo_sec: clampOptionalInt(b.durata_riposo_sec, 0, 300),
        durata_blocco_sec: clampOptionalInt(b.durata_blocco_sec, 60, 7200),
        note: trimOrNull(b.note, 500),
        esercizi: eserciziBlocco,
      });
    }

    if (esercizi.length === 0 && blocchi.length === 0) {
      issues.push({
        level: "warning",
        category: "draft",
        message: `${sessionLabel}: sessione salvata vuota (bozza parziale).`,
        sessionId: s.id,
        sessionNumber,
      });
    }

    return {
      nome_sessione: nomeSessione,
      focus_muscolare: trimOrNull(s.focus_muscolare, 200),
      durata_minuti: durataMinuti,
      note: trimOrNull(s.note, 500),
      esercizi,
      blocchi,
    };
  });

  const totalSavedExercises = sessionsInput.reduce((sum, session) => {
    const straight = session.esercizi.length;
    const inBlocks = (session.blocchi ?? []).reduce((acc, b) => acc + b.esercizi.length, 0);
    return sum + straight + inBlocks;
  }, 0);
  if (totalSavedExercises === 0) {
    issues.push({
      level: "warning",
      category: "draft",
      message: "Scheda salvata senza esercizi: bozza valida ma incompleta.",
    });
  }

  const criticalCount = issues.filter((i) => i.level === "critical").length;
  const warningCount = issues.filter((i) => i.level === "warning").length;
  return { sessionsInput, issues, criticalCount, warningCount };
}

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function SchedaDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: idStr } = use(params);
  const fromParam = useSearchParams().get("from");
  const returnClientId = fromParam?.startsWith("clienti-") ? fromParam.slice(8) : null;
  const returnToAllenamenti = fromParam === "allenamenti";
  const id = parseInt(idStr, 10);
  const router = useRouter();

  const { data: plan, isLoading, isError } = useWorkout(isNaN(id) ? null : id);
  const updateWorkout = useUpdateWorkout();
  const updateSessions = useUpdateWorkoutSessions();
  const { data: clientsData } = useClients();
  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  // Exercise map per preview
  const exerciseData = useExercises();
  const allExercises = useMemo(() => exerciseData.data?.items ?? [], [exerciseData.data]);
  const exerciseMap = useMemo(
    () => new Map(allExercises.map((e) => [e.id, e])),
    [allExercises],
  );

  // Safety map: anamnesi × condizioni mediche (lazy, solo con cliente assegnato)
  const { data: safetyMap } = useExerciseSafetyMap(plan?.id_cliente ?? null);
  const safetyEntries = safetyMap?.entries;

  // 1RM: ultima misurazione forza cliente (lazy, solo con cliente assegnato)
  const { data: latestMeasurement } = useLatestMeasurement(plan?.id_cliente ?? null);
  const oneRMByPattern = useMemo(() => {
    if (!latestMeasurement) return null;
    const map: Record<string, number> = {};
    for (const [pattern, metricId] of Object.entries(PATTERN_TO_1RM)) {
      const val = latestMeasurement.valori.find(v => v.id_metrica === metricId);
      if (val) map[pattern] = val.valore;
    }
    return Object.keys(map).length > 0 ? map : null;
  }, [latestMeasurement]);

  // Safety overview panel
  const [safetyExpanded, setSafetyExpanded] = useState(false);

  // Local state per editing
  const [sessions, setSessions] = useState<SessionCardData[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [smartPlanPackage, setSmartPlanPackage] = useState<TSPlanPackage | null>(null);
  const [smartBackendAnalysis, setSmartBackendAnalysis] = useState<TSAnalisiPiano | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [saveIssues, setSaveIssues] = useState<SaveIssue[]>([]);
  const [saveIssuesExpanded, setSaveIssuesExpanded] = useState(false);
  const [historyPast, setHistoryPast] = useState<SessionCardData[][]>([]);
  const [historyFuture, setHistoryFuture] = useState<SessionCardData[][]>([]);
  const highlightedNodeRef = useRef<HTMLElement | null>(null);
  const highlightTimeoutRef = useRef<number | null>(null);
  const sessionsRef = useRef<SessionCardData[]>([]);
  const coalesceTimerRef = useRef<number | null>(null);
  const coalesceKeyRef = useRef<string | null>(null);
  const coalesceBaseRef = useRef<SessionCardData[] | null>(null);
  const smartPlanPackageHydratedRef = useRef<number | null>(null);
  sessionsRef.current = sessions;

  // Ref che riflette isDirty — usato nell'effect per non catturare closure stale
  const isDirtyRef = useRef(false);
  isDirtyRef.current = isDirty;

  // Protezione dati: beforeunload + draft auto-save in sessionStorage
  const draftKey = isNaN(id) ? undefined : `scheda-builder-${id}`;
  useUnsavedChanges({ dirty: isDirty, draftKey, draftData: sessions });

  // Branding export PDF: logo trainer salvato in localStorage
  const logoStorageKey = useMemo(() => {
    const trainer = getStoredTrainer();
    return `${WORKOUT_LOGO_STORAGE_PREFIX}.${trainer?.id ?? "anonymous"}`;
  }, []);
  const [exportLogoDataUrl, setExportLogoDataUrl] = useState<string | null>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem(logoStorageKey);
    setExportLogoDataUrl(saved);
  }, [logoStorageKey]);

  const handleLogoChange = useCallback((value: string | null) => {
    setExportLogoDataUrl(value);
    if (value) {
      window.localStorage.setItem(logoStorageKey, value);
    } else {
      window.localStorage.removeItem(logoStorageKey);
    }
  }, [logoStorageKey]);

  // Navigazione guardata — protegge tutti i punti di uscita dal builder
  const goBack = useCallback((force = false) => {
    if (!force && isDirtyRef.current && !window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    const dest = returnClientId
      ? `/clienti/${returnClientId}?tab=schede`
      : returnToAllenamenti ? "/allenamenti" : "/schede";
    router.push(dest);
  }, [router, returnClientId, returnToAllenamenti]);

  const guardedNavigate = useCallback((href: string) => {
    if (isDirtyRef.current && !window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    router.push(href);
  }, [router]);

  // Header inline editing
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  // Exercise selector
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectorContext, setSelectorContext] = useState<{
    sessionId: number;
    exerciseId?: number;
    sezione?: TemplateSection;
    blockId?: number;  // se set: aggiunge/sostituisce esercizio in un blocco
  } | null>(null);

  const clearCoalesceTimer = useCallback(() => {
    if (coalesceTimerRef.current) {
      window.clearTimeout(coalesceTimerRef.current);
      coalesceTimerRef.current = null;
    }
  }, []);

  const pushHistorySnapshot = useCallback((snapshot: SessionCardData[]) => {
    setHistoryPast((past) => [
      ...past.slice(-(HISTORY_LIMIT - 1)),
      cloneSessionsSnapshot(snapshot),
    ]);
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
    coalesceTimerRef.current = window.setTimeout(() => {
      flushCoalescedHistory();
    }, COALESCE_DELAY_MS);
  }, [clearCoalesceTimer, flushCoalescedHistory]);

  const applySessionsChange = useCallback(
    (
      updater: (prev: SessionCardData[]) => SessionCardData[],
      options?: { trackHistory?: boolean; markDirty?: boolean; coalesceKey?: string },
    ) => {
      const prev = sessionsRef.current;
      const next = updater(prev);
      if (next === prev) return;

      if (options?.trackHistory !== false) {
        const coalesceKey = options?.coalesceKey;
        if (coalesceKey) {
          if (coalesceKeyRef.current && coalesceKeyRef.current !== coalesceKey) {
            flushCoalescedHistory();
          }
          if (!coalesceBaseRef.current) {
            coalesceBaseRef.current = cloneSessionsSnapshot(prev);
          }
          coalesceKeyRef.current = coalesceKey;
          scheduleCoalescedFlush();
        } else {
          flushCoalescedHistory();
          pushHistorySnapshot(prev);
        }
      }

      sessionsRef.current = next;
      setSessions(next);
      if (options?.markDirty !== false) {
        setIsDirty(true);
      }
    },
    [flushCoalescedHistory, pushHistorySnapshot, scheduleCoalescedFlush],
  );

  // Sync server → local (protegge modifiche non salvate)
  useEffect(() => {
    if (plan && !isDirtyRef.current) {
      setSessions(
        plan.sessioni.map((s) => ({
          id: s.id,
          numero_sessione: s.numero_sessione,
          nome_sessione: s.nome_sessione,
          focus_muscolare: s.focus_muscolare,
          durata_minuti: s.durata_minuti,
          note: s.note,
          esercizi: [...s.esercizi],
          blocchi: (s.blocchi ?? []).map(serverBlockToCardData),
        })),
      );
      clearCoalesceTimer();
      coalesceBaseRef.current = null;
      coalesceKeyRef.current = null;
      setHistoryPast([]);
      setHistoryFuture([]);
      const serverTs = plan.updated_at ?? plan.created_at;
      if (serverTs) {
        const parsed = new Date(serverTs);
        if (!Number.isNaN(parsed.getTime())) {
          setLastSavedAt(parsed);
        }
      }
    }
  }, [plan, clearCoalesceTimer]);

  // Handoff temporaneo dal TemplateSelector: usa il plan-package solo alla prima apertura del builder.
  useEffect(() => {
    if (!plan) return;
    if (smartPlanPackageHydratedRef.current === plan.id) return;
    smartPlanPackageHydratedRef.current = plan.id;
    setSmartPlanPackage(consumeSmartPlanPackage(plan.id));
  }, [plan]);

  // Draft recovery — recupera bozza da sessionStorage se presente (TTL 24h)
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

  // Dopo una nuova modifica, gli avvisi precedenti non sono piu affidabili.
  useEffect(() => {
    if (!isDirtyRef.current || saveIssues.length === 0) return;
    setSaveIssues([]);
    setSaveIssuesExpanded(false);
  }, [sessions, saveIssues.length]);

  useEffect(() => {
    if (!isDirty || !smartPlanPackage) return;
    setSmartPlanPackage(null);
  }, [isDirty, smartPlanPackage]);

  useEffect(() => {
    return () => {
      clearCoalesceTimer();
      if (highlightTimeoutRef.current) {
        window.clearTimeout(highlightTimeoutRef.current);
      }
      highlightedNodeRef.current?.classList.remove(
        "ring-2",
        "ring-primary",
        "ring-offset-2",
        "ring-offset-background",
      );
    };
  }, [clearCoalesceTimer]);

  // Client name
  const clientNome = plan?.client_nome && plan?.client_cognome
    ? `${plan.client_nome} ${plan.client_cognome}`
    : undefined;

  // Volume totale scheda (solo esercizi principali con carico)
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

  const lastSavedLabel = useMemo(() => {
    if (!lastSavedAt) return null;
    return lastSavedAt.toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [lastSavedAt]);

  const saveCriticalCount = useMemo(
    () => saveIssues.filter((issue) => issue.level === "critical").length,
    [saveIssues],
  );
  const saveWarningCount = useMemo(
    () => saveIssues.filter((issue) => issue.level === "warning").length,
    [saveIssues],
  );
  const visibleSaveIssues = useMemo(
    () => (saveIssuesExpanded ? saveIssues : saveIssues.slice(0, 3)),
    [saveIssues, saveIssuesExpanded],
  );
  const hiddenSaveIssuesCount = useMemo(
    () => Math.max(0, saveIssues.length - 3),
    [saveIssues.length],
  );
  const saveIssueCategoryCounts = useMemo(() => {
    const counts: Partial<Record<SaveIssueCategory, number>> = {};
    for (const issue of saveIssues) {
      counts[issue.category] = (counts[issue.category] ?? 0) + 1;
    }
    return (Object.entries(counts) as Array<[SaveIssueCategory, number]>)
      .sort((a, b) => b[1] - a[1]);
  }, [saveIssues]);
  const canUndo = historyPast.length > 0;
  const canRedo = historyFuture.length > 0;

  const handleUndo = useCallback(() => {
    flushCoalescedHistory();
    const current = sessionsRef.current;
    setHistoryPast((past) => {
      if (past.length === 0) return past;
      const previous = past[past.length - 1];
      const previousSnapshot = cloneSessionsSnapshot(previous);
      setHistoryFuture((future) => [
        cloneSessionsSnapshot(current),
        ...future,
      ].slice(0, HISTORY_LIMIT));
      sessionsRef.current = previousSnapshot;
      setSessions(previousSnapshot);
      setIsDirty(true);
      return past.slice(0, -1);
    });
  }, [flushCoalescedHistory]);

  const handleRedo = useCallback(() => {
    flushCoalescedHistory();
    const current = sessionsRef.current;
    setHistoryFuture((future) => {
      if (future.length === 0) return future;
      const next = future[0];
      const nextSnapshot = cloneSessionsSnapshot(next);
      setHistoryPast((past) => [
        ...past.slice(-(HISTORY_LIMIT - 1)),
        cloneSessionsSnapshot(current),
      ]);
      sessionsRef.current = nextSnapshot;
      setSessions(nextSnapshot);
      setIsDirty(true);
      return future.slice(1);
    });
  }, [flushCoalescedHistory]);

  const issueHasTarget = useCallback((issue: SaveIssue) => (
    issue.sessionId != null ||
    issue.sessionNumber != null ||
    issue.blockId != null ||
    issue.exerciseRowId != null
  ), []);
  const firstNavigableIssue = useMemo(
    () => saveIssues.find(issueHasTarget),
    [saveIssues, issueHasTarget],
  );

  const jumpToIssue = useCallback((issue: SaveIssue) => {
    const selectorCandidates: string[] = [];
    if (issue.exerciseRowId != null) {
      selectorCandidates.push(`[data-workout-exercise-id="${issue.exerciseRowId}"]`);
    }
    if (issue.blockId != null) {
      selectorCandidates.push(`[data-workout-block-id="${issue.blockId}"]`);
    }
    if (issue.sessionId != null) {
      selectorCandidates.push(`[data-workout-session-id="${issue.sessionId}"]`);
    }
    if (issue.sessionNumber != null) {
      selectorCandidates.push(`[data-workout-session-number="${issue.sessionNumber}"]`);
    }

    let target: HTMLElement | null = null;
    for (const selector of selectorCandidates) {
      const found = document.querySelector(selector);
      if (found instanceof HTMLElement) {
        target = found;
        break;
      }
    }

    if (!target) return;

    highlightedNodeRef.current?.classList.remove(
      "ring-2",
      "ring-primary",
      "ring-offset-2",
      "ring-offset-background",
    );
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("ring-2", "ring-primary", "ring-offset-2", "ring-offset-background");
    highlightedNodeRef.current = target;

    if (highlightTimeoutRef.current) {
      window.clearTimeout(highlightTimeoutRef.current);
    }
    highlightTimeoutRef.current = window.setTimeout(() => {
      target.classList.remove("ring-2", "ring-primary", "ring-offset-2", "ring-offset-background");
    }, 1800);
  }, []);
  const focusFirstIssue = useCallback((issues: SaveIssue[]) => {
    const first = issues.find(issueHasTarget);
    if (!first) return;
    setSaveIssuesExpanded(true);
    window.setTimeout(() => jumpToIssue(first), 20);
  }, [issueHasTarget, jumpToIssue]);

  // Safety stats: conteggi avoid/caution/modify sugli esercizi nella scheda corrente (straight + in blocchi)
  const safetyStats = useMemo(() => {
    if (!safetyEntries) return { avoid: 0, caution: 0, modify: 0, total: 0 };
    const exerciseIds = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) exerciseIds.add(e.id_esercizio);
      for (const b of s.blocchi) {
        for (const e of b.esercizi) exerciseIds.add(e.id_esercizio);
      }
    }
    let avoid = 0;
    let caution = 0;
    let modify = 0;
    for (const [exId, entry] of Object.entries(safetyEntries)) {
      if (!exerciseIds.has(Number(exId))) continue;
      if (entry.severity === "avoid") avoid++;
      else if (entry.severity === "caution") caution++;
      else modify++;
    }
    return { avoid, caution, modify, total: avoid + caution + modify };
  }, [safetyEntries, sessions]);

  const safetyConditionStats = useMemo(() => {
    const detected = safetyMap?.condition_count ?? 0;
    if (!safetyEntries) {
      return { detected, mapped: 0, bodyTagged: 0, planImpacted: 0 };
    }

    const planExerciseIds = new Set<number>();
    for (const session of sessions) {
      for (const exercise of session.esercizi) planExerciseIds.add(exercise.id_esercizio);
      for (const block of session.blocchi) {
        for (const exercise of block.esercizi) planExerciseIds.add(exercise.id_esercizio);
      }
    }

    const mapped = new Set<number>();
    const bodyTagged = new Set<number>();
    const planImpacted = new Set<number>();

    for (const [exerciseId, entry] of Object.entries(safetyEntries)) {
      const numericExerciseId = Number(exerciseId);
      for (const condition of entry.conditions) {
        mapped.add(condition.id);
        if (condition.body_tags.length > 0) bodyTagged.add(condition.id);
        if (planExerciseIds.has(numericExerciseId)) {
          planImpacted.add(condition.id);
        }
      }
    }

    return {
      detected,
      mapped: mapped.size,
      bodyTagged: bodyTagged.size,
      planImpacted: planImpacted.size,
    };
  }, [safetyEntries, safetyMap?.condition_count, sessions]);

  // Condizioni raggruppate per categoria + esercizi coinvolti (per pannello espanso)
  const groupedConditions = useMemo(() => {
    if (!safetyEntries) return new Map<string, { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }[]>();

    // Mappa esercizio_id → nome (dagli esercizi nella scheda corrente)
    const exerciseNameMap = new Map<number, string>();
    for (const s of sessions) {
      for (const ex of s.esercizi) {
        exerciseNameMap.set(ex.id_esercizio, ex.esercizio_nome);
      }
      for (const block of s.blocchi) {
        for (const ex of block.esercizi) {
          exerciseNameMap.set(ex.id_esercizio, ex.esercizio_nome);
        }
      }
    }

    // Raccolta condizioni uniche con worst severity + esercizi coinvolti
    const condMap = new Map<number, SafetyConditionDetail & { worstSeverity: string; exercises: Map<number, { nome: string; severity: string }> }>();
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      const exId = Number(exIdStr);
      const exName = exerciseNameMap.get(exId);
      if (!exName) continue; // esercizio non nella scheda corrente

      for (const cond of entry.conditions) {
        const existing = condMap.get(cond.id);
        if (!existing) {
          const exercises = new Map<number, { nome: string; severity: string }>();
          exercises.set(exId, { nome: exName, severity: cond.severita });
          condMap.set(cond.id, { ...cond, worstSeverity: cond.severita, exercises });
        } else {
          const sevRank: Record<string, number> = { avoid: 2, modify: 1, caution: 0 };
          if ((sevRank[cond.severita] ?? 0) > (sevRank[existing.worstSeverity] ?? 0)) {
            existing.worstSeverity = cond.severita;
          }
          existing.exercises.set(exId, { nome: exName, severity: cond.severita });
        }
      }
    }

    // Raggruppa per categoria
    const groups = new Map<string, { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }[]>();
    for (const cond of condMap.values()) {
      const cat = cond.categoria;
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push({
        nome: cond.nome,
        worstSeverity: cond.worstSeverity,
        exercises: Array.from(cond.exercises.values()),
      });
    }

    // Ordina per CATEGORY_ORDER
    const sorted = new Map<string, { nome: string; worstSeverity: string; exercises: { nome: string; severity: string }[] }[]>();
    for (const cat of CATEGORY_ORDER) {
      if (groups.has(cat)) sorted.set(cat, groups.get(cat)!);
    }
    return sorted;
  }, [safetyEntries, sessions]);

  // Condizioni uniche con body_tags per Risk Body Map
  const uniqueConditionsForMap = useMemo(() => {
    if (!safetyEntries) return [];
    const seen = new Map<number, SafetyConditionDetail>();
    for (const entry of Object.values(safetyEntries)) {
      for (const cond of entry.conditions) {
        const sevRank: Record<string, number> = { avoid: 2, modify: 1, caution: 0 };
        const existing = seen.get(cond.id);
        if (!existing || (sevRank[cond.severita] ?? 0) > (sevRank[existing.severita] ?? 0)) {
          seen.set(cond.id, cond); // worst severity wins
        }
      }
    }
    return Array.from(seen.values()).filter((c) => c.body_tags.length > 0);
  }, [safetyEntries]);

  // Set di exercise ID gia' usati nella scheda (per badge "In scheda" nel selector)
  const usedExerciseIds = useMemo(() => {
    const ids = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) ids.add(e.id_esercizio);
      for (const b of s.blocchi) {
        for (const e of b.esercizi) ids.add(e.id_esercizio);
      }
    }
    return ids;
  }, [sessions]);

  // (beforeunload gestito da useUnsavedChanges sopra)

  // Dati safety per PDF clinico
  const safetyExportData = useMemo(() => {
    if (!safetyMap || !safetyEntries || safetyMap.condition_count === 0) return undefined;

    // Mappa esercizio_id → nome (dalla scheda corrente)
    const exerciseNameMap = new Map<number, string>();
    for (const s of sessions) {
      for (const ex of s.esercizi) {
        exerciseNameMap.set(ex.id_esercizio, ex.esercizio_nome);
      }
      for (const block of s.blocchi) {
        for (const ex of block.esercizi) {
          exerciseNameMap.set(ex.id_esercizio, ex.esercizio_nome);
        }
      }
    }

    // Condizioni uniche → esercizi coinvolti
    const condMap = new Map<number, { nome: string; severita: string; esercizi: Set<string> }>();
    for (const [exIdStr, entry] of Object.entries(safetyEntries)) {
      const exName = exerciseNameMap.get(Number(exIdStr));
      if (!exName) continue;
      for (const cond of entry.conditions) {
        const existing = condMap.get(cond.id);
        if (!existing) {
          condMap.set(cond.id, { nome: cond.nome, severita: cond.severita, esercizi: new Set([exName]) });
        } else {
          existing.esercizi.add(exName);
          const sevRank: Record<string, number> = { avoid: 2, modify: 1, caution: 0 };
          if ((sevRank[cond.severita] ?? 0) > (sevRank[existing.severita] ?? 0)) {
            existing.severita = cond.severita;
          }
        }
      }
    }

    return {
      clientNome: safetyMap.client_nome,
      conditionNames: safetyMap.condition_names,
      rows: Array.from(condMap.values())
        .sort((a, b) => {
          const order: Record<string, number> = { avoid: 0, caution: 1, modify: 2 };
          return (order[a.severita] ?? 3) - (order[b.severita] ?? 3);
        })
        .map((c) => ({ condizione: c.nome, severita: c.severita, esercizi: Array.from(c.esercizi) })),
    };
  }, [safetyMap, safetyEntries, sessions]);

  // ── Handlers sessioni ──

  const handleUpdateSession = useCallback((sessionId: number, updates: Partial<SessionCardData>) => {
    const fields = Object.keys(updates) as (keyof SessionCardData)[];
    const coalesceField =
      fields.length === 1 && SESSION_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
    applySessionsChange(
      (prev) => prev.map((s) => (s.id === sessionId ? { ...s, ...updates } : s)),
      { coalesceKey: coalesceField ? `session:${sessionId}:${coalesceField}` : undefined },
    );
  }, [applySessionsChange]);

  const handleDeleteSession = useCallback((sessionId: number) => {
    applySessionsChange((prev) => {
      const filtered = prev.filter((s) => s.id !== sessionId);
      return filtered.map((s, idx) => ({ ...s, numero_sessione: idx + 1 }));
    });
  }, [applySessionsChange]);

  const handleAddSession = useCallback(() => {
    const newId = -(Date.now());
    applySessionsChange((prev) => [
      ...prev,
      {
        id: newId,
        numero_sessione: prev.length + 1,
        nome_sessione: `Sessione ${prev.length + 1}`,
        focus_muscolare: null,
        durata_minuti: 60,
        note: null,
        esercizi: [],
        blocchi: [],
      },
    ]);
  }, [applySessionsChange]);

  const handleDuplicateSession = useCallback((sessionId: number) => {
    const source = sessions.find((s) => s.id === sessionId);
    if (!source) return;
    const now = Date.now();
    let tempId = now;
    applySessionsChange((prev) => [
      ...prev,
      {
        ...source,
        id: -(tempId++),
        numero_sessione: prev.length + 1,
        nome_sessione: `${source.nome_sessione} (copia)`,
        esercizi: source.esercizi.map((e, idx) => ({
          ...e,
          id: -(tempId + idx),
          ordine: idx + 1,
        })),
        blocchi: source.blocchi.map((b, bi) => ({
          ...b,
          id: -(tempId + source.esercizi.length + bi + 1),
          esercizi: b.esercizi.map((e, ei) => ({
            ...e,
            id: -(tempId + source.esercizi.length + bi * 100 + ei + 100),
          })),
        })),
      },
    ]);
  }, [sessions, applySessionsChange]);

  // ── Handlers esercizi ──

  const handleAddExercise = useCallback((sessionId: number, sezione?: TemplateSection) => {
    setSelectorContext({ sessionId, sezione });
    setSelectorOpen(true);
  }, []);

  const handleReplaceExercise = useCallback((sessionId: number, exerciseId: number) => {
    // Deduce la sezione dall'esercizio che si sta sostituendo
    const session = sessions.find((s) => s.id === sessionId);
    const exercise = session?.esercizi.find((e) => e.id === exerciseId);
    const sezione = exercise ? getSectionForCategory(exercise.esercizio_categoria) : undefined;
    setSelectorContext({ sessionId, exerciseId, sezione });
    setSelectorOpen(true);
  }, [sessions]);

  const handleExerciseSelected = useCallback((exercise: Exercise) => {
    if (!selectorContext) return;

    const isBlockContext = selectorContext.blockId !== undefined;

    applySessionsChange((prev) =>
      prev.map((s) => {
        if (s.id !== selectorContext.sessionId) return s;

        // ── Aggiunta/sostituzione in un BLOCCO ──
        if (isBlockContext) {
          const blockId = selectorContext.blockId!;
          return {
            ...s,
            blocchi: s.blocchi.map((b) => {
              if (b.id !== blockId) return b;
              if (selectorContext.exerciseId) {
                // Replace in block
                return {
                  ...b,
                  esercizi: b.esercizi.map((e) =>
                    e.id === selectorContext.exerciseId
                      ? { ...e, id_esercizio: exercise.id, esercizio_nome: exercise.nome, esercizio_categoria: exercise.categoria, esercizio_attrezzatura: exercise.attrezzatura }
                      : e,
                  ),
                };
              } else {
                // Add to block — defaults per esercizi in blocco (serie=1, rip=12-15, riposo=0)
                const newId = -(Date.now());
                return {
                  ...b,
                  esercizi: [
                    ...b.esercizi,
                    {
                      id: newId,
                      id_esercizio: exercise.id,
                      esercizio_nome: exercise.nome,
                      esercizio_categoria: exercise.categoria,
                      esercizio_attrezzatura: exercise.attrezzatura,
                      ordine: b.esercizi.length + 1,
                      serie: 1,  // in blocco: il blocco gestisce i giri
                      ripetizioni: "12-15",
                      tempo_riposo_sec: 0,  // riposo gestito dal blocco
                      tempo_esecuzione: null,
                      carico_kg: null,
                      note: null,
                    },
                  ],
                };
              }
            }),
          };
        }

        // ── Aggiunta/sostituzione STRAIGHT (non in blocco) ──
        if (selectorContext.exerciseId) {
          // Replace straight exercise
          return {
            ...s,
            esercizi: s.esercizi.map((e) =>
              e.id === selectorContext.exerciseId
                ? {
                    ...e,
                    id_esercizio: exercise.id,
                    esercizio_nome: exercise.nome,
                    esercizio_categoria: exercise.categoria,
                    esercizio_attrezzatura: exercise.attrezzatura,
                  }
                : e,
            ),
          };
        } else {
          // Add new straight exercise
          const newId = -(Date.now());
          const section = getSectionForCategory(exercise.categoria);
          const defaults = getSmartDefaults(exercise, plan?.obiettivo ?? "generale", section);
          return {
            ...s,
            esercizi: [
              ...s.esercizi,
              {
                id: newId,
                id_esercizio: exercise.id,
                esercizio_nome: exercise.nome,
                esercizio_categoria: exercise.categoria,
                esercizio_attrezzatura: exercise.attrezzatura,
                ordine: s.esercizi.length + 1,
                serie: defaults.serie,
                ripetizioni: defaults.ripetizioni,
                tempo_riposo_sec: defaults.tempo_riposo_sec,
                tempo_esecuzione: null,
                carico_kg: null,
                note: null,
              },
            ],
          };
        }
      }),
    );
    setSelectorContext(null);
  }, [selectorContext, plan?.obiettivo, applySessionsChange]);

  const handleUpdateExercise = useCallback(
    (sessionId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => {
      const fields = Object.keys(updates) as (keyof WorkoutExerciseRow)[];
      const coalesceField =
        fields.length === 1 && EXERCISE_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
      applySessionsChange(
        (prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  esercizi: s.esercizi.map((e) =>
                    e.id === exerciseId ? { ...e, ...updates } : e,
                  ),
                }
              : s,
          ),
        {
          coalesceKey: coalesceField
            ? `exercise:${sessionId}:${exerciseId}:${coalesceField}`
            : undefined,
        },
      );
    },
    [applySessionsChange],
  );

  const handleDeleteExercise = useCallback((sessionId: number, exerciseId: number) => {
    applySessionsChange((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              esercizi: s.esercizi
                .filter((e) => e.id !== exerciseId)
                .map((e, idx) => ({ ...e, ordine: idx + 1 })),
            }
          : s,
      ),
    );
  }, [applySessionsChange]);

  const handleQuickReplace = useCallback((sessionId: number, exerciseId: number, newExerciseId: number) => {
    const newEx = exerciseMap.get(newExerciseId);
    if (!newEx) return;
    applySessionsChange((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        return {
          ...s,
          esercizi: s.esercizi.map((e) =>
            e.id === exerciseId
              ? {
                  ...e,
                  id_esercizio: newEx.id,
                  esercizio_nome: newEx.nome,
                  esercizio_categoria: newEx.categoria,
                  esercizio_attrezzatura: newEx.attrezzatura,
                }
              : e,
          ),
        };
      }),
    );
  }, [exerciseMap, applySessionsChange]);

  // ── Block handlers ──

  const handleAddBlock = useCallback((sessionId: number, tipo: BlockType) => {
    applySessionsChange((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        const newOrdine = s.blocchi.length + s.esercizi.length + 1;
        return { ...s, blocchi: [...s.blocchi, createBlockCardData(tipo, newOrdine)] };
      }),
    );
  }, [applySessionsChange]);

  const handleUpdateBlock = useCallback((sessionId: number, blockId: number, updates: Partial<BlockCardData>) => {
    const fields = Object.keys(updates) as (keyof BlockCardData)[];
    const coalesceField =
      fields.length === 1 && BLOCK_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
    applySessionsChange(
      (prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? { ...s, blocchi: s.blocchi.map((b) => (b.id === blockId ? { ...b, ...updates } : b)) }
            : s,
        ),
      { coalesceKey: coalesceField ? `block:${sessionId}:${blockId}:${coalesceField}` : undefined },
    );
  }, [applySessionsChange]);

  const handleDeleteBlock = useCallback((sessionId: number, blockId: number) => {
    applySessionsChange((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? { ...s, blocchi: s.blocchi.filter((b) => b.id !== blockId) }
          : s,
      ),
    );
  }, [applySessionsChange]);

  const handleAddExerciseToBlock = useCallback((sessionId: number, blockId: number) => {
    setSelectorContext({ sessionId, blockId });
    setSelectorOpen(true);
  }, []);

  const handleUpdateExerciseInBlock = useCallback(
    (sessionId: number, blockId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => {
      const fields = Object.keys(updates) as (keyof WorkoutExerciseRow)[];
      const coalesceField =
        fields.length === 1 && EXERCISE_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
      applySessionsChange(
        (prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  blocchi: s.blocchi.map((b) =>
                    b.id === blockId
                      ? { ...b, esercizi: b.esercizi.map((e) => (e.id === exerciseId ? { ...e, ...updates } : e)) }
                      : b,
                  ),
                }
              : s,
          ),
        {
          coalesceKey: coalesceField
            ? `block-exercise:${sessionId}:${blockId}:${exerciseId}:${coalesceField}`
            : undefined,
        },
      );
    },
    [applySessionsChange],
  );

  const handleDeleteExerciseFromBlock = useCallback((sessionId: number, blockId: number, exerciseId: number) => {
    applySessionsChange((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              blocchi: s.blocchi.map((b) =>
                b.id === blockId
                  ? { ...b, esercizi: b.esercizi.filter((e) => e.id !== exerciseId).map((e, i) => ({ ...e, ordine: i + 1 })) }
                  : b,
              ),
            }
          : s,
      ),
    );
  }, [applySessionsChange]);

  const handleReplaceExerciseInBlock = useCallback((sessionId: number, blockId: number, exerciseId: number) => {
    setSelectorContext({ sessionId, blockId, exerciseId });
    setSelectorOpen(true);
  }, []);

  const handleQuickReplaceInBlock = useCallback(
    (sessionId: number, blockId: number, exerciseId: number, newExerciseId: number) => {
      const newEx = exerciseMap.get(newExerciseId);
      if (!newEx) return;
      applySessionsChange((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                blocchi: s.blocchi.map((b) =>
                  b.id === blockId
                    ? {
                        ...b,
                        esercizi: b.esercizi.map((e) =>
                          e.id === exerciseId
                            ? { ...e, id_esercizio: newEx.id, esercizio_nome: newEx.nome, esercizio_categoria: newEx.categoria, esercizio_attrezzatura: newEx.attrezzatura }
                            : e,
                        ),
                      }
                    : b,
                ),
              }
            : s,
        ),
      );
    },
    [exerciseMap, applySessionsChange],
  );

  const handleDuplicateBlock = useCallback((sessionId: number, blockId: number) => {
    applySessionsChange((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        const source = s.blocchi.find((b) => b.id === blockId);
        if (!source) return s;
        const newId = -(Date.now());
        const dup: BlockCardData = {
          ...source,
          id: newId,
          nome: source.nome ? `${source.nome} (copia)` : null,
          ordine: Math.max(...s.blocchi.map((b) => b.ordine), 0) + 1,
          esercizi: source.esercizi.map((e, i) => ({
            ...e,
            id: -(Date.now() + i + 1),
          })),
        };
        return { ...s, blocchi: [...s.blocchi, dup] };
      }),
    );
  }, [applySessionsChange]);

  const handleClearSection = useCallback((sessionId: number, sezione: TemplateSection, what: "exercises" | "blocks" | "all") => {
    applySessionsChange((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        const clearEx = what === "exercises" || what === "all";
        const clearBl = (what === "blocks" || what === "all") && sezione === "principale";
        return {
          ...s,
          esercizi: clearEx
            ? s.esercizi.filter((e) => getSectionForCategory(e.esercizio_categoria) !== sezione)
            : s.esercizi,
          blocchi: clearBl ? [] : s.blocchi,
        };
      }),
    );
  }, [applySessionsChange]);

  // ── Save ──

  const handleSave = useCallback(() => {
    if (!plan) return;
    flushCoalescedHistory();
    const currentSessions = sessionsRef.current;

    const { sessionsInput, issues, criticalCount, warningCount } = prepareSessionsInputForSave(
      currentSessions,
      exerciseMap,
      oneRMByPattern,
    );
    setSaveIssues(issues);
    setSaveIssuesExpanded(criticalCount > 0);
    if (criticalCount > 0) {
      return;
    }

    updateSessions.mutate(
      { id: plan.id, sessions: sessionsInput },
      {
        onSuccess: (savedPlan) => {
          if (warningCount > 0) {
            const firstWarning = issues.find((issue) => issue.level === "warning")?.message;
            toast.warning(
              `Scheda salvata con ${warningCount} avvis${warningCount === 1 ? "o" : "i"}.${
                firstWarning ? ` ${firstWarning}` : ""
              }`,
              {
                action: {
                  label: "Rivedi avvisi",
                  onClick: () => focusFirstIssue(issues),
                },
              },
            );
          }
          setIsDirty(false);
          if (draftKey) clearDraft(draftKey);
          const serverTs = savedPlan.updated_at ?? savedPlan.created_at;
          const parsed = serverTs ? new Date(serverTs) : new Date();
          if (!Number.isNaN(parsed.getTime())) {
            setLastSavedAt(parsed);
          }
        },
      },
    );
  }, [plan, updateSessions, draftKey, exerciseMap, oneRMByPattern, flushCoalescedHistory, focusFirstIssue]);

  // Shortcut globale: Ctrl+S / Cmd+S salva le modifiche della scheda.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      if (event.key.toLowerCase() !== "s") return;
      event.preventDefault();
      if (!isDirty || updateSessions.isPending) return;
      handleSave();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [handleSave, isDirty, updateSessions.isPending]);

  // Shortcut globale: Ctrl/Cmd+Z undo, Ctrl/Cmd+Shift+Z o Ctrl/Cmd+Y redo.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      if (isEditableTarget(event.target)) return;

      const key = event.key.toLowerCase();
      if (key === "z") {
        event.preventDefault();
        if (event.shiftKey) {
          if (canRedo) handleRedo();
        } else if (canUndo) {
          handleUndo();
        }
        return;
      }
      if (key === "y") {
        event.preventDefault();
        if (canRedo) handleRedo();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [canUndo, canRedo, handleUndo, handleRedo]);

  // ── Inline metadata editing ──

  const startEdit = useCallback((field: string, value: string) => {
    setEditingField(field);
    setEditValue(value);
  }, []);

  const saveEdit = useCallback(() => {
    if (!plan || !editingField) return;
    const v = editValue.trim();
    if (v && v !== String((plan as unknown as Record<string, unknown>)[editingField] ?? "")) {
      updateWorkout.mutate({ id: plan.id, [editingField]: v });
    }
    setEditingField(null);
  }, [plan, editingField, editValue, updateWorkout]);

  const cancelEdit = useCallback(() => setEditingField(null), []);

  // ── Loading / Error ──

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (isError || !plan) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-destructive">Scheda non trovata.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/schede")}>
          Torna alle schede
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" data-print-hide>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => goBack()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            {editingField === "nome" ? (
              <div className="flex items-center gap-1">
                <Input
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                  className="h-8 text-lg font-bold"
                  autoFocus
                />
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={saveEdit}>
                  <Check className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={cancelEdit}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <button
                onClick={() => startEdit("nome", plan.nome)}
                className="flex items-center gap-2 text-xl font-bold tracking-tight hover:text-primary transition-colors"
              >
                {plan.nome}
                <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            )}
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Select
                value={plan.id_cliente ? String(plan.id_cliente) : "__none__"}
                onValueChange={(v) => {
                  const newClientId = v === "__none__" ? null : Number(v);
                  updateWorkout.mutate({ id: plan.id, id_cliente: newClientId });
                }}
              >
                <SelectTrigger size="sm" className="w-[180px] text-xs">
                  <SelectValue placeholder="Assegna cliente" />
                </SelectTrigger>
                <SelectContent position="popper" sideOffset={4}>
                  <SelectItem value="__none__">Nessun cliente</SelectItem>
                  {clients.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.nome} {c.cognome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {plan.id_cliente && clientNome && (
                <button
                  onClick={() => guardedNavigate(`/clienti/${plan.id_cliente}`)}
                  className="text-xs text-primary hover:underline"
                >
                  Vai al profilo
                </button>
              )}
              <Select
                value={plan.obiettivo}
                onValueChange={(v) => updateWorkout.mutate({ id: plan.id, obiettivo: v })}
              >
                <SelectTrigger className="h-6 w-auto text-xs border-0 bg-transparent p-0 font-medium">
                  <Badge variant="outline" className="text-xs cursor-pointer">
                    {OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}
                  </Badge>
                </SelectTrigger>
                <SelectContent>
                  {OBIETTIVI_SCHEDA.map((o) => (
                    <SelectItem key={o} value={o}>{OBIETTIVO_LABELS[o]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={plan.livello}
                onValueChange={(v) => updateWorkout.mutate({ id: plan.id, livello: v })}
              >
                <SelectTrigger className="h-6 w-auto text-xs border-0 bg-transparent p-0 font-medium">
                  <Badge variant="outline" className="text-xs cursor-pointer">
                    {LIVELLO_LABELS[plan.livello] ?? plan.livello}
                  </Badge>
                </SelectTrigger>
                <SelectContent>
                  {LIVELLI_SCHEDA.map((l) => (
                    <SelectItem key={l} value={l}>{LIVELLO_LABELS[l]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {totalVolume != null && (
                <Badge variant="outline" className="text-xs tabular-nums">
                  Vol. totale: {totalVolume.toLocaleString("it-IT")} kg
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isDirty && lastSavedLabel && (
            <span className="hidden sm:inline text-xs text-muted-foreground">
              Salvata alle {lastSavedLabel}
            </span>
          )}
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={handleUndo}
            disabled={!canUndo}
            title="Annulla (Ctrl/Cmd+Z)"
          >
            <Undo2 className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={handleRedo}
            disabled={!canRedo}
            title="Ripeti (Ctrl/Cmd+Shift+Z)"
          >
            <Redo2 className="h-4 w-4" />
          </Button>
          <ExportButtons
            nome={plan.nome}
            obiettivo={plan.obiettivo}
            livello={plan.livello}
            clientNome={clientNome}
            durata_settimane={plan.durata_settimane}
            sessioni_per_settimana={plan.sessioni_per_settimana}
            sessioni={sessions}
            safety={safetyExportData}
            logoDataUrl={exportLogoDataUrl}
            onLogoChange={handleLogoChange}
          />
          {isDirty && (
            <Button onClick={handleSave} disabled={updateSessions.isPending}>
              <Save className="mr-1.5 h-4 w-4" />
              {updateSessions.isPending ? "Salvataggio..." : "Salva"}
            </Button>
          )}
        </div>
      </div>

      {/* ── Banner ritorno al contesto di provenienza ── */}
      {returnClientId && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-2 flex items-center gap-2" data-print-hide>
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <button
            onClick={() => guardedNavigate(`/clienti/${returnClientId}?tab=schede`)}
            className="text-sm text-primary hover:underline"
          >
            Torna al profilo cliente
          </button>
        </div>
      )}
      {returnToAllenamenti && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-2 flex items-center gap-2" data-print-hide>
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <button
            onClick={() => guardedNavigate("/allenamenti")}
            className="text-sm text-primary hover:underline"
          >
            Torna al monitoraggio
          </button>
        </div>
      )}

      {/* ── Split Layout ── */}
      <div className="grid gap-6 lg:grid-cols-2 print:block">
        {/* Editor (sinistra) */}
        <div className="space-y-3" data-print-hide>
          {/* Safety Overview Panel — dashboard clinica collapsibile */}
          {safetyMap && safetyMap.condition_count > 0 && (
            <Collapsible open={safetyExpanded} onOpenChange={setSafetyExpanded}>
              <Card className={`border-l-4 ${safetyStats.avoid > 0 ? "border-l-red-500" : safetyStats.caution > 0 ? "border-l-amber-400" : "border-l-blue-400"} transition-all duration-200`}>
                <CardContent className="p-4 space-y-3">
                  {/* Header — sempre visibile */}
                  <CollapsibleTrigger asChild>
                    <button className="flex items-center justify-between w-full text-left group">
                      <div className="flex items-center gap-2">
                        <Shield className={`h-4.5 w-4.5 ${safetyStats.avoid > 0 ? "text-red-500" : safetyStats.caution > 0 ? "text-amber-500" : "text-blue-500"}`} />
                        <div>
                          <span className="text-sm font-semibold">Profilo Clinico</span>
                          <span className="text-sm text-muted-foreground"> — {safetyMap.client_nome}</span>
                        </div>
                      </div>
                      <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${safetyExpanded ? "rotate-180" : ""}`} />
                    </button>
                  </CollapsibleTrigger>

                  {/* KPI mini-row */}
                  <div className="grid grid-cols-4 gap-2">
                    <div className="rounded-lg bg-muted/50 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums">{safetyMap.condition_count}</div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Condizioni</div>
                    </div>
                    <div className="rounded-lg bg-red-50 dark:bg-red-950/30 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums text-red-600 dark:text-red-400">{safetyStats.avoid}</div>
                      <div className="text-[10px] text-red-600/70 dark:text-red-400/70 uppercase tracking-wider">Evitare</div>
                    </div>
                    <div className="rounded-lg bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums text-amber-600 dark:text-amber-400">{safetyStats.caution}</div>
                      <div className="text-[10px] text-amber-600/70 dark:text-amber-400/70 uppercase tracking-wider">Cautela</div>
                    </div>
                    <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 px-3 py-2 text-center">
                      <div className="text-lg font-extrabold tracking-tighter tabular-nums text-blue-600 dark:text-blue-400">{safetyStats.modify}</div>
                      <div className="text-[10px] text-blue-600/70 dark:text-blue-400/70 uppercase tracking-wider">Adattare</div>
                    </div>
                  </div>

                  {/* Badge condizioni */}
                  <div className="flex flex-wrap gap-1.5">
                    {safetyMap.condition_names.map((name) => (
                      <Badge key={name} variant="outline" className="text-[11px] font-normal">
                        {name}
                      </Badge>
                    ))}
                  </div>

                  <div className="text-[10px] text-muted-foreground">
                    {safetyConditionStats.planImpacted} condizioni impattano la scheda corrente su {safetyConditionStats.detected} rilevate.
                    {safetyConditionStats.mapped < safetyConditionStats.detected && (
                      <span> {safetyConditionStats.mapped} sono gia&apos; mappate nel catalogo safety.</span>
                    )}
                    {safetyConditionStats.bodyTagged < safetyConditionStats.mapped && (
                      <span> {safetyConditionStats.bodyTagged} hanno body tags anatomici renderizzabili.</span>
                    )}
                  </div>

                  {/* Pannello espanso — Risk Body Map + condizioni raggruppate */}
                  <CollapsibleContent className="space-y-3">
                    <Separator />
                    {/* Risk Body Map */}
                    {uniqueConditionsForMap.length > 0 && (
                      <div className="flex flex-col items-center">
                        <RiskBodyMap conditions={uniqueConditionsForMap} />
                        <div className="flex items-center gap-3 mt-1">
                          <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
                            <span className="h-2 w-2 rounded-full bg-red-500" /> Evitare
                          </span>
                          <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
                            <span className="h-2 w-2 rounded-full bg-amber-500" /> Cautela
                          </span>
                          <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
                            <span className="h-2 w-2 rounded-full bg-blue-500" /> Adattare
                          </span>
                        </div>
                      </div>
                    )}
                    {/* Medication flags */}
                    {safetyMap.medication_flags && safetyMap.medication_flags.length > 0 && (
                      <div>
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                          Farmaci Rilevanti
                        </div>
                        <div className="space-y-1.5">
                          {safetyMap.medication_flags.map((mf) => (
                            <div key={mf.flag} className="flex items-start gap-2 text-xs">
                              <InfoIcon className="h-3.5 w-3.5 shrink-0 mt-0.5 text-purple-500" />
                              <p className="text-muted-foreground leading-relaxed">{mf.nota}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {Array.from(groupedConditions.entries()).map(([categoria, conditions]) => (
                      <div key={categoria}>
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                          {CONDITION_CATEGORY_LABELS[categoria] ?? categoria}
                        </div>
                        <div className="space-y-2.5">
                          {conditions.map((cond) => (
                            <div key={cond.nome}>
                              <div className="flex items-center gap-2 text-xs">
                                {cond.worstSeverity === "avoid" ? (
                                  <ShieldAlert className="h-3.5 w-3.5 shrink-0 text-red-500" />
                                ) : cond.worstSeverity === "caution" ? (
                                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-500" />
                                ) : (
                                  <InfoIcon className="h-3.5 w-3.5 shrink-0 text-blue-500" />
                                )}
                                <span className="flex-1 font-medium">{cond.nome}</span>
                                <span className={`text-[10px] font-medium ${cond.worstSeverity === "avoid" ? "text-red-600 dark:text-red-400" : cond.worstSeverity === "caution" ? "text-amber-600 dark:text-amber-400" : "text-blue-600 dark:text-blue-400"}`}>
                                  {cond.worstSeverity === "avoid" ? "Evitare" : cond.worstSeverity === "caution" ? "Cautela" : "Adattare"}
                                </span>
                              </div>
                              {/* Esercizi coinvolti */}
                              {cond.exercises.length > 0 && (
                                <div className="ml-5.5 mt-1 flex flex-wrap gap-1">
                                  {cond.exercises.map((ex) => (
                                    <span
                                      key={ex.nome}
                                      className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] ${
                                        ex.severity === "avoid"
                                          ? "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400"
                                          : ex.severity === "caution"
                                            ? "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                                            : "bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400"
                                      }`}
                                    >
                                      {ex.nome}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                    {plan.id_cliente && (
                      <button
                        onClick={() => guardedNavigate(`/clienti/${plan.id_cliente}`)}
                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-1"
                      >
                        Vai al profilo di {safetyMap.client_nome.split(" ")[0]}
                      </button>
                    )}
                  </CollapsibleContent>
                </CardContent>
              </Card>
            </Collapsible>
          )}

          {/* Muscle Map Panel — silhouette anatomica con muscoli illuminati live */}
          {sessions.length > 0 && (
            <MuscleMapPanel
              sessions={sessions}
              exerciseMap={exerciseMap}
              livello={plan.livello}
              sessioniPerSettimana={plan.sessioni_per_settimana}
              backendAnalysis={smartBackendAnalysis}
            />
          )}

          {/* Smart Analysis Panel — analisi copertura muscolare, volume, biomeccanica */}
          {sessions.length > 0 && (
            <SmartAnalysisPanel
              sessions={sessions.map(s => ({
                nome_sessione: s.nome_sessione,
                esercizi: s.esercizi.map(e => ({
                  id_esercizio: e.id_esercizio,
                  serie: e.serie,
                })),
              }))}
              exerciseMap={exerciseMap}
              livello={plan.livello}
              obiettivo={plan.obiettivo}
              sessioniPerSettimana={plan.sessioni_per_settimana}
              safetyMap={safetyEntries ?? null}
              smartPlanPackage={smartPlanPackage}
              safetyConditionCount={safetyConditionStats.detected}
              impactedConditionCount={safetyConditionStats.planImpacted}
              onBackendAnalysisChange={setSmartBackendAnalysis}
            />
          )}

          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              safetyMap={safetyEntries}
              exerciseMap={exerciseMap}
              schedaId={id}
              parentFrom={fromParam}
              oneRMByPattern={oneRMByPattern}
              onUpdateSession={handleUpdateSession}
              onDeleteSession={handleDeleteSession}
              onDuplicateSession={handleDuplicateSession}
              onAddExercise={handleAddExercise}
              onUpdateExercise={handleUpdateExercise}
              onDeleteExercise={handleDeleteExercise}
              onReplaceExercise={handleReplaceExercise}
              onQuickReplace={handleQuickReplace}
              onAddBlock={handleAddBlock}
              onUpdateBlock={handleUpdateBlock}
              onDeleteBlock={handleDeleteBlock}
              onDuplicateBlock={handleDuplicateBlock}
              onAddExerciseToBlock={handleAddExerciseToBlock}
              onUpdateExerciseInBlock={handleUpdateExerciseInBlock}
              onDeleteExerciseFromBlock={handleDeleteExerciseFromBlock}
              onReplaceExerciseInBlock={handleReplaceExerciseInBlock}
              onQuickReplaceInBlock={handleQuickReplaceInBlock}
              onClearSection={handleClearSection}
            />
          ))}

          <Button
            variant="outline"
            className="w-full"
            onClick={handleAddSession}
          >
            <Plus className="mr-2 h-4 w-4" />
            Aggiungi Sessione
          </Button>
        </div>

        {/* Preview (destra, solo desktop + stampa) */}
        <div className="hidden lg:block print:block space-y-4 sticky top-6 workout-preview-container">
          <WorkoutPreview
            nome={plan.nome}
            obiettivo={plan.obiettivo}
            livello={plan.livello}
            clientNome={clientNome}
            durata_settimane={plan.durata_settimane}
            sessioni_per_settimana={plan.sessioni_per_settimana}
            sessioni={sessions}
            logoDataUrl={exportLogoDataUrl}
            note={plan.note}
            exerciseMap={exerciseMap}
          />
        </div>
      </div>

      {/* Exercise Selector Dialog */}
      <ExerciseSelector
        open={selectorOpen}
        onOpenChange={setSelectorOpen}
        onSelect={handleExerciseSelected}
        categoryFilter={
          selectorContext?.sezione
            ? SECTION_CATEGORIES[selectorContext.sezione]
            : undefined
        }
        safetyMap={safetyEntries}
        schedaId={id}
        usedExerciseIds={usedExerciseIds}
      />

      {/* Save bar sticky: riduce frizione su schede lunghe (CTA sempre visibile). */}
      {(isDirty || saveIssues.length > 0) && (
        <div
          className="fixed bottom-3 left-1/2 z-40 w-[calc(100%-1.5rem)] max-w-2xl -translate-x-1/2"
          data-print-hide
        >
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
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8"
                    onClick={handleUndo}
                    disabled={!canUndo}
                    title="Annulla"
                  >
                    <Undo2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8"
                    onClick={handleRedo}
                    disabled={!canRedo}
                    title="Ripeti"
                  >
                    <Redo2 className="h-4 w-4" />
                  </Button>
                  <Button onClick={handleSave} disabled={updateSessions.isPending} className="h-8">
                    <Save className="mr-1.5 h-4 w-4" />
                    {updateSessions.isPending ? "Salvataggio..." : "Salva"}
                  </Button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8"
                  onClick={() => {
                    setSaveIssues([]);
                    setSaveIssuesExpanded(false);
                  }}
                >
                  Chiudi
                </Button>
              )}
            </div>
            {saveIssues.length > 0 && (
              <div
                className={`mt-2 rounded-md border px-2 py-1.5 ${
                  saveCriticalCount > 0
                    ? "border-red-300 bg-red-50/80 dark:border-red-900 dark:bg-red-950/30"
                    : "border-amber-300 bg-amber-50/80 dark:border-amber-900 dark:bg-amber-950/30"
                }`}
              >
                <p
                  className={`text-[11px] font-medium ${
                    saveCriticalCount > 0
                      ? "text-red-700 dark:text-red-300"
                      : "text-amber-700 dark:text-amber-300"
                  }`}
                >
                  {saveCriticalCount > 0
                    ? `Salvataggio bloccato: ${saveCriticalCount} errore critico.`
                    : `Salvataggio assistito: ${saveWarningCount} avviso/i non bloccante/i.`}
                </p>
                {saveIssueCategoryCounts.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {saveIssueCategoryCounts.map(([category, count]) => (
                      <span
                        key={category}
                        className="inline-flex items-center rounded border border-current/20 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                      >
                        {SAVE_ISSUE_CATEGORY_LABELS[category]}: {count}
                      </span>
                    ))}
                  </div>
                )}
                <ul className="mt-1 space-y-0.5">
                  {visibleSaveIssues.map((issue, idx) => (
                    <li key={`${issue.level}-${idx}`} className="text-[10px] text-muted-foreground">
                      {issueHasTarget(issue) ? (
                        <button
                          type="button"
                          onClick={() => jumpToIssue(issue)}
                          className="text-left hover:text-foreground hover:underline"
                        >
                          • {issue.message}
                        </button>
                      ) : (
                        <>• {issue.message}</>
                      )}
                    </li>
                  ))}
                  {!saveIssuesExpanded && hiddenSaveIssuesCount > 0 && (
                    <li className="text-[10px] text-muted-foreground">
                      • +{hiddenSaveIssuesCount} altri avvisi
                    </li>
                  )}
                </ul>
                {saveIssues.length > 3 && (
                  <button
                    type="button"
                    onClick={() => setSaveIssuesExpanded((prev) => !prev)}
                    className="mt-1 text-[10px] font-medium text-primary hover:underline"
                  >
                    {saveIssuesExpanded ? "Mostra meno avvisi" : `Mostra tutti gli avvisi (${saveIssues.length})`}
                  </button>
                )}
                {firstNavigableIssue && (
                  <button
                    type="button"
                    onClick={() => jumpToIssue(firstNavigableIssue)}
                    className="mt-1 block text-[10px] font-medium text-primary hover:underline"
                  >
                    Vai al primo punto da rivedere
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
