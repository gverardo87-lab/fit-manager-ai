// src/lib/export-workout-pdf.ts
/**
 * Export clinico scaricabile (HTML -> PDF) con layout ispirato al vecchio Excel:
 * copertina, eventuale profilo clinico, sessioni con card principali e foto incorporate.
 */

import { toast } from "sonner";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import { BLOCK_TYPE_LABELS, type WorkoutExerciseRow } from "@/types/api";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import type { BlockCardData } from "@/components/workouts/BlockCard";

export interface SafetyExportData {
  clientNome: string;
  conditionNames: string[];
  rows: { condizione: string; severita: string; esercizi: string[] }[];
}

export interface ClinicalPdfExportData {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  durata_settimane?: number;
  sessioni_per_settimana?: number;
  sessioni: SessionCardData[];
  safety?: SafetyExportData;
  logoDataUrl?: string | null;
}

interface ExerciseImagePair {
  start?: string;
  end?: string;
}

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza",
  ipertrofia: "Ipertrofia",
  resistenza: "Resistenza",
  dimagrimento: "Dimagrimento",
  generale: "Generale",
};

const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante",
  intermedio: "Intermedio",
  avanzato: "Avanzato",
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

const SECTION_TITLES: Record<TemplateSection, string> = {
  avviamento: "AVVIAMENTO",
  principale: "BLOCCO SERIE X RIPETIZIONI",
  stretching: "STRETCHING & MOBILITA",
};

const SECTION_CLASS: Record<TemplateSection, string> = {
  avviamento: "section-avviamento",
  principale: "section-principale",
  stretching: "section-stretching",
};

function escapeHtml(value: string | null | undefined): string {
  if (!value) return "";
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function collectExerciseIds(sessioni: SessionCardData[]): number[] {
  const ids = new Set<number>();
  for (const session of sessioni) {
    for (const ex of session.esercizi) {
      ids.add(ex.id_esercizio);
    }
    for (const block of session.blocchi) {
      for (const ex of block.esercizi) {
        ids.add(ex.id_esercizio);
      }
    }
  }
  return [...ids];
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

async function fetchImageAsDataUrl(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const blob = await res.blob();
    return await blobToDataUrl(blob);
  } catch {
    return null;
  }
}

async function prefetchExerciseImages(exerciseIds: number[]): Promise<Map<number, ExerciseImagePair>> {
  const map = new Map<number, ExerciseImagePair>();
  const uniqueIds = [...new Set(exerciseIds)];
  await Promise.allSettled(
    uniqueIds.map(async (id) => {
      const [start, end] = await Promise.all([
        fetchImageAsDataUrl(`/media/exercises/${id}/exec_start.jpg`),
        fetchImageAsDataUrl(`/media/exercises/${id}/exec_end.jpg`),
      ]);
      if (start || end) {
        map.set(id, {
          ...(start ? { start } : {}),
          ...(end ? { end } : {}),
        });
      }
    }),
  );
  return map;
}

function groupBySection(esercizi: WorkoutExerciseRow[]) {
  const groups: Record<TemplateSection, WorkoutExerciseRow[]> = {
    avviamento: [],
    principale: [],
    stretching: [],
  };
  for (const ex of esercizi) {
    const section = getSectionForCategory(ex.esercizio_categoria);
    groups[section].push(ex);
  }
  return groups;
}

function imageTag(src: string | null | undefined, alt: string) {
  if (!src) {
    return `<div class="photo-wrap empty"><span class="photo-ph">Foto non disponibile</span></div>`;
  }
  return `<div class="photo-wrap"><img src="${src}" alt="${escapeHtml(alt)}" onerror="this.style.display='none';this.parentElement.classList.add('empty')"/><span class="photo-ph">Foto non disponibile</span></div>`;
}

function renderPrimaryCard(ex: WorkoutExerciseRow, idx: number, imgs?: ExerciseImagePair): string {
  return `
    <article class="exercise-card">
      <div class="exercise-head">
        <span class="exercise-idx">${idx + 1}</span>
        <h4>${escapeHtml(ex.esercizio_nome)}</h4>
      </div>
      <div class="exercise-body">
        <div class="photos">
          ${imageTag(imgs?.start, `${ex.esercizio_nome} start`)}
          ${imageTag(imgs?.end, `${ex.esercizio_nome} end`)}
        </div>
        <div class="metrics">
          <div><span>Serie</span><strong>${ex.serie}</strong></div>
          <div><span>Rip</span><strong>${escapeHtml(ex.ripetizioni)}</strong></div>
          <div><span>Kg</span><strong>${ex.carico_kg ?? "-"}</strong></div>
          <div><span>Riposo</span><strong>${ex.tempo_riposo_sec}s</strong></div>
          ${
            ex.tempo_esecuzione
              ? `<div class="metric-full"><span>Tempo</span><strong>${escapeHtml(ex.tempo_esecuzione)}</strong></div>`
              : ""
          }
          ${
            ex.note
              ? `<div class="metric-full notes"><span>Note</span><strong>${escapeHtml(ex.note)}</strong></div>`
              : ""
          }
        </div>
      </div>
    </article>
  `;
}

function blockPrefix(block: BlockCardData, idx: number): string {
  if (block.tipo_blocco === "superset") return `A${idx + 1}`;
  if (block.tipo_blocco === "tabata") return "•";
  return `${idx + 1}`;
}

function blockImageTag(src: string | null | undefined, alt: string): string {
  if (!src) {
    return `<div class="block-photo-wrap empty"><span>n/d</span></div>`;
  }
  return `<div class="block-photo-wrap"><img src="${src}" alt="${escapeHtml(alt)}" onerror="this.style.display='none';this.parentElement.classList.add('empty')"/><span>n/d</span></div>`;
}

function renderBlock(block: BlockCardData, imageMap: Map<number, ExerciseImagePair>): string {
  const label = BLOCK_TYPE_LABELS[block.tipo_blocco] ?? block.tipo_blocco;
  const detail = [
    block.nome ? escapeHtml(block.nome) : "",
    block.giri > 0 ? `${block.giri} ${block.tipo_blocco === "emom" ? "min" : "giri"}` : "",
    block.durata_lavoro_sec ? `${block.durata_lavoro_sec}s lavoro` : "",
    block.durata_riposo_sec ? `${block.durata_riposo_sec}s riposo` : "",
    block.durata_blocco_sec ? `${Math.round(block.durata_blocco_sec / 60)} min` : "",
  ].filter(Boolean).join(" · ");

  const rows = block.esercizi.map((ex, idx) => `
      <tr>
        <td class="tc">${blockPrefix(block, idx)}</td>
        <td>${escapeHtml(ex.esercizio_nome)}</td>
        <td class="tc">${escapeHtml(ex.ripetizioni || "-")}</td>
        <td class="tc">${ex.carico_kg ?? "-"}</td>
        <td>${blockImageTag(imageMap.get(ex.id_esercizio)?.start, `${ex.esercizio_nome} start`)}</td>
        <td>${blockImageTag(imageMap.get(ex.id_esercizio)?.end, `${ex.esercizio_nome} end`)}</td>
      </tr>
    `).join("");

  return `
    <section class="block-card">
      <header>
        <strong>${escapeHtml(label.toUpperCase())}</strong>
        ${detail ? `<span>${detail}</span>` : ""}
      </header>
      <table>
        <thead>
          <tr><th class="tc">#</th><th>Esercizio</th><th class="tc">Rip</th><th class="tc">Kg</th><th class="tc">Start</th><th class="tc">End</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </section>
  `;
}

function renderCompactTable(exercises: WorkoutExerciseRow[]): string {
  if (exercises.length === 0) return "";
  const rows = exercises.map((ex, idx) => `
    <tr>
      <td class="tc">${idx + 1}</td>
      <td>${escapeHtml(ex.esercizio_nome)}</td>
      <td class="tc">${ex.serie}</td>
      <td class="tc">${escapeHtml(ex.ripetizioni)}</td>
      <td>${escapeHtml(ex.note)}</td>
    </tr>
  `).join("");
  return `
    <table class="compact-table">
      <thead>
        <tr><th class="tc">#</th><th>Esercizio</th><th class="tc">Serie</th><th class="tc">Rip</th><th>Note</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderCover(data: ClinicalPdfExportData): string {
  const info: string[] = [
    `<li><span>Cliente</span><strong>${escapeHtml(data.clientNome ?? "Scheda generica")}</strong></li>`,
    `<li><span>Obiettivo</span><strong>${escapeHtml(OBIETTIVO_LABELS[data.obiettivo] ?? data.obiettivo)}</strong></li>`,
    `<li><span>Livello</span><strong>${escapeHtml(LIVELLO_LABELS[data.livello] ?? data.livello)}</strong></li>`,
  ];
  if (data.durata_settimane) {
    info.push(`<li><span>Durata</span><strong>${data.durata_settimane} settimane</strong></li>`);
  }
  if (data.sessioni_per_settimana) {
    info.push(`<li><span>Frequenza</span><strong>${data.sessioni_per_settimana}x / settimana</strong></li>`);
  }
  return `
    <section class="page cover">
      <div class="brand">ProFit AI Studio</div>
      <h1>${escapeHtml(data.nome)}</h1>
      <p class="sub">SCHEDA DI ALLENAMENTO</p>
      <ul class="cover-grid">${info.join("")}</ul>
      ${data.logoDataUrl ? `<img class="cover-logo" src="${data.logoDataUrl}" alt="Logo cliente"/>` : ""}
      <footer>${new Date().toLocaleDateString("it-IT")}</footer>
    </section>
  `;
}

function renderSafetyPage(safety: SafetyExportData, schedaNome: string): string {
  const rows = safety.rows.map((r, idx) => `
    <tr>
      <td class="tc">${idx + 1}</td>
      <td>${escapeHtml(r.condizione)}</td>
      <td class="tc ${r.severita === "avoid" ? "sev-avoid" : "sev-caution"}">${r.severita === "avoid" ? "EVITARE" : "CAUTELA"}</td>
      <td>${escapeHtml(r.esercizi.join(", "))}</td>
    </tr>
  `).join("");
  return `
    <section class="page">
      <h2>Profilo Clinico · ${escapeHtml(safety.clientNome)}</h2>
      <p class="muted">${safety.conditionNames.length} condizioni rilevate · Scheda: ${escapeHtml(schedaNome)}</p>
      <table class="safety-table">
        <thead>
          <tr><th class="tc">#</th><th>Condizione Medica</th><th class="tc">Severita</th><th>Esercizi Coinvolti</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <p class="muted">Nota: questo foglio e' informativo. Il trainer decide sempre.</p>
    </section>
  `;
}

function renderSessionPage(data: ClinicalPdfExportData, session: SessionCardData, imageMap: Map<number, ExerciseImagePair>): string {
  const grouped = groupBySection(session.esercizi);
  const content = SECTION_ORDER.map((section) => {
    const items = grouped[section];
    const isPrincipale = section === "principale";
    if (items.length === 0 && (!isPrincipale || session.blocchi.length === 0)) return "";

    const body = isPrincipale
      ? [
          ...items.map((ex, idx) => renderPrimaryCard(ex, idx, imageMap.get(ex.id_esercizio))),
          ...session.blocchi.slice().sort((a, b) => a.ordine - b.ordine).map((block) => renderBlock(block, imageMap)),
        ].join("")
      : renderCompactTable(items);

    return `
      <section class="session-section ${SECTION_CLASS[section]}">
        <h3>${SECTION_TITLES[section]}</h3>
        ${body}
      </section>
    `;
  }).join("");

  return `
    <section class="page session">
      <header class="session-head">
        <h2>${escapeHtml(data.nome)}</h2>
        <p>${escapeHtml(data.clientNome ?? "Scheda generica")} · ${escapeHtml(OBIETTIVO_LABELS[data.obiettivo] ?? data.obiettivo)} · ${escapeHtml(LIVELLO_LABELS[data.livello] ?? data.livello)}</p>
      </header>
      <div class="session-title">
        <strong>${escapeHtml(session.nome_sessione)}</strong>
        ${session.focus_muscolare ? `<span>${escapeHtml(session.focus_muscolare)}</span>` : ""}
      </div>
      ${content}
      <footer>${new Date().toLocaleDateString("it-IT")}</footer>
    </section>
  `;
}

function buildHtml(data: ClinicalPdfExportData, imageMap: Map<number, ExerciseImagePair>): string {
  const safetyPage =
    data.safety && data.safety.rows.length > 0
      ? renderSafetyPage(data.safety, data.nome)
      : "";

  const sessionPages = data.sessioni.map((s) => renderSessionPage(data, s, imageMap)).join("");

  return `
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(data.nome)} · PDF Clinico</title>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; font-family: Arial, sans-serif; color: #1f2937; background: #f3f4f6; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto 8mm; background: #fff; padding: 10mm; page-break-after: always; position: relative; }
    .page:last-child { page-break-after: auto; }
    .brand { color: #00796b; font-size: 24px; font-weight: 700; text-align: center; margin-top: 30mm; }
    .cover h1 { text-align: center; margin: 10mm 0 2mm; color: #004d40; font-size: 24px; }
    .cover .sub { text-align: center; color: #6b7280; letter-spacing: 0.8px; margin: 0 0 10mm; }
    .cover-grid { max-width: 120mm; margin: 0 auto; padding: 0; list-style: none; }
    .cover-grid li { display: flex; justify-content: space-between; padding: 3mm 0; border-bottom: 1px solid #e5e7eb; gap: 8mm; }
    .cover-grid span { color: #6b7280; }
    .cover-logo { display: block; max-width: 52mm; max-height: 22mm; margin: 10mm auto 0; object-fit: contain; }
    h2 { margin: 0 0 2mm; color: #00695c; font-size: 18px; }
    .muted { color: #6b7280; font-size: 12px; margin: 0 0 4mm; }
    .session-head p { margin: 0; color: #6b7280; font-size: 12px; }
    .session-title { margin: 4mm 0 2mm; padding: 2.2mm 3mm; background: #eef2f7; border-left: 3px solid #009688; display: flex; justify-content: space-between; gap: 8px; font-size: 12px; }
    .session-section { margin-top: 3mm; }
    .session-section h3 { margin: 0 0 2mm; padding: 1.8mm 2.4mm; font-size: 11px; letter-spacing: 0.5px; color: #0f766e; }
    .section-avviamento h3 { background: #fff8e1; }
    .section-principale h3 { background: #e0f2f1; }
    .section-stretching h3 { background: #e0f7fa; }
    .exercise-card { border: 1px solid #d1d5db; margin-bottom: 2mm; break-inside: avoid; }
    .exercise-head { background: #009688; color: #fff; display: flex; align-items: center; gap: 8px; padding: 1.6mm 2.4mm; }
    .exercise-head h4 { margin: 0; font-size: 12px; line-height: 1.2; }
    .exercise-idx { display: inline-flex; min-width: 20px; justify-content: center; font-weight: 700; }
    .exercise-body { display: grid; grid-template-columns: 68mm 1fr; gap: 2.2mm; padding: 2.2mm; background: #f9fafb; }
    .photos { display: grid; grid-template-columns: 1fr 1fr; gap: 2mm; align-items: stretch; }
    .photo-wrap { border: 1px solid #d1d5db; min-height: 28mm; display: flex; align-items: center; justify-content: center; background: #fff; overflow: hidden; position: relative; }
    .photo-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .photo-ph { display: none; color: #9ca3af; font-size: 10px; padding: 4px; text-align: center; }
    .photo-wrap.empty .photo-ph { display: block; }
    .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 1.8mm; }
    .metrics > div { border: 1px solid #d1d5db; background: #fff; padding: 1.4mm 2mm; }
    .metrics span { display: block; font-size: 10px; color: #6b7280; margin-bottom: 0.8mm; }
    .metrics strong { font-size: 12px; }
    .metrics .metric-full { grid-column: 1 / -1; }
    .metrics .notes strong { font-size: 11px; font-weight: 600; }
    .block-card { border: 1px solid #d1d5db; margin: 2mm 0; break-inside: avoid; }
    .block-card header { background: #eef2ff; padding: 1.6mm 2.4mm; display: flex; justify-content: space-between; gap: 8px; }
    .block-card header strong { font-size: 11px; color: #312e81; }
    .block-card header span { font-size: 10px; color: #6b7280; }
    .block-photo-wrap { width: 24mm; min-height: 16mm; border: 1px solid #d1d5db; background: #fff; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .block-photo-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .block-photo-wrap span { display: none; font-size: 9px; color: #9ca3af; }
    .block-photo-wrap.empty span { display: block; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #e5e7eb; padding: 1.4mm 1.8mm; font-size: 10px; vertical-align: top; }
    th { background: #f3f4f6; text-align: left; }
    .tc { text-align: center; }
    .compact-table tbody tr:nth-child(even) td { background: #f9fafb; }
    .safety-table tbody tr:nth-child(even) td { background: #fef2f2; }
    .sev-avoid { color: #b91c1c; font-weight: 700; }
    .sev-caution { color: #b45309; font-weight: 700; }
    footer { position: absolute; left: 10mm; right: 10mm; bottom: 6mm; display: flex; justify-content: flex-end; font-size: 10px; color: #9ca3af; }
    @page { size: A4; margin: 10mm; }
    @media screen {
      .page { box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12); }
    }
  </style>
</head>
<body>
  ${renderCover(data)}
  ${safetyPage}
  ${sessionPages}
</body>
</html>
  `;
}

function sanitizeFilename(value: string): string {
  const cleaned = value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9\s-_]/g, "")
    .trim()
    .replace(/\s+/g, "_");
  return cleaned || "scheda_clinica";
}

function downloadHtml(content: string, filename: string): void {
  const blob = new Blob([content], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function downloadWorkoutClinicalHtml(data: ClinicalPdfExportData): Promise<void> {
  const exerciseIds = collectExerciseIds(data.sessioni);
  const imageMap = exerciseIds.length > 0 ? await prefetchExerciseImages(exerciseIds) : new Map<number, ExerciseImagePair>();
  if (exerciseIds.length > 0 && imageMap.size === 0) {
    toast.warning("Nessuna foto trovata per gli esercizi della scheda.");
  }
  const html = buildHtml(data, imageMap);
  const filename = `${sanitizeFilename(data.nome)}_clinico.html`;
  downloadHtml(html, filename);
  toast.success("File clinico scaricato. Aprilo e usa Stampa > Salva come PDF.");
}

// Alias compatibilita: ora export clinico avviene via download file locale.
export async function exportWorkoutClinicalPdf(data: ClinicalPdfExportData): Promise<void> {
  return downloadWorkoutClinicalHtml(data);
}
