"""
CardImportRepository - Data access layer for imported workout cards

Gestisce CRUD per le schede allenamento importate da Excel/Word.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .base_repository import BaseRepository
from core.error_handler import safe_operation, ErrorSeverity


class CardImportRepository(BaseRepository):
    """Repository per gestione schede allenamento importate."""

    @safe_operation(
        operation_name="Save Imported Card",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def save_card(
        self,
        id_cliente: Optional[int],
        file_name: str,
        file_type: str,
        file_path: Optional[str] = None,
        raw_content: Optional[str] = None,
        parsed_exercises: Optional[list] = None,
        parsed_metadata: Optional[dict] = None
    ) -> Optional[int]:
        """
        Salva scheda importata nel DB.

        Returns:
            ID della scheda creata o None se errore
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO imported_workout_cards (
                    id_cliente, file_name, file_type, file_path,
                    raw_content, parsed_exercises, parsed_metadata,
                    extraction_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'parsed')
            """, (
                id_cliente,
                file_name,
                file_type,
                file_path,
                raw_content,
                json.dumps(parsed_exercises, ensure_ascii=False) if parsed_exercises else None,
                json.dumps(parsed_metadata, ensure_ascii=False) if parsed_metadata else None,
            ))
            return cursor.lastrowid

    @safe_operation(
        operation_name="Get All Cards",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_all_cards(self) -> List[Dict[str, Any]]:
        """Recupera tutte le schede importate."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT iwc.*, c.nome, c.cognome
                FROM imported_workout_cards iwc
                LEFT JOIN clienti c ON iwc.id_cliente = c.id
                ORDER BY iwc.imported_at DESC
            """)
            cards = []
            for row in cursor.fetchall():
                card = self._row_to_dict(row)
                # Deserialize JSON fields
                if card.get('parsed_exercises'):
                    card['parsed_exercises'] = json.loads(card['parsed_exercises'])
                if card.get('parsed_metadata'):
                    card['parsed_metadata'] = json.loads(card['parsed_metadata'])
                cards.append(card)
            return cards

    @safe_operation(
        operation_name="Get Cards by Client",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_cards_by_client(self, client_id: Optional[int]) -> List[Dict[str, Any]]:
        """Recupera schede importate per un cliente specifico."""
        with self._connect() as conn:
            cursor = conn.cursor()
            if client_id is None:
                cursor.execute("""
                    SELECT * FROM imported_workout_cards
                    WHERE id_cliente IS NULL
                    ORDER BY imported_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT * FROM imported_workout_cards
                    WHERE id_cliente = ?
                    ORDER BY imported_at DESC
                """, (client_id,))

            cards = []
            for row in cursor.fetchall():
                card = self._row_to_dict(row)
                if card.get('parsed_exercises'):
                    card['parsed_exercises'] = json.loads(card['parsed_exercises'])
                if card.get('parsed_metadata'):
                    card['parsed_metadata'] = json.loads(card['parsed_metadata'])
                cards.append(card)
            return cards

    @safe_operation(
        operation_name="Get Card by ID",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una singola scheda per ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM imported_workout_cards WHERE id = ?", (card_id,))
            row = cursor.fetchone()
            if not row:
                return None
            card = self._row_to_dict(row)
            if card.get('parsed_exercises'):
                card['parsed_exercises'] = json.loads(card['parsed_exercises'])
            if card.get('parsed_metadata'):
                card['parsed_metadata'] = json.loads(card['parsed_metadata'])
            return card

    @safe_operation(
        operation_name="Update Extraction Status",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=False
    )
    def update_extraction_status(
        self, card_id: int, status: str, error: Optional[str] = None
    ) -> bool:
        """Aggiorna lo stato di estrazione di una scheda."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE imported_workout_cards
                SET extraction_status = ?, extraction_error = ?
                WHERE id = ?
            """, (status, error, card_id))
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Mark Pattern Extracted",
        severity=ErrorSeverity.LOW,
        fallback_return=False
    )
    def mark_pattern_extracted(self, card_id: int) -> bool:
        """Segna una scheda come 'pattern estratti'."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE imported_workout_cards
                SET pattern_extracted = 1, extraction_status = 'extracted'
                WHERE id = ?
            """, (card_id,))
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Delete Imported Card",
        severity=ErrorSeverity.HIGH,
        fallback_return=False
    )
    def delete_card(self, card_id: int) -> bool:
        """Elimina una scheda importata."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM imported_workout_cards WHERE id = ?", (card_id,))
            return cursor.rowcount > 0
