import type { BlockType } from "@/types/api";

export interface BlockPreviewMetric {
  label: string;
  value: string;
}

interface BlockMetricSource {
  giri: number;
  durata_lavoro_sec: number | null;
  durata_riposo_sec: number | null;
  durata_blocco_sec: number | null;
}

export function buildBlockMetrics(
  block: BlockMetricSource,
  tipo: BlockType,
): BlockPreviewMetric[] {
  const metrics: BlockPreviewMetric[] = [];
  const push = (label: string, value: string | null): void => {
    if (!value) return;
    metrics.push({ label, value });
  };

  const giriLabel = tipo === "emom" ? "Minuti" : "Giri";
  const giriValue = block.giri > 0 ? String(block.giri) : null;
  const lavoroValue = block.durata_lavoro_sec ? `${block.durata_lavoro_sec}s` : null;
  const recuperoValue = block.durata_riposo_sec ? `${block.durata_riposo_sec}s` : null;
  const durataValue = block.durata_blocco_sec
    ? `${Math.round(block.durata_blocco_sec / 60)} min`
    : null;

  switch (tipo) {
    case "tabata":
      push("Lavoro", lavoroValue);
      push("Recupero", recuperoValue);
      push(giriLabel, giriValue);
      push("Durata", durataValue);
      break;
    case "amrap":
    case "for_time":
      push("Durata", durataValue);
      push(giriLabel, giriValue);
      push("Recupero", recuperoValue);
      break;
    case "emom":
      push(giriLabel, giriValue);
      push("Lavoro", lavoroValue);
      push("Recupero", recuperoValue);
      push("Durata", durataValue);
      break;
    default:
      push(giriLabel, giriValue);
      push("Lavoro", lavoroValue);
      push("Recupero", recuperoValue);
      push("Durata", durataValue);
      break;
  }

  return metrics;
}
