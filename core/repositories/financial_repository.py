"""
FinancialRepository - Data access layer for Financial Operations

FASE 2 REFACTORING: Repository Pattern - Financial Domain

Responsabilità:
- Registrazione movimenti cassa (entrate/uscite)
- Gestione spese ricorrenti
- Calcolo bilanci (cassa, competenza)
- Calcolo metriche finanziarie unificate
- Previsione cash flow

NOTE: Questo repository implementa la LOGICA FINANZIARIA UNIFICATA
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta

from .base_repository import BaseRepository
from core.models import MovimentoCassa, MovimentoCassaCreate, SpesaRicorrente, SpesaRicorrenteCreate
from core.error_handler import safe_operation, ErrorSeverity, ConflictError
from core.constants import MovementType, RateStatus, ExpenseFrequency


class FinancialRepository(BaseRepository):
    """
    Repository per gestione Finanza.
    
    Metodi principali:
    - register_cash_movement(movement: MovimentoCassaCreate) -> MovimentoCassa
    - get_cash_balance(start_date, end_date) -> Dict
    - calculate_unified_metrics(start_date, end_date) -> Dict
    - get_cash_forecast(days) -> Dict
    - add_recurring_expense(expense: SpesaRicorrenteCreate) -> SpesaRicorrente
    - get_recurring_expenses() -> List[SpesaRicorrente]
    """
    
    @safe_operation(
        operation_name="Register Cash Movement",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def register_cash_movement(self, movement: MovimentoCassaCreate) -> Optional[MovimentoCassa]:
        """
        Registra movimento cassa (entrata o uscita).
        
        Args:
            movement: Dati movimento da registrare (validato Pydantic)
        
        Returns:
            MovimentoCassa creato con ID o None se errore
        
        Example:
            movement = MovimentoCassaCreate(
                tipo="USCITA",
                categoria="AFFITTO",
                importo=1200,
                metodo="BONIFICO",
                data_effettiva=date.today(),
                note="Affitto palestra gennaio"
            )
            created = financial_repo.register_cash_movement(movement)
        """
        with self._connect() as conn:
            cursor = conn.cursor()

            # Duplicate protection: prevent paying same recurring expense twice in a month
            if movement.id_spesa_ricorrente is not None:
                anno_mese = movement.data_effettiva.strftime('%Y-%m')
                cursor.execute("""
                    SELECT id FROM movimenti_cassa
                    WHERE id_spesa_ricorrente = ?
                      AND strftime('%Y-%m', data_effettiva) = ?
                """, (movement.id_spesa_ricorrente, anno_mese))
                existing = cursor.fetchone()
                if existing:
                    raise ConflictError(
                        f"Spesa ricorrente #{movement.id_spesa_ricorrente} "
                        f"già pagata nel mese {anno_mese} (movimento #{existing[0]})"
                    )

            cursor.execute("""
                INSERT INTO movimenti_cassa (
                    data_movimento, data_effettiva, tipo, categoria, importo, metodo,
                    id_cliente, id_spesa_ricorrente, note, operatore
                ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, 'Admin')
            """, (
                movement.data_effettiva,
                movement.tipo,
                movement.categoria,
                movement.importo,
                movement.metodo,
                movement.id_cliente,
                movement.id_spesa_ricorrente,
                movement.note
            ))
            
            movement_id = cursor.lastrowid
            
            # Get created movement
            cursor.execute("SELECT * FROM movimenti_cassa WHERE id = ?", (movement_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            movement_dict = self._row_to_dict(row)

            return MovimentoCassa(**movement_dict)
    
    @safe_operation(
        operation_name="Get Cash Balance",
        severity=ErrorSeverity.MEDIUM,
        fallback_return={'incassato': 0, 'speso': 0, 'saldo_cassa': 0}
    )
    def get_cash_balance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calcola bilancio per cassa (fonte di verità assoluta).
        
        Args:
            start_date: Data inizio periodo (None = dall'inizio)
            end_date: Data fine periodo (None = fino a oggi)
        
        Returns:
            Dict con:
            - incassato: Somma entrate
            - speso: Somma uscite
            - saldo_cassa: incassato - speso
        
        LOGICA:
            - Basato SOLO su movimenti_cassa.data_effettiva
            - ENTRATE = tipo='ENTRATA'
            - USCITE = tipo='USCITA'
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if start_date and end_date:
                where_conditions.append("data_effettiva BETWEEN ? AND ?")
                params = [start_date, end_date]
            elif end_date and not start_date:
                where_conditions.append("data_effettiva <= ?")
                params = [end_date]
            elif start_date and not end_date:
                where_conditions.append("data_effettiva >= ?")
                params = [start_date]
            
            where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Unified query for entrate + uscite
            query = f"""
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo=? THEN importo ELSE 0 END), 0) as entrate,
                    COALESCE(SUM(CASE WHEN tipo=? THEN importo ELSE 0 END), 0) as uscite
                FROM movimenti_cassa
                WHERE 1=1{where_clause}
            """
            
            cursor.execute(query, [MovementType.ENTRATA.value, MovementType.USCITA.value] + params)
            result = cursor.fetchone()
            
            incassato = result['entrate']
            speso = result['uscite']
            
            return {
                'incassato': round(incassato, 2),
                'speso': round(speso, 2),
                'saldo_cassa': round(incassato - speso, 2)
            }
    
    @safe_operation(
        operation_name="Calculate Unified Metrics",
        severity=ErrorSeverity.MEDIUM,
        fallback_return={}
    )
    def calculate_unified_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calcola metriche finanziarie COMPLETE e COERENTI per un periodo.

        LOGICA UNIFICATA (fonte di verità unica: data_effettiva per movimenti):
        - ENTRATE = SUM(importo) WHERE tipo='ENTRATA' AND data_effettiva IN [start, end]
        - USCITE TOTALI = SUM(importo) WHERE tipo='USCITA' AND data_effettiva IN [start, end]
        - USCITE VARIABILI = uscite WHERE categoria IN ('SPESE_ATTREZZATURE', 'ALTRO')
        - COSTI FISSI = spese_ricorrenti mensili scalate al periodo
        - ORE FATTURATE = crediti_totali da contratti pagati nel periodo
        - ORE ESEGUITE = crediti_usati da contratti nel periodo
        - RATE MANCANTI = rate_programmate non saldate nel periodo
        - MARGINE = Entrate - Uscite_Variabili - Costi_Fissi_Periodo
        - MARGINE/ORA = Margine / Ore Fatturate

        Args:
            start_date: Data inizio periodo
            end_date: Data fine periodo

        Returns:
            Dict con metriche complete
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            giorni_periodo = (end_date - start_date).days + 1

            # 1. ENTRATE (da movimenti_cassa)
            entrate = cursor.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE tipo = ? AND data_effettiva BETWEEN ? AND ?
            """, (MovementType.ENTRATA.value, start_date, end_date)).fetchone()[0]

            # 2. USCITE TOTALI (da movimenti_cassa)
            uscite_totali = cursor.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE tipo = ? AND data_effettiva BETWEEN ? AND ?
            """, (MovementType.USCITA.value, start_date, end_date)).fetchone()[0]

            # 3. USCITE VARIABILI (categorie specifiche)
            uscite_variabili = cursor.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE tipo = ?
                AND categoria IN ('SPESE_ATTREZZATURE', 'ALTRO')
                AND data_effettiva BETWEEN ? AND ?
            """, (MovementType.USCITA.value, start_date, end_date)).fetchone()[0]

            # 4. COSTI FISSI (spese ricorrenti scalate al periodo)
            costi_fissi_mensili = cursor.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM spese_ricorrenti
                WHERE attiva = 1 AND frequenza = ?
            """, (ExpenseFrequency.MENSILE.value,)).fetchone()[0]
            costi_fissi_periodo = (costi_fissi_mensili / 30) * giorni_periodo

            # 5. ORE FATTURATE (crediti da contratti pagati)
            ore_fatturate = cursor.execute("""
                SELECT COALESCE(SUM(crediti_totali), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
                AND totale_versato > 0
            """, (start_date, end_date)).fetchone()[0]

            # 6. ORE ESEGUITE (crediti usati)
            ore_eseguite = cursor.execute("""
                SELECT COALESCE(SUM(crediti_usati), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
            """, (start_date, end_date)).fetchone()[0]

            # 7. RATE MANCANTI (non ancora incassate)
            rate_mancanti = cursor.execute("""
                SELECT COALESCE(SUM(importo_previsto), 0)
                FROM rate_programmate
                WHERE stato != ?
                AND data_scadenza BETWEEN ? AND ?
            """, (RateStatus.SALDATA.value, start_date, end_date)).fetchone()[0]

            # 8. CALCOLI MARGINE
            margine_lordo = entrate - uscite_variabili - costi_fissi_periodo
            margine_orario = (margine_lordo / ore_fatturate) if ore_fatturate > 0 else 0
            fatturato_per_ora = (entrate / ore_fatturate) if ore_fatturate > 0 else 0
            saldo = entrate - uscite_totali

            return {
                'periodo_inizio': str(start_date),
                'periodo_fine': str(end_date),
                'giorni': giorni_periodo,

                # ORE
                'ore_fatturate': round(ore_fatturate, 2),
                'ore_eseguite': round(ore_eseguite, 2),
                'ore_rimanenti': round(ore_fatturate - ore_eseguite, 2),

                # ENTRATE & SALDO
                'entrate_totali': round(entrate, 2),
                'rate_mancanti': round(rate_mancanti, 2),
                'saldo_effettivo': round(saldo, 2),
                'fatturato_per_ora': round(fatturato_per_ora, 2),

                # USCITE
                'uscite_totali': round(uscite_totali, 2),
                'uscite_variabili': round(uscite_variabili, 2),
                'costi_fissi_mensili': round(costi_fissi_mensili, 2),
                'costi_fissi_periodo': round(costi_fissi_periodo, 2),
                'costi_totali': round(uscite_variabili + costi_fissi_periodo, 2),

                # MARGINE
                'margine_lordo': round(margine_lordo, 2),
                'margine_netto': round(margine_lordo, 2),
                'margine_orario': round(margine_orario, 2),

                # METADATA
                'formula': 'Margine = Entrate - Uscite_Variabili - Costi_Fissi_Periodo',
                'note': 'Tutti i dati basati su data_effettiva (movimenti) e data_vendita (contratti)'
            }
    
    @safe_operation(
        operation_name="Get Cash Forecast",
        severity=ErrorSeverity.MEDIUM,
        fallback_return={}
    )
    def get_cash_forecast(self, days: int = 30) -> Dict[str, Any]:
        """
        Previsione cash flow per i prossimi N giorni.
        
        Args:
            days: Numero giorni da prevedere
        
        Returns:
            Dict con:
            - saldo_oggi: Saldo cassa corrente
            - rate_scadenti: Rate in scadenza prossimi N giorni
            - costi_previsti: Costi fissi proporzionali
            - saldo_previsto: saldo_oggi + rate_scadenti - costi_previsti
        """
        # Fetch balance BEFORE opening connection (avoid nested connections)
        balance = self.get_cash_balance()
        saldo_oggi = balance['saldo_cassa']

        oggi = date.today()
        data_fine_prev = oggi + timedelta(days=days)

        with self._connect() as conn:
            cursor = conn.cursor()

            # Upcoming rates (remaining amount = previsto - already paid)
            cursor.execute("""
                SELECT COALESCE(SUM(importo_previsto - importo_saldato), 0)
                FROM rate_programmate
                WHERE data_scadenza BETWEEN ? AND ?
                AND stato != ?
            """, (oggi, data_fine_prev, RateStatus.SALDATA.value))

            rate_scadenti = cursor.fetchone()[0]

            # Fixed costs: total monthly
            cursor.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM spese_ricorrenti
                WHERE attiva = 1 AND frequenza = ?
            """, (ExpenseFrequency.MENSILE.value,))

            costi_fissi_mensili = cursor.fetchone()[0]

            # Already paid this month (avoid double-counting with saldo_oggi)
            anno_mese = oggi.strftime('%Y-%m')
            cursor.execute("""
                SELECT COALESCE(SUM(mc.importo), 0)
                FROM movimenti_cassa mc
                WHERE mc.id_spesa_ricorrente IS NOT NULL
                  AND strftime('%Y-%m', mc.data_effettiva) = ?
            """, (anno_mese,))
            gia_pagati_mese = cursor.fetchone()[0]

            # Forecast: full projection minus what's already been paid
            # (paid expenses are already deducted from saldo_oggi as USCITA)
            costi_previsti_lordi = (costi_fissi_mensili / 30) * days
            costi_previsti = max(0, costi_previsti_lordi - gia_pagati_mese)

        return {
            'saldo_oggi': round(saldo_oggi, 2),
            'rate_scadenti': round(rate_scadenti, 2),
            'costi_previsti': round(costi_previsti, 2),
            'saldo_previsto': round(saldo_oggi + rate_scadenti - costi_previsti, 2),
            'periodo': f"{oggi} + {days} giorni"
        }
    
    @safe_operation(
        operation_name="Add Recurring Expense",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def add_recurring_expense(self, expense: SpesaRicorrenteCreate) -> Optional[SpesaRicorrente]:
        """
        Aggiunge spesa ricorrente.
        
        Args:
            expense: Dati spesa ricorrente (validato Pydantic)
        
        Returns:
            SpesaRicorrente creata o None se errore
        
        Example:
            expense = SpesaRicorrenteCreate(
                nome="Affitto Palestra",
                categoria="COSTI_FISSI",
                importo=1200,
                frequenza="MENSILE",
                giorno_scadenza=5,
                giorno_inizio=1
            )
            created = financial_repo.add_recurring_expense(expense)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO spese_ricorrenti (
                    nome, categoria, importo, frequenza,
                    giorno_scadenza, giorno_inizio, data_prossima_scadenza, attiva
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                expense.nome,
                expense.categoria,
                expense.importo,
                expense.frequenza,
                expense.giorno_scadenza,
                expense.giorno_inizio,
                expense.data_prossima_scadenza,
                expense.attiva
            ))
            
            expense_id = cursor.lastrowid
            
            # Get created expense
            cursor.execute("SELECT * FROM spese_ricorrenti WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return SpesaRicorrente(**self._row_to_dict(row))
    
    @safe_operation(
        operation_name="Get Recurring Expenses",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_recurring_expenses(self, only_active: bool = True) -> List[SpesaRicorrente]:
        """
        Recupera tutte spese ricorrenti.
        
        Args:
            only_active: Se True, ritorna solo spese attive
        
        Returns:
            Lista SpesaRicorrente
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM spese_ricorrenti"
            params = []
            
            if only_active:
                query += " WHERE attiva = ?"
                params.append(1)
            
            query += " ORDER BY nome ASC"
            
            cursor.execute(query, params)
            return [SpesaRicorrente(**self._row_to_dict(r)) for r in cursor.fetchall()]

    @safe_operation(
        operation_name="Update Recurring Expense",
        severity=ErrorSeverity.HIGH,
        fallback_return=False
    )
    def update_recurring_expense(
        self,
        expense_id: int,
        nome: str,
        importo: float,
        categoria: str,
        giorno_scadenza: int
    ) -> bool:
        """Aggiorna una spesa ricorrente esistente."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE spese_ricorrenti
                SET nome = ?, importo = ?, categoria = ?, giorno_scadenza = ?
                WHERE id = ?
            """, (nome, importo, categoria, giorno_scadenza, expense_id))
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Toggle Recurring Expense",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=False
    )
    def toggle_recurring_expense(self, expense_id: int, attiva: bool) -> bool:
        """Attiva/disattiva una spesa ricorrente (soft delete)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE spese_ricorrenti SET attiva = ? WHERE id = ?",
                (1 if attiva else 0, expense_id)
            )
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Delete Recurring Expense",
        severity=ErrorSeverity.HIGH,
        fallback_return=False
    )
    def delete_recurring_expense(self, expense_id: int) -> bool:
        """Elimina definitivamente una spesa ricorrente."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM spese_ricorrenti WHERE id = ?",
                (expense_id,)
            )
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Get Unpaid Fixed Expenses",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_unpaid_fixed_expenses(self, month: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Recupera spese fisse scadute e non pagate (o pagate male) nel mese.
        
        Args:
            month: Mese di riferimento (default: mese corrente)
        
        Returns:
            Lista dict spese non pagate con info:
            - id, nome, importo, giorno_scadenza, categoria, frequenza, attiva
            - movimento_id: ID movimento se esiste ma importo errato
            - importo_pagato: Importo pagato se movimento esiste
        
        NOTE:
            Una spesa è "non pagata" se:
            1. Non esiste movimento collegato nel mese, OPPURE
            2. Esiste movimento ma importo non corrisponde (diff > 0.01€)
        """
        if month is None:
            month = date.today()
        
        anno_mese = month.strftime('%Y-%m')
        giorno_oggi = month.day
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sf.*, 
                       mc.id as movimento_id,
                       mc.importo as importo_pagato
                FROM spese_ricorrenti sf
                LEFT JOIN movimenti_cassa mc 
                    ON sf.id = mc.id_spesa_ricorrente
                    AND strftime('%Y-%m', mc.data_effettiva) = ?
                WHERE sf.attiva = 1
                  AND sf.giorno_scadenza <= ?
                  AND (
                      mc.id IS NULL OR
                      ABS(mc.importo - sf.importo) > 0.01
                  )
                ORDER BY sf.giorno_scadenza ASC
            """, (anno_mese, giorno_oggi))
            
            return [self._row_to_dict(r) for r in cursor.fetchall()]
    
    @safe_operation(
        operation_name="Get Cash Breakdown",
        severity=ErrorSeverity.LOW,
        fallback_return=[]
    )
    def get_cash_breakdown_by_category(
        self, 
        start_date: date, 
        end_date: date, 
        tipo: str = MovementType.ENTRATA.value
    ) -> List[Dict[str, Any]]:
        """
        Ottiene breakdown movimenti per categoria nel periodo.
        
        Args:
            start_date: Data inizio periodo
            end_date: Data fine periodo
            tipo: 'ENTRATA' o 'USCITA'
        
        Returns:
            Lista dict con categoria e totale ordinati per totale DESC
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT categoria, SUM(importo) as totale
                FROM movimenti_cassa
                WHERE tipo = ? AND data_effettiva >= ? AND data_effettiva <= ?
                GROUP BY categoria
                ORDER BY totale DESC
            """, (tipo, start_date, end_date))
            
            return [{'categoria': r[0], 'totale': r[1]} for r in cursor.fetchall()]
    
    @safe_operation(
        operation_name="Get Movement Categories",
        severity=ErrorSeverity.LOW,
        fallback_return=[]
    )
    def get_movement_categories(self) -> List[str]:
        """
        Recupera tutte le categorie utilizzate nei movimenti cassa.
        
        Returns:
            Lista categorie ordinate alfabeticamente
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT categoria 
                FROM movimenti_cassa 
                WHERE categoria IS NOT NULL
                ORDER BY categoria ASC
            """)
            
            return [r[0] for r in cursor.fetchall()]
    
    @safe_operation(
        operation_name="Get Bilancio Competenza",
        severity=ErrorSeverity.MEDIUM,
        fallback_return={}
    )
    def get_bilancio_competenza(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """
        Bilancio per COMPETENZA - Ore vendute nel periodo.
        
        Args:
            start_date: Data inizio periodo
            end_date: Data fine periodo
        
        Returns:
            Dict con:
            - ore_vendute: Totale crediti venduti
            - ore_eseguite: Crediti già usati
            - ore_rimanenti: Crediti residui
            - fatturato_potenziale: Totale prezzo contratti
            - incassato_su_contratti: Totale versato
            - rate_mancanti: Differenza da incassare
        
        NOTE:
            Base: data_vendita dei contratti (quando è stata fatta la vendita)
            Uso: Vedere quanto DOVREBBE arrivare
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Ore vendute nel periodo
            cursor.execute("""
                SELECT COALESCE(SUM(crediti_totali), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
            """, (start_date, end_date))
            ore_vendute = cursor.fetchone()[0]
            
            # Ore eseguite
            cursor.execute("""
                SELECT COALESCE(SUM(crediti_usati), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
            """, (start_date, end_date))
            ore_eseguite = cursor.fetchone()[0]
            
            # Fatturato potenziale
            cursor.execute("""
                SELECT COALESCE(SUM(prezzo_totale), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
            """, (start_date, end_date))
            fatturato_potenziale = cursor.fetchone()[0]
            
            # Incassato su contratti
            cursor.execute("""
                SELECT COALESCE(SUM(totale_versato), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
            """, (start_date, end_date))
            incassato = cursor.fetchone()[0]
            
            return {
                'ore_vendute': round(ore_vendute, 2),
                'ore_eseguite': round(ore_eseguite, 2),
                'ore_rimanenti': round(ore_vendute - ore_eseguite, 2),
                'fatturato_potenziale': round(fatturato_potenziale, 2),
                'incassato_su_contratti': round(incassato, 2),
                'rate_mancanti': round(fatturato_potenziale - incassato, 2)
            }
    
    @safe_operation(
        operation_name="Get Daily Metrics Range",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_daily_metrics_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Calcola metriche giornaliere per un range di date.
        
        Args:
            start_date: Data inizio
            end_date: Data fine
        
        Returns:
            Lista dict con metriche per ogni giorno
        
        NOTE:
            Usa calculate_unified_metrics per ogni giorno
        """
        metrics = []
        current = start_date
        
        while current <= end_date:
            daily = self.calculate_unified_metrics(current, current)
            daily['data'] = str(current)
            metrics.append(daily)
            current += timedelta(days=1)
        
        return metrics
    
    @safe_operation(
        operation_name="Get Margine Per Cliente",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_margine_per_cliente(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Calcola margine per ogni cliente nel periodo.
        
        Args:
            start_date: Data inizio periodo
            end_date: Data fine periodo
        
        Returns:
            Lista dict con margine per cliente ordinati per fatturato DESC
            Campi: cliente_id, cliente, sessioni, ore, fatturato, costi, margine, margine_orario
        
        NOTE:
            Calcola ore da durata sessioni in agenda
            Fatturato da movimenti ENTRATA
            Costi da movimenti USCITA
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id,
                    c.nome || ' ' || c.cognome as cliente,
                    COUNT(DISTINCT a.id) as sessioni,
                    COALESCE(SUM(
                        (CAST(substr(a.data_fine, 12, 2) AS REAL) + 
                         CAST(substr(a.data_fine, 15, 2) AS REAL)/60) -
                        (CAST(substr(a.data_inizio, 12, 2) AS REAL) + 
                         CAST(substr(a.data_inizio, 15, 2) AS REAL)/60)
                    ), 0) as ore,
                    COALESCE(SUM(CASE WHEN m.tipo='ENTRATA' THEN m.importo ELSE 0 END), 0) as fatturato,
                    COALESCE(SUM(CASE WHEN m.tipo='USCITA' THEN m.importo ELSE 0 END), 0) as costi
                FROM clienti c
                LEFT JOIN agenda a ON c.id = a.id_cliente AND DATE(a.data_inizio) BETWEEN ? AND ?
                LEFT JOIN movimenti_cassa m ON c.id = m.id_cliente AND DATE(m.data_effettiva) BETWEEN ? AND ?
                GROUP BY c.id
                ORDER BY fatturato DESC
            """, (start_date, end_date, start_date, end_date))
            
            rows = cursor.fetchall()
            
            return [
                {
                    'cliente_id': r[0],
                    'cliente': r[1],
                    'sessioni': r[2],
                    'ore': round(r[3], 2),
                    'fatturato': round(r[4], 2),
                    'costi': round(r[5], 2),
                    'margine': round(r[4] - r[5], 2),
                    'margine_orario': round((r[4] - r[5]) / r[3], 2) if r[3] > 0 else 0
                }
                for r in rows if r[3] > 0
            ]
    
    @safe_operation(
        operation_name="Get Hourly Metrics Period",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_hourly_metrics_period(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Recupera metriche unificate per un periodo (una per giorno).
        
        Args:
            start_date: Data inizio
            end_date: Data fine
        
        Returns:
            Lista dict con metriche giornaliere
        
        NOTE:
            Alias di get_daily_metrics_range per compatibilità
        """
        return self.get_daily_metrics_range(start_date, end_date)

    # ------------------------------------------------------------------
    # CASH MOVEMENTS CRUD (per 04_Cassa)
    # ------------------------------------------------------------------

    @safe_operation(
        operation_name="Get Cash Movements Filtered",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_cash_movements_filtered(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        tipo: Optional[str] = None,
        cliente_id: Optional[int] = None,
        categoria: Optional[str] = None,
        search_text: Optional[str] = None,
        sort_by: str = "recent",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recupera movimenti cassa con filtri dinamici.
        """
        with self._connect() as conn:
            query = """
                SELECT data_movimento, data_effettiva, tipo, categoria,
                       importo, metodo, note, id_cliente, id
                FROM movimenti_cassa
            """
            conditions = []
            params = []

            if date_from:
                conditions.append("data_effettiva >= ?")
                params.append(str(date_from))
            if date_to:
                conditions.append("data_effettiva <= ?")
                params.append(str(date_to))
            if tipo:
                conditions.append("tipo = ?")
                params.append(tipo)
            if cliente_id is not None:
                conditions.append("id_cliente = ?")
                params.append(cliente_id)
            if categoria:
                conditions.append("categoria = ?")
                params.append(categoria)
            if search_text and search_text.strip():
                conditions.append("(note LIKE ? OR categoria LIKE ?)")
                term = f"%{search_text.strip()}%"
                params.extend([term, term])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            sort_map = {
                "recent": "data_movimento DESC, id DESC",
                "oldest": "data_movimento ASC, id ASC",
                "amount_asc": "importo ASC",
                "amount_desc": "importo DESC",
            }
            query += f" ORDER BY {sort_map.get(sort_by, sort_map['recent'])}"
            query += f" LIMIT {int(limit)}"

            cursor = conn.cursor()
            cursor.execute(query, params)
            return [self._row_to_dict(r) for r in cursor.fetchall()]

    @safe_operation(
        operation_name="Update Cash Movement",
        severity=ErrorSeverity.HIGH,
        fallback_return=False
    )
    def update_cash_movement(
        self,
        movimento_id: int,
        data_effettiva: date,
        tipo: str,
        importo: float,
        categoria: str,
        metodo: str,
        note: str
    ) -> bool:
        """
        Aggiorna un movimento cassa esistente.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE movimenti_cassa
                SET data_effettiva = ?, tipo = ?, importo = ?,
                    categoria = ?, metodo = ?, note = ?
                WHERE id = ?
            """, (data_effettiva, tipo, importo, categoria, metodo, note, movimento_id))
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Delete Cash Movement",
        severity=ErrorSeverity.HIGH,
        fallback_return=False
    )
    def delete_cash_movement(self, movimento_id: int) -> bool:
        """
        Elimina un movimento cassa.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movimenti_cassa WHERE id = ?", (movimento_id,))
            return cursor.rowcount > 0

