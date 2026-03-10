import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type { InstallationSupportSnapshotResponse } from "@/types/api";

function buildSnapshotFilename() {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  return `fitmanager-support-snapshot-${timestamp}.json`;
}

async function downloadSupportSnapshot() {
  const { data } = await apiClient.get<InstallationSupportSnapshotResponse>(
    "/system/support-snapshot",
  );
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = buildSnapshotFilename();
  a.click();
  URL.revokeObjectURL(url);
}

export function useDownloadSupportSnapshot() {
  return useMutation({
    mutationFn: downloadSupportSnapshot,
    onSuccess: () => {
      toast.success("Snapshot diagnostico scaricato");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nel download dello snapshot diagnostico"),
      );
    },
  });
}
