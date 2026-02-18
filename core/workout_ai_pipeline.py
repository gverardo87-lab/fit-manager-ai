"""
WorkoutAIPipeline - AI-augmented workout generation

Two generation paths:
1. DNA-driven (when imported cards exist): builds program from trainer's
   actual workout cards, adapting exercises for the specific client
2. Algorithmic fallback: uses WorkoutGeneratorV2 when no DNA available

The pipeline degrades gracefully:
- DNA available (>= 1 card): DNA-driven generation
- No DNA: pure algorithmic program
- No assessment: uses UI-provided profile
- LLM unavailable: DNA-driven still works (no AI enhancement)
"""

import json
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate

from core.config import MAIN_LLM_MODEL
from core.repositories import (
    AssessmentRepository, TrainerDNARepository, CardImportRepository
)
from core.workout_generator_v2 import WorkoutGeneratorV2
from core.periodization_models import get_periodization_plan, Goal
from core.methodology_chain import MethodologyChain
from core.error_handler import logger


# Enhancement prompt (optimized for llama3:8b context window)
ENHANCEMENT_PROMPT = PromptTemplate(
    template="""Sei un assistente che suggerisce modifiche al programma per allinearlo allo stile del trainer.

STILE TRAINER (DNA):
{style_context}

PATTERN DNA:
- Esercizi preferiti: {preferred_exercises}
- Schema set: {set_scheme}
- Filosofia accessori: {accessory_philosophy}
- Ordine esercizi: {ordering_style}

SESSIONE GENERATA:
{session_json}

CLIENTE: Goal={goal}, Level={level}, Limitazioni={limitazioni}

Suggerisci 1-3 modifiche SPECIFICHE in JSON valido (nessun testo prima o dopo):
{{
  "suggestions": [
    {{
      "type": "replace",
      "target_exercise_index": 0,
      "reason": "motivo della modifica",
      "new_exercise_name": "nome esercizio sostitutivo",
      "new_sets": 4,
      "new_reps": "8-12"
    }}
  ],
  "style_alignment_score": 0.7
}}

JSON:""",
    input_variables=[
        "style_context", "preferred_exercises", "set_scheme",
        "accessory_philosophy", "ordering_style", "session_json",
        "goal", "level", "limitazioni"
    ]
)


class WorkoutAIPipeline:
    """AI-augmented workout generation pipeline."""

    def __init__(self):
        self.workout_gen = WorkoutGeneratorV2()
        self.assessment_repo = AssessmentRepository()
        self.dna_repo = TrainerDNARepository()
        self.card_import_repo = CardImportRepository()
        self.methodology_chain = MethodologyChain()
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM with graceful fallback."""
        try:
            self.llm = OllamaLLM(model=MAIN_LLM_MODEL, temperature=0.3)
            self.llm.invoke("test")
            logger.info("WorkoutAIPipeline: LLM ready")
        except Exception as e:
            logger.warning(f"WorkoutAIPipeline: LLM unavailable ({e})")
            self.llm = None

    def generate_with_ai(
        self,
        client_id: int,
        client_profile: Dict[str, Any],
        weeks: int = 4,
        periodization_model: str = "linear",
        sessions_per_week: int = 3,
        use_assessment: bool = True,
        use_trainer_dna: bool = True,
    ) -> Dict[str, Any]:
        """
        Full AI-augmented generation pipeline.

        When DNA is available (>= 1 imported card), uses DNA-driven generation
        that builds the program from the trainer's actual workout cards.
        Falls back to algorithmic generation when no DNA available.
        """
        ai_metadata = {
            "assessment_used": False,
            "dna_used": False,
            "dna_driven": False,
            "ai_enhanced": False,
            "dna_level": "none",
            "style_alignment_score": 0.0,
            "suggestions_applied": 0,
            "dna_exercises_used": 0,
            "custom_exercises": 0,
        }

        # A) Enrich profile from assessment
        if use_assessment:
            enriched = self._enrich_from_assessment(client_id, client_profile)
            if enriched:
                client_profile = enriched
                ai_metadata["assessment_used"] = True

        # B) DNA-driven generation (when cards available)
        workout = None
        if use_trainer_dna:
            dna_summary = self.dna_repo.get_active_patterns()
            if dna_summary:
                ai_metadata["dna_level"] = dna_summary.dna_level

            if dna_summary and dna_summary.total_cards_imported >= 1:
                workout = self._generate_from_dna(
                    client_profile=client_profile,
                    weeks=weeks,
                    sessions_per_week=sessions_per_week,
                    periodization_model=periodization_model,
                )
                if workout and 'error' not in workout:
                    ai_metadata["dna_used"] = True
                    ai_metadata["dna_driven"] = True
                    # Count DNA vs custom exercises
                    for week_data in workout.get('weekly_schedule', {}).values():
                        for session in week_data.get('sessions', {}).values():
                            for ex in session.get('main_workout', []):
                                if ex.get('is_custom'):
                                    ai_metadata["custom_exercises"] += 1
                                else:
                                    ai_metadata["dna_exercises_used"] += 1
                        break  # count only week 1
                    logger.info("WorkoutAIPipeline: DNA-driven generation successful")
                else:
                    workout = None  # fall through to algorithmic

        # C) Algorithmic fallback
        if workout is None:
            workout = self.workout_gen.generate_professional_workout(
                client_profile=client_profile,
                weeks=weeks,
                periodization_model=periodization_model,
                sessions_per_week=sessions_per_week,
            )

        if 'error' in workout:
            return workout

        # D) AI Enhancement with LLM (optional, for all sessions in week 1)
        if use_trainer_dna and ai_metadata["dna_level"] != "none":
            dna_summary = self.dna_repo.get_active_patterns()
            if dna_summary:
                enhanced = self._ai_enhance_all_sessions(
                    workout, dna_summary, client_profile
                )
                if enhanced:
                    ai_metadata["ai_enhanced"] = True
                    ai_metadata["style_alignment_score"] = enhanced.get(
                        "alignment_score", 0.0
                    )
                    ai_metadata["suggestions_applied"] = enhanced.get(
                        "suggestions_applied", 0
                    )

        workout["ai_metadata"] = ai_metadata
        return workout

    # ==================================================================
    # DNA-DRIVEN GENERATION
    # ==================================================================

    def _generate_from_dna(
        self,
        client_profile: Dict[str, Any],
        weeks: int,
        sessions_per_week: int,
        periodization_model: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a workout program based on imported trainer cards.

        Reads actual exercise data from imported cards and builds a program
        that mirrors the trainer's style, adapted for the specific client.
        """
        try:
            # 1. Build template from imported cards
            dna_template = self._build_dna_template(sessions_per_week)
            if not dna_template:
                logger.warning("DNA generation: no template could be built")
                return None

            # 2. Adapt exercises for the client
            weekly_template = self._adapt_template_for_client(
                dna_template, client_profile
            )
            if not weekly_template:
                return None

            # 3. Get periodization plan
            goal_str = client_profile.get('goal', 'hypertrophy')
            goal_map = {
                'strength': Goal.STRENGTH,
                'hypertrophy': Goal.HYPERTROPHY,
                'endurance': Goal.ENDURANCE,
                'fat_loss': Goal.FAT_LOSS,
                'functional': Goal.ENDURANCE,
            }
            goal = goal_map.get(goal_str, Goal.HYPERTROPHY)

            periodization_plan = get_periodization_plan(
                model=periodization_model,
                weeks=weeks,
                goal=goal,
            )

            # 4. Apply periodization across weeks
            complete_program = self._apply_dna_periodization(
                weekly_template, periodization_plan, weeks
            )

            # 5. Add warmup/cooldown
            complete_program = self.workout_gen._add_smart_warmup_cooldown(
                complete_program
            )

            # 6. Build output in same format as WorkoutGeneratorV2
            # Detect split from card metadata
            cards = self.card_import_repo.get_all_cards()
            split_type = "dna_custom"
            if cards:
                meta = cards[0].get('parsed_metadata', {})
                if meta:
                    split_type = meta.get('detected_split') or "dna_custom"

            output = {
                'client_name': f"{client_profile.get('nome', '')} {client_profile.get('cognome', '')}".strip(),
                'goal': goal_str,
                'level': client_profile.get('level', 'intermediate'),
                'duration_weeks': weeks,
                'sessions_per_week': sessions_per_week,
                'split_type': split_type,
                'periodization_model': periodization_plan.model_name,
                'periodization_description': periodization_plan.description,
                'weekly_schedule': complete_program,
                'volume_analysis': self._simple_volume_analysis(weekly_template),
                'progressive_overload': self.workout_gen._generate_progression_guidelines(goal),
                'recovery_recommendations': self.workout_gen._generate_recovery_guidelines(goal),
                'notes': "Programma generato dal DNA del trainer - basato sulle schede importate.",
                'generated_date': datetime.now().isoformat(),
            }

            return output

        except Exception as e:
            logger.error(f"DNA generation failed: {e}")
            return None

    def _build_dna_template(
        self, sessions_per_week: int
    ) -> Optional[Dict[str, List[Dict]]]:
        """
        Build a weekly template from ALL imported cards.

        Merges exercises across cards, grouped by day.
        With multiple cards: exercises appearing more often get priority.
        """
        cards = self.card_import_repo.get_all_cards()
        if not cards:
            return None

        # Collect exercises by day from all cards
        day_exercises: Dict[str, List[Dict]] = {}

        for card in cards:
            exercises = card.get('parsed_exercises', [])
            if not exercises:
                continue

            for ex_data in exercises:
                day = ex_data.get('day_section') or 'GIORNO 1'
                day_exercises.setdefault(day, []).append(ex_data)

        if not day_exercises:
            return None

        # Sort days naturally (GIORNO 1, GIORNO 2, etc.)
        sorted_days = sorted(
            day_exercises.keys(),
            key=lambda d: int(re.search(r'\d+', d).group()) if re.search(r'\d+', d) else 0
        )

        # Limit to requested sessions_per_week
        if len(sorted_days) > sessions_per_week:
            sorted_days = sorted_days[:sessions_per_week]

        # If we have fewer days than requested, duplicate existing ones
        while len(sorted_days) < sessions_per_week:
            # Cycle through existing days
            idx = len(sorted_days) % len(day_exercises)
            source_day = list(day_exercises.keys())[idx]
            new_day = f"GIORNO {len(sorted_days) + 1}"
            day_exercises[new_day] = day_exercises[source_day]
            sorted_days.append(new_day)

        # Deduplicate and filter exercises within each day
        template = {}
        for i, day_key in enumerate(sorted_days, 1):
            exercises = day_exercises[day_key]

            # Deduplicate: keep best version of each exercise
            seen = {}
            for ex in exercises:
                name = ex.get('name', '').strip()
                if not name or len(name) < 3:
                    continue

                # Filter out junk entries (no sets, no reps, very low match)
                has_data = (
                    ex.get('sets') is not None or
                    ex.get('reps') is not None or
                    (ex.get('match_score', 0) or 0) >= 0.5
                )
                if not has_data:
                    continue

                name_lower = name.lower()
                existing = seen.get(name_lower)
                if existing is None:
                    seen[name_lower] = ex
                elif (ex.get('match_score', 0) or 0) > (existing.get('match_score', 0) or 0):
                    seen[name_lower] = ex

            template[f"day_{i}"] = list(seen.values())

        return template

    def _adapt_template_for_client(
        self,
        dna_template: Dict[str, List[Dict]],
        client_profile: Dict[str, Any],
    ) -> Optional[Dict[str, List[Dict]]]:
        """
        Adapt DNA template exercises for the specific client.

        For each exercise:
        1. Find in exercise_db (by canonical_id or fuzzy match)
        2. Check equipment/contraindication compatibility
        3. If incompatible, find alternative with same movement pattern
        4. If no DB match, include as custom exercise
        """
        equipment = client_profile.get('equipment', ['barbell', 'dumbbell'])
        limitazioni = client_profile.get('limitazioni', '')
        if isinstance(limitazioni, str):
            limitazioni = [l.strip() for l in limitazioni.split(';') if l.strip()]

        adapted = {}
        for day_key, exercises in dna_template.items():
            day_exercises = []
            used_ids = set()

            for ex_data in exercises:
                adapted_ex = self._adapt_single_exercise(
                    ex_data, equipment, limitazioni, used_ids
                )
                if adapted_ex:
                    ex_id = adapted_ex.get('id', '')
                    if ex_id:
                        used_ids.add(ex_id)
                    day_exercises.append(adapted_ex)

            if day_exercises:
                adapted[day_key] = day_exercises

        return adapted if adapted else None

    def _adapt_single_exercise(
        self,
        ex_data: Dict,
        equipment: List[str],
        limitazioni: List[str],
        used_ids: set,
    ) -> Optional[Dict]:
        """Adapt a single DNA exercise for the client."""
        db_exercise = None
        match_score = ex_data.get('match_score', 0) or 0

        # Try canonical_id first (from parser's fuzzy match)
        canonical_id = ex_data.get('canonical_id')
        if canonical_id and canonical_id not in used_ids:
            db_exercise = self.workout_gen.exercise_db.exercises.get(canonical_id)

        # Fuzzy match fallback - only if parser had a reasonable match score.
        # If parser couldn't match (score < 0.5), include as custom exercise
        # instead of risking a bad fuzzy match.
        if not db_exercise and match_score >= 0.5:
            db_exercise = self._fuzzy_find_exercise(
                ex_data.get('name', ''), used_ids
            )

        if db_exercise:
            # Check compatibility
            if self._is_compatible(db_exercise, equipment, limitazioni):
                return self._format_dna_exercise(db_exercise, ex_data)
            else:
                # Find alternative with same movement pattern
                alt = self._find_alternative(
                    db_exercise, equipment, limitazioni, used_ids
                )
                if alt:
                    return self._format_dna_exercise(alt, ex_data)

        # No DB match - include as custom exercise
        return self._format_custom_exercise(ex_data)

    def _fuzzy_find_exercise(
        self, name: str, used_ids: set
    ) -> Optional[Any]:
        """Find best matching exercise in DB using fuzzy matching."""
        if not name:
            return None

        name_lower = name.lower().strip()
        best_match = None
        best_score = 0.0

        for ex_id, ex in self.workout_gen.exercise_db.exercises.items():
            if ex_id in used_ids:
                continue
            for db_name in [ex.italian_name.lower(), ex.name.lower()]:
                score = SequenceMatcher(None, name_lower, db_name).ratio()
                if score > best_score:
                    best_score = score
                    best_match = ex

        if best_score >= 0.5:
            return best_match
        return None

    def _is_compatible(
        self, exercise, equipment: List[str], limitazioni: List[str]
    ) -> bool:
        """Check if exercise is compatible with client's equipment and limitations."""
        # Equipment check
        if exercise.equipment:
            if not any(eq in equipment for eq in exercise.equipment):
                if 'bodyweight' not in exercise.equipment:
                    return False

        # Contraindication check
        if limitazioni and exercise.contraindications:
            for limit in limitazioni:
                limit_lower = limit.lower()
                for contra in exercise.contraindications:
                    if limit_lower in contra.lower() or contra.lower() in limit_lower:
                        return False

        return True

    def _find_alternative(
        self, exercise, equipment: List[str],
        limitazioni: List[str], used_ids: set
    ) -> Optional[Any]:
        """Find an alternative exercise with the same movement pattern."""
        pattern = getattr(exercise, 'movement_pattern', '')
        if not pattern:
            return None

        for ex_id, ex in self.workout_gen.exercise_db.exercises.items():
            if ex_id in used_ids:
                continue
            if ex_id == exercise.id:
                continue
            if pattern not in getattr(ex, 'movement_pattern', ''):
                continue
            if self._is_compatible(ex, equipment, limitazioni):
                return ex

        return None

    def _format_dna_exercise(
        self, db_exercise, dna_data: Dict
    ) -> Dict[str, Any]:
        """
        Format exercise using DNA data for sets/reps (from trainer's card)
        enriched with DB metadata (muscles, video, form cues).
        """
        # Use DNA sets/reps (what the trainer actually programmed)
        sets = dna_data.get('sets')
        reps = dna_data.get('reps')
        rest = dna_data.get('rest_seconds')

        # Parse sets if string
        if isinstance(sets, str):
            try:
                sets = int(sets)
            except (ValueError, TypeError):
                sets = None

        return {
            'id': db_exercise.id,
            'name': db_exercise.name,
            'italian_name': db_exercise.italian_name,
            'description': getattr(db_exercise, 'description', ''),
            'primary_muscles': [m.value for m in db_exercise.primary_muscles],
            'secondary_muscles': [m.value for m in db_exercise.secondary_muscles],
            'equipment': db_exercise.equipment,
            'difficulty': db_exercise.difficulty.value,
            'sets': sets or 4,
            'reps': str(reps) if reps else '8-12',
            'rest_seconds': rest or 90,
            'intensity_percent': 0.7,
            'notes': getattr(db_exercise, 'notes', ''),
            'is_main_lift': False,
            'is_custom': False,
            'load_note': dna_data.get('load_note', ''),
            'video_url': getattr(db_exercise, 'video_url', ''),
            'video_thumbnail': getattr(db_exercise, 'video_thumbnail', ''),
            'image_url': getattr(db_exercise, 'image_url', ''),
            'setup_instructions': getattr(db_exercise, 'setup_instructions', []),
            'execution_steps': getattr(db_exercise, 'execution_steps', []),
            'breathing_cues': getattr(db_exercise, 'breathing_cues', ''),
            'form_cues': getattr(db_exercise, 'form_cues', []),
            'common_mistakes': getattr(db_exercise, 'common_mistakes', []),
            'safety_tips': getattr(db_exercise, 'safety_tips', []),
            'contraindications': db_exercise.contraindications,
            'movement_pattern': getattr(db_exercise, 'movement_pattern', ''),
            'plane_of_movement': getattr(db_exercise, 'plane_of_movement', []),
        }

    def _format_custom_exercise(self, dna_data: Dict) -> Dict[str, Any]:
        """
        Include exercise from DNA even without DB match.

        This is key: the trainer's exercises are always included,
        even if they're not in our exercise database.
        """
        name = dna_data.get('name', 'Esercizio')
        safe_id = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())

        sets = dna_data.get('sets')
        reps = dna_data.get('reps')
        rest = dna_data.get('rest_seconds')

        if isinstance(sets, str):
            try:
                sets = int(sets)
            except (ValueError, TypeError):
                sets = None

        return {
            'id': f"custom_{safe_id}",
            'name': name,
            'italian_name': name,
            'description': '',
            'primary_muscles': [],
            'secondary_muscles': [],
            'equipment': [],
            'difficulty': 'intermediate',
            'sets': sets or 4,
            'reps': str(reps) if reps else '8-12',
            'rest_seconds': rest or 90,
            'intensity_percent': 0.7,
            'notes': '',
            'is_main_lift': False,
            'is_custom': True,
            'load_note': dna_data.get('load_note', ''),
            'video_url': '',
            'video_thumbnail': '',
            'image_url': '',
            'setup_instructions': [],
            'execution_steps': [],
            'breathing_cues': '',
            'form_cues': [],
            'common_mistakes': [],
            'safety_tips': [],
            'contraindications': [],
            'movement_pattern': '',
            'plane_of_movement': [],
        }

    def _apply_dna_periodization(
        self,
        weekly_template: Dict[str, List[Dict]],
        periodization_plan,
        weeks: int,
    ) -> Dict:
        """
        Apply periodization to DNA-based template.

        Week 1 mirrors the trainer's card exactly.
        Subsequent weeks apply progressive overload via periodization model.
        """
        complete_program = {}
        deload_frequency = 4

        for week_num in range(1, weeks + 1):
            is_deload = (week_num % deload_frequency == 0) and week_num > 1
            week_params = periodization_plan.weeks[
                min(week_num - 1, len(periodization_plan.weeks) - 1)
            ]

            week_program = {}
            for day_key, exercises in weekly_template.items():
                adapted_exercises = []

                for exercise in exercises:
                    ex = dict(exercise)

                    if week_num == 1:
                        # Week 1: use exact DNA data (trainer's original programming)
                        ex['intensity_percent'] = week_params.intensity_percent
                    elif is_deload:
                        # Deload: reduce volume
                        ex['sets'] = max(2, int(ex.get('sets', 3) * 0.6))
                        ex['intensity_percent'] = max(
                            60, week_params.intensity_percent - 10
                        )
                        ex['notes'] = f"🔵 DELOAD - {ex.get('notes', '')}"
                    else:
                        # Progressive weeks: adjust intensity, keep DNA structure
                        ex['intensity_percent'] = week_params.intensity_percent
                        ex['rest_seconds'] = week_params.rest_seconds

                    adapted_exercises.append(ex)

                # Store as flat list - _add_smart_warmup_cooldown will wrap it
                week_program[day_key] = adapted_exercises

            complete_program[f'week_{week_num}'] = {
                'week_number': week_num,
                'focus': "Deload & Recovery" if is_deload else week_params.focus,
                'is_deload': is_deload,
                'intensity_percent': (
                    week_params.intensity_percent - 10 if is_deload
                    else week_params.intensity_percent
                ),
                'notes': (
                    "Settimana di scarico: volume ridotto, focus recupero e tecnica."
                    if is_deload else week_params.notes
                ),
                'sessions': week_program,
            }

        return complete_program

    def _simple_volume_analysis(
        self, weekly_template: Dict[str, List[Dict]]
    ) -> Dict:
        """Simple volume analysis for DNA-generated programs."""
        muscle_volume: Dict[str, int] = {}

        for day_key, exercises in weekly_template.items():
            for ex in exercises:
                sets = ex.get('sets', 3)
                if isinstance(sets, str):
                    try:
                        sets = int(sets)
                    except ValueError:
                        sets = 3
                for muscle in ex.get('primary_muscles', []):
                    muscle_volume[muscle] = muscle_volume.get(muscle, 0) + sets

        return {
            'total_sets_per_muscle': muscle_volume,
            'warnings': [],
            'recommendations': [],
            'status': 'dna_based',
        }

    # ==================================================================
    # AI ENHANCEMENT (LLM-based, applied to ALL sessions)
    # ==================================================================

    def _ai_enhance_all_sessions(
        self,
        workout: Dict[str, Any],
        dna_summary,
        client_profile: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to suggest modifications for ALL sessions in week 1.

        Enhancement is optional - the DNA-based program is already valid
        without LLM involvement.
        """
        if self.llm is None:
            return None

        try:
            style_context = self.methodology_chain.retrieve_style_context(
                goal=client_profile.get('goal', 'generic'),
                level=client_profile.get('level', 'intermediate'),
            )
            if not style_context:
                style_context = "Nessun contesto di stile disponibile"

            weekly = workout.get('weekly_schedule', {})
            week1 = weekly.get('week_1', {})
            sessions = week1.get('sessions', {})
            if not sessions:
                return None

            total_applied = 0
            total_score = 0.0
            sessions_enhanced = 0

            # Enhance each session in week 1
            for day_key, session in sessions.items():
                main_exercises = session.get('main_workout', [])
                if not main_exercises:
                    continue

                session_simple = [
                    {
                        "index": i,
                        "name": ex.get('italian_name', ex.get('name', '')),
                        "sets": ex.get('sets'),
                        "reps": ex.get('reps'),
                        "muscles": ex.get('primary_muscles', []),
                    }
                    for i, ex in enumerate(main_exercises)
                ]

                chain = ENHANCEMENT_PROMPT | self.llm
                response = chain.invoke({
                    "style_context": style_context[:1500],
                    "preferred_exercises": ", ".join(
                        dna_summary.preferred_exercises[:10]
                    ),
                    "set_scheme": dna_summary.preferred_set_scheme or "varied",
                    "accessory_philosophy": (
                        dna_summary.accessory_philosophy or "balanced"
                    ),
                    "ordering_style": (
                        dna_summary.ordering_style or "compound_first"
                    ),
                    "session_json": json.dumps(
                        session_simple, ensure_ascii=False
                    )[:1000],
                    "goal": client_profile.get('goal', ''),
                    "level": client_profile.get('level', ''),
                    "limitazioni": client_profile.get('limitazioni', 'Nessuna'),
                })

                suggestions_data = self._parse_suggestions(response)
                if suggestions_data:
                    applied = self._apply_suggestions(
                        workout, day_key, suggestions_data.get("suggestions", [])
                    )
                    total_applied += applied
                    total_score += suggestions_data.get(
                        "style_alignment_score", 0.0
                    )
                    sessions_enhanced += 1

            if sessions_enhanced > 0:
                return {
                    "alignment_score": total_score / sessions_enhanced,
                    "suggestions_applied": total_applied,
                }

            return None

        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
            return None

    def _parse_suggestions(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse suggestions JSON from LLM response."""
        text = response.strip()

        if "```" in text:
            parts = text.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{"):
                    text = cleaned
                    break

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return None

    def _apply_suggestions(
        self,
        workout: Dict[str, Any],
        day_key: str,
        suggestions: List[Dict[str, Any]],
    ) -> int:
        """Apply LLM suggestions to a specific day in week 1."""
        applied = 0
        week1 = workout.get('weekly_schedule', {}).get('week_1', {})
        sessions = week1.get('sessions', {})
        session = sessions.get(day_key, {})
        main_exercises = session.get('main_workout', [])

        for suggestion in suggestions[:3]:
            idx = suggestion.get("target_exercise_index")
            if idx is None or idx < 0 or idx >= len(main_exercises):
                continue

            stype = suggestion.get("type", "")
            exercise = main_exercises[idx]

            if stype == "replace":
                new_name = suggestion.get("new_exercise_name", "")
                reason = suggestion.get("reason", "")
                if new_name:
                    exercise['ai_suggestion'] = f"DNA suggerisce: {new_name}"
                    exercise['ai_reason'] = reason
                    if suggestion.get("new_sets"):
                        exercise['sets'] = suggestion['new_sets']
                    if suggestion.get("new_reps"):
                        exercise['reps'] = suggestion['new_reps']
                    applied += 1

            elif stype in ("modify_sets", "modify_reps"):
                if suggestion.get("new_sets"):
                    exercise['sets'] = suggestion['new_sets']
                if suggestion.get("new_reps"):
                    exercise['reps'] = suggestion['new_reps']
                exercise['ai_reason'] = suggestion.get(
                    "reason", "Adattamento stile trainer"
                )
                applied += 1

        return applied

    # ==================================================================
    # ASSESSMENT ENRICHMENT (unchanged)
    # ==================================================================

    def _enrich_from_assessment(
        self, client_id: int, profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Enrich client profile with assessment data."""
        initial = self.assessment_repo.get_initial(client_id)
        if not initial:
            return None

        enriched = dict(profile)

        # Limitations from assessment
        limitations_parts = []
        if initial.limitazioni:
            limitations_parts.append(initial.limitazioni)
        if initial.infortuni_attuali:
            limitations_parts.append(initial.infortuni_attuali)
        if initial.infortuni_pregessi:
            limitations_parts.append(f"Pregressi: {initial.infortuni_pregessi}")

        if limitations_parts:
            existing = enriched.get('limitazioni', '')
            if existing and existing != 'Nessuna':
                limitations_parts.insert(0, existing)
            enriched['limitazioni'] = "; ".join(limitations_parts)

        # Body composition
        if initial.peso_kg:
            enriched['peso_kg'] = initial.peso_kg
        if initial.altezza_cm:
            enriched['altezza_cm'] = initial.altezza_cm
        if initial.massa_grassa_pct:
            enriched['massa_grassa_pct'] = initial.massa_grassa_pct

        # Estimated 1RM (Epley formula)
        strength_data = {}
        if initial.panca_peso_kg and initial.panca_reps:
            strength_data['bench_1rm'] = round(
                initial.panca_peso_kg * (1 + initial.panca_reps / 30), 1
            )
        if initial.squat_macchina_peso_kg and initial.squat_macchina_reps:
            strength_data['squat_1rm'] = round(
                initial.squat_macchina_peso_kg * (1 + initial.squat_macchina_reps / 30), 1
            )
        if initial.rematore_peso_kg and initial.rematore_reps:
            strength_data['row_1rm'] = round(
                initial.rematore_peso_kg * (1 + initial.rematore_reps / 30), 1
            )

        followup = self.assessment_repo.get_latest_followup(client_id)
        if followup:
            if followup.peso_kg:
                enriched['peso_kg'] = followup.peso_kg
            if followup.panca_peso_kg and followup.panca_reps:
                strength_data['bench_1rm'] = round(
                    followup.panca_peso_kg * (1 + followup.panca_reps / 30), 1
                )

        if strength_data:
            enriched['strength_estimates'] = strength_data

        # Mobility notes
        mobility_notes = []
        for field in ['mobilita_spalle_note', 'mobilita_anche_note', 'mobilita_schiena_note']:
            val = getattr(initial, field, None)
            if val:
                mobility_notes.append(val)
        if mobility_notes:
            enriched['mobility_notes'] = "; ".join(mobility_notes)

        return enriched

    # ==================================================================
    # STATUS
    # ==================================================================

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Return status of all pipeline components."""
        dna_status = self.dna_repo.get_dna_status() or {}
        meth_status = self.methodology_chain.get_status()

        return {
            "llm_available": self.llm is not None,
            "dna_cards": dna_status.get('total_cards', 0),
            "dna_patterns": dna_status.get('total_patterns', 0),
            "dna_level": dna_status.get('dna_level', 'none'),
            "methodology_docs": meth_status.get('documents_count', 0),
            "methodology_available": meth_status.get('available', False),
        }
