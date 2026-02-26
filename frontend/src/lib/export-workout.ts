// src/lib/export-workout.ts
/**
 * Export scheda allenamento in Excel (client-side).
 *
 * Librerie: exceljs + file-saver.
 * - 1 foglio per sessione (tab)
 * - 3 sezioni per sessione: Avviamento, Principale, Stretching
 * - Header teal + formattazione professionale
 */

import ExcelJS from "exceljs";
import { saveAs } from "file-saver";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import type { WorkoutExerciseRow } from "@/types/api";

const TEAL = "009688";
const WHITE = "FFFFFF";
const LIGHT_TEAL = "E0F2F1";
const AMBER_LIGHT = "FFF8E1";
const CYAN_LIGHT = "E0F7FA";

const SECTION_COLORS: Record<TemplateSection, { bg: string; label: string }> = {
  avviamento: { bg: AMBER_LIGHT, label: "AVVIAMENTO" },
  principale: { bg: LIGHT_TEAL, label: "ESERCIZIO PRINCIPALE" },
  stretching: { bg: CYAN_LIGHT, label: "STRETCHING & MOBILITA" },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

interface ExportData {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  sessioni: SessionCardData[];
  aiCommentary?: string | null;
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

export async function exportWorkoutExcel({
  nome,
  obiettivo,
  livello,
  clientNome,
  sessioni,
  aiCommentary,
}: ExportData): Promise<void> {
  const wb = new ExcelJS.Workbook();
  wb.creator = "ProFit AI Studio";
  wb.created = new Date();

  for (const session of sessioni) {
    // Limita nome foglio a 31 char (limite Excel)
    const sheetName = session.nome_sessione.slice(0, 31);
    const ws = wb.addWorksheet(sheetName);

    // Larghezza colonne
    ws.columns = [
      { width: 5 },   // #
      { width: 30 },  // Esercizio
      { width: 8 },   // Serie
      { width: 12 },  // Ripetizioni
      { width: 10 },  // Riposo
      { width: 12 },  // Tempo
      { width: 25 },  // Note
    ];

    // ── Header scheda ──
    const headerRow = ws.addRow([nome]);
    headerRow.font = { bold: true, size: 14, color: { argb: TEAL } };
    ws.mergeCells("A1:G1");

    const subRow = ws.addRow([
      `${clientNome ?? "Scheda generica"} — ${obiettivo} — ${livello}`,
    ]);
    subRow.font = { size: 10, color: { argb: "666666" } };
    ws.mergeCells("A2:G2");

    ws.addRow([]); // Riga vuota

    // ── Header sessione ──
    const sessHeaderRow = ws.addRow([
      `${session.nome_sessione}${session.focus_muscolare ? ` — ${session.focus_muscolare}` : ""}`,
    ]);
    sessHeaderRow.font = { bold: true, size: 11 };
    const currentRow = ws.rowCount;
    ws.mergeCells(`A${currentRow}:G${currentRow}`);

    // ── Sezioni ──
    const grouped = groupBySection(session.esercizi);

    for (const sectionKey of SECTION_ORDER) {
      const exercises = grouped[sectionKey];
      if (exercises.length === 0) continue;

      const config = SECTION_COLORS[sectionKey];

      // Section header
      ws.addRow([]); // spazio
      const sectionRow = ws.addRow([config.label]);
      const sectionRowNum = ws.rowCount;
      sectionRow.font = { bold: true, size: 9, color: { argb: TEAL } };
      sectionRow.eachCell((cell) => {
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: config.bg } };
      });
      ws.mergeCells(`A${sectionRowNum}:G${sectionRowNum}`);

      // Intestazione tabella (solo per principale)
      if (sectionKey === "principale") {
        const colHeaders = ["#", "Esercizio", "Serie", "Ripetizioni", "Riposo (s)", "Tempo", "Note"];
        const thRow = ws.addRow(colHeaders);
        thRow.eachCell((cell) => {
          cell.font = { bold: true, size: 10, color: { argb: WHITE } };
          cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: TEAL } };
          cell.alignment = { horizontal: "center", vertical: "middle" };
          cell.border = {
            bottom: { style: "thin", color: { argb: TEAL } },
          };
        });
        thRow.getCell(2).alignment = { horizontal: "left", vertical: "middle" };
      }

      // Righe esercizi
      exercises.forEach((ex, idx) => {
        if (sectionKey === "principale") {
          const row = ws.addRow([
            idx + 1,
            ex.esercizio_nome,
            ex.serie,
            ex.ripetizioni,
            ex.tempo_riposo_sec,
            ex.tempo_esecuzione ?? "",
            ex.note ?? "",
          ]);

          // Zebra striping
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
          row.font = { size: 10 };
        } else {
          // Compact per avviamento/stretching
          const row = ws.addRow([
            idx + 1,
            ex.esercizio_nome,
            ex.serie,
            ex.ripetizioni,
            "",
            "",
            ex.note ?? "",
          ]);
          if (idx % 2 === 0) {
            row.eachCell((cell) => {
              cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: config.bg } };
            });
          }
          row.getCell(1).alignment = { horizontal: "center" };
          row.getCell(2).alignment = { horizontal: "left" };
          row.getCell(3).alignment = { horizontal: "center" };
          row.getCell(4).alignment = { horizontal: "center" };
          row.font = { size: 10 };
        }
      });
    }

    // ── Footer ──
    ws.addRow([]);
    const footerRow = ws.addRow(["ProFit AI Studio", "", "", "", "", "", new Date().toLocaleDateString("it-IT")]);
    footerRow.font = { size: 8, italic: true, color: { argb: "999999" } };
  }

  // ── Foglio AI Commentary ──
  if (aiCommentary) {
    const parsed = parseCommentaryForExport(aiCommentary);

    if (parsed.version === 2) {
      // V2: blocchi distribuiti — panoramica, guida per sessione, consigli
      const panoramica = parsed.blocks.find((b) => b.type === "panoramica");
      const consigli = parsed.blocks.find((b) => b.type === "consigli");
      const sessionBlocks = parsed.blocks.filter((b) => b.type === "session") as Array<{
        type: "session"; session_numero: number; session_nome: string; content: string;
      }>;

      // Foglio Panoramica
      if (panoramica?.content) {
        const ws = wb.addWorksheet("Panoramica");
        ws.columns = [{ width: 80 }];
        addCommentaryHeader(ws, "Panoramica del Programma", nome, clientNome);
        writeMarkdownLines(ws, panoramica.content);
        addCommentaryFooter(ws);
      }

      // Guida sessione integrata nei fogli sessione esistenti
      for (const block of sessionBlocks) {
        if (!block.content) continue;
        // Trova il foglio sessione corrispondente
        const sheetName = sessioni
          .find((s) => s.numero_sessione === block.session_numero)
          ?.nome_sessione.slice(0, 31);
        const ws = sheetName ? wb.getWorksheet(sheetName) : null;
        if (!ws) continue;

        // Aggiungi guida in coda al foglio sessione
        ws.addRow([]);
        const guidaHeader = ws.addRow([`Guida — ${block.session_nome}`]);
        guidaHeader.font = { bold: true, size: 11, color: { argb: TEAL } };
        const guidaRowNum = ws.rowCount;
        ws.mergeCells(`A${guidaRowNum}:G${guidaRowNum}`);

        writeMarkdownLines(ws, block.content, 7);
      }

      // Foglio Consigli
      if (consigli?.content) {
        const ws = wb.addWorksheet("Consigli Generali");
        ws.columns = [{ width: 80 }];
        addCommentaryHeader(ws, "Consigli Generali", nome, clientNome);
        writeMarkdownLines(ws, consigli.content);
        addCommentaryFooter(ws);
      }
    } else {
      // V1 fallback: foglio monolitico (invariato)
      const ws = wb.addWorksheet("Guida alla Scheda");
      ws.columns = [{ width: 80 }];
      addCommentaryHeader(ws, "Guida alla Scheda", nome, clientNome);
      writeMarkdownLines(ws, aiCommentary);
      addCommentaryFooter(ws);
    }
  }

  // Download
  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const filename = `${nome.replace(/[^a-zA-Z0-9àèéìòùÀÈÉÌÒÙ\s-]/g, "").trim()}.xlsx`;
  saveAs(blob, filename);
}

// ════════════════════════════════════════════════════════════
// COMMENTARY EXPORT HELPERS
// ════════════════════════════════════════════════════════════

interface CommentaryV2Export {
  version: 2;
  blocks: Array<{
    type: string;
    content?: string;
    session_numero?: number;
    session_nome?: string;
  }>;
}

type ParsedCommentaryExport =
  | { version: 1; text: string }
  | CommentaryV2Export;

function parseCommentaryForExport(raw: string): ParsedCommentaryExport {
  try {
    const parsed = JSON.parse(raw);
    if (parsed?.version === 2 && Array.isArray(parsed?.blocks)) {
      return parsed as CommentaryV2Export;
    }
  } catch {
    // Not JSON — v1
  }
  return { version: 1, text: raw };
}

function addCommentaryHeader(
  ws: ExcelJS.Worksheet,
  title: string,
  nome: string,
  clientNome?: string,
) {
  const titleRow = ws.addRow([title]);
  titleRow.font = { bold: true, size: 14, color: { argb: TEAL } };

  const subRow = ws.addRow([`${nome} — ${clientNome ?? "Scheda generica"}`]);
  subRow.font = { size: 10, color: { argb: "666666" } };

  ws.addRow([]);
}

function addCommentaryFooter(ws: ExcelJS.Worksheet) {
  ws.addRow([]);
  const footerRow = ws.addRow(["ProFit AI Studio — " + new Date().toLocaleDateString("it-IT")]);
  footerRow.font = { size: 8, italic: true, color: { argb: "999999" } };
}

function writeMarkdownLines(ws: ExcelJS.Worksheet, text: string, mergeWidth?: number) {
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) {
      ws.addRow([]);
      continue;
    }

    const clean = trimmed.replace(/\*\*(.+?)\*\*/g, "$1");

    if (trimmed.startsWith("## ")) {
      const row = ws.addRow([clean.slice(3)]);
      row.font = { bold: true, size: 12, color: { argb: TEAL } };
      if (mergeWidth) ws.mergeCells(`A${ws.rowCount}:${colLetter(mergeWidth)}${ws.rowCount}`);
    } else if (trimmed.startsWith("### ")) {
      const row = ws.addRow([clean.slice(4)]);
      row.font = { bold: true, size: 10 };
      if (mergeWidth) ws.mergeCells(`A${ws.rowCount}:${colLetter(mergeWidth)}${ws.rowCount}`);
    } else if (trimmed.startsWith("- ")) {
      const row = ws.addRow([`  \u2022 ${clean.slice(2)}`]);
      row.font = { size: 10 };
      row.alignment = { wrapText: true };
      if (mergeWidth) ws.mergeCells(`A${ws.rowCount}:${colLetter(mergeWidth)}${ws.rowCount}`);
    } else {
      const row = ws.addRow([clean]);
      row.font = { size: 10 };
      row.alignment = { wrapText: true };
      if (mergeWidth) ws.mergeCells(`A${ws.rowCount}:${colLetter(mergeWidth)}${ws.rowCount}`);
    }
  }
}

function colLetter(n: number): string {
  return String.fromCharCode(64 + n); // 1→A, 7→G
}
