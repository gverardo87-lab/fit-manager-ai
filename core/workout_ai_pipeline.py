"""
WorkoutAIPipeline - AI-augmented workout generation

Simplified pipeline that delegates generation to WorkoutGenerator (3 modes)
and optionally enhances with AI coaching cues.

The pipeline degrades gracefully:
- With LLM: adds coaching cues and session narratives
- Without LLM: pure algorithmic generation (still excellent)
- With assessment: enriches client profile with body composition and strength data
- Without assessment: uses UI-provided profile as-is

AI boundaries: LLM generates ONLY coaching cues (technique, breathing).
NEVER generates or modifies exercise names, sets, or reps.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate

from core.config import MAIN_LLM_MODEL
from core.repositories import (
    AssessmentRepository, TrainerDNARepository, CardImportRepository
)
from core.workout_generator import WorkoutGenerator
from core.methodology_chain import MethodologyChain
from core.error_handler import logger


# Coaching cues prompt - technique tips and motivation ONLY
# NEVER generates exercise names (hallucination prevention)
COACHING_PROMPT = PromptTemplate(
    template="""Sei un coach esperto di fitness. Genera coaching cues tecnici per questa sessione.

SESSIONE: {session_name}
ESERCIZI:
{exercises_list}

CLIENTE: Goal={goal}, Level={level}

Per ogni esercizio, genera 1-2 cues tecnici BREVI (max 15 parole ciascuno).
NON modificare nomi esercizi, serie o ripetizioni.

Rispondi SOLO in JSON valido (nessun testo prima o dopo):
{{
  "session_narrative": "Breve descrizione motivazionale della sessione (1 frase)",
  "cues": [
    {{
      "exercise_index": 0,
      "technique_cue": "cue tecnico breve",
      "breathing_cue": "cue respirazione breve"
    }}
  ]
}}

JSON:""",
    input_variables=["session_name", "exercises_list", "goal", "level"]
)


class WorkoutAIPipeline:
    """AI-augmented workout generation pipeline.

    Delegates generation to WorkoutGenerator (supports 3 modes:
    archive, dna, combined) and optionally enhances with LLM
    coaching cues.
    """

    def __init__(self):
        self.generator = WorkoutGenerator()
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
        mode: str = 'archive',
        use_assessment: bool = True,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """Full AI-augmented generation pipeline.

        Args:
            client_id: Client ID for assessment/DNA lookup
            client_profile: Dict con nome, goal, level, equipment, limitazioni...
            weeks: Numero settimane (1-12)
            periodization_model: Nome modello periodizzazione
            sessions_per_week: Sessioni per settimana (1-6)
            mode: 'archive' (solo archivio), 'dna' (solo DNA), 'combined' (entrambi)
            use_assessment: Se True, arricchisce profilo da assessment
            use_ai: Se True, aggiunge coaching cues via LLM
        """
        ai_metadata = {
            "assessment_used": False,
            "mode": mode,
            "ai_enhanced": False,
            "coaching_cues_added": 0,
            "llm_available": self.llm is not None,
            "generated_at": datetime.now().isoformat(),
        }

        # 1. Enrich profile from assessment
        if use_assessment:
            enriched = self._enrich_from_assessment(client_id, client_profile)
            if enriched:
                client_profile = enriched
                ai_metadata["assessment_used"] = True

        # 2. Load DNA data if needed
        dna_data = None
        if mode in ('dna', 'combined'):
            dna_data = self._load_dna_data()
            if not dna_data or not dna_data.get('cards'):
                if mode == 'dna':
                    logger.warning("WorkoutAIPipeline: no DNA cards, falling back to archive")
                    mode = 'archive'
                    ai_metadata["mode"] = 'archive'

        # 3. Generate with WorkoutGenerator (handles all 3 modes)
        workout = self.generator.generate(
            client_id=client_id,
            profile=client_profile,
            weeks=weeks,
            sessions_per_week=sessions_per_week,
            periodization_model=periodization_model,
            mode=mode,
            dna_data=dna_data,
        )

        if 'error' in workout:
            return workout

        # 3. AI Enhancement - coaching cues only (optional)
        if use_ai and self.llm:
            cues_added = self._add_coaching_cues(workout, client_profile)
            if cues_added > 0:
                ai_metadata["ai_enhanced"] = True
                ai_metadata["coaching_cues_added"] = cues_added

        workout["ai_metadata"] = ai_metadata
        return workout

    # ==================================================================
    # DNA DATA LOADING
    # ==================================================================

    def _load_dna_data(self) -> Optional[Dict[str, Any]]:
        """Load DNA data from repositories for dna/combined modes."""
        try:
            cards_raw = self.card_import_repo.get_all_cards()
            if not cards_raw:
                return None

            # Convert cards to format expected by WeekPlanner
            cards = []
            for card in cards_raw:
                exercises = card.get('parsed_exercises', [])
                metadata = card.get('parsed_metadata', {}) or {}
                if exercises:
                    cards.append({
                        'exercises': exercises,
                        'metadata': metadata,
                    })

            if not cards:
                return None

            # Get DNA summary for combined mode scoring
            summary = self.dna_repo.get_active_patterns()

            return {
                'cards': cards,
                'summary': summary,
            }

        except Exception as e:
            logger.warning(f"Failed to load DNA data: {e}")
            return None

    # ==================================================================
    # AI COACHING CUES
    # ==================================================================

    def _add_coaching_cues(
        self,
        workout: Dict[str, Any],
        client_profile: Dict[str, Any],
    ) -> int:
        """Add coaching cues to week 1 sessions via LLM.

        Only generates technique and breathing cues.
        NEVER modifies exercise names, sets, or reps.
        """
        if self.llm is None:
            return 0

        try:
            weekly = workout.get('weekly_schedule', {})
            week1 = weekly.get('week_1', {})
            sessions = week1.get('sessions', [])
            if not sessions:
                return 0

            total_cues = 0

            for session in sessions:
                exercises = session.get('exercises', [])
                if not exercises:
                    continue

                # Build exercise list for prompt
                ex_lines = []
                for i, ex in enumerate(exercises):
                    name = ex.get('italian_name') or ex.get('name', '?')
                    sets = ex.get('sets', '?')
                    reps = ex.get('reps', '?')
                    ex_lines.append(f"{i+1}. {name} - {sets}x{reps}")

                chain = COACHING_PROMPT | self.llm
                response = chain.invoke({
                    "session_name": session.get('name', 'Sessione'),
                    "exercises_list": "\n".join(ex_lines),
                    "goal": client_profile.get('goal', 'general'),
                    "level": client_profile.get('level', 'intermediate'),
                })

                cues_data = self._parse_cues_json(response)
                if cues_data:
                    session['coaching_cues'] = cues_data.get('cues', [])
                    session['session_narrative'] = cues_data.get(
                        'session_narrative', ''
                    )
                    total_cues += len(cues_data.get('cues', []))

            return total_cues

        except Exception as e:
            logger.warning(f"Coaching cues generation failed: {e}")
            return 0

    def _parse_cues_json(self, response: str) -> Optional[Dict]:
        """Parse coaching cues JSON from LLM response."""
        text = response.strip()

        # Handle markdown code blocks
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{"):
                    text = cleaned
                    break

        # Extract JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return None

    # ==================================================================
    # ASSESSMENT ENRICHMENT
    # ==================================================================

    def _enrich_from_assessment(
        self, client_id: int, profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Enrich client profile with assessment data.

        Aggiunge al profilo: limitazioni, composizione corporea,
        stime 1RM (Epley), note mobilita'.
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
        for field_name in ['mobilita_spalle_note', 'mobilita_anche_note', 'mobilita_schiena_note']:
            val = getattr(initial, field_name, None)
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
