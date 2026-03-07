# FitManager Collaboration Contract v1

Protocollo operativo per la collaborazione tra utente e Codex sui task
ad alta complessita' tecnica, architetturale o scientifica.

Stato: active
Data: 2026-03-07
Baseline modello validata: `gpt-5.4`
Fonti di governo: `AGENTS.md` -> `CLAUDE.md` -> `docs/ai-sync/MULTI_AGENT_SYNC.md`

## 1. Obiettivo

Ridurre ambiguita', regressioni e dispersione nelle sessioni di sviluppo.
Questo contratto trasforma la conversazione in un workflow tecnico ripetibile.

Va usato soprattutto quando il task:

- tocca piu' layer (`frontend` + `api` + docs)
- cambia architettura o contratti dati
- coinvolge logica clinica/scientifica
- richiede refactor delicati o validazione forte

## 2. Principi Operativi

1. Contratti, non prompt liberi.
2. Runtime reale prima della documentazione, salvo documenti di governance.
3. Determinismo prima di varieta' nei flussi business-critical.
4. Un microstep verificabile alla volta.
5. Evidence over opinion: file, linee, test, output, invarianti.
6. Se emerge un tradeoff architetturale, si apre un decision gate prima di editare oltre.

## 3. Modalita' di Lavoro

All'inizio del task l'utente dichiara una modalita' primaria.

- `ANALYZE`: esplorazione e diagnosi. Nessun edit.
- `PLAN`: proposta tecnica strutturata. Nessun edit salvo docs richieste.
- `PATCH`: implementazione diretta, salvo blocker o decision gate.
- `REVIEW`: code review orientata a bug, regressioni, rischi e test mancanti.
- `VERIFY`: esecuzione di check, audit o confronto rispetto a invarianti.
- `DOCSYNC`: aggiornamento spec, log, workboard e documentazione di governo.

Se la modalita' non viene dichiarata:

- task piccoli -> `PATCH`
- task architetturali o scientifici -> `ANALYZE` poi `PLAN`

## 4. Task Brief Minimo

Per task medi o grandi, l'utente dovrebbe fornire questo frame:

```text
Mode:
Goal:
Why now:
Non-goals:
Constraints:
Files/layers likely involved:
Acceptance checks:
Decision gate:
```

Significato pratico:

- `Goal`: risultato desiderato
- `Why now`: urgenza reale o impatto atteso
- `Non-goals`: cosa NON va toccato
- `Constraints`: vincoli tecnici, di prodotto o di tempo
- `Acceptance checks`: prove minime richieste
- `Decision gate`: "decidi tu" oppure "fermati prima di cambiare X"

## 5. Risposta Attesa da Codex

Per task seri, Codex risponde sempre con questa struttura minima:

```text
Impact map
Microstep corrente
Verification plan o checks eseguiti
Risks found
Next smallest step
```

Regole:

- niente soluzioni vaghe senza impatto concreto
- niente edit multi-area senza esplicitare il perimetro
- niente "se vuoi posso" quando il task richiede esecuzione
- nessuna dichiarazione di completamento senza evidenza di verifica

## 6. Selezione Profilo Codex

Profili disponibili in `.codex/config.toml`:

- `quick`: grep, lint mirati, fix piccoli, triage rapido
- `default`: patch normali con ragionamento alto ma output compatto
- `deep`: architettura, scientific engine, migrazioni concettuali, task multi-layer
- `safe`: review o audit senza scrittura

Uso consigliato:

- bug localizzato -> `quick`
- feature standard -> `default`
- refactor SMART / SSoT / safety / architecture -> `deep`
- audit preliminare o code review -> `safe`

## 7. Contratto di Esecuzione

Durante `PATCH`, Codex segue questo loop:

1. dichiarare impact map breve
2. implementare un microstep utile
3. eseguire verifica mirata
4. fare quick technical review
5. riportare rischi e prossimo microstep

Codex deve fermarsi e chiedere conferma solo se:

- il task implica una decisione architetturale non banale
- emergono conflitti con modifiche utente non allineate
- la richiesta rischia di violare invarianti di sicurezza o prodotto

## 8. Decision Gate

Un decision gate si apre quando il task non e' piu' "solo implementazione".

Codex in quel caso deve fornire:

1. problema osservato
2. opzione A
3. opzione B
4. tradeoff concreti
5. raccomandazione

Formato desiderato:

```text
Decision gate
Problem
Option A
Option B
Recommendation
```

## 9. Handoff Packet

Ogni microstep chiuso o task interrotto deve lasciare un handoff minimo:

- stato attuale
- file toccati
- check eseguiti
- rischi aperti
- prossimo passo minimo

Questo vale anche se il task non viene completato nello stesso turno.

## 10. Addendum SMART / Training Science

Per il filone SMART questo contratto aggiunge invarianti obbligatori.

### 10.1 Invarianti

- Il backend e' la SSoT scientifica.
- La modalita' clinica deve essere deterministica.
- Nessuna costante scientifica duplicata nel frontend.
- La generazione deve essere spiegabile e auditabile.
- Il piano scientifico canonico deve essere distinguibile dalla scheda editabile.

### 10.2 Verifiche minime prima di patch architetturali

- mappa del flusso dati reale `builder -> engine -> persistence -> analysis`
- elenco delle duplicazioni scientifiche residue
- elenco delle parti non deterministiche
- elenco dei bridge frontend/backend che semplificano o distorcono il modello
- test o dataset di confronto da usare come baseline

### 10.3 Anti-pattern vietati

- refactor SMART senza dataset di verifica
- cambi di algoritmo senza tracciare l'invariante che si vuole preservare
- bridge frontend che falsano split, ruoli o parametri canonici
- random non seedato nei percorsi clinici o scientifici
- rollout che chiude solo la UI ma lascia due motori divergenti

## 11. Template Pratico da Incollare

Template breve:

```text
Mode: ANALYZE
Goal: capire dove la pipeline SMART diverge dalla SSoT backend
Why now: stiamo preparando un refactor decisivo
Non-goals: nessun edit runtime in questo step
Constraints: usa solo codice e docs del repo
Files/layers likely involved: frontend smart-programming, useTrainingScience, api/training_science
Acceptance checks: mappa gap reali + priorita' + rischi
Decision gate: fermati prima di proporre cambi schema o DB
```

Template implementativo:

```text
Mode: PATCH
Goal: spostare la generazione SMART al backend mantenendo il builder funzionante
Why now: chiudere la SSoT prima del lavoro scientifico avanzato
Non-goals: niente redesign UI in questo step
Constraints: un microstep per volta, docs sync obbligatoria
Files/layers likely involved: api training_science, frontend TemplateSelector, hooks, types, docs
Acceptance checks: test backend mirati + lint frontend file toccati
Decision gate: fermati se serve cambiare il modello dati della scheda
```

## 12. Criterio di Successo

La collaborazione funziona bene quando:

- le richieste hanno perimetro chiaro
- le risposte producono output verificabili
- i rischi emergono presto
- i microstep restano reversibili
- il contesto scientifico non si disperde in chat non tracciate

Questo documento e' un acceleratore operativo, non una formalita'.
