# UPG-2026-03-04-04 - Assistant Frontend UX Spec (V1)

## Metadata

- Upgrade ID: UPG-2026-03-04-04
- Date: 2026-03-04
- Owner: Codex
- Area: Frontend / Command Palette
- Priority: high
- Target release: test_react

## Goal

Integrare il parser assistant nella Command Palette esistente mantenendo UX veloce, keyboard-first e controllo esplicito dell'utente.

## UX Principles

- Nessun autosave invisibile.
- Preview prima del commit.
- Errori chiari, non tecnici.
- Latenza percepita minima.
- Funzionamento completo da tastiera.

## Command Palette Integration

Componente target:

- `frontend/src/components/layout/CommandPalette.tsx`

Nuove aree UI:

- input mode `search` / `assistant`;
- preview card operazioni assistant;
- elenco ambiguita' risolvibili;
- CTA `Invio per confermare`.

## Interaction Flow

1. Utente apre palette (`Ctrl+K`).
2. Digita frase naturale.
3. Debounce 180ms -> chiamata `POST /assistant/parse`.
4. Preview pannello destro:
   - operazioni trovate;
   - campi estratti;
   - warning/ambiguita'.
5. Se stato `ready`: `Invio` -> `POST /assistant/commit`.
6. Esito:
   - toast success/error;
   - invalidate query keys.

## UI States

- `idle`: nessun input.
- `parsing`: spinner leggero inline.
- `preview_ready`: card verde, confermabile.
- `preview_needs_confirmation`: card gialla con selettori.
- `preview_blocked`: card rossa con missing fields.
- `committing`: lock temporaneo invio.
- `committed`: toast + reset input.

## Preview Card Structure

- Header: `N operazioni riconosciute`.
- Lista per operazione:
  - dominio (`Agenda`, `Cassa`, `Misurazioni`, ...);
  - descrizione umana;
  - campi chiave (`cliente`, `data`, `importo`, ecc.);
  - confidence badge.
- Footer:
  - shortcut `Invio conferma`;
  - `Esc` annulla;
  - warning text se ambiguo.

## Ambiguity UX

Per ogni ambiguita':

- mostra top 3 candidati con score;
- selezione rapida con frecce + invio;
- memorizza risoluzione nel payload commit (`client_resolutions[]`).

Se non risolta:

- commit disabilitato.

## Query Invalidation Matrix (Frontend)

Matrice minima da rispettare:

- agenda:
  - `["events"]`, `["dashboard"]`, `["clients"]`, `["contracts"]`, `["contract"]`
- client/anamnesi:
  - `["clients"]`, `["client"]`, `["dashboard"]`
- contratti:
  - `["contracts"]`, `["contract"]`, `["clients"]`, `["client"]`, `["dashboard"]`, `["movements"]`, `["movement-stats"]`, `["aging-report"]`, `["cash-balance"]`
- cassa:
  - `["movements"]`, `["movement-stats"]`, `["dashboard"]`, `["aging-report"]`, `["cash-balance"]`
- misurazioni:
  - `["measurements", clientId]`, `["goals", clientId]`
- workout log:
  - `["workout-logs"]`

## Accessibility

- Focus management coerente (input resta focusato).
- Annunci ARIA per cambio stato parse.
- Contrasto badge stato conforme.
- Nessuna dipendenza solo colore per warning/error.

## Performance Budget

- Parse request debounce: 150-250ms.
- Rendering preview <= 16ms medio.
- Nessun fetch heavy aggiuntivo ad apertura palette oltre quelli gia' presenti.
- Abort request precedente su nuova digitazione.

## Error Handling UX

- Errore rete parse:
  - "Impossibile analizzare ora. Riprova."
- Errore commit dominio:
  - mostra messaggio dominio-safe (es. overlap agenda).
- Errore ambiguita' non risolta:
  - callout con istruzione diretta.

## Telemetry (No PII in clear)

Eventi:

- `assistant_parse_requested`
- `assistant_parse_ready`
- `assistant_parse_blocked`
- `assistant_commit_success`
- `assistant_commit_failed`

Campi:

- `correlation_id`
- `intent_count`
- `latency_ms`
- `status_bucket`

No payload testuale completo nei log analytics.
