import type { TSPlanPackage } from "@/types/api";

const STORAGE_PREFIX = "fitmanager.smart-plan-package";
const MAX_AGE_MS = 2 * 60 * 60 * 1000;

interface StoredSmartPlanPackage {
  storedAt: number;
  planPackage: TSPlanPackage;
}

function getStorageKey(workoutId: number): string {
  return `${STORAGE_PREFIX}.${workoutId}`;
}

function readStoredPlanPackage(workoutId: number): StoredSmartPlanPackage | null {
  if (typeof window === "undefined") return null;

  const raw = window.sessionStorage.getItem(getStorageKey(workoutId));
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as StoredSmartPlanPackage;
    if (
      typeof parsed !== "object" ||
      parsed === null ||
      typeof parsed.storedAt !== "number" ||
      typeof parsed.planPackage !== "object" ||
      parsed.planPackage === null
    ) {
      window.sessionStorage.removeItem(getStorageKey(workoutId));
      return null;
    }
    return parsed;
  } catch {
    window.sessionStorage.removeItem(getStorageKey(workoutId));
    return null;
  }
}

export function storeSmartPlanPackage(workoutId: number, planPackage: TSPlanPackage): void {
  if (typeof window === "undefined") return;

  const payload: StoredSmartPlanPackage = {
    storedAt: Date.now(),
    planPackage,
  };
  window.sessionStorage.setItem(getStorageKey(workoutId), JSON.stringify(payload));
}

export function consumeSmartPlanPackage(workoutId: number): TSPlanPackage | null {
  const stored = readStoredPlanPackage(workoutId);
  if (!stored) return null;

  window.sessionStorage.removeItem(getStorageKey(workoutId));
  if (Date.now() - stored.storedAt > MAX_AGE_MS) {
    return null;
  }

  return stored.planPackage;
}
