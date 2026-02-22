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
