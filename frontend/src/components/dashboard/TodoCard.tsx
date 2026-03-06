// src/components/dashboard/TodoCard.tsx
"use client";

/**
 * TodoCard - post-it promemoria stile frigorifero.
 *
 * Design:
 * - Sfondo giallo post-it con angolo piegato
 * - Font handwritten (Caveat) per i todo
 * - Hero "Azione consigliata" con priorita deterministica
 * - Inline input per creazione rapida (titolo + invio)
 * - Lista todo ordinata per urgenza
 * - Scaduti = rosso, oggi = ambra, futuri = blu
 * - Completati in fondo, barrati, opacity ridotta
 * - Altezza fissa h-[480px] per allineamento con TodayAgenda
 */

import Link from "next/link";
import { useRef, useState, type KeyboardEvent } from "react";
import {
  AlertTriangle,
  BellRing,
  CalendarClock,
  CalendarDays,
  Check,
  ClipboardCheck,
  ListTodo,
  Plus,
  Sparkles,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useCreateTodo, useDeleteTodo, useTodos, useToggleTodo } from "@/hooks/useTodos";
import { formatShortDate } from "@/lib/format";
import type { Todo } from "@/types/api";

// Priority helpers

function formatLocalISODate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getTodoBucket(todo: Todo, todayISO: string): number {
  if (todo.completato) return 4;
  if (!todo.data_scadenza) return 3;
  if (todo.data_scadenza < todayISO) return 0;
  if (todo.data_scadenza === todayISO) return 1;
  return 2;
}

function sortTodosByPriority(todos: Todo[], todayISO: string): Todo[] {
  return [...todos].sort((a, b) => {
    const bucketDelta = getTodoBucket(a, todayISO) - getTodoBucket(b, todayISO);
    if (bucketDelta !== 0) return bucketDelta;

    if (a.data_scadenza && b.data_scadenza && a.data_scadenza !== b.data_scadenza) {
      return a.data_scadenza.localeCompare(b.data_scadenza);
    }

    if (a.created_at !== b.created_at) {
      return b.created_at.localeCompare(a.created_at);
    }

    return b.id - a.id;
  });
}

function getUrgencyClass(todo: Todo, todayISO: string): string {
  if (todo.completato) return "text-muted-foreground/50 line-through";
  if (!todo.data_scadenza) return "";

  if (todo.data_scadenza < todayISO) return "text-red-600 dark:text-red-400";
  if (todo.data_scadenza === todayISO) return "text-amber-600 dark:text-amber-400";
  return "";
}

function getDateBadgeClass(todo: Todo, todayISO: string): string {
  if (todo.completato) return "bg-muted text-muted-foreground/50";
  if (!todo.data_scadenza) return "";

  if (todo.data_scadenza < todayISO) return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  if (todo.data_scadenza === todayISO) return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
}

function scrollToAlertPanel(): void {
  const panel = document.getElementById("alert-panel");
  if (panel) panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

type TodoHeroMode =
  | "overdue"
  | "today"
  | "critical_alerts"
  | "warning_alerts"
  | "upcoming_sessions"
  | "free";

interface TodoHeroState {
  mode: TodoHeroMode;
  title: string;
  detail: string;
  primaryLabel: string;
  primaryHref?: string;
  targetTodoId?: number;
  icon: LucideIcon;
  panelTone: string;
  iconTone: string;
  titleTone: string;
}

interface TodoHeroContext {
  todayISO: string;
  todos: Todo[];
  overdueCount: number;
  dueTodayCount: number;
  criticalAlertCount: number;
  warningAlertCount: number;
  upcomingSessionsCount: number;
}

function buildTodoHeroState(ctx: TodoHeroContext): TodoHeroState {
  const firstOverdueTodo = ctx.todos.find(
    (todo) => !todo.completato && !!todo.data_scadenza && todo.data_scadenza < ctx.todayISO,
  );
  const firstDueTodayTodo = ctx.todos.find(
    (todo) => !todo.completato && !!todo.data_scadenza && todo.data_scadenza === ctx.todayISO,
  );

  if (ctx.overdueCount > 0) {
    return {
      mode: "overdue",
      title: ctx.overdueCount === 1 ? "1 promemoria scaduto da chiudere" : `${ctx.overdueCount} promemoria scaduti da chiudere`,
      detail: firstOverdueTodo
        ? `Priorita: ${firstOverdueTodo.titolo}`
        : "Chiudi i task scaduti prima delle prossime sessioni.",
      primaryLabel: "Completa prossimo",
      targetTodoId: firstOverdueTodo?.id,
      icon: AlertTriangle,
      panelTone: "border-red-200 bg-red-50/70 dark:border-red-900/40 dark:bg-red-950/20",
      iconTone: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
      titleTone: "text-red-700 dark:text-red-300",
    };
  }

  if (ctx.dueTodayCount > 0) {
    return {
      mode: "today",
      title: ctx.dueTodayCount === 1 ? "1 promemoria da chiudere oggi" : `${ctx.dueTodayCount} promemoria da chiudere oggi`,
      detail: firstDueTodayTodo
        ? `Prossimo task: ${firstDueTodayTodo.titolo}`
        : "Chiudi i task della giornata entro fine turno.",
      primaryLabel: "Completa prossimo",
      targetTodoId: firstDueTodayTodo?.id,
      icon: ClipboardCheck,
      panelTone: "border-amber-200 bg-amber-50/70 dark:border-amber-900/40 dark:bg-amber-950/20",
      iconTone: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
      titleTone: "text-amber-700 dark:text-amber-300",
    };
  }

  if (ctx.criticalAlertCount > 0) {
    return {
      mode: "critical_alerts",
      title: ctx.criticalAlertCount === 1 ? "1 alert critico operativo" : `${ctx.criticalAlertCount} alert critici operativi`,
      detail: "Apri il pannello alert e risolvi prima le criticita bloccanti.",
      primaryLabel: "Apri alert",
      icon: BellRing,
      panelTone: "border-red-200 bg-red-50/70 dark:border-red-900/40 dark:bg-red-950/20",
      iconTone: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
      titleTone: "text-red-700 dark:text-red-300",
    };
  }

  if (ctx.warningAlertCount > 0) {
    return {
      mode: "warning_alerts",
      title: ctx.warningAlertCount === 1 ? "1 avviso operativo da monitorare" : `${ctx.warningAlertCount} avvisi operativi da monitorare`,
      detail: "Non e bloccante, ma conviene chiuderli entro la giornata.",
      primaryLabel: "Apri alert",
      icon: BellRing,
      panelTone: "border-amber-200 bg-amber-50/70 dark:border-amber-900/40 dark:bg-amber-950/20",
      iconTone: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
      titleTone: "text-amber-700 dark:text-amber-300",
    };
  }

  if (ctx.upcomingSessionsCount > 0) {
    return {
      mode: "upcoming_sessions",
      title: ctx.upcomingSessionsCount === 1 ? "1 sessione imminente in agenda" : `${ctx.upcomingSessionsCount} sessioni imminenti in agenda`,
      detail: "Apri agenda e prepara i task pre-sessione.",
      primaryLabel: "Apri agenda",
      primaryHref: "/agenda",
      icon: CalendarClock,
      panelTone: "border-blue-200 bg-blue-50/70 dark:border-blue-900/40 dark:bg-blue-950/20",
      iconTone: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
      titleTone: "text-blue-700 dark:text-blue-300",
    };
  }

  return {
    mode: "free",
    title: "Nessuna urgenza operativa in corso",
    detail: "Crea un follow-up strategico per clienti inattivi o rinnovi in arrivo.",
    primaryLabel: "Aggiungi follow-up",
    icon: Sparkles,
    panelTone: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/40 dark:bg-emerald-950/20",
    iconTone: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
    titleTone: "text-emerald-700 dark:text-emerald-300",
  };
}

interface TodoCardProps {
  criticalAlertCount?: number;
  warningAlertCount?: number;
  upcomingSessionsCount?: number;
}

// Component

export function TodoCard({
  criticalAlertCount = 0,
  warningAlertCount = 0,
  upcomingSessionsCount = 0,
}: TodoCardProps = {}) {
  const { data, isLoading } = useTodos();
  const createTodo = useCreateTodo();
  const toggleTodo = useToggleTodo();
  const deleteTodo = useDeleteTodo();

  const [newTitle, setNewTitle] = useState("");
  const [newDate, setNewDate] = useState("");
  const [showDateInput, setShowDateInput] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const todayISO = formatLocalISODate(new Date());
  const todos = sortTodosByPriority(data?.items ?? [], todayISO);
  const activeCount = todos.filter((todo) => !todo.completato).length;
  const overdueCount = todos.filter(
    (todo) => !todo.completato && !!todo.data_scadenza && todo.data_scadenza < todayISO,
  ).length;
  const dueTodayCount = todos.filter(
    (todo) => !todo.completato && !!todo.data_scadenza && todo.data_scadenza === todayISO,
  ).length;
  const upcomingCount = todos.filter(
    (todo) => !todo.completato && !!todo.data_scadenza && todo.data_scadenza > todayISO,
  ).length;
  const hero = buildTodoHeroState({
    todayISO,
    todos,
    overdueCount,
    dueTodayCount,
    criticalAlertCount,
    warningAlertCount,
    upcomingSessionsCount,
  });

  const handleCreate = () => {
    const titolo = newTitle.trim();
    if (!titolo) return;
    createTodo.mutate({ titolo, data_scadenza: newDate || undefined });
    setNewTitle("");
    setNewDate("");
    setShowDateInput(false);
    inputRef.current?.focus();
  };

  const handleHeroPrimaryAction = () => {
    if ((hero.mode === "overdue" || hero.mode === "today") && hero.targetTodoId) {
      toggleTodo.mutate(hero.targetTodoId);
      return;
    }

    if (hero.mode === "critical_alerts" || hero.mode === "warning_alerts") {
      scrollToAlertPanel();
      return;
    }

    if (hero.mode === "free") {
      createTodo.mutate({
        titolo: "Follow-up clienti inattivi",
        data_scadenza: todayISO,
      });
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleCreate();
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[480px] flex-col space-y-4 rounded-xl border p-4 sm:p-5">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-24 w-full rounded-lg" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  const HeroIcon = hero.icon;
  const showAlertShortcut = criticalAlertCount + warningAlertCount > 0 &&
    hero.mode !== "critical_alerts" && hero.mode !== "warning_alerts";

  return (
    <div
      id="todo-panel"
      className="relative flex h-[480px] min-w-0 flex-col overflow-hidden rounded-2xl border-2 border-amber-300/70 bg-gradient-to-br from-amber-50 via-yellow-50/95 to-amber-100/70 p-4 shadow-[4px_6px_16px_-2px_rgba(0,0,0,0.10),_0_1px_3px_rgba(0,0,0,0.06)] sm:p-5 dark:border-amber-700/50 dark:from-amber-950/50 dark:via-zinc-900 dark:to-amber-900/30"
      style={{ backgroundImage: "repeating-linear-gradient(transparent, transparent 31px, rgba(180,160,120,0.10) 31px, rgba(180,160,120,0.10) 32px)" }}
    >
      {/* Angolo piegato post-it — con ombra sotto la piega */}
      <div className="pointer-events-none absolute right-0 top-0 h-12 w-12">
        <div className="absolute right-0 top-0 h-12 w-12 bg-gradient-to-bl from-amber-200/90 via-amber-100 to-yellow-50 dark:from-amber-800/60 dark:via-amber-900/50 dark:to-amber-950/40" style={{ clipPath: "polygon(100% 0, 0 0, 100% 100%)" }} />
        <div className="absolute right-0 top-0 h-12 w-12" style={{ clipPath: "polygon(100% 0, 0 0, 100% 100%)", boxShadow: "inset -3px 3px 6px rgba(0,0,0,0.10)" }} />
        <div className="absolute right-0 top-[48px] h-2 w-12 bg-gradient-to-r from-transparent via-black/[0.04] to-transparent dark:via-black/[0.15]" style={{ clipPath: "polygon(0 0, 100% 0, 85% 100%, 15% 100%)" }} />
      </div>

      {/* Puntina 3D — corpo metallico con riflesso e ombra proiettata */}
      <div className="pointer-events-none absolute left-5 top-3.5">
        {/* Ombra proiettata */}
        <div className="absolute left-0.5 top-1 h-5 w-5 rounded-full bg-black/10 blur-[2px] dark:bg-black/25" />
        {/* Corpo puntina */}
        <div className="relative flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-red-400 via-red-500 to-red-600 shadow-[0_1px_3px_rgba(0,0,0,0.3),inset_0_1px_1px_rgba(255,255,255,0.3)] dark:from-red-500 dark:via-red-600 dark:to-red-700">
          {/* Riflesso metallico */}
          <div className="absolute left-1 top-0.5 h-2 w-2.5 rounded-full bg-gradient-to-br from-white/50 to-transparent" />
          {/* Punto centrale */}
          <div className="h-1.5 w-1.5 rounded-full bg-red-800/40 dark:bg-red-900/50" />
        </div>
      </div>

      {/* Header */}
      <div className="mb-3 flex flex-wrap items-center gap-2 pl-7">
        <h3 className="font-[family-name:var(--font-caveat)] text-2xl font-bold text-amber-900/80 sm:text-3xl dark:text-amber-200/80">Promemoria</h3>
        {todos.length > 0 && (
          <span className="ml-auto font-[family-name:var(--font-caveat)] text-base font-semibold text-amber-700/60 dark:text-amber-400/60">
            {activeCount} attivi
          </span>
        )}
      </div>

      {/* Hero action */}
      <div className={`mb-3 shrink-0 rounded-lg border p-3 backdrop-blur-[1px] ${hero.panelTone}`}>
        <div className="flex min-w-0 items-start gap-2.5">
          <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${hero.iconTone}`}>
            <HeroIcon className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">Azione consigliata</p>
            <p className={`mt-0.5 text-sm font-semibold ${hero.titleTone}`}>{hero.title}</p>
            <p className="mt-1 text-xs text-muted-foreground">{hero.detail}</p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {hero.primaryHref ? (
            <Link href={hero.primaryHref}>
              <Button size="sm" className="h-8 text-xs">{hero.primaryLabel}</Button>
            </Link>
          ) : (
            <Button
              size="sm"
              className="h-8 text-xs"
              onClick={handleHeroPrimaryAction}
              disabled={toggleTodo.isPending || createTodo.isPending}
            >
              {hero.primaryLabel}
            </Button>
          )}
          {showAlertShortcut && (
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={scrollToAlertPanel}
            >
              Apri alert
            </Button>
          )}
        </div>
      </div>

      {/* Inline create */}
      <div className="mb-3 shrink-0 space-y-2">
        <div className="flex min-w-0 items-center gap-2">
          <Input
            ref={inputRef}
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Scrivi un promemoria..."
            className="h-10 border-amber-300/60 bg-white/60 font-[family-name:var(--font-caveat)] text-lg placeholder:font-sans placeholder:text-sm dark:border-amber-800/40 dark:bg-zinc-900/40"
            maxLength={200}
          />
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "h-8 w-8 shrink-0",
              showDateInput && "text-pink-500",
            )}
            onClick={() => setShowDateInput((prev) => !prev)}
            title="Aggiungi scadenza"
          >
            <CalendarDays className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 shrink-0 border-amber-300/60 dark:border-amber-800/40"
            onClick={handleCreate}
            disabled={!newTitle.trim() || createTodo.isPending}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {showDateInput && (
          <Input
            type="date"
            value={newDate}
            onChange={(e) => setNewDate(e.target.value)}
            className="h-8 border-amber-300/60 bg-white/60 text-sm dark:border-amber-800/40 dark:bg-zinc-900/40"
          />
        )}
      </div>

      {/* Priority counters */}
      {activeCount > 0 && (
        <div className="mb-3 grid shrink-0 grid-cols-3 gap-1.5">
          <div className="rounded-md border border-red-200 bg-red-50/80 px-2 py-1.5 text-center dark:border-red-900/40 dark:bg-red-950/20">
            <p className="text-base font-extrabold leading-none tabular-nums text-red-700 dark:text-red-300">
              {overdueCount}
            </p>
            <p className="mt-1 text-[10px] font-semibold tracking-wide text-red-700/80 uppercase dark:text-red-300/80">
              Scaduti
            </p>
          </div>
          <div className="rounded-md border border-amber-200 bg-amber-50/80 px-2 py-1.5 text-center dark:border-amber-900/40 dark:bg-amber-950/20">
            <p className="text-base font-extrabold leading-none tabular-nums text-amber-700 dark:text-amber-300">
              {dueTodayCount}
            </p>
            <p className="mt-1 text-[10px] font-semibold tracking-wide text-amber-700/80 uppercase dark:text-amber-300/80">
              Oggi
            </p>
          </div>
          <div className="rounded-md border border-blue-200 bg-blue-50/80 px-2 py-1.5 text-center dark:border-blue-900/40 dark:bg-blue-950/20">
            <p className="text-base font-extrabold leading-none tabular-nums text-blue-700 dark:text-blue-300">
              {upcomingCount}
            </p>
            <p className="mt-1 text-[10px] font-semibold tracking-wide text-blue-700/80 uppercase dark:text-blue-300/80">
              Prossimi
            </p>
          </div>
        </div>
      )}

      {/* Todo list — scrollable, fills remaining space */}
      {todos.length === 0 ? (
        <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-amber-300/50 p-6 text-center dark:border-amber-800/30">
          <ListTodo className="h-8 w-8 text-amber-400/40" />
          <p className="font-[family-name:var(--font-caveat)] text-2xl font-semibold text-amber-700/60 dark:text-amber-400/50">Nessun promemoria</p>
          <p className="text-xs text-muted-foreground/70">
            Scrivi qualcosa qui sopra
          </p>
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1 pr-1">
          <div className="space-y-1.5">
            {todos.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
                todayISO={todayISO}
                onToggle={() => toggleTodo.mutate(todo.id)}
                onDelete={() => deleteTodo.mutate(todo.id)}
              />
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

// Single Todo Item

function TodoItem({
  todo,
  todayISO,
  onToggle,
  onDelete,
}: {
  todo: Todo;
  todayISO: string;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const urgencyClass = getUrgencyClass(todo, todayISO);
  const dateBadgeClass = getDateBadgeClass(todo, todayISO);

  const isOverdue = !todo.completato && !!todo.data_scadenza &&
    todo.data_scadenza < todayISO;
  const isToday = !todo.completato && !!todo.data_scadenza &&
    todo.data_scadenza === todayISO;

  const containerClass = todo.completato
    ? "bg-amber-100/30 opacity-60 border border-amber-200/40 dark:bg-zinc-900/30 dark:border-amber-800/20"
    : isOverdue
      ? "border border-l-4 border-l-red-500 bg-red-50/60 dark:bg-red-950/20"
      : isToday
        ? "border border-l-4 border-l-amber-500 bg-amber-50/60 dark:bg-amber-950/20"
        : "border border-amber-200/50 bg-white/50 dark:border-amber-800/30 dark:bg-zinc-900/40";

  return (
    <div
      className={`group flex min-w-0 items-center gap-2 overflow-hidden rounded-lg px-3 py-2 transition-all hover:shadow-sm ${containerClass}`}
    >
      <button
        onClick={onToggle}
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors ${
          todo.completato
            ? "border-emerald-500 bg-emerald-500 text-white"
            : "border-amber-400/60 hover:border-emerald-400 dark:border-amber-600/40"
        }`}
      >
        {todo.completato && <Check className="h-3 w-3" />}
      </button>

      <div className="min-w-0 flex-1">
        <p className={`truncate font-[family-name:var(--font-caveat)] text-xl font-semibold leading-tight sm:text-2xl ${urgencyClass}`}>
          {todo.titolo}
        </p>
      </div>

      {todo.data_scadenza && (
        <span className={`max-w-[78px] shrink-0 truncate rounded px-1.5 py-0.5 text-[9px] font-medium ${dateBadgeClass}`}>
          {formatShortDate(todo.data_scadenza, false)}
        </span>
      )}

      <button
        onClick={onDelete}
        className="shrink-0 rounded p-1 text-muted-foreground/30 opacity-100 transition-opacity hover:text-red-500 sm:opacity-0 sm:group-hover:opacity-100"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
