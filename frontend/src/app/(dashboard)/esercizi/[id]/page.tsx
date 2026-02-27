// src/app/(dashboard)/esercizi/[id]/page.tsx
"use client";

/**
 * Scheda Esercizio — pagina dettaglio con hero muscolare + 5 tab.
 *
 * Pattern identico a /contratti/[id] e /clienti/[id]:
 * - use(params) per unwrap Promise (React 19)
 * - useExercise(id) per fetch enriched (media + relazioni)
 * - Header persistente + Hero section + 5 tab
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
import { MuscleMap } from "@/components/exercises/MuscleMap";
import { ExerciseSheet } from "@/components/exercises/ExerciseSheet";
import { DeleteExerciseDialog } from "@/components/exercises/DeleteExerciseDialog";
import {
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  DIFFICULTY_LABELS,
  DIFFICULTY_COLORS,
  EQUIPMENT_LABELS,
  PATTERN_LABELS,
  MUSCLE_LABELS,
  FORCE_TYPE_LABELS,
  LATERAL_PATTERN_LABELS,
  RELATION_TYPE_LABELS,
  KINETIC_CHAIN_LABELS,
  MOVEMENT_PLANE_LABELS,
  CONTRACTION_TYPE_LABELS,
  JOINT_ROLE_LABELS,
} from "@/components/exercises/exercise-constants";
import type { Exercise, TaxonomyMuscle } from "@/types/api";

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

function ClassificationRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-right">{value}</span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// HERO: MAPPA MUSCOLARE + CLASSIFICAZIONE
// ════════════════════════════════════════════════════════════

function MuscleGroup({ muscles, ruolo, colorIntensity }: {
  muscles: TaxonomyMuscle[];
  ruolo: string;
  colorIntensity: "strong" | "soft";
}) {
  // Raggruppa per gruppo muscolare
  const byGroup = new Map<string, TaxonomyMuscle[]>();
  for (const m of muscles) {
    const group = MUSCLE_LABELS[m.gruppo] || m.gruppo;
    if (!byGroup.has(group)) byGroup.set(group, []);
    byGroup.get(group)!.push(m);
  }

  const borderColor = colorIntensity === "strong"
    ? "border-blue-300 dark:border-blue-700"
    : "border-blue-200 dark:border-blue-800";
  const bgColor = colorIntensity === "strong"
    ? "bg-blue-50 dark:bg-blue-900/20"
    : "bg-blue-50/50 dark:bg-blue-900/10";
  const textColor = colorIntensity === "strong"
    ? "text-blue-700 dark:text-blue-400"
    : "text-blue-500 dark:text-blue-400/70";
  const dotColor = colorIntensity === "strong"
    ? "bg-blue-600 dark:bg-blue-400"
    : "bg-blue-300 dark:bg-blue-500/50";

  return (
    <div className="space-y-2">
      {Array.from(byGroup.entries()).map(([group, groupMuscles]) => (
        <div key={group}>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">{group}</p>
          <div className="flex flex-wrap gap-1">
            {groupMuscles.map((m) => (
              <span
                key={m.id}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${borderColor} ${bgColor} ${textColor}`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
                {m.nome}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function ExerciseHero({ exercise }: { exercise: Exercise }) {
  const hasTaxonomy = exercise.muscoli_dettaglio.length > 0;
  const primaryMuscles = exercise.muscoli_dettaglio.filter((m) => m.ruolo === "primary");
  const secondaryMuscles = exercise.muscoli_dettaglio.filter((m) => m.ruolo === "secondary");

  return (
    <div className="rounded-xl border bg-gradient-to-br from-zinc-50 to-zinc-100/50 p-5 dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="grid gap-6 md:grid-cols-[auto_1fr]">
        {/* Sinistra: Mappa muscolare */}
        <div className="flex justify-center">
          <MuscleMap
            muscoliPrimari={exercise.muscoli_primari}
            muscoliSecondari={exercise.muscoli_secondari}
          />
        </div>

        {/* Destra: Muscoli + Classificazione */}
        <div className="space-y-4">
          {/* Muscoli — anatomici (se disponibili) o gruppi */}
          {hasTaxonomy ? (
            <>
              {primaryMuscles.length > 0 && (
                <div>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Muscoli Primari ({primaryMuscles.length})
                  </h3>
                  <MuscleGroup muscles={primaryMuscles} ruolo="primary" colorIntensity="strong" />
                </div>
              )}
              {secondaryMuscles.length > 0 && (
                <div>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Muscoli Secondari ({secondaryMuscles.length})
                  </h3>
                  <MuscleGroup muscles={secondaryMuscles} ruolo="secondary" colorIntensity="soft" />
                </div>
              )}
            </>
          ) : (
            <>
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Muscoli Primari
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {exercise.muscoli_primari.map((m) => (
                    <span
                      key={m}
                      className="inline-flex items-center gap-1.5 rounded-full border border-blue-300 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 dark:border-blue-700 dark:bg-blue-900/20 dark:text-blue-400"
                    >
                      <span className="h-2 w-2 rounded-full bg-blue-600 dark:bg-blue-400" />
                      {MUSCLE_LABELS[m] || m}
                    </span>
                  ))}
                </div>
              </div>
              {exercise.muscoli_secondari.length > 0 && (
                <div>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Muscoli Secondari
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {exercise.muscoli_secondari.map((m) => (
                      <span
                        key={m}
                        className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50/50 px-2.5 py-1 text-xs font-medium text-blue-500 dark:border-blue-800 dark:bg-blue-900/10 dark:text-blue-400/70"
                      >
                        <span className="h-2 w-2 rounded-full bg-blue-300 dark:bg-blue-500/50" />
                        {MUSCLE_LABELS[m] || m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Articolazioni */}
          {exercise.articolazioni.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Articolazioni
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {exercise.articolazioni.map((j) => (
                  <span
                    key={j.id}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
                      j.ruolo === "agonist"
                        ? "border-teal-300 bg-teal-50 text-teal-700 dark:border-teal-700 dark:bg-teal-900/20 dark:text-teal-400"
                        : "border-zinc-300 bg-zinc-50 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-400"
                    }`}
                  >
                    {j.nome}
                    <span className="text-[10px] opacity-60">
                      {JOINT_ROLE_LABELS[j.ruolo] || j.ruolo}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Classificazione */}
          <div className="border-t pt-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Classificazione
            </h3>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2">
              <ClassificationRow
                label="Categoria"
                value={CATEGORY_LABELS[exercise.categoria] || exercise.categoria}
              />
              <ClassificationRow
                label="Pattern"
                value={PATTERN_LABELS[exercise.pattern_movimento] || exercise.pattern_movimento}
              />
              {exercise.force_type && (
                <ClassificationRow
                  label="Forza"
                  value={FORCE_TYPE_LABELS[exercise.force_type] || exercise.force_type}
                />
              )}
              {exercise.lateral_pattern && (
                <ClassificationRow
                  label="Lateralita&apos;"
                  value={LATERAL_PATTERN_LABELS[exercise.lateral_pattern] || exercise.lateral_pattern}
                />
              )}
              <ClassificationRow
                label="Attrezzatura"
                value={EQUIPMENT_LABELS[exercise.attrezzatura] || exercise.attrezzatura}
              />
              <ClassificationRow
                label="Difficolta&apos;"
                value={DIFFICULTY_LABELS[exercise.difficolta] || exercise.difficolta}
              />
              {exercise.catena_cinetica && (
                <ClassificationRow
                  label="Catena Cinetica"
                  value={KINETIC_CHAIN_LABELS[exercise.catena_cinetica] || exercise.catena_cinetica}
                />
              )}
              {exercise.piano_movimento && (
                <ClassificationRow
                  label="Piano"
                  value={MOVEMENT_PLANE_LABELS[exercise.piano_movimento] || exercise.piano_movimento}
                />
              )}
              {exercise.tipo_contrazione && (
                <ClassificationRow
                  label="Contrazione"
                  value={CONTRACTION_TYPE_LABELS[exercise.tipo_contrazione] || exercise.tipo_contrazione}
                />
              )}
              <ClassificationRow
                label="Recupero"
                value={`${exercise.ore_recupero}h`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TAB: PANORAMICA (snellito — muscoli/classificazione nell'hero)
// ════════════════════════════════════════════════════════════

function PanoramicaTab({ exercise }: { exercise: Exercise }) {
  const hasAnatomia = exercise.descrizione_anatomica;
  const hasBiomeccanica = exercise.descrizione_biomeccanica;

  return (
    <div className="space-y-6">
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
  // Immagini esecuzione FDB (start/end position)
  const execImages = exercise.media.filter(
    (m) => m.tipo === "image" && m.descrizione?.startsWith("fdb:exec_")
  );
  const startImg = execImages.find((m) => m.descrizione === "fdb:exec_start");
  const endImg = execImages.find((m) => m.descrizione === "fdb:exec_end");

  const hasContent = exercise.setup || exercise.esecuzione || exercise.respirazione || exercise.coaching_cues.length > 0 || execImages.length > 0;

  if (!hasContent) {
    return <EmptySection title="Istruzioni di esecuzione" description="Contenuto in arrivo — questa sezione conterra' setup, movimento, respirazione e coaching cues" />;
  }

  return (
    <div className="space-y-4">
      {/* Illustrazioni esecuzione (start/end) */}
      {(startImg || endImg) && (
        <ContentCard title="Illustrazione Esecuzione" icon={ImageIcon}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {startImg && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-muted-foreground text-center">
                  Posizione Iniziale
                </p>
                <div className="overflow-hidden rounded-lg border bg-zinc-50 dark:bg-zinc-900">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getMediaUrl(startImg.url) || ""}
                    alt="Posizione iniziale"
                    className="h-auto w-full object-contain"
                  />
                </div>
              </div>
            )}
            {endImg && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-muted-foreground text-center">
                  Posizione Finale
                </p>
                <div className="overflow-hidden rounded-lg border bg-zinc-50 dark:bg-zinc-900">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getMediaUrl(endImg.url) || ""}
                    alt="Posizione finale"
                    className="h-auto w-full object-contain"
                  />
                </div>
              </div>
            )}
          </div>
        </ContentCard>
      )}

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
  // Escludi media FDB exec (mostrati in EsecuzioneTab)
  const userMedia = exercise.media.filter(
    (m) => !m.descrizione?.startsWith("fdb:")
  );
  const hasMedia = mainImage || mainVideo || userMedia.length > 0;

  if (!hasMedia) {
    return <EmptySection title="Nessun media" description="Le immagini e i video verranno visualizzati qui" />;
  }

  return (
    <div className="space-y-4">
      {mainImage && (
        <div className="overflow-hidden rounded-lg border">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={mainImage} alt={exercise.nome} className="h-auto w-full max-h-96 object-contain bg-zinc-50 dark:bg-zinc-900" />
        </div>
      )}

      {mainVideo && (
        <div className="overflow-hidden rounded-lg border">
          <video controls className="h-auto w-full max-h-96" preload="metadata">
            <source src={mainVideo} />
          </video>
        </div>
      )}

      {userMedia.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {userMedia.map((m) => {
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

  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // Loading
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-9 rounded-lg" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-52" />
            <Skeleton className="h-4 w-36" />
          </div>
        </div>
        <Skeleton className="h-72 w-full rounded-xl" />
        <Skeleton className="h-10 w-full rounded-lg" />
        <Skeleton className="h-48 w-full rounded-lg" />
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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Link
            href="/esercizi"
            className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-white shadow-sm transition-colors hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight">{exercise.nome}</h1>
              {exercise.is_builtin && <Lock className="h-4 w-4 text-muted-foreground" />}
            </div>
            {exercise.nome_en && (
              <p className="mt-0.5 text-sm text-muted-foreground">{exercise.nome_en}</p>
            )}
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              <Badge label={CATEGORY_LABELS[exercise.categoria] || exercise.categoria} colorClass={CATEGORY_COLORS[exercise.categoria]} />
              <Badge label={DIFFICULTY_LABELS[exercise.difficolta] || exercise.difficolta} colorClass={DIFFICULTY_COLORS[exercise.difficolta]} />
              <Badge label={EQUIPMENT_LABELS[exercise.attrezzatura] || exercise.attrezzatura} />
            </div>
          </div>
        </div>
        {!exercise.is_builtin && (
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
        )}
      </div>

      {/* ── Hero: Mappa Muscolare + Classificazione ── */}
      <ExerciseHero exercise={exercise} />

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

      {/* ── Sheet modifica + Dialog elimina ── */}
      {!exercise.is_builtin && (
        <>
          <ExerciseSheet
            open={sheetOpen}
            onOpenChange={setSheetOpen}
            exercise={exercise}
          />
          <DeleteExerciseDialog
            open={deleteOpen}
            onOpenChange={setDeleteOpen}
            exercise={exercise}
          />
        </>
      )}
    </div>
  );
}
