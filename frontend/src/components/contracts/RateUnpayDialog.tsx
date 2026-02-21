// src/components/contracts/RateUnpayDialog.tsx
"use client";

/**
 * Dialog di sicurezza per la revoca di un pagamento rata.
 *
 * L'utente DEVE digitare "ANNULLA" per confermare.
 * Questa UX "speed bump" previene revoche accidentali che
 * eliminano il record dal Libro Mastro e riaprono il contratto.
 */

import { useState } from "react";
import { Loader2, AlertTriangle } from "lucide-react";

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUnpayRate } from "@/hooks/useRates";
import type { Rate } from "@/types/api";

interface RateUnpayDialogProps {
  rate: Rate | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

export function RateUnpayDialog({
  rate,
  open,
  onOpenChange,
}: RateUnpayDialogProps) {
  const unpayMutation = useUnpayRate();
  const [confirmation, setConfirmation] = useState("");

  const isConfirmed = confirmation === "ANNULLA";

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) setConfirmation("");
    onOpenChange(isOpen);
  };

  const handleConfirm = () => {
    if (!rate || !isConfirmed) return;

    unpayMutation.mutate(rate.id, {
      onSuccess: () => {
        setConfirmation("");
        onOpenChange(false);
      },
    });
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Revoca Pagamento
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3">
              <p>
                Stai per revocare il pagamento di{" "}
                <strong>{rate ? formatCurrency(rate.importo_saldato) : ""}</strong>{" "}
                sulla rata <strong>{rate?.descrizione ?? `#${rate?.id}`}</strong>.
              </p>
              <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive dark:border-destructive/30 dark:bg-destructive/10">
                <p className="font-semibold">Questa azione:</p>
                <ul className="mt-1.5 list-disc pl-5 space-y-1">
                  <li>Riportera' la rata allo stato PENDENTE</li>
                  <li>Riaprira' il contratto (se era saldato)</li>
                  <li>Cancellera' il record dal Libro Mastro</li>
                </ul>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-2 py-2">
          <Label htmlFor="confirm-unpay" className="text-sm">
            Digita <strong className="font-mono">ANNULLA</strong> per confermare
          </Label>
          <Input
            id="confirm-unpay"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            placeholder="Digita ANNULLA..."
            autoComplete="off"
          />
        </div>

        <AlertDialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={unpayMutation.isPending}
          >
            Chiudi
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            disabled={!isConfirmed || unpayMutation.isPending}
          >
            {unpayMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Revoca Pagamento
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
