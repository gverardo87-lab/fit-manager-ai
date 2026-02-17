"""
AgendaRepository - Data access layer for Sessions and Events

FASE 2 REFACTORING: Repository Pattern - Agenda Domain

Responsabilità:
- CRUD sessioni allenamento
- CRUD eventi calendario
- Query eventi per range date
- Gestione crediti contratto quando PT session completata
- Storico lezioni cliente

NOTE: Gestisce automaticamente decremento crediti_usati quando PT session creata
"""

from typing import Optional, List
from datetime import datetime, date

from .base_repository import BaseRepository
from core.models_v2 import Sessione, SessioneCreate
from core.error_handler import safe_operation, ErrorSeverity


class AgendaRepository(BaseRepository):
    """
    Repository per gestione Agenda / Sessioni.
    
    Metodi principali:
    - create_event(session: SessioneCreate) -> Sessione
    - update_event(id: int, data: SessioneCreate) -> Sessione
    - delete_event(id: int) -> None
    - get_events_by_range(start: date, end: date) -> List[Sessione]
    - get_client_session_history(client_id: int) -> List[Sessione]
    """
    
    @safe_operation(
        operation_name="Create Event",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def create_event(self, session: SessioneCreate) -> Optional[Sessione]:
        """
        Crea nuovo evento/sessione in agenda.
        
        Args:
            session: Dati sessione da creare
        
        Returns:
            Sessione creata con ID o None se errore
        
        NOTE:
            - Se categoria='PT' e cliente ha contratto aperto, decrementa crediti
            - Aggiorna crediti_usati in contratti table
        
        Example:
            session = SessioneCreate(
                id_cliente=1,
                data_inizio=datetime.now(),
                data_fine=datetime.now() + timedelta(hours=1),
                categoria="PT",
                titolo="Upper Body Strength"
            )
            created = agenda_repo.create_event(session)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Find active contract if PT session
            id_contratto = None
            if session.categoria == 'PT' and session.id_cliente:
                cursor.execute("""
                    SELECT id FROM contratti 
                    WHERE id_cliente = ? 
                    AND chiuso = 0 
                    AND crediti_usati < crediti_totali 
                    ORDER BY data_inizio ASC 
                    LIMIT 1
                """, (session.id_cliente,))
                
                row = cursor.fetchone()
                if row:
                    id_contratto = row['id']
                    # Increment crediti_usati
                    cursor.execute("""
                        UPDATE contratti 
                        SET crediti_usati = crediti_usati + 1 
                        WHERE id = ?
                    """, (id_contratto,))
            
            # Insert event
            cursor.execute("""
                INSERT INTO agenda (
                    data_inizio, data_fine, categoria, titolo, 
                    id_cliente, id_contratto, stato, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.data_inizio,
                session.data_fine,
                session.categoria,
                session.titolo,
                session.id_cliente,
                id_contratto,
                session.stato,
                session.note
            ))
            
            event_id = cursor.lastrowid
            
            # Get created event
            cursor.execute("SELECT * FROM agenda WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            event_dict = self._row_to_dict(row)
            
            # Ensure data_creazione exists
            if not event_dict.get('data_creazione'):
                event_dict['data_creazione'] = datetime.now()
            
            return Sessione(**event_dict)
    
    @safe_operation(
        operation_name="Get Events by Range",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_events_by_range(self, start: date, end: date) -> List[Sessione]:
        """
        Recupera tutti eventi in un range di date.
        
        Args:
            start: Data inizio range
            end: Data fine range (inclusive)
        
        Returns:
            Lista eventi con nome/cognome cliente (LEFT JOIN clienti)
        
        NOTE:
            - Include anche eventi senza cliente associato
            - Ordine: data_inizio ASC
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, c.nome, c.cognome
                FROM agenda a
                LEFT JOIN clienti c ON a.id_cliente = c.id
                WHERE date(a.data_inizio) BETWEEN ? AND ?
                ORDER BY a.data_inizio ASC
            """, (start, end))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                event_dict = self._row_to_dict(row)
                
                # Ensure data_creazione exists
                if not event_dict.get('data_creazione'):
                    event_dict['data_creazione'] = datetime.now()
                
                # Remove extra fields from JOIN (nome, cognome not in Sessione model)
                event_dict.pop('nome', None)
                event_dict.pop('cognome', None)
                
                events.append(Sessione(**event_dict))
            
            return events
    
    @safe_operation(
        operation_name="Delete Event",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def delete_event(self, id: int) -> None:
        """
        Elimina evento e ripristina crediti se PT session.
        
        Args:
            id: ID evento da eliminare
        
        NOTE:
            - Se evento ha id_contratto, decrementa crediti_usati
            - Garantisce ripristino crediti per cancellazioni
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Get event data
            cursor.execute("SELECT id_contratto FROM agenda WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if row and row['id_contratto']:
                # Restore credits
                cursor.execute("""
                    UPDATE contratti 
                    SET crediti_usati = crediti_usati - 1 
                    WHERE id = ?
                """, (row['id_contratto'],))
            
            # Delete event
            cursor.execute("DELETE FROM agenda WHERE id = ?", (id,))
    
    @safe_operation(
        operation_name="Update Event",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def update_event(
        self,
        id: int,
        data_inizio: datetime,
        data_fine: datetime,
        titolo: str,
        note: str = ""
    ) -> Optional[Sessione]:
        """
        Aggiorna evento esistente (data, titolo, note).
        
        Args:
            id: ID evento da aggiornare
            data_inizio: Nuova data/ora inizio
            data_fine: Nuova data/ora fine
            titolo: Nuovo titolo
            note: Nuove note
        
        Returns:
            Sessione aggiornata o None se errore
        
        NOTE:
            - Non modifica categoria, cliente, contratto (solo update di scheduling)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE agenda 
                SET data_inizio = ?, data_fine = ?, titolo = ?, note = ?
                WHERE id = ?
            """, (data_inizio, data_fine, titolo, note, id))
            
            # Get updated event
            cursor.execute("SELECT * FROM agenda WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            event_dict = self._row_to_dict(row)
            
            # Ensure data_creazione exists
            if not event_dict.get('data_creazione'):
                event_dict['data_creazione'] = datetime.now()
            
            return Sessione(**event_dict)
    
    @safe_operation(
        operation_name="Confirm Event",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def confirm_event(self, id: int) -> None:
        """
        Conferma evento (imposta stato='Fatto').
        
        Args:
            id: ID evento da confermare
        
        NOTE:
            - Usato per marcare sessioni completate
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Fetch event data first to check for contract
            cursor.execute("SELECT * FROM agenda WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            cursor.execute("""
                UPDATE agenda 
                SET stato = 'Fatto' 
                WHERE id = ?
            """, (id,))
            
            if row and row['id_contratto']:
                # Restore credits
                cursor.execute("""
                    UPDATE contratti 
                    SET crediti_usati = crediti_usati - 1 
                    WHERE id = ?
                """, (row['id_contratto'],))
            
            # Delete event
            cursor.execute("DELETE FROM agenda WHERE id = ?", (id,))
    
    @safe_operation(
        operation_name="Get Client Session History",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_client_session_history(self, client_id: int) -> List[Sessione]:
        """
        Recupera storico lezioni/sessioni di un cliente.
        
        Args:
            client_id: ID cliente
        
        Returns:
            Lista sessioni ordinate per data DESC (più recente prima)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, c.tipo_pacchetto
                FROM agenda a
                LEFT JOIN contratti c ON a.id_contratto = c.id
                WHERE a.id_cliente = ?
                ORDER BY a.data_inizio DESC
            """, (client_id,))
            
            rows = cursor.fetchall()
            sessions = []
            
            for row in rows:
                session_dict = self._row_to_dict(row)
                
                # Ensure data_creazione exists
                if not session_dict.get('data_creazione'):
                    session_dict['data_creazione'] = datetime.now()
                
                # Remove extra field from JOIN
                session_dict.pop('tipo_pacchetto', None)
                
                sessions.append(Sessione(**session_dict))
            
            return sessions
