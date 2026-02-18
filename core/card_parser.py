"""
CardParser - Import and parse workout cards from Excel/Word files

Parses Chiara's existing workout cards into structured data.
Handles varied formats with heuristic column detection and
fuzzy exercise name matching against the exercise database.
"""

import io
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from core.exercise_database import ExerciseDatabase


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ParsedExercise:
    """Single exercise extracted from a workout card."""
    name: str
    canonical_id: Optional[str] = None  # matched ID from exercise_db
    match_score: float = 0.0            # fuzzy match confidence
    sets: Optional[int] = None
    reps: Optional[str] = None          # "8-12" or "3x10" or "12"
    rest_seconds: Optional[int] = None
    load_note: Optional[str] = None     # "70%", "60kg", "RM"
    notes: Optional[str] = None
    row_index: int = 0


@dataclass
class ParsedCardMetadata:
    """Metadata detected from a workout card."""
    detected_goal: Optional[str] = None
    detected_split: Optional[str] = None
    detected_weeks: Optional[int] = None
    detected_sessions_per_week: Optional[int] = None
    trainer_notes: List[str] = field(default_factory=list)
    sheet_names: List[str] = field(default_factory=list)


@dataclass
class ParsedCard:
    """Complete result of parsing a workout card file."""
    raw_text: str
    exercises: List[ParsedExercise]
    metadata: ParsedCardMetadata
    parse_confidence: float = 0.0       # 0.0-1.0 overall confidence


# ============================================================================
# COLUMN DETECTION PATTERNS
# ============================================================================

# Column header patterns (case-insensitive)
EXERCISE_HEADERS = [
    "esercizio", "exercise", "nome", "name", "movimento", "movement",
    "es.", "ex.", "esercizi"
]
SETS_HEADERS = [
    "serie", "sets", "set", "s", "ser"
]
REPS_HEADERS = [
    "ripetizioni", "reps", "rep", "r", "rip", "ripet"
]
REST_HEADERS = [
    "recupero", "rest", "pausa", "rec", "rec."
]
LOAD_HEADERS = [
    "carico", "load", "peso", "weight", "kg", "%", "intensita", "intensity"
]
NOTE_HEADERS = [
    "note", "notes", "nota", "annotazioni", "commenti", "tempo"
]

# Goal detection keywords
GOAL_KEYWORDS = {
    "strength": ["forza", "strength", "1rm", "massimale", "max", "powerlifting"],
    "hypertrophy": ["ipertrofia", "hypertrophy", "massa", "muscle", "volume", "bodybuilding"],
    "fat_loss": ["dimagrimento", "fat loss", "definizione", "cut", "lean", "cardio"],
    "endurance": ["resistenza", "endurance", "stamina", "conditioning", "circuito"],
    "functional": ["funzionale", "functional", "mobilita", "mobility", "calisthenics"],
}

# Split detection keywords
SPLIT_KEYWORDS = {
    "full_body": ["full body", "total body", "tutto corpo", "completo"],
    "upper_lower": ["upper", "lower", "alto", "basso", "superiore", "inferiore"],
    "push_pull_legs": ["push", "pull", "legs", "ppl", "spinta", "tirata", "gambe"],
    "bro_split": ["petto", "schiena", "spalle", "braccia", "chest", "back", "arms"],
}


class CardParser:
    """Parses workout cards from Excel and Word files."""

    def __init__(self):
        self.exercise_db = ExerciseDatabase()
        # Build lookup of all exercise names for fuzzy matching
        self._exercise_names = {}
        for ex_id, ex in self.exercise_db.exercises.items():
            self._exercise_names[ex.italian_name.lower()] = ex_id
            self._exercise_names[ex.name.lower()] = ex_id

    def parse_file(self, file_bytes: bytes, filename: str) -> ParsedCard:
        """Auto-detect file format and parse."""
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        if ext in ("xlsx", "xls"):
            return self.parse_excel(file_bytes, filename)
        elif ext in ("docx", "doc"):
            return self.parse_word(file_bytes, filename)
        else:
            return ParsedCard(
                raw_text="",
                exercises=[],
                metadata=ParsedCardMetadata(),
                parse_confidence=0.0,
            )

    # ================================================================
    # EXCEL PARSING
    # ================================================================

    def parse_excel(self, file_bytes: bytes, filename: str) -> ParsedCard:
        """Parse an Excel workout card."""
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        all_exercises: List[ParsedExercise] = []
        raw_lines: List[str] = []
        metadata = ParsedCardMetadata(sheet_names=wb.sheetnames)

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue

            # Detect column layout
            col_map = self._detect_columns(rows)

            # Parse exercises from rows
            start_row = 1 if col_map["header_row"] == 0 else col_map["header_row"] + 1
            for i, row in enumerate(rows[start_row:], start=start_row):
                line = " | ".join(str(c) for c in row if c is not None)
                raw_lines.append(line)

                ex = self._parse_exercise_row(row, col_map, i)
                if ex:
                    all_exercises.append(ex)

            # Detect metadata from all cell values
            all_text = " ".join(
                str(cell) for row in rows for cell in row if cell is not None
            ).lower()
            self._detect_metadata(all_text, metadata)

        # Normalize exercise names against exercise_db
        for ex in all_exercises:
            canonical_id, score = self._normalize_exercise_name(ex.name)
            ex.canonical_id = canonical_id
            ex.match_score = score

        # Calculate confidence
        if all_exercises:
            avg_match = sum(e.match_score for e in all_exercises) / len(all_exercises)
            has_sets = sum(1 for e in all_exercises if e.sets is not None) / len(all_exercises)
            has_reps = sum(1 for e in all_exercises if e.reps is not None) / len(all_exercises)
            confidence = (avg_match * 0.5) + (has_sets * 0.25) + (has_reps * 0.25)
        else:
            confidence = 0.0

        return ParsedCard(
            raw_text="\n".join(raw_lines),
            exercises=all_exercises,
            metadata=metadata,
            parse_confidence=round(confidence, 2),
        )

    def _detect_columns(self, rows: list) -> dict:
        """Detect which columns contain exercise, sets, reps, etc."""
        col_map = {
            "exercise": None,
            "sets": None,
            "reps": None,
            "rest": None,
            "load": None,
            "notes": None,
            "header_row": 0,
        }

        # Try first 5 rows as potential headers
        for row_idx, row in enumerate(rows[:5]):
            if row is None:
                continue
            for col_idx, cell in enumerate(row):
                if cell is None:
                    continue
                cell_str = str(cell).strip().lower()

                if any(h == cell_str or cell_str.startswith(h) for h in EXERCISE_HEADERS):
                    col_map["exercise"] = col_idx
                    col_map["header_row"] = row_idx
                elif any(h == cell_str or cell_str.startswith(h) for h in SETS_HEADERS):
                    col_map["sets"] = col_idx
                elif any(h == cell_str or cell_str.startswith(h) for h in REPS_HEADERS):
                    col_map["reps"] = col_idx
                elif any(h == cell_str or cell_str.startswith(h) for h in REST_HEADERS):
                    col_map["rest"] = col_idx
                elif any(h == cell_str or cell_str.startswith(h) for h in LOAD_HEADERS):
                    col_map["load"] = col_idx
                elif any(h == cell_str or cell_str.startswith(h) for h in NOTE_HEADERS):
                    col_map["notes"] = col_idx

        # Fallback: if no exercise column detected, assume first text column
        if col_map["exercise"] is None and rows:
            for row in rows[1:4]:  # Check rows 1-3
                if row is None:
                    continue
                for col_idx, cell in enumerate(row):
                    if cell and isinstance(cell, str) and len(cell) > 3:
                        col_map["exercise"] = col_idx
                        break
                if col_map["exercise"] is not None:
                    break

            # Guess sets/reps from adjacent columns
            if col_map["exercise"] is not None:
                ex_col = col_map["exercise"]
                for row in rows[1:4]:
                    if row is None:
                        continue
                    for offset in range(1, min(5, len(row) - ex_col)):
                        val = row[ex_col + offset] if ex_col + offset < len(row) else None
                        if val is None:
                            continue
                        val_str = str(val).strip()
                        # Small integer = likely sets
                        if col_map["sets"] is None and val_str.isdigit() and 1 <= int(val_str) <= 10:
                            col_map["sets"] = ex_col + offset
                        # Range or number = likely reps
                        elif col_map["reps"] is None and re.match(r'^\d+[-x/]\d+$|^\d+$', val_str):
                            if col_map["sets"] is not None:
                                col_map["reps"] = ex_col + offset

        return col_map

    def _parse_exercise_row(self, row: tuple, col_map: dict, row_idx: int) -> Optional[ParsedExercise]:
        """Parse a single row into a ParsedExercise."""
        if col_map["exercise"] is None:
            return None

        ex_col = col_map["exercise"]
        if ex_col >= len(row) or row[ex_col] is None:
            return None

        name = str(row[ex_col]).strip()
        if len(name) < 2 or name.lower() in ("none", "-", ""):
            return None

        # Skip if it looks like a header or section title
        if name.lower() in EXERCISE_HEADERS:
            return None

        ex = ParsedExercise(name=name, row_index=row_idx)

        # Sets
        if col_map["sets"] is not None and col_map["sets"] < len(row):
            val = row[col_map["sets"]]
            if val is not None:
                try:
                    ex.sets = int(float(str(val)))
                except (ValueError, TypeError):
                    pass

        # Reps
        if col_map["reps"] is not None and col_map["reps"] < len(row):
            val = row[col_map["reps"]]
            if val is not None:
                ex.reps = str(val).strip()

        # Rest
        if col_map["rest"] is not None and col_map["rest"] < len(row):
            val = row[col_map["rest"]]
            if val is not None:
                try:
                    # Handle "60s", "90", "1:30"
                    rest_str = str(val).strip().lower().replace("s", "").replace("sec", "").replace("''", "")
                    if ":" in rest_str:
                        parts = rest_str.split(":")
                        ex.rest_seconds = int(parts[0]) * 60 + int(parts[1])
                    else:
                        ex.rest_seconds = int(float(rest_str))
                except (ValueError, TypeError):
                    pass

        # Load
        if col_map["load"] is not None and col_map["load"] < len(row):
            val = row[col_map["load"]]
            if val is not None:
                ex.load_note = str(val).strip()

        # Notes
        if col_map["notes"] is not None and col_map["notes"] < len(row):
            val = row[col_map["notes"]]
            if val is not None:
                ex.notes = str(val).strip()

        return ex

    # ================================================================
    # WORD PARSING
    # ================================================================

    def parse_word(self, file_bytes: bytes, filename: str) -> ParsedCard:
        """Parse a Word workout card."""
        try:
            import docx
        except ImportError:
            return ParsedCard(
                raw_text="python-docx non installato",
                exercises=[],
                metadata=ParsedCardMetadata(),
                parse_confidence=0.0,
            )

        doc = docx.Document(io.BytesIO(file_bytes))
        all_exercises: List[ParsedExercise] = []
        raw_lines: List[str] = []
        metadata = ParsedCardMetadata()

        # Extract from tables (primary source)
        for table in doc.tables:
            rows = []
            for tr in table.rows:
                row_data = tuple(cell.text.strip() for cell in tr.cells)
                rows.append(row_data)
                raw_lines.append(" | ".join(row_data))

            if rows:
                col_map = self._detect_columns(rows)
                start_row = col_map["header_row"] + 1 if col_map["header_row"] >= 0 else 0
                for i, row in enumerate(rows[start_row:], start=start_row):
                    ex = self._parse_exercise_row(row, col_map, i)
                    if ex:
                        all_exercises.append(ex)

        # Extract text paragraphs for metadata + notes
        all_text_parts = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                raw_lines.append(text)
                all_text_parts.append(text.lower())

        # Detect metadata
        all_text = " ".join(all_text_parts)
        self._detect_metadata(all_text, metadata)

        # Add paragraph text as trainer notes if no tables found
        if not all_exercises:
            for para_text in all_text_parts:
                if len(para_text) > 10:
                    metadata.trainer_notes.append(para_text)

        # Normalize exercise names
        for ex in all_exercises:
            canonical_id, score = self._normalize_exercise_name(ex.name)
            ex.canonical_id = canonical_id
            ex.match_score = score

        # Calculate confidence
        if all_exercises:
            avg_match = sum(e.match_score for e in all_exercises) / len(all_exercises)
            has_sets = sum(1 for e in all_exercises if e.sets is not None) / len(all_exercises)
            has_reps = sum(1 for e in all_exercises if e.reps is not None) / len(all_exercises)
            confidence = (avg_match * 0.5) + (has_sets * 0.25) + (has_reps * 0.25)
        else:
            confidence = 0.0

        return ParsedCard(
            raw_text="\n".join(raw_lines),
            exercises=all_exercises,
            metadata=metadata,
            parse_confidence=round(confidence, 2),
        )

    # ================================================================
    # SHARED HELPERS
    # ================================================================

    def _normalize_exercise_name(self, name: str) -> Tuple[str, float]:
        """
        Match exercise name against exercise database using fuzzy matching.

        Returns:
            (canonical_id or None, similarity_score 0.0-1.0)
        """
        name_lower = name.lower().strip()

        # Exact match
        if name_lower in self._exercise_names:
            return self._exercise_names[name_lower], 1.0

        # Fuzzy match
        best_id = None
        best_score = 0.0
        for db_name, ex_id in self._exercise_names.items():
            score = SequenceMatcher(None, name_lower, db_name).ratio()
            if score > best_score:
                best_score = score
                best_id = ex_id

        if best_score >= 0.6:
            return best_id, round(best_score, 2)

        return None, 0.0

    def _detect_metadata(self, text: str, metadata: ParsedCardMetadata):
        """Detect goal, split, and other metadata from text."""
        text_lower = text.lower()

        # Detect goal
        for goal, keywords in GOAL_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                metadata.detected_goal = goal
                break

        # Detect split
        for split, keywords in SPLIT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                metadata.detected_split = split
                break

        # Detect weeks
        weeks_match = re.search(r'(\d+)\s*(?:settiman[ae]|weeks?)', text_lower)
        if weeks_match:
            metadata.detected_weeks = int(weeks_match.group(1))

        # Detect sessions per week
        sessions_match = re.search(r'(\d+)\s*(?:volte|sessioni|allenamenti|x)\s*(?:a\s*)?(?:settimana|week)', text_lower)
        if sessions_match:
            metadata.detected_sessions_per_week = int(sessions_match.group(1))
