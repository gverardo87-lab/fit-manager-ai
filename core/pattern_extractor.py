"""
PatternExtractor - Extract trainer methodology patterns from imported cards

Uses Ollama LLM to analyze workout cards and extract style patterns.
Falls back to algorithmic extraction if LLM is unavailable.

Extracted patterns feed into the Trainer DNA system.
"""

import json
from typing import List, Dict, Any, Optional

from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate

from core.config import MAIN_LLM_MODEL
from core.repositories import CardImportRepository, TrainerDNARepository
from core.card_parser import ParsedCard, ParsedExercise
from core.methodology_chain import MethodologyChain
from core.error_handler import logger


# LLM prompt for pattern extraction (optimized for llama3:8b context window)
EXTRACTION_PROMPT = PromptTemplate(
    template="""Analizza questa scheda allenamento ed estrai i pattern metodologici del trainer.

ESERCIZI DELLA SCHEDA:
{exercises_text}

METADATA:
- Goal rilevato: {goal}
- Split rilevato: {split}
- Sessioni/settimana: {sessions}

Rispondi SOLO con un JSON valido (nessun testo prima o dopo):
{{
  "preferred_compound_exercises": ["nome1", "nome2"],
  "accessory_philosophy": "high_volume" oppure "low_volume" oppure "balanced",
  "set_scheme": "5x5" oppure "4x8-12" oppure "3x10-15" oppure "varied",
  "uses_supersets": true oppure false,
  "progression_style": "linear" oppure "wavy" oppure "undulating",
  "ordering_style": "compound_first" oppure "antagonist_pairs" oppure "circuit",
  "notes_for_ai": "breve descrizione dello stile unico del trainer"
}}

JSON:""",
    input_variables=["exercises_text", "goal", "split", "sessions"]
)


class PatternExtractor:
    """Extracts trainer methodology patterns from parsed workout cards."""

    def __init__(self):
        self.llm = None
        self.card_import_repo = CardImportRepository()
        self.dna_repo = TrainerDNARepository()
        self.methodology_chain = MethodologyChain()
        self._init_llm()

    def _init_llm(self):
        """Try to initialize Ollama LLM. Graceful if unavailable."""
        try:
            self.llm = OllamaLLM(model=MAIN_LLM_MODEL, temperature=0.2)
            # Quick test to verify connection
            self.llm.invoke("test")
            logger.info("PatternExtractor: LLM initialized")
        except Exception as e:
            logger.warning(f"PatternExtractor: LLM unavailable ({e}), using algorithmic fallback")
            self.llm = None

    def extract_from_card(self, card_id: int, parsed_card: ParsedCard) -> Dict[str, Any]:
        """
        Extract patterns from a parsed card and save to Trainer DNA.

        Tries LLM first, falls back to algorithmic extraction.

        Returns:
            Dict with extracted patterns and metadata
        """
        if not parsed_card.exercises:
            return {"success": False, "error": "Nessun esercizio nella scheda"}

        # Try LLM extraction first
        patterns = None
        extraction_method = "algorithmic"

        if self.llm is not None:
            try:
                patterns = self._extract_with_llm(parsed_card)
                extraction_method = "llm"
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, falling back to algorithmic")

        # Fallback to algorithmic
        if patterns is None:
            patterns = self._extract_algorithmic(parsed_card)

        # Save patterns to Trainer DNA
        saved_count = self._save_patterns_to_dna(patterns, card_id)

        # Add to methodology vectorstore for RAG
        self.methodology_chain.add_card_to_rag(card_id, parsed_card, patterns)

        # Mark card as extracted
        self.card_import_repo.mark_pattern_extracted(card_id)

        return {
            "success": True,
            "method": extraction_method,
            "patterns": patterns,
            "patterns_saved": saved_count,
        }

    def _extract_with_llm(self, parsed_card: ParsedCard) -> Dict[str, Any]:
        """Extract patterns using LLM analysis."""
        # Build exercise text (limit to 15 for context window)
        exercises_text = self._format_exercises_for_prompt(parsed_card.exercises[:15])

        chain = EXTRACTION_PROMPT | self.llm
        response = chain.invoke({
            "exercises_text": exercises_text,
            "goal": parsed_card.metadata.detected_goal or "non specificato",
            "split": parsed_card.metadata.detected_split or "non specificato",
            "sessions": str(parsed_card.metadata.detected_sessions_per_week or "non specificato"),
        })

        # Parse JSON from response
        return self._parse_llm_response(response)

    def _format_exercises_for_prompt(self, exercises: List[ParsedExercise]) -> str:
        """Format exercises as readable text for the LLM prompt."""
        lines = []
        for i, ex in enumerate(exercises, 1):
            parts = [f"{i}. {ex.name}"]
            if ex.sets:
                parts.append(f"{ex.sets} serie")
            if ex.reps:
                parts.append(f"{ex.reps} reps")
            if ex.rest_seconds:
                parts.append(f"rec {ex.rest_seconds}s")
            if ex.load_note:
                parts.append(f"carico: {ex.load_note}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling common formatting issues."""
        text = response.strip()

        # Try to find JSON block in the response
        # Sometimes LLM wraps in ```json ... ```
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{"):
                    text = cleaned
                    break

        # Find the JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)

        raise ValueError(f"No valid JSON found in LLM response: {text[:200]}")

    def _extract_algorithmic(self, parsed_card: ParsedCard) -> Dict[str, Any]:
        """
        Fallback: extract patterns algorithmically from exercise data.

        Analyzes sets/reps distributions, exercise ordering, etc.
        """
        exercises = parsed_card.exercises

        # Compound exercises (exercises with canonical_id and high match)
        compound_names = [
            ex.name for ex in exercises
            if ex.canonical_id and ex.match_score >= 0.6
        ]

        # Analyze set/rep schemes
        sets_list = [ex.sets for ex in exercises if ex.sets]
        reps_list = [ex.reps for ex in exercises if ex.reps]

        # Determine set scheme
        if sets_list:
            avg_sets = sum(sets_list) / len(sets_list)
            if avg_sets >= 5:
                set_scheme = "5x5"
            elif avg_sets >= 4:
                set_scheme = "4x8-12"
            else:
                set_scheme = "3x10-15"
        else:
            set_scheme = "varied"

        # Determine volume philosophy
        total_exercises = len(exercises)
        if total_exercises >= 8:
            accessory_philosophy = "high_volume"
        elif total_exercises <= 4:
            accessory_philosophy = "low_volume"
        else:
            accessory_philosophy = "balanced"

        # Detect supersets (consecutive exercises with same rest or short rest)
        uses_supersets = False
        for ex in exercises:
            if ex.rest_seconds and ex.rest_seconds <= 15:
                uses_supersets = True
                break

        return {
            "preferred_compound_exercises": compound_names[:10],
            "accessory_philosophy": accessory_philosophy,
            "set_scheme": set_scheme,
            "uses_supersets": uses_supersets,
            "progression_style": "linear",  # default assumption
            "ordering_style": "compound_first",  # default assumption
            "notes_for_ai": f"Scheda con {total_exercises} esercizi, analisi algoritmica",
        }

    def _save_patterns_to_dna(self, patterns: Dict[str, Any], card_id: int) -> int:
        """Save extracted patterns to TrainerDNA repository."""
        saved = 0

        # Preferred exercises
        preferred = patterns.get("preferred_compound_exercises", [])
        if preferred:
            result = self.dna_repo.upsert_pattern(
                pattern_type="exercise_preference",
                pattern_key="compound_exercises",
                pattern_value=preferred,
                card_id=card_id
            )
            if result:
                saved += 1

        # Set scheme
        set_scheme = patterns.get("set_scheme")
        if set_scheme:
            result = self.dna_repo.upsert_pattern(
                pattern_type="set_scheme",
                pattern_key="primary_scheme",
                pattern_value=set_scheme,
                card_id=card_id
            )
            if result:
                saved += 1

        # Accessory philosophy
        philosophy = patterns.get("accessory_philosophy")
        if philosophy:
            result = self.dna_repo.upsert_pattern(
                pattern_type="accessory_philosophy",
                pattern_key="volume_approach",
                pattern_value=philosophy,
                card_id=card_id
            )
            if result:
                saved += 1

        # Ordering style
        ordering = patterns.get("ordering_style")
        if ordering:
            result = self.dna_repo.upsert_pattern(
                pattern_type="ordering_style",
                pattern_key="exercise_order",
                pattern_value=ordering,
                card_id=card_id
            )
            if result:
                saved += 1

        # Split preference (from card metadata)
        split_pref = patterns.get("split_preference")
        if split_pref:
            result = self.dna_repo.upsert_pattern(
                pattern_type="split_preference",
                pattern_key="preferred_split",
                pattern_value=split_pref,
                card_id=card_id
            )
            if result:
                saved += 1

        # Supersets usage
        uses_supersets = patterns.get("uses_supersets")
        if uses_supersets is not None:
            result = self.dna_repo.upsert_pattern(
                pattern_type="training_technique",
                pattern_key="uses_supersets",
                pattern_value=str(uses_supersets).lower(),
                card_id=card_id
            )
            if result:
                saved += 1

        # Progression style
        progression = patterns.get("progression_style")
        if progression:
            result = self.dna_repo.upsert_pattern(
                pattern_type="progression_style",
                pattern_key="primary_progression",
                pattern_value=progression,
                card_id=card_id
            )
            if result:
                saved += 1

        # AI notes
        notes = patterns.get("notes_for_ai")
        if notes:
            result = self.dna_repo.upsert_pattern(
                pattern_type="ai_notes",
                pattern_key=f"card_{card_id}_notes",
                pattern_value=notes,
                card_id=card_id
            )
            if result:
                saved += 1

        return saved
