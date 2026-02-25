// src/app/(dashboard)/esercizi/[id]/page.tsx
"use client";

/**
 * Scheda Esercizio — pagina dettaglio con 5 tab.
 *
 * Pattern identico a /contratti/[id] e /clienti/[id]:
 * - use(params) per unwrap Promise (React 19)
 * - useExercise(id) per fetch enriched (media + relazioni)
 * - Header con back + nome + badge + azioni
 * - 5 tab: Panoramica, Esecuzione, Errori, Media, Varianti
 */

import { use, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  Dumbbell,
  AlertTriangle,
  Image as ImageIcon,
  GitBranch,
  Activity,
  Shield,
  Loader2,
  Lock,
  Wind,
  Timer,
  ArrowUp,
  ArrowDown,
  Shuffle,
  Pencil,
  Trash2,
  FileText,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

import { useExercise } from "@/hooks/useExercises";
import { getMediaUrl } from "@/lib/media";
import {
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  DIFFICULTY_LABELS,
  DIFFICULTY_COLORS,
  EQUIPMENT_LABELS,
  PATTERN_LABELS,
  MUSCLE_LABELS,
  FORCE_TYPE_LABELS,
  FORCE_TYPE_COLORS,
  LATERAL_PATTERN_LABELS,
  LATERAL_PATTERN_COLORS,
  RELATION_TYPE_LABELS,
} from "@/components/exercises/exercise-constants";
import type { Exercise } from "@/types/api";

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function Badge({ label, colorClass }: { label: string; colorClass?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass || "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"}`}>
      {label}
    </span>
  );
}

function EmptySection({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <FileText className="mb-3 h-10 w-10 text-muted-foreground/40" />
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className="mt-1 text-xs text-muted-foreground/60">{description}</p>
    </div>
  );
}

function ContentCard({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <Icon className="h-4 w-4 text-muted-foreground" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: PANORAMICA
// ════════════════════════════════════════════════════════════

function PanoramicaTab({ exercise }: { exercise: Exercise }) {
  const hasAnatomia = exercise.descrizione_anatomica;
  const hasBiomeccanica = exercise.descrizione_biomeccanica;

  return (
    <div className="space-y-6">
      {/* Classificazione */}
      <div className="flex flex-wrap gap-2">
        <Badge label={CATEGORY_LABELS[exercise.categoria] || exercise.categoria} colorClass={CATEGORY_COLORS[exercise.categoria]} />
        <Badge label={PATTERN_LABELS[exercise.pattern_movimento] || exercise.pattern_movimento} />
        <Badge label={DIFFICULTY_LABELS[exercise.difficolta] || exercise.difficolta} colorClass={DIFFICULTY_COLORS[exercise.difficolta]} />
        {exercise.force_type && (
          <Badge label={FORCE_TYPE_LABELS[exercise.force_type] || exercise.force_type} colorClass={FORCE_TYPE_COLORS[exercise.force_type]} />
        )}
        {exercise.lateral_pattern && (
          <Badge label={LATERAL_PATTERN_LABELS[exercise.lateral_pattern] || exercise.lateral_pattern} colorClass={LATERAL_PATTERN_COLORS[exercise.lateral_pattern]} />
        )}
      </div>

      {/* Descrizioni */}
      <div className="grid gap-4 md:grid-cols-2">
        <ContentCard title="Anatomia" icon={Activity}>
          {hasAnatomia ? (
            <p className="text-sm leading-relaxed whitespace-pre-line">{exercise.descrizione_anatomica}</p>
          ) : (
            <EmptySection title="Descrizione anatomica" description="Contenuto in arrivo" />
          )}
        </ContentCard>

        <ContentCard title="Biomeccanica" icon={Dumbbell}>
          {hasBiomeccanica ? (
            <p className="text-sm leading-relaxed whitespace-pre-line">{exercise.descrizione_biomeccanica}</p>
          ) : (
            <EmptySection title="Descrizione biomeccanica" description="Contenuto in arrivo" />
          )}
        </ContentCard>
      </div>

      {/* Muscoli */}
      <div className="grid gap-4 md:grid-cols-2">
        <ContentCard title="Muscoli Primari" icon={Activity}>
          <div className="flex flex-wrap gap-2">
            {exercise.muscoli_primari.map((m) => (
              <span key={m} className="rounded-full border border-primary bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                {MUSCLE_LABELS[m] || m}
              </span>
            ))}
          </div>
        </ContentCard>

        {exercise.muscoli_secondari.length > 0 && (
          <ContentCard title="Muscoli Secondari" icon={Activity}>
            <div className="flex flex-wrap gap-2">
              {exercise.muscoli_secondari.map((m) => (
                <span key={m} className="rounded-full border border-violet-400 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-600 dark:bg-violet-900/20 dark:text-violet-400">
                  {MUSCLE_LABELS[m] || m}
                </span>
              ))}
            </div>
          </ContentCard>
        )}
      </div>

      {/* Parametri */}
      <ContentCard title="Parametri Allenamento" icon={Timer}>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {exercise.rep_range_forza && (
            <div>
              <p className="text-xs text-muted-foreground">Forza</p>
              <p className="text-sm font-medium">{exercise.rep_range_forza} rep</p>
            </div>
          )}
          {exercise.rep_range_ipertrofia && (
            <div>
              <p className="text-xs text-muted-foreground">Ipertrofia</p>
              <p className="text-sm font-medium">{exercise.rep_range_ipertrofia} rep</p>
            </div>
          )}
          {exercise.rep_range_resistenza && (
            <div>
              <p className="text-xs text-muted-foreground">Resistenza</p>
              <p className="text-sm font-medium">{exercise.rep_range_resistenza} rep</p>
            </div>
          )}
          <div>
            <p className="text-xs text-muted-foreground">Recupero</p>
            <p className="text-sm font-medium">{exercise.ore_recupero}h</p>
          </div>
          {exercise.tempo_consigliato && (
            <div>
              <p className="text-xs text-muted-foreground">Tempo</p>
              <p className="text-sm font-medium">{exercise.tempo_consigliato}</p>
            </div>
          )}
        </div>
      </ContentCard>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: ESECUZIONE
// ════════════════════════════════════════════════════════════

function EsecuzioneTab({ exercise }: { exercise: Exercise }) {
  const hasContent = exercise.setup || exercise.esecuzione || exercise.respirazione || exercise.coaching_cues.length > 0;

  if (!hasContent) {
    return <EmptySection title="Istruzioni di esecuzione" description="Contenuto in arrivo — questa sezione conterra' setup, movimento, respirazione e coaching cues" />;
  }

  return (
    <div className="space-y-4">
      {exercise.setup && (
        <ContentCard title="Setup — Posizione Iniziale" icon={BookOpen}>
          <p className="text-sm leading-relaxed whitespace-pre-line">{exercise.setup}</p>
        </ContentCard>
      )}

      {exercise.esecuzione && (
        <ContentCard title="Esecuzione — Movimento" icon={Activity}>
          <p className="text-sm leading-relaxed whitespace-pre-line">{exercise.esecuzione}</p>
        </ContentCard>
      )}

      {exercise.respirazione && (
        <ContentCard title="Respirazione" icon={Wind}>
          <p className="text-sm leading-relaxed">{exercise.respirazione}</p>
        </ContentCard>
      )}

      {exercise.coaching_cues.length > 0 && (
        <ContentCard title="Coaching Cues" icon={BookOpen}>
          <ol className="space-y-2">
            {exercise.coaching_cues.map((cue, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                  {i + 1}
                </span>
                {cue}
              </li>
            ))}
          </ol>
        </ContentCard>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: ERRORI & SICUREZZA
// ════════════════════════════════════════════════════════════

function ErroriTab({ exercise }: { exercise: Exercise }) {
  const hasContent = exercise.errori_comuni.length > 0 || exercise.controindicazioni.length > 0 || exercise.note_sicurezza;

  if (!hasContent) {
    return <EmptySection title="Errori comuni e sicurezza" description="Contenuto in arrivo — questa sezione conterra' errori da evitare, controindicazioni e note di sicurezza" />;
  }

  return (
    <div className="space-y-4">
      {exercise.errori_comuni.length > 0 && (
        <ContentCard title="Errori Comuni" icon={AlertTriangle}>
          <div className="space-y-3">
            {exercise.errori_comuni.map((err, i) => (
              <div key={i} className="rounded-lg border p-3">
                <p className="text-sm font-medium text-red-600 dark:text-red-400">
                  {err.errore}
                </p>
                <p className="mt-1 text-sm text-emerald-600 dark:text-emerald-400">
                  {err.correzione}
                </p>
              </div>
            ))}
          </div>
        </ContentCard>
      )}

      {exercise.controindicazioni.length > 0 && (
        <ContentCard title="Controindicazioni" icon={Shield}>
          <div className="flex flex-wrap gap-2">
            {exercise.controindicazioni.map((c) => (
              <span key={c} className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                {c}
              </span>
            ))}
          </div>
        </ContentCard>
      )}

      {exercise.note_sicurezza && (
        <ContentCard title="Note di Sicurezza" icon={Shield}>
          <p className="text-sm leading-relaxed whitespace-pre-line">{exercise.note_sicurezza}</p>
        </ContentCard>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: MEDIA
// ════════════════════════════════════════════════════════════

function MediaTab({ exercise }: { exercise: Exercise }) {
  const mainImage = getMediaUrl(exercise.image_url);
  const mainVideo = getMediaUrl(exercise.video_url);
  const hasMedia = mainImage || mainVideo || exercise.media.length > 0;

  if (!hasMedia) {
    return <EmptySection title="Nessun media" description="Le immagini e i video verranno visualizzati qui" />;
  }

  return (
    <div className="space-y-4">
      {/* Immagine principale */}
      {mainImage && (
        <div className="overflow-hidden rounded-lg border">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={mainImage} alt={exercise.nome} className="h-auto w-full max-h-96 object-contain bg-zinc-50 dark:bg-zinc-900" />
        </div>
      )}

      {/* Video principale */}
      {mainVideo && (
        <div className="overflow-hidden rounded-lg border">
          <video controls className="h-auto w-full max-h-96" preload="metadata">
            <source src={mainVideo} />
          </video>
        </div>
      )}

      {/* Galleria */}
      {exercise.media.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {exercise.media.map((m) => {
            const url = getMediaUrl(m.url);
            if (!url) return null;
            return m.tipo === "image" ? (
              <div key={m.id} className="overflow-hidden rounded-lg border">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={url} alt={m.descrizione || exercise.nome} className="h-40 w-full object-cover" />
                {m.descrizione && <p className="p-2 text-xs text-muted-foreground">{m.descrizione}</p>}
              </div>
            ) : (
              <div key={m.id} className="overflow-hidden rounded-lg border">
                <video controls className="h-40 w-full object-cover" preload="metadata">
                  <source src={url} />
                </video>
                {m.descrizione && <p className="p-2 text-xs text-muted-foreground">{m.descrizione}</p>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: VARIANTI
// ════════════════════════════════════════════════════════════

function VariantiTab({ exercise }: { exercise: Exercise }) {
  if (exercise.relazioni.length === 0) {
    return <EmptySection title="Nessuna variante" description="Le progressioni, regressioni e varianti verranno visualizzate qui" />;
  }

  const progressions = exercise.relazioni.filter((r) => r.tipo_relazione === "progression");
  const regressions = exercise.relazioni.filter((r) => r.tipo_relazione === "regression");
  const variations = exercise.relazioni.filter((r) => r.tipo_relazione === "variation");

  return (
    <div className="space-y-4">
      {progressions.length > 0 && (
        <ContentCard title="Progressioni" icon={ArrowUp}>
          <div className="space-y-2">
            {progressions.map((r) => (
              <Link
                key={r.id}
                href={`/esercizi/${r.related_exercise_id}`}
                className="flex items-center gap-2 rounded-lg border p-3 transition-colors hover:bg-muted/50"
              >
                <ArrowUp className="h-4 w-4 text-emerald-500" />
                <span className="text-sm font-medium">{r.related_exercise_nome}</span>
                <span className="ml-auto text-xs text-muted-foreground">{RELATION_TYPE_LABELS[r.tipo_relazione]}</span>
              </Link>
            ))}
          </div>
        </ContentCard>
      )}

      {regressions.length > 0 && (
        <ContentCard title="Regressioni" icon={ArrowDown}>
          <div className="space-y-2">
            {regressions.map((r) => (
              <Link
                key={r.id}
                href={`/esercizi/${r.related_exercise_id}`}
                className="flex items-center gap-2 rounded-lg border p-3 transition-colors hover:bg-muted/50"
              >
                <ArrowDown className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium">{r.related_exercise_nome}</span>
                <span className="ml-auto text-xs text-muted-foreground">{RELATION_TYPE_LABELS[r.tipo_relazione]}</span>
              </Link>
            ))}
          </div>
        </ContentCard>
      )}

      {variations.length > 0 && (
        <ContentCard title="Varianti" icon={Shuffle}>
          <div className="space-y-2">
            {variations.map((r) => (
              <Link
                key={r.id}
                href={`/esercizi/${r.related_exercise_id}`}
                className="flex items-center gap-2 rounded-lg border p-3 transition-colors hover:bg-muted/50"
              >
                <Shuffle className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">{r.related_exercise_nome}</span>
                <span className="ml-auto text-xs text-muted-foreground">{RELATION_TYPE_LABELS[r.tipo_relazione]}</span>
              </Link>
            ))}
          </div>
        </ContentCard>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function ExerciseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const exerciseId = parseInt(id, 10);
  const { data: exercise, isLoading, isError, refetch } = useExercise(exerciseId);

  // Loading
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Error
  if (isError || !exercise) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-destructive" />
        <h2 className="text-lg font-semibold">Esercizio non trovato</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          L&apos;esercizio richiesto non esiste o non e&apos; accessibile.
        </p>
        <div className="mt-4 flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/esercizi">Torna all&apos;archivio</Link>
          </Button>
          <Button onClick={() => refetch()}>Riprova</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/esercizi">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold sm:text-2xl">{exercise.nome}</h1>
              {exercise.is_builtin && <Lock className="h-4 w-4 text-muted-foreground" />}
            </div>
            {exercise.nome_en && (
              <p className="text-sm text-muted-foreground">{exercise.nome_en}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge label={EQUIPMENT_LABELS[exercise.attrezzatura] || exercise.attrezzatura} />
          <Badge label={DIFFICULTY_LABELS[exercise.difficolta] || exercise.difficolta} colorClass={DIFFICULTY_COLORS[exercise.difficolta]} />
          <Badge label={CATEGORY_LABELS[exercise.categoria] || exercise.categoria} colorClass={CATEGORY_COLORS[exercise.categoria]} />
        </div>
      </div>

      {/* ── Tabs ── */}
      <Tabs defaultValue="panoramica" className="w-full">
        <TabsList className="w-full overflow-x-auto">
          <TabsTrigger value="panoramica" className="gap-1.5">
            <BookOpen className="h-4 w-4" />
            <span className="hidden sm:inline">Panoramica</span>
          </TabsTrigger>
          <TabsTrigger value="esecuzione" className="gap-1.5">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">Esecuzione</span>
          </TabsTrigger>
          <TabsTrigger value="errori" className="gap-1.5">
            <AlertTriangle className="h-4 w-4" />
            <span className="hidden sm:inline">Errori</span>
          </TabsTrigger>
          <TabsTrigger value="media" className="gap-1.5">
            <ImageIcon className="h-4 w-4" />
            <span className="hidden sm:inline">Media</span>
          </TabsTrigger>
          <TabsTrigger value="varianti" className="gap-1.5">
            <GitBranch className="h-4 w-4" />
            <span className="hidden sm:inline">Varianti</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="panoramica">
          <PanoramicaTab exercise={exercise} />
        </TabsContent>
        <TabsContent value="esecuzione">
          <EsecuzioneTab exercise={exercise} />
        </TabsContent>
        <TabsContent value="errori">
          <ErroriTab exercise={exercise} />
        </TabsContent>
        <TabsContent value="media">
          <MediaTab exercise={exercise} />
        </TabsContent>
        <TabsContent value="varianti">
          <VariantiTab exercise={exercise} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
