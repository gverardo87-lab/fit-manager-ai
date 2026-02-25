// src/components/dashboard/TodoCard.tsx
"use client";

/**
 * TodoCard — card promemoria per la Dashboard.
 *
 * Design:
 * - Inline input per creazione rapida (titolo + invio)
 * - Lista todo con checkbox toggle + colori urgenza
 * - Scaduti = rosso, oggi = ambra, futuri/senza data = default
 * - Completati in fondo, barrati, opacity ridotta
 * - Delete via X button on hover
 */

import { useState, useRef, type KeyboardEvent } from "react";
import { Plus, Trash2, ListTodo, Check, CalendarDays } from "lucide-react";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTodos, useCreateTodo, useToggleTodo, useDeleteTodo } from "@/hooks/useTodos";
import { formatShortDate } from "@/lib/format";
import type { Todo } from "@/types/api";

// ── Urgency colors based on scadenza ──

function getUrgencyClass(todo: Todo): string {
  if (todo.completato) return "text-muted-foreground/50 line-through";
  if (!todo.data_scadenza) return "";

  const today = new Date().toISOString().slice(0, 10);
  if (todo.data_scadenza < today) return "text-red-600 dark:text-red-400";
  if (todo.data_scadenza === today) return "text-amber-600 dark:text-amber-400";
  return "";
}

function getDateBadgeClass(todo: Todo): string {
  if (todo.completato) return "bg-muted text-muted-foreground/50";
  if (!todo.data_scadenza) return "";

  const today = new Date().toISOString().slice(0, 10);
  if (todo.data_scadenza < today) return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  if (todo.data_scadenza === today) return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-muted text-muted-foreground";
}

// ── Component ──

export function TodoCard() {
  const { data, isLoading } = useTodos();
  const createTodo = useCreateTodo();
  const toggleTodo = useToggleTodo();
  const deleteTodo = useDeleteTodo();

  const [newTitle, setNewTitle] = useState("");
  const [newDate, setNewDate] = useState("");
  const [showDateInput, setShowDateInput] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleCreate = () => {
    const titolo = newTitle.trim();
    if (!titolo) return;
    createTodo.mutate({ titolo, data_scadenza: newDate || undefined });
    setNewTitle("");
    setNewDate("");
    setShowDateInput(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleCreate();
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border p-5 space-y-4">
        <Skeleton className="h-5 w-40" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  const todos = data?.items ?? [];

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <ListTodo className="h-4 w-4 text-pink-500" />
        <h3 className="text-sm font-semibold">Promemoria</h3>
        {todos.length > 0 && (
          <span className="ml-auto text-[10px] font-medium text-muted-foreground">
            {todos.filter((t) => !t.completato).length} attivi
          </span>
        )}
      </div>

      {/* Inline create */}
      <div className="mb-3 space-y-2">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nuovo promemoria..."
            className="h-8 text-sm"
            maxLength={200}
          />
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "h-8 w-8 shrink-0",
              showDateInput && "text-pink-500"
            )}
            onClick={() => setShowDateInput((prev) => !prev)}
            title="Aggiungi scadenza"
          >
            <CalendarDays className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 shrink-0"
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
            className="h-8 text-sm"
          />
        )}
      </div>

      {/* Todo list */}
      {todos.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed p-6 text-center">
          <ListTodo className="h-8 w-8 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">Nessun promemoria</p>
          <p className="text-xs text-muted-foreground/70">
            Aggiungi un promemoria qui sopra
          </p>
        </div>
      ) : (
        <ScrollArea className={todos.length > 6 ? "h-[240px]" : ""}>
          <div className="space-y-1.5">
            {todos.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
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

// ── Single Todo Item ──

function TodoItem({
  todo,
  onToggle,
  onDelete,
}: {
  todo: Todo;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const urgencyClass = getUrgencyClass(todo);
  const dateBadgeClass = getDateBadgeClass(todo);

  const isOverdue = !todo.completato && !!todo.data_scadenza &&
    todo.data_scadenza < new Date().toISOString().slice(0, 10);
  const isToday = !todo.completato && !!todo.data_scadenza &&
    todo.data_scadenza === new Date().toISOString().slice(0, 10);

  const containerClass = todo.completato
    ? "bg-muted/30 opacity-60 border"
    : isOverdue
      ? "border border-l-4 border-l-red-500 bg-red-50/60 dark:bg-red-950/20"
      : isToday
        ? "border border-l-4 border-l-amber-500 bg-amber-50/60 dark:bg-amber-950/20"
        : "border bg-white dark:bg-zinc-900";

  return (
    <div
      className={`group flex items-center gap-2 rounded-lg px-3 py-2 transition-all hover:shadow-sm ${containerClass}`}
    >
      {/* Checkbox toggle */}
      <button
        onClick={onToggle}
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors ${
          todo.completato
            ? "border-emerald-500 bg-emerald-500 text-white"
            : "border-muted-foreground/30 hover:border-emerald-400"
        }`}
      >
        {todo.completato && <Check className="h-3 w-3" />}
      </button>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className={`truncate text-sm font-medium ${urgencyClass}`}>
          {todo.titolo}
        </p>
      </div>

      {/* Date badge */}
      {todo.data_scadenza && (
        <span className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium ${dateBadgeClass}`}>
          {formatShortDate(todo.data_scadenza, false)}
        </span>
      )}

      {/* Delete button (visible on hover) */}
      <button
        onClick={onDelete}
        className="shrink-0 rounded p-1 text-muted-foreground/30 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
