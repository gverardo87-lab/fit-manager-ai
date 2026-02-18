"""
TrainerDNARepository - Data access layer for Trainer DNA patterns

Gestisce i pattern metodologici estratti dalle schede importate.
I pattern si accumulano nel tempo: ogni nuova scheda rafforza
o contraddice i pattern esistenti.

Confidence formula: min(0.95, 0.3 + evidence_count * 0.15)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .base_repository import BaseRepository
from core.models import TrainerDNASummary
from core.error_handler import safe_operation, ErrorSeverity


class TrainerDNARepository(BaseRepository):
    """Repository per gestione Trainer DNA patterns."""

    @safe_operation(
        operation_name="Upsert Pattern",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def upsert_pattern(
        self,
        pattern_type: str,
        pattern_key: str,
        pattern_value: Any,
        card_id: int
    ) -> Optional[int]:
        """
        Inserisce o aggiorna un pattern DNA.

        Se il pattern (type + key) esiste gia':
        - Incrementa evidence_count
        - Ricalcola confidence_score
        - Aggiunge card_id alla lista source_card_ids

        Se il pattern e' nuovo:
        - Crea con evidence_count=1, confidence=0.5
        """
        value_json = json.dumps(pattern_value, ensure_ascii=False) if not isinstance(pattern_value, str) else pattern_value

        with self._connect() as conn:
            cursor = conn.cursor()

            # Check if pattern exists
            cursor.execute("""
                SELECT id, evidence_count, source_card_ids
                FROM trainer_dna_patterns
                WHERE pattern_type = ? AND pattern_key = ?
            """, (pattern_type, pattern_key))
            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                new_count = existing['evidence_count'] + 1
                new_confidence = min(0.95, 0.3 + new_count * 0.15)

                # Add card_id to source list
                existing_ids = json.loads(existing['source_card_ids']) if existing['source_card_ids'] else []
                if card_id not in existing_ids:
                    existing_ids.append(card_id)

                cursor.execute("""
                    UPDATE trainer_dna_patterns
                    SET pattern_value = ?,
                        evidence_count = ?,
                        confidence_score = ?,
                        source_card_ids = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    value_json,
                    new_count,
                    round(new_confidence, 2),
                    json.dumps(existing_ids),
                    existing['id']
                ))
                return existing['id']
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO trainer_dna_patterns (
                        pattern_type, pattern_key, pattern_value,
                        confidence_score, evidence_count, source_card_ids
                    ) VALUES (?, ?, ?, 0.5, 1, ?)
                """, (
                    pattern_type,
                    pattern_key,
                    value_json,
                    json.dumps([card_id])
                ))
                return cursor.lastrowid

    @safe_operation(
        operation_name="Get Active Patterns",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_active_patterns(self, min_confidence: float = 0.3) -> Optional[TrainerDNASummary]:
        """
        Recupera riepilogo aggregato di tutti i pattern attivi.

        Returns:
            TrainerDNASummary o None se nessun pattern
        """
        with self._connect() as conn:
            cursor = conn.cursor()

            # Count total cards
            cursor.execute("SELECT COUNT(*) as cnt FROM imported_workout_cards")
            total_cards = cursor.fetchone()['cnt']

            # Get all patterns above min confidence
            cursor.execute("""
                SELECT pattern_type, pattern_key, pattern_value,
                       confidence_score, evidence_count
                FROM trainer_dna_patterns
                WHERE confidence_score >= ?
                ORDER BY confidence_score DESC
            """, (min_confidence,))
            rows = cursor.fetchall()

            if not rows and total_cards == 0:
                return None

            total_patterns = len(rows)
            avg_confidence = sum(r['confidence_score'] for r in rows) / total_patterns if rows else 0.0

            # Extract specific patterns
            preferred_exercises = []
            preferred_set_scheme = None
            preferred_split = None
            accessory_philosophy = None
            ordering_style = None

            for row in rows:
                ptype = row['pattern_type']
                pvalue = row['pattern_value']

                try:
                    value = json.loads(pvalue) if isinstance(pvalue, str) else pvalue
                except (json.JSONDecodeError, TypeError):
                    value = pvalue

                if ptype == 'exercise_preference' and isinstance(value, list):
                    preferred_exercises.extend(value)
                elif ptype == 'exercise_preference' and isinstance(value, str):
                    preferred_exercises.append(value)
                elif ptype == 'set_scheme':
                    if preferred_set_scheme is None:
                        preferred_set_scheme = str(value)
                elif ptype == 'split_preference':
                    if preferred_split is None:
                        preferred_split = str(value)
                elif ptype == 'accessory_philosophy':
                    if accessory_philosophy is None:
                        accessory_philosophy = str(value)
                elif ptype == 'ordering_style':
                    if ordering_style is None:
                        ordering_style = str(value)

            # Determine DNA level
            if total_cards >= 10:
                dna_level = "established"
            elif total_cards >= 3:
                dna_level = "developing"
            else:
                dna_level = "learning"

            return TrainerDNASummary(
                total_cards_imported=total_cards,
                total_patterns=total_patterns,
                average_confidence=round(avg_confidence, 2),
                preferred_exercises=preferred_exercises[:20],
                preferred_set_scheme=preferred_set_scheme,
                preferred_split=preferred_split,
                accessory_philosophy=accessory_philosophy,
                ordering_style=ordering_style,
                dna_level=dna_level,
            )

    @safe_operation(
        operation_name="Get Patterns by Type",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_patterns_by_type(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Recupera tutti i pattern di un certo tipo."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trainer_dna_patterns
                WHERE pattern_type = ?
                ORDER BY confidence_score DESC
            """, (pattern_type,))
            patterns = []
            for row in cursor.fetchall():
                p = self._row_to_dict(row)
                if p.get('pattern_value'):
                    try:
                        p['pattern_value'] = json.loads(p['pattern_value'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if p.get('source_card_ids'):
                    try:
                        p['source_card_ids'] = json.loads(p['source_card_ids'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                patterns.append(p)
            return patterns

    @safe_operation(
        operation_name="Get DNA Status",
        severity=ErrorSeverity.LOW,
        fallback_return={}
    )
    def get_dna_status(self) -> Dict[str, Any]:
        """
        Ritorna stato rapido del DNA trainer.

        Returns:
            Dict con total_cards, patterns_extracted, confidence_level
        """
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as cnt FROM imported_workout_cards")
            total_cards = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM imported_workout_cards WHERE pattern_extracted = 1")
            extracted = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt, COALESCE(AVG(confidence_score), 0) as avg_conf FROM trainer_dna_patterns")
            row = cursor.fetchone()
            total_patterns = row['cnt']
            avg_confidence = row['avg_conf']

            if total_cards >= 10:
                level = "established"
            elif total_cards >= 3:
                level = "developing"
            else:
                level = "learning"

            return {
                'total_cards': total_cards,
                'cards_extracted': extracted,
                'total_patterns': total_patterns,
                'average_confidence': round(avg_confidence, 2),
                'dna_level': level,
            }
