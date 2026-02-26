/**
 * Genera SVG statici delle muscle map per ogni esercizio.
 *
 * Usa react-dom/server + react-muscle-highlighter per renderizzare
 * SVG front-only per ogni esercizio, salvati come file statici.
 *
 * Eseguire dalla directory frontend:
 *   cd frontend && npx tsx ../tools/admin_scripts/generate-muscle-maps.ts
 *
 * Requisiti: sql.js (npm install --save-dev sql.js)
 */

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import Body from "react-muscle-highlighter";
import type { ExtendedBodyPart, Slug } from "react-muscle-highlighter";
import initSqlJs from "sql.js";
import * as fs from "fs";
import * as path from "path";

// ════════════════════════════════════════════════════════════
// MUSCLE MAP UTILS (same logic as lib/muscle-map-utils.ts)
// Duplicated here to avoid TS path alias resolution issues
// ════════════════════════════════════════════════════════════

const MUSCLE_SLUG_MAP: Record<string, Slug[]> = {
  quadriceps: ["quadriceps"],
  hamstrings: ["hamstring"],
  glutes: ["gluteal"],
  calves: ["calves"],
  adductors: ["adductors"],
  chest: ["chest"],
  back: ["upper-back", "lower-back"],
  lats: ["upper-back"],
  shoulders: ["deltoids"],
  traps: ["trapezius"],
  biceps: ["biceps"],
  triceps: ["triceps"],
  forearms: ["forearm"],
  core: ["abs", "obliques"],
};

const FRONT_SLUGS: Set<Slug> = new Set([
  "abs", "adductors", "biceps", "calves", "chest", "deltoids",
  "forearm", "obliques", "quadriceps", "tibialis", "trapezius",
]);

function buildBodyData(
  muscles: string[],
  intensity: number,
  sideFilter: Set<Slug>,
): ExtendedBodyPart[] {
  const seen = new Set<Slug>();
  const parts: ExtendedBodyPart[] = [];

  for (const muscle of muscles) {
    const slugs = MUSCLE_SLUG_MAP[muscle];
    if (!slugs) continue;
    for (const slug of slugs) {
      if (sideFilter.has(slug) && !seen.has(slug)) {
        seen.add(slug);
        parts.push({ slug, intensity });
      }
    }
  }

  return parts;
}

// ════════════════════════════════════════════════════════════
// CONFIG
// ════════════════════════════════════════════════════════════

// Colori teal accent (coerenza brand)
const COLORS = ["#0d9488", "#5eead4"]; // teal-600 (primari), teal-300 (secondari)
const DEFAULT_FILL = "#e5e7eb"; // zinc-200

// Paths
const SCRIPT_DIR = path.dirname(new URL(import.meta.url).pathname);
// Handle Windows paths: /C:/... → C:/...
const normalizedDir = SCRIPT_DIR.replace(/^\/([A-Z]:)/, "$1");
const BASE_DIR = path.resolve(normalizedDir, "..", "..");
const MEDIA_DIR = path.join(BASE_DIR, "data", "media", "exercises");
const DBS = [
  path.join(BASE_DIR, "data", "crm.db"),
  path.join(BASE_DIR, "data", "crm_dev.db"),
];

// ════════════════════════════════════════════════════════════
// SVG GENERATION
// ════════════════════════════════════════════════════════════

interface ExerciseRow {
  id: number;
  nome: string;
  muscoli_primari: string;
  muscoli_secondari: string | null;
}

function generateSvg(primari: string[], secondari: string[]): string {
  const frontData = [
    ...buildBodyData(primari, 1, FRONT_SLUGS),
    ...buildBodyData(secondari, 2, FRONT_SLUGS),
  ];

  const element = createElement(Body, {
    data: frontData,
    side: "front",
    gender: "male",
    scale: 0.3,
    colors: COLORS,
    border: "none",
    defaultFill: DEFAULT_FILL,
  });

  return renderToStaticMarkup(element);
}

// ════════════════════════════════════════════════════════════
// MAIN
// ════════════════════════════════════════════════════════════

async function main() {
  console.log("Muscle Map SVG Generator");
  console.log("=".repeat(60));

  const SQL = await initSqlJs();

  for (const dbPath of DBS) {
    if (!fs.existsSync(dbPath)) {
      console.log(`  SKIP: ${dbPath} not found`);
      continue;
    }

    const dbName = path.basename(dbPath);
    console.log(`\n  Processing: ${dbName}`);

    const buffer = fs.readFileSync(dbPath);
    const db = new SQL.Database(buffer);

    // Fetch active exercises
    const rows = db.exec(
      "SELECT id, nome, muscoli_primari, muscoli_secondari FROM esercizi WHERE deleted_at IS NULL ORDER BY id"
    );

    if (!rows.length || !rows[0].values.length) {
      console.log("    No exercises found");
      db.close();
      continue;
    }

    const exercises: ExerciseRow[] = rows[0].values.map((row) => ({
      id: row[0] as number,
      nome: row[1] as string,
      muscoli_primari: row[2] as string,
      muscoli_secondari: row[3] as string | null,
    }));

    console.log(`    Found ${exercises.length} exercises`);

    let generated = 0;
    let skipped = 0;

    for (const ex of exercises) {
      let primari: string[] = [];
      let secondari: string[] = [];

      try {
        primari = JSON.parse(ex.muscoli_primari || "[]");
      } catch {
        primari = [];
      }
      try {
        secondari = JSON.parse(ex.muscoli_secondari || "[]");
      } catch {
        secondari = [];
      }

      if (primari.length === 0) {
        skipped++;
        continue;
      }

      // Generate SVG
      const svg = generateSvg(primari, secondari);

      // Save file
      const exerciseDir = path.join(MEDIA_DIR, String(ex.id));
      fs.mkdirSync(exerciseDir, { recursive: true });
      const svgPath = path.join(exerciseDir, "muscle-map.svg");
      fs.writeFileSync(svgPath, svg, "utf-8");

      // Update DB
      const relativeUrl = `/media/exercises/${ex.id}/muscle-map.svg`;
      db.run("UPDATE esercizi SET muscle_map_url = ? WHERE id = ?", [relativeUrl, ex.id]);

      generated++;
    }

    // Save DB back
    const data = db.export();
    const dbBuffer = Buffer.from(data);
    fs.writeFileSync(dbPath, dbBuffer);
    db.close();

    console.log(`    Generated: ${generated}, Skipped (no muscles): ${skipped}`);
    console.log(`    DB updated: ${dbName}`);
  }

  console.log("\nDone.");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
