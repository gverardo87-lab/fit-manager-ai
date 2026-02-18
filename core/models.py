# core/models.py (Validation Layer con Pydantic)
"""
Data models con validazione automatica per FitManager AI.
Garantisce che TUTTI i dati in input siano corretti prima di andare nel DB.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import date, datetime, timedelta
from typing import Optional, List, Any
import json
import re

# ============================================================================
# CLIENTE MODELS
# ============================================================================

class ClienteBase(BaseModel):
    """Base model per Cliente (senza ID)"""
    nome: str = Field(min_length=1, max_length=100)
    cognome: str = Field(min_length=1, max_length=100)
    telefono: Optional[str] = None  # Pattern validation moved to validator for backward compatibility
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = Field(None, pattern="^(Uomo|Donna|Altro)$")
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Convert empty string to None for backward compatibility with old data"""
        if v is None or v == '':
            return None
        # Validate pattern only if value is provided
        if not re.match(r"^[+]?[0-9\s\-()]{6,20}$", v):
            raise ValueError('Telefono non valido')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Convert empty string to None for backward compatibility with old data"""
        if v is None or v == '':
            return None
        if '@' not in v or '.' not in v:
            raise ValueError('Email non valida')
        return v.lower()
    
    @field_validator('data_nascita')
    @classmethod
    def validate_data_nascita(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        if v > date.today():
            raise ValueError('Data di nascita non può essere nel futuro')
        return v

class ClienteCreate(ClienteBase):
    """Model per creazione cliente"""
    anamnesi: Optional[dict] = Field(default_factory=dict)

class ClienteUpdate(BaseModel):
    """Model per update cliente (tutti i campi optional)"""
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = None
    anamnesi: Optional[dict] = None

class CreditSummary(BaseModel):
    """Summary crediti aggregati su tutti i contratti attivi di un cliente.

    Formula:
        crediti_disponibili = crediti_totali - crediti_completati - crediti_prenotati

    crediti_prenotati = sessioni in stato 'Programmato' (prenotate, non ancora eseguite)
    crediti_completati = sessioni confermate (crediti_usati nei contratti)
    """
    crediti_totali: int = 0
    crediti_completati: int = 0
    crediti_prenotati: int = 0
    crediti_disponibili: int = 0
    contratti_attivi: int = 0


class Cliente(ClienteBase):
    """Model completo Cliente (con ID)"""
    id: int
    data_creazione: datetime
    stato: str = "Attivo"
    lezioni_residue: int = 0  # backward compat: = crediti_disponibili
    crediti: Optional[CreditSummary] = None
    anamnesi_json: Optional[str] = None

    class Config:
        from_attributes = True

# ============================================================================
# MISURAZIONE MODELS
# ============================================================================

class MisurazioneBase(BaseModel):
    """Base model per Misurazione"""
    id_cliente: int = Field(gt=0)
    data_misurazione: date = Field(default_factory=date.today)
    peso: float = Field(ge=20, le=300, description="Peso in kg")
    massa_grassa: float = Field(ge=0, le=60, description="Percentuale grasso corporeo")
    massa_magra: Optional[float] = Field(None, ge=0, le=200, description="Massa magra in kg")
    acqua: Optional[float] = Field(0, ge=0, le=100)
    
    # Circonferenze
    collo: Optional[float] = Field(None, ge=0, le=100)
    spalle: Optional[float] = Field(None, ge=0, le=200)
    torace: Optional[float] = Field(None, ge=0, le=200)
    braccio: Optional[float] = Field(None, ge=0, le=100)
    vita: Optional[float] = Field(None, ge=0, le=200)
    fianchi: Optional[float] = Field(None, ge=0, le=200)
    coscia: Optional[float] = Field(None, ge=0, le=100)
    polpaccio: Optional[float] = Field(None, ge=0, le=100)
    
    note: Optional[str] = Field(None, max_length=500)
    
    @field_validator('data_misurazione')
    @classmethod
    def validate_data_misurazione(cls, v: date) -> date:
        if v > date.today():
            raise ValueError('Data misurazione non può essere nel futuro')
        return v
    
    @field_validator('massa_magra')
    @classmethod
    def validate_massa_magra(cls, v: Optional[float], info) -> Optional[float]:
        """Valida che massa magra + massa grassa <= peso"""
        if v is None:
            return v
        data = info.data
        if 'peso' in data and 'massa_grassa' in data:
            total = v + data['massa_grassa']
            if total > data['peso'] + 5:  # Tolleranza 5kg
                raise ValueError(f'Massa magra ({v}) + grassa ({data["massa_grassa"]}) > peso ({data["peso"]})')
        return v

class MisurazioneCreate(MisurazioneBase):
    """Model per creazione misurazione"""
    pass

class Misurazione(MisurazioneBase):
    """Model completo Misurazione (con ID e metadata)"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# CONTRATTO MODELS
# ============================================================================

class RataProgrammata(BaseModel):
    """Model per singola rata di un contratto"""
    id: Optional[int] = None
    id_contratto: int
    data_scadenza: date
    importo_previsto: float = Field(gt=0)
    descrizione: Optional[str] = None
    stato: str = Field(default="PENDENTE", pattern="^(PENDENTE|SALDATA)$")
    importo_saldato: float = Field(default=0, ge=0)

class ContratoBase(BaseModel):
    """Base model per Contratto"""
    id_cliente: int = Field(gt=0)
    tipo_pacchetto: str = Field(
        min_length=1, 
        max_length=100,
        description="Es: '10 PT', '20 PT', 'Mensile', 'Trimestrale', 'Annuale', 'Consulenza'"
    )
    crediti_totali: int = Field(ge=1, le=1000)
    prezzo_totale: float = Field(ge=0, description="Prezzo totale contratto in €")
    data_inizio: date
    data_scadenza: date
    acconto: float = Field(default=0, ge=0)
    metodo_acconto: Optional[str] = Field(None, pattern="^(CONTANTI|POS|BONIFICO)$")
    note: Optional[str] = Field(None, max_length=500)
    
    @field_validator('data_scadenza')
    @classmethod
    def validate_data_scadenza(cls, v: date, info) -> date:
        if 'data_inizio' in info.data:
            if v <= info.data['data_inizio']:
                raise ValueError('Data scadenza deve essere dopo data inizio')
        return v
    
    @field_validator('acconto')
    @classmethod
    def validate_acconto(cls, v: float, info) -> float:
        if 'prezzo_totale' in info.data:
            if v > info.data['prezzo_totale']:
                raise ValueError('Acconto non può essere > prezzo totale')
        return v

class ContratoCreate(ContratoBase):
    """Model per creazione contratto"""
    pass

class Contratto(ContratoBase):
    """Model completo Contratto"""
    id: int
    crediti_usati: int = 0
    totale_versato: float = 0
    stato_pagamento: str = "PENDENTE"
    chiuso: bool = False
    data_vendita: date = Field(default_factory=date.today)
    rate: Optional[List[RataProgrammata]] = None

    class Config:
        from_attributes = True

# ============================================================================
# FINANCIAL MODELS
# ============================================================================

class MovimentoCassaBase(BaseModel):
    """Base model per Movimento Cassa"""
    tipo: str = Field(pattern="^(ENTRATA|USCITA)$", description="ENTRATA = soldi in, USCITA = soldi out")
    categoria: str = Field(min_length=1, max_length=100)
    importo: float = Field(gt=0, le=1_000_000, description="Importo in €, sempre positivo")
    metodo: str = Field(default="CONTANTI", pattern="^(CONTANTI|POS|BONIFICO|ASSEGNO|ALTRO)$")
    data_effettiva: date = Field(default_factory=date.today)
    id_cliente: Optional[int] = Field(None, gt=0)
    id_spesa_ricorrente: Optional[int] = None
    note: Optional[str] = Field(None, max_length=500)

    @field_validator('data_effettiva')
    @classmethod
    def validate_data(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        if v > date.today() + timedelta(days=30):
            raise ValueError('Data non può essere più di 30 giorni nel futuro')
        return v

class MovimentoCassaCreate(MovimentoCassaBase):
    """Model per creazione movimento cassa"""
    pass

class MovimentoCassa(MovimentoCassaBase):
    """Model completo Movimento Cassa"""
    id: int
    data_movimento: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class SpesaRicorrenteBase(BaseModel):
    """Base model per Spesa Ricorrente"""
    nome: str = Field(min_length=1, max_length=100, description="Es: 'Affitto palestra'")
    categoria: str = Field(min_length=1, max_length=100)
    importo: float = Field(gt=0, le=100_000)
    frequenza: str = Field(pattern="^(MENSILE|TRIMESTRALE|ANNUALE)$")
    giorno_scadenza: int = Field(ge=1, le=31, description="Giorno del mese per scadenza")
    giorno_inizio: int = Field(default=1, ge=1, le=31)
    data_prossima_scadenza: Optional[date] = None
    attiva: bool = True

class SpesaRicorrenteCreate(SpesaRicorrenteBase):
    """Model per creazione spesa ricorrente"""
    pass

class SpesaRicorrente(SpesaRicorrenteBase):
    """Model completo Spesa Ricorrente"""
    id: int

    class Config:
        from_attributes = True

# ============================================================================
# AGENDA / SESSIONE MODELLI
# ============================================================================

class SessioneBase(BaseModel):
    """Base model per Sessione Allenamento"""
    id_cliente: Optional[int] = Field(None, gt=0)  # Optional per eventi generici (SALA, CONSULENZA, CORSO)
    data_inizio: datetime
    data_fine: datetime
    categoria: str  # Validato e normalizzato da field_validator
    titolo: str = Field(min_length=1, max_length=200)
    stato: str = Field(default="Programmato", pattern="^(Programmato|Completato|Cancellato|Rinviato)$")
    note: Optional[str] = Field(None, max_length=500)
    
    @field_validator('categoria')
    @classmethod
    def validate_categoria(cls, v: str) -> str:
        """Normalizza e valida categoria (case-insensitive)"""
        categorie_valide = ["PT", "SALA", "NUOTO", "YOGA", "CONSULENZA", "CORSO"]
        v_upper = v.upper()
        if v_upper not in categorie_valide:
            raise ValueError(f'Categoria deve essere una tra: {", ".join(categorie_valide)}')
        return v_upper
    
    @field_validator('data_fine')
    @classmethod
    def validate_data_fine(cls, v: datetime, info) -> datetime:
        if 'data_inizio' in info.data:
            if v <= info.data['data_inizio']:
                raise ValueError('Data fine deve essere dopo data inizio')
            duration = (v - info.data['data_inizio']).total_seconds() / 3600
            if duration > 4:
                raise ValueError('Sessione non può durare più di 4 ore')
        return v

class SessioneCreate(SessioneBase):
    """Model per creazione sessione"""
    pass

class Sessione(SessioneBase):
    """Model completo Sessione"""
    id: int
    data_creazione: datetime

    class Config:
        from_attributes = True

# ============================================================================
# WORKOUT TEMPLATE MODELS
# ============================================================================

class Esercizio(BaseModel):
    """Singolo esercizio in un workout"""
    nome: str = Field(min_length=1, max_length=100)
    serie: int = Field(ge=1, le=10)
    ripetizioni: str = Field(min_length=1, max_length=20, description="Es: '8-10' o '30s'")
    riposo_secondi: int = Field(ge=30, le=600)
    note: Optional[str] = Field(None, max_length=200)

class WorkoutTemplate(BaseModel):
    """Template di workout predefinito"""
    id: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=100)
    target_body_parts: List[str]
    durata_minuti: int = Field(ge=15, le=180)
    difficolta: str = Field(pattern="^(Principiante|Intermedio|Avanzato)$")
    esercizi: List[Esercizio] = Field(min_items=1, max_items=20)
    periodicita: str = Field(description="Es: '3x/settimana', 'daily', 'weekly'")
    descrizione: Optional[str] = None

# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: int

class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str
    data: Optional[dict] = None

class MessageResponse(BaseModel):
    """Simple message response"""
    message: str

# ============================================================================
# BULK OPERATIONS
# ============================================================================

class BulkCreateSessioniRequest(BaseModel):
    """Request per creazione bulk sessioni"""
    sessioni: List[SessioneCreate] = Field(min_items=1, max_items=100)
    skip_on_conflict: bool = False

class BulkUpdateClientiRequest(BaseModel):
    """Request per update bulk clienti"""
    updates: List[dict] = Field(min_items=1, max_items=50)

# ============================================================================
# CONFIG MODELS
# ============================================================================

class AppConfig(BaseModel):
    """Configuration settings globali"""
    app_name: str = "FitManager AI"
    app_version: str = "3.0.0"
    max_file_size_mb: int = 50
    session_timeout_hours: int = 8
    dark_mode_enabled: bool = False
    sentry_dsn: Optional[str] = None
    
    class Config:
        frozen = True  # Immutable config

# ============================================================================
# ASSESSMENT MODELS
# ============================================================================

class AssessmentInitialCreate(BaseModel):
    """Model per creazione assessment iniziale"""
    id_cliente: int = Field(gt=0)
    data_assessment: date = Field(default_factory=date.today)

    # Antropometria
    altezza_cm: Optional[float] = Field(None, ge=100, le=250)
    peso_kg: Optional[float] = Field(None, ge=20, le=300)
    massa_grassa_pct: Optional[float] = Field(None, ge=0, le=60)

    # Circonferenze
    circonferenza_petto_cm: Optional[float] = Field(None, ge=0, le=200)
    circonferenza_vita_cm: Optional[float] = Field(None, ge=0, le=200)
    circonferenza_bicipite_sx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_bicipite_dx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_fianchi_cm: Optional[float] = Field(None, ge=0, le=200)
    circonferenza_quadricipite_sx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_quadricipite_dx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_coscia_sx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_coscia_dx_cm: Optional[float] = Field(None, ge=0, le=100)

    # Test forza
    pushups_reps: Optional[int] = Field(None, ge=0)
    pushups_note: Optional[str] = None
    panca_peso_kg: Optional[float] = Field(None, ge=0)
    panca_reps: Optional[int] = Field(None, ge=0)
    panca_note: Optional[str] = None
    rematore_peso_kg: Optional[float] = Field(None, ge=0)
    rematore_reps: Optional[int] = Field(None, ge=0)
    rematore_note: Optional[str] = None
    lat_machine_peso_kg: Optional[float] = Field(None, ge=0)
    lat_machine_reps: Optional[int] = Field(None, ge=0)
    lat_machine_note: Optional[str] = None
    squat_bastone_note: Optional[str] = None
    squat_macchina_peso_kg: Optional[float] = Field(None, ge=0)
    squat_macchina_reps: Optional[int] = Field(None, ge=0)
    squat_macchina_note: Optional[str] = None

    # Mobilita
    mobilita_spalle_note: Optional[str] = None
    mobilita_gomiti_note: Optional[str] = None
    mobilita_polsi_note: Optional[str] = None
    mobilita_anche_note: Optional[str] = None
    mobilita_schiena_note: Optional[str] = None

    # Anamnesi
    infortuni_pregessi: Optional[str] = None
    infortuni_attuali: Optional[str] = None
    limitazioni: Optional[str] = None
    storia_medica: Optional[str] = None

    # Obiettivi
    goals_quantificabili: Optional[str] = None
    goals_benessere: Optional[str] = None

    # Foto
    foto_fronte_path: Optional[str] = None
    foto_lato_path: Optional[str] = None
    foto_dietro_path: Optional[str] = None

    # Note
    note_colloquio: Optional[str] = None

class AssessmentInitial(AssessmentInitialCreate):
    """Model completo Assessment Iniziale (con ID)"""
    id: int
    data_creazione: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssessmentFollowupCreate(BaseModel):
    """Model per creazione assessment di follow-up"""
    id_cliente: int = Field(gt=0)
    data_followup: date = Field(default_factory=date.today)

    # Antropometria
    peso_kg: Optional[float] = Field(None, ge=20, le=300)
    massa_grassa_pct: Optional[float] = Field(None, ge=0, le=60)

    # Circonferenze
    circonferenza_petto_cm: Optional[float] = Field(None, ge=0, le=200)
    circonferenza_vita_cm: Optional[float] = Field(None, ge=0, le=200)
    circonferenza_bicipite_sx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_bicipite_dx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_fianchi_cm: Optional[float] = Field(None, ge=0, le=200)
    circonferenza_quadricipite_sx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_quadricipite_dx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_coscia_sx_cm: Optional[float] = Field(None, ge=0, le=100)
    circonferenza_coscia_dx_cm: Optional[float] = Field(None, ge=0, le=100)

    # Test forza
    pushups_reps: Optional[int] = Field(None, ge=0)
    panca_peso_kg: Optional[float] = Field(None, ge=0)
    panca_reps: Optional[int] = Field(None, ge=0)
    rematore_peso_kg: Optional[float] = Field(None, ge=0)
    rematore_reps: Optional[int] = Field(None, ge=0)
    squat_peso_kg: Optional[float] = Field(None, ge=0)
    squat_reps: Optional[int] = Field(None, ge=0)

    # Progress e note
    goals_progress: Optional[str] = None
    foto_fronte_path: Optional[str] = None
    foto_lato_path: Optional[str] = None
    foto_dietro_path: Optional[str] = None
    note_followup: Optional[str] = None

class AssessmentFollowup(AssessmentFollowupCreate):
    """Model completo Assessment Follow-up (con ID)"""
    id: int
    data_creazione: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# WORKOUT PLAN MODELS
# ============================================================================

class WorkoutPlanCreate(BaseModel):
    """Model per creazione piano di allenamento"""
    id_cliente: int = Field(gt=0)
    data_inizio: date
    goal: Optional[str] = None
    level: Optional[str] = None
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    sessions_per_week: Optional[int] = Field(None, ge=1, le=7)
    methodology: Optional[str] = None
    weekly_schedule: Optional[Any] = None  # List/dict, serializzato come JSON nel DB
    exercises_details: Optional[str] = None
    progressive_overload_strategy: Optional[str] = None
    recovery_recommendations: Optional[str] = None
    sources: Optional[Any] = None  # List, serializzato come JSON nel DB
    note: Optional[str] = None

class WorkoutPlan(BaseModel):
    """Model completo Piano Allenamento (con ID)"""
    id: int
    id_cliente: int
    data_creazione: Optional[datetime] = None
    data_inizio: date
    goal: Optional[str] = None
    level: Optional[str] = None
    duration_weeks: Optional[int] = None
    sessions_per_week: Optional[int] = None
    methodology: Optional[str] = None
    weekly_schedule: Optional[Any] = None
    exercises_details: Optional[str] = None
    progressive_overload_strategy: Optional[str] = None
    recovery_recommendations: Optional[str] = None
    sources: Optional[Any] = None
    attivo: bool = True
    completato: bool = False
    note: Optional[str] = None

    class Config:
        from_attributes = True

# ============================================================================
# PROGRESS RECORD MODELS
# ============================================================================

class ProgressRecordCreate(BaseModel):
    """Model per creazione record di progresso"""
    id_cliente: int = Field(gt=0)
    data: date = Field(default_factory=date.today)
    pushup_reps: Optional[int] = Field(None, ge=0)
    vo2_estimate: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None

class ProgressRecord(ProgressRecordCreate):
    """Model completo Progress Record (con ID)"""
    id: int
    data_creazione: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# TRAINER DNA MODELS (Workout Card Import & Methodology Learning)
# ============================================================================

class ImportedCardCreate(BaseModel):
    """Model per importazione scheda allenamento"""
    id_cliente: Optional[int] = Field(None, gt=0)
    file_name: str = Field(min_length=1, max_length=255)
    file_type: str = Field(pattern="^(excel|word)$")
    file_path: Optional[str] = None
    raw_content: Optional[str] = None
    parsed_exercises: Optional[Any] = None
    parsed_metadata: Optional[Any] = None

class ImportedCard(ImportedCardCreate):
    """Model completo Imported Card (con ID)"""
    id: int
    extraction_status: str = "pending"
    extraction_error: Optional[str] = None
    pattern_extracted: bool = False
    imported_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TrainerDNAPatternCreate(BaseModel):
    """Model per creazione pattern DNA trainer"""
    pattern_type: str = Field(min_length=1, max_length=50)
    pattern_key: str = Field(min_length=1, max_length=200)
    pattern_value: Any
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence_count: int = Field(ge=1, default=1)
    source_card_ids: Optional[List[int]] = None

class TrainerDNASummary(BaseModel):
    """Riepilogo aggregato del DNA del trainer"""
    total_cards_imported: int = 0
    total_patterns: int = 0
    average_confidence: float = 0.0
    preferred_exercises: List[str] = Field(default_factory=list)
    preferred_set_scheme: Optional[str] = None
    preferred_split: Optional[str] = None
    accessory_philosophy: Optional[str] = None
    ordering_style: Optional[str] = None
    dna_level: str = "learning"  # 'learning' | 'developing' | 'established'
