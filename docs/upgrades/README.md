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

## Ultimo allineamento (2026-03-09)

- `UPG-2026-03-09-08`: refactor di `Oggi` in chiave `stack + detail`: header minimo, agenda di supporto, queue a 3 sezioni e detail sticky, per differenziarla davvero dalla dashboard senza toccare `/`.
- `UPG-2026-03-09-07`: primo shell frontend reale del workspace `Oggi` su route `/oggi`, con focus case, agenda live, queue per bucket, detail panel e link dedicato in sidebar, senza ancora sostituire la dashboard `/`.
- `UPG-2026-03-09-06`: introdotto `GET /api/workspace/cases/{case_id}` con payload detail read-only (`signals`, `related_entities`, `activity_preview`), visibilita finance dipendente dal workspace e hook frontend `useWorkspaceCaseDetail()`.
- `UPG-2026-03-09-05`: lista casi `GET /api/workspace/cases` con paginazione e filtri server-side, snapshot condiviso con `today`, policy finance differenziata tra `today` e `renewals_cash`, e hook frontend `useWorkspaceCases()`.
- `UPG-2026-03-09-04`: primo scaffold runtime del workspace con `GET /api/workspace/today`, type sync frontend, hook read-only e readiness condivisa estratta in service.
- `UPG-2026-03-09-03`: contratto tecnico `Workspace v1` con endpoint read-only `/api/workspace/*`, tipi condivisi, merge keys e policy finance per `Oggi`.
- `UPG-2026-03-09-02`: definizione prodotto del nuovo workspace operativo FitManager con home post-login `Oggi`, case engine, dual timeline e 4 viste native.
- `UPG-2026-03-09-01`: profilo cliente trasformato in CRM hub operativo con onboarding checklist, path bar journey e tab rifiniti.
- `UPG-2026-03-08-02`: anamnesi v2 riallineata al Google Form reale con 6 step, circa 45 campi e compat safety engine.
- `UPG-2026-03-07-37`: esposizione REST del motore scientifico con 5 endpoint JWT auth e zero dipendenza dal DB.
- `UPG-2026-03-07-40`: creato il primo scaffold backend-first del `plan-package` SMART con runtime layer DB-aware separato dal core puro, endpoint additivo `/training-science/plan-package`, mirror TypeScript e hook `useGeneratePlanPackage()`, senza ancora tagliare il flusso UI legacy.
- `UPG-2026-03-07-41`: `TemplateSelector` smart ora usa davvero il `plan-package` backend-first e salva il draft restituito dal backend, chiudendo il vecchio path locale di generazione nel flusso utente principale.
- `UPG-2026-03-07-42`: introdotto il primo handoff temporaneo `plan-package -> builder`: cache in `sessionStorage`, consumo one-shot nella pagina scheda e `SmartAnalysisPanel` canonico-first finche' la scheda non viene modificata.
- `UPG-2026-03-07-43`: hotfix backend sul `plan-package`: eliminata la costruzione invalida di candidati con `rank=0` che mandava in `500` il nuovo endpoint SMART.
- `UPG-2026-03-07-44`: primo pass stateful del ranker SMART: feedback settimanale deterministico su balance orizzontale/verticale, rebalance quad-posteriore, boost frequenza bicipiti/femorali, penalita' overlap recupero e diversita' minima esercizi.
- `UPG-2026-03-07-45`: riequilibrato il canonico `full_body 3x` nel planner SMART: la rotazione passa di fatto da `A/B/A` a `A/B/C`, cosi' la Smart Analysis puo' misurare una distribuzione meno sbilanciata su orizzontale/verticale e catena posteriore gia' nel piano scientifico, non solo nel ranking.
- `UPG-2026-03-07-46`: aggiunti guardrail scientifici in `plan_builder.py`: la Fase 2 non puo' piu' spingere i `push` oltre la soglia accettabile del rapporto `Push:Pull`, e la Fase 3 puo' dare priorita' quad-specifica e una piccola correzione `leg_extension` quando `Quad:Ham` resta sotto target.
- `UPG-2026-03-07-51`: raffinato il `3x beginner` SMART anticipando la correzione frequency-aware prima della compensazione volume generica, cosi' i pochi slot accessori non vengono consumati prima di assicurare `freq >= 2x` ai piccoli distretti.
- `UPG-2026-03-07-52`: raffinata ancora la priorita' del `3x beginner`: le correzioni frequency-aware ora seguono il volume settimanale reale vs `MEV/MAV` e saltano i muscoli gia' pieni, cosi' gli slot accessori si concentrano davvero sui distretti piu' carenti come il deltoide laterale.
- `UPG-2026-03-07-53`: hardening del ranker SMART beginner: i candidati con `rep_range` coerente con l'obiettivo vengono favoriti, mentre `advanced`, `cardio` e movimenti `jump/skill/plyo` vengono frenati molto di piu' nei profili principianti, per evitare schede concrete non plausibili come `muscle-up` o `box jump`.
- `UPG-2026-03-07-54`: ulteriore gate runtime sul draft beginner: se nello stesso slot esistono alternative compatibili, i candidati `advanced` o chiaramente `skill/plyo/cardio` non entrano piu' nell'auto-fill SMART. Il trainer puo' ancora forzarli manualmente, ma non escono piu' come scelta automatica di default.
- `UPG-2026-03-07-55`: formalizzato `SMART Scientific Method v1`: SMART deve smettere di crescere per patch locali e diventare un `Scientific Protocol Engine` backend-first, incardinato nel KineScore, con `Evidence Registry`, `Protocol Registry`, `Constraint Engine`, `Canonical Plan Engine` e `Validation Harness`.
- `UPG-2026-03-07-56`: definito `SMART Protocol Registry v1`: il metodo ora dichiara anche quali celle della matrice sono supportate, `clinical_only` o `unsupported_by_policy`, e fissa le prime 6 famiglie ufficiali da implementare (`PRT-001 ... PRT-006`).
- `UPG-2026-03-07-57`: definito `SMART Constraint Schema v1`: i protocolli ora hanno una grammatica formale di vincoli tipizzati (`Session`, `Volume`, `Frequency`, `Balance`, `Recovery`, `Suitability`, `Clinical`, `ValidationContract`) pronta per diventare modelli backend.
- `UPG-2026-03-07-58`: scritte le prime `Protocol Definitions v1` (`PRT-001 ... PRT-006`): il registry non e' piu' solo forma, ma contenuto prescrittivo concreto, con target population, criteri di ingresso, vincoli completi e validation contract.
- `UPG-2026-03-07-59`: definito `SMART Demand Vector v1`: il metodo introduce un layer biomeccanico-funzionale esplicito per distinguere il costo degli esercizi oltre pattern e muscoli, con 10 dimensioni ordinali, famiglie semantiche, classi di evidenza e integrazione diretta con protocolli, suitability e validation harness.
- `UPG-2026-03-07-60`: definita `SMART Validation Matrix v1`: il metodo ora dichiara anche i casi benchmark obbligatori `VM-001 ... VM-006`, gli invarianti, le tolleranze, i warning ammessi/vietati e il release gate scientifico per i protocolli supportati.
- `UPG-2026-03-07-61`: definite le `SMART Validation Fixtures v1`: il metodo dichiara ora anche il formato concreto delle fixture congelate `CFG-*`, `RQ-*`, `EXP-*` e del registry index, cosi' la validation matrix puo' diventare davvero un harness eseguibile e versionato.
- `UPG-2026-03-07-62`: definito `SMART Evidence Registry v1`: il metodo dichiara ora anche il registro di fonti, anchor, claim e parametri con classi di evidenza, origine del parametro e population scope, cosi' ogni scelta del motore puo' essere tracciata e difesa scientificamente.
- `UPG-2026-03-07-63`: definito il primo `SMART Evidence Population Pass v1`: il registry non e' piu' solo una shape, ma contiene gia' un primo catalogo minimo di fonti, anchor, claim, parametri e usage map per sostenere i protocolli v1 in modo epistemicamente onesto.
- `UPG-2026-03-07-64`: definito `SMART Runtime Translation Plan v1`: il metodo ha ora una mappa concreta, file-per-file e per fasi, per entrare nel backend reale senza big bang e senza rompere il motore attuale, usando `/plan-package` come percorso pilota e un approccio `adapter-first`.
- `UPG-2026-03-07-65`: introdotto il primo scaffold runtime del `Protocol Registry`: il backend ha ora moduli `registry/` read-only, un selector deterministico e metadata `protocol` dentro `TSPlanPackage`, cosi' `/plan-package` inizia a parlare la lingua del nuovo metodo senza ancora riscrivere il planner legacy.
- `UPG-2026-03-07-66`: introdotto `Constraint Adapter v1`: `/plan-package` misura ora il piano legacy rispetto al protocollo selezionato e restituisce un report strutturato `constraint_evaluation`, preparando il passaggio futuro a veri vincoli runtime senza forzare ancora enforcement o rewrite del planner.
- `UPG-2026-03-07-50`: hardening build frontend offline-safe: chiuso il drift TypeScript in `MuscleMapPanel` e rimossi i fetch obbligatori a Google Fonts in build, mantenendo le stesse variabili tipografiche via fallback locali/system-safe.
- `UPG-2026-03-07-48`: corretto il `3x beginner` nel planner SMART con micro-dose dirette frequency-aware su deltoide laterale, bicipiti, tricipiti e polpacci, cosi' i piccoli distretti raggiungono `freq >= 2x` senza gonfiare in modo cieco il volume settimanale.
- `UPG-2026-03-07-47`: riallineata la lettura SMART nel builder: il KPI alto ora conta anche gli eccessi dentro "Da correggere", `MuscleMapPanel` usa la stessa analisi backend di `SmartAnalysisPanel` con palette a 4 stati, e il builder distingue esplicitamente tra condizioni anamnestiche rilevate, condizioni mappate nel catalogo e condizioni che impattano la scheda corrente.
- `UPG-2026-03-07-38`: riallineata la baseline progetto `.codex/config.toml` a `gpt-5.4` con profili CLI `quick/deep/safe`, mantenendo il file repo privo di preferenze macchina/personali.
- `UPG-2026-03-07-39`: introdotto `FitManager Collaboration Contract v1`, protocollo user-Codex per task complessi con mode esplicite, task brief minimo, decision gate e addendum SMART/Training Science.

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
