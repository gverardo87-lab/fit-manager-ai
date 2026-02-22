// src/hooks/useBackup.ts
/**
 * Custom hooks per il modulo Backup.
 *
 * Pattern: una funzione per operazione.
 * - useBackups()       — lista backup disponibili
 * - useCreateBackup()  — crea backup atomico
 * - useRestoreBackup() — ripristina da file upload
 * - downloadBackup()   — scarica file .sqlite (helper, non hook)
 * - exportTrainerData() — scarica JSON GDPR (helper, non hook)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  BackupInfo,
  BackupCreateResponse,
  BackupRestoreResponse,
} from "@/types/api";

// ── Query: lista backup ──

export function useBackups() {
  return useQuery<BackupInfo[]>({
    queryKey: ["backups"],
    queryFn: async () => {
      const { data } = await apiClient.get<BackupInfo[]>("/backup/list");
      return data;
    },
  });
}

// ── Mutation: crea backup ──

export function useCreateBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<BackupCreateResponse>(
        "/backup/create"
      );
      return data;
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["backups"] });
      toast.success(res.message);
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nella creazione del backup")
      );
    },
  });
}

// ── Mutation: restore da file upload ──

export function useRestoreBackup() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<BackupRestoreResponse>(
        "/backup/restore",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return data;
    },
    onSuccess: (res) => {
      toast.success(res.message);
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nel ripristino del backup")
      );
    },
  });
}

// ── Helper: scarica file backup (blob + JWT) ──

export async function downloadBackup(filename: string) {
  try {
    const { data } = await apiClient.get(`/backup/download/${filename}`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    toast.error(extractErrorMessage(error, "Errore nel download del backup"));
  }
}

// ── Helper: export JSON GDPR ──

export async function exportTrainerData() {
  try {
    const { data } = await apiClient.get("/backup/export");
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Export completato");
  } catch (error) {
    toast.error(
      extractErrorMessage(error, "Errore nell'export dei dati")
    );
  }
}
