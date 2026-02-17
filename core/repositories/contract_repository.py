"""
ContractRepository - Data access layer for Contracts and Payment Rates

FASE 2 REFACTORING: Repository Pattern - Contract Domain

Responsabilità:
- CRUD contratti vendita
- Gestione piano rate (generate, update, delete)
- Pagamento rate con aggiornamento contratto
- Query rate pendenti/scadute

NOTE: Questo repository gestisce SOLO data access.
La business logic (validazioni prezzo, acconto, etc.) è ora nei Pydantic models.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from .base_repository import BaseRepository
from core.models_v2 import Contratto, ContratoCreate, RataProgrammata
from core.error_handler import safe_operation, ErrorSeverity

# Constants
TIPO_ENTRATA = "ENTRATA"
TIPO_USCITA = "USCITA"
CATEGORIA_ACCONTO = "ACCONTO_CONTRATTO"
CATEGORIA_RATA = "PAGAMENTO_RATA"


class ContractRepository(BaseRepository):
    """
    Repository per gestione Contratti e Rate.
    
    Metodi principali:
    - create_contract(contract: ContratoCreate) -> Contratto
    - get_contract_by_id(id: int) -> Optional[Contratto]
    - delete_contract(id: int) -> None
    - generate_payment_plan(contract_id, amount, n_rates, start_date, frequency)
    - get_rates_by_contract(contract_id: int) -> List[RataProgrammata]
    - pay_rate(rate_id, amount, method, payment_date) -> None
    - get_pending_rates(until_date, only_future) -> List[Dict]
    - get_overdue_rates() -> List[Dict]
    """
    
    @safe_operation(
        operation_name="Create Contract",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def create_contract(self, contract: ContratoCreate) -> Optional[Contratto]:
        """
        Crea nuovo contratto vendita.
        
        Args:
            contract: Dati contratto da creare (validato da Pydantic)
        
        Returns:
            Contratto creato con ID o None se errore
        
        NOTE:
            - Se acconto > 0, registra movimento cassa ACCONTO_CONTRATTO
            - totale_versato inizializzato con acconto
            - stato_pagamento = 'PENDENTE' se residuo > 0
        
        Example:
            contract = ContratoCreate(
                id_cliente=1,
                tipo_pacchetto="10 PT",
                crediti_totali=10,
                prezzo_totale=500,
                data_inizio=date.today(),
                data_scadenza=date.today() + timedelta(days=90),
                acconto=150,
                metodo_acconto="POS"
            )
            created = contract_repo.create_contract(contract)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Insert contract
            cursor.execute("""
                INSERT INTO contratti (
                    id_cliente, tipo_pacchetto, data_inizio, data_scadenza,
                    crediti_totali, prezzo_totale, totale_versato, 
                    stato_pagamento, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDENTE', ?)
            """, (
                contract.id_cliente,
                contract.tipo_pacchetto,
                contract.data_inizio,
                contract.data_scadenza,
                contract.crediti_totali,
                contract.prezzo_totale,
                contract.acconto,  # totale_versato = acconto iniziale
                contract.note
            ))
            
            contract_id = cursor.lastrowid
            
            # Register acconto as cash movement if > 0
            if contract.acconto > 0:
                data_acconto = date.today()  # Acconto today by default
                cursor.execute("""
                    INSERT INTO movimenti_cassa (
                        data_effettiva, tipo, categoria, importo, metodo,
                        id_cliente, id_contratto, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Acconto contestuale')
                """, (
                    data_acconto,
                    TIPO_ENTRATA,
                    CATEGORIA_ACCONTO,
                    contract.acconto,
                    contract.metodo_acconto,
                    contract.id_cliente,
                    contract_id
                ))
            
            return self.get_contract_by_id(contract_id)
    
    @safe_operation(
        operation_name="Get Contract by ID",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_contract_by_id(self, id: int) -> Optional[Contratto]:
        """
        Recupera contratto per ID con rate programmate.
        
        Args:
            id: ID contratto
        
        Returns:
            Contratto con lista rate o None se non trovato
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM contratti WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            contract_dict = self._row_to_dict(row)
            
            # Get payment rates
            cursor.execute("""
                SELECT * FROM rate_programmate 
                WHERE id_contratto = ? 
                ORDER BY data_scadenza ASC
            """, (id,))
            
            rates = [RataProgrammata(**self._row_to_dict(r)) for r in cursor.fetchall()]
            contract_dict['rate'] = rates
            
            # Set default data_vendita if missing
            if not contract_dict.get('data_vendita'):
                contract_dict['data_vendita'] = contract_dict.get('data_inizio', date.today())
            
            return Contratto(**contract_dict)
    
    @safe_operation(
        operation_name="Delete Contract",
        severity=ErrorSeverity.CRITICAL,
        fallback_return=None
    )
    def delete_contract(self, id: int) -> None:
        """
        Elimina contratto e tutte le entità correlate.
        
        Args:
            id: ID contratto da eliminare
        
        WARNING:
            - Elimina anche movimenti cassa e rate associate (CASCADE)
            - Operazione irreversibile
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Delete related cash movements
            cursor.execute("DELETE FROM movimenti_cassa WHERE id_contratto = ?", (id,))
            
            # Delete payment rates
            cursor.execute("DELETE FROM rate_programmate WHERE id_contratto = ?", (id,))
            
            # Delete contract
            cursor.execute("DELETE FROM contratti WHERE id = ?", (id,))
    
    @safe_operation(
        operation_name="Generate Payment Plan",
        severity=ErrorSeverity.HIGH,
        fallback_return=[]
    )
    def generate_payment_plan(
        self,
        contract_id: int,
        amount_to_split: float,
        n_rates: int,
        start_date: date,
        frequency: str = "MENSILE"
    ) -> List[RataProgrammata]:
        """
        Genera piano rate per un contratto.
        
        Args:
            contract_id: ID contratto
            amount_to_split: Importo da rateizzare
            n_rates: Numero rate
            start_date: Data prima rata
            frequency: 'MENSILE' | 'SETTIMANALE' | 'TRIMESTRALE'
        
        Returns:
            Lista rate programmate create
        
        NOTE:
            - Elimina rate PENDENTI esistenti prima di creare nuove
            - Mantiene rate già SALDATE
        """
        if n_rates < 1:
            return []
        
        rate_amount = amount_to_split / n_rates
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Delete existing PENDING rates
            cursor.execute("""
                DELETE FROM rate_programmate 
                WHERE id_contratto = ? AND stato = 'PENDENTE'
            """, (contract_id,))
            
            # Generate new rates
            for i in range(n_rates):
                # Calculate due date based on frequency
                if frequency == "MENSILE":
                    due_date = start_date + relativedelta(months=i)
                elif frequency == "SETTIMANALE":
                    due_date = start_date + relativedelta(weeks=i)
                elif frequency == "TRIMESTRALE":
                    due_date = start_date + relativedelta(months=i*3)
                else:
                    due_date = start_date + relativedelta(months=i)  # Default monthly
                
                description = f"Rata {i+1}/{n_rates}"
                
                cursor.execute("""
                    INSERT INTO rate_programmate (
                        id_contratto, data_scadenza, importo_previsto, descrizione
                    ) VALUES (?, ?, ?, ?)
                """, (contract_id, due_date, rate_amount, description))
            
            # Return created rates
            return self.get_rates_by_contract(contract_id)
    
    @safe_operation(
        operation_name="Get Rates by Contract",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_rates_by_contract(self, contract_id: int) -> List[RataProgrammata]:
        """
        Recupera tutte rate di un contratto.
        
        Args:
            contract_id: ID contratto
        
        Returns:
            Lista rate ordinate per data scadenza ASC
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rate_programmate 
                WHERE id_contratto = ? 
                ORDER BY data_scadenza ASC
            """, (contract_id,))
            
            return [RataProgrammata(**self._row_to_dict(r)) for r in cursor.fetchall()]
    
    @safe_operation(
        operation_name="Pay Rate",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def pay_rate(
        self,
        rate_id: int,
        amount_paid: float,
        payment_method: str,
        payment_date: date,
        notes: str = ""
    ) -> None:
        """
        Registra pagamento rata.
        
        Args:
            rate_id: ID rata da pagare
            amount_paid: Importo versato
            payment_method: 'CONTANTI' | 'POS' | 'BONIFICO'
            payment_date: Data effettiva pagamento
            notes: Note opzionali
        
        NOTE:
            - Aggiorna rate_programmate.importo_saldato
            - Aggiorna rate_programmate.stato ('PARZIALE' | 'SALDATA')
            - Aggiorna contratti.totale_versato
            - Registra movimento cassa PAGAMENTO_RATA
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Get rate data
            cursor.execute("SELECT * FROM rate_programmate WHERE id = ?", (rate_id,))
            rate = cursor.fetchone()
            
            if not rate:
                raise ValueError(f"Rata ID {rate_id} non trovata")
            
            # Get contract data
            cursor.execute("SELECT id_cliente FROM contratti WHERE id = ?", (rate['id_contratto'],))
            contract = cursor.fetchone()
            
            if not contract:
                raise ValueError(f"Contratto ID {rate['id_contratto']} non trovato")
            
            # Register cash movement
            cursor.execute("""
                INSERT INTO movimenti_cassa (
                    data_effettiva, tipo, categoria, importo, metodo,
                    id_cliente, id_contratto, id_rata, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment_date,
                TIPO_ENTRATA,
                CATEGORIA_RATA,
                amount_paid,
                payment_method,
                contract['id_cliente'],
                rate['id_contratto'],
                rate_id,
                notes
            ))
            
            # Update rate
            new_paid_amount = rate['importo_saldato'] + amount_paid
            # Rate is SALDATA if paid amount >= expected (with 0.1€ tolerance)
            new_status = 'SALDATA' if new_paid_amount >= rate['importo_previsto'] - 0.1 else 'PARZIALE'
            
            cursor.execute("""
                UPDATE rate_programmate 
                SET importo_saldato = ?, stato = ? 
                WHERE id = ?
            """, (new_paid_amount, new_status, rate_id))
            
            # Update contract totale_versato
            cursor.execute("""
                UPDATE contratti 
                SET totale_versato = totale_versato + ? 
                WHERE id = ?
            """, (amount_paid, rate['id_contratto']))
    
    @safe_operation(
        operation_name="Get Pending Rates",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_pending_rates(
        self,
        until_date: Optional[date] = None,
        only_future: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recupera rate non pagate.
        
        Args:
            until_date: Data limite massima (inclusa)
            only_future: Se True, esclude rate già scadute
        
        Returns:
            Lista dict con rate + dati cliente (per display)
        
        NOTE:
            - Include dati cliente (nome, cogn ome) via JOIN
            - Ordine: data_scadenza ASC
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            oggi = date.today()
            
            query = """
                SELECT rp.*, c.id_cliente, c.tipo_pacchetto, cl.nome, cl.cognome
                FROM rate_programmate rp
                JOIN contratti c ON rp.id_contratto = c.id
                JOIN clienti cl ON c.id_cliente = cl.id
                WHERE rp.stato != 'SALDATA'
            """
            params = []
            
            # Filter only future rates
            if only_future:
                query += " AND rp.data_scadenza >= ?"
                params.append(oggi)
            
            # Filter until date
            if until_date:
                query += " AND rp.data_scadenza <= ?"
                params.append(until_date)
            
            query += " ORDER BY rp.data_scadenza ASC"
            
            cursor.execute(query, params)
            return [self._row_to_dict(r) for r in cursor.fetchall()]
    
    @safe_operation(
        operation_name="Get Overdue Rates",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_overdue_rates(self) -> List[Dict[str, Any]]:
        """
        Recupera rate scadute e non pagate (da sollecitare).
        
        Returns:
            Lista dict con rate scadute + dati cliente
        
        NOTE:
            - Scadute = data_scadenza < oggi AND stato != 'SALDATA'
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            oggi = date.today()
            
            cursor.execute("""
                SELECT rp.*, c.id_cliente, c.tipo_pacchetto, cl.nome, cl.cognome
                FROM rate_programmate rp
                JOIN contratti c ON rp.id_contratto = c.id
                JOIN clienti cl ON c.id_cliente = cl.id
                WHERE rp.stato != 'SALDATA'
                AND rp.data_scadenza < ?
                ORDER BY rp.data_scadenza ASC
            """, (oggi,))
            
            return [self._row_to_dict(r) for r in cursor.fetchall()]
    
    @safe_operation(
        operation_name="Update Contract Details",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def update_contract_details(
        self,
        contract_id: int,
        prezzo_totale: Optional[float] = None,
        crediti_totali: Optional[int] = None,
        data_scadenza: Optional[date] = None
    ) -> None:
        """
        Aggiorna dettagli contratto (prezzo, crediti, scadenza).
        
        Args:
            contract_id: ID contratto da aggiornare
            prezzo_totale: Nuovo prezzo totale (opzionale)
            crediti_totali: Nuovi crediti totali (opzionale)
            data_scadenza: Nuova data scadenza (opzionale)
        
        NOTE:
            - Aggiorna solo campi forniti (non None)
            - Non modifica totale_versato o rate
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if prezzo_totale is not None:
                updates.append("prezzo_totale = ?")
                params.append(prezzo_totale)
            
            if crediti_totali is not None:
                updates.append("crediti_totali = ?")
                params.append(crediti_totali)
            
            if data_scadenza is not None:
                updates.append("data_scadenza = ?")
                params.append(data_scadenza)
            
            if not updates:
                return
            
            params.append(contract_id)
            query = f"UPDATE contratti SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
    
    @safe_operation(
        operation_name="Add Manual Rate",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def add_manual_rate(
        self,
        contract_id: int,
        due_date: date,
        amount: float,
        description: str = "Rata Extra"
    ) -> None:
        """
        Aggiunge rata manuale al contratto.
        
        Args:
            contract_id: ID contratto
            due_date: Data scadenza rata
            amount: Importo rata
            description: Descrizione rata (default: "Rata Extra")
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rate_programmate (
                    id_contratto, data_scadenza, importo_previsto, descrizione
                ) VALUES (?, ?, ?, ?)
            """, (contract_id, due_date, amount, description))
    
    @safe_operation(
        operation_name="Update Rate",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def update_rate(
        self,
        rate_id: int,
        due_date: Optional[date] = None,
        amount: Optional[float] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Aggiorna singola rata.
        
        Args:
            rate_id: ID rata da aggiornare
            due_date: Nuova data scadenza (opzionale)
            amount: Nuovo importo (opzionale)
            description: Nuova descrizione (opzionale)
        
        NOTE:
            - Aggiorna solo campi forniti (non None)
            - Non modifica stato o importo_saldato
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if due_date is not None:
                updates.append("data_scadenza = ?")
                params.append(due_date)
            
            if amount is not None:
                updates.append("importo_previsto = ?")
                params.append(amount)
            
            if description is not None:
                updates.append("descrizione = ?")
                params.append(description)
            
            if not updates:
                return
            
            params.append(rate_id)
            query = f"UPDATE rate_programmate SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
    
    @safe_operation(
        operation_name="Delete Rate",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def delete_rate(self, rate_id: int) -> None:
        """
        Elimina singola rata.
        
        Args:
            rate_id: ID rata da eliminare
        
        WARNING:
            - Elimina anche movimenti cassa associati alla rata
            - Operazione irreversibile
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movimenti_cassa WHERE id_rata = ?", (rate_id,))
            cursor.execute("DELETE FROM rate_programmate WHERE id = ?", (rate_id,))
    
    @safe_operation(
        operation_name="Remodulate Payment Plan",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def remodulate_payment_plan(
        self,
        contract_id: int,
        starting_rate_id: int,
        new_first_amount: float,
        new_first_date: date
    ) -> None:
        """
        Rimodula piano rate successive partendo da una rata specifica.
        
        Args:
            contract_id: ID contratto
            starting_rate_id: ID rata da modificare
            new_first_amount: Nuovo importo prima rata
            new_first_date: Nuova data prima rata
        
        Logica:
            1. Modifica rata indicata con nuovi valori
            2. Recupera rate successive PENDENTI
            3. Ricalcola importi e date mantenendo numero rate
            4. Aggiorna tutte rate successive
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Update starting rate
            cursor.execute("""
                UPDATE rate_programmate 
                SET data_scadenza = ?, importo_previsto = ? 
                WHERE id = ?
            """, (new_first_date, new_first_amount, starting_rate_id))
            
            # Get all subsequent PENDING rates
            cursor.execute("""
                SELECT * FROM rate_programmate 
                WHERE id_contratto = ? 
                AND id > ? 
                AND stato = 'PENDENTE'
                ORDER BY data_scadenza ASC
            """, (contract_id, starting_rate_id))
            
            subsequent_rates = cursor.fetchall()
            
            if not subsequent_rates:
                return
            
            # Calculate total remaining amount and redistribute
            total_remaining = sum(r['importo_previsto'] for r in subsequent_rates)
            n_rates = len(subsequent_rates)
            new_amount_per_rate = total_remaining / n_rates if n_rates > 0 else 0
            
            # Update subsequent rates with new amounts and dates
            for i, rate in enumerate(subsequent_rates):
                # Calculate new date (monthly spacing from new_first_date)
                new_date = new_first_date + relativedelta(months=i+1)
                
                cursor.execute("""
                    UPDATE rate_programmate 
                    SET data_scadenza = ?, importo_previsto = ? 
                    WHERE id = ?
                """, (new_date, new_amount_per_rate, rate['id']))
