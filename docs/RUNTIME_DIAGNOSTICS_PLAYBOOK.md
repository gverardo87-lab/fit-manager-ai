# FitManager AI Studio - Runtime Diagnostics Playbook

> Playbook shell operativo per capire rapidamente se il problema e':
> - frontend/proxy;
> - backend;
> - licenza mancante;
> - processi zombie/porte occupate.
>
> Questo documento nasce dal caso reale risolto l'11 marzo 2026 durante il rollout sul
> PC del trainer: app apparentemente "rotta", ma runtime sano e `license.key` spostata
> fuori dalla cartella `data\` attiva.

---

## 1. Verita di base

Prima di qualsiasi diagnosi, ricordare il mapping corretto delle porte in produzione locale:

- **porta 3000** = frontend Next.js + proxy locale
- **porta 8000** = backend FastAPI diretto

Errore da evitare:
- invertire le porte e leggere il problema dalla sorgente sbagliata.

---

## 2. Quando usare questo playbook

Usa questi comandi se succede almeno uno di questi casi:

- il browser apre FitManager ma le pagine sembrano tutte in errore;
- dopo reinstall o upgrade non e chiaro se il problema e il setup o la licenza;
- vuoi capire se frontend e backend sono vivi separatamente;
- sospetti processi zombie su `3000` o `8000`;
- vuoi raccogliere evidenze rapide prima di fare restore o reinstallazione.

Questo playbook non sostituisce il runbook completo:
- per recovery operativa usa anche [SUPPORT_RUNBOOK.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/SUPPORT_RUNBOOK.md)
- per aggiornamenti usa anche [UPGRADE_PROCEDURE.md](/Users/gvera/Projects/FitManager_AI_Studio/docs/UPGRADE_PROCEDURE.md)

---

## 3. Diagnosi Rapida in 60 secondi

Apri **PowerShell** e lancia, in quest'ordine:

```powershell
curl.exe -i http://localhost:3000/
curl.exe -i http://localhost:3000/health
curl.exe -i http://localhost:8000/health
```

Poi verifica il file licenza:

```powershell
Test-Path "<CARTELLA_INSTALLAZIONE>\\data\\license.key"
```

Sostituisci `<CARTELLA_INSTALLAZIONE>` con il percorso reale dell'app, per esempio:

```powershell
Test-Path "C:\\Program Files\\FitManager\\data\\license.key"
```

---

## 4. Come interpretare le risposte

### Caso A - `3000` risponde con `/login`, `8000/health` segnala licenza mancante

Segnali tipici:

```powershell
curl.exe -i http://localhost:3000/
```

Risposta attesa:
- redirect `302/307` a `/login` oppure pagina login HTML

```powershell
curl.exe -i http://localhost:8000/health
```

Risposta tipica:
- backend vivo
- messaggio o payload che indica `license key not found` oppure `license_status = missing`

Interpretazione:
- frontend vivo
- backend vivo
- runtime sano
- problema reale: `data\license.key` assente nella cartella installata attiva

Azione corretta:
1. non fare restore;
2. non reinstallare come prima mossa;
3. ricopiare `license.key` in:
   - `<cartella installazione>\data\license.key`
4. riavviare FitManager.

### Caso B - `3000/health` risponde ma `8000/health` non risponde

Interpretazione:
- frontend/proxy vivo
- backend non partito, crashato o porta sbagliata

Azione corretta:
- verificare launcher, log e processo backend

### Caso C - `8000/health` risponde ma `3000` non risponde

Interpretazione:
- backend vivo
- problema frontend o processo Node

Azione corretta:
- verificare processo frontend
- controllare porte
- controllare log/launcher

### Caso D - nessuna delle due porte risponde

Interpretazione:
- FitManager non e partito davvero
- oppure ci sono state chiusure/crash

Azione corretta:
- verificare processi, launcher e log

---

## 5. Diagnosi Porte e Processi

Se i `curl.exe` non bastano, controlla direttamente chi occupa le porte:

```powershell
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

Se vedi un PID in `LISTENING`, identifica il processo:

```powershell
Get-Process -Id <PID>
```

Se scopri un processo zombie o sbagliato, puoi chiuderlo:

```powershell
taskkill /PID <PID> /T /F
```

Poi ricontrolla:

```powershell
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

Se la porta non e piu in ascolto, riavvia FitManager e ripeti i `curl.exe`.

---

## 6. Log Locale

Quando il comportamento non e chiaro, raccogli sempre anche il log runtime:

```powershell
Get-Content "<CARTELLA_INSTALLAZIONE>\\data\\logs\\fitmanager.log" -Tail 200
```

Esempio:

```powershell
Get-Content "C:\\Program Files\\FitManager\\data\\logs\\fitmanager.log" -Tail 200
```

Questo comando serve a distinguere:
- crash applicativo;
- errore di binding porte;
- errore licenza;
- errore backend startup.

---

## 7. Matrice Decisionale Rapida

| Segnale | Significato | Prima azione |
|---|---|---|
| `3000` -> `/login`, `8000/health` -> `license missing` | runtime sano, licenza mancante | ricopiare `data\license.key` |
| `3000/health` ok, `8000/health` ko | proxy vivo, backend giu | controllare backend e log |
| `8000/health` ok, `3000` ko | backend vivo, frontend giu | controllare processo Node / launcher |
| `3000` ko, `8000` ko | app non partita o crash | controllare processi, log, launcher |
| `Test-Path ...\data\license.key` -> `False` | licenza fisicamente assente | ricopiare la licenza nel percorso finale |

---

## 8. Procedura esatta per il caso licenza mancante

1. Individua la cartella installata reale.
2. Verifica:

```powershell
Test-Path "<CARTELLA_INSTALLAZIONE>\\data\\license.key"
```

3. Se il risultato e `False`, copia il file corretto in:

```text
<CARTELLA_INSTALLAZIONE>\data\license.key
```

4. Verifica che il nome non sia stato alterato:
- `license.key`
- non `license.key.txt`
- non `license (1).key`

5. Riavvia FitManager.
6. Ripeti:

```powershell
curl.exe -i http://localhost:8000/health
```

7. Se la licenza e ora valida, riapri l'app.

---

## 9. Nota storica importante

Nel caso reale risolto l'**11 marzo 2026**:

- il trainer vedeva tutte le pagine come "in errore";
- il nuovo setup sembrava sospetto;
- anche reinstallando una versione precedente il sintomo appariva uguale.

La diagnosi corretta e arrivata dai comandi shell:

```powershell
curl.exe -i http://localhost:3000/
curl.exe -i http://localhost:8000/health
```

Interpretazione corretta:
- `3000` vivo;
- `8000` vivo;
- problema non di installer o DB;
- `license.key` spostata fuori dalla cartella `data\` attiva.

Lezione di prodotto:
- prima di classificare il problema come bug runtime, restore necessario o reinstallazione
  rotta, fare sempre il check shell + file fisico.

---

## 10. Output da conservare per supporto, manuale e monografia

Per ogni caso reale, conservare:

1. output dei comandi:
   - `curl.exe -i http://localhost:3000/`
   - `curl.exe -i http://localhost:3000/health`
   - `curl.exe -i http://localhost:8000/health`
   - `Test-Path "<CARTELLA_INSTALLAZIONE>\\data\\license.key"`
2. ultime 200 righe di:
   - `data\\logs\\fitmanager.log`
3. snapshot diagnostico esportato dalla UI
4. versione installata
5. esito finale della correzione

Questo materiale non e solo supporto: e base primaria per la futura guida utente,
manuale tecnico e monografia di lancio.
