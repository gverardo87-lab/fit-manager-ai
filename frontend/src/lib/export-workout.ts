// src/lib/export-workout.ts
/**
 * Export scheda allenamento in Excel — Layout "Scheda Clinica".
 *
 * Documento medico-sportivo proprietario ProFit AI Studio.
 * Struttura: Copertina → Profilo Clinico (opzionale) → 1 foglio per sessione.
 *
 * Esercizi principali: card-block (header teal + 2 righe dati/immagini + separatore).
 * Avviamento/stretching: righe compatte.
 * Immagini: exec_start.jpg + exec_end.jpg affiancate (150×100px).
 */

import ExcelJS from "exceljs";
import { saveAs } from "file-saver";
import { toast } from "sonner";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import type { WorkoutExerciseRow } from "@/types/api";

// ── Colori ──

const TEAL = "009688";
const TEAL_DARK = "00796B";
const WHITE = "FFFFFF";
const LIGHT_TEAL = "E0F2F1";
const AMBER_LIGHT = "FFF8E1";
const CYAN_LIGHT = "E0F7FA";
const RED_LIGHT = "FFEBEE";
const RED = "C62828";
const AMBER = "E65100";
const GRAY = "666666";
const GRAY_LIGHT = "999999";
const GRAY_BG = "F5F5F5";

// ── Sezioni ──

const SECTION_COLORS: Record<TemplateSection, { bg: string; label: string }> = {
  avviamento: { bg: AMBER_LIGHT, label: "AVVIAMENTO" },
  principale: { bg: LIGHT_TEAL, label: "ESERCIZIO PRINCIPALE" },
  stretching: { bg: CYAN_LIGHT, label: "STRETCHING & MOBILITA" },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

// ── Immagini ──

const IMAGE_ROW_HEIGHT = 55;
const IMAGE_SIZE = { width: 150, height: 100 };
const CARD_SEPARATOR_HEIGHT = 8;

// ── Labels ──

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

// ── Colonne ──

const MERGE_CARD = "H";  // 8 colonne (A-H) — layout card con immagini
const MERGE_TABLE = "H";  // 8 colonne (A-H) — layout tabella senza immagini (+ carico)

// ── Interfaces ──

interface SafetyExportData {
  clientNome: string;
  conditionNames: string[];
  rows: { condizione: string; severita: string; esercizi: string[] }[];
}

interface ExerciseImagePair {
  start?: ArrayBuffer;
  end?: ArrayBuffer;
}

interface ExportData {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  durata_settimane?: number;
  sessioni_per_settimana?: number;
  sessioni: SessionCardData[];
  safety?: SafetyExportData;
  exerciseIds?: number[];
}

// ── Helpers ──

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

async function fetchImageAsBuffer(url: string): Promise<ArrayBuffer | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return await res.arrayBuffer();
  } catch (err) {
    console.warn(`[Export] Fetch immagine fallita: ${url}`, err);
    return null;
  }
}

async function prefetchExerciseImages(
  exerciseIds: number[],
): Promise<Map<number, ExerciseImagePair>> {
  const map = new Map<number, ExerciseImagePair>();
  const uniqueIds = [...new Set(exerciseIds)];

  // URL relativi — same-origin grazie al rewrite Next.js in next.config.ts
  // che proxya /media/* al backend. Evita problemi CORS con StaticFiles.
  await Promise.allSettled(
    uniqueIds.map(async (id) => {
      const [startBuf, endBuf] = await Promise.all([
        fetchImageAsBuffer(`/media/exercises/${id}/exec_start.jpg`),
        fetchImageAsBuffer(`/media/exercises/${id}/exec_end.jpg`),
      ]);
      if (startBuf || endBuf) {
        map.set(id, {
          ...(startBuf && { start: startBuf }),
          ...(endBuf && { end: endBuf }),
        });
      }
    }),
  );

  return map;
}

// ════════════════════════════════════════════════════════════
// FOGLIO COPERTINA
// ════════════════════════════════════════════════════════════

function createCoverSheet(
  wb: ExcelJS.Workbook,
  data: ExportData,
  mergeLetter: string,
) {
  const ws = wb.addWorksheet("Copertina");

  // Stesse colonne del foglio sessione per coerenza visiva
  ws.columns = [
    { width: 4 }, { width: 22 }, { width: 22 }, { width: 9 },
    { width: 10 }, { width: 9 }, { width: 10 }, { width: 24 },
  ];

  // Margine superiore
  ws.addRow([]);
  ws.addRow([]);
  ws.addRow([]);

  // Brand
  const brandRow = ws.addRow(["ProFit AI Studio"]);
  const brandRowNum = ws.rowCount;
  ws.mergeCells(`A${brandRowNum}:${mergeLetter}${brandRowNum}`);
  brandRow.getCell(1).font = { bold: true, size: 20, color: { argb: TEAL } };
  brandRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
  brandRow.height = 30;

  ws.addRow([]);

  // Linea separatrice
  const lineRow = ws.addRow([]);
  const lineRowNum = ws.rowCount;
  ws.mergeCells(`A${lineRowNum}:${mergeLetter}${lineRowNum}`);
  lineRow.getCell(1).border = {
    bottom: { style: "medium", color: { argb: TEAL } },
  };

  ws.addRow([]);

  // Nome scheda
  const nameRow = ws.addRow([data.nome]);
  const nameRowNum = ws.rowCount;
  ws.mergeCells(`A${nameRowNum}:${mergeLetter}${nameRowNum}`);
  nameRow.getCell(1).font = { bold: true, size: 16, color: { argb: TEAL_DARK } };
  nameRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
  nameRow.height = 26;

  ws.addRow([]);

  // Sottotitolo
  const subtitleRow = ws.addRow(["SCHEDA DI ALLENAMENTO"]);
  const subtitleRowNum = ws.rowCount;
  ws.mergeCells(`A${subtitleRowNum}:${mergeLetter}${subtitleRowNum}`);
  subtitleRow.getCell(1).font = { size: 11, color: { argb: GRAY } };
  subtitleRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };

  ws.addRow([]);
  ws.addRow([]);

  // Griglia dati programma — label in col D, valore in col E-F
  const infoRows: [string, string][] = [
    ["Cliente", data.clientNome ?? "Scheda generica"],
    ["Obiettivo", OBIETTIVO_LABELS[data.obiettivo] ?? data.obiettivo],
    ["Livello", LIVELLO_LABELS[data.livello] ?? data.livello],
  ];
  if (data.durata_settimane) {
    infoRows.push(["Durata", `${data.durata_settimane} settimane`]);
  }
  if (data.sessioni_per_settimana) {
    infoRows.push(["Frequenza", `${data.sessioni_per_settimana}x / settimana`]);
  }

  for (const [label, value] of infoRows) {
    const row = ws.addRow(["", "", "", label, value]);
    const rowNum = ws.rowCount;
    ws.mergeCells(`E${rowNum}:F${rowNum}`);
    row.getCell(4).font = { size: 10, color: { argb: GRAY } };
    row.getCell(4).alignment = { horizontal: "right", vertical: "middle" };
    row.getCell(5).font = { bold: true, size: 11 };
    row.getCell(5).alignment = { horizontal: "left", vertical: "middle" };
    row.height = 20;
  }

  ws.addRow([]);
  ws.addRow([]);
  ws.addRow([]);

  // Data
  const dateRow = ws.addRow([new Date().toLocaleDateString("it-IT")]);
  const dateRowNum = ws.rowCount;
  ws.mergeCells(`A${dateRowNum}:${mergeLetter}${dateRowNum}`);
  dateRow.getCell(1).font = { size: 10, color: { argb: GRAY } };
  dateRow.getCell(1).alignment = { horizontal: "center" };

  // Footer
  const footerRow = ws.addRow(["Documento generato da ProFit AI Studio"]);
  const footerRowNum = ws.rowCount;
  ws.mergeCells(`A${footerRowNum}:${mergeLetter}${footerRowNum}`);
  footerRow.getCell(1).font = { size: 9, italic: true, color: { argb: GRAY_LIGHT } };
  footerRow.getCell(1).alignment = { horizontal: "center" };
}

// ════════════════════════════════════════════════════════════
// FOGLIO PROFILO CLINICO
// ════════════════════════════════════════════════════════════

function createSafetySheet(
  wb: ExcelJS.Workbook,
  safety: SafetyExportData,
  nome: string,
) {
  const ws = wb.addWorksheet("Profilo Clinico");
  ws.columns = [
    { width: 6 },   // #
    { width: 30 },  // Condizione
    { width: 12 },  // Severita
    { width: 50 },  // Esercizi coinvolti
  ];

  const titleRow = ws.addRow([`Profilo Clinico — ${safety.clientNome}`]);
  titleRow.font = { bold: true, size: 14, color: { argb: RED } };
  ws.mergeCells("A1:D1");

  const subRow = ws.addRow([`${safety.conditionNames.length} condizioni rilevate — Scheda: ${nome}`]);
  subRow.font = { size: 10, color: { argb: GRAY } };
  ws.mergeCells("A2:D2");

  ws.addRow([]);

  const thRow = ws.addRow(["#", "Condizione Medica", "Severita", "Esercizi Coinvolti"]);
  thRow.eachCell((cell) => {
    cell.font = { bold: true, size: 10, color: { argb: WHITE } };
    cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: RED } };
    cell.alignment = { horizontal: "center", vertical: "middle" };
  });
  thRow.getCell(2).alignment = { horizontal: "left", vertical: "middle" };
  thRow.getCell(4).alignment = { horizontal: "left", vertical: "middle" };

  safety.rows.forEach((row, idx) => {
    const isAvoid = row.severita === "avoid";
    const dataRow = ws.addRow([
      idx + 1,
      row.condizione,
      isAvoid ? "EVITARE" : "CAUTELA",
      row.esercizi.join(", "),
    ]);
    dataRow.font = { size: 10 };
    dataRow.getCell(1).alignment = { horizontal: "center" };
    dataRow.getCell(3).alignment = { horizontal: "center" };
    dataRow.getCell(3).font = {
      size: 10,
      bold: true,
      color: { argb: isAvoid ? RED : AMBER },
    };

    if (idx % 2 === 0) {
      dataRow.eachCell((cell) => {
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: RED_LIGHT } };
      });
    }
  });

  ws.addRow([]);
  const note = ws.addRow(["Nota: questo foglio e' informativo. Il trainer decide SEMPRE."]);
  note.font = { size: 9, italic: true, color: { argb: GRAY_LIGHT } };
  ws.mergeCells(`A${ws.rowCount}:D${ws.rowCount}`);
}

// ════════════════════════════════════════════════════════════
// CARD-BLOCK: Esercizio Principale
// ════════════════════════════════════════════════════════════

function addExerciseCard(
  ws: ExcelJS.Worksheet,
  wb: ExcelJS.Workbook,
  ex: WorkoutExerciseRow,
  idx: number,
  imgs: ExerciseImagePair | undefined,
) {
  const ml = MERGE_CARD;

  // ── Row 1: Header band (nome esercizio su teal) ──
  const headerRow = ws.addRow([idx + 1, ex.esercizio_nome]);
  const headerRowNum = ws.rowCount;
  ws.mergeCells(`B${headerRowNum}:${ml}${headerRowNum}`);
  headerRow.getCell(1).font = { bold: true, size: 11, color: { argb: WHITE } };
  headerRow.getCell(1).fill = { type: "pattern", pattern: "solid", fgColor: { argb: TEAL } };
  headerRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
  headerRow.getCell(2).font = { bold: true, size: 12, color: { argb: WHITE } };
  headerRow.getCell(2).fill = { type: "pattern", pattern: "solid", fgColor: { argb: TEAL } };
  headerRow.getCell(2).alignment = { horizontal: "left", vertical: "middle" };
  // Fill tutte le celle merged
  for (let c = 3; c <= 8; c++) {
    headerRow.getCell(c).fill = { type: "pattern", pattern: "solid", fgColor: { argb: TEAL } };
  }
  headerRow.height = 22;

  // ── Row 2: Data line 1 (Serie + Carico) ──
  const dataRow1 = ws.addRow([
    "", "", "",
    "Serie",
    ex.serie,
    "Kg",
    ex.carico_kg != null ? `${ex.carico_kg}` : "—",
    ex.note ?? "",
  ]);
  const dataRow1Num = ws.rowCount;

  // ── Row 3: Data line 2 (Rip + Riposo) ──
  const dataRow2 = ws.addRow([
    "", "", "",
    "Rip",
    ex.ripetizioni,
    "Riposo",
    `${ex.tempo_riposo_sec}s`,
    ex.tempo_esecuzione ? `Tempo: ${ex.tempo_esecuzione}` : "",
  ]);
  const dataRow2Num = ws.rowCount;

  // Merge note (H) verticale
  ws.mergeCells(`H${dataRow1Num}:H${dataRow2Num}`);

  // Altezza righe dati
  ws.getRow(dataRow1Num).height = IMAGE_ROW_HEIGHT;
  ws.getRow(dataRow2Num).height = IMAGE_ROW_HEIGHT;

  // Sfondo leggero per area dati
  for (let r = dataRow1Num; r <= dataRow2Num; r++) {
    for (let c = 1; c <= 8; c++) {
      ws.getRow(r).getCell(c).fill = {
        type: "pattern", pattern: "solid", fgColor: { argb: GRAY_BG },
      };
    }
  }

  // Stile label (D, F)
  for (const r of [dataRow1Num, dataRow2Num]) {
    ws.getRow(r).getCell(4).font = { size: 9, color: { argb: GRAY } };
    ws.getRow(r).getCell(4).alignment = { horizontal: "right", vertical: "middle" };
    ws.getRow(r).getCell(6).font = { size: 9, color: { argb: GRAY } };
    ws.getRow(r).getCell(6).alignment = { horizontal: "right", vertical: "middle" };
  }

  // Stile valori (E, G)
  for (const r of [dataRow1Num, dataRow2Num]) {
    ws.getRow(r).getCell(5).font = { bold: true, size: 11 };
    ws.getRow(r).getCell(5).alignment = { horizontal: "left", vertical: "middle" };
    ws.getRow(r).getCell(7).font = { bold: true, size: 11 };
    ws.getRow(r).getCell(7).alignment = { horizontal: "left", vertical: "middle" };
  }

  // Stile nota (H)
  ws.getRow(dataRow1Num).getCell(8).font = { size: 9, color: { argb: GRAY } };
  ws.getRow(dataRow1Num).getCell(8).alignment = {
    horizontal: "left", vertical: "top", wrapText: true,
  };

  // ── Immagini ──
  if (imgs) {
    if (imgs.start) {
      const imgId = wb.addImage({ buffer: imgs.start, extension: "jpeg" });
      ws.addImage(imgId, {
        tl: { col: 1.05, row: dataRow1Num - 1 + 0.05 },
        ext: IMAGE_SIZE,
      });
    }
    if (imgs.end) {
      const imgId = wb.addImage({ buffer: imgs.end, extension: "jpeg" });
      ws.addImage(imgId, {
        tl: { col: 2.05, row: dataRow1Num - 1 + 0.05 },
        ext: IMAGE_SIZE,
      });
    }
  }

  // ── Row 4: Separatore ──
  const sepRow = ws.addRow([]);
  sepRow.height = CARD_SEPARATOR_HEIGHT;
}

// ════════════════════════════════════════════════════════════
// RIGHE COMPATTE: Avviamento / Stretching
// ════════════════════════════════════════════════════════════

function addCompactRow(
  ws: ExcelJS.Worksheet,
  ex: WorkoutExerciseRow,
  idx: number,
  sectionBg: string,
  isCard: boolean,
) {
  if (isCard) {
    // Layout 8 colonne: merge B:C per nome
    const row = ws.addRow([
      idx + 1,
      ex.esercizio_nome,
      "",
      "",
      ex.serie,
      ex.ripetizioni,
      "",
      ex.note ?? "",
    ]);
    const rowNum = ws.rowCount;
    ws.mergeCells(`B${rowNum}:C${rowNum}`);

    row.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
    row.getCell(2).alignment = { horizontal: "left", vertical: "middle" };
    row.getCell(5).alignment = { horizontal: "center", vertical: "middle" };
    row.getCell(6).alignment = { horizontal: "center", vertical: "middle" };
    row.getCell(8).alignment = { horizontal: "left", vertical: "middle" };
    row.font = { size: 10 };

    if (idx % 2 === 0) {
      row.eachCell((cell) => {
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: sectionBg } };
      });
    }
  } else {
    // Layout 8 colonne: senza immagini
    const row = ws.addRow([
      idx + 1,
      ex.esercizio_nome,
      ex.serie,
      ex.ripetizioni,
      "",
      "",
      "",
      ex.note ?? "",
    ]);

    row.getCell(1).alignment = { horizontal: "center" };
    row.getCell(2).alignment = { horizontal: "left" };
    row.getCell(3).alignment = { horizontal: "center" };
    row.getCell(4).alignment = { horizontal: "center" };
    row.font = { size: 10 };

    if (idx % 2 === 0) {
      row.eachCell((cell) => {
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: sectionBg } };
      });
    }
  }
}

// ════════════════════════════════════════════════════════════
// EXPORT PRINCIPALE
// ════════════════════════════════════════════════════════════

export async function exportWorkoutExcel({
  nome,
  obiettivo,
  livello,
  clientNome,
  durata_settimane,
  sessioni_per_settimana,
  sessioni,
  safety,
  exerciseIds,
}: ExportData): Promise<void> {
  // Pre-fetch immagini in parallelo
  const requestedCount = exerciseIds?.length ?? 0;
  const imageMap = requestedCount > 0
    ? await prefetchExerciseImages(exerciseIds!)
    : new Map<number, ExerciseImagePair>();

  const hasImages = imageMap.size > 0;

  // Diagnostica: avvisa se immagini richieste ma non trovate
  if (requestedCount > 0 && !hasImages) {
    console.warn(`[Export] 0/${requestedCount} immagini trovate. Backend attivo?`);
    toast.info("Export senza immagini — nessuna illustrazione trovata per gli esercizi");
  } else if (requestedCount > 0) {
    console.info(`[Export] ${imageMap.size}/${requestedCount} esercizi con immagini`);
  }

  const wb = new ExcelJS.Workbook();
  wb.creator = "ProFit AI Studio";
  wb.created = new Date();

  const mergeLetter = hasImages ? MERGE_CARD : MERGE_TABLE;

  // ── Foglio 1: Copertina ──
  createCoverSheet(wb, {
    nome, obiettivo, livello, clientNome,
    durata_settimane, sessioni_per_settimana,
    sessioni, exerciseIds,
  }, mergeLetter);

  // ── Foglio 2: Profilo Clinico (opzionale) ──
  if (safety && safety.rows.length > 0) {
    createSafetySheet(wb, safety, nome);
  }

  // ── Fogli Sessione ──
  for (const session of sessioni) {
    const sheetName = session.nome_sessione.slice(0, 31);
    const ws = wb.addWorksheet(sheetName);

    // Colonne
    if (hasImages) {
      ws.columns = [
        { width: 4 },   // A: #
        { width: 22 },  // B: Img Start
        { width: 22 },  // C: Img End
        { width: 9 },   // D: Label
        { width: 10 },  // E: Value
        { width: 9 },   // F: Label
        { width: 10 },  // G: Value
        { width: 24 },  // H: Note
      ];
    } else {
      ws.columns = [
        { width: 5 },   // A: #
        { width: 30 },  // B: Esercizio
        { width: 8 },   // C: Serie
        { width: 12 },  // D: Ripetizioni
        { width: 10 },  // E: Carico (kg)
        { width: 10 },  // F: Riposo
        { width: 12 },  // G: Tempo
        { width: 25 },  // H: Note
      ];
    }

    // ── Header scheda ──
    const headerRow = ws.addRow([nome]);
    headerRow.font = { bold: true, size: 14, color: { argb: TEAL } };
    ws.mergeCells(`A1:${mergeLetter}1`);

    const subRow = ws.addRow([
      `${clientNome ?? "Scheda generica"} — ${OBIETTIVO_LABELS[obiettivo] ?? obiettivo} — ${LIVELLO_LABELS[livello] ?? livello}`,
    ]);
    subRow.font = { size: 10, color: { argb: GRAY } };
    ws.mergeCells(`A2:${mergeLetter}2`);

    ws.addRow([]);

    // ── Header sessione ──
    const sessHeaderRow = ws.addRow([
      `${session.nome_sessione}${session.focus_muscolare ? ` — ${session.focus_muscolare}` : ""}`,
    ]);
    sessHeaderRow.font = { bold: true, size: 11 };
    const sessRowNum = ws.rowCount;
    ws.mergeCells(`A${sessRowNum}:${mergeLetter}${sessRowNum}`);

    // ── Sezioni ──
    const grouped = groupBySection(session.esercizi);

    for (const sectionKey of SECTION_ORDER) {
      const exercises = grouped[sectionKey];
      if (exercises.length === 0) continue;

      const config = SECTION_COLORS[sectionKey];
      const isPrincipale = sectionKey === "principale";

      // Section header
      ws.addRow([]);
      const sectionRow = ws.addRow([config.label]);
      const sectionRowNum = ws.rowCount;
      sectionRow.font = { bold: true, size: 9, color: { argb: TEAL } };
      sectionRow.eachCell((cell) => {
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: config.bg } };
      });
      ws.mergeCells(`A${sectionRowNum}:${mergeLetter}${sectionRowNum}`);

      if (isPrincipale && hasImages) {
        // ── Card-Block layout ──
        exercises.forEach((ex, idx) => {
          const imgs = imageMap.get(ex.id_esercizio);
          addExerciseCard(ws, wb, ex, idx, imgs);
        });
      } else if (isPrincipale && !hasImages) {
        // ── Tabella classica per principale senza immagini ──
        const colHeaders = ["#", "Esercizio", "Serie", "Ripetizioni", "Carico (kg)", "Riposo (s)", "Tempo", "Note"];
        const thRow = ws.addRow(colHeaders);
        thRow.eachCell((cell) => {
          cell.font = { bold: true, size: 10, color: { argb: WHITE } };
          cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: TEAL } };
          cell.alignment = { horizontal: "center", vertical: "middle" };
          cell.border = { bottom: { style: "thin", color: { argb: TEAL } } };
        });
        thRow.getCell(2).alignment = { horizontal: "left", vertical: "middle" };

        exercises.forEach((ex, idx) => {
          const row = ws.addRow([
            idx + 1,
            ex.esercizio_nome,
            ex.serie,
            ex.ripetizioni,
            ex.carico_kg != null ? ex.carico_kg : "",
            ex.tempo_riposo_sec,
            ex.tempo_esecuzione ?? "",
            ex.note ?? "",
          ]);

          if (idx % 2 === 0) {
            row.eachCell((cell) => {
              cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: LIGHT_TEAL } };
            });
          }

          row.getCell(1).alignment = { horizontal: "center" };
          row.getCell(2).alignment = { horizontal: "left" };
          row.getCell(3).alignment = { horizontal: "center" };
          row.getCell(4).alignment = { horizontal: "center" };
          row.getCell(5).alignment = { horizontal: "center" };
          row.getCell(6).alignment = { horizontal: "center" };
          row.getCell(7).alignment = { horizontal: "center" };
          row.font = { size: 10 };
        });
      } else {
        // ── Righe compatte per avviamento/stretching ──
        // Mini-header per sezioni compatte
        if (hasImages) {
          const compactHeader = ws.addRow(["#", "Esercizio", "", "", "Serie", "Rip", "", "Note"]);
          const chNum = ws.rowCount;
          ws.mergeCells(`B${chNum}:C${chNum}`);
          compactHeader.eachCell((cell) => {
            cell.font = { bold: true, size: 9, color: { argb: GRAY } };
            cell.alignment = { horizontal: "center", vertical: "middle" };
          });
          compactHeader.getCell(2).alignment = { horizontal: "left", vertical: "middle" };
          compactHeader.getCell(8).alignment = { horizontal: "left", vertical: "middle" };
        }

        exercises.forEach((ex, idx) => {
          addCompactRow(ws, ex, idx, config.bg, hasImages);
        });
      }
    }

    // ── Footer ──
    ws.addRow([]);
    const footerCells = ["ProFit AI Studio", "", "", "", "", "", "", new Date().toLocaleDateString("it-IT")];
    const footerRow = ws.addRow(footerCells);
    footerRow.font = { size: 8, italic: true, color: { argb: GRAY_LIGHT } };
  }

  // ── Download ──
  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const filename = `${nome.replace(/[^a-zA-Z0-9àèéìòùÀÈÉÌÒÙ\s-]/g, "").trim()}.xlsx`;
  saveAs(blob, filename);
}
