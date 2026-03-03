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
