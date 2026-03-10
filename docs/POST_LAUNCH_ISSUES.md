# FitManager AI Studio — Post-Launch Issue Register

> Registro problemi noti e debiti tecnici da risolvere dopo il lancio.
> Priorita: P0 = blocco, P1 = importante, P2 = miglioramento, P3 = cosmetico.

---

## Problemi Noti al Lancio

| # | Priorita | Area | Descrizione | Workaround | Stato |
|---|----------|------|-------------|------------|-------|
| 1 | P2 | UI | `__version__` non visibile nella pagina Impostazioni | Risolto il 2026-03-10 da `UPG-2026-03-10-08`: ora esposto in `Impostazioni > Stato installazione` | closed |
| 2 | P2 | Backend | 9 repository legacy (sqlite3 raw) usati solo da core/ | Non impattano il CRM core | deferred |
| 3 | P2 | Backend | FinancialRepository + CardImportRepository legacy (dict raw) | Non usati dal CRM attivo | deferred |
| 4 | P3 | Frontend | ESLint 5 warning residui (`react-hooks/incompatible-library` da react-hook-form `watch()`) | Non-actionable, nessun impatto | deferred |
| 5 | P2 | License | Nessun workflow di rinnovo licenza in-app | Rigenerare license.key manualmente con CLI | open |
| 6 | P1 | Test | pytest non eseguibile su ambiente locale gvera (venv launcher rotto) | Funziona in CI e su altri ambienti | open |

---

## Debito Tecnico Post-Lancio

| # | Area | Descrizione | Impatto |
|---|------|-------------|---------|
| 1 | core/ | Moduli AI dormenti (~10,300 LOC) — da esporre via API endpoints | Nessuno su CRM base |
| 2 | Esercizi | 720 esercizi archiviati reinseribili via `activate_batch.py` | Catalogo piu ampio possibile |
| 3 | Build | Rebuild installer dopo ogni modifica significativa | Manuale, ~5 min |
| 4 | Testing | Test E2E richiedono server avviato | Non CI-native |
| 5 | Docs | Conteggi in CLAUDE.md/README.md da aggiornare periodicamente | Documentazione stale |

---

## Issues Post-Lancio (da compilare dopo il go-live)

| # | Data | Segnalato da | Priorita | Descrizione | Risoluzione | Stato |
|---|------|-------------|----------|-------------|-------------|-------|
| | | | | | | |

---

*Creato il 2026-03-10 durante Step 6 Launch Hardening.*
