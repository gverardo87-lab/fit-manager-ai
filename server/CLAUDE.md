# Server - UI Layer (Streamlit)

Questa cartella contiene SOLO la presentazione. ~5.000 LOC.

## Regole

- Importare solo da `core/repositories/`, `core/models.py`, `core/ui_components.py`
- Mai importare `sqlite3` direttamente (zero violazioni ad oggi)
- Validare con Pydantic PRIMA di chiamare il repository
- Gestire SEMPRE il caso `None` da repository (fallback di @safe_operation):
  ```python
  result = repo.method()
  if result is None:
      st.error("Operazione non riuscita")
      return
  ```
- Azioni distruttive: SEMPRE con conferma (render_confirm_delete / render_confirm_action)

## Struttura pagina standard

```python
import streamlit as st
from core.repositories import ClientRepository
from core.models import ClienteCreate
from core.ui_components import load_custom_css, render_confirm_delete

st.set_page_config(page_title="...", page_icon=":material/...", layout="wide")
load_custom_css()  # SEMPRE come prima cosa dopo set_page_config

repo = ClientRepository()

# Session state initialization
if 'my_key' not in st.session_state:
    st.session_state.my_key = None

# Sidebar per filtri/selezione
with st.sidebar:
    ...

# Contenuto principale
# Form con validazione Pydantic on submit
# Gestione None returns
```

## Mappa pagine

| Pagina | LOC | Repository usati | Responsabilita' |
|--------|-----|-----------------|-----------------|
| app.py | 328 | Client, Agenda, Financial, Contract | Dashboard, KPI, sessioni imminenti, alert |
| 01_Agenda | 344 | Client, Agenda | Calendario FullCalendar, CRUD eventi, crediti |
| 02_Assistente_Esperto | 347 | KnowledgeChain | Chat RAG, viewer PDF, fonti |
| 03_Clienti | 472 | Client, Contract, Agenda | Profilo, contratti, rate, storico |
| 04_Cassa | 1117 | Client, Contract, Financial | Cash flow, rate, spese fisse, filtri avanzati |
| 05_Analisi_Margine | 482 | Financial | Margine orario, target, trend, per-cliente |
| 06_Assessment | 729 | Client, Assessment | Assessment iniziale/followup, foto, grafici |
| 07_Programma | 988 | Client, Workout, CardImport, TrainerDNA | Generazione AI, salvati, importa, DNA |
| 08_Document_Explorer | ~200 | DocumentManager | Browser PDF, ricerca, navigazione |

## UI Components (core/ui_components.py, 555 LOC)

Componenti riutilizzabili da usare INVECE di HTML inline:

| Funzione | Uso |
|----------|-----|
| `load_custom_css()` | Carica CSS centralizzato (chiamare in ogni pagina) |
| `badge(text, variant)` | Badge colorato (success, warning, danger, info) |
| `status_badge(status)` | Badge automatico per stati comuni |
| `format_currency(value)` | Formato europeo: € 1.234,56 |
| `render_metric_box(label, value)` | KPI box stilizzato |
| `render_card(title, content)` | Card con varianti |
| `render_confirm_delete(item_id, session_key, details, callback)` | Conferma CRITICA: checkbox + bottone disabilitato |
| `render_confirm_action(item_id, session_key, message, label, callback)` | Conferma LEGGERA: warning + 2 bottoni |
| `empty_state_component(title, description)` | Empty state (DA USARE PIU' SPESSO) |
| `render_success_message(text)` | Messaggio successo stilizzato |
| `render_error_message(text)` | Messaggio errore stilizzato |

## Design System

CSS centralizzato in `server/assets/styles.css` con variabili:
- Colori: `var(--primary)` blu, `var(--secondary)` verde, `var(--accent)` arancione, `var(--danger)` rosso
- Spacing: `var(--radius)`, `var(--shadow)`
- Componenti: `.kpi-card`, `.card`, `.badge`, `.badge-success/warning/danger`

Tema Streamlit in `.streamlit/config.toml` (light mode).

**Problema noto**: alcune pagine usano colori hardcoded (#0066cc) invece di var(--primary). Da uniformare.
**Problema noto**: mix di st.metric() e HTML KPI cards. Scegliere un pattern unico.

## Pattern Session State

- Inizializzare SEMPRE all'inizio della pagina: `if 'key' not in st.session_state: st.session_state.key = None`
- Per conferme distruttive: `st.session_state.deleting_X_id = item_id` -> mostra pannello -> reset a None
- Per dialog (@st.dialog): `st.rerun()` re-renderizza il dialog, non chiude la finestra
- Chiavi dinamiche (es. `f'confirm_{id}'`): funzionano ma creano chiavi "garbage" nel session state

## Problemi noti UI

- **04_Cassa.py** (1117 LOC): pagina piu' grande, candidata per split in sotto-componenti
- **07_Programma.py** (988 LOC): seconda piu' grande, complessita' giustificata dalla pipeline AI
- **Responsivita' mobile**: zero media queries nel CSS, layout solo desktop
- **Dark mode**: non implementato
- **Conversione Pydantic->dict**: pattern ripetuto in 5 pagine, da estrarre in utility
- **Valori hardcoded**: date default (1990-01-01), genere default ("Uomo"), path foto - da spostare in config
