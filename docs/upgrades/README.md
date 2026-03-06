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

## Ultimo allineamento (2026-03-06)

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
- `UPG-2026-03-05-14..17`: superseded — vecchio approccio guida a capitoli/illustrata. Sostituito da SpotlightTour (UPG-23).
- `UPG-2026-03-05-18`: hardening dashboard mobile overflow/clipping (KPI/alert/agenda/todo) con width constraints e wrapping/truncate sicuro.
- `UPG-2026-03-05-19`: dashboard piu' viva con barra "Focus operativo" + animazioni leggere a comparsa (no nuove dipendenze, rollback via flag locale).
- `UPG-2026-03-05-20`: scaffold pagina `/guida` + sidebar + CommandPalette. Evoluto in SpotlightTour (UPG-23).
- `UPG-2026-03-05-21`: hardening governance per sviluppo parallelo Codex + Claude Code (priority sync, protocollo lock/handoff, workboard contract, allineamento CLAUDE layer).
- `UPG-2026-03-05-23`: SpotlightTour interattivo 19 passi con navigazione cross-page. Hub `/guida` con tour launcher, FAQ, scorciatoie e feature discovery.
- `UPG-2026-03-05-24`: stabilizzazione CI backend su pagamenti rate: test `test_pay_rate_creates_cash_movement` reso deterministico con `data_pagamento` esplicita, piu' verifica target (`test singolo + file completo`).
- `UPG-2026-03-05-25`: hardening lint React Hooks su agenda/draft guard (`setState-in-effect`, `ref in render`, deps memo) con verifica mirata ESLint sui file critici.
- `UPG-2026-03-05-26`: hardening sprint T2-T6 pre-lancio: hook safety frontend (0 errori ESLint), cleanup lint minori, esclusione `tests/legacy` da Ruff (0 errori `api/tests`) e rimozione `license.key` pre-bundled dall'installer.
- `UPG-2026-03-06-27`: dashboard reminder-first: promemoria portati in priorita alta nella board (mobile/tablet-first), alert spostati sotto i promemoria e `TodoCard` hardenizzata con bucket `scaduti/oggi/prossimi` + ordinamento urgenza e data locale robusta.
- `UPG-2026-03-06-28`: `TodoCard` evoluta in "Azione consigliata" con priorita cross-signal (todo + alert + agenda) e CTA operative dirette; rimosso `Date.now` dai path render per rispettare React purity lint.
- `UPG-2026-03-06-29`: dashboard resa piu' densa e operativa: eliminata barra focus ridondante, KPI ridotti ai due essenziali, top layout 50/50 con promemoria post-it a sinistra e pannello unico clock+sedute scorrevoli a destra.
- `UPG-2026-03-06-30`: introdotta coda "Clinical Readiness" (API + dashboard) per onboarding legacy: priorita deterministica su anamnesi/baseline/scheda, KPI readiness e CTA dirette cliente-per-cliente con test backend multi-tenant dedicati.
- `UPG-2026-03-06-31`: CTA readiness rese realmente one-click con auto-avvio guidato (wizard anamnesi e selector scheda) tramite deep-link con flag consumati in URL, riducendo i click operativi nel flusso iniziale.
- `UPG-2026-03-06-32`: introdotta pagina `Clienti > MyPortal` come board readiness dedicata (anamnesi/misurazioni/scheda per cliente) con filtri e ricerca, riusando la stessa fonte calcolo della dashboard senza appesantire il backend.
- `UPG-2026-03-06-33`: timeline scadenze operativa in MyPortal/readiness con date e urgenze calcolate lato API (`next_due_date`, `days_to_due`, `timeline_status`, `timeline_reason`) per tracciare in modo affidabile cosa scade e quando.
- `UPG-2026-03-06-34`: avviata architettura MyPortal v2 (worklist-first) con M0a/M0b/M0c + M1 frontend completo: endpoint read-only paginato `clinical-readiness/worklist`, MyPortal con paginazione reale, filtri avanzati/timeline paginata e decoupling schema readiness in modulo dedicato `api/schemas/clinical.py`.
