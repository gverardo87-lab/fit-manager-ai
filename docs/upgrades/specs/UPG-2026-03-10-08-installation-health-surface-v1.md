# Patch Spec - Installation Health Surface v1

## Metadata

- Upgrade ID: UPG-2026-03-10-08
- Date: 2026-03-10
- Owner: Codex
- Area: Cross-layer (API + Frontend + Deployment UX)
- Priority: high
- Status: done

## Problem

FitManager e gia installabile e protetto a livello di licensing/packaging, ma mancava una superficie
interna al prodotto che rendesse subito verificabile:

1. quale build sta girando;
2. se il gate licenza e davvero attivo;
3. se l'istanza e in `dev` o `prod`;
4. se i due database locali sono sani;
5. se il portale pubblico e configurato in modo coerente.

Senza questa visibilita, l'affidabilita resta implicita e il supporto post-vendita parte alla cieca.

## Desired Outcome

La pagina `Impostazioni` deve mostrare uno stato installazione chiaro e leggibile, utile sia al trainer
sia al supporto:

- versione applicazione
- modalita runtime (`source` vs `installer`)
- ambiente (`development` vs `production`)
- stato enforcement licenza
- stato licenza
- connessione DB business e catalog
- stato portale pubblico
- uptime e orario di avvio istanza

## Scope

- In scope:
  - tipizzazione backend del payload `/health`
  - arricchimento `/health` con metadati runtime
  - proxy Next.js same-origin per `/health`
  - allowlist middleware frontend per `/health`
  - hook frontend dedicato
  - nuova sezione `Stato installazione` in `Impostazioni`
  - sync docs upgrade + checklist `CLAUDE.md`
- Out of scope:
  - support bundle scaricabile
  - logging persistente locale
  - wizard di diagnostica guidata
  - check attivi LAN/Tailscale dal browser

## Implementation

### Backend

- Nuovo schema `api/schemas/system.py` con `HealthResponse`.
- `/health` ora espone:
  - `license_enforcement_enabled`
  - `app_mode`
  - `distribution_mode`
  - `public_portal_enabled`
  - `public_base_url_configured`
  - `started_at`
  - `uptime_seconds`
- Il payload resta compatibile con i consumatori esistenti (`status`, `version`, `db`, `catalog`, `license_status`).

### Frontend

- `frontend/next.config.ts`: rewrite same-origin di `/health` verso il backend.
- `frontend/src/middleware.ts`: `/health` aggiunto alle `PUBLIC_ROUTES`.
- `frontend/src/hooks/useSystemHealth.ts`: query React Query dedicata.
- `frontend/src/components/settings/SystemStatusSection.tsx`: nuova card con advisory state-aware.
- `frontend/src/app/(dashboard)/impostazioni/page.tsx`: integrazione della nuova sezione.
- `frontend/src/types/api.ts`: mirror TypeScript del payload health.

## Verification

- `venv\Scripts\ruff.exe check api/main.py api/schemas/system.py`
- `npm --prefix frontend run lint -- "src/app/(dashboard)/impostazioni/page.tsx" "src/components/settings/SystemStatusSection.tsx" "src/hooks/useSystemHealth.ts" "src/middleware.ts"`
- `npm --prefix frontend run build`

## Risks / Residuals

1. Il warning Next 16 su `middleware` deprecato resta preesistente: da migrare a `proxy` in un microstep dedicato.
2. Il pannello espone metadati runtime ma non genera ancora un pacchetto di supporto esportabile.
3. `PUBLIC_BASE_URL` viene mostrato come stato configurato/non configurato, non come URL completo: scelta intenzionale per tenere il payload health sobrio e non farne una pagina di debug.

## Next Smallest Step

Implementare un `support snapshot` read-only scaricabile da `Impostazioni` con:

- versione
- health runtime
- stato licenza
- flag portale pubblico
- timestamp
- ultimi backup disponibili

senza includere PII o dati business.
