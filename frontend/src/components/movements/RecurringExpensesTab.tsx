// src/components/movements/RecurringExpensesTab.tsx
"use client";

/**
 * Tab Spese Fisse — Paradigma "Conferma & Registra".
 *
 * Funzionalita':
 * - PendingExpensesBanner: alert spese in attesa di conferma per il mese
 * - Form inline per aggiungere (con categoria, 5 frequenze, data_inizio)
 * - Tabella con colonna Categoria, edit inline, toggle, delete con conferma
 * - Edit Dialog (pattern RateEditDialog) con data_inizio
 * - Stima Mensile KPI pesata per frequenza
 */

import { useState, useEffect } from "react";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  Loader2,
  Plus,
  Trash2,
  Power,
  PowerOff,
  CalendarClock,
  Pencil,
  AlertTriangle,
  CheckCircle2,
  Building2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import { DatePicker } from "@/components/ui/date-picker";
import {
  useRecurringExpenses,
  useCreateRecurringExpense,
  useUpdateRecurringExpense,
  useDeleteRecurringExpense,
} from "@/hooks/useRecurringExpenses";
import {
  usePendingExpenses,
  useConfirmExpenses,
} from "@/hooks/useMovements";
import { Skeleton } from "@/components/ui/skeleton";
import type { RecurringExpense, ExpenseFrequency, PendingExpenseItem } from "@/types/api";
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

const MESI_NOMI = [
  "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
  "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
];

// ── Helpers ──

/** Stima mensile pesata per frequenza */
function estimateMonthly(expense: RecurringExpense): number {
  switch (expense.frequenza) {
    case "SETTIMANALE": return expense.importo * 4.33;
    case "TRIMESTRALE": return expense.importo / 3;
    case "SEMESTRALE": return expense.importo / 6;
    case "ANNUALE": return expense.importo / 12;
    default: return expense.importo; // MENSILE
  }
}

/** ISO string "YYYY-MM-DD" → Date locale */
function isoToDate(iso: string | null | undefined): Date | undefined {
  if (!iso) return undefined;
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Date → ISO string "YYYY-MM-DD" */
function dateToIso(d: Date | undefined): string | null {
  if (!d) return null;
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

// ── Props ──

interface RecurringExpensesTabProps {
  anno: number;
  mese: number;
}

// ── Main ──

export function RecurringExpensesTab({ anno, mese }: RecurringExpensesTabProps) {
  const { data, isLoading } = useRecurringExpenses();
  const expenses = data?.items ?? [];

  return (
    <div className="space-y-6">
      <PendingExpensesBanner anno={anno} mese={mese} />

      <AddExpenseForm />

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!isLoading && expenses.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-16">
          <CalendarClock className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">
            Nessuna spesa ricorrente configurata
          </p>
          <p className="mt-1 text-xs text-muted-foreground/70">
            Aggiungi la prima spesa fissa con il form qui sopra
          </p>
        </div>
      )}

      {expenses.length > 0 && <ExpensesTable expenses={expenses} />}

      {expenses.length > 0 && (
        <div className="flex items-center justify-between rounded-xl border border-l-4 border-l-red-500 bg-gradient-to-r from-red-50/50 to-white px-5 py-4 dark:from-red-950/20 dark:to-zinc-900">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30">
              <Building2 className="h-4 w-4 text-red-600 dark:text-red-400" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">
              Stima Mensile Spese Fisse
            </span>
          </div>
          <span className="text-xl font-bold text-red-700 dark:text-red-400">
            {formatCurrency(
              expenses.filter((e) => e.attiva).reduce((sum, e) => sum + estimateMonthly(e), 0)
            )}
          </span>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PENDING BANNER — Spese in attesa di conferma per il mese
// ════════════════════════════════════════════════════════════

function PendingExpensesBanner({ anno, mese }: { anno: number; mese: number }) {
  const { data, isLoading } = usePendingExpenses(anno, mese);
  const confirmMutation = useConfirmExpenses();
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const items = data?.items ?? [];

  // Chiave univoca per la selezione UI: id_spesa + mese_anno_key
  // mese_anno_key da solo non basta — piu' spese MENSILI nello stesso mese
  // hanno la stessa key "2026-02", il Set le collasserebbe in un unico elemento.
  const selKey = (i: PendingExpenseItem) => `${i.id_spesa}::${i.mese_anno_key}`;

  // Reset selezione quando cambia mese o dati
  useEffect(() => {
    if (items.length > 0) {
      setSelected(new Set(items.map(selKey)));
    } else {
      setSelected(new Set());
    }
  }, [items]);

  if (isLoading || items.length === 0) return null;

  const allSelected = selected.size === items.length;
  const noneSelected = selected.size === 0;
  const totaleSelezionato = items
    .filter((i) => selected.has(selKey(i)))
    .reduce((sum, i) => sum + i.importo, 0);

  const toggleItem = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(items.map(selKey)));
    }
  };

  const handleConfirm = () => {
    const toConfirm = items
      .filter((i) => selected.has(selKey(i)))
      .map((i) => ({ id_spesa: i.id_spesa, mese_anno_key: i.mese_anno_key }));
    if (toConfirm.length === 0) return;
    confirmMutation.mutate(toConfirm);
  };

  return (
    <div className="rounded-xl border border-l-4 border-amber-200 border-l-amber-500 bg-gradient-to-r from-amber-50/80 to-white p-4 dark:border-amber-800/50 dark:border-l-amber-500 dark:from-amber-950/20 dark:to-zinc-900">
      <div className="mb-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
        <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">
          {items.length} {items.length === 1 ? "spesa in attesa" : "spese in attesa"} di conferma — {MESI_NOMI[mese]} {anno}
        </span>
      </div>

      <div className="space-y-2">
        {items.map((item) => (
          <PendingItemRow
            key={selKey(item)}
            item={item}
            checked={selected.has(selKey(item))}
            onToggle={() => toggleItem(selKey(item))}
          />
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={toggleAll}>
            {allSelected ? "Deseleziona tutte" : "Seleziona tutte"}
          </Button>
          <span className="text-sm text-muted-foreground">
            Totale selezionato: <span className="font-semibold">{formatCurrency(totaleSelezionato)}</span>
          </span>
        </div>
        <Button
          size="sm"
          onClick={handleConfirm}
          disabled={noneSelected || confirmMutation.isPending}
        >
          {confirmMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <CheckCircle2 className="mr-2 h-4 w-4" />
          )}
          Conferma selezionate
        </Button>
      </div>
    </div>
  );
}

function PendingItemRow({
  item,
  checked,
  onToggle,
}: {
  item: PendingExpenseItem;
  checked: boolean;
  onToggle: () => void;
}) {
  const dataPrevista = isoToDate(item.data_prevista);
  const dataLabel = dataPrevista
    ? format(dataPrevista, "d MMM", { locale: it })
    : "";

  return (
    <div className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 hover:bg-amber-100/60 dark:hover:bg-amber-900/20" onClick={onToggle}>
      <Checkbox
        checked={checked}
        onCheckedChange={onToggle}
        onClick={(e) => e.stopPropagation()}
      />
      <span className="flex-1 text-sm font-medium">{item.nome}</span>
      {item.categoria && (
        <span className="text-xs text-muted-foreground">{item.categoria}</span>
      )}
      <span className="w-24 text-right text-sm font-bold tabular-nums text-red-600 dark:text-red-400">
        {formatCurrency(item.importo)}
      </span>
      <span className="w-16 text-right text-xs text-muted-foreground">
        {dataLabel}
      </span>
      <span className="w-24 text-right text-xs text-muted-foreground">
        {FREQUENZA_LABELS[item.frequenza] ?? item.frequenza}
      </span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// FORM INLINE — Aggiungi spesa (con data_inizio)
// ════════════════════════════════════════════════════════════

function AddExpenseForm() {
  const [nome, setNome] = useState("");
  const [importo, setImporto] = useState("");
  const [giorno, setGiorno] = useState("1");
  const [frequenza, setFrequenza] = useState<ExpenseFrequency>("MENSILE");
  const [categoria, setCategoria] = useState("");
  const [dataInizio, setDataInizio] = useState<Date | undefined>(new Date());

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
        data_inizio: dateToIso(dataInizio),
      },
      {
        onSuccess: () => {
          setNome("");
          setImporto("");
          setGiorno("1");
          setFrequenza("MENSILE");
          setCategoria("");
          setDataInizio(new Date());
        },
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border bg-gradient-to-r from-zinc-50/80 to-white p-4 shadow-sm dark:from-zinc-800/30 dark:to-zinc-900">
      <div className="mb-3 flex items-center gap-2">
        <Plus className="h-4 w-4 text-muted-foreground" />
        <p className="text-sm font-semibold">Aggiungi Spesa Fissa</p>
      </div>
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
        <div className="w-44 space-y-1.5">
          <Label className="text-xs">Attiva dal</Label>
          <DatePicker
            value={dataInizio}
            onChange={setDataInizio}
            placeholder="Data inizio..."
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

// ════════════════════════════════════════════════════════════
// EDIT DIALOG — modifica spesa con data_inizio (pattern RateEditDialog)
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
  const [dataInizio, setDataInizio] = useState<Date | undefined>();

  const updateMutation = useUpdateRecurringExpense();

  // Sync state da props quando il dialog si apre
  useEffect(() => {
    if (expense && open) {
      setNome(expense.nome);
      setImporto(String(expense.importo));
      setGiorno(String(expense.giorno_scadenza));
      setFrequenza(expense.frequenza);
      setCategoria(expense.categoria ?? "");
      setDataInizio(isoToDate(expense.data_inizio));
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
        data_inizio: dateToIso(dataInizio),
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

          <div className="space-y-1.5">
            <Label>Attiva dal</Label>
            <DatePicker
              value={dataInizio}
              onChange={setDataInizio}
              placeholder="Data inizio..."
            />
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
// TABELLA — edit, colonna categoria, delete confirm
// ════════════════════════════════════════════════════════════

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = isoToDate(iso);
  if (!d) return "";
  return format(d, "dd MMM yyyy", { locale: it });
}

function ExpensesTable({ expenses }: { expenses: RecurringExpense[] }) {
  const updateMutation = useUpdateRecurringExpense();
  const deleteMutation = useDeleteRecurringExpense();

  const [editTarget, setEditTarget] = useState<RecurringExpense | null>(null);
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
              <TableHead className="text-center">Attiva dal</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="w-[130px]">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {expenses.map((expense, idx) => (
              <TableRow
                key={expense.id}
                className={`transition-colors hover:bg-muted/50 ${!expense.attiva ? "opacity-50" : ""} ${idx % 2 !== 0 ? "bg-muted/20" : ""}`}
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
                  {expense.giorno_scadenza}°
                </TableCell>
                <TableCell className="text-center text-xs text-muted-foreground">
                  {formatDate(expense.data_inizio)}
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
                          dal {formatDate(expense.data_disattivazione)}
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

      {/* Edit Dialog */}
      <ExpenseEditDialog
        expense={editTarget}
        open={editTarget !== null}
        onOpenChange={(open) => { if (!open) setEditTarget(null); }}
      />

      {/* Delete Confirm Dialog */}
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
