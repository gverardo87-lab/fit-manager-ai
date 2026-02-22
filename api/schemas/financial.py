# api/schemas/financial.py
"""
Pydantic schemas per il dominio finanziario (Contratti + Rate + Movimenti + Dashboard).

SICUREZZA - Mass Assignment Prevention:
- ContractCreate: NO trainer_id (injected da JWT nel router)
- RateCreate: NO trainer_id, NO id_cliente (derivano dal contratto)
- RatePayment: NO id_contratto, NO id_cliente (derivano dalla rata target)
- MovementManualCreate: NO id_contratto, NO id_rata, NO id_cliente (Ledger Integrity)

Deep Relational IDOR chain:
  Rate -> Contract.trainer_id (verifica diretta)
  Contract -> Client.trainer_id (verifica coerenza Relational IDOR)
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


# ════════════════════════════════════════════════════════════
# COSTANTI VALIDE (allineate a core/constants.py)
# ════════════════════════════════════════════════════════════

VALID_PAYMENT_METHODS = {"CONTANTI", "POS", "BONIFICO", "ASSEGNO", "ALTRO"}
VALID_RATE_STATUSES = {"PENDENTE", "PARZIALE", "SALDATA"}
VALID_PAYMENT_STATUSES = {"PENDENTE", "PARZIALE", "SALDATO"}


# ════════════════════════════════════════════════════════════
# CONTRACT SCHEMAS
# ════════════════════════════════════════════════════════════

class ContractCreate(BaseModel):
    """
    Schema per creazione contratto.

    BLINDATO: nessun trainer_id — iniettato dal JWT nel router.
    id_cliente: verificato via Relational IDOR (deve appartenere al trainer).
    """
    model_config = {"extra": "forbid"}

    id_cliente: int = Field(gt=0)
    tipo_pacchetto: str = Field(min_length=1, max_length=100)
    crediti_totali: int = Field(ge=1, le=1000)
    prezzo_totale: float = Field(ge=0, le=1_000_000)
    data_inizio: date
    data_scadenza: date
    acconto: float = Field(default=0, ge=0, le=1_000_000)
    metodo_acconto: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_dates_and_acconto(self):
        """Validazione cross-field: date coerenti + acconto <= prezzo."""
        if self.data_scadenza <= self.data_inizio:
            raise ValueError("data_scadenza deve essere dopo data_inizio")
        if self.acconto > self.prezzo_totale:
            raise ValueError("acconto non puo' essere maggiore del prezzo_totale")
        if self.acconto > 0 and not self.metodo_acconto:
            raise ValueError("metodo_acconto obbligatorio se acconto > 0")
        if self.metodo_acconto and self.metodo_acconto not in VALID_PAYMENT_METHODS:
            raise ValueError(f"metodo_acconto invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return self


class ContractUpdate(BaseModel):
    """
    Schema per aggiornamento contratto (partial update).

    BLINDATO:
    - NO trainer_id (non trasferibile)
    - NO id_cliente (non trasferibile)
    - NO crediti_usati, totale_versato (calcolati automaticamente)
    - NO chiuso (gestito da logica di business separata)
    """
    model_config = {"extra": "forbid"}

    tipo_pacchetto: Optional[str] = Field(None, min_length=1, max_length=100)
    crediti_totali: Optional[int] = Field(None, ge=1, le=1000)
    prezzo_totale: Optional[float] = Field(None, ge=0, le=1_000_000)
    data_inizio: Optional[date] = None
    data_scadenza: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)


class ContractResponse(BaseModel):
    """Response model per contratto con rate."""
    id: int
    id_cliente: int
    tipo_pacchetto: Optional[str] = None
    data_vendita: Optional[date] = None
    data_inizio: Optional[date] = None
    data_scadenza: Optional[date] = None
    crediti_totali: Optional[int] = None
    crediti_usati: int = 0
    prezzo_totale: Optional[float] = None
    acconto: float = 0
    totale_versato: float = 0
    stato_pagamento: str = "PENDENTE"
    note: Optional[str] = None
    chiuso: bool = False

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# RATE SCHEMAS
# ════════════════════════════════════════════════════════════

class RateCreate(BaseModel):
    """
    Schema per creazione singola rata manuale.

    BLINDATO:
    - NO trainer_id (derivato dal contratto)
    - NO id_cliente (derivato dal contratto)
    - id_contratto: verificato via Bouncer (contratto deve appartenere al trainer)
    """
    model_config = {"extra": "forbid"}

    id_contratto: int = Field(gt=0)
    data_scadenza: date
    importo_previsto: float = Field(gt=0, le=1_000_000)
    descrizione: Optional[str] = Field(None, max_length=200)


class RateUpdate(BaseModel):
    """
    Schema per aggiornamento rata (partial update, solo rate PENDENTI).

    BLINDATO:
    - NO id_contratto (non trasferibile)
    - NO stato (gestito solo via pagamento)
    - NO importo_saldato (gestito solo via pagamento)
    """
    model_config = {"extra": "forbid"}

    data_scadenza: Optional[date] = None
    importo_previsto: Optional[float] = Field(None, gt=0, le=1_000_000)
    descrizione: Optional[str] = Field(None, max_length=200)


class RatePayment(BaseModel):
    """
    Schema per pagamento rata — Unit of Work.

    Operazione atomica:
    1. Aggiorna rate_programmate.importo_saldato += importo
    2. Aggiorna rate_programmate.stato (PARZIALE | SALDATA)
    3. Aggiorna contratti.totale_versato += importo
    4. Crea movimento_cassa ENTRATA

    BLINDATO:
    - NO id_contratto, NO id_cliente (derivano dalla rata target)
    - importo: strettamente positivo
    """
    model_config = {"extra": "forbid"}

    importo: float = Field(gt=0, le=1_000_000)
    metodo: str = Field(default="CONTANTI")
    data_pagamento: date = Field(default_factory=date.today)
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("metodo")
    @classmethod
    def validate_metodo(cls, v: str) -> str:
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Metodo invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return v


class RateResponse(BaseModel):
    """
    Response model per singola rata.

    Campi ricevuta (opzionali, popolati solo per rate SALDATE):
    - data_pagamento: data effettiva del pagamento (da CashMovement)
    - metodo_pagamento: metodo usato (CONTANTI, POS, etc.)

    Campi computati (calcolati nel router, mai dal frontend):
    - importo_residuo: quanto manca per saldare questa rata
    - is_scaduta: true se non saldata e oltre la data_scadenza
    - giorni_ritardo: giorni di ritardo (0 se non scaduta)
    """
    id: int
    id_contratto: int
    data_scadenza: date
    importo_previsto: float
    descrizione: Optional[str] = None
    stato: str = "PENDENTE"
    importo_saldato: float = 0
    data_pagamento: Optional[date] = None
    metodo_pagamento: Optional[str] = None

    # ── Computed (calcolati nel router) ──
    importo_residuo: float = 0
    is_scaduta: bool = False
    giorni_ritardo: int = 0

    model_config = {"from_attributes": True}


class ContractListResponse(ContractResponse):
    """
    Response arricchita per la lista contratti con KPI aggregati.

    Campi extra (calcolati nel router via batch fetch):
    - client_nome/cognome: nome del cliente (evita JOIN lato frontend)
    - rate_totali/rate_pagate: conteggi per progress badge
    - ha_rate_scadute: true se almeno una rata PENDENTE/PARZIALE e' oltre scadenza
    """
    client_nome: str = ""
    client_cognome: str = ""
    rate_totali: int = 0
    rate_pagate: int = 0
    ha_rate_scadute: bool = False


class ContractWithRatesResponse(ContractResponse):
    """
    Response model per contratto con lista rate embedded.

    KPI computati (calcolati in _to_response_with_rates, unica fonte di verita'):
    - Il frontend NON calcola nessun valore finanziario, li legge da qui.
    - Formula chiave: importo_da_rateizzare = prezzo - acconto - somma_saldate
    """
    rate: List[RateResponse] = []

    # ── KPI Computed (calcolati nel router) ──
    residuo: float = 0                  # prezzo_totale - totale_versato
    percentuale_versata: int = 0        # round((totale_versato / prezzo_totale) * 100)
    importo_da_rateizzare: float = 0    # prezzo - acconto - somma(SALDATA)
    somma_rate_previste: float = 0      # sum(ALL importo_previsto)
    somma_rate_saldate: float = 0       # sum(SALDATA importo_previsto)
    somma_rate_pendenti: float = 0      # sum(non-SALDATA importo_previsto)
    piano_allineato: bool = True        # abs(importo_da_rateizzare - somma_rate_pendenti) < 0.01
    importo_disallineamento: float = 0  # importo_da_rateizzare - somma_rate_pendenti
    rate_totali: int = 0
    rate_pagate: int = 0
    rate_scadute: int = 0

    # ── Credit breakdown (computed on read da eventi PT) ──
    sedute_programmate: int = 0   # stato=Programmato
    sedute_completate: int = 0    # stato=Completato
    sedute_rinviate: int = 0      # stato=Rinviato
    crediti_residui: int = 0      # crediti_totali - programmate - completate


# ════════════════════════════════════════════════════════════
# PAYMENT PLAN GENERATION SCHEMA
# ════════════════════════════════════════════════════════════

class PaymentPlanCreate(BaseModel):
    """
    Schema per generazione piano rate automatico.

    Elimina rate PENDENTI esistenti e ne crea di nuove.
    Rate gia' SALDATE vengono mantenute.
    """
    model_config = {"extra": "forbid"}

    importo_da_rateizzare: float = Field(gt=0, le=1_000_000)
    numero_rate: int = Field(ge=1, le=60)
    data_prima_rata: date
    frequenza: str = Field(default="MENSILE")

    @field_validator("frequenza")
    @classmethod
    def validate_frequenza(cls, v: str) -> str:
        valid = {"MENSILE", "SETTIMANALE", "TRIMESTRALE"}
        if v not in valid:
            raise ValueError(f"Frequenza invalida. Valide: {sorted(valid)}")
        return v


# ════════════════════════════════════════════════════════════
# MOVEMENT SCHEMAS (Ledger)
# ════════════════════════════════════════════════════════════

VALID_MOVEMENT_TYPES = {"ENTRATA", "USCITA"}


class MovementManualCreate(BaseModel):
    """
    Schema per creazione movimento manuale (spese, incassi extra).

    BLINDATO (Ledger Integrity):
    - NO id_contratto (solo movimenti di sistema — pagamenti rata, acconti)
    - NO id_rata (solo movimenti di sistema)
    - NO id_cliente (solo movimenti di sistema)
    - NO trainer_id (injected da JWT nel router)

    L'utente puo' creare solo movimenti "liberi" (affitto, attrezzatura, ecc.).
    I movimenti legati a contratti/rate vengono creati SOLO dal sistema
    tramite pay_rate e create_contract.
    """
    model_config = {"extra": "forbid"}

    importo: float = Field(gt=0, le=1_000_000)
    tipo: str
    categoria: Optional[str] = Field(None, max_length=100)
    metodo: Optional[str] = None
    data_effettiva: date
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        if v not in VALID_MOVEMENT_TYPES:
            raise ValueError(f"Tipo invalido. Validi: {sorted(VALID_MOVEMENT_TYPES)}")
        return v

    @field_validator("categoria", mode="before")
    @classmethod
    def sanitize_categoria(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v if v else None

    @field_validator("metodo")
    @classmethod
    def validate_metodo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Metodo invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return v


class MovementResponse(BaseModel):
    """Response model per movimento cassa."""
    id: int
    data_movimento: Optional[datetime] = None
    data_effettiva: date
    tipo: str
    categoria: Optional[str] = None
    importo: float
    metodo: Optional[str] = None
    id_cliente: Optional[int] = None
    id_contratto: Optional[int] = None
    id_rata: Optional[int] = None
    id_spesa_ricorrente: Optional[int] = None
    note: Optional[str] = None
    operatore: str = "API"

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# DASHBOARD SCHEMA
# ════════════════════════════════════════════════════════════

class DashboardSummary(BaseModel):
    """
    KPI aggregati per la dashboard.

    Tutti calcolati con query SQL aggregate (func.count, func.sum)
    per latenza zero — nessun record caricato in Python.
    """
    active_clients: int = 0
    monthly_revenue: float = 0.0
    pending_rates: int = 0
    todays_appointments: int = 0
    ledger_alerts: int = 0


# ════════════════════════════════════════════════════════════
# RICONCILIAZIONE CONTRATTI vs LEDGER
# ════════════════════════════════════════════════════════════

class ReconciliationItem(BaseModel):
    """Singolo contratto con divergenza tra totale_versato e libro mastro."""
    contract_id: int
    client_name: str
    totale_versato: float
    ledger_total: float
    delta: float


class ReconciliationResponse(BaseModel):
    """Risultato audit riconciliazione: contratti allineati vs divergenti."""
    total_contracts: int
    aligned: int
    divergent: int
    items: List[ReconciliationItem] = []
