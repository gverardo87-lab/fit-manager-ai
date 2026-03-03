import { buildBlockMetrics } from "@/lib/workout-preview-block-metrics";
import type { BlockType } from "@/types/api";

function makeBlock(overrides?: Partial<{
  giri: number;
  durata_lavoro_sec: number | null;
  durata_riposo_sec: number | null;
  durata_blocco_sec: number | null;
}>) {
  return {
    giri: 3,
    durata_lavoro_sec: 20,
    durata_riposo_sec: 10,
    durata_blocco_sec: 240,
    ...overrides,
  };
}

describe("buildBlockMetrics", () => {
  it("orders tabata metrics as work/recovery/rounds/duration", () => {
    const metrics = buildBlockMetrics(makeBlock(), "tabata");

    expect(metrics).toEqual([
      { label: "Lavoro", value: "20s" },
      { label: "Recupero", value: "10s" },
      { label: "Giri", value: "3" },
      { label: "Durata", value: "4 min" },
    ]);
  });

  it("uses 'Minuti' label for emom", () => {
    const metrics = buildBlockMetrics(
      makeBlock({ giri: 12, durata_lavoro_sec: 40, durata_riposo_sec: null, durata_blocco_sec: 600 }),
      "emom",
    );

    expect(metrics).toEqual([
      { label: "Minuti", value: "12" },
      { label: "Lavoro", value: "40s" },
      { label: "Durata", value: "10 min" },
    ]);
  });

  it("prioritizes duration for amrap and for_time", () => {
    const block = makeBlock({ giri: 5, durata_lavoro_sec: null, durata_riposo_sec: 30, durata_blocco_sec: 725 });

    const amrap = buildBlockMetrics(block, "amrap");
    const forTime = buildBlockMetrics(block, "for_time");

    expect(amrap).toEqual([
      { label: "Durata", value: "12 min" },
      { label: "Giri", value: "5" },
      { label: "Recupero", value: "30s" },
    ]);
    expect(forTime).toEqual(amrap);
  });

  it("returns empty metrics when no values are available", () => {
    const metrics = buildBlockMetrics(
      makeBlock({
        giri: 0,
        durata_lavoro_sec: null,
        durata_riposo_sec: null,
        durata_blocco_sec: null,
      }),
      "circuit",
    );

    expect(metrics).toEqual([]);
  });

  it("keeps default ordering for classic structured blocks", () => {
    const block = makeBlock({ giri: 4, durata_lavoro_sec: null, durata_riposo_sec: 20, durata_blocco_sec: 360 });
    const types: BlockType[] = ["circuit", "superset"];

    for (const type of types) {
      expect(buildBlockMetrics(block, type)).toEqual([
        { label: "Giri", value: "4" },
        { label: "Recupero", value: "20s" },
        { label: "Durata", value: "6 min" },
      ]);
    }
  });
});
