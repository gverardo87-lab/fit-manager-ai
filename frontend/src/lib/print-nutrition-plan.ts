// src/lib/print-nutrition-plan.ts
/**
 * Genera una finestra di stampa ottimizzata per il piano alimentare.
 * Apre una nuova tab con HTML puro, chiama window.print() dopo un breve delay.
 */

import type { NutritionPlanDetail } from "@/types/api";

const MEAL_LABELS: Record<string, string> = {
  COLAZIONE: "Colazione",
  SPUNTINO_MATTINA: "Spuntino mattina",
  PRANZO: "Pranzo",
  SPUNTINO_POMERIGGIO: "Merenda",
  CENA: "Cena",
  PRE_WORKOUT: "Pre-workout",
  POST_WORKOUT: "Post-workout",
};

const GIORNO_LABELS: Record<number, string> = {
  0: "Ogni giorno",
  1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì",
  5: "Venerdì", 6: "Sabato", 7: "Domenica",
};

export function printNutritionPlan(plan: NutritionPlanDetail): void {
  const days = Array.from(
    new Set([0, ...plan.pasti.map((m) => m.giorno_settimana)])
  ).sort((a, b) => a - b);

  const dayBlocks = days.map((giorno) => {
    const meals = plan.pasti.filter((m) => m.giorno_settimana === giorno);
    if (meals.length === 0) return "";

    const dayTotals = meals.reduce(
      (acc, m) => ({
        kcal: acc.kcal + m.totale_kcal,
        p: acc.p + m.totale_proteine_g,
        c: acc.c + m.totale_carboidrati_g,
        g: acc.g + m.totale_grassi_g,
      }),
      { kcal: 0, p: 0, c: 0, g: 0 }
    );

    const mealBlocks = meals.map((meal) => {
      const label = meal.nome ?? MEAL_LABELS[meal.tipo_pasto] ?? meal.tipo_pasto;
      const rows = meal.componenti
        .map(
          (c) =>
            `<tr><td>${c.alimento_nome ?? `Alimento #${c.alimento_id}`}</td><td class="num">${c.quantita_g}g</td><td class="num">${Math.round(c.energia_kcal)} kcal</td><td class="num">P${Math.round(c.proteine_g)}g C${Math.round(c.carboidrati_g)}g G${Math.round(c.grassi_g)}g</td></tr>`
        )
        .join("");
      return `
        <div class="meal">
          <div class="meal-header">
            <strong>${label}</strong>
            <span class="meal-kcal">${Math.round(meal.totale_kcal)} kcal &nbsp;·&nbsp; P${Math.round(meal.totale_proteine_g)}g C${Math.round(meal.totale_carboidrati_g)}g G${Math.round(meal.totale_grassi_g)}g</span>
          </div>
          ${rows ? `<table><thead><tr><th>Alimento</th><th class="num">Quantità</th><th class="num">Calorie</th><th class="num">Macro</th></tr></thead><tbody>${rows}</tbody></table>` : ""}
        </div>`;
    }).join("");

    return `
      <div class="day">
        <h2>${GIORNO_LABELS[giorno] ?? `Giorno ${giorno}`}
          <span class="day-totals">&nbsp;·&nbsp; ${Math.round(dayTotals.kcal)} kcal &nbsp;·&nbsp; P${Math.round(dayTotals.p)}g C${Math.round(dayTotals.c)}g G${Math.round(dayTotals.g)}g</span>
        </h2>
        ${mealBlocks}
      </div>`;
  }).join("");

  const targetLine = [
    plan.obiettivo_calorico ? `Target: ${plan.obiettivo_calorico} kcal/die` : "",
    plan.proteine_g_target ? `P ${plan.proteine_g_target}g` : "",
    plan.carboidrati_g_target ? `C ${plan.carboidrati_g_target}g` : "",
    plan.grassi_g_target ? `G ${plan.grassi_g_target}g` : "",
  ].filter(Boolean).join(" · ");

  const html = `<!DOCTYPE html><html lang="it"><head>
  <meta charset="utf-8">
  <title>${plan.nome}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; font-size: 11px; color: #111; padding: 20px; }
    h1 { font-size: 18px; margin-bottom: 4px; }
    .meta { color: #555; font-size: 10px; margin-bottom: 20px; }
    .day { margin-bottom: 22px; page-break-inside: avoid; }
    h2 { font-size: 13px; font-weight: bold; background: #f0f0f0; padding: 5px 10px; border-radius: 3px; margin-bottom: 8px; }
    .day-totals { font-size: 11px; font-weight: normal; color: #444; }
    .meal { margin-bottom: 10px; padding-left: 8px; }
    .meal-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
    .meal-kcal { color: #555; font-size: 10px; }
    table { width: 100%; border-collapse: collapse; font-size: 10px; }
    th, td { text-align: left; padding: 2px 6px; border-bottom: 1px solid #eee; }
    th { background: #fafafa; font-weight: 600; color: #444; }
    .num { text-align: right; }
    @media print { body { padding: 0; } }
  </style>
  </head><body>
  <h1>${plan.nome}</h1>
  <p class="meta">${targetLine}${plan.data_inizio ? ` &nbsp;·&nbsp; Dal ${plan.data_inizio}` : ""}${plan.data_fine ? ` al ${plan.data_fine}` : ""}</p>
  ${dayBlocks}
  </body></html>`;

  const w = window.open("", "_blank");
  if (w) {
    w.document.write(html);
    w.document.close();
    setTimeout(() => w.print(), 350);
  }
}
