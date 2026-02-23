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
export function toISOLocal(date: Date): string {
  const Y = date.getFullYear();
  const M = String(date.getMonth() + 1).padStart(2, "0");
  const D = String(date.getDate()).padStart(2, "0");
  const h = String(date.getHours()).padStart(2, "0");
  const m = String(date.getMinutes()).padStart(2, "0");
  const s = String(date.getSeconds()).padStart(2, "0");
  return `${Y}-${M}-${D}T${h}:${m}:${s}`;
}
