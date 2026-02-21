// src/components/movements/RecurringExpensesTab.tsx
"use client";

/**
 * Tab Spese Fisse — gestione abbonamenti e spese ricorrenti mensili.
 *
 * Mini-form inline per aggiungere + tabellina con toggle attiva/disattiva
 * e bottone elimina. Contribuisce al calcolo del Margine Netto.
 */

import { useState } from "react";
import {
  Loader2,
  Plus,
  Trash2,
  Power,
  PowerOff,
  CalendarClock,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useRecurringExpenses,
  useCreateRecurringExpense,
  useUpdateRecurringExpense,
  useDeleteRecurringExpense,
} from "@/hooks/useRecurringExpenses";
import { Skeleton } from "@/components/ui/skeleton";
import type { RecurringExpense } from "@/types/api";

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

export function RecurringExpensesTab() {
  const { data, isLoading } = useRecurringExpenses();
  const expenses = data?.items ?? [];

  return (
    <div className="space-y-6">
      {/* ── Form inline per aggiungere ── */}
      <AddExpenseForm />

      {/* ── Tabella ── */}
      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!isLoading && expenses.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-10">
          <CalendarClock className="mb-2 h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Nessuna spesa ricorrente configurata
          </p>
        </div>
      )}

      {expenses.length > 0 && <ExpensesTable expenses={expenses} />}

      {/* ── Totale mensile ── */}
      {expenses.length > 0 && (
        <div className="flex items-center justify-between rounded-lg border bg-red-50/50 px-4 py-3 dark:bg-red-950/20">
          <span className="text-sm font-medium text-muted-foreground">
            Totale Spese Fisse Mensili
          </span>
          <span className="text-lg font-bold text-red-700 dark:text-red-400">
            {formatCurrency(
              expenses.filter((e) => e.attiva).reduce((sum, e) => sum + e.importo, 0)
            )}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Form inline ──

function AddExpenseForm() {
  const [nome, setNome] = useState("");
  const [importo, setImporto] = useState("");
  const [giorno, setGiorno] = useState("1");

  const createMutation = useCreateRecurringExpense();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome.trim() || !importo) return;

    createMutation.mutate(
      {
        nome: nome.trim(),
        importo: parseFloat(importo),
        giorno_scadenza: parseInt(giorno, 10) || 1,
      },
      {
        onSuccess: () => {
          setNome("");
          setImporto("");
          setGiorno("1");
        },
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border bg-zinc-50/50 p-4 dark:bg-zinc-800/30">
      <p className="mb-3 text-sm font-semibold">Aggiungi Spesa Fissa</p>
      <div className="flex items-end gap-3">
        <div className="flex-1 space-y-1.5">
          <Label className="text-xs">Nome</Label>
          <Input
            placeholder="es. Affitto Sala"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
          />
        </div>
        <div className="w-28 space-y-1.5">
          <Label className="text-xs">Importo</Label>
          <Input
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0,00"
            value={importo}
            onChange={(e) => setImporto(e.target.value)}
          />
        </div>
        <div className="w-20 space-y-1.5">
          <Label className="text-xs">Giorno</Label>
          <Input
            type="number"
            min="1"
            max="31"
            value={giorno}
            onChange={(e) => setGiorno(e.target.value)}
          />
        </div>
        <Button
          type="submit"
          size="sm"
          disabled={createMutation.isPending || !nome.trim() || !importo}
        >
          {createMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
        </Button>
      </div>
    </form>
  );
}

// ── Tabella spese ──

function ExpensesTable({ expenses }: { expenses: RecurringExpense[] }) {
  const updateMutation = useUpdateRecurringExpense();
  const deleteMutation = useDeleteRecurringExpense();

  const handleToggle = (expense: RecurringExpense) => {
    updateMutation.mutate({ id: expense.id, attiva: !expense.attiva });
  };

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead className="text-right">Importo</TableHead>
            <TableHead className="text-center">Giorno</TableHead>
            <TableHead className="text-center">Stato</TableHead>
            <TableHead className="w-[100px]">Azioni</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {expenses.map((expense) => (
            <TableRow
              key={expense.id}
              className={expense.attiva ? "" : "opacity-50"}
            >
              <TableCell className="font-medium">{expense.nome}</TableCell>
              <TableCell className="text-right font-bold tabular-nums text-red-600 dark:text-red-400">
                {formatCurrency(expense.importo)}
              </TableCell>
              <TableCell className="text-center text-sm text-muted-foreground">
                {expense.giorno_scadenza}° del mese
              </TableCell>
              <TableCell className="text-center">
                {expense.attiva ? (
                  <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
                    Attiva
                  </Badge>
                ) : (
                  <Badge variant="secondary">Disattiva</Badge>
                )}
              </TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleToggle(expense)}
                    disabled={updateMutation.isPending}
                  >
                    {expense.attiva ? (
                      <PowerOff className="h-4 w-4 text-amber-500" />
                    ) : (
                      <Power className="h-4 w-4 text-emerald-500" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => deleteMutation.mutate(expense.id)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
