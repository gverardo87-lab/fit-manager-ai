# core/constants.py
"""
Costanti e Enumerazioni centralizzate per FitManager AI Studio.
Ogni stringa ripetuta in piu' di un file DEVE essere definita qui come Enum.
Usare sempre EnumMember.value quando si passa a SQL o si confronta con dati DB.
"""

from enum import Enum


# ════════════════════════════════════════════════════════════
# STATI EVENTO (agenda.stato)
# ════════════════════════════════════════════════════════════

class EventStatus(str, Enum):
    """Stati possibili per un evento in agenda."""
    PROGRAMMATO = "Programmato"
    COMPLETATO = "Completato"
    CANCELLATO = "Cancellato"
    RINVIATO = "Rinviato"


# ════════════════════════════════════════════════════════════
# STATI RATA (rate_programmate.stato)
# ════════════════════════════════════════════════════════════

class RateStatus(str, Enum):
    """Stati possibili per una rata di pagamento."""
    PENDENTE = "PENDENTE"
    PARZIALE = "PARZIALE"
    SALDATA = "SALDATA"


# ════════════════════════════════════════════════════════════
# TIPO MOVIMENTO CASSA (movimenti_cassa.tipo)
# ════════════════════════════════════════════════════════════

class MovementType(str, Enum):
    """Tipi di movimento cassa."""
    ENTRATA = "ENTRATA"
    USCITA = "USCITA"


# ════════════════════════════════════════════════════════════
# METODO PAGAMENTO (movimenti_cassa.metodo)
# ════════════════════════════════════════════════════════════

class PaymentMethod(str, Enum):
    """Metodi di pagamento accettati."""
    CONTANTI = "CONTANTI"
    POS = "POS"
    BONIFICO = "BONIFICO"
    ASSEGNO = "ASSEGNO"
    ALTRO = "ALTRO"


# ════════════════════════════════════════════════════════════
# CATEGORIA SESSIONE (agenda.categoria)
# ════════════════════════════════════════════════════════════

class SessionCategory(str, Enum):
    """Categorie di sessione/evento — allineate a api/routers/agenda.py VALID_CATEGORIES."""
    PT = "PT"
    SALA = "SALA"
    CORSO = "CORSO"
    COLLOQUIO = "COLLOQUIO"


# ════════════════════════════════════════════════════════════
# FREQUENZA SPESE RICORRENTI (spese_ricorrenti.frequenza)
# ════════════════════════════════════════════════════════════

class ExpenseFrequency(str, Enum):
    """Frequenze per spese ricorrenti — allineate a frontend EXPENSE_FREQUENCIES."""
    MENSILE = "MENSILE"
    SETTIMANALE = "SETTIMANALE"
    TRIMESTRALE = "TRIMESTRALE"
    SEMESTRALE = "SEMESTRALE"
    ANNUALE = "ANNUALE"
