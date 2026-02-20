# core/workout_generator.py
"""
Workout Generator - Generatore unico di programmi di allenamento.

Tre modalita':
- 'archive': usa ExerciseArchive (174+ esercizi) + templates hardcoded
- 'dna': usa schede importate + pattern DNA del trainer
- 'combined': struttura DNA + archivio per selezione e fallback

Integra:
- ExerciseArchive per selezione esercizi con scoring multi-dimensionale
- SessionTemplate per struttura slot-based (max 8 esercizi per sessione)
- PeriodizationModels per periodizzazione scientifica (5 modelli)
- TrainerDNA per preferenze metodologiche del trainer
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path
import json

from core.error_handler import logger
from core.exercise_archive import ExerciseArchive, ScoredExercise
from core.session_template import SessionTemplate, WeekPlanner, TemplateSlot
from core.periodization_models import get_periodization_plan, Goal, PeriodizationPlan


class WorkoutGenerator:
    """Generatore unico di programmi di allenamento.

    Tre modalita':
    - 'archive': usa solo ExerciseArchive + templates hardcoded
    - 'dna': usa solo schede importate + pattern DNA
    - 'combined': struttura DNA + archivio per selezione/fallback
    """

    def __init__(self):
        self.archive = ExerciseArchive()
        self.planner = WeekPlanner()

        # Volume tracking (sets/settimana per muscolo — evidenza scientifica)
        self.optimal_volume = {
            'chest': (12, 20), 'back': (14, 22), 'shoulders': (12, 18),
            'quadriceps': (12, 20), 'hamstrings': (10, 16), 'glutes': (12, 20),
            'biceps': (8, 14), 'triceps': (10, 16), 'calves': (12, 18),
        }

    def generate(self, client_id: int, profile: Dict[str, Any],
                 weeks: int = 4, sessions_per_week: int = 3,
                 periodization_model: str = 'linear',
                 mode: str = 'archive',
                 dna_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Genera programma completo.

        Args:
            client_id: ID cliente
            profile: {
                'nome': str, 'cognome': str,
                'goal': str, 'level': str,
                'equipment': List[str],
                'limitazioni': List[str] o str
            }
            weeks: Durata in settimane (1-52)
            sessions_per_week: Sessioni per settimana (1-7)
            periodization_model: 'linear'|'block'|'dup'|'conjugate'|'rpe'
            mode: 'archive'|'dna'|'combined'
            dna_data: {
                'cards': List[dict],        # schede parsate
                'summary': dict             # TrainerDNASummary
            } (necessario per mode='dna' o 'combined')
        """
        logger.info(f"WorkoutGenerator: mode={mode}, weeks={weeks}, "
                     f"sessions={sessions_per_week}, model={periodization_model}")

        # 1. Prepara contesto selezione
        context = self._build_context(profile, dna_data, mode)

        # 2. Mappa goal
        goal = self._map_goal(profile.get('goal', 'strength'))

        # 3. Ottieni templates per la settimana
        week_templates = self._get_week_templates(
            mode, sessions_per_week, profile.get('level', 'intermediate'), dna_data
        )

        # 4. Genera piano periodizzazione
        periodization = get_periodization_plan(
            model=periodization_model, weeks=weeks, goal=goal
        )

        # 5. Riempi ogni sessione e applica periodizzazione
        weekly_schedule = {}
        for week_num in range(1, weeks + 1):
            week_params = periodization.weeks[week_num - 1]
            week_sessions = {}

            for i, template in enumerate(week_templates):
                day_key = f"day_{i + 1}"
                session = self._fill_session(template, context, goal, mode)

                # Applica periodizzazione
                session = self._apply_week_params(session, week_params)

                # Aggiungi warmup/cooldown
                week_sessions[day_key] = {
                    'name': template.name,
                    'warmup': self._get_warmup(),
                    'main_workout': session,
                    'cooldown': self._get_cooldown(),
                }

            weekly_schedule[f'week_{week_num}'] = {
                'week_number': week_num,
                'focus': week_params.focus,
                'is_deload': week_params.is_deload,
                'intensity_percent': week_params.intensity_percent,
                'notes': week_params.notes,
                'sessions': week_sessions,
            }

        # 6. Volume analysis
        volume_report = self._analyze_volume(week_templates, context, goal, mode)

        # 7. Determina split type
        split_map = {1: 'full_body', 2: 'full_body', 3: 'full_body',
                     4: 'upper_lower', 5: 'push_pull_legs', 6: 'push_pull_legs'}
        split_type = split_map.get(sessions_per_week, 'full_body')

        # 8. Output
        return {
            'client_name': f"{profile.get('nome', '')} {profile.get('cognome', '')}".strip(),
            'goal': goal.value,
            'level': profile.get('level', 'intermediate'),
            'duration_weeks': weeks,
            'sessions_per_week': sessions_per_week,
            'split_type': split_type,
            'periodization_model': periodization.model_name,
            'periodization_description': periodization.description,
            'generation_mode': mode,
            'weekly_schedule': weekly_schedule,
            'volume_analysis': volume_report,
            'progressive_overload': self._get_progression_guidelines(goal),
            'recovery_recommendations': self._get_recovery_guidelines(),
            'notes': self._get_program_notes(profile),
            'generated_date': datetime.now().isoformat(),
        }

    # ─────────────── CONTESTO E MAPPING ───────────────

    def _build_context(self, profile: Dict, dna_data: Optional[Dict],
                       mode: str) -> Dict[str, Any]:
        """Costruisce il contesto di selezione per l'archivio."""
        # Parse limitazioni (stringa o lista)
        limitazioni = profile.get('limitazioni', [])
        if isinstance(limitazioni, str):
            limitazioni = [l.strip() for l in limitazioni.split(',') if l.strip()]

        context = {
            'client_level': profile.get('level', 'intermediate'),
            'available_equipment': profile.get('equipment', ['barbell', 'dumbbell', 'bodyweight']),
            'contraindications': limitazioni,
            'recently_used': set(),
            'dna_preferences': None,
            'goal': profile.get('goal', 'strength'),
        }

        # In modalita' combined, DNA aggiunge bonus scoring
        if mode == 'combined' and dna_data and dna_data.get('summary'):
            summary = dna_data['summary']
            if isinstance(summary, dict):
                context['dna_preferences'] = summary
            else:
                # Se e' un oggetto Pydantic (TrainerDNASummary)
                context['dna_preferences'] = summary.model_dump() if hasattr(summary, 'model_dump') else vars(summary)

        return context

    def _map_goal(self, goal_str: str) -> Goal:
        """Mappa stringa goal in enum Goal."""
        goal_map = {
            'strength': Goal.STRENGTH, 'forza': Goal.STRENGTH,
            'hypertrophy': Goal.HYPERTROPHY, 'ipertrofia': Goal.HYPERTROPHY, 'massa': Goal.HYPERTROPHY,
            'fat_loss': Goal.FAT_LOSS, 'dimagrimento': Goal.FAT_LOSS,
            'endurance': Goal.ENDURANCE, 'resistenza': Goal.ENDURANCE,
            'power': Goal.POWER, 'potenza': Goal.POWER,
            'functional': Goal.STRENGTH,
        }
        return goal_map.get(goal_str.lower(), Goal.STRENGTH)

    def _get_week_templates(self, mode: str, sessions_per_week: int,
                            level: str, dna_data: Optional[Dict]) -> List[SessionTemplate]:
        """Ottieni templates della settimana in base alla modalita'."""
        if mode == 'archive':
            return self.planner.plan_week_from_archive(sessions_per_week, level)

        elif mode == 'dna':
            if dna_data and dna_data.get('cards'):
                templates = self.planner.plan_week_from_dna(dna_data['cards'])
                if templates:
                    return templates[:sessions_per_week]
            # Fallback ad archive se non ci sono schede
            logger.warning("WorkoutGenerator: no DNA cards, falling back to archive")
            return self.planner.plan_week_from_archive(sessions_per_week, level)

        else:  # combined
            if dna_data and dna_data.get('cards'):
                return self.planner.plan_week_combined(
                    sessions_per_week, level, dna_data['cards']
                )
            return self.planner.plan_week_from_archive(sessions_per_week, level)

    # ─────────────── FILL SESSION ───────────────

    def _fill_session(self, template: SessionTemplate, context: Dict,
                      goal: Goal, mode: str) -> List[Dict]:
        """Riempi gli slot del template con esercizi concreti."""
        exercises = []
        used_ids: Set[int] = set()

        for slot in template.slots:
            exercise_entry = None

            if mode == 'dna' and slot.sets and slot.reps:
                # STRADA B: usa l'esercizio dalla scheda DNA
                exercise_entry = self._resolve_dna_exercise(slot, context, goal, used_ids)
            else:
                # STRADA A/C: seleziona dall'archivio con scoring
                candidates = self.archive.select_for_slot(
                    slot.movement_pattern, slot.target_muscles, context
                )
                # Escludi gia' usati in questa sessione
                candidates = [c for c in candidates if c.exercise['id'] not in used_ids]

                if candidates:
                    best = candidates[0]
                    is_main = slot.role in ('main_compound',)
                    exercise_entry = self._format_exercise(
                        best.exercise, goal, is_main, slot
                    )
                    used_ids.add(best.exercise['id'])

            if exercise_entry:
                exercises.append(exercise_entry)
            elif slot.required:
                logger.warning(f"WorkoutGenerator: no exercise found for slot "
                               f"{slot.movement_pattern} in '{template.name}'")

        return exercises

    def _resolve_dna_exercise(self, slot: TemplateSlot, context: Dict,
                               goal: Goal, used_ids: Set[int]) -> Optional[Dict]:
        """Risolvi esercizio DNA: cerca nell'archivio, fallback custom."""
        # Cerca nell'archivio per pattern
        candidates = self.archive.select_for_slot(
            slot.movement_pattern, slot.target_muscles, context
        )
        candidates = [c for c in candidates if c.exercise['id'] not in used_ids]

        if candidates:
            best = candidates[0]
            is_main = slot.role in ('main_compound',)
            entry = self._format_exercise(best.exercise, goal, is_main, slot)
            # Sovrascrivi con set/rep del DNA
            if slot.sets:
                entry['sets'] = slot.sets
            if slot.reps:
                entry['reps'] = slot.reps
            used_ids.add(best.exercise['id'])
            return entry

        # Fallback: esercizio custom generico
        return {
            'id': None,
            'name': f"Custom ({slot.movement_pattern})",
            'italian_name': None,
            'primary_muscles': slot.target_muscles,
            'secondary_muscles': [],
            'equipment': 'bodyweight',
            'difficulty': context.get('client_level', 'intermediate'),
            'sets': slot.sets or 3,
            'reps': slot.reps or '8-12',
            'rest_seconds': 90,
            'is_main_lift': False,
            'notes': f'DNA exercise - {slot.movement_pattern}',
            'is_custom': True,
        }

    def _format_exercise(self, exercise: Dict, goal: Goal,
                         is_main: bool, slot: Optional[TemplateSlot] = None) -> Dict:
        """Formatta esercizio per l'output."""
        # Determina sets/reps in base al goal
        sets, reps = self._get_sets_reps(exercise, goal, is_main)

        # Se lo slot DNA ha set/rep, usali
        if slot and slot.sets:
            sets = slot.sets
        if slot and slot.reps:
            reps = slot.reps

        return {
            'id': exercise.get('id'),
            'name': exercise.get('name', ''),
            'italian_name': exercise.get('italian_name'),
            'primary_muscles': exercise.get('primary_muscles', []),
            'secondary_muscles': exercise.get('secondary_muscles', []),
            'equipment': exercise.get('equipment', 'bodyweight'),
            'difficulty': exercise.get('difficulty', 'intermediate'),
            'sets': sets,
            'reps': reps,
            'rest_seconds': 180 if is_main else 90,
            'is_main_lift': is_main,
            'notes': '',
            'movement_pattern': exercise.get('movement_pattern', ''),
            'contraindications': exercise.get('contraindications', []),
        }

    def _get_sets_reps(self, exercise: Dict, goal: Goal, is_main: bool) -> tuple:
        """Determina sets e reps in base al goal e ruolo."""
        if goal == Goal.STRENGTH:
            sets = 5 if is_main else 3
            reps = exercise.get('rep_range_strength', '3-6') or '3-6'
        elif goal == Goal.HYPERTROPHY:
            sets = 4 if is_main else 3
            reps = exercise.get('rep_range_hypertrophy', '8-12') or '8-12'
        elif goal == Goal.ENDURANCE:
            sets = 3
            reps = exercise.get('rep_range_endurance', '15-20') or '15-20'
        elif goal == Goal.FAT_LOSS:
            sets = 3
            reps = exercise.get('rep_range_hypertrophy', '10-15') or '10-15'
        else:  # POWER
            sets = 4 if is_main else 3
            reps = exercise.get('rep_range_strength', '3-5') or '3-5'
        return sets, reps

    # ─────────────── PERIODIZZAZIONE ───────────────

    def _apply_week_params(self, exercises: List[Dict],
                           week_params) -> List[Dict]:
        """Applica parametri periodizzazione a una sessione."""
        result = []
        for ex in exercises:
            ex_copy = ex.copy()
            if week_params.is_deload:
                # Deload: meno serie, meno intensita'
                ex_copy['sets'] = max(2, ex_copy['sets'] - 1)
                ex_copy['intensity_percent'] = week_params.intensity_percent
                ex_copy['notes'] = f"DELOAD - {ex_copy['notes']}"
            else:
                if ex_copy['is_main_lift']:
                    ex_copy['sets'] = week_params.volume_sets
                else:
                    ex_copy['sets'] = max(2, week_params.volume_sets - 1)
                ex_copy['reps'] = f"{week_params.reps_per_set[0]}-{week_params.reps_per_set[1]}"
                ex_copy['rest_seconds'] = week_params.rest_seconds
                ex_copy['intensity_percent'] = week_params.intensity_percent
            result.append(ex_copy)
        return result

    # ─────────────── VOLUME ANALYSIS ───────────────

    def _analyze_volume(self, templates: List[SessionTemplate], context: Dict,
                        goal: Goal, mode: str) -> Dict[str, Any]:
        """Analizza volume settimanale per gruppo muscolare."""
        muscle_sets: Dict[str, int] = {}

        for template in templates:
            session = self._fill_session(template, context, goal, mode)
            for ex in session:
                for muscle in ex.get('primary_muscles', []):
                    muscle_sets[muscle] = muscle_sets.get(muscle, 0) + ex.get('sets', 3)
                for muscle in ex.get('secondary_muscles', []):
                    muscle_sets[muscle] = muscle_sets.get(muscle, 0) + max(1, ex.get('sets', 3) // 2)

        report = {}
        for muscle, total_sets in sorted(muscle_sets.items()):
            optimal = self.optimal_volume.get(muscle)
            if optimal:
                status = 'OK' if optimal[0] <= total_sets <= optimal[1] else \
                         'LOW' if total_sets < optimal[0] else 'HIGH'
                report[muscle] = {
                    'sets_per_week': total_sets,
                    'optimal_range': f"{optimal[0]}-{optimal[1]}",
                    'status': status,
                }
            else:
                report[muscle] = {'sets_per_week': total_sets, 'status': 'OK'}

        return report

    # ─────────────── WARMUP / COOLDOWN ───────────────

    def _get_warmup(self) -> Dict:
        return {
            'duration_minutes': 10,
            'exercises': [
                {'name': 'Light Cardio', 'duration': '5 min',
                 'notes': 'Tapis roulant, bike, o jumping jacks'},
                {'name': 'Dynamic Stretching', 'duration': '5 min',
                 'notes': 'Leg swings, arm circles, torso twists'},
            ]
        }

    def _get_cooldown(self) -> Dict:
        return {
            'duration_minutes': 10,
            'exercises': [
                {'name': 'Static Stretching', 'duration': '5 min',
                 'notes': 'Focus muscoli allenati'},
                {'name': 'Foam Rolling', 'duration': '5 min',
                 'notes': 'Auto-miofascial release'},
            ]
        }

    # ─────────────── GUIDELINES ───────────────

    def _get_progression_guidelines(self, goal: Goal) -> str:
        guidelines = {
            Goal.STRENGTH: (
                "**Progressive Overload (Forza):**\n"
                "- Aumenta peso 2.5-5% ogni settimana (se completi tutte le rep)\n"
                "- Se non riesci, mantieni peso\n- Deload ogni 4 settimane (-10% peso)"
            ),
            Goal.HYPERTROPHY: (
                "**Progressive Overload (Ipertrofia):**\n"
                "- Aumenta reps prima (double progression)\n"
                "- Quando raggiungi reps massime, aumenta peso 2.5%\n"
                "- Focus: volume totale (sets x reps x peso)"
            ),
            Goal.ENDURANCE: (
                "**Progressive Overload (Resistenza):**\n"
                "- Aumenta reps/durata progressivamente\n"
                "- Riduci tempi recupero gradualmente"
            ),
        }
        return guidelines.get(goal, guidelines[Goal.STRENGTH])

    def _get_recovery_guidelines(self) -> str:
        return (
            "**Recupero Ottimale:**\n"
            "- Sonno: 7-9 ore/notte\n"
            "- Proteine: 1.6-2.2g/kg peso corporeo\n"
            "- Idratazione: 2-3L acqua/giorno\n"
            "- Giorni riposo: almeno 1-2/settimana"
        )

    def _get_program_notes(self, profile: Dict) -> str:
        nome = profile.get('nome', 'Cliente')
        goal = profile.get('goal', 'strength').upper()
        level = profile.get('level', 'intermediate').capitalize()
        notes = f"**Programma per {nome}** - Obiettivo: {goal}, Livello: {level}"
        limitazioni = profile.get('limitazioni', '')
        if limitazioni:
            if isinstance(limitazioni, list):
                limitazioni = ', '.join(limitazioni)
            notes += f"\nLimitazioni: {limitazioni}"
            notes += "\nIMPORTANTE: Se un esercizio causa dolore, FERMATI."
        return notes
