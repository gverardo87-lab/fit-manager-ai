"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { ShieldAlert, Mail, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const STATUS_CONFIG: Record<string, { label: string; description: string; color: string }> = {
  missing: {
    label: "Non trovata",
    description: "Nessun file di licenza presente. Contatta il supporto per ricevere la tua licenza.",
    color: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  },
  expired: {
    label: "Scaduta",
    description: "La tua licenza e' scaduta. Contatta il supporto per rinnovarla.",
    color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
  invalid: {
    label: "Non valida",
    description: "Il file di licenza non e' valido. Potrebbe essere corrotto o non autorizzato.",
    color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
  unconfigured: {
    label: "Non configurata",
    description: "Il sistema di licenza non e' ancora configurato. Contatta il supporto.",
    color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
  },
}

const DEFAULT_CONFIG = {
  label: "Problema licenza",
  description: "Si e' verificato un problema con la licenza. Contatta il supporto.",
  color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
}

function LicenzaContent() {
  const searchParams = useSearchParams()
  const status = searchParams.get("status") ?? "missing"
  const config = STATUS_CONFIG[status] ?? DEFAULT_CONFIG

  return (
    <Card className="w-full max-w-md shadow-xl">
      <CardHeader className="text-center">
        <div className="bg-primary/10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full">
          <ShieldAlert className="text-primary h-8 w-8" />
        </div>
        <CardTitle className="text-2xl">Licenza FitManager</CardTitle>
        <Badge className={`mx-auto mt-2 ${config.color}`}>{config.label}</Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-muted-foreground text-center text-sm">
          {config.description}
        </p>

        <div className="bg-muted rounded-lg p-4">
          <h3 className="mb-2 text-sm font-medium">Come risolvere</h3>
          <ol className="text-muted-foreground list-inside list-decimal space-y-1 text-sm">
            <li>Contatta il supporto tecnico</li>
            <li>Riceverai un file di licenza aggiornato</li>
            <li>Posizionalo nella cartella dati dell&apos;applicazione</li>
            <li>Riavvia FitManager</li>
          </ol>
        </div>

        <div className="flex flex-col gap-2">
          <Button
            className="w-full"
            onClick={() => {
              window.location.href = "mailto:supporto@fitmanager.it?subject=Licenza%20FitManager"
            }}
          >
            <Mail className="mr-2 h-4 w-4" />
            Contatta supporto
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              window.location.href = "/login"
            }}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Torna al login
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function LicenzaPage() {
  return (
    <div className="bg-mesh-login flex min-h-screen items-center justify-center p-4">
      <Suspense>
        <LicenzaContent />
      </Suspense>
    </div>
  )
}
