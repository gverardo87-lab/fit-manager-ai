# 🛠️ PIANO DI AZIONE TECNICO - FitManager AI

## FASE 1: STABILIZZAZIONE CRITICA (Questa settimana)

### TASK 1: Unificare Identità di Progetto ⭐ PRIORITÀ 1

**Problema**: 3 nomi diversi (CapoCantiere, FitManager, ProFit)

**Azioni**:
```bash
# 1. Rinominare file
mv server/pages/01_Agenda.py → 01_📅_Agenda.py
mv server/pages/02_Clienti.py → 02_👥_Clienti.py
mv server/pages/03_Cassa.py → 03_💳_Cassa.py

# 2. Aggiornare README.md completamente
# 3. Aggiornare pyproject.toml (name, description)
# 4. Aggiornare server/app.py (title, icon)
```

**File da Aggiornare**:
- [README.md](README.md) - Rimpiazzare CapoCantiere con FitManager
- [pyproject.toml](pyproject.toml) - name="fit-manager-ai", update description
- [server/app.py](server/app.py) - page_title="FitManager AI", icon="🏋️"
- `.env.example` - creare con variabili corrette

---

### TASK 2: Schema DB Validation ⭐ PRIORITÀ 1

**Problema**: Inconsistenza nelle chiavi (grasso vs massa_grassa, data vs data_misurazione)

**Soluzione**: Introdurre Pydantic DTO + validazione
```python
# core/models.py (NUOVO FILE)
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional

class MisurazioneDTO(BaseModel):
    id_cliente: int
    data_misurazione: date = Field(default_factory=date.today)
    peso: float = Field(ge=20, le=300)  # Validazione range
    massa_grassa: float = Field(ge=0, le=60)  # Nome CORRETTO
    massa_magra: float = Field(ge=0, le=200)
    acqua: Optional[float] = 0
    collo: Optional[float] = 0
    spalle: Optional[float] = 0
    torace: Optional[float] = 0
    braccio: Optional[float] = 0
    vita: Optional[float] = 0
    fianchi: Optional[float] = 0
    coscia: Optional[float] = 0
    polpaccio: Optional[float] = 0
    note: Optional[str] = ""
    
    @field_validator('peso')
    def validate_peso(cls, v):
        if v < 20 or v > 300:
            raise ValueError('Peso deve essere tra 20 e 300 kg')
        return v

class ClienteDTO(BaseModel):
    id: Optional[int] = None
    nome: str = Field(min_length=1)
    cognome: str = Field(min_length=1)
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = None
    
    @field_validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Email non valida')
        return v

class ContratoDTO(BaseModel):
    id: Optional[int] = None
    id_cliente: int
    tipo_pacchetto: str
    data_inizio: date
    data_scadenza: date
    crediti_totali: int = Field(ge=1)
    prezzo_totale: float = Field(ge=0)
    acconto: Optional[float] = 0
    
    @field_validator('data_scadenza')
    def validate_dates(cls, v, info):
        if 'data_inizio' in info.data and v <= info.data['data_inizio']:
            raise ValueError('Data scadenza deve essere dopo inizio')
        return v
```

**File da Aggiornare**:
- ✅ Creato: [core/models.py](core/models.py)
- [core/crm_db.py](core/crm_db.py#L265) - Usare DTO in add_misurazione_completa()
- [server/pages/02_Clienti.py](server/pages/02_Clienti.py#L65) - Aggiornare dialog_misurazione()

---

### TASK 3: Error Handler Centralizzato ⭐ PRIORITÀ 1

**Nuovo File**: [core/error_handler.py](core/error_handler.py)
```python
import streamlit as st
from typing import Callable, Any
import logging
from functools import wraps

logger = logging.getLogger("fitmanager")

class FitManagerException(Exception):
    """Base exception per FitManager"""
    pass

class ClienteNotFound(FitManagerException):
    pass

class ContrattoInvalido(FitManagerException):
    pass

class DatabaseError(FitManagerException):
    pass

def handle_streamlit_error(func: Callable) -> Callable:
    """Decorator per handling errors in Streamlit pages"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FitManagerException as e:
            st.error(f"❌ Errore applicazione: {str(e)}")
            logger.error(f"FitManager error in {func.__name__}: {str(e)}")
        except ValueError as e:
            st.error(f"❌ Valore non valido: {str(e)}")
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
        except Exception as e:
            st.error(f"❌ Errore critico: {str(e)}")
            logger.exception(f"Unexpected error in {func.__name__}")
            st.info("👨‍💻 Contatta l'amministratore se il problema persiste")
    return wrapper

def safe_db_operation(func: Callable) -> Callable:
    """Decorator per operazioni DB con rollback automatico"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"DB operation failed: {str(e)}")
            raise DatabaseError(f"Errore nel database: {str(e)}")
    return wrapper
```

**Utilizzo nei moduli**:
```python
# core/crm_db.py
from core.error_handler import safe_db_operation

@safe_db_operation
def add_misurazione_completa(self, id_cliente, dati):
    # ... existing code
```

---

### TASK 4: Rimuovere Moduli Legacy ⭐ PRIORITÀ 2

**Azione**: Consolidare/Deprecare moduli orfani

```
❌ Da eliminare o rinominare:
  - 03_Esperto_Tecnico.py (legacy, sovrapposizione con 02_Expert_Chat)
  - 06_Document_Explorer.py (solo lettura, incompleto)
  - 07_Meteo_Cantiere.py (template non funzionante)
  - 08_Bollettino_Mare.py (API non completata)

✅ Mantenere in sprint 2:
  - core/chat_logic.py (refactor per pt_coaching)
  - core/workflow_engine.py (completare per allenamenti)
```

**Azione Concreta**:
```bash
# Rinominare con prefisso DEPRECATED
mv 03_Esperto_Tecnico.py → _DEPRECATED_03_Esperto_Tecnico.py
mv 06_Document_Explorer.py → _DEPRECATED_06_Document_Explorer.py
```

---

### TASK 5: CSS Esterno ⭐ PRIORITÀ 2

**Problema**: CSS inline in ogni pagina (duplicato, non manutenibile)

**Soluzione**: [server/styles.css](server/styles.css)
```css
/* Global Styles */
:root {
    --primary: #0068c9;
    --success: #09ab3b;
    --warning: #f7a800;
    --danger: #ff5630;
    --light: #f8f9fa;
    --dark: #1f2937;
}

/* Metric Cards */
.stMetric {
    background-color: #ffffff;
    padding: 15px 20px;
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border: 1px solid #f0f0f0;
    transition: transform 0.2s;
}

.stMetric:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.1);
}

/* Dialog Styling */
.dialog-container {
    background: white;
    border-radius: 10px;
    padding: 20px;
}

/* Responsive */
@media (max-width: 768px) {
    .stMetric { padding: 10px 15px; }
}
```

**Usare in Pages**:
```python
# server/pages/02_Clienti.py
import streamlit as st

st.markdown("""
    <style>
        %s
    </style>
    """ % open("server/styles.css").read(), unsafe_allow_html=True)
```

---

## FASE 2: FEATURE CORE (Week 3-4)

### TASK 6: Completare Modulo Cassa 💳

**File**: [server/pages/03_Cassa.py](server/pages/03_Cassa.py)

**Features da implementare**:
- Riepilogo incassi giornalieri/mensili
- Tracking rate pagate vs scadute
- Report storico pagamenti per cliente
- Esportazione PDF cedolini

---

### TASK 7: Workout Templates 🏋️

**File**: [core/workout_templates.py](core/workout_templates.py) (NUOVO)

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Exercise:
    name: str
    sets: int
    reps: str  # "8-10" o "30s"
    rest_seconds: int
    notes: str = ""

@dataclass
class WorkoutSession:
    id: str
    name: str
    target_body_parts: List[str]
    duration_minutes: int
    difficulty: str  # Beginner, Intermediate, Advanced
    exercises: List[Exercise]
    periodicity: str  # "3x/settimana", "daily"

# Libreria template predefinita
WORKOUT_TEMPLATES = {
    "push_day": WorkoutSession(
        id="push_day",
        name="Push Day (Petto, Spalle, Tricipiti)",
        target_body_parts=["Petto", "Spalle", "Tricipiti"],
        duration_minutes=60,
        difficulty="Intermediate",
        exercises=[
            Exercise("Bench Press", 4, "6-8", 180),
            Exercise("Incline Dumbbell Press", 3, "8-10", 120),
            Exercise("Cable Flyes", 3, "12-15", 90),
            # ... altri
        ],
        periodicity="1x/settimana"
    ),
    # ... altri template
}
```

---

### TASK 8: Test Coverage 🧪

**File**: [tests/](tests/) (NUOVO FOLDER)

```
tests/
├── test_models.py          # DTO validation
├── test_crm_db.py          # Database operations
├── test_shift_service.py    # Shift logic
├── conftest.py             # Fixtures
└── test_e2e_02_clienti.py  # End-to-end
```

**Esempio test**:
```python
# tests/test_models.py
import pytest
from core.models import MisurazioneDTO, ClienteDTO

def test_misurazione_validation():
    # ✅ Valido
    m = MisurazioneDTO(
        id_cliente=1,
        peso=75.5,
        massa_grassa=15.0,
        massa_magra=60.5
    )
    assert m.peso == 75.5
    
    # ❌ Invalido
    with pytest.raises(ValueError):
        MisurazioneDTO(
            id_cliente=1,
            peso=150,  # Ok
            massa_grassa=70,  # > 60, invalid!
            massa_magra=80
        )

def test_cliente_email_validation():
    # ✅ Email valida
    c = ClienteDTO(nome="Mario", cognome="Rossi", email="mario@example.com")
    assert "@" in c.email
    
    # ❌ Email invalida
    with pytest.raises(ValueError):
        ClienteDTO(nome="Mario", cognome="Rossi", email="invalid")
```

---

## FASE 3: AI INTEGRATION (Week 5-6)

### TASK 9: Document Ingest Completo 📄

**Feature**: Drag-drop PDF → auto-index in ChromaDB

**File**: [server/pages/04_📚_Documento_Ingest.py](server/pages/04_📚_Documento_Ingest.py) (NUOVO)

```python
import streamlit as st
from core.document_manager import NavalDocumentManager

st.title("📚 Carica Libreria Allenamenti")

uploaded_files = st.file_uploader("Carica PDF allenamenti/nutrizione", accept_multiple_files=True, type="pdf")

if uploaded_files:
    doc_manager = NavalDocumentManager()
    
    with st.spinner("Indicizzazione in corso..."):
        for file in uploaded_files:
            doc_manager.ingest_document(file.name, file.getbuffer())
    
    st.success(f"✅ {len(uploaded_files)} documenti indicizzati")
    
    # Preview
    docs = doc_manager.list_documents()
    st.dataframe(docs)
```

---

### TASK 10: RAG Integration nelle Pages 🤖

**Implementare RAG Context in 02_Clienti.py**:
```python
# Aggiungi a tabs[0] (Performance):
if st.button("💬 AI Coach"):
    with st.chat_message("user"):
        query = st.text_input("Chiedi consiglio al coach...")
        if query:
            response = get_expert_response(f"Cliente {cli['nome']}: {query}")
            st.write(response)
```

---

## FASE 4: POLISH & SCALE (Week 7-8)

### TASK 11: Responsive Design
- Mobile-first CSS
- Breakpoints per tablet (768px, 1024px)
- Touch-friendly buttons

### TASK 12: Dark Mode Toggle
```python
# core/theme.py
if st.session_state.get('dark_mode', False):
    st.set_page_config(theme="dark")
else:
    st.set_page_config(theme="light")
```

### TASK 13: Export Features
- PDF schede allenamento
- CSV report clienti
- Excel contratti

---

## METRICHE DI SUCCESSO

```
✅ Sprint 1 (Stabilizzazione)
  - Schema DB 100% validato (Pydantic)
  - Zero test coverage → 15%
  - 3 bug critici fissati
  - README aggiornato e consistente

✅ Sprint 2 (Feature Core)
  - Cassa.py completo
  - Workout templates > 10 template
  - Test coverage 30%
  - Performance: query < 200ms

✅ Sprint 3 (AI)
  - RAG integrato in 3 pages
  - Document ingest funzionante
  - Chatbot context-aware

✅ Sprint 4 (MVP Release)
  - Zero crash in production (3 days stress test)
  - Mobile usabile (>60% score lighthouse)
  - NPS >40
  - <5 min onboarding
```

---

## DEPENDENZE DA AGGIUNGERE

```toml
# pyproject.toml
pydantic==2.7.0           # Validation
pytest==8.0.0             # Testing
pytest-cov==4.1.0         # Coverage
pytest-streamlit==0.2.0   # Streamlit E2E
black==24.1.0             # Code formatter
mypy==1.8.0               # Type checking
python-dotenv==1.0.1      # Already present ✓
```

---

## CHECKLIST FINALE

- [ ] README completamente aggiornato
- [ ] Schema DB con validation Pydantic
- [ ] Error handler centralizzato
- [ ] Moduli legacy deprecati
- [ ] CSS esterno
- [ ] Cassa.py completo
- [ ] Workout templates
- [ ] 30%+ test coverage
- [ ] RAG integrato
- [ ] Document ingest
- [ ] Mobile responsive
- [ ] Dark mode
- [ ] Export PDF/CSV
- [ ] Performance < 200ms queries
- [ ] Zero crash stress test

---

**Documento**: Piano d'azione tecnico
**Data**: 17 Gennaio 2026
**Durata**: 8 settimane
**Risorse**: 1-2 developer

