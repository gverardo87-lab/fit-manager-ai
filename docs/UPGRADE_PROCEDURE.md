# FitManager AI Studio - Procedura Upgrade Cliente

> Guida operativa utente per aggiornare FitManager sul PC del trainer senza perdere dati,
> licenza o configurazione locale.
> Questa guida e' pensata per installazioni reali gia in uso.

---

## 1. Obiettivo

Aggiornare FitManager alla nuova versione in modo sicuro, con il rischio minimo possibile.

Principio guida:
- prima si protegge il dato;
- poi si aggiorna il programma;
- il restore del backup si usa solo se serve davvero.

Procedura consigliata:
- **upgrade in-place**, cioe installazione della nuova versione sopra quella esistente,
  nella stessa cartella.

Procedura da evitare come prima scelta:
- disinstallare tutto e reinstallare da zero prima ancora di verificare se l'upgrade
  standard mantiene correttamente dati e licenza.

---

## 2. Quando usare questa guida

Usa questa procedura quando:
- hai una nuova versione di `FitManager_Setup_*.exe`;
- il trainer usa gia FitManager sul proprio PC;
- vuoi mantenere dati, licenza, backup e configurazione;
- stai aggiornando il programma senza cambiare macchina.

Se invece stai installando FitManager su un nuovo PC o devi ripristinare da zero una
macchina guasta, usa prima [SUPPORT_RUNBOOK.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/SUPPORT_RUNBOOK.md).

---

## 3. Regole Non Negoziabili

- Non copiare manualmente `crm.db` sopra il database live.
- Non eliminare a mano file `-wal` o `-shm`.
- Non fare restore "per abitudine" se l'upgrade ha gia mantenuto i dati correttamente.
- Non cambiare cartella di installazione durante l'upgrade standard.
- Non perdere la copia esterna di `license.key` prima di iniziare.

---

## 4. Materiale da Preparare

Prima di iniziare devi avere:

- il nuovo installer, per esempio `FitManager_Setup_1.0.0.exe`;
- accesso al FitManager attuale sul PC del trainer;
- accesso alla cartella installata;
- una posizione sicura dove copiare temporaneamente i file critici
  (Desktop, cartella locale dedicata, chiavetta, disco esterno).

Consigliato:
- chiavetta USB o cartella dedicata `Backup Upgrade FitManager`;
- blocco note per annotare versione e percorso installazione.

---

## 5. Strategia Consigliata

### Percorso standard

1. Creare e verificare un backup.
2. Salvare fuori dall'app una copia di sicurezza di `license.key` e della cartella backup.
3. Chiudere FitManager.
4. Installare il nuovo setup **nella stessa cartella** della versione precedente.
5. Riavviare FitManager.
6. Verificare licenza, stato installazione e dati reali.
7. Usare il restore solo se emergono problemi reali.

### Perche questa e la strategia giusta

Perche riduce al minimo il rischio:
- i dati gia presenti possono restare dove sono;
- l'installer aggiorna solo i file programma;
- la cartella `data/` e progettata per essere preservata;
- eviti restore inutili su sistemi che in realta sono gia sani.

---

## 6. Checklist Pre-Upgrade

Spunta ogni voce prima di lanciare il nuovo setup.

- [ ] FitManager attuale si apre correttamente.
- [ ] Ho scaricato lo `Snapshot diagnostico` da `Impostazioni`.
- [ ] Ho creato un backup manuale dall'app.
- [ ] Ho verificato il backup, se la funzione di verifica e disponibile.
- [ ] Ho copiato fuori dalla cartella installata `data\\license.key`.
- [ ] Ho copiato fuori dalla cartella installata almeno `data\\backups\\`.
- [ ] Ho identificato la cartella installata di FitManager.
- [ ] Ho chiuso FitManager prima dell'upgrade.
- [ ] Ho il nuovo installer pronto.

Se anche solo una voce critica manca, fermati e completa prima la preparazione.

---

## 7. Procedura Dettagliata - Upgrade In-Place

### Step 1 - Apri la versione attuale

1. Avvia FitManager sul PC del trainer.
2. Vai in `Impostazioni`.
3. Controlla che l'app sia in stato normale.

### Step 2 - Salva evidenze e backup

1. Scarica lo `Snapshot diagnostico`.
2. Crea un backup manuale.
3. Se disponibile, verifica il backup.
4. Conserva questi file fuori dalla cartella installata.

### Step 3 - Copia di sicurezza minima

Copiare in una posizione sicura:

- `data\\license.key`
- `data\\backups\\`

Se vuoi la massima prudenza:
- copia tutta la cartella `data\\`

### Step 4 - Identifica la cartella di installazione

Metodo consigliato:

1. Tasto destro sull'icona di FitManager.
2. `Apri percorso file`.
3. Segna la cartella esatta.

Esempi comuni:
- `C:\\Program Files\\FitManager\\`
- `C:\\Program Files (x86)\\FitManager\\`

### Step 5 - Chiusura pulita

1. Chiudi FitManager.
2. Verifica che non restino finestre del launcher aperte.
3. Se hai dubbi, controlla Gestione Attivita.

### Step 6 - Lancia il nuovo setup

1. Esegui il nuovo `FitManager_Setup_*.exe`.
2. Quando il setup chiede il percorso di installazione:
   - usa **la stessa cartella** della versione esistente.
3. Completa l'installazione.

### Step 7 - Primo avvio post-upgrade

1. Avvia FitManager.
2. Verifica che non compaia un errore bloccante.
3. Se vieni reindirizzato a `/licenza`, passa alla sezione 9.

### Step 8 - Verifica immediata post-upgrade

Vai in `Impostazioni -> Stato installazione` e controlla:

- versione aggiornata;
- licenza valida;
- database business raggiungibile;
- catalogo raggiungibile;
- stato generale coerente.

Poi verifica a campione i dati reali:

- almeno 1 cliente noto;
- almeno 1 contratto noto;
- agenda leggibile;
- cassa leggibile;
- almeno 1 scheda visibile.

Se tutto e corretto:
- **upgrade riuscito**
- non fare restore

---

## 8. Quando Fare Restore

Fai restore del backup solo se, dopo l'upgrade:

- mancano clienti, contratti, schede o appuntamenti;
- il database risulta corrotto o non leggibile;
- l'app si apre ma i dati risultano incoerenti;
- il cambio versione ha lasciato il sistema in stato non recuperabile con i soli file esistenti.

Se i dati sono gia al loro posto, non fare restore.

---

## 9. Se La Licenza Non Viene Rilevata

Sintomi tipici:
- redirect a `/licenza`
- `license_status` non valido in `Stato installazione`

Procedura:

1. Chiudi FitManager.
2. Prendi la copia esterna di sicurezza di `license.key`.
3. Copiala in:
   - `<cartella installazione>\\data\\license.key`
4. Riavvia FitManager.
5. Ricontrolla `Impostazioni -> Stato installazione`.

Se la licenza continua a non risultare valida:
- fermati;
- non fare restore come prima mossa;
- usa [SUPPORT_RUNBOOK.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/SUPPORT_RUNBOOK.md).

---

## 10. Procedura Restore Solo Se Necessario

1. Apri FitManager.
2. Vai alla funzione di restore backup.
3. Seleziona il backup corretto.
4. Avvia il restore.
5. Attendi la conclusione completa.
6. Rifai login se richiesto.
7. Ricontrolla:
   - clienti
   - contratti
   - agenda
   - cassa
   - schede
   - media

Importante:
- non sovrascrivere mai il DB a mano dal file system;
- il restore corretto deve passare dal flusso dell'app.

---

## 11. Procedura Alternativa - Disinstalla e Reinstalla

Usala solo se:
- l'upgrade standard fallisce;
- la versione precedente e' chiaramente rotta;
- il supporto tecnico ti chiede esplicitamente di farlo.

Ordine corretto:

1. Fai backup manuale e snapshot.
2. Copia fuori `license.key`.
3. Copia fuori almeno `data\\backups\\`.
4. Disinstalla FitManager.
5. Controlla che la cartella `data\\` sia ancora presente.
6. Verifica che esistano ancora almeno:
   - `crm.db`
   - `catalog.db`
   - `license.key`
   - `backups`
7. Installa la nuova versione nella stessa cartella.
8. Avvia FitManager.
9. Verifica dati e licenza.
10. Fai restore solo se qualcosa manca.

Questa strada e' piu delicata del normale upgrade in-place.

---

## 12. Controllo Finale di Accettazione

L'upgrade e riuscito solo se alla fine risultano veri tutti questi punti:

- [ ] FitManager si apre correttamente.
- [ ] Il login funziona.
- [ ] La licenza risulta valida.
- [ ] `Stato installazione` non mostra errori bloccanti.
- [ ] I clienti reali sono presenti.
- [ ] I contratti reali sono presenti.
- [ ] Agenda e schede risultano leggibili.
- [ ] Non e stato necessario copiare manualmente alcun DB.

Se anche uno di questi punti fallisce, l'upgrade non e chiuso.

---

## 13. Cosa Fare Subito Dopo

Una volta riuscito l'upgrade:

1. Crea un nuovo backup post-upgrade.
2. Scarica un nuovo snapshot diagnostico.
3. Se il setup di connettivita e previsto:
   - apri `Impostazioni -> Connettivita`
   - completa il wizard
   - verifica il portale pubblico

Questo ti lascia una baseline pulita anche per il supporto successivo.

---

## 14. Riferimenti

- [SUPPORT_RUNBOOK.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/SUPPORT_RUNBOOK.md)
- [RELEASE_CHECKLIST.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/RELEASE_CHECKLIST.md)
- [TAILSCALE_FUNNEL_SETUP.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/TAILSCALE_FUNNEL_SETUP.md)

---

*Questa guida e' pensata per diventare una base della futura guida utente sugli upgrade del prodotto.*
