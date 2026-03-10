"use client";

import {
  Download,
  FileSearch,
  HardDriveDownload,
  Loader2,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

import { useDownloadSupportSnapshot } from "@/hooks/useSystemSupport";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const INCLUDED_ITEMS = [
  "stato runtime e health dell'istanza",
  "versione, modalità sorgente/installer e dev/prod",
  "stato licenza e protezione licenza attiva/non attiva",
  "stato portale pubblico e base URL configurata",
  "ultimi backup locali disponibili con checksum",
];

const EXCLUDED_ITEMS = [
  "clienti, contratti, movimenti e dati business",
  "token JWT, credenziali o segreti runtime",
  "contenuti clinici o finanziari del trainer",
];

function SnapshotList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "good" | "neutral";
}) {
  const iconClass =
    tone === "good"
      ? "text-emerald-700 dark:text-emerald-300"
      : "text-slate-700 dark:text-slate-300";

  return (
    <div className="rounded-xl border bg-background/80 p-4">
      <div className="mb-3 flex items-center gap-2">
        {tone === "good" ? (
          <ShieldCheck className={`h-4 w-4 ${iconClass}`} />
        ) : (
          <LockKeyhole className={`h-4 w-4 ${iconClass}`} />
        )}
        <p className="text-sm font-semibold text-foreground">{title}</p>
      </div>
      <ul className="space-y-2 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 rounded-full bg-current opacity-70" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function SupportSnapshotSection() {
  const downloadSnapshot = useDownloadSupportSnapshot();

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <FileSearch className="h-5 w-5 text-teal-600" />
              <CardTitle>Snapshot diagnostico</CardTitle>
            </div>
            <CardDescription>
              Scarica un JSON di sola lettura per supporto tecnico locale. Serve a rendere l&apos;installazione
              diagnosticabile in pochi minuti senza esportare dati business o informazioni sensibili.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            onClick={() => downloadSnapshot.mutate()}
            disabled={downloadSnapshot.isPending}
          >
            {downloadSnapshot.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            Scarica diagnostica
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-xl border border-teal-200/70 bg-teal-50/70 p-4 text-sm text-teal-900 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-100">
          <div className="flex items-start gap-3">
            <HardDriveDownload className="mt-0.5 h-4 w-4 shrink-0" />
            <div className="space-y-1">
              <p className="font-semibold">Supporto rapido, nessuna esposizione superflua</p>
              <p>
                Questo export non sostituisce il backup: serve solo a fotografare lo stato tecnico
                dell&apos;istanza quando devi analizzare un problema di installazione, licenza o runtime.
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <SnapshotList title="Incluso nello snapshot" items={INCLUDED_ITEMS} tone="good" />
          <SnapshotList title="Escluso intenzionalmente" items={EXCLUDED_ITEMS} tone="neutral" />
        </div>
      </CardContent>
    </Card>
  );
}
