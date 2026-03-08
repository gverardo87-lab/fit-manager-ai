# Strategia Implementazione: Client Portal (MyPortal) e Monitoraggio Allenamenti

Questo documento delinea la strategia per l'implementazione del "Client Portal" all'interno di FitManager AI Studio. L'obiettivo è fornire ai clienti un accesso dedicato, sicuro e read-only/limitato per consultare le proprie schede, visualizzare la libreria esercizi (i 345 builtin + custom abilitati), e compilare live le sessioni di allenamento con i carichi reali.

Questa implementazione abiliterà la nuova metrica di "Compliance Allenamenti" nel monitoraggio del cliente.

## 1. Architettura e Sicurezza (Zero Cloud & Zero App)

Il cliente non scaricherà alcuna app e i dati non finiranno nel cloud. Continueremo a sfruttare **Tailscale Funnel**.

### 1.1 Sistema di Autenticazione (Magic Link)
Evitiamo di gravare il cliente con password.
- **Flusso**: Il trainer genera dal CRM un "Magic Link" o "Access Pass" permanente per il cliente (es. `https://chiara.ts.net/myportal/{client_uuid}`).
- **Implementazione Backend**: Modello `ClientAccessPass` (UUID4 `token`, `client_id`, `is_active`). Nessuna password. Il token viene salvato in un cookie HttpOnly a lunga scadenza (es. 90 giorni) sul dispositivo del cliente al primo accesso, permettendo rientri successivi senza link.
- **Revoca**: Il trainer può invalidare il pass dal CRM in qualsiasi momento.

### 1.2 Routing e UI Mobile-First
- Il portale vivrà sotto il prefisso `/myportal` in Next.js.
- **Layout Separato**: Non utilizzerà la Sidebar o il Command Palette del trainer. Avrà una bottom navigation in stile app nativa (Home, Scheda, Esercizi, Profilo).
- **Offline Resilience**: Uso massiccio di React Query e Service Worker (PWA capabilities) per gestire micro-disconnessioni in palestra.

## 2. Modello Dati (Backend)

Saranno necessarie nuove tabelle e endpoint REST esposti tramite `api/routers/myportal.py`.

### 2.1 Tabella `workout_logs` (Nuova)
Traccia l'esecuzione reale rispetto alla scheda prescritta.
- `id` (PK)
- `client_id` (FK)
- `session_id` (FK -> `sessioni_scheda`)
- `data_esecuzione` (Date)
- `durata_effettiva_minuti` (Int)
- `percezione_sforzo_rpe` (Int 1-10)
- `note_cliente` (Text)

### 2.2 Tabella `exercise_logs` (Nuova)
Traccia i set/ripetizioni reali.
- `id` (PK)
- `workout_log_id` (FK -> `workout_logs`)
- `exercise_session_id` (FK -> `esercizi_sessione`)
- `serie_numero` (Int)
- `ripetizioni_eseguite` (Int)
- `carico_kg` (Float)
- `tecnica_ok` (Bool, auto-valutazione)

## 3. Funzionalità del Portale Cliente

### 3.1 La Scheda di Allenamento (Live Mode)
- **Vista**: Riproduzione mobile-friendly della scheda attiva.
- **Esecuzione (Live Mode)**: Quando il cliente entra in palestra preme "Inizia Allenamento".
- **Compilazione**: Interfaccia a stepper/carousel per ogni esercizio. Campi input numerici larghi per inserire facilmente Kg e Reps tra una serie e l'altra con i pollici. Rest timer integrato (visivo/acustico).

### 3.2 Libreria Esercizi (Limitata)
- Il cliente può accedere al dettaglio dell'esercizio (muscoli coinvolti, SVG della muscle map, istruzioni, video/foto esecuzione).
- **Filtro Severo**: Verranno esposti solo i ~345 esercizi built-in e gli esercizi custom che il trainer ha contrassegnato come "Visibili al cliente" o che sono presenti nella scheda attuale del cliente.

### 3.3 Dashboard Cliente
- Vista progressi (grafico compliance: allenamenti completati vs previsti).
- Prossimo allenamento programmato.
- Messaggi o note dal trainer.

## 4. Evoluzione del CRM (Lato Trainer)

### 4.1 Monitoraggio Compliance (Nuova Tab nel Profilo Cliente)
- **Dati Aggregati**: Percentuale di completamento delle schede nel mese corrente.
- **Analisi Scostamenti**: Highlight visivo se il cliente abbassa sistematicamente il carico o non completa le serie prescritte.
- **Volume Load Progressivo**: Calcolo in background del Volume Load settimanale reale (Kg x Reps x Sets) basato sui dati inseriti dal cliente, confrontato con quello stimato teorico.

### 4.2 Gestione Accessi
- Pulsante per generare/revocare il Magic Link dalla pagina "Panoramica" o "Impostazioni" del profilo cliente.

## 5. Fasi di Implementazione (Roadmap Esecutiva)

### Fase 1: Data Layer & Auth (Backend)
1. Creazione modelli SQLAlchemy: `ClientAccessPass`, `WorkoutLog`, `ExerciseLog`.
2. Generazione migrazioni Alembic.
3. Creazione router `/api/myportal/` con autenticazione basata su Bearer Token (UUID), separata dal JWT del trainer.
4. Endpoint REST: validate pass, get active workout, submit logs.

### Fase 2: MyPortal Core (Frontend)
1. Configurazione Tailwind e layout mobile PWA (`/myportal/layout.tsx`).
2. Creazione pagina "Login/Access" per l'ingestione del Magic Link.
3. Creazione "Home" e visualizzazione statica della scheda.

### Fase 3: Live Workout Mode (Frontend)
1. Sviluppo del componente `LiveWorkoutSession` (state machine in React per tracciare start, timer riposo, fine set, fine sessione).
2. Sviluppo interfaccia inserimento carico/ripetizioni ottimizzata per l'uso "sudato" in palestra (bottoni +/-, tastierino numerico custom grande).
3. Integrazione con l'API per l'invio dei dati (autosave ogni set completato).

### Fase 4: Integrazione CRM (Frontend Trainer)
1. Aggiunta UI generazione Magic Link nel profilo cliente.
2. Sviluppo della nuova Tab "Compliance" e "Log Allenamenti" nel profilo cliente, con grafici Recharts per mostrare il volume di allenamento e RPE nel tempo.

## 6. Rischi e Mitigazioni

- **Disconnessioni in palestra**: Il cliente potrebbe perdere la connessione mentre compila i dati. **Mitigazione**: Il frontend React salverà lo stato dell'allenamento live in `localStorage`. Alla riconnessione (o all'avvio successivo), sincronizzerà i dati "orfani" verso il server (`SyncEngine` locale).
- **CORS e URL**: Poiché il portale cliente verrà servito dallo stesso IP/Tailscale Funnel del CRM principale, le regole CORS esistenti (aggiornate precedentemente) sono già sufficienti.
- **Sicurezza IDOR**: Endpoint del portale estremamente rigidi. Un token di accesso garantisce visibilità **solo** all'ID cliente associato. Zero possibilità di enumerare altri clienti o visualizzare l'agenda o le finanze.
