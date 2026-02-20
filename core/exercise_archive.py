# core/exercise_archive.py
"""
Exercise Archive - Archivio esercizi persistente su SQLite.

Sostituisce exercise_database.py con un sistema backed da database:
- 300+ esercizi seed con metadata completa
- CRUD per esercizi custom (DNA import, manuali)
- Selezione con punteggio multi-dimensionale per WorkoutGenerator
- Filtri per pattern, equipment, difficulty, muscoli

Le classi PeriodizationTemplates e ProgressionStrategies sono incluse
per compatibilita' con knowledge_chain.py.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from core.error_handler import logger
from core.repositories.base_repository import DB_FILE


# ═══════════════════════════════════════════════════════════════
# SCORED EXERCISE (risultato di selezione)
# ═══════════════════════════════════════════════════════════════

@dataclass
class ScoredExercise:
    """Esercizio con punteggio di selezione."""
    exercise: Dict[str, Any]
    total_score: float
    score_breakdown: Dict[str, float] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# COMPATIBLE PATTERNS (per scoring parziale)
# ═══════════════════════════════════════════════════════════════

COMPATIBLE_PATTERNS = {
    'push_h': ['push_v'],
    'push_v': ['push_h'],
    'pull_h': ['pull_v'],
    'pull_v': ['pull_h'],
    'squat': ['hinge'],
    'hinge': ['squat'],
    'core': ['rotation', 'carry'],
    'rotation': ['core'],
    'carry': ['core'],
}

DIFFICULTY_ORDER = {'beginner': 0, 'intermediate': 1, 'advanced': 2}


# ═══════════════════════════════════════════════════════════════
# EXERCISE ARCHIVE
# ═══════════════════════════════════════════════════════════════

class ExerciseArchive:
    """Archivio esercizi su SQLite. Sostituisce exercise_database.py."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_FILE
        self._ensure_table()
        self._seed_if_empty()

    def _ensure_table(self):
        """Crea tabella exercises se non esiste."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                italian_name TEXT,
                category TEXT NOT NULL,
                movement_pattern TEXT NOT NULL,
                primary_muscles TEXT NOT NULL,
                secondary_muscles TEXT,
                equipment TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                rep_range_strength TEXT,
                rep_range_hypertrophy TEXT,
                rep_range_endurance TEXT,
                recovery_hours INTEGER DEFAULT 48,
                instructions TEXT,
                contraindications TEXT,
                is_custom INTEGER DEFAULT 0,
                source TEXT DEFAULT 'builtin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ─────────────── CRUD ───────────────

    def add_exercise(self, data: Dict[str, Any]) -> Optional[int]:
        """Aggiunge un esercizio. Ritorna ID o None se duplicato."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO exercises (name, italian_name, category, movement_pattern,
                    primary_muscles, secondary_muscles, equipment, difficulty,
                    rep_range_strength, rep_range_hypertrophy, rep_range_endurance,
                    recovery_hours, instructions, contraindications, is_custom, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'], data.get('italian_name'),
                data['category'], data['movement_pattern'],
                json.dumps(data['primary_muscles']),
                json.dumps(data.get('secondary_muscles', [])),
                data['equipment'], data['difficulty'],
                data.get('rep_range_strength'), data.get('rep_range_hypertrophy'),
                data.get('rep_range_endurance'),
                data.get('recovery_hours', 48),
                json.dumps(data.get('instructions')) if data.get('instructions') else None,
                json.dumps(data.get('contraindications', [])),
                1 if data.get('is_custom') else 0,
                data.get('source', 'manual'),
            ))
            conn.commit()
            exercise_id = cursor.lastrowid
            conn.close()
            return exercise_id
        except sqlite3.IntegrityError:
            return None  # Nome duplicato
        except Exception as e:
            logger.error(f"ExerciseArchive.add_exercise error: {e}")
            return None

    def get_exercise(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        """Recupera un esercizio per ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Recupera esercizio per nome (case-insensitive)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exercises WHERE LOWER(name) = LOWER(?)", (name,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def search(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Cerca esercizi per nome/nome IT + filtri opzionali."""
        conn = self._get_conn()
        cursor = conn.cursor()

        conditions = ["(LOWER(name) LIKE ? OR LOWER(italian_name) LIKE ?)"]
        params: list = [f"%{query.lower()}%", f"%{query.lower()}%"]

        if filters:
            if filters.get('category'):
                conditions.append("category = ?")
                params.append(filters['category'])
            if filters.get('movement_pattern'):
                conditions.append("movement_pattern = ?")
                params.append(filters['movement_pattern'])
            if filters.get('equipment'):
                conditions.append("equipment = ?")
                params.append(filters['equipment'])
            if filters.get('difficulty'):
                conditions.append("difficulty = ?")
                params.append(filters['difficulty'])

        sql = f"SELECT * FROM exercises WHERE {' AND '.join(conditions)} ORDER BY name"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def get_all(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Ritorna tutti gli esercizi con filtri opzionali."""
        conn = self._get_conn()
        cursor = conn.cursor()

        conditions = []
        params: list = []

        if filters:
            if filters.get('category'):
                conditions.append("category = ?")
                params.append(filters['category'])
            if filters.get('movement_pattern'):
                conditions.append("movement_pattern = ?")
                params.append(filters['movement_pattern'])
            if filters.get('equipment'):
                conditions.append("equipment = ?")
                params.append(filters['equipment'])
            if filters.get('difficulty'):
                conditions.append("difficulty = ?")
                params.append(filters['difficulty'])
            if filters.get('primary_muscle'):
                conditions.append("primary_muscles LIKE ?")
                params.append(f'%"{filters["primary_muscle"]}"%')

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor.execute(f"SELECT * FROM exercises{where} ORDER BY name", params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def count(self) -> int:
        """Conta esercizi totali."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM exercises")
        n = cursor.fetchone()[0]
        conn.close()
        return n

    def get_by_pattern(self, pattern: str, equipment: Optional[List[str]] = None,
                       level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recupera esercizi per movement_pattern con filtri."""
        conn = self._get_conn()
        cursor = conn.cursor()

        conditions = ["movement_pattern = ?"]
        params: list = [pattern]

        if equipment:
            placeholders = ','.join('?' * len(equipment))
            conditions.append(f"equipment IN ({placeholders})")
            params.extend(equipment)
        if level:
            conditions.append("difficulty = ?")
            params.append(level)

        sql = f"SELECT * FROM exercises WHERE {' AND '.join(conditions)} ORDER BY name"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    # ─────────────── SELEZIONE CON PUNTEGGIO ───────────────

    def select_for_slot(self, slot_pattern: str, slot_muscles: List[str],
                        context: Dict[str, Any]) -> List[ScoredExercise]:
        """
        Seleziona esercizi per uno slot di sessione, ordinati per score.

        Args:
            slot_pattern: movement_pattern richiesto dallo slot
            slot_muscles: muscoli target dello slot
            context: {
                'client_level': str,
                'available_equipment': List[str],
                'contraindications': List[str],
                'recently_used': Set[int],
                'dna_preferences': Optional[dict],  # TrainerDNASummary
                'goal': str
            }

        Returns:
            Lista di ScoredExercise ordinata per score decrescente
        """
        # Carica candidati dal DB (pattern esatto + compatibili)
        compatible = COMPATIBLE_PATTERNS.get(slot_pattern, [])
        all_patterns = [slot_pattern] + compatible

        conn = self._get_conn()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(all_patterns))
        cursor.execute(
            f"SELECT * FROM exercises WHERE movement_pattern IN ({placeholders})",
            all_patterns
        )
        rows = cursor.fetchall()
        conn.close()

        candidates = [self._row_to_dict(r) for r in rows]

        # Filtra per equipment disponibile
        available_eq = set(context.get('available_equipment', []))
        available_eq.add('bodyweight')  # bodyweight sempre disponibile
        candidates = [c for c in candidates if c['equipment'] in available_eq]

        # Filtra per controindicazioni
        contraindications = [l.lower() for l in context.get('contraindications', [])]
        if contraindications:
            safe = []
            for c in candidates:
                contra_list = c.get('contraindications', [])
                is_safe = not any(
                    cl in contra.lower()
                    for cl in contraindications
                    for contra in contra_list
                )
                if is_safe:
                    safe.append(c)
            candidates = safe

        # Score ogni candidato
        scored = []
        for ex in candidates:
            score, breakdown = self._score_exercise(ex, slot_pattern, slot_muscles, context)
            scored.append(ScoredExercise(
                exercise=ex,
                total_score=score,
                score_breakdown=breakdown
            ))

        # Ordina per score decrescente
        scored.sort(key=lambda s: s.total_score, reverse=True)
        return scored

    def _score_exercise(self, exercise: Dict, slot_pattern: str,
                        slot_muscles: List[str], context: Dict) -> tuple:
        """Score multi-dimensionale per selezione esercizi."""
        score = 0.0
        breakdown = {}

        # 1. Pattern match (30%)
        if exercise['movement_pattern'] == slot_pattern:
            breakdown['pattern'] = 0.30
        elif exercise['movement_pattern'] in COMPATIBLE_PATTERNS.get(slot_pattern, []):
            breakdown['pattern'] = 0.15
        else:
            breakdown['pattern'] = 0.0
        score += breakdown['pattern']

        # 2. Difficulty match (25%)
        client_level = context.get('client_level', 'intermediate')
        ex_level = exercise['difficulty']
        if ex_level == client_level:
            breakdown['difficulty'] = 0.25
        elif abs(DIFFICULTY_ORDER.get(ex_level, 1) - DIFFICULTY_ORDER.get(client_level, 1)) == 1:
            breakdown['difficulty'] = 0.12
        else:
            breakdown['difficulty'] = 0.0
        score += breakdown['difficulty']

        # 3. DNA preference (20%) — solo se context ha DNA
        dna = context.get('dna_preferences')
        if dna:
            preferred = [e.lower() for e in dna.get('preferred_exercises', [])]
            if exercise['name'].lower() in preferred:
                breakdown['dna'] = 0.20
            elif exercise.get('italian_name') and exercise['italian_name'].lower() in preferred:
                breakdown['dna'] = 0.20
            else:
                breakdown['dna'] = 0.0
        else:
            breakdown['dna'] = 0.0
        score += breakdown['dna']

        # 4. Equipment fit (15%)
        breakdown['equipment'] = 0.15  # gia' filtrato prima, tutti hanno eq disponibile
        score += breakdown['equipment']

        # 5. Freshness (10%) — penalizza se usato recentemente
        recently_used = context.get('recently_used', set())
        if exercise['id'] not in recently_used:
            breakdown['freshness'] = 0.10
        else:
            breakdown['freshness'] = 0.0
        score += breakdown['freshness']

        # 6. Muscle match bonus (bonus fino a +5%)
        ex_muscles = set(exercise.get('primary_muscles', []))
        target = set(slot_muscles)
        if target and ex_muscles:
            overlap = len(ex_muscles & target) / max(len(target), 1)
            breakdown['muscle_match'] = round(overlap * 0.05, 3)
        else:
            breakdown['muscle_match'] = 0.0
        score += breakdown['muscle_match']

        return round(score, 3), breakdown

    # ─────────────── HELPERS ───────────────

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Converte Row in dict con deserializzazione JSON."""
        d = {key: row[key] for key in row.keys()}
        # Deserializza campi JSON
        for field_name in ('primary_muscles', 'secondary_muscles', 'contraindications'):
            if d.get(field_name):
                try:
                    d[field_name] = json.loads(d[field_name])
                except (json.JSONDecodeError, TypeError):
                    d[field_name] = []
            else:
                d[field_name] = []
        if d.get('instructions'):
            try:
                d['instructions'] = json.loads(d['instructions'])
            except (json.JSONDecodeError, TypeError):
                d['instructions'] = None
        d['is_custom'] = bool(d.get('is_custom', 0))
        return d

    # ─────────────── SEED ───────────────

    def _seed_if_empty(self):
        """Popola con 300+ esercizi se tabella vuota."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM exercises")
        count = cursor.fetchone()[0]

        if count > 0:
            conn.close()
            return

        logger.info("ExerciseArchive: seeding 300+ exercises...")
        exercises = _get_seed_exercises()

        for ex in exercises:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO exercises
                        (name, italian_name, category, movement_pattern,
                         primary_muscles, secondary_muscles, equipment, difficulty,
                         rep_range_strength, rep_range_hypertrophy, rep_range_endurance,
                         recovery_hours, instructions, contraindications, is_custom, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'builtin')
                """, (
                    ex['name'], ex.get('it'),
                    ex['cat'], ex['pat'],
                    json.dumps(ex['pm']), json.dumps(ex.get('sm', [])),
                    ex['eq'], ex['diff'],
                    ex.get('str'), ex.get('hyp'), ex.get('end'),
                    ex.get('rec', 48),
                    json.dumps(ex['instr']) if ex.get('instr') else None,
                    json.dumps(ex.get('contra', [])),
                ))
            except Exception as e:
                logger.warning(f"Seed skip '{ex['name']}': {e}")

        conn.commit()
        final_count = cursor.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
        conn.close()
        logger.info(f"ExerciseArchive: seeded {final_count} exercises")


# ═══════════════════════════════════════════════════════════════
# SEED DATA — 300+ esercizi organizzati per pattern di movimento
# ═══════════════════════════════════════════════════════════════

def _get_seed_exercises() -> List[Dict[str, Any]]:
    """Ritorna lista di esercizi per il seed iniziale.

    Chiavi abbreviate per compattezza:
        name: nome inglese (UNIQUE)
        it:   nome italiano
        cat:  category (compound|isolation|bodyweight|cardio)
        pat:  movement_pattern
        pm:   primary_muscles (list)
        sm:   secondary_muscles (list)
        eq:   equipment
        diff: difficulty
        str:  rep_range_strength
        hyp:  rep_range_hypertrophy
        end:  rep_range_endurance
        rec:  recovery_hours
        contra: controindicazioni
        instr: istruzioni {setup, execution, mistakes}
    """
    return [
        # ═══════════════════════ SQUAT PATTERN ═══════════════════════
        {"name": "Back Squat", "it": "Squat Bilanciere", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-12", "end": "15-20", "rec": 48},
        {"name": "Front Squat", "it": "Squat Anteriore", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["core"], "eq": "barbell", "diff": "advanced",
         "str": "3-6", "hyp": "6-12", "end": "12-15", "rec": 48},
        {"name": "Goblet Squat", "it": "Squat Goblet", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["core"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Leg Press", "it": "Pressa Gambe", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Bodyweight Squat", "it": "Squat a Corpo Libero", "cat": "bodyweight", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "bodyweight", "diff": "beginner",
         "str": "15-20", "hyp": "15-20", "end": "20-30", "rec": 12},
        {"name": "Bulgarian Split Squat", "it": "Squat Bulgaro", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Hack Squat", "it": "Hack Squat Machine", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps"], "sm": ["glutes"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "8-15", "end": "12-20", "rec": 36},
        {"name": "Walking Lunges", "it": "Affondi Camminati", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "dumbbell", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Step Up", "it": "Step Up", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Sissy Squat", "it": "Sissy Squat", "cat": "bodyweight", "pat": "squat",
         "pm": ["quadriceps"], "sm": ["core"], "eq": "bodyweight", "diff": "advanced",
         "str": "6-10", "hyp": "8-15", "end": "12-20", "rec": 36,
         "contra": ["ginocchio"]},
        {"name": "Pistol Squat", "it": "Squat Pistola", "cat": "bodyweight", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "bodyweight", "diff": "advanced",
         "str": "3-6", "hyp": "5-10", "end": "8-15", "rec": 36},
        {"name": "Smith Machine Squat", "it": "Squat al Multipower", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Leg Extension", "it": "Estensione Gambe", "cat": "isolation", "pat": "squat",
         "pm": ["quadriceps"], "eq": "machine", "diff": "beginner",
         "str": "10-15", "hyp": "12-15", "end": "15-20", "rec": 24},
        {"name": "Reverse Lunge", "it": "Affondo Inverso", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings", "core"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Lateral Lunge", "it": "Affondo Laterale", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["adductors"], "eq": "dumbbell", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Belt Squat", "it": "Belt Squat", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings"], "eq": "machine", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Zercher Squat", "it": "Zercher Squat", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["core", "biceps"], "eq": "barbell", "diff": "advanced",
         "str": "3-6", "hyp": "6-10", "end": "10-12", "rec": 48},

        # ═══════════════════════ HINGE PATTERN ═══════════════════════
        {"name": "Conventional Deadlift", "it": "Stacco da Terra Classico", "cat": "compound", "pat": "hinge",
         "pm": ["hamstrings", "glutes", "back"], "sm": ["quadriceps", "core"], "eq": "barbell", "diff": "advanced",
         "str": "1-6", "hyp": "6-10", "end": "10-15", "rec": 48},
        {"name": "Sumo Deadlift", "it": "Stacco Sumo", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "back"], "sm": ["quadriceps", "core"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-10", "end": "10-15", "rec": 48},
        {"name": "Romanian Deadlift", "it": "Stacco Rumeno", "cat": "compound", "pat": "hinge",
         "pm": ["hamstrings", "glutes"], "sm": ["back"], "eq": "barbell", "diff": "intermediate",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Hip Thrust", "it": "Hip Thrust", "cat": "compound", "pat": "hinge",
         "pm": ["glutes"], "sm": ["hamstrings", "core"], "eq": "barbell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-20", "rec": 36},
        {"name": "Glute Bridge", "it": "Ponte Glutei", "cat": "bodyweight", "pat": "hinge",
         "pm": ["glutes"], "sm": ["hamstrings", "core"], "eq": "bodyweight", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Good Morning", "it": "Good Morning", "cat": "compound", "pat": "hinge",
         "pm": ["hamstrings", "glutes"], "sm": ["back", "core"], "eq": "barbell", "diff": "advanced",
         "str": "5-8", "hyp": "6-10", "end": "8-12", "rec": 48,
         "contra": ["schiena"]},
        {"name": "Nordic Hamstring Curl", "it": "Nordic Curl", "cat": "bodyweight", "pat": "hinge",
         "pm": ["hamstrings"], "sm": ["glutes", "core"], "eq": "bodyweight", "diff": "advanced",
         "str": "3-6", "hyp": "5-8", "end": "8-12", "rec": 48},
        {"name": "Single Leg RDL", "it": "Stacco Rumeno Unilaterale", "cat": "compound", "pat": "hinge",
         "pm": ["hamstrings", "glutes"], "sm": ["core"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Cable Pull Through", "it": "Cable Pull Through", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings"], "sm": ["core"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Leg Curl", "it": "Curl Gambe", "cat": "isolation", "pat": "hinge",
         "pm": ["hamstrings"], "eq": "machine", "diff": "beginner",
         "str": "8-12", "hyp": "12-15", "end": "15-20", "rec": 24},
        {"name": "Seated Leg Curl", "it": "Leg Curl Seduto", "cat": "isolation", "pat": "hinge",
         "pm": ["hamstrings"], "eq": "machine", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Dumbbell RDL", "it": "Stacco Rumeno Manubri", "cat": "compound", "pat": "hinge",
         "pm": ["hamstrings", "glutes"], "sm": ["back"], "eq": "dumbbell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Trap Bar Deadlift", "it": "Stacco Trap Bar", "cat": "compound", "pat": "hinge",
         "pm": ["quadriceps", "glutes", "hamstrings"], "sm": ["back", "core"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-10", "end": "10-15", "rec": 48},
        {"name": "Kettlebell Swing", "it": "Swing Kettlebell", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings"], "sm": ["core", "shoulders"], "eq": "kettlebell", "diff": "intermediate",
         "str": "10-15", "hyp": "15-20", "end": "20-30", "rec": 24},
        {"name": "Barbell Hip Thrust", "it": "Hip Thrust Bilanciere", "cat": "compound", "pat": "hinge",
         "pm": ["glutes"], "sm": ["hamstrings", "core"], "eq": "barbell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-20", "rec": 36},
        {"name": "Single Leg Hip Thrust", "it": "Hip Thrust Unilaterale", "cat": "compound", "pat": "hinge",
         "pm": ["glutes"], "sm": ["hamstrings", "core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "6-10", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Standing Calf Raises", "it": "Rialzi Sulle Punte", "cat": "isolation", "pat": "hinge",
         "pm": ["calves"], "eq": "machine", "diff": "beginner",
         "str": "10-15", "hyp": "15-20", "end": "20-30", "rec": 24},
        {"name": "Seated Calf Raises", "it": "Calf Raise Seduto", "cat": "isolation", "pat": "hinge",
         "pm": ["calves"], "eq": "machine", "diff": "beginner",
         "str": "10-15", "hyp": "15-20", "end": "20-30", "rec": 24},
        {"name": "45 Degree Back Extension", "it": "Iperestensioni 45°", "cat": "compound", "pat": "hinge",
         "pm": ["back", "glutes"], "sm": ["hamstrings"], "eq": "bodyweight", "diff": "beginner",
         "str": "8-12", "hyp": "12-15", "end": "15-20", "rec": 24},
        {"name": "Deficit Deadlift", "it": "Stacco in Deficit", "cat": "compound", "pat": "hinge",
         "pm": ["hamstrings", "glutes", "back"], "sm": ["quadriceps", "core"], "eq": "barbell", "diff": "advanced",
         "str": "1-5", "hyp": "5-8", "end": "8-10", "rec": 48},

        # ═══════════════════════ PUSH HORIZONTAL ═══════════════════════
        {"name": "Barbell Bench Press", "it": "Panca Piana Bilanciere", "cat": "compound", "pat": "push_h",
         "pm": ["chest"], "sm": ["triceps", "shoulders"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-12", "end": "12-15", "rec": 48},
        {"name": "Dumbbell Bench Press", "it": "Panca Manubri", "cat": "compound", "pat": "push_h",
         "pm": ["chest"], "sm": ["triceps", "shoulders"], "eq": "dumbbell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-15", "rec": 48},
        {"name": "Incline Bench Press", "it": "Panca Inclinata", "cat": "compound", "pat": "push_h",
         "pm": ["chest"], "sm": ["shoulders", "triceps"], "eq": "barbell", "diff": "intermediate",
         "str": "4-6", "hyp": "6-10", "end": "10-15", "rec": 48},
        {"name": "Incline Dumbbell Press", "it": "Panca Inclinata Manubri", "cat": "compound", "pat": "push_h",
         "pm": ["chest"], "sm": ["shoulders", "triceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 48},
        {"name": "Decline Bench Press", "it": "Panca Declinata", "cat": "compound", "pat": "push_h",
         "pm": ["chest"], "sm": ["triceps"], "eq": "barbell", "diff": "intermediate",
         "str": "4-6", "hyp": "6-10", "end": "10-12", "rec": 48},
        {"name": "Push-ups", "it": "Flessioni", "cat": "bodyweight", "pat": "push_h",
         "pm": ["chest"], "sm": ["triceps", "shoulders", "core"], "eq": "bodyweight", "diff": "beginner",
         "str": "8-15", "hyp": "10-20", "end": "15-30", "rec": 24},
        {"name": "Cable Crossover", "it": "Croci ai Cavi", "cat": "isolation", "pat": "push_h",
         "pm": ["chest"], "sm": ["shoulders"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Pec Deck Machine", "it": "Pectoral Machine", "cat": "isolation", "pat": "push_h",
         "pm": ["chest"], "eq": "machine", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Landmine Press", "it": "Landmine Press", "cat": "compound", "pat": "push_h",
         "pm": ["chest", "shoulders"], "sm": ["core"], "eq": "barbell", "diff": "intermediate",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Close Grip Bench Press", "it": "Panca Presa Stretta", "cat": "compound", "pat": "push_h",
         "pm": ["triceps"], "sm": ["chest", "shoulders"], "eq": "barbell", "diff": "intermediate",
         "str": "4-6", "hyp": "6-10", "end": "10-12", "rec": 48},
        {"name": "Dumbbell Fly", "it": "Croci Manubri", "cat": "isolation", "pat": "push_h",
         "pm": ["chest"], "sm": ["shoulders"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Incline Dumbbell Fly", "it": "Croci Inclinato Manubri", "cat": "isolation", "pat": "push_h",
         "pm": ["chest"], "sm": ["shoulders"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Machine Chest Press", "it": "Chest Press Machine", "cat": "compound", "pat": "push_h",
         "pm": ["chest"], "sm": ["triceps", "shoulders"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "12-20", "rec": 36},
        {"name": "Floor Press", "it": "Floor Press", "cat": "compound", "pat": "push_h",
         "pm": ["chest", "triceps"], "sm": ["shoulders"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-10", "end": "10-12", "rec": 48},
        {"name": "Diamond Push-ups", "it": "Flessioni Diamante", "cat": "bodyweight", "pat": "push_h",
         "pm": ["triceps"], "sm": ["chest", "core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "6-12", "hyp": "10-15", "end": "15-25", "rec": 24},
        {"name": "Svend Press", "it": "Svend Press", "cat": "isolation", "pat": "push_h",
         "pm": ["chest"], "eq": "dumbbell", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},

        # ═══════════════════════ PUSH VERTICAL ═══════════════════════
        {"name": "Overhead Press", "it": "Spinta in Alto", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps", "core"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-12", "end": "12-15", "rec": 48},
        {"name": "Dumbbell Shoulder Press", "it": "Spinta Manubri in Alto", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Arnold Press", "it": "Arnold Press", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Seated Dumbbell Press", "it": "Press Manubri Seduto", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps"], "eq": "dumbbell", "diff": "beginner",
         "str": "5-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Lateral Raises", "it": "Alzate Laterali", "cat": "isolation", "pat": "push_v",
         "pm": ["shoulders"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "12-15", "end": "15-20", "rec": 24},
        {"name": "Cable Lateral Raise", "it": "Alzate Laterali Cavi", "cat": "isolation", "pat": "push_v",
         "pm": ["shoulders"], "eq": "cable", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Rear Delt Fly", "it": "Alzate Posteriori", "cat": "isolation", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["traps"], "eq": "dumbbell", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Reverse Pec Deck", "it": "Pectoral Machine Inversa", "cat": "isolation", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["traps"], "eq": "machine", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Machine Shoulder Press", "it": "Shoulder Press Machine", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Pike Push-ups", "it": "Flessioni Pike", "cat": "bodyweight", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps", "core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "5-10", "hyp": "8-15", "end": "12-20", "rec": 24},
        {"name": "Handstand Push-ups", "it": "Flessioni in Verticale", "cat": "bodyweight", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps", "core"], "eq": "bodyweight", "diff": "advanced",
         "str": "3-6", "hyp": "5-10", "end": "8-15", "rec": 36},
        {"name": "Tricep Dips", "it": "Dip Parallele", "cat": "compound", "pat": "push_v",
         "pm": ["triceps"], "sm": ["chest", "shoulders"], "eq": "bodyweight", "diff": "intermediate",
         "str": "5-10", "hyp": "8-12", "end": "10-15", "rec": 36},
        {"name": "Push Press", "it": "Push Press", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps", "core", "quadriceps"], "eq": "barbell", "diff": "advanced",
         "str": "3-5", "hyp": "5-8", "end": "8-10", "rec": 48},
        {"name": "Z Press", "it": "Z Press", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps", "core"], "eq": "barbell", "diff": "advanced",
         "str": "5-8", "hyp": "6-10", "end": "10-12", "rec": 48},
        {"name": "Upright Row", "it": "Rematore Alto", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders", "traps"], "eq": "barbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36,
         "contra": ["spalla", "impingement"]},
        {"name": "Front Raise", "it": "Alzate Frontali", "cat": "isolation", "pat": "push_v",
         "pm": ["shoulders"], "eq": "dumbbell", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Landmine Lateral Raise", "it": "Alzate Laterali Landmine", "cat": "isolation", "pat": "push_v",
         "pm": ["shoulders"], "eq": "barbell", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},

        # ═══════════════════════ PULL HORIZONTAL ═══════════════════════
        {"name": "Barbell Bent Over Row", "it": "Remata Bilanciere", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "barbell", "diff": "intermediate",
         "str": "3-6", "hyp": "6-12", "end": "12-15", "rec": 48},
        {"name": "Dumbbell Single Arm Row", "it": "Remata Manubrio", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps", "core"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "T-Bar Row", "it": "Rematore T-Bar", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "barbell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-15", "rec": 48},
        {"name": "Chest Supported Row", "it": "Rematore Petto Appoggiato", "cat": "compound", "pat": "pull_h",
         "pm": ["back"], "sm": ["biceps", "traps"], "eq": "dumbbell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Pendlay Row", "it": "Rematore Pendlay", "cat": "compound", "pat": "pull_h",
         "pm": ["back"], "sm": ["biceps", "traps"], "eq": "barbell", "diff": "advanced",
         "str": "3-6", "hyp": "5-8", "end": "8-10", "rec": 48},
        {"name": "Cable Row Wide Grip", "it": "Rematore Cavi Presa Larga", "cat": "compound", "pat": "pull_h",
         "pm": ["lats", "back"], "sm": ["biceps"], "eq": "cable", "diff": "beginner",
         "str": "8-10", "hyp": "10-15", "end": "12-20", "rec": 36},
        {"name": "Inverted Row", "it": "Rematore Inverso", "cat": "bodyweight", "pat": "pull_h",
         "pm": ["back"], "sm": ["biceps", "core"], "eq": "bodyweight", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Seated Cable Row", "it": "Rematore Cavi Seduto", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "cable", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "12-20", "rec": 36},
        {"name": "Machine Row", "it": "Row Machine", "cat": "compound", "pat": "pull_h",
         "pm": ["back"], "sm": ["biceps"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "12-20", "rec": 36},
        {"name": "Meadows Row", "it": "Meadows Row", "cat": "compound", "pat": "pull_h",
         "pm": ["lats"], "sm": ["biceps", "core"], "eq": "barbell", "diff": "advanced",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Seal Row", "it": "Seal Row", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Kroc Row", "it": "Kroc Row", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps", "core"], "eq": "dumbbell", "diff": "advanced",
         "str": "6-8", "hyp": "8-15", "end": "12-20", "rec": 36},

        # ═══════════════════════ PULL VERTICAL ═══════════════════════
        {"name": "Pull-ups", "it": "Trazioni", "cat": "bodyweight", "pat": "pull_v",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "bodyweight", "diff": "advanced",
         "str": "3-6", "hyp": "6-12", "end": "12-20", "rec": 24},
        {"name": "Chin-ups", "it": "Trazioni Supine", "cat": "bodyweight", "pat": "pull_v",
         "pm": ["back", "lats", "biceps"], "sm": ["core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "3-8", "hyp": "6-12", "end": "12-20", "rec": 24},
        {"name": "Lat Pulldown", "it": "Lat Machine", "cat": "compound", "pat": "pull_v",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Wide Grip Lat Pulldown", "it": "Lat Machine Presa Larga", "cat": "compound", "pat": "pull_v",
         "pm": ["lats"], "sm": ["biceps", "back"], "eq": "machine", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Close Grip Lat Pulldown", "it": "Lat Machine Presa Stretta", "cat": "compound", "pat": "pull_v",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "machine", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Neutral Grip Pull-ups", "it": "Trazioni Presa Neutra", "cat": "bodyweight", "pat": "pull_v",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "bodyweight", "diff": "intermediate",
         "str": "3-8", "hyp": "6-12", "end": "12-20", "rec": 24},
        {"name": "Face Pull", "it": "Face Pull Cavi", "cat": "isolation", "pat": "pull_v",
         "pm": ["shoulders", "traps"], "sm": ["back"], "eq": "cable", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Straight Arm Pulldown", "it": "Pulldown Braccia Tese", "cat": "isolation", "pat": "pull_v",
         "pm": ["lats"], "sm": ["core"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Cable Pullover", "it": "Pullover ai Cavi", "cat": "isolation", "pat": "pull_v",
         "pm": ["lats", "chest"], "sm": ["core"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Assisted Pull-ups", "it": "Trazioni Assistite", "cat": "compound", "pat": "pull_v",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "machine", "diff": "beginner",
         "str": "5-8", "hyp": "8-12", "end": "12-20", "rec": 24},
        {"name": "Weighted Pull-ups", "it": "Trazioni Zavorrate", "cat": "compound", "pat": "pull_v",
         "pm": ["back", "lats"], "sm": ["biceps"], "eq": "bodyweight", "diff": "advanced",
         "str": "3-5", "hyp": "5-8", "end": "8-12", "rec": 36},
        {"name": "Single Arm Lat Pulldown", "it": "Lat Machine Unilaterale", "cat": "compound", "pat": "pull_v",
         "pm": ["lats"], "sm": ["biceps"], "eq": "cable", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},

        # ═══════════════════════ ARMS — BICEPS ═══════════════════════
        {"name": "Barbell Curl", "it": "Curl Bilanciere", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "sm": ["forearms"], "eq": "barbell", "diff": "beginner",
         "str": "6-8", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Dumbbell Curl", "it": "Curl Manubri", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "sm": ["forearms"], "eq": "dumbbell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Hammer Curl", "it": "Curl Martello", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "sm": ["forearms"], "eq": "dumbbell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Preacher Curl", "it": "Curl Panca Scott", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "eq": "barbell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Cable Curl", "it": "Curl Cavi", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Incline Dumbbell Curl", "it": "Curl Manubri Panca Inclinata", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Concentration Curl", "it": "Curl Concentrato", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "EZ Bar Curl", "it": "Curl Barra EZ", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "sm": ["forearms"], "eq": "barbell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Spider Curl", "it": "Spider Curl", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Bayesian Curl", "it": "Bayesian Curl", "cat": "isolation", "pat": "pull_h",
         "pm": ["biceps"], "eq": "cable", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},

        # ═══════════════════════ ARMS — TRICEPS ═══════════════════════
        {"name": "Skull Crusher", "it": "French Press", "cat": "isolation", "pat": "push_h",
         "pm": ["triceps"], "eq": "barbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36,
         "contra": ["gomito"]},
        {"name": "Overhead Tricep Extension", "it": "Estensione Tricipiti Sopra Testa", "cat": "isolation", "pat": "push_v",
         "pm": ["triceps"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Rope Tricep Pushdown", "it": "Spinta Tricipiti Corda", "cat": "isolation", "pat": "push_v",
         "pm": ["triceps"], "eq": "cable", "diff": "beginner",
         "str": "10-12", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Cable Pushdown", "it": "Pushdown Cavi", "cat": "isolation", "pat": "push_v",
         "pm": ["triceps"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Tricep Kickback", "it": "Tricep Kickback", "cat": "isolation", "pat": "push_h",
         "pm": ["triceps"], "eq": "dumbbell", "diff": "beginner",
         "str": "10-12", "hyp": "12-15", "end": "15-20", "rec": 24},
        {"name": "Dumbbell Skull Crusher", "it": "French Press Manubri", "cat": "isolation", "pat": "push_h",
         "pm": ["triceps"], "eq": "dumbbell", "diff": "intermediate",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Cable Overhead Extension", "it": "Estensione Overhead Cavi", "cat": "isolation", "pat": "push_v",
         "pm": ["triceps"], "eq": "cable", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "JM Press", "it": "JM Press", "cat": "compound", "pat": "push_h",
         "pm": ["triceps"], "sm": ["chest"], "eq": "barbell", "diff": "advanced",
         "str": "4-6", "hyp": "6-10", "end": "10-12", "rec": 48},
        {"name": "Bench Dips", "it": "Dip su Panca", "cat": "bodyweight", "pat": "push_v",
         "pm": ["triceps"], "sm": ["shoulders"], "eq": "bodyweight", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "15-25", "rec": 24},

        # ═══════════════════════ FOREARMS ═══════════════════════
        {"name": "Wrist Curl", "it": "Curl Polso", "cat": "isolation", "pat": "pull_h",
         "pm": ["forearms"], "eq": "barbell", "diff": "beginner",
         "str": "10-15", "hyp": "15-20", "end": "20-30", "rec": 24},
        {"name": "Reverse Wrist Curl", "it": "Curl Polso Inverso", "cat": "isolation", "pat": "pull_h",
         "pm": ["forearms"], "eq": "barbell", "diff": "beginner",
         "str": "10-15", "hyp": "15-20", "end": "20-30", "rec": 24},
        {"name": "Farmer Walk", "it": "Farmer Walk", "cat": "compound", "pat": "carry",
         "pm": ["forearms", "traps"], "sm": ["core"], "eq": "dumbbell", "diff": "beginner",
         "str": "30-45s", "hyp": "45-60s", "end": "60-90s", "rec": 24},

        # ═══════════════════════ CORE ═══════════════════════
        {"name": "Plank", "it": "Plancia", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["shoulders", "back"], "eq": "bodyweight", "diff": "beginner",
         "str": "30-60s", "hyp": "45-90s", "end": "60-120s", "rec": 24},
        {"name": "Dead Bugs", "it": "Dead Bug", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "eq": "bodyweight", "diff": "beginner",
         "str": "10-15", "hyp": "15-20", "end": "20-30", "rec": 24},
        {"name": "Ab Wheel Rollout", "it": "Ruota Addominale", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["shoulders"], "eq": "bodyweight", "diff": "advanced",
         "str": "5-10", "hyp": "8-15", "end": "12-20", "rec": 36},
        {"name": "Cable Crunch", "it": "Crunch Cavi", "cat": "isolation", "pat": "core",
         "pm": ["core"], "eq": "cable", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Hanging Leg Raise", "it": "Sollevamento Gambe Appeso", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["back"], "eq": "bodyweight", "diff": "advanced",
         "str": "5-10", "hyp": "8-15", "end": "12-20", "rec": 24},
        {"name": "Pallof Press", "it": "Pallof Press", "cat": "isolation", "pat": "core",
         "pm": ["core"], "eq": "cable", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Russian Twist", "it": "Russian Twist", "cat": "bodyweight", "pat": "rotation",
         "pm": ["core"], "eq": "bodyweight", "diff": "beginner",
         "str": "15-25", "hyp": "20-30", "end": "25-40", "rec": 24},
        {"name": "Side Plank", "it": "Plank Laterale", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "eq": "bodyweight", "diff": "beginner",
         "str": "20-30s", "hyp": "30-45s", "end": "45-60s", "rec": 24},
        {"name": "Mountain Climbers", "it": "Mountain Climbers", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["shoulders", "quadriceps"], "eq": "bodyweight", "diff": "beginner",
         "str": "20-30", "hyp": "30-45", "end": "45-60", "rec": 24},
        {"name": "V-ups", "it": "V-ups", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "8-12", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "L-sit", "it": "L-sit", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["shoulders"], "eq": "bodyweight", "diff": "advanced",
         "str": "10-20s", "hyp": "15-30s", "end": "20-45s", "rec": 24},
        {"name": "Dragon Flag", "it": "Dragon Flag", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["back"], "eq": "bodyweight", "diff": "advanced",
         "str": "3-6", "hyp": "5-10", "end": "8-15", "rec": 36},
        {"name": "Bicycle Crunch", "it": "Crunch Bicicletta", "cat": "bodyweight", "pat": "rotation",
         "pm": ["core"], "eq": "bodyweight", "diff": "beginner",
         "str": "15-20", "hyp": "20-30", "end": "30-40", "rec": 24},
        {"name": "Bird Dog", "it": "Bird Dog", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["glutes", "back"], "eq": "bodyweight", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Hollow Body Hold", "it": "Hollow Body", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "15-30s", "hyp": "20-45s", "end": "30-60s", "rec": 24},

        # ═══════════════════════ ROTATION ═══════════════════════
        {"name": "Cable Woodchop", "it": "Woodchop ai Cavi", "cat": "compound", "pat": "rotation",
         "pm": ["core"], "sm": ["shoulders"], "eq": "cable", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Landmine Rotation", "it": "Rotazione Landmine", "cat": "compound", "pat": "rotation",
         "pm": ["core"], "sm": ["shoulders"], "eq": "barbell", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Med Ball Slam", "it": "Med Ball Slam", "cat": "compound", "pat": "rotation",
         "pm": ["core"], "sm": ["shoulders", "lats"], "eq": "bodyweight", "diff": "beginner",
         "str": "8-12", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Turkish Get-Up", "it": "Turkish Get-Up", "cat": "compound", "pat": "rotation",
         "pm": ["core", "shoulders"], "sm": ["glutes", "quadriceps"], "eq": "kettlebell", "diff": "advanced",
         "str": "3-5", "hyp": "5-8", "end": "8-10", "rec": 36},

        # ═══════════════════════ CARRY ═══════════════════════
        {"name": "Farmer Carry", "it": "Farmer Carry", "cat": "compound", "pat": "carry",
         "pm": ["forearms", "traps", "core"], "sm": ["shoulders"], "eq": "dumbbell", "diff": "beginner",
         "str": "30-45s", "hyp": "45-60s", "end": "60-90s", "rec": 24},
        {"name": "Suitcase Carry", "it": "Suitcase Carry", "cat": "compound", "pat": "carry",
         "pm": ["core", "forearms"], "sm": ["traps", "shoulders"], "eq": "dumbbell", "diff": "intermediate",
         "str": "30-45s", "hyp": "45-60s", "end": "60-90s", "rec": 24},
        {"name": "Overhead Carry", "it": "Overhead Carry", "cat": "compound", "pat": "carry",
         "pm": ["shoulders", "core"], "sm": ["traps"], "eq": "dumbbell", "diff": "advanced",
         "str": "20-30s", "hyp": "30-45s", "end": "45-60s", "rec": 24},
        {"name": "Waiter Walk", "it": "Waiter Walk", "cat": "compound", "pat": "carry",
         "pm": ["shoulders", "core"], "sm": ["traps"], "eq": "kettlebell", "diff": "intermediate",
         "str": "20-30s", "hyp": "30-45s", "end": "45-60s", "rec": 24},
        {"name": "Rack Carry", "it": "Rack Carry", "cat": "compound", "pat": "carry",
         "pm": ["core", "biceps"], "sm": ["shoulders", "traps"], "eq": "kettlebell", "diff": "intermediate",
         "str": "30-45s", "hyp": "45-60s", "end": "60-90s", "rec": 24},

        # ═══════════════════════ KETTLEBELL ═══════════════════════
        {"name": "Kettlebell Goblet Squat", "it": "Goblet Squat Kettlebell", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["core"], "eq": "kettlebell", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Kettlebell Clean", "it": "Clean Kettlebell", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings"], "sm": ["core", "shoulders"], "eq": "kettlebell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Kettlebell Snatch", "it": "Snatch Kettlebell", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings", "shoulders"], "sm": ["core"], "eq": "kettlebell", "diff": "advanced",
         "str": "5-8", "hyp": "8-12", "end": "12-20", "rec": 36},
        {"name": "Kettlebell Clean and Press", "it": "Clean & Press Kettlebell", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders", "glutes"], "sm": ["core", "triceps"], "eq": "kettlebell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-15", "rec": 36},
        {"name": "Kettlebell Windmill", "it": "Windmill Kettlebell", "cat": "compound", "pat": "rotation",
         "pm": ["core", "shoulders"], "sm": ["hamstrings"], "eq": "kettlebell", "diff": "advanced",
         "str": "5-8", "hyp": "8-10", "end": "10-12", "rec": 36},
        {"name": "Kettlebell Row", "it": "Remata Kettlebell", "cat": "compound", "pat": "pull_h",
         "pm": ["back", "lats"], "sm": ["biceps", "core"], "eq": "kettlebell", "diff": "beginner",
         "str": "6-10", "hyp": "8-12", "end": "12-15", "rec": 24},
        {"name": "Kettlebell Thruster", "it": "Thruster Kettlebell", "cat": "compound", "pat": "push_v",
         "pm": ["quadriceps", "shoulders"], "sm": ["glutes", "triceps", "core"], "eq": "kettlebell", "diff": "intermediate",
         "str": "5-8", "hyp": "8-12", "end": "12-15", "rec": 36},

        # ═══════════════════════ TRX / BAND ═══════════════════════
        {"name": "TRX Row", "it": "Remata TRX", "cat": "bodyweight", "pat": "pull_h",
         "pm": ["back"], "sm": ["biceps", "core"], "eq": "trx", "diff": "beginner",
         "str": "8-12", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "TRX Push-up", "it": "Flessioni TRX", "cat": "bodyweight", "pat": "push_h",
         "pm": ["chest"], "sm": ["triceps", "core"], "eq": "trx", "diff": "intermediate",
         "str": "6-12", "hyp": "10-15", "end": "15-25", "rec": 24},
        {"name": "TRX Squat", "it": "Squat TRX", "cat": "bodyweight", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["core"], "eq": "trx", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "TRX Pike", "it": "Pike TRX", "cat": "bodyweight", "pat": "core",
         "pm": ["core"], "sm": ["shoulders"], "eq": "trx", "diff": "intermediate",
         "str": "8-12", "hyp": "10-15", "end": "12-20", "rec": 24},
        {"name": "Band Pull Apart", "it": "Aperture Elastico", "cat": "isolation", "pat": "pull_h",
         "pm": ["shoulders", "back"], "eq": "band", "diff": "beginner",
         "str": "12-20", "hyp": "15-25", "end": "20-30", "rec": 24},
        {"name": "Band Face Pull", "it": "Face Pull Elastico", "cat": "isolation", "pat": "pull_v",
         "pm": ["shoulders", "traps"], "eq": "band", "diff": "beginner",
         "str": "12-20", "hyp": "15-25", "end": "20-30", "rec": 24},
        {"name": "Band Squat", "it": "Squat con Elastico", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["hamstrings"], "eq": "band", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Band Row", "it": "Remata Elastico", "cat": "compound", "pat": "pull_h",
         "pm": ["back"], "sm": ["biceps"], "eq": "band", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},
        {"name": "Band Overhead Press", "it": "Press Overhead Elastico", "cat": "compound", "pat": "push_v",
         "pm": ["shoulders"], "sm": ["triceps"], "eq": "band", "diff": "beginner",
         "str": "10-15", "hyp": "12-20", "end": "15-25", "rec": 24},

        # ═══════════════════════ TRAPS ═══════════════════════
        {"name": "Barbell Shrugs", "it": "Scrollate Bilanciere", "cat": "isolation", "pat": "pull_v",
         "pm": ["traps"], "eq": "barbell", "diff": "beginner",
         "str": "6-10", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Dumbbell Shrugs", "it": "Scrollate Manubri", "cat": "isolation", "pat": "pull_v",
         "pm": ["traps"], "eq": "dumbbell", "diff": "beginner",
         "str": "8-12", "hyp": "12-15", "end": "15-25", "rec": 24},

        # ═══════════════════════ CARDIO / CONDITIONING ═══════════════════════
        {"name": "Running", "it": "Corsa", "cat": "cardio", "pat": "squat",
         "pm": ["quadriceps", "hamstrings", "glutes"], "eq": "bodyweight", "diff": "beginner",
         "str": "20-30min", "hyp": "20-45min", "end": "30-60min", "rec": 24,
         "contra": ["ginocchio"]},
        {"name": "Cycling", "it": "Ciclismo", "cat": "cardio", "pat": "squat",
         "pm": ["quadriceps", "hamstrings", "glutes"], "eq": "machine", "diff": "beginner",
         "str": "30-45min", "hyp": "30-60min", "end": "45-120min", "rec": 12},
        {"name": "Rowing Machine", "it": "Vogatore", "cat": "cardio", "pat": "pull_h",
         "pm": ["back", "quadriceps", "hamstrings"], "sm": ["core", "biceps"], "eq": "machine", "diff": "intermediate",
         "str": "15-25min", "hyp": "20-40min", "end": "30-60min", "rec": 24},
        {"name": "Jump Rope", "it": "Salto con la Corda", "cat": "cardio", "pat": "squat",
         "pm": ["calves", "quadriceps"], "sm": ["core", "shoulders"], "eq": "bodyweight", "diff": "beginner",
         "str": "5-10min", "hyp": "10-20min", "end": "15-30min", "rec": 12},
        {"name": "Battle Ropes", "it": "Funi Battaglie", "cat": "cardio", "pat": "push_v",
         "pm": ["shoulders", "core"], "sm": ["back"], "eq": "bodyweight", "diff": "intermediate",
         "str": "20-30s", "hyp": "30-45s", "end": "45-60s", "rec": 24},
        {"name": "Box Jumps", "it": "Salti su Box", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["calves", "core"], "eq": "bodyweight", "diff": "intermediate",
         "str": "3-6", "hyp": "6-10", "end": "10-15", "rec": 24},
        {"name": "Burpees", "it": "Burpees", "cat": "bodyweight", "pat": "squat",
         "pm": ["quadriceps", "chest", "core"], "sm": ["shoulders", "triceps"], "eq": "bodyweight", "diff": "intermediate",
         "str": "5-10", "hyp": "10-15", "end": "15-20", "rec": 24},
        {"name": "Sled Push", "it": "Spinta Slitta", "cat": "compound", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["core", "shoulders"], "eq": "machine", "diff": "intermediate",
         "str": "20-30s", "hyp": "30-45s", "end": "45-60s", "rec": 36},
        {"name": "Assault Bike", "it": "Assault Bike", "cat": "cardio", "pat": "squat",
         "pm": ["quadriceps", "hamstrings"], "sm": ["shoulders", "core"], "eq": "machine", "diff": "beginner",
         "str": "20-30s", "hyp": "30-60s", "end": "60-120s", "rec": 12},
        {"name": "Stair Climber", "it": "Scalatore", "cat": "cardio", "pat": "squat",
         "pm": ["quadriceps", "glutes"], "sm": ["calves"], "eq": "machine", "diff": "beginner",
         "str": "10-15min", "hyp": "15-25min", "end": "20-40min", "rec": 12},
        {"name": "Elliptical", "it": "Ellittica", "cat": "cardio", "pat": "squat",
         "pm": ["quadriceps", "hamstrings", "glutes"], "eq": "machine", "diff": "beginner",
         "str": "15-25min", "hyp": "20-40min", "end": "30-60min", "rec": 12},
        {"name": "Swimming", "it": "Nuoto", "cat": "cardio", "pat": "pull_h",
         "pm": ["back", "shoulders"], "sm": ["core", "chest"], "eq": "bodyweight", "diff": "intermediate",
         "str": "15-25min", "hyp": "20-40min", "end": "30-60min", "rec": 12},

        # ═══════════════════════ OLYMPIC LIFTS ═══════════════════════
        {"name": "Power Clean", "it": "Girata al Petto", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings", "back"], "sm": ["quadriceps", "shoulders", "traps"], "eq": "barbell", "diff": "advanced",
         "str": "1-5", "hyp": "3-6", "end": "6-8", "rec": 48},
        {"name": "Hang Clean", "it": "Clean dalla Posizione", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings"], "sm": ["quadriceps", "traps", "shoulders"], "eq": "barbell", "diff": "advanced",
         "str": "1-5", "hyp": "3-6", "end": "6-8", "rec": 48},
        {"name": "Clean and Jerk", "it": "Slancio", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings", "shoulders"], "sm": ["quadriceps", "core", "triceps"], "eq": "barbell", "diff": "advanced",
         "str": "1-3", "hyp": "3-5", "end": "5-8", "rec": 48},
        {"name": "Snatch", "it": "Strappo", "cat": "compound", "pat": "hinge",
         "pm": ["glutes", "hamstrings", "shoulders"], "sm": ["quadriceps", "core", "back"], "eq": "barbell", "diff": "advanced",
         "str": "1-3", "hyp": "3-5", "end": "5-8", "rec": 48},
    ]


# ═══════════════════════════════════════════════════════════════
# PERIODIZATION TEMPLATES (mantenute per knowledge_chain.py)
# ═══════════════════════════════════════════════════════════════

class PeriodizationTemplates:
    """Template di periodizzazione per diversi goal e durata."""

    @staticmethod
    def get_linear_periodization(weeks: int = 12) -> Dict[str, Any]:
        if weeks < 4:
            weeks = 4
        phases = []
        wc = 1
        hyp_w = max(2, weeks // 4)
        phases.append({'phase': 'Hypertrophy', 'weeks': hyp_w, 'reps': '8-12',
                       'intensity': '65-75%', 'rest': '60-90s', 'weeks_range': (wc, wc + hyp_w - 1)})
        wc += hyp_w
        str_w = max(2, weeks // 4)
        phases.append({'phase': 'Strength', 'weeks': str_w, 'reps': '4-6',
                       'intensity': '80-90%', 'rest': '120-180s', 'weeks_range': (wc, wc + str_w - 1)})
        wc += str_w
        pow_w = max(1, weeks // 6)
        phases.append({'phase': 'Power', 'weeks': pow_w, 'reps': '1-3',
                       'intensity': '90-95%', 'rest': '180-300s', 'weeks_range': (wc, wc + pow_w - 1)})
        wc += pow_w
        dl_w = max(1, weeks // 8)
        phases.append({'phase': 'Deload', 'weeks': dl_w, 'reps': '10-15',
                       'intensity': '50-60%', 'rest': '45-60s', 'weeks_range': (wc, wc + dl_w - 1)})
        return {'type': 'Linear Periodization', 'total_weeks': weeks, 'phases': phases,
                'ideal_for': ['Strength', 'beginner->intermediate->advanced']}

    @staticmethod
    def get_block_periodization(weeks: int = 12) -> Dict[str, Any]:
        if weeks < 4:
            weeks = 4
        bw = weeks // 3
        blocks = [
            {'block': 'Accumulation', 'weeks': bw, 'reps': '8-15', 'intensity': 'Bassa-Media',
             'weeks_range': (1, bw)},
            {'block': 'Intensification', 'weeks': bw, 'reps': '3-8', 'intensity': 'Media-Alta',
             'weeks_range': (bw + 1, bw * 2)},
            {'block': 'Realization', 'weeks': bw, 'reps': '1-5', 'intensity': 'Massima',
             'weeks_range': (bw * 2 + 1, weeks)},
        ]
        return {'type': 'Block Periodization', 'total_weeks': weeks, 'blocks': blocks,
                'ideal_for': ['Strength', 'Powerlifting', 'advanced']}

    @staticmethod
    def get_undulating_periodization(weeks: int = 12) -> Dict[str, Any]:
        if weeks < 4:
            weeks = 4
        microcycle = [
            {'day': 'Hypertrophy', 'reps': '8-12', 'intensity': '65-75%', 'rest': '60-90s'},
            {'day': 'Strength', 'reps': '3-5', 'intensity': '85-95%', 'rest': '180+s'},
            {'day': 'Power/Endurance', 'reps': '10-15', 'intensity': '60-70%', 'rest': '45-60s'},
        ]
        return {'type': 'Undulating Periodization', 'total_weeks': weeks,
                'microcycle': microcycle, 'ideal_for': ['Hypertrophy + Strength mix', 'Intermediate/Advanced']}

    @staticmethod
    def get_deload_week() -> Dict[str, Any]:
        return {'type': 'Deload Week', 'volume': '40-50%', 'intensity': '50-60%',
                'reps': '10-15', 'rest': '45-60s', 'frequency': 'Ogni 3-4 settimane'}


class ProgressionStrategies:
    """Strategie per progressione e overload progressivo."""

    STRATEGIES = {
        'weight_progression': {'name': 'Weight Progression', 'best_for': ['Strength']},
        'rep_progression': {'name': 'Rep Progression', 'best_for': ['Hypertrophy', 'Beginners']},
        'density_progression': {'name': 'Density Progression', 'best_for': ['Conditioning']},
        'tempo_progression': {'name': 'Tempo Progression', 'best_for': ['Hypertrophy']},
        'range_of_motion': {'name': 'ROM Progression', 'best_for': ['Functional']},
        'exercise_variation': {'name': 'Exercise Variation', 'best_for': ['Variety', 'Long-term']},
        'drop_sets_pyramids': {'name': 'Drop Sets & Pyramids', 'best_for': ['Hypertrophy']},
    }

    @staticmethod
    def get_strategy(name: str) -> Optional[Dict[str, Any]]:
        return ProgressionStrategies.STRATEGIES.get(name)

    @staticmethod
    def get_all_strategies() -> Dict[str, Any]:
        return ProgressionStrategies.STRATEGIES

    @staticmethod
    def recommend_for_goal(goal: str) -> List[str]:
        recs = {
            'strength': ['weight_progression', 'rep_progression', 'density_progression'],
            'hypertrophy': ['rep_progression', 'tempo_progression', 'drop_sets_pyramids'],
            'endurance': ['rep_progression', 'density_progression'],
            'fat_loss': ['density_progression', 'exercise_variation'],
            'functional': ['range_of_motion', 'exercise_variation'],
        }
        return recs.get(goal, ['rep_progression', 'weight_progression'])
