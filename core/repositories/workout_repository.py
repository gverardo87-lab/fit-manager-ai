"""
WorkoutRepository - Data access layer for Workout Plans and Progress Records

FASE 2 REFACTORING: Repository Pattern - Workout Domain

Responsabilita:
- CRUD piani di allenamento (con serializzazione JSON)
- CRUD record di progresso
- Gestione stato piano (attivo/completato)
"""

import json
from typing import Optional, List
from datetime import datetime, date

from .base_repository import BaseRepository
from core.models import (
    WorkoutPlan, WorkoutPlanCreate,
    ProgressRecord, ProgressRecordCreate,
)
from core.error_handler import safe_operation, ErrorSeverity


class WorkoutRepository(BaseRepository):
    """
    Repository per gestione Piani Allenamento e Progresso.

    Metodi principali:
    - save_plan(plan) -> WorkoutPlan
    - get_plans_by_client(client_id) -> List[WorkoutPlan]
    - get_plan_by_id(plan_id) -> WorkoutPlan
    - delete_plan(plan_id) -> bool
    - mark_plan_completed(plan_id) -> bool
    - add_progress_record(record) -> ProgressRecord
    - get_progress_records(client_id) -> List[ProgressRecord]
    """

    def _serialize_plan_field(self, value) -> Optional[str]:
        """Serializza list/dict in JSON string per storage nel DB."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_plan_field(self, value: Optional[str]):
        """Deserializza JSON string in list/dict."""
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def _row_to_plan(self, row_dict: dict) -> WorkoutPlan:
        """Converte dict da DB a WorkoutPlan con deserializzazione JSON."""
        row_dict["weekly_schedule"] = self._deserialize_plan_field(row_dict.get("weekly_schedule"))
        row_dict["sources"] = self._deserialize_plan_field(row_dict.get("sources"))
        row_dict["attivo"] = bool(row_dict.get("attivo", 1))
        row_dict["completato"] = bool(row_dict.get("completato", 0))
        # Map NOTE column (uppercase in DB) to note field
        if "NOTE" in row_dict and "note" not in row_dict:
            row_dict["note"] = row_dict.pop("NOTE")
        return WorkoutPlan(**row_dict)

    # ------------------------------------------------------------------
    # WORKOUT PLANS
    # ------------------------------------------------------------------

    @safe_operation(
        operation_name="Save Workout Plan",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def save_plan(self, plan: WorkoutPlanCreate) -> Optional[WorkoutPlan]:
        """
        Salva piano di allenamento generato.
        Serializza weekly_schedule e sources come JSON.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workout_plans (
                    id_cliente, data_inizio, goal, level, duration_weeks,
                    sessions_per_week, methodology, weekly_schedule,
                    exercises_details, progressive_overload_strategy,
                    recovery_recommendations, sources, NOTE, attivo, completato
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """, (
                plan.id_cliente,
                plan.data_inizio,
                plan.goal,
                plan.level,
                plan.duration_weeks,
                plan.sessions_per_week,
                plan.methodology,
                self._serialize_plan_field(plan.weekly_schedule),
                plan.exercises_details,
                plan.progressive_overload_strategy,
                plan.recovery_recommendations,
                self._serialize_plan_field(plan.sources),
                plan.note,
            ))

            plan_id = cursor.lastrowid
            cursor.execute("SELECT * FROM workout_plans WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_plan(self._row_to_dict(row))

    @safe_operation(
        operation_name="Get Plans by Client",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_plans_by_client(self, client_id: int) -> List[WorkoutPlan]:
        """
        Recupera tutti i piani di un cliente (piu' recente prima).
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workout_plans WHERE id_cliente = ? ORDER BY data_creazione DESC",
                (client_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_plan(self._row_to_dict(r)) for r in rows]

    @safe_operation(
        operation_name="Get Plan by ID",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def get_plan_by_id(self, plan_id: int) -> Optional[WorkoutPlan]:
        """
        Recupera singolo piano per ID.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workout_plans WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_plan(self._row_to_dict(row))

    @safe_operation(
        operation_name="Delete Workout Plan",
        severity=ErrorSeverity.HIGH,
        fallback_return=False
    )
    def delete_plan(self, plan_id: int) -> bool:
        """
        Elimina piano di allenamento.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workout_plans WHERE id = ?", (plan_id,))
            return cursor.rowcount > 0

    @safe_operation(
        operation_name="Mark Plan Completed",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=False
    )
    def mark_plan_completed(self, plan_id: int) -> bool:
        """
        Segna piano come completato (completato=1).
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE workout_plans SET completato = 1 WHERE id = ?",
                (plan_id,),
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # PROGRESS RECORDS
    # ------------------------------------------------------------------

    @safe_operation(
        operation_name="Add Progress Record",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=None
    )
    def add_progress_record(self, record: ProgressRecordCreate) -> Optional[ProgressRecord]:
        """
        Aggiunge record di progresso per un cliente.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO progress_records (id_cliente, data, pushup_reps, vo2_estimate, note)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record.id_cliente,
                record.data,
                record.pushup_reps,
                record.vo2_estimate,
                record.note,
            ))

            record_id = cursor.lastrowid
            cursor.execute("SELECT * FROM progress_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                return None

            row_dict = self._row_to_dict(row)
            if not row_dict.get("data_creazione"):
                row_dict["data_creazione"] = datetime.now()
            return ProgressRecord(**row_dict)

    @safe_operation(
        operation_name="Get Progress Records",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=[]
    )
    def get_progress_records(self, client_id: int) -> List[ProgressRecord]:
        """
        Recupera tutti i record di progresso di un cliente (piu' recente prima).
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM progress_records WHERE id_cliente = ? ORDER BY data DESC",
                (client_id,),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                row_dict = self._row_to_dict(row)
                if not row_dict.get("data_creazione"):
                    row_dict["data_creazione"] = datetime.now()
                results.append(ProgressRecord(**row_dict))
            return results
