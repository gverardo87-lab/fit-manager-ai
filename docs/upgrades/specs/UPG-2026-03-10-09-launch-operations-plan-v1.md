# Patch Spec - Launch Operations Plan v1

## Metadata

- Upgrade ID: UPG-2026-03-10-09
- Date: 2026-03-10
- Owner: Codex
- Area: Launch Readiness + Operations + Supportability
- Priority: high
- Status: done

## Objective

Tradurre la baseline tecnica gia verificata del repository in un piano operativo pre-lancio
eseguibile, con priorita esplicite, date concrete, gate `pilot` vs `market` e divieti di scope creep.

FitManager non deve distinguersi sul mercato per "piu feature cloud", ma per:

1. installazione locale protetta;
2. affidabilita dimostrabile;
3. supporto tecnico rapido e deterministico;
4. continuita operativa anche senza dipendenze cloud.

## Progress Update As Of 2026-03-10

Questo piano e' nato come backlog operativo iniziale. Dopo la sua stesura sono stati chiusi
i seguenti microstep P0:

- `UPG-2026-03-10-11`: `support snapshot` read-only in `Impostazioni`
- `UPG-2026-03-10-12`: migrazione shell Next `middleware -> proxy`
- `UPG-2026-03-10-13`: logging locale persistente in `data/logs/`
- `UPG-2026-03-10-14`: matrice negativa di test sul gate licenza lato API
- `UPG-2026-03-10-15`: `SUPPORT_RUNBOOK.md` come artefatto operativo unico
- `UPG-2026-03-10-18`: preflight runtime/build dell'installer (`1.0.0`, naming versionato, `build-media.sh` su `catalog.db`, `build-installer.sh`, rimozione `license.key` da repo/assets)
- `UPG-2026-03-10-19`: release candidate `1.0.0` costruita davvero con `build-installer.sh`, freeze reale `catalog.db=400` / `crm.db locale=396`, packaging snapshot-based via `dist/release-data`

Restano ancora aperti i gate manuali/non documentali:

- prova installata `license.key` rimosso -> `/licenza`
- validazione reale LAN / Tailscale VPN / Funnel smartphone
- installazione pulita su macchina Windows non-dev
- restore del backup reale di Chiara sulla release candidate
- decisione finale su code signing per market gate

## Release Candidate Preflight Decisions As Of 2026-03-10

Decisioni aggiunte dopo la stesura iniziale del piano:

1. **Preflight anchor**: commit `4a19bf2` come baseline docs-first iniziale
2. **Versione candidata**: `1.0.0`, ora gia' riallineata in backend, frontend e installer
3. **Policy bundle dati**:
   - `catalog.db` canonico nel pacchetto, oggi congelato a 400 ID esercizio
   - `crm.db` vuoto nel bundle release candidate
4. **Dati reali trainer**: lo stato reale di Chiara rientra solo tramite restore verificato del backup piu recente
5. **Policy licenza**: `license.key` cliente fuori dal repository e fuori da `installer/assets`; destinazione runtime unica `data/license.key`
6. **Freeze artefatto**:
   - RC build eseguita il 2026-03-10
   - artefatto: `dist/FitManager_Setup_1.0.0.exe`
   - SHA-256: `05B2AF87FD01CF1A3DC5BB3DDFCAD3785C798CFA9DE3D93480B33359F2E3DC58`

## Next Strategic Workstream After Manual Validation

Dopo la riuscita della rehearsal installativa reale sul PC di Chiara
(`install -> license.key -> restore backup`), il prossimo workstream di prodotto non e'
piu solo "validare la rete", ma trasformare Tailscale/Funnel da runbook tecnico a
onboarding guidato dal prodotto.

Questo workstream e' ora formalizzato in:

- `UPG-2026-03-10-20`: `Connectivity Setup Wizard Plan v1`

Decisione chiave:

- il prodotto manterra' sempre `local_only` come fallback;
- aggiungera' poi due profili espliciti:
  - `trusted_devices`
  - `public_portal`
- Tailscale login resta nel client ufficiale;
- FitManager dovra' leggere lo stato reale della connettivita', configurare le proprie
  variabili (`PUBLIC_PORTAL_ENABLED`, `PUBLIC_BASE_URL`) e guidare il trainer con una UX
  deterministica.

## Verified Baseline As Of 2026-03-10

### Gia chiuso

- `bash tools/scripts/check-all.sh` verde.
- `pytest tests/ -v`: 269 test verdi.
- Vitest frontend: 69 test verdi.
- E2E business rehearsal: 36/36 PASS.
- E2E distribution rehearsal: 62/62 PASS.
- Installer nativo Windows prodotto e smoke-testato.
- Licensing RSA attivo, `launcher.bat` con `LICENSE_ENFORCEMENT_ENABLED=true`.
- Backup/restore bank-grade con WAL checkpoint e schema sync.
- Health/runtime surface esposta in `Impostazioni` con versione, stato licenza, stato DB, modalita `source/installer`, `dev/prod`.

### Gap ancora aperti al momento della stesura iniziale

- `support snapshot` read-only non ancora disponibile.
- Warning Next 16: convenzione `middleware` deprecata verso `proxy`.
- Logging locale operativo non ancora formalizzato in `data/logs/`.
- Test enforcement negativo licenza non ancora eseguito.
- Installazione pulita su macchina Windows non-dev non ancora verificata.
- Test reali LAN, Tailscale VPN esterna e Funnel smartphone non ancora chiusi.
- Runbook supporto installazione/licenza/recovery non ancora formalizzato come artefatto operativo unico.
- Code signing del pacchetto non ancora deciso o completato.

## Strategic Principle

Il piano separa due soglie diverse:

- `Pilot gate`: soglia minima per mettere il prodotto in mano a 3-5 utenti reali sotto osservazione.
- `Market gate`: soglia per vendere in modo piu ampio senza supporto "artigianale".

Non tutte le attivita bloccano il pilot. Alcune bloccano solo il go-live commerciale esteso.

## Priority Matrix

### P0 - Must Close Before Pilot (backlog iniziale)

1. `support snapshot` scaricabile da `Impostazioni`, senza PII.
2. Migrazione Next `middleware.ts -> proxy.ts` o equivalente compatibile Next 16.
3. Logging locale rotante in `data/logs/` con retention minima e senza dati sensibili inutili.
4. Test enforcement negativo licenza.
5. Runbook supporto v1: installazione, attivazione licenza, backup/restore, recovery post-update.
6. Una prova completa `install -> login -> setup -> cliente -> contratto -> rata -> pagamento -> backup -> restore`.

### P1 - Must Close Before Market Launch

1. Test installazione su macchina Windows pulita non-dev.
2. Test LAN da tablet/smartphone sulla stessa rete.
3. Test Tailscale VPN da rete esterna.
4. Test anamnesi self-service da smartphone via Funnel.
5. Code signing di installer ed eseguibile, oppure decisione formale di rollout pilot limitato senza signing.
6. Pacchetto release stabile con note di rilascio, issue note e rollback package conservato.

### P2 - Can Wait Until After First Paying Cohort

1. Workflow rinnovo licenza in-app.
2. Pulizia warning ESLint residui non-actionable.
3. Miglioramenti cosmetici non legati a supporto, distribuzione o affidabilita.
4. Nuove macro-feature AI o nuove superfici prodotto.

## Execution Window

Finestra operativa proposta: da **mercoledi 11 marzo 2026** a **martedi 24 marzo 2026**.

## Phase Plan

### Phase 0 - Scope Freeze

**Data**: 2026-03-11

**Deliverable**

- Freeze delle nuove macro-feature fino alla chiusura del pilot.
- Backlog etichettato solo per:
  - `launch-p0`
  - `launch-p1`
  - `pilot-fix`
- Chiarezza su cosa non entra prima del pilot.

**Done criteria**

- Nessuna nuova feature fuori da installazione, supporto, rete, licensing, backup, QA, docs operative.

### Phase 1 - Supportability Foundation

**Date**: 2026-03-11 -> 2026-03-13

**Microstep**

1. Implementare `support snapshot` read-only scaricabile da `Impostazioni`.
2. Migrare la shell Next dalla convenzione `middleware` alla convenzione compatibile Next 16.
3. Formalizzare logging locale persistente in `data/logs/`.
4. Collegare il support snapshot a health/runtime/licenza/backup metadata gia esposti.

**Output atteso**

- Un tecnico puo chiedere al cliente un solo file diagnostico.
- Il prodotto non dipende dal terminale per sapere che build sta girando.
- La shell frontend non porta warning architetturali pre-lancio.

**Verification**

- lint/build verdi sui file toccati;
- smoke UI su `Impostazioni`;
- verifica che lo snapshot non includa PII, JWT, dati business o chiavi.

### Phase 2 - Distribution Hardening

**Date**: 2026-03-13 -> 2026-03-16

**Microstep**

1. Eseguire test enforcement negativo: rimuovere `license.key`, verificare redirect/UX corretta.
2. Eseguire rehearsal completa su ambiente installato:
   - install
   - launch
   - login
   - setup
   - flusso business minimo
   - backup
   - restore
3. Formalizzare `SUPPORT_RUNBOOK.md` o equivalente operativo.
4. Preparare decisione su code signing:
   - `pilot-only unsigned` ammesso;
   - `market launch unsigned` non raccomandato.

**Output atteso**

- Il licensing non e solo "presente", ma anche verificato in negativo.
- Il recovery post-problema e ripetibile da documento, non da memoria orale.

**Verification**

- update `docs/RELEASE_CHECKLIST.md`;
- evidenza scritta dei pass manuali;
- issue register aggiornato.

### Phase 3 - Network And Portal Validation

**Date**: 2026-03-16 -> 2026-03-18

**Microstep**

1. Test LAN su tablet e smartphone in stessa rete Wi-Fi.
2. Test accesso Tailscale VPN da rete esterna.
3. Test completo Funnel su smartphone:
   - apertura link pubblico
   - compilazione anamnesi
   - ritorno dati corretto
4. Validare che health/support snapshot riflettano correttamente il contesto remoto.

**Output atteso**

- Le modalita di accesso supportate dal prodotto sono verificate sul campo, non solo "configurate".

**Verification**

- checklist rete aggiornata con data e device usato;
- nessun blocker su portale cliente.

### Phase 4 - Pilot Gate

**Date**: 2026-03-18 -> 2026-03-19

**Deliverable**

- Build `stable-rc` candidata al pilot.
- Known issues esplicite.
- Canale di supporto definito.
- Politica di triage: solo bugfix, niente nuove feature.

**Pilot go/no-go**

Il pilot puo partire solo se:

1. tutti i `P0` sono chiusi;
2. `RELEASE_CHECKLIST.md` sezioni 1-6 sono tutte verdi;
3. esiste almeno una prova manuale completa di flusso business e restore;
4. non esistono issue `P0` aperte;
5. l'operatore sa eseguire il recovery senza interventi ad hoc sul codice.

### Phase 5 - Controlled Pilot

**Date**: 2026-03-19 -> 2026-03-24

**Modello**

- 3-5 utenti reali, selezionati e seguiti.
- Nessun rollout ampio.
- Una sola build stabile per tutti i pilot user.
- Patch solo correttive, piccole e verificabili.

**Metriche da osservare**

1. tempo di installazione fino al primo login;
2. numero ticket/support request per installazione;
3. successo del primo backup;
4. stabilita portale anamnesi da smartphone;
5. bug che bloccano flussi core:
   - clienti
   - contratti
   - rate
   - agenda
   - schede
   - backup/restore

**Exit criteria**

- zero blocker aperti dal pilot;
- supporto gestibile con runbook e support snapshot;
- nessuna perdita dati o recovery fallito;
- backlog post-pilot distinto tra `must before market` e `can defer`.

## Market Gate

Il lancio commerciale piu ampio deve attendere questi criteri aggiuntivi:

1. test macchina Windows pulita completato;
2. rete validata (LAN + Tailscale + Funnel smartphone);
3. code signing completato o rischio accettato formalmente;
4. release package archiviato con rollback package equivalente;
5. issue register senza `P0/P1` aperti relativi a installazione, licenza, backup, portale o rete.

## Explicit "Do Not Do" Before Pilot

Per proteggere il lancio, fino alla chiusura del pilot NON entra:

1. nuova macro-feature AI;
2. refactor architetturale non richiesto da affidabilita/supporto;
3. migrazione SQLite -> PostgreSQL;
4. nuova surface dashboard/workspace non legata al lancio;
5. redesign estetico non legato a chiarezza operativa o installazione.

## Recommended Immediate Backlog

Ordine esecutivo raccomandato dal piano:

1. allineamento docs-first del preflight installer
2. version sync `1.0.0` su backend/frontend/installer
3. rimozione della `license.key` cliente dal perimetro repository/assets
4. chiarimento/orchestrazione della pipeline di build installer
5. rebuild release candidate
6. restore del backup reale di Chiara sulla candidate build
7. test negativo licenza su installazione reale
8. rehearsal macchina pulita + LAN/Tailscale/Funnel

## Risks / Residuals

1. Senza support snapshot e logging locale il supporto resta troppo dipendente da intervento esperto.
2. Senza test rete reali, il valore differenziante "locale ma accessibile" non e ancora dimostrato.
3. Senza code signing, la vendita ampia su Windows resta piu fragile sul piano reputazionale.
4. Senza freeze funzionale, il pilot rischia di essere inquinato da regressioni evitabili.

## Next Smallest Step

Aprire il microstep `UPG-2026-03-10-11` per implementare il `support snapshot` read-only scaricabile
da `Impostazioni`, usando come fonti locali:

- payload `/health`
- stato licenza
- modalita runtime
- readiness del portale pubblico
- elenco ultimi backup

senza includere dati cliente, JWT o contenuti business.
