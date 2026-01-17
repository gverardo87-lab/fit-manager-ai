# core/error_handler.py (Error Handling Centralizzato)
"""
Sistema di error handling coerente per FitManager AI.
Tutti gli errori passano da qui per logging, UI display e recovery.
"""

import streamlit as st
import logging
import traceback
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
from datetime import datetime
from enum import Enum
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "fitmanager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("fitmanager")

# ============================================================================
# EXCEPTION HIERARCHY
# ============================================================================

class FitManagerException(Exception):
    """Base exception per FitManager"""
    def __init__(self, message: str, code: str = "UNKNOWN", context: Optional[dict] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class ValidationError(FitManagerException):
    """Errore di validazione dati"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field

class ClienteNotFound(FitManagerException):
    """Cliente non trovato"""
    def __init__(self, cliente_id: int):
        super().__init__(
            f"Cliente con ID {cliente_id} non trovato",
            code="CLIENTE_NOT_FOUND",
            context={"cliente_id": cliente_id}
        )

class ContratoInvalido(FitManagerException):
    """Contratto non valido"""
    def __init__(self, message: str, contratto_id: Optional[int] = None):
        super().__init__(message, code="CONTRATTO_INVALIDO")
        if contratto_id:
            self.context["contratto_id"] = contratto_id

class DatabaseError(FitManagerException):
    """Errore operazione database"""
    def __init__(self, message: str, operation: str = "unknown"):
        super().__init__(
            f"Errore database durante {operation}: {message}",
            code="DATABASE_ERROR",
            context={"operation": operation}
        )

class ConflictError(FitManagerException):
    """Conflitto (es. turno overlapping)"""
    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT")

class PermissionDenied(FitManagerException):
    """Permesso negato"""
    def __init__(self, resource: str, action: str):
        super().__init__(
            f"Permesso negato: non puoi {action} {resource}",
            code="PERMISSION_DENIED",
            context={"resource": resource, "action": action}
        )

# ============================================================================
# ERROR HANDLING DECORATORS
# ============================================================================

F = TypeVar('F', bound=Callable)

def handle_streamlit_errors(page_name: str = "unknown") -> Callable[[F], F]:
    """
    Decorator per gestire errori nelle pagine Streamlit.
    Mostra messaggi user-friendly e loga errori dettagliati.
    
    Usage:
        @handle_streamlit_errors("02_Clienti")
        def my_page_logic():
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"📄 Page {page_name} - Executing {func.__name__}")
                return func(*args, **kwargs)
            
            except ValidationError as e:
                st.error(f"⚠️ Errore di validazione")
                st.write(f"**Dettagli**: {e.message}")
                if e.field:
                    st.write(f"**Campo**: {e.field}")
                logger.warning(f"Validation error in {page_name}: {e.message}")
            
            except ClienteNotFound as e:
                st.error(f"❌ {e.message}")
                st.info("💡 Seleziona un cliente valido dalla lista a sinistra")
                logger.warning(f"Cliente non trovato in {page_name}: {e.context}")
            
            except ContratoInvalido as e:
                st.error(f"❌ {e.message}")
                logger.warning(f"Contratto invalido in {page_name}: {e.context}")
            
            except DatabaseError as e:
                st.error(f"❌ Errore nel database")
                st.write(f"**Operazione**: {e.context.get('operation', 'unknown')}")
                st.warning("👨‍💻 Contatta l'amministratore se il problema persiste")
                logger.error(f"DB error in {page_name}: {e.message}", exc_info=True)
            
            except ConflictError as e:
                st.error(f"❌ {e.message}")
                st.info("💡 Controlla i turni overlapping e riprova")
                logger.warning(f"Conflict in {page_name}: {e.message}")
            
            except PermissionDenied as e:
                st.error(f"❌ {e.message}")
                logger.warning(f"Permission denied in {page_name}: {e.context}")
            
            except Exception as e:
                # Unexpected error
                error_id = f"{datetime.now().timestamp()}"
                st.error(f"❌ Errore critico (ID: {error_id})")
                st.write("```")
                st.write(str(e))
                st.write("```")
                st.warning(f"👨‍💻 Contatta support con ID: **{error_id}**")
                logger.exception(f"UNEXPECTED error in {page_name}: {error_id}")
        
        return wrapper
    return decorator

def safe_db_operation(operation_name: str = "unknown") -> Callable[[F], F]:
    """
    Decorator per operazioni database con rollback automatico.
    
    Usage:
        @safe_db_operation("add_misurazione")
        def add_misurazione_completa(self, id_cliente, dati):
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.debug(f"🔄 DB Operation: {operation_name}")
                result = func(*args, **kwargs)
                logger.info(f"✅ DB Operation successful: {operation_name}")
                return result
            
            except Exception as e:
                logger.error(f"❌ DB Operation failed: {operation_name} - {str(e)}")
                # Se la funzione ha transaction context, verrà rollbacked automaticamente
                raise DatabaseError(str(e), operation=operation_name)
        
        return wrapper
    return decorator

def safe_streamlit_dialog(dialog_name: str = "Dialog") -> Callable[[F], F]:
    """
    Decorator per dialoghi Streamlit con error recovery.
    
    Usage:
        @safe_streamlit_dialog("Misurazione")
        def dialog_misurazione(id_cliente, dati_pre=None):
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"🎯 Dialog {dialog_name} opened")
                return func(*args, **kwargs)
            
            except Exception as e:
                st.error(f"❌ Errore in {dialog_name}")
                st.write(f"**Dettagli**: {str(e)}")
                logger.exception(f"Dialog error: {dialog_name}")
                st.stop()  # Stop dialog execution
        
        return wrapper
    return decorator

# ============================================================================
# ERROR HANDLER CLASS (Singleton)
# ============================================================================

class ErrorHandler:
    """Gestore centralizzato degli errori"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.error_history = []
        return cls._instance
    
    def log_error(
        self,
        exception: Exception,
        page: str = "unknown",
        context: Optional[dict] = None
    ) -> str:
        """
        Log un errore con context.
        Returns: error_id per tracking
        """
        error_id = f"{datetime.now().timestamp()}"
        
        error_record = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "page": page,
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        self.error_history.append(error_record)
        
        # Log appropriato
        if isinstance(exception, (ValidationError, ClienteNotFound)):
            logger.warning(f"[{error_id}] {type(exception).__name__} in {page}")
        else:
            logger.error(f"[{error_id}] {type(exception).__name__} in {page}", exc_info=True)
        
        return error_id
    
    def get_error_history(self, page: Optional[str] = None, limit: int = 50) -> list:
        """Restituisce lo storico errori"""
        history = self.error_history
        if page:
            history = [e for e in history if e["page"] == page]
        return history[-limit:]
    
    def clear_history(self):
        """Pulisce lo storico"""
        self.error_history = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_error_handler() -> ErrorHandler:
    """Factory per ottenere singleton ErrorHandler"""
    return ErrorHandler()

def show_error_details(exception: FitManagerException) -> None:
    """Mostra dettagli errore in Streamlit"""
    with st.expander("🔍 Dettagli Errore"):
        st.write(f"**Codice**: {exception.code}")
        st.write(f"**Messaggio**: {exception.message}")
        if exception.context:
            st.write(f"**Context**: {exception.context}")
        st.write(f"**Timestamp**: {exception.timestamp.isoformat()}")

def log_page_activity(page_name: str, action: str, details: Optional[dict] = None) -> None:
    """Log attività delle pagine"""
    log_msg = f"📄 {page_name} - {action}"
    if details:
        log_msg += f" - {details}"
    logger.info(log_msg)

# ============================================================================
# PYDANTIC VALIDATION HELPER
# ============================================================================

def validate_model(model_class, data: dict) -> tuple[bool, Any, Optional[str]]:
    """
    Valida dati usando Pydantic model.
    Returns: (is_valid, validated_data or error, error_message)
    
    Usage:
        is_valid, data, error = validate_model(MisurazioneDTO, {"peso": 75, ...})
        if not is_valid:
            st.error(error)
    """
    try:
        validated = model_class(**data)
        return True, validated, None
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Validation failed for {model_class.__name__}: {error_msg}")
        return False, None, error_msg

# ============================================================================
# LOGGING CONFIG
# ============================================================================

def setup_logging(log_level: str = "INFO") -> None:
    """Configurazione logging centralizzata"""
    import os
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Get logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # File handler
    fh = logging.FileHandler("logs/fitmanager.log")
    fh.setLevel(logging.DEBUG)
    
    # Stream handler
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    
    root_logger.addHandler(fh)
    root_logger.addHandler(sh)

# Init logging on import
setup_logging()
