import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Bot,
  CheckCircle2,
  CircleDashed,
  Compass,
  Route,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const GUIDE_WAVES = [
  {
    title: "Wave 1 - Guida a capitoli",
    description:
      "Manuale step-by-step con capitoli e sezioni per coprire tutte le funzionalita principali del CRM.",
    status: "done",
    statusLabel: "Disponibile",
    icon: BookOpen,
  },
  {
    title: "Wave 2 - Guida illustrata",
    description:
      "Flow visuali orientati ai task reali: setup, dashboard scan, clienti e appuntamenti.",
    status: "in-progress",
    statusLabel: "In corso",
    icon: Route,
  },
  {
    title: "Wave 3 - Guida interattiva",
    description:
      "Tour in-app contestuali, checklist progressive e onboarding guidato sulle aree core.",
    status: "planned",
    statusLabel: "Pianificata",
    icon: Compass,
  },
  {
    title: "Wave 4 - Assistente virtuale NPL",
    description:
      "Assistente conversazionale collegato alla guida per risposte immediate e supporto operativo.",
    status: "planned",
    statusLabel: "Pianificata",
    icon: Bot,
  },
] as const;

const QUICK_PATHS = [
  {
    title: "Agenda e appuntamenti",
    description: "Organizza sessioni, verifica agenda giornaliera e gestisci cambi rapidi.",
    href: "/agenda",
  },
  {
    title: "Clienti e profilo",
    description: "Anagrafica, stato cliente, contratti attivi e storico operativo.",
    href: "/clienti",
  },
  {
    title: "Contratti e cassa",
    description: "Controlla pagamenti, rate e margine economico in modo coerente.",
    href: "/contratti",
  },
  {
    title: "Schede e monitoraggio",
    description: "Crea programmi, segui progresso e monitora allenamenti completati.",
    href: "/schede",
  },
] as const;

function statusBadgeClasses(status: (typeof GUIDE_WAVES)[number]["status"]): string {
  if (status === "done") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300";
  }

  if (status === "in-progress") {
    return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300";
  }

  return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300";
}

export default function GuidaPage() {
  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Guida FitManager</h1>
            <p className="text-sm text-muted-foreground">
              Punto di accesso unico per imparare il CRM e risolvere dubbi operativi.
            </p>
          </div>
        </div>

        <Badge variant="outline" className="w-fit gap-1.5 text-xs">
          <Sparkles className="h-3.5 w-3.5" />
          Guida in evoluzione
        </Badge>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Come usare questa pagina</CardTitle>
          <CardDescription>
            Parti dai percorsi rapidi per le operazioni quotidiane. Le wave successive estenderanno
            la guida con immagini, interazione contestuale e assistenza NPL.
          </CardDescription>
        </CardHeader>
      </Card>

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Route className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight">Roadmap guida</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {GUIDE_WAVES.map((wave) => {
            const Icon = wave.icon;
            const isDone = wave.status === "done";
            return (
              <Card key={wave.title} className="border-border/80">
                <CardHeader className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2">
                      <div className="rounded-md bg-muted p-2">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <CardTitle className="text-base">{wave.title}</CardTitle>
                    </div>
                    <Badge variant="outline" className={statusBadgeClasses(wave.status)}>
                      {wave.statusLabel}
                    </Badge>
                  </div>
                  <CardDescription>{wave.description}</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {isDone ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <CircleDashed className="h-3.5 w-3.5" />
                    )}
                    {isDone ? "Base pronta per review" : "Scaffold pronto per iterazione"}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <Separator />

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight">Percorsi rapidi</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {QUICK_PATHS.map((path) => (
            <Card key={path.href} className="border-border/80">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{path.title}</CardTitle>
                <CardDescription>{path.description}</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <Button asChild variant="outline" size="sm">
                  <Link href={path.href} className="inline-flex items-center gap-2">
                    Apri area
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
