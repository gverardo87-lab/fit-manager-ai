# FitManager AI Studio - Runbook Supporto, Licenza e Recovery

> Documento operativo unico per assistenza su installazione locale, licenza, backup/restore
> e recovery post-update. Versione iniziale allineata allo stato del prodotto del 10 marzo 2026.

---

## 1. Obiettivo

Questo runbook serve a evitare supporto "artigianale".

Ogni intervento deve partire da evidenze locali standard:
- `Stato installazione` in `Impostazioni`
- `Snapshot diagnostico` scaricato dalla UI
- log locale in `data/logs/fitmanager.log`
- elenco backup in `data/backups/`

Principio operativo:
- prima si raccoglie il contesto;
- poi si protegge il dato;
- solo dopo si modifica l'installazione.

---

## 2. Quando usare questo runbook

Usare questo documento se il problema riguarda almeno uno di questi casi:
- FitManager non parte correttamente o parte in modalita inattesa
- la licenza risulta `missing`, `invalid`, `expired` o `unconfigured`
- il trainer viene reindirizzato a `/licenza`
- serve ripristinare dati da backup
- un aggiornamento ha introdotto un problema e bisogna tornare operativi
- c'e un dubbio su ambiente `dev/prod`, runtime `source/installer` o stato del portale pubblico

Per problemi di rete/Tailscale/Funnel usare questo runbook come ingresso rapido e poi
passare a [TAILSCALE_FUNNEL_SETUP.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/TAILSCALE_FUNNEL_SETUP.md).

---

## 3. Raccolta Evidenze

Prima di toccare file o reinstallare:

1. Aprire `Impostazioni -> Stato installazione`.
2. Aprire `Impostazioni -> Snapshot diagnostico`.
3. Scaricare il JSON di snapshot.
4. Annotare:
   - versione
   - `app_mode`
   - `distribution_mode`
   - `license_status`
   - `license_enforcement_enabled`
   - stato `db` e `catalog`
   - `public_portal_enabled`
   - `public_base_url`
   - backup recenti visibili
5. Recuperare il file log locale:
   - `data/logs/fitmanager.log`
6. Chiedere sempre:
   - cosa stava facendo il trainer
   - da quando il problema e comparso
   - se c'e stato un aggiornamento, restore o cambio licenza poco prima

Se l'app non arriva nemmeno alla UI:
- raccogliere comunque `data/logs/fitmanager.log`;
- verificare che esistano `data/crm.db`, `data/catalog.db`, `data/.env`;
- usare la sezione 7 di questo runbook.

---

## 4. Mappa Decisionale Rapida

### Caso A - Problema licenza

Indizi tipici:
- redirect a `/licenza`
- `license_status` negativo in `/health` o nello snapshot
- installazione partita da sorgente senza enforcement corretto

Vai alla sezione 5.

### Caso B - Problema dati / backup / restore

Indizi tipici:
- dati mancanti o incoerenti
- restore necessario dopo errore utente o aggiornamento
- backup non verificato o dubbio

Vai alla sezione 6.

### Caso C - L'app non parte o parte male

Indizi tipici:
- browser non raggiungibile
- health non disponibile
- DB o catalog non connessi

Vai alla sezione 7.

### Caso D - Problema dopo aggiornamento

Indizi tipici:
- il problema nasce subito dopo una nuova versione
- il trainer riferisce che "prima funzionava"

Vai alla sezione 8.

---

## 5. Runbook Licenza

### 5.1 Interpretazione rapida degli stati

| Stato | Significato operativo | Azione primaria |
|---|---|---|
| `valid` | Licenza corretta | Cercare altrove |
| `missing` | `data/license.key` assente | Installare una licenza valida |
| `expired` | Licenza scaduta | Generare e consegnare nuova licenza |
| `invalid` | File corrotto o non firmato correttamente | Rigenerare e sostituire il file |
| `unconfigured` | Configurazione chiave pubblica / ambiente non coerente | Escalation tecnica |

### 5.2 Verifica minima

Controllare uno di questi punti:
- pagina `/licenza?status=...`
- `Stato installazione`
- `support snapshot`
- `GET /health` se disponibile

Verificare anche:
- `distribution_mode = installer` oppure `source`
- `license_enforcement_enabled = true` in produzione

### 5.3 Avvio corretto in produzione

Le due modalita sicure sono:

1. Installazione reale:
   - `installer/launcher.bat`

2. Produzione da sorgente:
   ```bash
   LICENSE_ENFORCEMENT_ENABLED=true uvicorn api.main:app --host 0.0.0.0 --port 8000
   cd frontend && npm run build && npm run prod
   ```

Non considerare valida una sessione "prod" avviata da sorgente senza
`LICENSE_ENFORCEMENT_ENABLED=true`.

### 5.4 Sostituzione della licenza

Procedura standard:

1. Chiudere FitManager.
2. Posizionare il nuovo file in:
   - `data/license.key`
3. Non rinominare il file.
4. Non aprire e non modificare il contenuto a mano.
5. Riavviare FitManager con la modalita corretta.
6. Verificare:
   - `license_status = valid`
   - `license_enforcement_enabled = true` in produzione
   - apertura normale della UI senza redirect a `/licenza`

### 5.5 Quando fermarsi e fare escalation

Escalare se:
- `license_status = unconfigured`
- la licenza risulta `invalid` anche dopo rigenerazione e sostituzione pulita
- il launcher e corretto ma l'istanza continua a partire senza enforcement
- la UI e il backend danno stati licenza incoerenti

Artefatti da allegare all'escalation:
- snapshot diagnostico JSON
- ultime 100 righe di `data/logs/fitmanager.log`
- stato della pagina `/licenza`

---

## 6. Runbook Backup e Restore

### 6.1 Regola non negoziabile

Mai sovrascrivere manualmente `crm.db` o i file `-wal` / `-shm`.

FitManager usa restore page-level via `sqlite3.backup()` proprio per evitare corruzioni
in WAL mode. Il restore corretto passa sempre dagli endpoint/UI di backup.

### 6.2 Prima di qualsiasi restore

Se l'app e ancora accessibile:

1. Creare un backup manuale.
2. Verificare il backup.
3. Scaricare, se serve, anche lo snapshot diagnostico.

Se l'app non e accessibile ma il DB esiste ancora:
- copiare in sola sicurezza la cartella `data/backups/` se necessario per analisi;
- non tentare overwrite manuali del DB live.

### 6.3 Sequenza standard di restore

1. Identificare il backup corretto in `data/backups/`.
2. Se possibile verificarlo prima del restore.
3. Eseguire il restore dall'app o dall'endpoint dedicato.
4. Attendere il completamento:
   - FitManager crea un safety backup `pre_restore_*`
   - esegue integrity check
   - forza WAL checkpoint
   - riallinea lo schema
5. Al termine:
   - la sessione utente viene invalidata
   - serve nuovo login

### 6.4 Verifiche post-restore

Dopo il nuovo login controllare:
- dashboard raggiungibile
- cliente noto presente
- almeno un contratto noto presente
- pagina cassa raggiungibile
- `Stato installazione` con `db = connected` e `catalog = connected`

### 6.5 Recovery del restore fallito

Se il restore ha peggiorato la situazione:

1. Cercare il safety backup `pre_restore_*.sqlite`.
2. Ripetere il restore usando quel safety backup.
3. Verificare di nuovo health e login.

### 6.6 Esportazione per supporto

Se il trainer chiede massima sicurezza prima di un intervento:
- creare un backup normale;
- creare anche un export dati se utile al supporto funzionale;
- conservare sempre il file originale prima del restore.

---

## 7. Runbook App Non Raggiungibile o Runtime Rotto

### 7.1 Controlli minimi

Verificare:
- il launcher e in esecuzione
- esiste `data/logs/fitmanager.log`
- esistono `data/crm.db` e `data/catalog.db`
- esiste `data/.env`

### 7.2 Controlli logici da fare subito

Nel log cercare:
- errori di avvio backend
- problemi su licenza
- errori DB/catalog
- crash subito dopo startup

### 7.3 Distinzione source vs installer

Se `distribution_mode = source` o il trainer usa una sessione da sviluppo:
- verificare che non stia lavorando per errore su ambiente sbagliato;
- in produzione reale la base consigliata resta l'installer.

### 7.4 Se il DB business e offline

Azioni:
- non lanciare seed o reset;
- non usare script distruttivi;
- valutare restore dal backup piu recente valido.

### 7.5 Se il catalog e offline

Questo e un caso da escalation tecnica.
Il catalog non contiene dati business del trainer, ma senza `catalog.db` il prodotto e incompleto.

---

## 8. Runbook Post-Update Recovery

### 8.1 Prima dell'aggiornamento

La procedura corretta e:

1. Creare `pre-update backup`.
2. Conservare l'installer precedente.
3. Annotare la versione corrente.

### 8.2 Se l'aggiornamento introduce un problema

Ordine di intervento:

1. Raccogliere snapshot diagnostico e log.
2. Verificare la nuova versione visibile in `Stato installazione`.
3. Se il problema e bloccante:
   - reinstallare la versione precedente disponibile
   - se necessario ripristinare il `pre_update_*.sqlite`
4. Verificare login e flusso core:
   - cliente
   - contratto
   - rata/incasso
   - backup

### 8.3 Definizione di recovery riuscito

La recovery e riuscita solo se:
- l'app apre normalmente;
- il login funziona;
- i dati principali sono presenti;
- health/snapshot tornano coerenti;
- non resta un problema licenza o DB aperto.

---

## 9. Cosa Non Fare

- Non sovrascrivere a mano i file SQLite del live system.
- Non usare `alembic upgrade head` da solo sui DB del cliente.
- Non lanciare seed/reset su `crm.db`.
- Non avviare la produzione da sorgente senza `LICENSE_ENFORCEMENT_ENABLED=true`.
- Non chiedere screenshot al posto di snapshot/log quando il prodotto e raggiungibile.
- Non condividere pubblicamente snapshot o log senza revisione, anche se non contengono PII business intenzionale.

---

## 10. Pacchetto Minimo da Inviare al Supporto

Per ogni ticket serio raccogliere:
- snapshot diagnostico JSON
- versione visualizzata in `Impostazioni`
- stato licenza visualizzato
- ultime righe di `data/logs/fitmanager.log`
- nome del backup eventualmente usato
- descrizione breve:
  - cosa stava facendo l'utente
  - cosa si aspettava
  - cosa e successo davvero

---

## 11. Collegamenti Operativi

- [RELEASE_CHECKLIST.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/RELEASE_CHECKLIST.md)
- [TAILSCALE_FUNNEL_SETUP.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/TAILSCALE_FUNNEL_SETUP.md)
- [DEPLOYMENT_PLAN.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/DEPLOYMENT_PLAN.md)
- [UPG-2026-03-10-09-launch-operations-plan-v1.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md)

---

## 12. Limiti di questa v1

Questa versione non copre ancora:
- workflow di rinnovo licenza in-app
- code signing Windows
- procedura macchina pulita dettagliata con screenshot
- diagnostica remota automatica

Questa v1 serve a una cosa precisa: rendere ripetibile il supporto di primo livello
su installazione, licenza, backup/restore e recovery post-update.
