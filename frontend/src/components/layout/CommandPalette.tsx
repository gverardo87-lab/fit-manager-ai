// src/components/layout/CommandPalette.tsx
"use client";

/**
 * Command Palette avanzata — Ctrl+K per aprire.
 *
 * 4 feature distintive:
 * 1. Preview Panel: pannello dati a destra con info live dell'elemento selezionato
 * 2. Risposte KPI: digiti "entrate" e vedi il numero senza navigare
 * 3. Azioni Contestuali: la palette sa dove sei e suggerisce azioni rilevanti
 * 4. Assistente AI: digita ">" per comandi in italiano naturale (parse + preview + commit)
 *
 * Dati lazy-loaded via React Query (enabled: open).
 * Zero prop drilling — custom event per apertura da sidebar.
 */

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  User,
  FileText,
  Dumbbell,
  Wallet,
  BookOpen,
  Settings,
  UserPlus,
  FilePlus,
  CalendarPlus,
  TrendingUp,
  AlertTriangle,
  CalendarCheck,
  CreditCard,
  Activity,
  BarChart3,
  Scale,
  HeartPulse,
  Sparkles,
  Loader2,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import apiClient from "@/lib/api-client";
import { formatCurrency } from "@/lib/format";
import { useParseAssistant, useCommitAssistant } from "@/hooks/useAssistant";
import type {
  ClientEnriched,
  ClientEnrichedListResponse,
  Exercise,
  ExerciseListResponse,
  DashboardSummary,
  MovementStats,
  AssistantParseResponse,
  AmbiguityItem,
  ParsedOperation,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// COSTANTI
// ════════════════════════════════════════════════════════════

const now = new Date();
const ANNO = now.getFullYear();
const MESE = now.getMonth() + 1;

const NAV_ITEMS = [
  { id: "nav-dashboard", href: "/", label: "Dashboard", icon: LayoutDashboard },
  { id: "nav-agenda", href: "/agenda", label: "Agenda", icon: Calendar },
  { id: "nav-clienti", href: "/clienti", label: "Clienti", icon: Users },
  { id: "nav-contratti", href: "/contratti", label: "Contratti", icon: FileText },
  { id: "nav-esercizi", href: "/esercizi", label: "Esercizi", icon: Dumbbell },
  { id: "nav-schede", href: "/schede", label: "Schede Allenamento", icon: Dumbbell },
  { id: "nav-monitoraggio", href: "/monitoraggio", label: "Monitoraggio Clienti", icon: BarChart3 },
  { id: "nav-allenamenti", href: "/allenamenti", label: "Aderenza Allenamenti", icon: Activity },
  { id: "nav-cassa", href: "/cassa", label: "Cassa", icon: Wallet },
  { id: "nav-guida", href: "/guida", label: "Guida", icon: BookOpen },
  { id: "nav-impostazioni", href: "/impostazioni", label: "Impostazioni", icon: Settings },
] as const;

const ACTIONS = [
  { id: "action-new-client", label: "Nuovo Cliente", icon: UserPlus, href: "/clienti?new=1" },
  { id: "action-new-contract", label: "Nuovo Contratto", icon: FilePlus, href: "/contratti?new=1" },
  { id: "action-new-session", label: "Nuova Sessione", icon: CalendarPlus, href: "/agenda?newEvent=1" },
] as const;

// ── Assistant ──

const INTENT_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  "agenda.create_event": { label: "Nuovo Evento", icon: Calendar, color: "text-violet-600 dark:text-violet-400", bg: "bg-violet-100 dark:bg-violet-900/30" },
  "movement.create_manual": { label: "Movimento di Cassa", icon: Wallet, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-100 dark:bg-emerald-900/30" },
  "measurement.create": { label: "Nuova Misurazione", icon: Scale, color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-900/30" },
};

const ASSISTANT_EXAMPLES = [
  { label: "Evento", example: "Marco domani alle 18 PT", icon: Calendar },
  { label: "Pagamento", example: "spesa affitto 800 euro", icon: Wallet },
  { label: "Misura", example: "Marco peso 82 massa grassa 18", icon: Scale },
] as const;

// ════════════════════════════════════════════════════════════
// PREVIEW: Client
// ════════════════════════════════════════════════════════════

function ClientPreview({ client }: { client: ClientEnriched }) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
          {client.nome[0]}{client.cognome[0]}
        </div>
        <div>
          <p className="text-sm font-semibold">{client.nome} {client.cognome}</p>
          <Badge
            variant={client.stato === "Attivo" ? "default" : "secondary"}
            className="mt-0.5 text-[10px]"
          >
            {client.stato}
          </Badge>
        </div>
      </div>

      <Separator />

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Crediti
          </p>
          <p className="text-lg font-extrabold tracking-tighter tabular-nums">
            {client.crediti_residui}
          </p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Contratti
          </p>
          <p className="text-lg font-extrabold tracking-tighter tabular-nums">
            {client.contratti_attivi}
          </p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Versato
          </p>
          <p className="text-sm font-bold tabular-nums">
            {formatCurrency(client.totale_versato)}
          </p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Totale Attivo
          </p>
          <p className="text-sm font-bold tabular-nums">
            {formatCurrency(client.prezzo_totale_attivo)}
          </p>
        </div>
      </div>

      {/* Warnings */}
      {client.ha_rate_scadute && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-2.5 text-xs font-medium text-red-700 dark:bg-red-950/30 dark:text-red-400">
          <AlertTriangle className="h-3.5 w-3.5" />
          Rate scadute
        </div>
      )}

      {/* Contact */}
      {(client.email || client.telefono) && (
        <>
          <Separator />
          <div className="space-y-1.5 text-xs text-muted-foreground">
            {client.email && <p>{client.email}</p>}
            {client.telefono && <p>{client.telefono}</p>}
          </div>
        </>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PREVIEW: Exercise
// ════════════════════════════════════════════════════════════

function ExercisePreview({ exercise }: { exercise: Exercise }) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <p className="text-sm font-semibold">{exercise.nome}</p>
        {exercise.nome_en && (
          <p className="text-xs text-muted-foreground">{exercise.nome_en}</p>
        )}
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-1.5">
        <Badge variant="default" className="text-[10px]">{exercise.categoria}</Badge>
        <Badge variant="secondary" className="text-[10px]">{exercise.difficolta}</Badge>
        <Badge variant="outline" className="text-[10px]">{exercise.attrezzatura}</Badge>
      </div>

      <Separator />

      {/* Classification */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Pattern
          </p>
          <p className="text-xs font-medium">{exercise.pattern_movimento}</p>
        </div>
        {exercise.force_type && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
              Forza
            </p>
            <p className="text-xs font-medium">{exercise.force_type}</p>
          </div>
        )}
      </div>

      {/* Muscles */}
      {exercise.muscoli_primari.length > 0 && (
        <>
          <Separator />
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
              Muscoli Primari
            </p>
            <div className="flex flex-wrap gap-1">
              {exercise.muscoli_primari.map((m) => (
                <span
                  key={m}
                  className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary"
                >
                  {m}
                </span>
              ))}
            </div>
          </div>
        </>
      )}

      {exercise.muscoli_secondari.length > 0 && (
        <div>
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Muscoli Secondari
          </p>
          <div className="flex flex-wrap gap-1">
            {exercise.muscoli_secondari.map((m) => (
              <span
                key={m}
                className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
              >
                {m}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PREVIEW: KPI
// ════════════════════════════════════════════════════════════

function KpiPreview({
  summary,
  stats,
}: {
  summary: DashboardSummary | undefined;
  stats: MovementStats | undefined;
}) {
  if (!summary && !stats) return null;

  return (
    <div className="space-y-4">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
        Panoramica Mese
      </p>

      <div className="space-y-3">
        {stats && (
          <>
            <KpiRow
              icon={TrendingUp}
              label="Entrate"
              value={formatCurrency(stats.totale_entrate)}
              color="text-emerald-600 dark:text-emerald-400"
            />
            <KpiRow
              icon={Wallet}
              label="Uscite"
              value={formatCurrency(stats.totale_uscite_variabili + stats.totale_uscite_fisse)}
              color="text-red-600 dark:text-red-400"
            />
            <KpiRow
              icon={Activity}
              label="Margine"
              value={formatCurrency(stats.margine_netto)}
              color={stats.margine_netto >= 0
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-red-600 dark:text-red-400"}
            />
          </>
        )}

        {summary && (
          <>
            <Separator />
            <KpiRow
              icon={Users}
              label="Clienti Attivi"
              value={String(summary.active_clients)}
              color="text-blue-600 dark:text-blue-400"
            />
            <KpiRow
              icon={CreditCard}
              label="Rate Pendenti"
              value={String(summary.pending_rates)}
              color={summary.pending_rates > 0
                ? "text-amber-600 dark:text-amber-400"
                : "text-emerald-600 dark:text-emerald-400"}
            />
            <KpiRow
              icon={CalendarCheck}
              label="Appuntamenti Oggi"
              value={String(summary.todays_appointments)}
              color="text-violet-600 dark:text-violet-400"
            />
          </>
        )}
      </div>
    </div>
  );
}

function KpiRow({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <span className={`text-sm font-bold tabular-nums ${color}`}>{value}</span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TIPO PREVIEW (solo search mode)
// ════════════════════════════════════════════════════════════

type PreviewData =
  | { type: "client"; data: ClientEnriched }
  | { type: "exercise"; data: Exercise }
  | { type: "kpi" }
  | null;

// ════════════════════════════════════════════════════════════
// ASSISTANT: Result Card (full-width, prominent)
// ════════════════════════════════════════════════════════════

function AssistantResultCard({
  operation,
  entities,
  ambiguities,
  onCommit,
  isCommitting,
}: {
  operation: ParsedOperation;
  entities: { label: string }[];
  ambiguities: AmbiguityItem[];
  onCommit: () => void;
  isCommitting: boolean;
}) {
  const config = INTENT_CONFIG[operation.intent] ?? {
    label: operation.intent,
    icon: Sparkles,
    color: "text-primary",
    bg: "bg-primary/10",
  };
  const Icon = config.icon;
  const ready = operation.confidence >= 0.4 && ambiguities.length === 0;

  const borderColor = operation.confidence >= 0.7
    ? "border-emerald-200 dark:border-emerald-800"
    : operation.confidence >= 0.4
      ? "border-amber-200 dark:border-amber-800"
      : "border-red-200 dark:border-red-800";

  return (
    <div className={`rounded-xl border-2 ${borderColor} overflow-hidden`}>
      {/* Header */}
      <div className={`flex items-center gap-3 px-4 py-3 ${config.bg}`}>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-background shadow-sm">
          <Icon className={`h-4.5 w-4.5 ${config.color}`} />
        </div>
        <div className="min-w-0 flex-1">
          <p className={`text-xs font-semibold ${config.color}`}>{config.label}</p>
          <p className="truncate text-sm font-medium">{operation.preview_label}</p>
        </div>
        {/* Confidence dot */}
        <div className={`h-2.5 w-2.5 rounded-full ${
          operation.confidence >= 0.7
            ? "bg-emerald-500"
            : operation.confidence >= 0.4
              ? "bg-amber-500"
              : "bg-red-500"
        }`} />
      </div>

      {/* Entities */}
      {entities.length > 0 && (
        <div className="space-y-0.5 px-4 py-2.5">
          {entities.map((e, i) => {
            const [key, ...rest] = e.label.split(":");
            const val = rest.join(":").trim();
            return (
              <div key={i} className="flex items-center justify-between py-1 text-xs">
                <span className="text-muted-foreground">{key}</span>
                <span className="font-medium">{val}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Ambiguities */}
      {ambiguities.length > 0 && (
        <div className="mx-4 mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
          <AlertTriangle className="mr-1.5 inline h-3 w-3" />
          {ambiguities[0].message}
        </div>
      )}

      {/* CTA */}
      {ready && (
        <div className="border-t bg-muted/30 px-4 py-2.5">
          <button
            type="button"
            onClick={onCommit}
            disabled={isCommitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {isCommitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Conferma
                <kbd className="rounded border border-primary-foreground/20 bg-primary-foreground/10 px-1.5 py-0.5 text-[10px]">
                  ↵
                </kbd>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const [assistantMode, setAssistantMode] = useState(false);
  const [parseResult, setParseResult] = useState<AssistantParseResponse | null>(null);
  const parseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  // ── Assistant mutations ──
  const parseMutation = useParseAssistant();
  const commitMutation = useCommitAssistant();

  // ── Derived ──
  const assistantText = assistantMode ? searchValue.trim() : "";

  // ── Keyboard shortcut: Ctrl+K ──
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // ── Custom event: sidebar search button ──
  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener("open-command-palette", handler);
    return () => window.removeEventListener("open-command-palette", handler);
  }, []);

  // ── Reset state on close ──
  useEffect(() => {
    if (open) return;

    const rafId = requestAnimationFrame(() => {
      setHighlighted("");
      setSearchValue("");
      setAssistantMode(false);
      setParseResult(null);
    });

    return () => cancelAnimationFrame(rafId);
  }, [open]);

  // ── Search input handler — detects ">" to enter assistant mode ──
  const handleSearchChange = useCallback(
    (value: string) => {
      if (!assistantMode) {
        if (value === ">") {
          setAssistantMode(true);
          setSearchValue("");
          return;
        }
        if (value.startsWith(">")) {
          setAssistantMode(true);
          setSearchValue(value.slice(1).trimStart());
          return;
        }
      }
      setSearchValue(value);
    },
    [assistantMode],
  );

  // ── Enter assistant mode from suggestion chip ──
  const enterAssistant = useCallback((text: string) => {
    setAssistantMode(true);
    setSearchValue(text);
  }, []);

  // ── Backspace on empty input exits assistant mode ──
  useEffect(() => {
    if (!open || !assistantMode) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Backspace" && searchValue === "") {
        setAssistantMode(false);
        setParseResult(null);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, assistantMode, searchValue]);

  // ── Debounced parse in assistant mode ──
  useEffect(() => {
    if (parseTimerRef.current) clearTimeout(parseTimerRef.current);

    if (!assistantMode || assistantText.length < 3) {
      const rafId = requestAnimationFrame(() => setParseResult(null));
      return () => cancelAnimationFrame(rafId);
    }

    parseTimerRef.current = setTimeout(() => {
      parseMutation.mutate(
        { text: assistantText },
        { onSuccess: (data) => setParseResult(data) },
      );
    }, 300);

    return () => {
      if (parseTimerRef.current) clearTimeout(parseTimerRef.current);
    };
  }, [assistantText, assistantMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Enter to commit in assistant mode ──
  const handleCommit = useCallback(
    (op: ParsedOperation) => {
      commitMutation.mutate(
        { intent: op.intent, payload: op.payload },
        {
          onSuccess: (data) => {
            setOpen(false);
            if (data.navigate_to) {
              router.push(data.navigate_to);
            }
          },
        },
      );
    },
    [commitMutation, router],
  );

  useEffect(() => {
    if (!open || !assistantMode || !parseResult?.success) return;

    const op = parseResult.operations[0];
    if (!op || op.confidence < 0.4 || parseResult.ambiguities.length > 0) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
        if (!commitMutation.isPending) {
          e.preventDefault();
          e.stopPropagation();
          handleCommit(op);
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown, true);
    return () => document.removeEventListener("keydown", handleKeyDown, true);
  }, [open, assistantMode, parseResult, commitMutation.isPending]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Lazy data: clienti ──
  const { data: clientsData } = useQuery<ClientEnrichedListResponse>({
    queryKey: ["clients"],
    queryFn: async () => {
      const { data } = await apiClient.get<ClientEnrichedListResponse>("/clients", {
        params: { page: 1, page_size: 200 },
      });
      return data;
    },
    enabled: open,
    staleTime: 30_000,
  });

  // ── Lazy data: esercizi ──
  const { data: exercisesData } = useQuery<ExerciseListResponse>({
    queryKey: ["exercises", undefined],
    queryFn: async () => {
      const { data } = await apiClient.get<ExerciseListResponse>("/exercises", {
        params: { page: 1, page_size: 1200 },
      });
      return data;
    },
    enabled: open,
    staleTime: 30_000,
  });

  // ── Lazy data: dashboard KPI ──
  const { data: summary } = useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary");
      return data;
    },
    enabled: open,
    staleTime: 30_000,
  });

  const { data: stats } = useQuery<MovementStats>({
    queryKey: ["movement-stats", { anno: ANNO, mese: MESE }],
    queryFn: async () => {
      const { data } = await apiClient.get<MovementStats>(
        `/movements/stats?anno=${ANNO}&mese=${MESE}`,
      );
      return data;
    },
    enabled: open,
    staleTime: 30_000,
  });

  const clients = clientsData?.items ?? [];
  const exercises = exercisesData?.items ?? [];

  // ── Client/Exercise lookup maps ──
  const clientMap = useMemo(
    () => new Map(clients.map((c) => [`client-${c.id}`, c])),
    [clients],
  );
  const exerciseMap = useMemo(
    () => new Map(exercises.map((e) => [`exercise-${e.id}`, e])),
    [exercises],
  );

  // ── Resolve preview (search mode only) ──
  const preview = useMemo((): PreviewData => {
    if (assistantMode) return null;
    if (!highlighted) return null;
    const client = clientMap.get(highlighted);
    if (client) return { type: "client", data: client };
    const exercise = exerciseMap.get(highlighted);
    if (exercise) return { type: "exercise", data: exercise };
    if (highlighted.startsWith("kpi-")) return { type: "kpi" };
    return null;
  }, [highlighted, clientMap, exerciseMap, assistantMode]);

  // ── Navigate + close ──
  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router],
  );

  // ── Contextual: detect current page entity ──
  const contextClient = useMemo(() => {
    const match = pathname.match(/^\/clienti\/(\d+)/);
    if (!match) return null;
    return clients.find((c) => c.id === Number(match[1])) ?? null;
  }, [pathname, clients]);

  // ── Context-aware assistant suggestions ──
  const contextSuggestions = useMemo(() => {
    if (contextClient) {
      return [
        { label: "Evento", example: `${contextClient.nome} domani alle 18 PT`, icon: Calendar },
        { label: "Misura", example: `${contextClient.nome} peso 80`, icon: Scale },
        { label: "Spesa", example: "spesa palestra 200 euro pos", icon: Wallet },
      ];
    }
    return [...ASSISTANT_EXAMPLES];
  }, [contextClient]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogHeader className="sr-only">
        <DialogTitle>Cerca</DialogTitle>
        <DialogDescription>Cerca clienti, esercizi, pagine...</DialogDescription>
      </DialogHeader>
      <DialogContent
        className={`gap-0 overflow-hidden p-0 ${assistantMode ? "max-w-2xl" : "max-w-3xl"}`}
        showCloseButton={false}
      >
        <Command
          value={highlighted}
          onValueChange={setHighlighted}
          shouldFilter={!assistantMode}
          className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group]]:px-2 [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-2.5"
        >
          <div className="flex">
            {/* ══ LEFT: Search + Results ══ */}
            <div className="flex min-w-0 flex-1 flex-col">
              {/* ── Assistant header bar ── */}
              {assistantMode && (
                <div className="flex items-center gap-2 border-b border-primary/10 bg-primary/5 px-4 py-2.5">
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <span className="text-xs font-semibold text-primary">Assistente</span>
                  <span className="hidden text-xs text-muted-foreground sm:inline">
                    — scrivi un comando in italiano
                  </span>
                  <div className="ml-auto flex items-center gap-2">
                    {parseMutation.isPending && (
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-primary/60" />
                    )}
                    <kbd className="rounded border px-1.5 py-0.5 text-[9px] text-muted-foreground/60">
                      ← torna
                    </kbd>
                  </div>
                </div>
              )}

              {/* ── Input ── */}
              <CommandInput
                placeholder={
                  assistantMode
                    ? "Es: Marco domani alle 18 PT..."
                    : "Cerca clienti, esercizi, pagine..."
                }
                value={searchValue}
                onValueChange={handleSearchChange}
              />

              {/* ── Shimmer loading bar ── */}
              {assistantMode && parseMutation.isPending && (
                <div className="h-0.5 w-full animate-pulse bg-primary/40" />
              )}

              {/* ── Suggestion chips (assistant mode, before typing) ── */}
              {assistantMode && searchValue.length < 3 && !parseResult && (
                <div className="flex flex-wrap items-center gap-1.5 border-b px-4 py-2">
                  <span className="text-[10px] font-medium text-muted-foreground/50">
                    Prova:
                  </span>
                  {contextSuggestions.map((s) => (
                    <button
                      key={s.example}
                      type="button"
                      onClick={() => setSearchValue(s.example)}
                      className="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] text-muted-foreground transition-all hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
                    >
                      <s.icon className="h-3 w-3" />
                      {s.label}
                    </button>
                  ))}
                </div>
              )}

              <CommandList className="max-h-[400px]">
                {/* ══════ ASSISTANT MODE ══════ */}
                {assistantMode ? (
                  <>
                    {/* Guide: no text yet */}
                    {!parseResult && assistantText.length < 3 && (
                      <div className="px-6 py-6">
                        <div className="mb-4 text-center">
                          <Sparkles className="mx-auto mb-2 h-8 w-8 text-primary/20" />
                          <p className="text-sm font-medium text-foreground/70">
                            Cosa vuoi fare?
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground/60">
                            Scrivi un comando o scegli un esempio
                          </p>
                        </div>
                        <div className="space-y-1.5">
                          {contextSuggestions.map((s) => (
                            <button
                              key={s.example}
                              type="button"
                              onClick={() => setSearchValue(s.example)}
                              className="flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-all hover:border-primary/20 hover:bg-primary/5"
                            >
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                <s.icon className="h-4 w-4 text-primary" />
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-xs font-medium">{s.label}</p>
                                <p className="truncate text-[11px] text-muted-foreground">
                                  &ldquo;{s.example}&rdquo;
                                </p>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Parsing... */}
                    {assistantText.length >= 3 && !parseResult && parseMutation.isPending && (
                      <div className="flex items-center justify-center gap-2 px-4 py-10">
                        <Loader2 className="h-5 w-5 animate-spin text-primary/40" />
                        <span className="text-sm text-muted-foreground">Analizzo...</span>
                      </div>
                    )}

                    {/* Result card */}
                    {parseResult?.success && parseResult.operations.length > 0 && (
                      <div className="p-3">
                        <AssistantResultCard
                          operation={parseResult.operations[0]}
                          entities={parseResult.entities}
                          ambiguities={parseResult.ambiguities}
                          onCommit={() => handleCommit(parseResult.operations[0])}
                          isCommitting={commitMutation.isPending}
                        />
                      </div>
                    )}

                    {/* Parse failure */}
                    {parseResult && !parseResult.success && (
                      <div className="px-6 py-8 text-center">
                        <p className="text-sm text-muted-foreground">
                          {parseResult.message}
                        </p>
                        <p className="mt-2 text-xs text-muted-foreground/50">
                          Prova: &ldquo;Marco domani alle 18 PT&rdquo;
                        </p>
                      </div>
                    )}

                    {/* Ambiguity resolution */}
                    {parseResult?.ambiguities.map((amb, i) => (
                      <div key={`amb-${i}`} className="border-t px-4 py-3">
                        <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                          <AlertTriangle className="h-3 w-3" />
                          {amb.message}
                        </p>
                        <div className="space-y-1">
                          {amb.candidates.map((c) => (
                            <button
                              key={c.value}
                              type="button"
                              onClick={() => {
                                const resolved = c.label;
                                const newText = searchValue.replace(
                                  new RegExp(amb.candidates[0]?.raw ?? "", "i"),
                                  resolved,
                                );
                                setSearchValue(newText);
                              }}
                              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs transition-colors hover:bg-muted"
                            >
                              <User className="h-3.5 w-3.5 text-muted-foreground" />
                              <span className="flex-1 text-left font-medium">{c.label}</span>
                              <span className="text-[10px] tabular-nums text-muted-foreground">
                                {Math.round(c.confidence * 100)}%
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </>
                ) : (
                <>
                {/* ══════ SEARCH MODE ══════ */}
                <CommandEmpty>Nessun risultato.</CommandEmpty>

                {/* ── Contestuale: azioni per il cliente corrente ── */}
                {contextClient && (
                  <>
                    <CommandGroup heading={`${contextClient.nome} ${contextClient.cognome}`}>
                      <CommandItem
                        value={`ctx-contratti-${contextClient.id}`}
                        onSelect={() => navigate(`/contratti?cliente=${contextClient.id}`)}
                      >
                        <FileText className="mr-2 h-4 w-4 text-muted-foreground" />
                        Contratti di {contextClient.nome}
                      </CommandItem>
                      <CommandItem
                        value={`ctx-new-contract-${contextClient.id}`}
                        onSelect={() => navigate(`/contratti?new=1&cliente=${contextClient.id}`)}
                      >
                        <FilePlus className="mr-2 h-4 w-4 text-muted-foreground" />
                        Nuovo contratto per {contextClient.nome}
                      </CommandItem>
                      <CommandItem
                        value={`ctx-session-${contextClient.id}`}
                        onSelect={() => navigate(`/agenda?newEvent=1&clientId=${contextClient.id}`)}
                      >
                        <CalendarPlus className="mr-2 h-4 w-4 text-muted-foreground" />
                        Nuova sessione con {contextClient.nome}
                      </CommandItem>
                      <CommandItem
                        value={`ctx-measurement-${contextClient.id}`}
                        onSelect={() => {
                          navigate(`/clienti/${contextClient.id}/misurazioni`);
                        }}
                      >
                        <Scale className="mr-2 h-4 w-4 text-muted-foreground" />
                        Registra misurazione per {contextClient.nome}
                      </CommandItem>
                      <CommandItem
                        value={`ctx-portale-${contextClient.id}`}
                        onSelect={() => navigate(`/monitoraggio/${contextClient.id}?from=clienti-${contextClient.id}`)}
                      >
                        <TrendingUp className="mr-2 h-4 w-4 text-muted-foreground" />
                        Monitoraggio di {contextClient.nome}
                      </CommandItem>
                      <CommandItem
                        value={`ctx-anamnesi-${contextClient.id}`}
                        onSelect={() => navigate(`/clienti/${contextClient.id}/anamnesi`)}
                      >
                        <HeartPulse className="mr-2 h-4 w-4 text-muted-foreground" />
                        Anamnesi di {contextClient.nome}
                      </CommandItem>
                    </CommandGroup>
                    <CommandSeparator />
                  </>
                )}

                {/* ── KPI: risposte dirette ── */}
                <CommandGroup heading="Dati Rapidi">
                  <CommandItem
                    value="kpi-entrate entrate incasso revenue mese"
                    onSelect={() => navigate("/cassa")}
                  >
                    <TrendingUp className="mr-2 h-4 w-4 text-emerald-500" />
                    <span>Entrate mese</span>
                    <span className="ml-auto text-sm font-bold tabular-nums text-emerald-600 dark:text-emerald-400">
                      {stats ? formatCurrency(stats.totale_entrate) : "..."}
                    </span>
                  </CommandItem>
                  <CommandItem
                    value="kpi-margine margine profitto netto guadagno"
                    onSelect={() => navigate("/cassa")}
                  >
                    <Activity className="mr-2 h-4 w-4 text-blue-500" />
                    <span>Margine netto</span>
                    <span className={`ml-auto text-sm font-bold tabular-nums ${
                      stats && stats.margine_netto >= 0
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-red-600 dark:text-red-400"
                    }`}>
                      {stats ? formatCurrency(stats.margine_netto) : "..."}
                    </span>
                  </CommandItem>
                  <CommandItem
                    value="kpi-rate rate scadute pendenti pagamenti"
                    onSelect={() => navigate("/")}
                  >
                    <AlertTriangle className="mr-2 h-4 w-4 text-amber-500" />
                    <span>Rate pendenti</span>
                    <span className="ml-auto text-sm font-bold tabular-nums text-amber-600 dark:text-amber-400">
                      {summary ? summary.pending_rates : "..."}
                    </span>
                  </CommandItem>
                  <CommandItem
                    value="kpi-oggi appuntamenti sessioni oggi"
                    onSelect={() => navigate("/agenda")}
                  >
                    <CalendarCheck className="mr-2 h-4 w-4 text-violet-500" />
                    <span>Appuntamenti oggi</span>
                    <span className="ml-auto text-sm font-bold tabular-nums text-violet-600 dark:text-violet-400">
                      {summary ? summary.todays_appointments : "..."}
                    </span>
                  </CommandItem>
                </CommandGroup>

                <CommandSeparator />

                {/* ── Navigazione ── */}
                <CommandGroup heading="Pagine">
                  {NAV_ITEMS.map((item) => (
                    <CommandItem
                      key={item.id}
                      value={item.id}
                      onSelect={() => navigate(item.href)}
                    >
                      <item.icon className="mr-2 h-4 w-4 text-muted-foreground" />
                      {item.label}
                    </CommandItem>
                  ))}
                </CommandGroup>

                <CommandSeparator />

                {/* ── Clienti (dinamico) ── */}
                {clients.length > 0 && (
                  <CommandGroup heading="Clienti">
                    {clients.map((c) => (
                      <CommandItem
                        key={`client-${c.id}`}
                        value={`client-${c.id}`}
                        keywords={[c.nome, c.cognome, c.email ?? "", c.telefono ?? ""]}
                        onSelect={() => navigate(`/clienti/${c.id}`)}
                      >
                        <User className="mr-2 h-4 w-4 text-muted-foreground" />
                        <span className="flex-1 truncate">
                          {c.nome} {c.cognome}
                        </span>
                        {c.ha_rate_scadute && (
                          <AlertTriangle className="h-3 w-3 text-red-500" />
                        )}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                )}

                <CommandSeparator />

                {/* ── Esercizi (dinamico) ── */}
                {exercises.length > 0 && (
                  <CommandGroup heading="Esercizi">
                    {exercises.map((ex) => (
                      <CommandItem
                        key={`exercise-${ex.id}`}
                        value={`exercise-${ex.id}`}
                        keywords={[ex.nome, ex.nome_en ?? "", ex.categoria, ex.attrezzatura]}
                        onSelect={() => navigate(`/esercizi/${ex.id}`)}
                      >
                        <Dumbbell className="mr-2 h-4 w-4 text-muted-foreground" />
                        <span className="flex-1 truncate">{ex.nome}</span>
                        <span className="text-[10px] text-muted-foreground">
                          {ex.categoria}
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                )}

                <CommandSeparator />

                {/* ── Azioni rapide ── */}
                <CommandGroup heading="Azioni">
                  {ACTIONS.map((action) => (
                    <CommandItem
                      key={action.id}
                      value={action.id}
                      onSelect={() => navigate(action.href)}
                    >
                      <action.icon className="mr-2 h-4 w-4 text-muted-foreground" />
                      {action.label}
                      <CommandShortcut>Azione</CommandShortcut>
                    </CommandItem>
                  ))}
                </CommandGroup>

                <CommandSeparator />

                {/* ── Assistente: discovery section ── */}
                <CommandGroup heading="Assistente">
                  {ASSISTANT_EXAMPLES.map((s) => (
                    <CommandItem
                      key={`assistant-${s.label}`}
                      value={`assistant-${s.label} ${s.example} assistente comando`}
                      onSelect={() => enterAssistant(s.example)}
                    >
                      <Sparkles className="mr-2 h-4 w-4 text-primary/50" />
                      <span className="flex-1">
                        {s.label}:
                        <span className="ml-1.5 text-muted-foreground">
                          &ldquo;{s.example}&rdquo;
                        </span>
                      </span>
                      <CommandShortcut>&gt;</CommandShortcut>
                    </CommandItem>
                  ))}
                </CommandGroup>
                </>
                )}
              </CommandList>
            </div>

            {/* ══ RIGHT: Preview Panel (search mode only) ══ */}
            {!assistantMode && (
              <div className="hidden w-72 border-l bg-muted/30 p-4 md:block">
                {preview?.type === "client" && (
                  <ClientPreview client={preview.data} />
                )}
                {preview?.type === "exercise" && (
                  <ExercisePreview exercise={preview.data} />
                )}
                {preview?.type === "kpi" && (
                  <KpiPreview summary={summary} stats={stats} />
                )}
                {!preview && (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <Dumbbell className="mb-3 h-8 w-8 text-muted-foreground/30" />
                    <p className="text-xs text-muted-foreground/50">
                      Seleziona un elemento per vedere l&apos;anteprima
                    </p>
                    <p className="mt-3 text-[10px] text-muted-foreground/40">
                      Digita <span className="rounded border bg-muted px-1.5 py-0.5 font-mono font-bold">&gt;</span> per l&apos;assistente
                    </p>
                    <kbd className="mt-3 rounded border bg-muted px-2 py-1 text-[10px] font-medium text-muted-foreground">
                      Ctrl K
                    </kbd>
                  </div>
                )}
              </div>
            )}
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
