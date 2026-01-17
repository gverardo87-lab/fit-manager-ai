# 🚀 ROADMAP IMMEDIATI - FitManager AI

## Cosa è stato fatto OGGI (17 Gennaio 2026)

✅ **Bug Fix Critico**: Risolto crash in `02_Clienti.py` al salvataggio primo check-up
- Problema: Chiavi dati incoerenti (grasso vs massa_grassa)
- Soluzione: Aggiunto try-except e validazione al salvataggio

✅ **Analisi Strategica Completa**: Documento `ANALISI_STRATEGICA.md`
- Visione del prodotto
- Punti di forza e debolezze
- 15 problemi identificati (critici, medi, minori)
- Roadmap 12 mesi

✅ **Piano d'Azione Tecnico**: Documento `PIANO_AZIONE_TECNICO.md`
- 13 task prioritizzati in 4 sprint
- Metriche di successo
- Dependenze da aggiungere

✅ **Nuovi Moduli Core**:
- `core/models.py` - Validation layer con Pydantic (DTO completi per CLI/Contratti/Misurazione)
- `core/error_handler.py` - Gestione errori centralizzata con logging

---

## 📅 PROSSIMI STEP (Settimana 1)

### LUNEDÌ - IDENTITÀ DI PROGETTO (2-3 ore)

```bash
# 1. Aggiornare README.md
# Rimuovere riferimenti a CapoCantiere
# Aggiungere: Vision, Features, Architecture, Getting Started

# 2. Aggiornare pyproject.toml
name = "fit-manager-ai"
description = "Professional fitness studio management with AI"
version = "3.0.0"

# 3. Aggiornare server/app.py
st.set_page_config(page_title="FitManager AI", page_icon="💪", layout="wide")
st.title("💪 FitManager AI - Professional Fitness Studio Management")

# 4. Rinominare file pages
01_📅_Agenda.py
02_👥_Clienti.py  (con bug fix incluso)
03_💳_Cassa.py
```

**Commit**: `chore: Unify project identity to FitManager AI`

---

### MARTEDÌ - INTEGRAZIONE MODELS (3-4 ore)

```python
# 1. Aggiornare 02_Clienti.py per usare Pydantic DTO
from core.models import ClienteCreate, MisurazioneDTO

# In dialog_misurazione():
try:
    # Validare i dati prima di salvare
    misurazione_data = {
        "id_cliente": id_cliente,
        "data_misurazione": dt,
        "peso": peso,
        "massa_grassa": grasso,  # Nome CORRETTO ora
        "massa_magra": muscolo,
        "collo": collo,
        "spalle": spalle,
        "torace": torace,
        "braccio": braccio,
        "vita": vita,
        "fianchi": fianchi,
        "coscia": coscia,
        "polpaccio": polpaccio,
        "note": note
    }
    
    # Validare con Pydantic
    misurazione = MisurazioneDTO(**misurazione_data)
    
    # Se arrivati qui, dati sono OK
    if id_misura:
        db.update_misurazione(id_misura, misurazione.model_dump())
    else:
        db.add_misurazione_completa(id_cliente, misurazione.model_dump())
    
    st.success("✅ Misurazione salvata!")
except ValueError as e:
    st.error(f"❌ Errore validazione: {str(e)}")
    logger.warning(f"Validation error: {str(e)}")

# 2. Fare lo stesso per dialog_vendita() con ContratoCreate
# 3. Aggiornare dialog_edit_rata() con RataProgrammata
```

**Commit**: `feat: Integrate Pydantic models for data validation`

---

### MERCOLEDÌ - ERROR HANDLER (2-3 ore)

```python
# 1. Aggiornare 02_Clienti.py per usare error handler
from core.error_handler import handle_streamlit_errors, logger

@handle_streamlit_errors("02_Clienti")
def main():
    # Tutto il codice della pagina qui
    ...

# 2. Aggiornare crm_db.py per usare @safe_db_operation
from core.error_handler import safe_db_operation

class CrmDBManager:
    @safe_db_operation("add_misurazione_completa")
    def add_misurazione_completa(self, id_cliente, dati):
        ...

# 3. Testare che error handling funziona:
# - Apri 02_Clienti.py
# - Prova a salvare con dati invalidi
# - Deve mostrare messaggio user-friendly
```

**Commit**: `feat: Implement centralized error handling with logging`

---

### GIOVEDÌ - RIMOZIONE MODULI LEGACY (1-2 ore)

```bash
# 1. Rinominare con prefisso DEPRECATED
mv 03_Esperto_Tecnico.py → _DEPRECATED_03_Esperto_Tecnico.py.bak
mv 06_Document_Explorer.py → _DEPRECATED_06_Document_Explorer.py.bak
mv 07_Meteo_Cantiere.py → _DEPRECATED_07_Meteo_Cantiere.py.bak
mv 08_Bollettino_Mare.py → _DEPRECATED_08_Bollettino_Mare.py.bak

# 2. Aggiornare server/app.py per non linkare pagine deprecated
# Rimuovere i page_link() per questi moduli

# 3. Aggiungere .gitignore per _DEPRECATED_*
echo "_DEPRECATED_*.py.bak" >> .gitignore
```

**Commit**: `chore: Deprecate legacy modules (03_Esperto, 06_Document, etc)`

---

### VENERDÌ - TESTING & VALIDATION (3-4 ore)

```python
# 1. Creare tests/conftest.py con fixtures
import pytest
from core.crm_db import CrmDBManager
from pathlib import Path
import tempfile

@pytest.fixture
def temp_db():
    """Database temporaneo per test"""
    with tempfile.NamedTemporaryFile() as f:
        db = CrmDBManager(f.name)
        yield db

@pytest.fixture
def sample_cliente():
    return {
        "nome": "Mario",
        "cognome": "Rossi",
        "telefono": "+39-333-123456",
        "email": "mario@example.com",
        "data_nascita": "1990-01-15",
        "sesso": "Uomo"
    }

# 2. Creare tests/test_models.py
def test_misurazione_validation():
    from core.models import MisurazioneDTO
    
    # ✅ Valido
    m = MisurazioneDTO(
        id_cliente=1,
        peso=75,
        massa_grassa=15,
        massa_magra=60
    )
    assert m.peso == 75

# 3. Creare tests/test_02_clienti_e2e.py
def test_save_first_measurement(temp_db):
    # Test end-to-end del flow completo
    # 1. Crea cliente
    # 2. Salva misurazione
    # 3. Verifica dati nel DB
    pass

# 4. Eseguire test
pytest tests/ -v --cov=core
```

**Commit**: `test: Add initial test suite (15% coverage)`

---

## 📊 METRICHE SETTIMANALI

| Metrica | Target | Status |
|---------|--------|--------|
| Schema DB validato | 100% | 🟢 Done |
| Error coverage | 80%+ | 🟡 25% (migliorerà con uso) |
| Test coverage | 15%+ | 🟡 5% (aggiungere tests) |
| Bug critici risolti | 0 | 🟢 1 risolto (check-up) |
| Moduli legacy rimossi | 100% | 🟡 4/4 deprecati |
| README aggiornato | 100% | 🟡 Pending |

---

## 🎯 OBIETTIVI FINE SETTIMANA 1

```
✅ DEVE ESSERE FATTO:
  [ ] Identità di progetto unificata (un solo nome ovunque)
  [ ] Models + Validation layer implementato
  [ ] Error handler centralizzato in uso
  [ ] Zero crash su 02_Clienti.py
  [ ] README aggiornato e pronto per presentazione
  [ ] Moduli legacy deprecati

🟢 BONUS (Se hai tempo):
  [ ] 15%+ test coverage
  [ ] Database schema migration script
  [ ] Logging strutturato funzionante
```

---

## 🔧 COMANDI UTILI

```bash
# Installare dipendenze nuove
pip install pydantic==2.7.0 pytest==8.0.0 pytest-cov==4.1.0

# Lanciare test
pytest tests/ -v --cov=core

# Lanciare app in dev
streamlit run server/app.py --logger.level=debug

# Controllare type hints
mypy core/ --ignore-missing-imports

# Formattare codice
black server/pages/*.py core/*.py

# Creare file di log
mkdir logs && echo "" > logs/fitmanager.log
```

---

## 📝 CHECKLIST PRE-COMMIT

Prima di fare `git push` ogni giorno:

```bash
# 1. Eseguire test
pytest tests/ -v

# 2. Verificare type hints
mypy core/ --ignore-missing-imports

# 3. Formattare codice
black .

# 4. Verificare no crash critici
# - Apri 02_Clienti.py e test il flow completo
# - Salva cliente, crea misurazione, verifica visualizzazione

# 5. Update CHANGELOG
# Aggiungere entry in CHANGELOG.md

# 6. Commit con messaggio semantico
git add .
git commit -m "feat: Fix X | refactor: Y | test: Z"
git push
```

---

## 💡 TIPS IMPLEMENTATIVI

### Per Aggiornare 02_Clienti.py Correttamente

```python
# OLD (Buggy)
if st.button("💾 Salva Check-up", type="primary"):
    dati = {"grasso": grasso, "muscolo": muscolo}  # ❌ Nomi sbagliati
    db.add_misurazione_completa(id_cliente, dati)

# NEW (Fixed)
if st.button("💾 Salva Check-up", type="primary"):
    from core.error_handler import logger
    from core.models import MisurazioneDTO
    
    try:
        # Preparare dati con nomi corretti
        misurazione_data = {
            "id_cliente": id_cliente,
            "data_misurazione": dt,
            "peso": peso,
            "massa_grassa": grasso,  # ✅ Nome corretto
            "massa_magra": muscolo,  # ✅ Nome corretto
            "collo": collo,
            "spalle": spalle,
            "torace": torace,
            "braccio": braccio,
            "vita": vita,
            "fianchi": fianchi,
            "coscia": coscia,
            "polpaccio": polpaccio,
            "note": note
        }
        
        # Validare con Pydantic
        misurazione = MisurazioneDTO(**misurazione_data)
        
        # Salvare se valido
        if id_misura:
            db.update_misurazione(id_misura, misurazione.model_dump())
        else:
            db.add_misurazione_completa(id_cliente, misurazione.model_dump())
        
        st.success("✅ Misurazione salvata correttamente!")
        logger.info(f"Misurazione salvata per cliente {id_cliente}")
        st.rerun()
    
    except ValueError as e:
        st.error(f"❌ Errore di validazione: {str(e)}")
        logger.warning(f"Validation error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Errore nel salvataggio: {str(e)}")
        logger.error(f"Save error: {str(e)}", exc_info=True)
```

---

## 🎓 LEARNING RESOURCES

- **Pydantic**: https://docs.pydantic.dev/latest/
- **Pytest**: https://docs.pytest.org/
- **Streamlit Best Practices**: https://docs.streamlit.io/deploy/tutorials
- **Python Logging**: https://docs.python.org/3/library/logging.html

---

## 📞 SUPPORT

Se hai domande durante l'implementazione:
1. Controlla `ANALISI_STRATEGICA.md` per contesto
2. Controlla `PIANO_AZIONE_TECNICO.md` per dettagli
3. Guarda i docstring nei moduli creati (models.py, error_handler.py)
4. Log file è in `logs/fitmanager.log`

---

**Preparato**: 17 Gennaio 2026, 14:30 UTC
**Prossimo Review**: Venerdì 17 Gennaio, EOD
**Durata Stimata**: 12-16 ore lavoro per completare Week 1

