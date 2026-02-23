// src/components/movements/RecurringExpensesTab.tsx
"use client";

/**
 * Tab Spese Fisse — gestione spese ricorrenti con categorie predefinite.
 *
 * Funzionalita':
 * - Form inline per aggiungere (con categoria + 5 frequenze)
 * - Tabella con colonna Categoria, edit inline, toggle, delete con conferma
 * - Edit Dialog (pattern RateEditDialog) per modifiche senza ricreare
 * - Totale mensile KPI
 */

import { useState, useEffect } from "react";
import {
  Loader2,
  Plus,
  Trash2,
  Power,
  PowerOff,
  CalendarClock,
  Pencil,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  useRecurringExpenses,
  useCreateRecurringExpense,
  useUpdateRecurringExpense,
  useDeleteRecurringExpense,
} from "@/hooks/useRecurringExpenses";
import { Skeleton } from "@/components/ui/skeleton";
import type { RecurringExpense, ExpenseFrequency } from "@/types/api";
import { EXPENSE_CATEGORIES, EXPENSE_FREQUENCIES } from "@/types/api";
import { formatCurrency } from "@/lib/format";

// ── Costanti ──

const FREQUENZA_LABELS: Record<string, string> = {
  MENSILE: "Mensile",
  SETTIMANALE: "Settimanale",
  TRIMESTRALE: "Trimestrale",
  SEMESTRALE: "Semestrale",
  ANNUALE: "Annuale",
};

// ── Main ──

export function RecurringExpensesTab() {
  const { data, isLoading } = useRecurringExpenses();
  const expenses = data?.items ?? [];

  return (
    <div className="space-y-6">
      <AddExpenseForm />

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

// ════════════════════════════════════════════════════════════
// FORM INLINE — Aggiungi spesa (S2: categoria, S4: 5 frequenze, S6: predefinite)
// ════════════════════════════════════════════════════════════

function AddExpenseForm() {
  const [nome, setNome] = useState("");
  const [importo, setImporto] = useState("");
  const [giorno, setGiorno] = useState("1");
  const [frequenza, setFrequenza] = useState<ExpenseFrequency>("MENSILE");
  const [categoria, setCategoria] = useState("");

  const createMutation = useCreateRecurringExpense();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome.trim() || !importo) return;

    createMutation.mutate(
      {
        nome: nome.trim(),
        importo: parseFloat(importo),
        giorno_scadenza: parseInt(giorno, 10) || 1,
        frequenza,
        categoria: categoria || null,
      },
      {
        onSuccess: () => {
          setNome("");
          setImporto("");
          setGiorno("1");
          setFrequenza("MENSILE");
          setCategoria("");
        },
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border bg-zinc-50/50 p-4 dark:bg-zinc-800/30">
      <p className="mb-3 text-sm font-semibold">Aggiungi Spesa Fissa</p>
      <div className="flex items-end gap-3 flex-wrap">
        <div className="flex-1 min-w-[150px] space-y-1.5">
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
        <div className="w-36 space-y-1.5">
          <Label className="text-xs">Categoria</Label>
          <Select value={categoria} onValueChange={setCategoria}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder="Seleziona..." />
            </SelectTrigger>
            <SelectContent>
              {EXPENSE_CATEGORIES.map((c) => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
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
        <div className="w-36 space-y-1.5">
          <Label className="text-xs">Frequenza</Label>
          <Select value={frequenza} onValueChange={(v) => setFrequenza(v as ExpenseFrequency)}>
            <SelectTrigger className="h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {EXPENSE_FREQUENCIES.map((f) => (
                <SelectItem key={f} value={f}>
                  {FREQUENZA_LABELS[f] ?? f}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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

// ════════════════════════════════════════════════════════════
// EDIT DIALOG — S1: modifica spesa senza ricreare (pattern RateEditDialog)
// ════════════════════════════════════════════════════════════

function ExpenseEditDialog({
  expense,
  open,
  onOpenChange,
}: {
  expense: RecurringExpense | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [nome, setNome] = useState("");
  const [importo, setImporto] = useState("");
  const [giorno, setGiorno] = useState("1");
  const [frequenza, setFrequenza] = useState<ExpenseFrequency>("MENSILE");
  const [categoria, setCategoria] = useState("");

  const updateMutation = useUpdateRecurringExpense();

  // Sync state da props quando il dialog si apre
  useEffect(() => {
    if (expense && open) {
      setNome(expense.nome);
      setImporto(String(expense.importo));
      setGiorno(String(expense.giorno_scadenza));
      setFrequenza(expense.frequenza);
      setCategoria(expense.categoria ?? "");
    }
  }, [expense, open]);

  const handleSave = () => {
    if (!expense || !nome.trim() || !importo) return;

    updateMutation.mutate(
      {
        id: expense.id,
        nome: nome.trim(),
        importo: parseFloat(importo),
        giorno_scadenza: parseInt(giorno, 10) || 1,
        frequenza,
        categoria: categoria || null,
      },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Modifica Spesa Ricorrente</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label>Nome</Label>
            <Input value={nome} onChange={(e) => setNome(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Importo</Label>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={importo}
                onChange={(e) => setImporto(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Giorno del mese</Label>
              <Input
                type="number"
                min="1"
                max="31"
                value={giorno}
                onChange={(e) => setGiorno(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Categoria</Label>
            <Select value={categoria} onValueChange={setCategoria}>
              <SelectTrigger>
                <SelectValue placeholder="Seleziona..." />
              </SelectTrigger>
              <SelectContent>
                {EXPENSE_CATEGORIES.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Frequenza</Label>
            <Select value={frequenza} onValueChange={(v) => setFrequenza(v as ExpenseFrequency)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPENSE_FREQUENCIES.map((f) => (
                  <SelectItem key={f} value={f}>
                    {FREQUENZA_LABELS[f] ?? f}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annulla
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending || !nome.trim() || !importo}
          >
            {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Salva
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════
// TABELLA — S1: edit, S2: colonna categoria, S3: delete confirm
// ════════════════════════════════════════════════════════════

function formatDisattivazione(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" });
}

function ExpensesTable({ expenses }: { expenses: RecurringExpense[] }) {
  const updateMutation = useUpdateRecurringExpense();
  const deleteMutation = useDeleteRecurringExpense();

  // S1: Edit dialog state
  const [editTarget, setEditTarget] = useState<RecurringExpense | null>(null);

  // S3: Delete confirm state
  const [deleteTarget, setDeleteTarget] = useState<RecurringExpense | null>(null);

  const handleToggle = (expense: RecurringExpense) => {
    updateMutation.mutate({ id: expense.id, attiva: !expense.attiva });
  };

  const handleConfirmDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget.id, {
      onSuccess: () => setDeleteTarget(null),
    });
  };

  return (
    <>
      <div className="rounded-lg border bg-white dark:bg-zinc-900">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead className="text-right">Importo</TableHead>
              <TableHead className="text-center">Categoria</TableHead>
              <TableHead className="text-center">Frequenza</TableHead>
              <TableHead className="text-center">Giorno</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="w-[130px]">Azioni</TableHead>
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
                <TableCell className="text-center text-xs text-muted-foreground">
                  {expense.categoria || "—"}
                </TableCell>
                <TableCell className="text-center text-xs text-muted-foreground">
                  {FREQUENZA_LABELS[expense.frequenza] ?? expense.frequenza}
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
                    <div className="flex flex-col items-center gap-0.5">
                      <Badge variant="secondary">Disattiva</Badge>
                      {expense.data_disattivazione && (
                        <span className="text-[10px] text-muted-foreground">
                          dal {formatDisattivazione(expense.data_disattivazione)}
                        </span>
                      )}
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setEditTarget(expense)}
                    >
                      <Pencil className="h-4 w-4 text-blue-500" />
                    </Button>
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
                      onClick={() => setDeleteTarget(expense)}
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

      {/* S1: Edit Dialog */}
      <ExpenseEditDialog
        expense={editTarget}
        open={editTarget !== null}
        onOpenChange={(open) => { if (!open) setEditTarget(null); }}
      />

      {/* S3: Delete Confirm Dialog */}
      <AlertDialog open={deleteTarget !== null} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare questa spesa ricorrente?</AlertDialogTitle>
            <AlertDialogDescription>
              Stai per eliminare{" "}
              <span className="font-semibold">{deleteTarget?.nome}</span>
              {" "}({deleteTarget ? formatCurrency(deleteTarget.importo) : ""}).
              Questa azione non puo&apos; essere annullata.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>Annulla</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={deleteMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
