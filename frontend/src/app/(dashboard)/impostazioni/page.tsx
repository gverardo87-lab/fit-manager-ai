// src/app/(dashboard)/impostazioni/page.tsx
"use client";

/**
 * Pagina Impostazioni — gestione backup e dati.
 *
 * Sezioni:
 * 1. Backup Database — crea, lista, scarica, ripristina
 * 2. Export Dati — download JSON (GDPR / portabilita')
 *
 * Scalabile: future sezioni (profilo, sicurezza, tema) si aggiungono qui.
 */

import { useRef, useState } from "react";
import {
  Settings,
  Database,
  Download,
  Upload,
  FileJson,
  HardDrive,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
  useBackups,
  useCreateBackup,
  useRestoreBackup,
  downloadBackup,
  exportTrainerData,
} from "@/hooks/useBackup";

// ── Helpers ──

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Page ──

export default function ImpostazioniPage() {
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [restoreFilename, setRestoreFilename] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: backups, isLoading, isError, refetch } = useBackups();
  const createBackup = useCreateBackup();
  const restoreBackup = useRestoreBackup();

  // ── Handlers ──

  const handleRestoreFromList = (filename: string) => {
    setRestoreFilename(filename);
    setRestoreDialogOpen(true);
  };

  const confirmRestoreFromList = async () => {
    if (!restoreFilename) return;
    setRestoreDialogOpen(false);

    // Scarica il backup come blob e re-invia a /restore
    const { data } = await (await import("@/lib/api-client")).default.get(
      `/backup/download/${restoreFilename}`,
      { responseType: "blob" }
    );
    const file = new File([data as Blob], restoreFilename, {
      type: "application/x-sqlite3",
    });
    restoreBackup.mutate(file);
  };

  const handleRestoreFromFile = () => {
    fileInputRef.current?.click();
  };

  const onFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    restoreBackup.mutate(file);
    // Reset input per permettere re-upload dello stesso file
    e.target.value = "";
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-900/30">
          <Settings className="h-5 w-5 text-slate-600 dark:text-slate-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Impostazioni</h1>
          <p className="text-sm text-muted-foreground">
            Gestione backup, dati e configurazione
          </p>
        </div>
      </div>

      {/* ── Sezione Backup ── */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              <div>
                <CardTitle>Backup Database</CardTitle>
                <CardDescription>
                  Crea copie di sicurezza del database e ripristina da backup
                  precedenti
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRestoreFromFile}
                disabled={restoreBackup.isPending}
              >
                <Upload className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Carica Backup</span>
              </Button>
              <Button
                size="sm"
                onClick={() => createBackup.mutate()}
                disabled={createBackup.isPending}
              >
                <HardDrive className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">
                  {createBackup.isPending ? "Creazione..." : "Crea Backup"}
                </span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Input file nascosto per restore da file */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".sqlite,.db"
            className="hidden"
            onChange={onFileSelected}
          />

          {/* Loading */}
          {isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {/* Errore */}
          {isError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
              <p className="text-destructive">
                Errore nel caricamento dei backup.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => refetch()}
              >
                Riprova
              </Button>
            </div>
          )}

          {/* Lista backup */}
          {backups && backups.length === 0 && (
            <div className="py-8 text-center text-muted-foreground">
              <Database className="mx-auto mb-3 h-10 w-10 opacity-30" />
              <p>Nessun backup disponibile</p>
              <p className="text-sm">
                Clicca &quot;Crea Backup&quot; per creare il primo
              </p>
            </div>
          )}

          {backups && backups.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead className="hidden sm:table-cell">Dimensione</TableHead>
                  <TableHead className="hidden sm:table-cell">Data</TableHead>
                  <TableHead className="text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {backups.map((backup) => (
                  <TableRow key={backup.filename}>
                    <TableCell className="font-mono text-sm truncate max-w-[180px]">
                      {backup.filename}
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">{formatBytes(backup.size_bytes)}</TableCell>
                    <TableCell className="hidden sm:table-cell">{formatDate(backup.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => downloadBackup(backup.filename)}
                        >
                          <Download className="h-4 w-4 sm:mr-1" />
                          <span className="hidden sm:inline">Scarica</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            handleRestoreFromList(backup.filename)
                          }
                          disabled={restoreBackup.isPending}
                        >
                          <RefreshCw className="h-4 w-4 sm:mr-1" />
                          <span className="hidden sm:inline">Ripristina</span>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ── Sezione Export ── */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <FileJson className="h-5 w-5 text-green-600" />
              <div>
                <CardTitle>Export Dati</CardTitle>
                <CardDescription>
                  Scarica tutti i tuoi dati in formato JSON (GDPR / portabilita')
                </CardDescription>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={exportTrainerData}>
              <Download className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Esporta JSON</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            L&apos;export include: clienti, contratti, rate, eventi, movimenti e
            spese ricorrenti. I record eliminati non vengono inclusi.
          </p>
        </CardContent>
      </Card>

      {/* ── Dialog conferma restore ── */}
      <AlertDialog
        open={restoreDialogOpen}
        onOpenChange={setRestoreDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Ripristinare il backup?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Il database corrente verra' sovrascritto con{" "}
              <span className="font-mono font-medium">{restoreFilename}</span>.
              <br />
              Un backup di sicurezza verra' creato automaticamente prima del
              ripristino.
              <br />
              <strong>
                Dopo il ripristino sara' necessario riavviare il server.
              </strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={confirmRestoreFromList}>
              Ripristina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
