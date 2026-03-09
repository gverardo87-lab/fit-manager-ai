# ADR - Operational Workspace via Case Engine + Dual Timeline

- Date: `2026-03-09`
- Status: `proposed`
- Deciders: `gvera`, `Codex`
- Related upgrade ID: `UPG-2026-03-09-02`

## Context

FitManager ha gia diversi moduli verticali efficaci:

- dashboard overview privacy-safe;
- profilo cliente sempre piu vicino a un CRM hub;
- monitoraggio/worklist tecnico-clinica;
- superfici onboarding e finance dedicate.

Manca pero una home post-login che diventi il centro mentale e operativo del trainer.

Il rischio principale e progettare questa home come:

- semplice dashboard aggiuntiva;
- feed cronologico unico di record eterogenei;
- insieme di pagine separate che duplicano lo stesso lavoro.

Questo approccio produrrebbe rumore. Una sessione imminente, un onboarding bloccato e un affitto studio da registrare non sono elementi equivalenti. Hanno semantica, severita, tempistiche e azioni corrette diverse.

## Decision Drivers

- ridurre rumore e duplicazioni;
- creare una home quotidiana realmente azionabile;
- preservare la separazione tra overview neutra e contesto finance sensibile;
- mantenere il comportamento deterministico e spiegabile;
- permettere un solo motore operativo per piu workspace;
- lasciare spazio a future saved views senza rifare il modello.

## Considered Options

### Option A - Feed cronologico unico di tutto

- Pro:
  - semplice da spiegare;
  - apparentemente vicino a una "timeline totale".
- Contro:
  - mescola domini non comparabili;
  - crea rumore;
  - incentiva duplicati;
  - non rispetta bene la gerarchia tra orari reali e scadenze operative;
  - rende difficile confinare la finanza in contesti dedicati.

### Option B - Quattro dashboard separate e indipendenti

- Pro:
  - implementazione concettuale piu lineare;
  - facile assegnare ownership ai moduli.
- Contro:
  - forza il trainer a cambiare contesto per capire cosa fare;
  - aumenta il rischio di ridondanze tra moduli;
  - non crea una vera home unica;
  - rende piu difficile costruire `Next Best Action` cross-domain.

### Option C - Un solo Case Engine con dual timeline e 4 workspace preset

- Pro:
  - riduce duplicazioni;
  - permette una home `Oggi` davvero cross-domain;
  - mantiene separata agenda oraria da queue operativa;
  - supporta viste native e future viste salvate sullo stesso modello;
  - consente reason line, merge rules e priorita spiegabili.
- Contro:
  - richiede un modello concettuale piu rigoroso;
  - impone regole di merge e ranking cross-domain ben definite;
  - aumenta il lavoro iniziale di information architecture.

## Decision

Viene scelta `Option C`.

FitManager introdurra un `Case Engine` unificato basato su tre livelli:

- `Signal`: fatto grezzo osservabile;
- `Case`: unita operativa mostrata al trainer;
- `Action`: risposta corretta e consentita al case.

La nuova home post-login target diventera `Oggi`.

La navigazione workspace usera 4 preset nativi sullo stesso motore:

- `Oggi`
- `Onboarding`
- `Programmi`
- `Rinnovi & Incassi`

Il sistema non usera una sola timeline cronologica. Usera invece due letture coordinate:

- `Timeline Agenda` per elementi con orario reale;
- `Operational Queue` per casi ordinati per finestra di urgenza.

La dashboard overview attuale non viene eliminata: viene riposizionata come superficie secondaria, raccomandata con naming `Panoramica`.

## Consequences

- Positive:
  - FitManager puo diventare la home mentale quotidiana del trainer;
  - il trainer vede problemi reali e non dati grezzi;
  - la finanza resta confinata nei contesti giusti;
  - il modello e estendibile a nuovi domini senza ridisegnare tutta la UX.
- Negative:
  - serve definire con precisione catalogo casi, merge rules e priority rules;
  - alcune superfici esistenti dovranno essere riallineate di naming e ruolo;
  - la prima implementazione dovra evitare di trasformare `Oggi` in una dashboard sovraccarica.
- Follow-up actions:
  - approvare la spec `UPG-2026-03-09-02`;
  - definire shape payload read-only del workspace;
  - mappare segnali esistenti ai case type iniziali;
  - pianificare il cutover route `home -> Oggi`, `dashboard -> Panoramica`.

## Rollback / Exit Strategy

Se il modello si rivelasse troppo denso o costoso da implementare:

- mantenere la dashboard overview attuale come default;
- usare `Oggi` come route secondaria o feature flag;
- ridurre il case engine ai domini `Agenda + Onboarding + Incassi`;
- trattare i workspace rimanenti come viste successive invece che parte del primo cutover.

## Supersedes / Superseded By

- Supersedes: nessuno
- Superseded by: da definire
