/**
 * Utility di formattazione centralizzate.
 *
 * Importare da qui invece di definire localmente in ogni componente.
 */

/** Formatta un numero come valuta EUR italiana (es. "€ 1.200,00"). */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

/**
 * Converte Date in stringa ISO LOCALE senza suffisso "Z".
 *
 * Perche': il backend salva datetime naive (senza timezone).
 * Se usi `toISOString()`, la data viene convertita in UTC e l'ora
 * si sposta di -1h (inverno) o -2h (estate) rispetto a ora locale.
 *
 * Esempio (CET, UTC+1):
 *   new Date("12:00 locale").toISOString()  → "11:00:00.000Z"  (SBAGLIATO)
 *   toISOLocal(new Date("12:00 locale"))    → "12:00:00"        (CORRETTO)
 */
/**
 * Formatta una data ISO "YYYY-MM-DD" come "3 gen 2026" (italiano).
 * Senza anno: "3 gen".
 */
export function formatShortDate(dateStr: string, withYear = true): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "short",
    ...(withYear && { year: "numeric" }),
  });
}

/**
 * Formatta una data ISO con ora: "25/02/2026, 14:30".
 */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Classe colore Tailwind per progress bar finanze (emerald/amber/red). */
export function getFinanceBarColor(ratio: number): string {
  if (ratio >= 0.8) return "bg-emerald-500";
  if (ratio >= 0.4) return "bg-amber-500";
  return "bg-red-500";
}

export function toISOLocal(date: Date): string {
  const Y = date.getFullYear();
  const M = String(date.getMonth() + 1).padStart(2, "0");
  const D = String(date.getDate()).padStart(2, "0");
  const h = String(date.getHours()).padStart(2, "0");
  const m = String(date.getMinutes()).padStart(2, "0");
  const s = String(date.getSeconds()).padStart(2, "0");
  return `${Y}-${M}-${D}T${h}:${m}:${s}`;
}
