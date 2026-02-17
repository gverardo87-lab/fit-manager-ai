"""
AssessmentRepository - Data access layer for Client Assessments

FASE 2 REFACTORING: Repository Pattern - Assessment Domain

Responsabilita:
- CRUD assessment iniziale (uno per cliente)
- CRUD assessment follow-up (multipli per cliente)
- Timeline assessment (iniziale + tutti follow-up ordinati)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository
from core.models import (
    AssessmentInitial, AssessmentInitialCreate,
    AssessmentFollowup, AssessmentFollowupCreate,
)
from core.error_handler import safe_operation, ErrorSeverity


class AssessmentRepository(BaseRepository):
    """
    Repository per gestione Assessment clienti.

    Metodi principali:
    - save_initial(assessment) -> AssessmentInitial
    - get_initial(client_id) -> AssessmentInitial
    - save_followup(assessment) -> AssessmentFollowup
    - get_followups(client_id) -> List[AssessmentFollowup]
    - get_latest_followup(client_id) -> AssessmentFollowup
    - get_timeline(client_id) -> List[Dict]
    """

    # ---- Colonne tabella assessment iniziale ----
    _INITIAL_COLUMNS = [
        "id_cliente", "data_assessment",
        "altezza_cm", "peso_kg", "massa_grassa_pct",
        "circonferenza_petto_cm", "circonferenza_vita_cm",
        "circonferenza_bicipite_sx_cm", "circonferenza_bicipite_dx_cm",
        "circonferenza_fianchi_cm",
        "circonferenza_quadricipite_sx_cm", "circonferenza_quadricipite_dx_cm",
        "circonferenza_coscia_sx_cm", "circonferenza_coscia_dx_cm",
        "pushups_reps", "pushups_note",
        "panca_peso_kg", "panca_reps", "panca_note",
        "rematore_peso_kg", "rematore_reps", "rematore_note",
        "lat_machine_peso_kg", "lat_machine_reps", "lat_machine_note",
        "squat_bastone_note",
        "squat_macchina_peso_kg", "squat_macchina_reps", "squat_macchina_note",
        "mobilita_spalle_note", "mobilita_gomiti_note", "mobilita_polsi_note",
        "mobilita_anche_note", "mobilita_schiena_note",
        "infortuni_pregessi", "infortuni_attuali", "limitazioni", "storia_medica",
        "goals_quantificabili", "goals_benessere",
        "foto_fronte_path", "foto_lato_path", "foto_dietro_path",
        "note_colloquio",
    ]

    # ---- Colonne tabella assessment follow-up ----
    _FOLLOWUP_COLUMNS = [
        "id_cliente", "data_followup",
        "peso_kg", "massa_grassa_pct",
        "circonferenza_petto_cm", "circonferenza_vita_cm",
        "circonferenza_bicipite_sx_cm", "circonferenza_bicipite_dx_cm",
        "circonferenza_fianchi_cm",
        "circonferenza_quadricipite_sx_cm", "circonferenza_quadricipite_dx_cm",
        "circonferenza_coscia_sx_cm", "circonferenza_coscia_dx_cm",
        "pushups_reps",
        "panca_peso_kg", "panca_reps",
        "rematore_peso_kg", "rematore_reps",
        "squat_peso_kg", "squat_reps",
        "goals_progress",
        "foto_fronte_path", "foto_lato_path", "foto_dietro_path",
        "note_followup",
    ]

    # ------------------------------------------------------------------
    # ASSESSMENT INIZIALE
    # ------------------------------------------------------------------

    @safe_operation(
        operation_name="Save Initial Assessment",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def save_initial(self, assessment: AssessmentInitialCreate) -> Optional[AssessmentInitial]:
        """
        Salva assessment iniziale (INSERT OR REPLACE - uno per cliente).
        """
        data = assessment.model_dump()
        cols = self._INITIAL_COLUMNS
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        values = [data.get(c) for c in cols]

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT OR REPLACE INTO client_assessment_initial ({col_names}) VALUES ({placeholders})",
                values,
            )

            cursor.execute(
                "SELECT * FROM client_assessment_initial WHERE id_cliente = ?",
                (assessment.id_cliente,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            row_dict = self._row_to_dict(row)
            if not row_dict.get("data_creazione"):
                row_dict["data_creazione"] = datetime.now()
            return AssessmentInitial(**row_dict)

    @safe_operation(
        operation_name="Get Initial Assessment",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_initial(self, client_id: int) -> Optional[AssessmentInitial]:
        """
        Recupera assessment iniziale di un cliente.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM client_assessment_initial WHERE id_cliente = ?",
                (client_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            row_dict = self._row_to_dict(row)
            if not row_dict.get("data_creazione"):
                row_dict["data_creazione"] = datetime.now()
            return AssessmentInitial(**row_dict)

    # ------------------------------------------------------------------
    # ASSESSMENT FOLLOW-UP
    # ------------------------------------------------------------------

    @safe_operation(
        operation_name="Save Followup Assessment",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def save_followup(self, assessment: AssessmentFollowupCreate) -> Optional[AssessmentFollowup]:
        """
        Salva assessment di follow-up (INSERT - multipli per cliente).
        """
        data = assessment.model_dump()
        cols = self._FOLLOWUP_COLUMNS
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        values = [data.get(c) for c in cols]

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO client_assessment_followup ({col_names}) VALUES ({placeholders})",
                values,
            )
            new_id = cursor.lastrowid

            cursor.execute(
                "SELECT * FROM client_assessment_followup WHERE id = ?",
                (new_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            row_dict = self._row_to_dict(row)
            if not row_dict.get("data_creazione"):
                row_dict["data_creazione"] = datetime.now()
            return AssessmentFollowup(**row_dict)

    @safe_operation(
        operation_name="Get Followup Assessments",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_followups(self, client_id: int) -> List[AssessmentFollowup]:
        """
        Recupera tutti gli assessment follow-up di un cliente (piu' recente prima).
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM client_assessment_followup WHERE id_cliente = ? ORDER BY data_followup DESC",
                (client_id,),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                row_dict = self._row_to_dict(row)
                if not row_dict.get("data_creazione"):
                    row_dict["data_creazione"] = datetime.now()
                results.append(AssessmentFollowup(**row_dict))
            return results

    @safe_operation(
        operation_name="Get Latest Followup",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_latest_followup(self, client_id: int) -> Optional[AssessmentFollowup]:
        """
        Recupera il follow-up piu' recente di un cliente.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM client_assessment_followup WHERE id_cliente = ? ORDER BY data_followup DESC LIMIT 1",
                (client_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            row_dict = self._row_to_dict(row)
            if not row_dict.get("data_creazione"):
                row_dict["data_creazione"] = datetime.now()
            return AssessmentFollowup(**row_dict)

    # ------------------------------------------------------------------
    # TIMELINE
    # ------------------------------------------------------------------

    @safe_operation(
        operation_name="Get Assessment Timeline",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_timeline(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Costruisce timeline completa degli assessment (iniziale + follow-up).

        Returns:
            Lista di dict: [{"type": "initial", "data": {...}}, {"type": "followup", "data": {...}}, ...]
        """
        timeline = []

        with self._connect() as conn:
            cursor = conn.cursor()

            # Assessment iniziale
            cursor.execute(
                "SELECT * FROM client_assessment_initial WHERE id_cliente = ?",
                (client_id,),
            )
            initial = cursor.fetchone()
            if initial:
                timeline.append({"type": "initial", "data": self._row_to_dict(initial)})

            # Follow-up ordinati per data ASC
            cursor.execute(
                "SELECT * FROM client_assessment_followup WHERE id_cliente = ? ORDER BY data_followup ASC",
                (client_id,),
            )
            for row in cursor.fetchall():
                timeline.append({"type": "followup", "data": self._row_to_dict(row)})

        return timeline
