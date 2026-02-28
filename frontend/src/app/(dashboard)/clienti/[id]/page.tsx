// src/app/(dashboard)/clienti/[id]/page.tsx
"use client";

/**
 * Scheda Cliente — pagina profilo full-page.
 *
 * Layout:
 * - ProfileHeader (persistente): avatar, nome, contatti, badge stato, modifica
 * - ProfileKpi (persistente): 4 card (crediti, contratti, finanze, ultimo evento)
 * - Tabs: Panoramica | Contratti | Sessioni | Movimenti
 *
 * Primo dynamic route dell'app. Params unwrapped con React 19 use().
 */

import { use, useState } from "react";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import { useRouter } from "next/navigation";
import {
  FileText,
  Calendar,
  Wallet,
  User,
  AlertTriangle,
  ClipboardList,
  HeartPulse,
  Plus,
  TrendingUp,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

import { Button } from "@/components/ui/button";
import { ClientProfileHeader } from "@/components/clients/ClientProfileHeader";
import { ClientProfileKpi } from "@/components/clients/ClientProfileKpi";
import { ClientSheet } from "@/components/clients/ClientSheet";
import { TemplateSelector } from "@/components/workouts/TemplateSelector";
import { AnamnesiSummary } from "@/components/clients/anamnesi/AnamnesiSummary";
import { AnamnesiWizard } from "@/components/clients/anamnesi/AnamnesiWizard";
import { isStructuredAnamnesi } from "@/components/clients/anamnesi/anamnesi-helpers";
import { ProgressiTab } from "@/components/clients/ProgressiTab";
import { useClient } from "@/hooks/useClients";
import { useClientContracts } from "@/hooks/useContracts";
import { useClientEvents, type EventHydrated } from "@/hooks/useAgenda";
import { useClientWorkouts } from "@/hooks/useWorkouts";
import { useMovements } from "@/hooks/useMovements";
import { formatCurrency } from "@/lib/format";
import type { ContractListItem, CashMovement, WorkoutPlan, AnamnesiData } from "@/types/api";

// ════════════════════════════════════════════════════════════
// PAGE COMPONENT
// ════════════════════════════════════════════════════════════

export default function ClientProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);

  const { data: client, isLoading } = useClient(clientId);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [templateSelectorOpen, setTemplateSelectorOpen] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);

  if (isLoading) return <ProfileSkeleton />;
  if (!client) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <AlertTriangle className="h-12 w-12 text-muted-foreground/30" />
        <p className="text-lg font-medium">Cliente non trovato</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ClientProfileHeader client={client} onEdit={() => setSheetOpen(true)} />
      <ClientProfileKpi client={client} />

      <Tabs defaultValue="panoramica">
        <TabsList className="w-full overflow-x-auto">
          <TabsTrigger value="panoramica">
            <User className="mr-2 h-4 w-4" />
            Panoramica
          </TabsTrigger>
          <TabsTrigger value="contratti">
            <FileText className="mr-2 h-4 w-4" />
            Contratti
          </TabsTrigger>
          <TabsTrigger value="sessioni">
            <Calendar className="mr-2 h-4 w-4" />
            Sessioni
          </TabsTrigger>
          <TabsTrigger value="movimenti">
            <Wallet className="mr-2 h-4 w-4" />
            Movimenti
          </TabsTrigger>
          <TabsTrigger value="schede">
            <ClipboardList className="mr-2 h-4 w-4" />
            Schede
          </TabsTrigger>
          <TabsTrigger value="progressi">
            <TrendingUp className="mr-2 h-4 w-4" />
            Progressi
          </TabsTrigger>
          <TabsTrigger value="anamnesi">
            <HeartPulse className="mr-2 h-4 w-4" />
            Anamnesi
          </TabsTrigger>
        </TabsList>

        <TabsContent value="panoramica" className="mt-4">
          <PanoramicaTab client={client} />
        </TabsContent>

        <TabsContent value="contratti" className="mt-4">
          <ContrattiTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="sessioni" className="mt-4">
          <SessioniTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="movimenti" className="mt-4">
          <MovimentiTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="schede" className="mt-4">
          <SchedeTab clientId={clientId} onNewScheda={() => setTemplateSelectorOpen(true)} />
        </TabsContent>

        <TabsContent value="progressi" className="mt-4">
          <ProgressiTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="anamnesi" className="mt-4">
          <AnamnesiTab
            anamnesi={client.anamnesi ?? null}
            onOpenWizard={() => setWizardOpen(true)}
          />
        </TabsContent>
      </Tabs>

      <TemplateSelector
        open={templateSelectorOpen}
        onOpenChange={setTemplateSelectorOpen}
        clientId={clientId}
      />

      <AnamnesiWizard
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        clientId={clientId}
        existing={client.anamnesi ?? null}
      />

      <ClientSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        client={client}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Panoramica
// ════════════════════════════════════════════════════════════

function PanoramicaTab({ client }: { client: { data_nascita: string | null; sesso: string | null; note_interne: string | null } }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Info personali */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Informazioni personali</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Data di nascita</span>
            <span className="font-medium">
              {client.data_nascita
                ? format(new Date(client.data_nascita + "T00:00:00"), "dd MMMM yyyy", { locale: it })
                : "—"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Sesso</span>
            <span className="font-medium">{client.sesso ?? "—"}</span>
          </div>
        </CardContent>
      </Card>

      {/* Note interne */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Note interne</CardTitle>
        </CardHeader>
        <CardContent>
          {client.note_interne ? (
            <p className="whitespace-pre-line text-sm">{client.note_interne}</p>
          ) : (
            <p className="text-sm italic text-muted-foreground">Nessuna nota</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Contratti
// ════════════════════════════════════════════════════════════

function ContrattiTab({ clientId }: { clientId: number }) {
  const { data, isLoading } = useClientContracts(clientId);

  if (isLoading) return <TabSkeleton />;

  const contracts = data?.items ?? [];

  if (contracts.length === 0) {
    return <EmptyTab message="Nessun contratto per questo cliente" />;
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Pacchetto</TableHead>
            <TableHead>Finanze</TableHead>
            <TableHead className="text-center">Crediti</TableHead>
            <TableHead>Stato</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contracts.map((c: ContractListItem) => {
            const prezzo = c.prezzo_totale ?? 0;
            const ratio = prezzo > 0 ? c.totale_versato / prezzo : 0;
            return (
              <TableRow key={c.id}>
                <TableCell className="font-medium">{c.tipo_pacchetto ?? "—"}</TableCell>
                <TableCell>
                  {prezzo > 0 ? (
                    <span className="text-sm tabular-nums">
                      {formatCurrency(c.totale_versato)} / {formatCurrency(prezzo)}
                    </span>
                  ) : "—"}
                </TableCell>
                <TableCell className="text-center">
                  <span className="font-mono text-sm">{c.crediti_usati}/{c.crediti_totali ?? 0}</span>
                </TableCell>
                <TableCell>
                  {c.chiuso ? (
                    <Badge variant="secondary">Chiuso</Badge>
                  ) : c.ha_rate_scadute ? (
                    <Badge className="bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400">
                      Rate in Ritardo
                    </Badge>
                  ) : (
                    <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
                      Attivo
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Sessioni
// ════════════════════════════════════════════════════════════

function SessioniTab({ clientId }: { clientId: number }) {
  const { data, isLoading } = useClientEvents(clientId);

  if (isLoading) return <TabSkeleton />;

  const events = data?.items ?? [];

  if (events.length === 0) {
    return <EmptyTab message="Nessuna sessione per questo cliente" />;
  }

  // Ordina per data decrescente (piu' recente prima)
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
              <TableCell className="font-medium">{e.titolo ?? "—"}</TableCell>
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
// TAB: Movimenti
// ════════════════════════════════════════════════════════════

function MovimentiTab({ clientId }: { clientId: number }) {
  const { data, isLoading } = useMovements({ id_cliente: clientId });

  if (isLoading) return <TabSkeleton />;

  const movements = data?.items ?? [];

  if (movements.length === 0) {
    return <EmptyTab message="Nessun movimento per questo cliente" />;
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Importo</TableHead>
            <TableHead>Metodo</TableHead>
            <TableHead className="hidden sm:table-cell">Note</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {movements.map((m: CashMovement) => (
            <TableRow key={m.id}>
              <TableCell className="tabular-nums">
                {m.data_effettiva
                  ? format(new Date(m.data_effettiva + "T00:00:00"), "dd MMM yyyy", { locale: it })
                  : "—"}
              </TableCell>
              <TableCell>
                <Badge
                  variant="outline"
                  className={
                    m.tipo === "ENTRATA"
                      ? "border-emerald-300 text-emerald-700 dark:border-emerald-700 dark:text-emerald-400"
                      : "border-red-300 text-red-700 dark:border-red-700 dark:text-red-400"
                  }
                >
                  {m.tipo}
                </Badge>
              </TableCell>
              <TableCell className="font-medium tabular-nums">
                {formatCurrency(m.importo)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {m.metodo ?? "—"}
              </TableCell>
              <TableCell className="hidden sm:table-cell text-sm text-muted-foreground truncate max-w-[200px]">
                {m.note ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Schede Allenamento
// ════════════════════════════════════════════════════════════

function SchedeTab({ clientId, onNewScheda }: { clientId: number; onNewScheda: () => void }) {
  const router = useRouter();
  const { data, isLoading } = useClientWorkouts(clientId);

  if (isLoading) return <TabSkeleton />;

  const workouts = data?.items ?? [];

  if (workouts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <ClipboardList className="h-10 w-10 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">Nessuna scheda per questo cliente</p>
        <Button variant="outline" size="sm" onClick={onNewScheda}>
          <Plus className="mr-2 h-4 w-4" />
          Crea Scheda
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={onNewScheda}>
          <Plus className="mr-2 h-4 w-4" />
          Nuova Scheda
        </Button>
      </div>
      <div className="rounded-lg border bg-white dark:bg-zinc-900">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Obiettivo</TableHead>
              <TableHead className="hidden sm:table-cell">Livello</TableHead>
              <TableHead className="text-center hidden sm:table-cell">Sessioni</TableHead>
              <TableHead className="hidden md:table-cell">Data</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {workouts.map((w: WorkoutPlan) => (
              <TableRow
                key={w.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/schede/${w.id}`)}
              >
                <TableCell className="font-medium">{w.nome}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">{w.obiettivo}</Badge>
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Badge variant="outline" className="text-xs">{w.livello}</Badge>
                </TableCell>
                <TableCell className="text-center hidden sm:table-cell tabular-nums">
                  {w.sessioni.length}
                </TableCell>
                <TableCell className="hidden md:table-cell text-sm text-muted-foreground tabular-nums">
                  {w.created_at
                    ? format(new Date(w.created_at), "dd MMM yyyy", { locale: it })
                    : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: Anamnesi
// ════════════════════════════════════════════════════════════

function AnamnesiTab({
  anamnesi,
  onOpenWizard,
}: {
  anamnesi: AnamnesiData | Record<string, unknown> | null;
  onOpenWizard: () => void;
}) {
  // Nessuna anamnesi
  if (!anamnesi) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <HeartPulse className="h-10 w-10 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">
          Nessuna anamnesi compilata per questo cliente
        </p>
        <Button variant="outline" size="sm" onClick={onOpenWizard}>
          <Plus className="mr-2 h-4 w-4" />
          Compila Anamnesi
        </Button>
      </div>
    );
  }

  // Anamnesi formato vecchio (legacy dict)
  if (!isStructuredAnamnesi(anamnesi as Record<string, unknown>)) {
    const legacyNote = (anamnesi as Record<string, unknown>).note;
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
        <HeartPulse className="h-10 w-10 text-amber-500/50" />
        <p className="text-sm text-muted-foreground">
          Anamnesi in formato precedente — ricompila per il nuovo questionario
        </p>
        {typeof legacyNote === "string" && legacyNote && (
          <p className="text-xs text-muted-foreground italic max-w-md text-center">
            Nota precedente: {legacyNote}
          </p>
        )}
        <Button variant="outline" size="sm" onClick={onOpenWizard}>
          <Plus className="mr-2 h-4 w-4" />
          Ricompila Anamnesi
        </Button>
      </div>
    );
  }

  // Anamnesi strutturata
  return <AnamnesiSummary data={anamnesi as AnamnesiData} onEdit={onOpenWizard} />;
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

function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-lg" />
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}
