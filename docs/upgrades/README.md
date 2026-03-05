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
