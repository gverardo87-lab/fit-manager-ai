// src/components/layout/CommandPalette.tsx
"use client";

/**
 * Command Palette avanzata — Ctrl+K per aprire.
 *
 * 3 feature distintive:
 * 1. Preview Panel: pannello dati a destra con info live dell'elemento selezionato
 * 2. Risposte KPI: digiti "entrate" e vedi il numero senza navigare
 * 3. Azioni Contestuali: la palette sa dove sei e suggerisce azioni rilevanti
 *
 * Dati lazy-loaded via React Query (enabled: open).
 * Zero prop drilling — custom event per apertura da sidebar.
 */

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  User,
  FileText,
  Dumbbell,
  Wallet,
  Settings,
  UserPlus,
  FilePlus,
  CalendarPlus,
  TrendingUp,
  AlertTriangle,
  CalendarCheck,
  CreditCard,
  Activity,
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
import type {
  ClientEnriched,
  ClientEnrichedListResponse,
  Exercise,
  ExerciseListResponse,
  DashboardSummary,
  MovementStats,
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
  { id: "nav-cassa", href: "/cassa", label: "Cassa", icon: Wallet },
  { id: "nav-impostazioni", href: "/impostazioni", label: "Impostazioni", icon: Settings },
] as const;

const ACTIONS = [
  { id: "action-new-client", label: "Nuovo Cliente", icon: UserPlus, href: "/clienti?new=1" },
  { id: "action-new-contract", label: "Nuovo Contratto", icon: FilePlus, href: "/contratti?new=1" },
  { id: "action-new-session", label: "Nuova Sessione", icon: CalendarPlus, href: "/agenda" },
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
// TIPO PREVIEW
// ════════════════════════════════════════════════════════════

type PreviewData =
  | { type: "client"; data: ClientEnriched }
  | { type: "exercise"; data: Exercise }
  | { type: "kpi" }
  | null;

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState("");
  const router = useRouter();
  const pathname = usePathname();

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

  // Reset highlighted on close
  useEffect(() => {
    if (!open) setHighlighted("");
  }, [open]);

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

  // ── Resolve preview from highlighted value ──
  const preview = useMemo((): PreviewData => {
    if (!highlighted) return null;
    const client = clientMap.get(highlighted);
    if (client) return { type: "client", data: client };
    const exercise = exerciseMap.get(highlighted);
    if (exercise) return { type: "exercise", data: exercise };
    if (highlighted.startsWith("kpi-")) return { type: "kpi" };
    return null;
  }, [highlighted, clientMap, exerciseMap]);

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

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogHeader className="sr-only">
        <DialogTitle>Cerca</DialogTitle>
        <DialogDescription>Cerca clienti, esercizi, pagine...</DialogDescription>
      </DialogHeader>
      <DialogContent
        className="max-w-3xl gap-0 overflow-hidden p-0"
        showCloseButton={false}
      >
        <Command
          value={highlighted}
          onValueChange={setHighlighted}
          className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group]]:px-2 [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-2.5"
        >
          <div className="flex">
            {/* ══ LEFT: Search + Results ══ */}
            <div className="flex min-w-0 flex-1 flex-col">
              <CommandInput placeholder="Cerca clienti, esercizi, pagine..." />
              <CommandList className="max-h-[400px]">
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
                        onSelect={() => navigate(`/agenda?cliente=${contextClient.id}`)}
                      >
                        <CalendarPlus className="mr-2 h-4 w-4 text-muted-foreground" />
                        Nuova sessione con {contextClient.nome}
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
              </CommandList>
            </div>

            {/* ══ RIGHT: Preview Panel (solo desktop) ══ */}
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
                  <kbd className="mt-3 rounded border bg-muted px-2 py-1 text-[10px] font-medium text-muted-foreground">
                    Ctrl K
                  </kbd>
                </div>
              )}
            </div>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
