# Upgrade Tracking Framework

Questo spazio tiene traccia delle patch in modo professionale e leggero.
Obiettivo: aumentare qualita, velocita e continuita tra release.

## Struttura

- `UPGRADE_LOG.md`: registro unico degli upgrade.
- `specs/PATCH_SPEC_TEMPLATE.md`: template di specifica pre-implementazione.
- `checklists/DOR_DOD_CHECKLIST.md`: checklist operativa prima/dopo lo sviluppo.

## Flusso standard

1. Crea una spec da template in `docs/upgrades/specs/`.
2. Aggiungi una riga in `UPGRADE_LOG.md` con stato `planned`.
3. Implementa la patch.
4. Esegui quality gate e test previsti.
5. Aggiorna la riga log con commit, stato finale e note.
6. Se la scelta e architetturale, aggiungi anche un ADR in `docs/adr/`.

## Convenzioni ID

Formato consigliato: `UPG-YYYY-MM-DD-XX`

Esempio:
- `UPG-2026-03-03-01`
- `UPG-2026-03-03-02`

## Stato upgrade

- `planned`
- `in_progress`
- `done`
- `rolled_back`
- `superseded`

## Ultimo allineamento (2026-03-05)

- `UPG-2026-03-04-01`: dual-DB + backup v2.0 bank-grade.
- `UPG-2026-03-04-02`: export clinico schede (HTML locale -> PDF) con logo e foto embedded.
- `UPG-2026-03-04-03`: hardening stampa (color fidelity, impaginazione, compattazione densita).
- `UPG-2026-03-04-04`: assistant CRM deterministico V0.5 (parser NLP + Command Palette UX).
- `UPG-2026-03-04-05`: redesign UX assistente Command Palette (full-width, discovery, suggestion chips).
- `UPG-2026-03-04-06`: launch market readiness roadmap (Wave 1-3 complete, installer 83MB testato).
- `UPG-2026-03-05-01`: fix installer post-smoke-test (path PyInstaller, seed media, backup restore WAL).
- `UPG-2026-03-05-02`: dashboard privacy-first (overview client-safe senza KPI economici in vista pubblica).
- `UPG-2026-03-05-03`: introduzione `AGENTS.md` + bootstrap `agents/` per workflow agent-first.
- `UPG-2026-03-05-04`: skill pack iniziale in `.codex/skills` per workflow automatici specializzati.
- `UPG-2026-03-05-05`: dashboard KPI operativi (sessioni imminenti + alert operativi) per uso quotidiano del chinesiologo.
- `UPG-2026-03-05-06`: dashboard "Lezioni della settimana" con vista per categoria/stato per pianificazione operativa rapida.
- `UPG-2026-03-05-07`: nuova skill `fitmanager-dashboard-crm-design` + routing in `AGENTS.md` per standardizzare i redesign dashboard.
- `UPG-2026-03-05-08`: split agenda dashboard in doppio riquadro con pannello live (orologio + countdown + stato sessione in corso/prossima/libero).
- `UPG-2026-03-05-09`: dashboard interattiva con cambio stato appuntamenti inline nelle righe Agenda.
- `UPG-2026-03-05-10`: rifinitura visuale dashboard con chip settimanali piu' leggibili e cromia state-aware per il pannello live.
- `UPG-2026-03-05-11`: correzione densita verticale dashboard: riquadri agenda/live compatti e appuntamenti sempre scrollabili internamente.
- `UPG-2026-03-05-12`: ottimizzazione responsive tablet/mobile dashboard + nuova skill riusabile `fitmanager-responsive-adaptive-ui` con routing in `AGENTS.md`.
- `UPG-2026-03-05-13`: hardening logica temporale dashboard (date locali no UTC shift + refresh automatico al cambio giorno).
- `UPG-2026-03-05-14`: Wave 0 guida completata (foundation governance): 3 nuove skill guida, routing `AGENTS.md`, roadmap Wave 1-3 pronta.
- `UPG-2026-03-05-15`: Wave 1 guida a capitoli/sezioni completata (`docs/guides/` con 12 capitoli route-mapped).
- `UPG-2026-03-05-16`: Wave 2 guida illustrata con callout standard (planned).
- `UPG-2026-03-05-17`: Wave 3 guida interattiva + integrazione assistant/help routing (planned).
- `UPG-2026-03-05-18`: hardening dashboard mobile overflow/clipping (KPI/alert/agenda/todo) con width constraints e wrapping/truncate sicuro.
