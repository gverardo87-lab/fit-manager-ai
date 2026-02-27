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
import type { WorkoutExerciseRow, SafetyMapResponse, ExerciseSafetyEntry } from "@/types/api";

const TEAL = "009688";
const WHITE = "FFFFFF";
const LIGHT_TEAL = "E0F2F1";
const AMBER_LIGHT = "FFF8E1";
const CYAN_LIGHT = "E0F7FA";
const RED_LIGHT = "FFEBEE";
const RED = "C62828";
const AMBER = "E65100";

const SECTION_COLORS: Record<TemplateSection, { bg: string; label: string }> = {
  avviamento: { bg: AMBER_LIGHT, label: "AVVIAMENTO" },
  principale: { bg: LIGHT_TEAL, label: "ESERCIZIO PRINCIPALE" },
  stretching: { bg: CYAN_LIGHT, label: "STRETCHING & MOBILITA" },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

interface SafetyExportData {
  clientNome: string;
  conditionNames: string[];
  /** Condizioni raggruppate: { condizione, severita, esercizi coinvolti } */
  rows: { condizione: string; severita: string; esercizi: string[] }[];
}

interface ExportData {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  sessioni: SessionCardData[];
  safety?: SafetyExportData;
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
  safety,
}: ExportData): Promise<void> {
  const wb = new ExcelJS.Workbook();
  wb.creator = "ProFit AI Studio";
  wb.created = new Date();

  // ── Foglio Profilo Clinico (se safety presente) ──
  if (safety && safety.rows.length > 0) {
    const ws = wb.addWorksheet("Profilo Clinico");
    ws.columns = [
      { width: 6 },   // #
      { width: 30 },  // Condizione
      { width: 12 },  // Severita
      { width: 50 },  // Esercizi coinvolti
    ];

    // Header
    const titleRow = ws.addRow([`Profilo Clinico — ${safety.clientNome}`]);
    titleRow.font = { bold: true, size: 14, color: { argb: RED } };
    ws.mergeCells("A1:D1");

    const subRow = ws.addRow([`${safety.conditionNames.length} condizioni rilevate — Scheda: ${nome}`]);
    subRow.font = { size: 10, color: { argb: "666666" } };
    ws.mergeCells("A2:D2");

    ws.addRow([]);

    // Intestazione tabella
    const thRow = ws.addRow(["#", "Condizione Medica", "Severita", "Esercizi Coinvolti"]);
    thRow.eachCell((cell) => {
      cell.font = { bold: true, size: 10, color: { argb: WHITE } };
      cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: RED } };
      cell.alignment = { horizontal: "center", vertical: "middle" };
    });
    thRow.getCell(2).alignment = { horizontal: "left", vertical: "middle" };
    thRow.getCell(4).alignment = { horizontal: "left", vertical: "middle" };

    // Righe condizioni
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

      // Zebra striping rosso chiaro
      if (idx % 2 === 0) {
        dataRow.eachCell((cell) => {
          cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: RED_LIGHT } };
        });
      }
    });

    // Footer
    ws.addRow([]);
    const note = ws.addRow(["Nota: questo foglio e' informativo. Il trainer decide SEMPRE."]);
    note.font = { size: 9, italic: true, color: { argb: "999999" } };
    ws.mergeCells(`A${ws.rowCount}:D${ws.rowCount}`);
  }

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

  // Download
  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const filename = `${nome.replace(/[^a-zA-Z0-9àèéìòùÀÈÉÌÒÙ\s-]/g, "").trim()}.xlsx`;
  saveAs(blob, filename);
}
