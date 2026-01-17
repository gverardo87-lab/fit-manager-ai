# ⚡ QUICK START - Implementazione Settimanale

**Tempo estimato**: 12-16 ore | **Difficoltà**: Media | **Prerequisiti**: Python 3.9+, Streamlit, Git

---

## 🚀 SETUP INIZIALE (15 minuti)

```bash
# 1. Installa dipendenze nuove
pip install pydantic==2.7.0 pytest==8.0.0 pytest-cov==4.1.0

# 2. Crea directory logs
mkdir -p logs

# 3. Verifica import dei moduli nuovi
python -c "from core.models import MisurazioneDTO; from core.error_handler import handle_streamlit_errors; print('✅ Setup OK')"

# 4. Verifica che Streamlit funziona
streamlit run server/app.py --logger.level=debug
```

---

## 📋 TODO CHECKLIST (Copia nei tuoi tracker task)

### LUNEDÌ - Identità di Progetto (2h)

- [ ] **README.md**
  - [ ] Rimuovere titolo "CapoCantiere AI 2.0"
  - [ ] Aggiungere titolo "FitManager AI - Professional Fitness Studio Management"
  - [ ] Aggiungere sezione "✨ Features"
  - [ ] Aggiungere sezione "🚀 Quick Start"
  - [ ] Aggiungere sezione "🏗️ Architecture"
  - [ ] Aggiungere sezione "📦 Pricing" (opzionale)

- [ ] **pyproject.toml**
  - [ ] `name = "fit-manager-ai"`
  - [ ] `version = "3.0.0"`
  - [ ] `description = "Professional fitness studio management with AI"`

- [ ] **server/app.py**
  - [ ] `st.set_page_config(page_title="FitManager AI")`
  - [ ] `st.title("💪 FitManager AI")`
  - [ ] Rimuovere link a pagine deprecated

- [ ] **Git Commit**
  ```bash
  git add README.md pyproject.toml server/app.py
  git commit -m "chore: Unify project identity to FitManager AI"
  git push
  ```

**Verifica**: `grep -r "CapoCantiere" .` deve tornare vuoto (tranne in commenti)

---

### MARTEDÌ - Integrare Pydantic Models (3h)

- [ ] **Aggiornare 02_Clienti.py**
  - [ ] Aggiungi import:
    ```python
    from core.models import MisurazioneDTO, ClienteCreate
    from core.error_handler import logger
    ```
  - [ ] In `dialog_misurazione()` sostituire linea 65-70:
    ```python
    if st.button("💾 Salva Check-up", type="primary"):
        try:
            # Preparare dati
            misurazione_data = {
                "id_cliente": id_cliente,
                "data_misurazione": dt,
                "peso": peso,
                "massa_grassa": grasso,  # ✅ Nome corretto
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
            
            # Validare
            misurazione = MisurazioneDTO(**misurazione_data)
            
            # Salvare
            if id_misura:
                db.update_misurazione(id_misura, misurazione.model_dump())
            else:
                db.add_misurazione_completa(id_cliente, misurazione.model_dump())
            
            st.success("✅ Misurazione salvata!")
            logger.info(f"Misurazione salvata per cliente {id_cliente}")
            st.rerun()
        
        except ValueError as e:
            st.error(f"❌ Errore validazione: {str(e)}")
            logger.warning(f"Validation: {str(e)}")
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
            logger.error(f"Error: {str(e)}", exc_info=True)
    ```

- [ ] **Fare lo stesso in `dialog_vendita()` (linea ~90)**
  - [ ] Aggiungere validazione `ContratoCreate`
  - [ ] Visualizzare errori user-friendly

- [ ] **Fare lo stesso in `dialog_edit_rata()` (linea ~150)**
  - [ ] Aggiungere validazione `RataProgrammata`

- [ ] **Test manuale**
  - [ ] Apri 02_Clienti.py
  - [ ] Prova a salvare con dati INVALIDI (es: peso=500, email=invalid)
  - [ ] Deve mostrare messaggio di errore

- [ ] **Git Commit**
  ```bash
  git add server/pages/02_Clienti.py
  git commit -m "feat: Integrate Pydantic models for data validation"
  git push
  ```

**Verifica**: Nessun crash, validazione funziona

---

### MERCOLEDÌ - Error Handler (3h)

- [ ] **Aggiornare 02_Clienti.py per usare error handler**
  ```python
  # Top del file
  from core.error_handler import handle_streamlit_errors, logger
  
  # Wrappare main logic
  @handle_streamlit_errors("02_Clienti")
  def main():
      # ... tutto il codice della pagina
  
  # Bottom del file
  if __name__ == "__main__":
      main()
  ```

- [ ] **Aggiornare crm_db.py**
  - [ ] Aggiungi import:
    ```python
    from core.error_handler import safe_db_operation, DatabaseError
    ```
  - [ ] Decorare metodi critici:
    ```python
    @safe_db_operation("add_misurazione_completa")
    def add_misurazione_completa(self, id_cliente, dati):
        ...
    
    @safe_db_operation("update_misurazione")
    def update_misurazione(self, id_misura, dati):
        ...
    ```

- [ ] **Test error handling**
  - [ ] Apri 02_Clienti.py
  - [ ] Rimuovi una colonna dal DB (simula DB corruption)
  - [ ] Deve mostrare errore amichevole (non crash)
  - [ ] Deve logare dettagli in logs/fitmanager.log

- [ ] **Verificare logs**
  ```bash
  tail -f logs/fitmanager.log
  # Deve contenere messaggi di info/warning/error
  ```

- [ ] **Git Commit**
  ```bash
  git add core/error_handler.py server/pages/02_Clienti.py core/crm_db.py
  git commit -m "feat: Implement centralized error handling with logging"
  git push
  ```

**Verifica**: No crash su errori, logs generati correttamente

---

### GIOVEDÌ - Deprecare Moduli Legacy (1h)

- [ ] **Rinominare file**
  ```bash
  cd server/pages/
  
  mv 03_Esperto_Tecnico.py _DEPRECATED_03_Esperto_Tecnico.py.bak
  mv 06_Document_Explorer.py _DEPRECATED_06_Document_Explorer.py.bak
  mv 07_Meteo_Cantiere.py _DEPRECATED_07_Meteo_Cantiere.py.bak
  mv 08_Bollettino_Mare.py _DEPRECATED_08_Bollettino_Mare.py.bak
  ```

- [ ] **Aggiornare server/app.py**
  - [ ] Rimuovere i page_link() per pagine deprecated
  - [ ] Verificare che solo Agenda + Clienti restino

- [ ] **Aggiornare .gitignore**
  ```bash
  echo "_DEPRECATED_*.py.bak" >> .gitignore
  ```

- [ ] **Git Commit**
  ```bash
  git add server/pages/ server/app.py .gitignore
  git commit -m "chore: Deprecate legacy modules (03_Esperto, 06_Document, etc)"
  git push
  ```

**Verifica**: `ls server/pages/` mostra solo file attivi

---

### VENERDÌ - Testing & Validation (4h)

- [ ] **Creare tests/conftest.py**
  ```python
  import pytest
  from core.crm_db import CrmDBManager
  import tempfile
  
  @pytest.fixture
  def temp_db():
      with tempfile.NamedTemporaryFile() as f:
          db = CrmDBManager(f.name)
          yield db
  
  @pytest.fixture
  def sample_cliente():
      return {
          "nome": "Mario",
          "cognome": "Rossi",
          "telefono": "+39-333-123456",
          "email": "mario@example.com"
      }
  
  @pytest.fixture
  def sample_misurazione():
      return {
          "id_cliente": 1,
          "peso": 75.5,
          "massa_grassa": 15.0,
          "massa_magra": 60.5
      }
  ```

- [ ] **Creare tests/test_models.py**
  ```python
  import pytest
  from core.models import MisurazioneDTO, ClienteCreate
  
  def test_misurazione_valid():
      m = MisurazioneDTO(
          id_cliente=1,
          peso=75,
          massa_grassa=15,
          massa_magra=60
      )
      assert m.peso == 75
  
  def test_misurazione_invalid_peso():
      with pytest.raises(ValueError):
          MisurazioneDTO(
              id_cliente=1,
              peso=500,  # Too high!
              massa_grassa=15,
              massa_magra=60
          )
  
  def test_misurazione_invalid_grasso():
      with pytest.raises(ValueError):
          MisurazioneDTO(
              id_cliente=1,
              peso=75,
              massa_grassa=70,  # > 60, invalid
              massa_magra=60
          )
  
  def test_cliente_valid():
      c = ClienteCreate(
          nome="Mario",
          cognome="Rossi",
          email="mario@example.com"
      )
      assert c.nome == "Mario"
  ```

- [ ] **Eseguire test**
  ```bash
  pytest tests/ -v
  pytest tests/ --cov=core --cov-report=html
  # Aprire htmlcov/index.html nel browser
  ```

- [ ] **Aggiungere GitHub Actions CI/CD** (opzionale)
  ```yaml
  # .github/workflows/test.yml
  name: Test
  
  on: [push, pull_request]
  
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=core
  ```

- [ ] **Git Commit**
  ```bash
  git add tests/ .github/
  git commit -m "test: Add initial test suite (15% coverage)"
  git push
  ```

**Verifica**: 
- [ ] `pytest tests/ -v` passa con ≥5 test
- [ ] Coverage ≥ 15%
- [ ] Nessun import error

---

## 🧪 TEST CHECKLIST FINALE

Prima di considerare la settimana completa:

```bash
# 1. Lanciare app in dev
streamlit run server/app.py &

# 2. Aprire 02_Clienti.py
# - [ ] Selezionare cliente
# - [ ] Aprire dialog "Primo Check-up"
# - [ ] Inserire peso=75, grasso=15, muscolo=60
# - [ ] Cliccare "Salva Check-up"
# - [ ] Deve mostrare ✅ "Salvato!"
# - [ ] Deve logare in logs/fitmanager.log
# - [ ] Must NOT crash

# 3. Testare validazione
# - [ ] Inserire peso=500 (invalido)
# - [ ] Deve mostrare ❌ "Errore di validazione"
# - [ ] Deve mostrare quale campo è invalido
# - [ ] Must NOT crash

# 4. Verificare log file
tail logs/fitmanager.log
# Deve contenere:
# - INFO: Misurazione salvata per cliente X
# - WARNING: Validation error: Peso deve essere tra 20 e 300
```

---

## 📊 PROGRESS TRACKER

Usa questa tabella per trackare giornalmente:

| Giorno | Task | Status | Note |
|--------|------|--------|------|
| Lun | Identità progetto | 🟢 Done | All files updated |
| Mar | Models integration | 🟢 Done | 02_Clienti tested |
| Mer | Error handler | 🟡 In Progress | Fixing issues |
| Gio | Deprecate legacy | 🟢 Done | 4 files renamed |
| Ven | Testing | 🔴 Not Started | Target: 15% coverage |

---

## 🎯 SUCCESS METRICS

Alla fine della settimana, devi avere:

```
✅ MUST HAVE
  [ ] Identità progetto unificata in 3+ file
  [ ] models.py funzionante e integrato
  [ ] error_handler.py in uso in 2+ moduli
  [ ] Zero crash in 02_Clienti.py (dopo fix)
  [ ] Logs generati in logs/fitmanager.log
  [ ] Moduli legacy deprecati (_DEPRECATED_ prefix)

🟢 SHOULD HAVE
  [ ] 15%+ test coverage (pytest)
  [ ] README aggiornato e sensato
  [ ] .gitignore include _DEPRECATED_*

🟡 NICE TO HAVE
  [ ] GitHub Actions CI/CD running
  [ ] Type hints check with mypy
  [ ] Code formatted with black
```

---

## 💡 TIPS & TRICKS

### Se Streamlit Non Si Aggiorna
```bash
# Pulire cache
rm -rf ~/.streamlit/cache
streamlit cache clear

# Riavviare con --logger.level=debug
streamlit run server/app.py --logger.level=debug
```

### Se Test Falliscono
```bash
# Eseguire con verbose output
pytest tests/test_models.py -vv -s

# Eseguire singolo test
pytest tests/test_models.py::test_misurazione_valid -vv

# Vedere traceback completo
pytest tests/ --tb=long
```

### Se Database È Corrotto
```bash
# Backup e ricrea
mv data/crm.db data/crm.db.bak
python -c "from core.crm_db import CrmDBManager; CrmDBManager()"
# Database ricreato vuoto - popola con dati test
```

### Debug Print (Temporary)
```python
# In Streamlit
st.write(f"DEBUG: {variable}")
st.json({"key": value})

# In Core logic
import json
print(json.dumps(data, indent=2, default=str))
```

---

## 🆘 TROUBLESHOOTING

### Problema: "ModuleNotFoundError: No module named 'pydantic'"
```bash
pip install pydantic==2.7.0
python -c "import pydantic; print(pydantic.__version__)"
```

### Problema: "ImportError: cannot import name 'MisurazioneDTO' from 'core.models'"
```bash
# Verificare file core/models.py esiste
ls -la core/models.py

# Verificare import nel file
head core/models.py | grep "class MisurazioneDTO"

# Ricaricare moduli
python -c "from core.models import MisurazioneDTO; print('OK')"
```

### Problema: "AttributeError: 'dict' object has no attribute 'model_dump'"
```python
# ❌ Sbagliato
dati = {"peso": 75}  # Dict normale
db.add(dati.model_dump())  # Non ha method model_dump()

# ✅ Corretto
dati = {"peso": 75}
misurazione = MisurazioneDTO(**dati)  # Convertire a Pydantic model
db.add(misurazione.model_dump())  # Convertire back a dict
```

### Problema: Test lento
```bash
# Usare -x per fermarsi al primo fail
pytest tests/ -x

# Usare -k per filtrare
pytest tests/ -k "misurazione"

# Profiling
pytest tests/ --durations=10
```

---

## 📞 FINAL CHECKLIST

Prima di dire "Week 1 completa":

- [ ] Tutte le task lasciate sono COMPLETATE (non partly done)
- [ ] Tutti i commit sono pushati a remote
- [ ] `git log --oneline` mostra 5-6 commit della settimana
- [ ] Nessun file uncommitted (`git status` clean)
- [ ] Code review personale (leggi il tuo codice nuovo)
- [ ] Nessun hardcoded path o secrets nei file
- [ ] Testo in README è grammaticalmente corretto
- [ ] Link nei documenti funzionano
- [ ] Nessun `print()` debug rimasto nel codice
- [ ] Nessun `TODO` o `FIXME` non intenzionale
- [ ] Backup del database fatto

---

**Tempo Totale Estimato**: 12-16 ore lavoro
**Difficoltà**: Media (non richiede knowledge avanzato)
**Deadline Soft**: Venerdì 17 Gennaio EOD

Buona implementazione! 🚀

