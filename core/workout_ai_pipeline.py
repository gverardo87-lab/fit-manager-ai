"""
WorkoutAIPipeline - AI-augmented workout generation

Combines:
1. Assessment data → enriched client profile
2. WorkoutGeneratorV2 → algorithmic program
3. Trainer DNA + Methodology RAG → AI style enhancement

The pipeline degrades gracefully:
- No assessment: uses UI-provided profile
- No DNA: returns pure algorithmic program
- LLM unavailable: returns algorithmic program

Usage:
    pipeline = WorkoutAIPipeline()
    result = pipeline.generate_with_ai(
        client_id=1,
        client_profile={...},
        weeks=8,
        periodization_model="block",
        sessions_per_week=4,
        use_assessment=True,
        use_trainer_dna=True,
    )
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate

from core.config import MAIN_LLM_MODEL
from core.repositories import AssessmentRepository, TrainerDNARepository
from core.workout_generator_v2 import WorkoutGeneratorV2
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

SESSIONE GENERATA (Settimana 1, Giorno 1):
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

        Returns the workout plan dict with additional 'ai_metadata' key
        containing enhancement info.
        """
        ai_metadata = {
            "assessment_used": False,
            "dna_used": False,
            "ai_enhanced": False,
            "dna_level": "none",
            "style_alignment_score": 0.0,
            "suggestions_applied": 0,
        }

        # A) Enrich profile from assessment
        if use_assessment:
            enriched = self._enrich_from_assessment(client_id, client_profile)
            if enriched:
                client_profile = enriched
                ai_metadata["assessment_used"] = True

        # B) Generate algorithmic program
        workout = self.workout_gen.generate_professional_workout(
            client_profile=client_profile,
            weeks=weeks,
            periodization_model=periodization_model,
            sessions_per_week=sessions_per_week,
        )

        if 'error' in workout:
            return workout

        # C) AI Enhancement with Trainer DNA
        if use_trainer_dna:
            dna_summary = self.dna_repo.get_active_patterns()
            if dna_summary and dna_summary.total_cards_imported >= 2:
                ai_metadata["dna_level"] = dna_summary.dna_level
                enhanced = self._ai_enhance_program(
                    workout, dna_summary, client_profile
                )
                if enhanced:
                    workout = enhanced["workout"]
                    ai_metadata["ai_enhanced"] = True
                    ai_metadata["dna_used"] = True
                    ai_metadata["style_alignment_score"] = enhanced.get("alignment_score", 0.0)
                    ai_metadata["suggestions_applied"] = enhanced.get("suggestions_applied", 0)
            elif dna_summary:
                ai_metadata["dna_level"] = dna_summary.dna_level

        workout["ai_metadata"] = ai_metadata
        return workout

    def _enrich_from_assessment(
        self, client_id: int, profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich client profile with assessment data.

        Reads initial + latest followup to populate:
        - Limitations from medical history
        - Estimated 1RM from strength tests (Epley formula)
        - Body composition for program adjustments
        """
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

        # Estimated 1RM from strength tests (Epley formula: peso * (1 + reps/30))
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

        # Check latest followup for updated values
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

        # Mobility notes for exercise selection
        mobility_notes = []
        for field in ['mobilita_spalle_note', 'mobilita_anche_note', 'mobilita_schiena_note']:
            val = getattr(initial, field, None)
            if val:
                mobility_notes.append(val)
        if mobility_notes:
            enriched['mobility_notes'] = "; ".join(mobility_notes)

        return enriched

    def _ai_enhance_program(
        self,
        workout: Dict[str, Any],
        dna_summary,
        client_profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM + Trainer DNA to suggest modifications to the generated program.

        Only modifies week 1, day 1 session (keeps rest intact for consistency).
        """
        if self.llm is None:
            return None

        try:
            # Get style context from methodology RAG
            style_context = self.methodology_chain.retrieve_style_context(
                goal=client_profile.get('goal', 'generic'),
                level=client_profile.get('level', 'intermediate'),
            )
            if not style_context:
                style_context = "Nessun contesto di stile disponibile"

            # Get first session for enhancement
            weekly = workout.get('weekly_schedule', {})
            week1 = weekly.get('week_1', {})
            sessions = week1.get('sessions', {})
            if not sessions:
                return None

            first_day_key = list(sessions.keys())[0]
            first_session = sessions[first_day_key]
            main_exercises = first_session.get('main_workout', [])

            if not main_exercises:
                return None

            # Simplify exercise data for prompt
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
                "style_context": style_context[:1500],  # limit for context window
                "preferred_exercises": ", ".join(dna_summary.preferred_exercises[:10]),
                "set_scheme": dna_summary.preferred_set_scheme or "varied",
                "accessory_philosophy": dna_summary.accessory_philosophy or "balanced",
                "ordering_style": dna_summary.ordering_style or "compound_first",
                "session_json": json.dumps(session_simple, ensure_ascii=False)[:1000],
                "goal": client_profile.get('goal', ''),
                "level": client_profile.get('level', ''),
                "limitazioni": client_profile.get('limitazioni', 'Nessuna'),
            })

            # Parse suggestions
            suggestions_data = self._parse_suggestions(response)
            if not suggestions_data:
                return None

            # Apply suggestions to workout
            applied = self._apply_suggestions(
                workout, first_day_key, suggestions_data.get("suggestions", [])
            )

            return {
                "workout": workout,
                "alignment_score": suggestions_data.get("style_alignment_score", 0.0),
                "suggestions_applied": applied,
            }

        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
            return None

    def _parse_suggestions(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse suggestions JSON from LLM response."""
        text = response.strip()

        # Handle ```json blocks
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
        suggestions: List[Dict[str, Any]]
    ) -> int:
        """
        Apply LLM suggestions to week 1 of the workout.

        Only applies safe modifications (set/rep changes, exercise name notes).
        Does NOT remove exercises or change program structure.
        """
        applied = 0
        week1 = workout.get('weekly_schedule', {}).get('week_1', {})
        sessions = week1.get('sessions', {})
        session = sessions.get(day_key, {})
        main_exercises = session.get('main_workout', [])

        for suggestion in suggestions[:3]:  # max 3 modifications
            idx = suggestion.get("target_exercise_index")
            if idx is None or idx < 0 or idx >= len(main_exercises):
                continue

            stype = suggestion.get("type", "")
            exercise = main_exercises[idx]

            if stype == "replace":
                # Add AI note but keep the exercise (safe approach)
                new_name = suggestion.get("new_exercise_name", "")
                reason = suggestion.get("reason", "")
                if new_name:
                    exercise['ai_suggestion'] = f"DNA suggerisce: {new_name}"
                    exercise['ai_reason'] = reason
                    # Apply set/rep changes if provided
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
                exercise['ai_reason'] = suggestion.get("reason", "Adattamento stile trainer")
                applied += 1

        return applied

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
