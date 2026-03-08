// src/components/clients/profile/PanoramicaTab.tsx
"use client";

import { format } from "date-fns";
import { it } from "date-fns/locale";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PanoramicaTabProps {
  client: {
    data_nascita: string | null;
    sesso: string | null;
    note_interne: string | null;
  };
}

export function PanoramicaTab({ client }: PanoramicaTabProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Informazioni personali</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Data di nascita</span>
            <span className="font-medium">
              {client.data_nascita
                ? format(new Date(client.data_nascita + "T00:00:00"), "dd MMMM yyyy", { locale: it })
                : "—"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Sesso</span>
            <span className="font-medium">{client.sesso ?? "—"}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Note interne</CardTitle>
        </CardHeader>
        <CardContent>
          {client.note_interne ? (
            <p className="whitespace-pre-line text-sm">{client.note_interne}</p>
          ) : (
            <p className="text-sm italic text-muted-foreground">Nessuna nota</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
