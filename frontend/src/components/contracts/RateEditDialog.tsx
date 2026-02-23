// src/components/contracts/RateEditDialog.tsx
"use client";

/**
 * Dialog per modificare una rata esistente (tutte le rate).
 *
 * Campi modificabili: importo_previsto, data_scadenza, descrizione.
 * Rate con pagamenti: importo_previsto >= importo_saldato (validazione).
 */

import { useState, useEffect } from "react";
import { format, parseISO } from "date-fns";
import { Loader2, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DatePicker } from "@/components/ui/date-picker";
import { useUpdateRate } from "@/hooks/useRates";
import { formatCurrency } from "@/lib/format";
import type { Rate } from "@/types/api";

interface RateEditDialogProps {
  rate: Rate | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RateEditDialog({
  rate,
  open,
  onOpenChange,
}: RateEditDialogProps) {
  const updateMutation = useUpdateRate();

  const [importo, setImporto] = useState("");
  const [descrizione, setDescrizione] = useState("");
  const [dataScadenza, setDataScadenza] = useState<Date | undefined>(undefined);

  // Sync state quando la rata cambia (prop-driven open)
  useEffect(() => {
    if (rate && open) {
      setImporto(String(rate.importo_previsto));
      setDescrizione(rate.descrizione ?? "");
      setDataScadenza(parseISO(rate.data_scadenza));
    }
  }, [rate, open]);

  const hasPagamenti = (rate?.importo_saldato ?? 0) > 0;
  const importoNum = parseFloat(importo) || 0;
  const belowSaldato = hasPagamenti && importoNum < (rate?.importo_saldato ?? 0) - 0.01;

  const handleSave = () => {
    if (!rate || !dataScadenza || belowSaldato) return;

    updateMutation.mutate(
      {
        rateId: rate.id,
        importo_previsto: importoNum || rate.importo_previsto,
        data_scadenza: format(dataScadenza, "yyyy-MM-dd"),
        descrizione: descrizione.trim() || undefined,
      },
      {
        onSuccess: () => onOpenChange(false),
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>Modifica Rata</DialogTitle>
          <DialogDescription>
            {rate?.descrizione ?? `Rata #${rate?.id}`}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Info pagamenti su rate con versato */}
          {hasPagamenti && rate && (
            <div className="flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50/50 px-3 py-2.5 dark:border-blue-900/50 dark:bg-blue-950/20">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Questa rata ha {formatCurrency(rate.importo_saldato)} gia' versato.
                L&apos;importo previsto non puo' scendere sotto il versato.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="edit-importo">Importo Previsto</Label>
            <Input
              id="edit-importo"
              type="number"
              step="0.01"
              min={hasPagamenti ? rate?.importo_saldato : 0.01}
              value={importo}
              onChange={(e) => setImporto(e.target.value)}
            />
            {belowSaldato && rate && (
              <p className="text-[11px] text-destructive">
                Non puoi impostare meno di {formatCurrency(rate.importo_saldato)} (gia' versato)
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Data Scadenza</Label>
            <DatePicker
              value={dataScadenza}
              onChange={setDataScadenza}
              placeholder="Seleziona data..."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-descrizione">Descrizione</Label>
            <Input
              id="edit-descrizione"
              value={descrizione}
              onChange={(e) => setDescrizione(e.target.value)}
              placeholder="es. Rata 1/3"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={updateMutation.isPending}
          >
            Annulla
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending || !importo || !dataScadenza || belowSaldato}
          >
            {updateMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Salva
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
