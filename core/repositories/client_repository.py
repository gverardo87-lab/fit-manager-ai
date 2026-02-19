"""
ClientRepository - Data access layer for Clients and Measurements

FASE 2 REFACTORING: Repository Pattern - Client Domain

Responsabilità:
- CRUD clienti (create, read, update, delete)
- CRUD misurazioni (measurements tracking)
- Client financial history aggregation
- Client session history aggregation

Tutti metodi:
- Accettano Pydantic models in input
- Ritornano Pydantic models in output
- Usano @safe_operation for error handling
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
import json

from .base_repository import BaseRepository
from core.models import (
    Cliente, ClienteCreate, ClienteUpdate,
    Misurazione, MisurazioneCreate, CreditSummary
)
from core.error_handler import safe_operation, ErrorSeverity


class ClientRepository(BaseRepository):
    """
    Repository per gestione Clienti e Misurazioni.
    
    Metodi principali:
    - create(cliente: ClienteCreate) -> Cliente
    - get_by_id(id: int) -> Optional[Cliente]
    - get_all_active() -> List[Cliente]
    - update(id: int, data: ClienteUpdate) -> Cliente
    - add_measurement(measurement: MisurazioneCreate) -> Misurazione
    - get_measurements_by_client(client_id: int) -> List[Misurazione]
    """
    
    @safe_operation(
        operation_name="Create Client",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def create(self, cliente: ClienteCreate) -> Optional[Cliente]:
        """
        Crea nuovo cliente nel DB.
        
        Args:
            cliente: Dati cliente da creare (Pydantic model)
        
        Returns:
            Cliente creato con ID assegnato o None se errore
        
        Example:
            client_repo = ClientRepository()
            new_client = ClienteCreate(
                nome="Mario",
                cognome="Rossi",
                telefono="3331234567",
                email="mario.rossi@gmail.com"
            )
            created = client_repo.create(new_client)
            if created:
                print(f"Cliente {created.id} creato!")
        """
        anamnesi_json = self._serialize_json(cliente.anamnesi)
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clienti (
                    nome, cognome, telefono, email, data_nascita, sesso,
                    anamnesi_json, stato
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Attivo')
            """, (
                cliente.nome,
                cliente.cognome,
                cliente.telefono or '',
                cliente.email or '',
                cliente.data_nascita,
                cliente.sesso or 'Uomo',
                anamnesi_json
            ))

            client_id = cursor.lastrowid

        # Fetch AFTER commit - get_by_id opens a new connection
        return self.get_by_id(client_id)
    
    @safe_operation(
        operation_name="Get Client by ID",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_by_id(self, id: int) -> Optional[Cliente]:
        """
        Recupera cliente per ID con crediti residui calcolati.
        
        Args:
            id: ID cliente da recuperare
        
        Returns:
            Cliente con metadata completa o None se non trovato
        
        Note:
            - Calcola lezioni_residue dal contratto attivo
            - Deserializza anamnesi_json in dict
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Get client data
            cursor.execute("SELECT * FROM clienti WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            client_dict = self._row_to_dict(row)
            
            # Sanitize empty strings to None for backward compatibility with old data
            if client_dict.get('telefono') == '':
                client_dict['telefono'] = None
            if client_dict.get('email') == '':
                client_dict['email'] = None
            
            # Calculate credits from ALL active contracts (no LIMIT 1)
            cursor.execute("""
                SELECT
                    COUNT(*) as num_contratti,
                    COALESCE(SUM(crediti_totali), 0) as totali,
                    COALESCE(SUM(crediti_usati), 0) as completati
                FROM contratti
                WHERE id_cliente = ? AND chiuso = 0
            """, (id,))
            contract_sum = cursor.fetchone()

            # Count booked sessions (Programmato) across active contracts
            cursor.execute("""
                SELECT COUNT(*) as prenotati
                FROM agenda a
                JOIN contratti c ON a.id_contratto = c.id
                WHERE c.id_cliente = ? AND c.chiuso = 0
                  AND a.stato = 'Programmato'
            """, (id,))
            booked = cursor.fetchone()

            totali = contract_sum['totali'] if contract_sum else 0
            completati = contract_sum['completati'] if contract_sum else 0
            prenotati = booked['prenotati'] if booked else 0
            disponibili = totali - completati - prenotati
            num_contratti = contract_sum['num_contratti'] if contract_sum else 0

            client_dict['lezioni_residue'] = disponibili  # backward compat
            client_dict['crediti'] = CreditSummary(
                crediti_totali=totali,
                crediti_completati=completati,
                crediti_prenotati=prenotati,
                crediti_disponibili=disponibili,
                contratti_attivi=num_contratti
            )
            
            # Ensure data_creazione exists (set to now if NULL)
            if not client_dict.get('data_creazione'):
                client_dict['data_creazione'] = datetime.now()
            
            # Parse anamnesi_json
            client_dict['anamnesi'] = self._deserialize_json(client_dict.get('anamnesi_json'))
            
            return Cliente(**client_dict)
    
    @safe_operation(
        operation_name="Get Active Clients",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_all_active(self) -> List[Cliente]:
        """
        Recupera tutti clienti attivi.
        
        Returns:
            Lista di clienti attivi (stato='Attivo'), ordinati per cognome
        
        Note:
            - Ritorna lista vuota se errore
            - Ordine: cognome ASC
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM clienti 
                WHERE stato = 'Attivo' 
                ORDER BY cognome ASC
            """)
            
            rows = cursor.fetchall()
            clients = []
            
            for row in rows:
                client_dict = self._row_to_dict(row)
                
                # Sanitize empty strings to None for backward compatibility with old data
                if client_dict.get('telefono') == '':
                    client_dict['telefono'] = None
                if client_dict.get('email') == '':
                    client_dict['email'] = None
                
                # Ensure data_creazione exists
                if not client_dict.get('data_creazione'):
                    client_dict['data_creazione'] = datetime.now()
                
                # Set default lezioni_residue (will be calculated if needed)
                client_dict['lezioni_residue'] = 0
                
                # Parse anamnesi_json
                client_dict['anamnesi'] = self._deserialize_json(client_dict.get('anamnesi_json'))
                
                clients.append(Cliente(**client_dict))
            
            return clients
    
    @safe_operation(
        operation_name="Update Client",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def update(self, id: int, data: ClienteUpdate) -> Optional[Cliente]:
        """
        Aggiorna dati cliente esistente.
        
        Args:
            id: ID cliente da aggiornare
            data: Dati da aggiornare (solo campi non-None vengono aggiornati)
        
        Returns:
            Cliente aggiornato o None se non trovato/errore
        
        Example:
            update_data = ClienteUpdate(telefono="3339876543")
            updated = client_repo.update(client_id=1, data=update_data)
        """
        # Get current client
        current_client = self.get_by_id(id)
        if not current_client:
            return None
        
        # Build update dict (only non-None fields)
        update_dict = {}
        if data.nome is not None:
            update_dict['nome'] = data.nome
        if data.cognome is not None:
            update_dict['cognome'] = data.cognome
        if data.telefono is not None:
            update_dict['telefono'] = data.telefono
        if data.email is not None:
            update_dict['email'] = data.email
        if data.data_nascita is not None:
            update_dict['data_nascita'] = data.data_nascita
        if data.sesso is not None:
            update_dict['sesso'] = data.sesso
        if data.anamnesi is not None:
            update_dict['anamnesi_json'] = self._serialize_json(data.anamnesi)
        
        if not update_dict:
            return current_client  # No changes
        
        # Build SQL UPDATE query
        fields = ', '.join(f"{k} = ?" for k in update_dict.keys())
        values = list(update_dict.values())
        values.append(id)
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE clienti 
                SET {fields}
                WHERE id = ?
            """, values)
        
        return self.get_by_id(id)
    
    @safe_operation(
        operation_name="Add Measurement",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def add_measurement(self, measurement: MisurazioneCreate) -> Optional[Misurazione]:
        """
        Aggiunge nuova misurazione per un cliente.
        
        Args:
            measurement: Dati misurazione da creare
        
        Returns:
            Misurazione creata con ID assegnato o None se errore
        
        Example:
            measurement = MisurazioneCreate(
                id_cliente=1,
                data_misurazione=date.today(),
                peso=75.5,
                massa_grassa=18.2,
                vita=82,
                fianchi=95
            )
            created = client_repo.add_measurement(measurement)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO misurazioni (
                    id_cliente, data_misurazione, peso, massa_grassa, massa_magra, acqua,
                    collo, spalle, torace, braccio, vita, fianchi, coscia, polpaccio, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                measurement.id_cliente,
                measurement.data_misurazione,
                measurement.peso,
                measurement.massa_grassa,
                measurement.massa_magra,
                measurement.acqua,
                measurement.collo,
                measurement.spalle,
                measurement.torace,
                measurement.braccio,
                measurement.vita,
                measurement.fianchi,
                measurement.coscia,
                measurement.polpaccio,
                measurement.note
            ))
            
            measurement_id = cursor.lastrowid
            
            # Retrieve created measurement
            cursor.execute("SELECT * FROM misurazioni WHERE id = ?", (measurement_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            measurement_dict = self._row_to_dict(row)
            
            # Ensure created_at exists
            if not measurement_dict.get('created_at'):
                measurement_dict['created_at'] = datetime.now()
            
            return Misurazione(**measurement_dict)
    
    @safe_operation(
        operation_name="Get Client Measurements",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_measurements_by_client(self, client_id: int) -> List[Misurazione]:
        """
        Recupera tutte misurazioni di un cliente.
        
        Args:
            client_id: ID cliente
        
        Returns:
            Lista misurazioni ordinate per data DESC (più recente prima)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM misurazioni 
                WHERE id_cliente = ? 
                ORDER BY data_misurazione DESC
            """, (client_id,))
            
            rows = cursor.fetchall()
            measurements = []
            
            for row in rows:
                measurement_dict = self._row_to_dict(row)
                
                # Ensure created_at exists
                if not measurement_dict.get('created_at'):
                    measurement_dict['created_at'] = datetime.now()
                
                measurements.append(Misurazione(**measurement_dict))
            
            return measurements
    
    @safe_operation(
        operation_name="Update Measurement",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def update_measurement(self, id: int, data: MisurazioneCreate) -> Optional[Misurazione]:
        """
        Aggiorna misurazione esistente.
        
        Args:
            id: ID misurazione da aggiornare
            data: Nuovi dati misurazione
        
        Returns:
            Misurazione aggiornata o None se errore
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE misurazioni SET
                    data_misurazione = ?, peso = ?, massa_grassa = ?, massa_magra = ?, acqua = ?,
                    collo = ?, spalle = ?, torace = ?, braccio = ?, vita = ?, fianchi = ?, 
                    coscia = ?, polpaccio = ?, note = ?
                WHERE id = ?
            """, (
                data.data_misurazione, data.peso, data.massa_grassa, data.massa_magra, data.acqua,
                data.collo, data.spalle, data.torace, data.braccio, data.vita, data.fianchi,
                data.coscia, data.polpaccio, data.note, id
            ))
            
            # Retrieve updated measurement
            cursor.execute("SELECT * FROM misurazioni WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            measurement_dict = self._row_to_dict(row)
            
            # Ensure created_at exists
            if not measurement_dict.get('created_at'):
                measurement_dict['created_at'] = datetime.now()
            
            return Misurazione(**measurement_dict)
    
    @safe_operation(
        operation_name="Get Client Financial History",
        severity=ErrorSeverity.MEDIUM,
        fallback_return={"contratti": [], "movimenti": [], "saldo_globale": 0}
    )
    def get_financial_history(self, client_id: int) -> Dict[str, Any]:
        """
        Recupera storico finanziario completo di un cliente.
        
        Args:
            client_id: ID cliente
        
        Returns:
            Dict con:
            - contratti: lista contratti (dict)
            - movimenti: lista movimenti cassa (dict)
            - saldo_globale: totale dovuto - totale versato
        
        Note:
            - Questo metodo potrebbe essere migrato in FinancialRepository
            - Mantenuto qui per compatibilità con get_cliente_financial_history()
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Get contracts
            cursor.execute("""
                SELECT * FROM contratti 
                WHERE id_cliente = ? 
                ORDER BY data_vendita DESC
            """, (client_id,))
            contratti = [self._row_to_dict(r) for r in cursor.fetchall()]
            
            # Get cash movements
            cursor.execute("""
                SELECT * FROM movimenti_cassa 
                WHERE id_cliente = ? 
                ORDER BY data_movimento DESC
            """, (client_id,))
            movimenti = [self._row_to_dict(r) for r in cursor.fetchall()]
            
            # Calculate global balance
            dovuto = sum(c['prezzo_totale'] for c in contratti)
            versato = sum(c['totale_versato'] for c in contratti)
            
            return {
                "contratti": contratti,
                "movimenti": movimenti,
                "saldo_globale": dovuto - versato
            }
