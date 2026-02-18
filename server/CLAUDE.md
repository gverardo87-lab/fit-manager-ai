# Server - UI Layer (Streamlit)

Questa cartella contiene SOLO la presentazione. Nessuna logica di business qui.

## Regole

- Importare solo da core/repositories/, mai da sqlite3 direttamente
- Tutte le pagine sono migrate al Repository Pattern
- Usare st.form() per input raggruppati
- Validare con Pydantic PRIMA di chiamare il repository
- Gestire il caso in cui il repository ritorna None (fallback di @safe_operation)

## Struttura pagina standard

```python
import streamlit as st
from core.repositories import ClientRepository  # dal repository, mai dal DB

repo = ClientRepository()

st.set_page_config(page_title="...", page_icon="...", layout="wide")
st.title("Titolo")

# Sidebar per filtri
# Contenuto principale in colonne
# Form con validazione Pydantic on submit
```

## UI

- Testo in italiano
- Layout: wide
- Color scheme: blue (#0066cc) primary, green (#00a86b) success, orange (#ff6b35) warning, red (#e74c3c) error
