// src/app/(dashboard)/contratti/[id]/page.tsx
"use client";

/**
 * Scheda Contratto — pagina full-page con dettaglio completo.
 *
 * Layout:
 * - ContractHeader (persistente): back, nome cliente (link), pacchetto, badge stato, azioni
 * - ContractFinancialHero (persistente): 6-10 KPI cards finanziarie + crediti
 * - Tabs: Piano Pagamenti | Sessioni | Dettagli
 *
 * Pattern identico a /clienti/[id] — dynamic route con use(params).
 */

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  ArrowLeft,
  FileText,
  Pencil,
  Trash2,
  Receipt,
  Calendar,
  Settings2,
  AlertTriangle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { ContractFinancialHero } from "@/components/contracts/ContractFinancialHero";
import { PaymentPlanTab } from "@/components/contracts/PaymentPlanTab";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { DeleteContractDialog } from "@/components/contracts/DeleteContractDialog";
import { useContract } from "@/hooks/useContracts";
import { useContractEvents, type EventHydrated } from "@/hooks/useAgenda";

// ════════════════════════════════════════════════════════════
// PAGE COMPONENT
// ════════════════════════════════════════════════════════════

export default function ContractDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const contractId = parseInt(id, 10);
  const router = useRouter();

  const { data: contract, isLoading } = useContract(contractId);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  if (isLoading) return <PageSkeleton />;
  if (!contract) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <AlertTriangle className="h-12 w-12 text-muted-foreground/30" />
        <p className="text-lg font-medium">Contratto non trovato</p>
      </div>
    );
  }

  const clientName = contract.client_nome && contract.client_cognome
    ? `${contract.client_cognome} ${contract.client_nome}`
    : undefined;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Link
            href="/contratti"
            className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-white shadow-sm transition-colors hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight">
                {contract.tipo_pacchetto ?? "Contratto"}
              </h1>
              {contract.chiuso ? (
                <Badge variant="secondary">Chiuso</Badge>
              ) : (
                <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
                  Attivo
                </Badge>
              )}
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              {clientName && (
                <Link
                  href={`/clienti/${contract.id_cliente}`}
                  className="font-medium text-foreground hover:underline"
                >
                  {clientName}
                </Link>
              )}
              {contract.data_inizio && (
                <>
                  <span className="text-muted-foreground/50">|</span>
                  <span>
                    {format(new Date(contract.data_inizio + "T00:00:00"), "dd MMM yyyy", { locale: it })}
                    {contract.data_scadenza && (
                      <> — {format(new Date(contract.data_scadenza + "T00:00:00"), "dd MMM yyyy", { locale: it })}</>
                    )}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setSheetOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Modifica
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Elimina
          </Button>
        </div>
      </div>

      {/* ── Financial Hero KPI ── */}
      <ContractFinancialHero contract={contract} />

      {/* ── Tabs ── */}
      <Tabs defaultValue="payments">
        <TabsList>
          <TabsTrigger value="payments">
            <Receipt className="mr-2 h-4 w-4" />
            Piano Pagamenti
          </TabsTrigger>
          <TabsTrigger value="sessioni">
            <Calendar className="mr-2 h-4 w-4" />
            Sessioni
          </TabsTrigger>
          <TabsTrigger value="dettagli">
            <Settings2 className="mr-2 h-4 w-4" />
            Dettagli
          </TabsTrigger>
        </TabsList>

        <TabsContent value="payments" className="mt-4">
          <PaymentPlanTab contract={contract} />
        </TabsContent>

        <TabsContent value="sessioni" className="mt-4">
          <SessioniTab contractId={contractId} />
        </TabsContent>

        <TabsContent value="dettagli" className="mt-4">
          <DettagliTab contract={contract} />
        </TabsContent>
      </Tabs>

      {/* ── Sheet modifica ── */}
      <ContractSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        contract={contract}
      />

      {/* ── Dialog elimina (redirect dopo eliminazione) ── */}
      <DeleteContractDialog
        open={deleteOpen}
        onOpenChange={(open) => {
          setDeleteOpen(open);
          if (!open && deleteOpen) {
            // Se il dialog si chiude dopo aver confermato, torna alla lista
            // (il contratto sara' gia' stato eliminato dalla mutation)
          }
        }}
        contract={contract}
        clientName={clientName}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Sessioni (eventi PT del contratto)
// ════════════════════════════════════════════════════════════

function SessioniTab({ contractId }: { contractId: number }) {
  const { data, isLoading } = useContractEvents(contractId);

  if (isLoading) return <TabSkeleton />;

  const events = data?.items ?? [];

  if (events.length === 0) {
    return <EmptyTab message="Nessuna sessione collegata a questo contratto" />;
  }

  const sorted = [...events].sort(
    (a, b) => b.data_inizio.getTime() - a.data_inizio.getTime()
  );

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Titolo</TableHead>
            <TableHead>Categoria</TableHead>
            <TableHead>Stato</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((e: EventHydrated) => (
            <TableRow key={e.id}>
              <TableCell className="tabular-nums">
                {format(e.data_inizio, "dd MMM yyyy HH:mm", { locale: it })}
              </TableCell>
              <TableCell className="font-medium">{e.titolo ?? "\u2014"}</TableCell>
              <TableCell>
                <Badge variant="outline">{e.categoria}</Badge>
              </TableCell>
              <TableCell>
                <Badge
                  variant="secondary"
                  className={
                    e.stato === "Completato"
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                      : e.stato === "Cancellato"
                      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                      : ""
                  }
                >
                  {e.stato}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Dettagli (info contratto read-only)
// ════════════════════════════════════════════════════════════

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";
import type { ContractWithRates } from "@/types/api";

function DettagliTab({ contract }: { contract: ContractWithRates }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Info contratto */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Informazioni contratto</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <DetailRow label="Tipo pacchetto" value={contract.tipo_pacchetto ?? "\u2014"} />
          <DetailRow label="Prezzo totale" value={formatCurrency(contract.prezzo_totale ?? 0)} />
          <DetailRow
            label="Acconto"
            value={contract.acconto > 0 ? formatCurrency(contract.acconto) : "\u2014"}
          />
          <DetailRow
            label="Crediti totali"
            value={contract.crediti_totali != null ? `${contract.crediti_totali}` : "\u2014"}
          />
        </CardContent>
      </Card>

      {/* Date e stato */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Date e stato</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <DetailRow
            label="Data inizio"
            value={contract.data_inizio
              ? format(new Date(contract.data_inizio + "T00:00:00"), "dd MMMM yyyy", { locale: it })
              : "\u2014"}
          />
          <DetailRow
            label="Data scadenza"
            value={contract.data_scadenza
              ? format(new Date(contract.data_scadenza + "T00:00:00"), "dd MMMM yyyy", { locale: it })
              : "\u2014"}
          />
          <DetailRow label="Stato" value={contract.chiuso ? "Chiuso" : "Attivo"} />
          {contract.note && (
            <div className="pt-2">
              <p className="text-muted-foreground">Note</p>
              <p className="mt-1 whitespace-pre-line font-medium">{contract.note}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SHARED UI
// ════════════════════════════════════════════════════════════

function EmptyTab({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

function TabSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-lg" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-40 w-full rounded-xl" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}
