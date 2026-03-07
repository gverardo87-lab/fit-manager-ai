import type { TSAnalisiPiano, TSAnalisiVolume } from "@/types/api";

export type BackendVolumeStatusKey = "deficit" | "suboptimal" | "optimal" | "excess";

export interface BackendVolumeCounts {
  deficit: number;
  suboptimal: number;
  optimal: number;
  excess: number;
  attention: number;
  total: number;
}

export interface BackendMuscleMapBuckets {
  optimal: string[];
  suboptimal: string[];
  excess: string[];
  deficit: string[];
  activeCount: number;
}

const ANALYSIS_TO_SLUG_KEY: Record<string, string> = {
  petto: "chest",
  dorsali: "back",
  deltoide_anteriore: "shoulders",
  deltoide_laterale: "shoulders",
  deltoide_posteriore: "shoulders",
  bicipiti: "biceps",
  tricipiti: "triceps",
  quadricipiti: "quadriceps",
  femorali: "hamstrings",
  glutei: "glutes",
  polpacci: "calves",
  trapezio: "traps",
  core: "core",
  avambracci: "forearms",
  adduttori: "adductors",
};

export function mapBackendVolumeStatus(stato: string): BackendVolumeStatusKey {
  switch (stato) {
    case "sotto_mev":
      return "deficit";
    case "mev_mav":
      return "suboptimal";
    case "ottimale":
      return "optimal";
    case "sopra_mav":
    case "sopra_mrv":
      return "excess";
    default:
      return "optimal";
  }
}

export function getBackendVolumeCounts(
  analysis: TSAnalisiPiano | null | undefined,
): BackendVolumeCounts {
  if (!analysis) {
    return {
      deficit: 0,
      suboptimal: 0,
      optimal: 0,
      excess: 0,
      attention: 0,
      total: 0,
    };
  }

  const counts = analysis.volume.per_muscolo.reduce<BackendVolumeCounts>(
    (acc, muscle) => {
      const status = mapBackendVolumeStatus(muscle.stato);
      acc[status] += 1;
      acc.total += 1;
      return acc;
    },
    {
      deficit: 0,
      suboptimal: 0,
      optimal: 0,
      excess: 0,
      attention: 0,
      total: 0,
    },
  );

  counts.attention = counts.deficit + counts.suboptimal + counts.excess;
  return counts;
}

export function buildBackendMuscleMapBuckets(
  volume: TSAnalisiVolume | null | undefined,
): BackendMuscleMapBuckets {
  const buckets: BackendMuscleMapBuckets = {
    optimal: [],
    suboptimal: [],
    excess: [],
    deficit: [],
    activeCount: 0,
  };

  if (!volume) return buckets;

  const slugStatus = new Map<string, BackendVolumeStatusKey>();
  const statusPriority: Record<BackendVolumeStatusKey, number> = {
    optimal: 0,
    suboptimal: 1,
    excess: 2,
    deficit: 3,
  };

  for (const muscle of volume.per_muscolo) {
    const slugKey = ANALYSIS_TO_SLUG_KEY[muscle.muscolo];
    if (!slugKey) continue;
    const status = mapBackendVolumeStatus(muscle.stato);
    const current = slugStatus.get(slugKey);
    if (!current || statusPriority[status] > statusPriority[current]) {
      slugStatus.set(slugKey, status);
    }
  }

  for (const [slugKey, status] of slugStatus.entries()) {
    buckets[status].push(slugKey);
  }

  buckets.activeCount =
    buckets.optimal.length +
    buckets.suboptimal.length +
    buckets.excess.length +
    buckets.deficit.length;

  return buckets;
}
