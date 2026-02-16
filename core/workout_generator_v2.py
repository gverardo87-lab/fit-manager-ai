# core/workout_generator_v2.py
"""
Workout Generator V2 - Versione Professionale REFACTORED

Integra:
- Database UNIFICATO 500+ esercizi (exercise_database - UNICA FONTE)
- 5 Modelli periodizzazione scientifica (periodization_models)
- Output strutturato e professionale
- Progressive overload automatico

REFACTOR V2:
- Eliminato exercise_library_extended e exercise_library_pro
- Usa SOLO exercise_database con metodi smart
- Selezione intelligente invece di hardcode
- Validazione equipment e controindicazioni
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.exercise_database import exercise_db, MuscleGroup, DifficultyLevel
from core.periodization_models import get_periodization_plan, Goal, PeriodizationPlan


class WorkoutGeneratorV2:
    """
    Generatore professionale di programmi allenamento - REFACTORED V3

    Features:
    - Selezione esercizi da database UNIFICATO 500+
    - Periodizzazione scientifica (5 modelli)
    - EXERCISE ROTATION: Varianti automatiche ogni 2-4 settimane
    - SMART WARM-UP: Riscaldamento specifico + specific warm-up sets
    - DELOAD AUTOMATION: Settimana scarico ogni 3-4 settimane
    - VOLUME TRACKING: Calcolo sets ottimali per muscolo
    - Progressive overload tracking
    - Validazione equipment e controindicazioni
    - Output professionale
    """

    def __init__(self):
        """Inizializza generatore con database esercizi UNIFICATO"""
        print("[INIT] Caricamento database esercizi UNIFICATO V3...")
        self.exercise_db = exercise_db  # Usa istanza globale
        
        # Volume tracking guidelines (sets/week per muscolo - evidenza scientifica)
        self.optimal_volume_ranges = {
            MuscleGroup.CHEST: (12, 20),      # 12-20 sets/week
            MuscleGroup.BACK: (14, 22),       # Più volume per back
            MuscleGroup.SHOULDERS: (12, 18),
            MuscleGroup.QUADRICEPS: (12, 20),
            MuscleGroup.HAMSTRINGS: (10, 16),
            MuscleGroup.GLUTES: (12, 20),
            MuscleGroup.BICEPS: (8, 14),      # Isolation
            MuscleGroup.TRICEPS: (10, 16),
            MuscleGroup.CALVES: (12, 18),
            MuscleGroup.CORE: (0, 0),  # Non tracciato (fatto ogni sessione)
        }
        
        print(f"[OK] Caricati {self.exercise_db.count_exercises()} esercizi")
        print("[OK] Volume tracking attivo: 10-22 sets/week per muscolo")

    def generate_professional_workout(
        self,
        client_profile: Dict[str, Any],
        weeks: int = 4,
        periodization_model: str = "linear",
        sessions_per_week: int = 3
    ) -> Dict[str, Any]:
        """
        Genera programma allenamento PROFESSIONALE

        Args:
            client_profile: {
                'nome': str,
                'cognome': str,
                'goal': 'strength' | 'hypertrophy' | 'fat_loss' | 'endurance',
                'level': 'beginner' | 'intermediate' | 'advanced',
                'disponibilita_giorni': int (3-6),
                'equipment': List[str],  # es. ['barbell', 'dumbbell', 'bodyweight']
                'limitazioni': List[str]  # es. ['collo', 'ginocchio']
            }
            weeks: Durata programma (4-12 settimane)
            periodization_model: 'linear' | 'block' | 'dup' | 'conjugate' | 'rpe'
            sessions_per_week: Sessioni/settimana (3-6)

        Returns:
            Programma completo strutturato
        """

        # Step 1: Map goal a enum
        goal_map = {
            'strength': Goal.STRENGTH,
            'forza': Goal.STRENGTH,
            'hypertrophy': Goal.HYPERTROPHY,
            'ipertrofia': Goal.HYPERTROPHY,
            'massa': Goal.HYPERTROPHY,
            'fat_loss': Goal.FAT_LOSS,
            'dimagrimento': Goal.FAT_LOSS,
            'endurance': Goal.ENDURANCE,
            'resistenza': Goal.ENDURANCE,
            'power': Goal.POWER,
            'potenza': Goal.POWER
        }
        goal = goal_map.get(client_profile['goal'].lower(), Goal.STRENGTH)

        # Step 2: Genera piano periodizzazione
        print(f"[PERIODIZATION] Generando piano {periodization_model} per {weeks} settimane...")
        periodization_plan = get_periodization_plan(
            model=periodization_model,
            weeks=weeks,
            goal=goal
        )

        # Step 3: Determina split allenamento
        split_type = self._determine_split(
            sessions_per_week,
            client_profile['level'],
            goal
        )

        # Step 4: Seleziona esercizi per ogni sessione
        print(f"[EXERCISES] Selezionando esercizi per split {split_type}...")
        weekly_template = self._create_weekly_template(
            split_type=split_type,
            level=client_profile['level'],
            goal=goal,
            equipment=client_profile.get('equipment', ['barbell', 'dumbbell']),
            limitazioni=client_profile.get('limitazioni', [])
        )

        # Step 5: Applica exercise rotation (varianti ogni 2-4 settimane)
        print(f"[ROTATION] Applicando rotazione esercizi...")
        rotated_templates = self._apply_exercise_rotation(
            weekly_template,
            weeks,
            equipment=client_profile.get('equipment', []),
            limitazioni=client_profile.get('limitazioni', [])
        )

        # Step 6: Applica periodizzazione con deload automatico
        print(f"[APPLY] Applicando periodizzazione a {weeks} settimane...")
        complete_program = self._apply_periodization_to_template_v2(
            rotated_templates,
            periodization_plan,
            weeks
        )

        # Step 7: Volume tracking validation
        print(f"[VOLUME] Validando volume per muscolo...")
        volume_report = self._validate_weekly_volume(weekly_template)
        
        # Step 8: Aggiungi smart warm-up e cool-down
        complete_program = self._add_smart_warmup_cooldown(complete_program)

        # Step 9: Genera output finale con volume report
        output = {
            'client_name': f"{client_profile.get('nome', '')} {client_profile.get('cognome', '')}".strip(),
            'goal': goal.value,
            'level': client_profile['level'],
            'duration_weeks': weeks,
            'sessions_per_week': sessions_per_week,
            'split_type': split_type,
            'periodization_model': periodization_plan.model_name,
            'periodization_description': periodization_plan.description,
            'weekly_schedule': complete_program,
            'volume_analysis': volume_report,  # NEW: Volume tracking
            'progressive_overload': self._generate_progression_guidelines(goal),
            'recovery_recommendations': self._generate_recovery_guidelines(goal),
            'notes': self._generate_program_notes(client_profile),
            'generated_date': datetime.now().isoformat()
        }

        print(f"[SUCCESS] Programma generato: {weeks} settimane, {sessions_per_week} sessioni/settimana")
        return output

    def _determine_split(
        self,
        sessions_per_week: int,
        level: str,
        goal: Goal
    ) -> str:
        """
        Determina il miglior split allenamento

        Returns:
            'full_body' | 'upper_lower' | 'push_pull_legs' | 'bro_split'
        """
        if sessions_per_week <= 3:
            return 'full_body'  # 3x settimana full body
        elif sessions_per_week == 4:
            return 'upper_lower'  # 2x upper, 2x lower
        elif sessions_per_week >= 5:
            if level == 'advanced':
                return 'push_pull_legs'  # PPL o PPL rest PPL
            else:
                return 'upper_lower'  # Meglio non esagerare

        return 'full_body'

    def _create_weekly_template(
        self,
        split_type: str,
        level: str,
        goal: Goal,
        equipment: List[str],
        limitazioni: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Crea template settimanale con esercizi concreti

        Returns:
            {
                'day_1': [exercises],
                'day_2': [exercises],
                ...
            }
        """

        # Map difficoltà
        difficulty_map = {
            'beginner': DifficultyLevel.BEGINNER,
            'intermediate': DifficultyLevel.INTERMEDIATE,
            'advanced': DifficultyLevel.ADVANCED
        }
        difficulty = difficulty_map.get(level, DifficultyLevel.INTERMEDIATE)

        template = {}

        if split_type == 'full_body':
            # 3 sessioni full body
            for day_num in range(1, 4):
                template[f'day_{day_num}'] = self._select_full_body_exercises(
                    difficulty, goal, equipment, limitazioni, day_num
                )

        elif split_type == 'upper_lower':
            # 2 upper, 2 lower
            template['day_1_upper'] = self._select_upper_body_exercises(
                difficulty, goal, equipment, limitazioni, day=1
            )
            template['day_2_lower'] = self._select_lower_body_exercises(
                difficulty, goal, equipment, limitazioni, day=1
            )
            template['day_3_upper'] = self._select_upper_body_exercises(
                difficulty, goal, equipment, limitazioni, day=2
            )
            template['day_4_lower'] = self._select_lower_body_exercises(
                difficulty, goal, equipment, limitazioni, day=2
            )

        elif split_type == 'push_pull_legs':
            # Push, Pull, Legs
            template['day_1_push'] = self._select_push_exercises(
                difficulty, goal, equipment, limitazioni
            )
            template['day_2_pull'] = self._select_pull_exercises(
                difficulty, goal, equipment, limitazioni
            )
            template['day_3_legs'] = self._select_leg_exercises(
                difficulty, goal, equipment, limitazioni
            )

        return template

    def _select_full_body_exercises(
        self,
        difficulty: DifficultyLevel,
        goal: Goal,
        equipment: List[str],
        limitazioni: List[str],
        day_num: int
    ) -> List[Dict]:
        """Seleziona esercizi per sessione full body - SMART SELECTION"""

        exercises = []
        used_ids = []

        # Esercizio composto lower body (squat pattern alternato con hinge)
        if day_num == 1 or day_num == 3:
            pattern = 'squat'
        else:
            pattern = 'hinge'  # deadlift/RDL
        
        ex = self.exercise_db.select_best_for_pattern(
            pattern=pattern,
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))
            used_ids.append(ex.id)

        # Esercizio composto upper body push
        push_ex = self.exercise_db.select_best_for_pattern(
            pattern='push',
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if push_ex and push_ex.id not in used_ids:
            exercises.append(self._format_exercise(push_ex, goal, is_main=True))
            used_ids.append(push_ex.id)

        # Esercizio composto upper body pull
        pull_ex = self.exercise_db.select_best_for_pattern(
            pattern='pull',
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if pull_ex and pull_ex.id not in used_ids:
            exercises.append(self._format_exercise(pull_ex, goal, is_main=True))
            used_ids.append(pull_ex.id)

        # Accessori (2-3 esercizi bilanciati)
        accessory_muscles = [MuscleGroup.QUADRICEPS, MuscleGroup.SHOULDERS, MuscleGroup.CORE]
        accessory_exercises = self.exercise_db.select_balanced_workout(
            muscles=accessory_muscles,
            count=3,
            equipment=equipment,
            level=difficulty,
            exclude_ids=used_ids
        )
        
        for acc_ex in accessory_exercises:
            exercises.append(self._format_exercise(acc_ex, goal, is_main=False))

        return exercises

    def _select_upper_body_exercises(
        self,
        difficulty: DifficultyLevel,
        goal: Goal,
        equipment: List[str],
        limitazioni: List[str],
        day: int
    ) -> List[Dict]:
        """Seleziona esercizi upper body - SMART SELECTION"""
        exercises = []
        used_ids = []

        # Main push
        push_ex = self.exercise_db.select_best_for_pattern(
            pattern='push',
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if push_ex:
            exercises.append(self._format_exercise(push_ex, goal, is_main=True))
            used_ids.append(push_ex.id)

        # Main pull
        pull_ex = self.exercise_db.select_best_for_pattern(
            pattern='pull',
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if pull_ex and pull_ex.id not in used_ids:
            exercises.append(self._format_exercise(pull_ex, goal, is_main=True))
            used_ids.append(pull_ex.id)

        # Accessori (3-4 esercizi bilanciati)
        accessory_muscles = [
            MuscleGroup.SHOULDERS,
            MuscleGroup.BICEPS,
            MuscleGroup.TRICEPS,
            MuscleGroup.TRAPS
        ]
        accessory_exercises = self.exercise_db.select_balanced_workout(
            muscles=accessory_muscles,
            count=4,
            equipment=equipment,
            level=difficulty,
            exclude_ids=used_ids
        )
        
        for acc_ex in accessory_exercises:
            exercises.append(self._format_exercise(acc_ex, goal, is_main=False))

        return exercises

    def _select_lower_body_exercises(
        self,
        difficulty: DifficultyLevel,
        goal: Goal,
        equipment: List[str],
        limitazioni: List[str],
        day: int
    ) -> List[Dict]:
        """Seleziona esercizi lower body - SMART SELECTION"""
        exercises = []
        used_ids = []

        # Main compound (alternare squat e hinge)
        pattern = 'squat' if day == 1 else 'hinge'
        main_ex = self.exercise_db.select_best_for_pattern(
            pattern=pattern,
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if main_ex:
            exercises.append(self._format_exercise(main_ex, goal, is_main=True))
            used_ids.append(main_ex.id)

        # Accessori (3-4 esercizi)
        accessory_muscles = [
            MuscleGroup.QUADRICEPS,
            MuscleGroup.HAMSTRINGS,
            MuscleGroup.GLUTES,
            MuscleGroup.CALVES
        ]
        accessory_exercises = self.exercise_db.select_balanced_workout(
            muscles=accessory_muscles,
            count=4,
            equipment=equipment,
            level=difficulty,
            exclude_ids=used_ids
        )
        
        for acc_ex in accessory_exercises:
            exercises.append(self._format_exercise(acc_ex, goal, is_main=False))

        return exercises

    def _select_push_exercises(self, difficulty, goal, equipment, limitazioni) -> List[Dict]:
        """Push day (chest/shoulders/triceps) - SMART SELECTION"""
        exercises = []
        used_ids = []

        # Main push
        main_push = self.exercise_db.select_best_for_pattern(
            pattern='push',
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if main_push:
            exercises.append(self._format_exercise(main_push, goal, is_main=True))
            used_ids.append(main_push.id)

        # Accessori push
        push_muscles = [MuscleGroup.CHEST, MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS]
        accessory_exercises = self.exercise_db.select_balanced_workout(
            muscles=push_muscles,
            count=4,
            equipment=equipment,
            level=difficulty,
            exclude_ids=used_ids
        )
        
        for acc_ex in accessory_exercises:
            exercises.append(self._format_exercise(acc_ex, goal, is_main=False))

        return exercises

    def _select_pull_exercises(self, difficulty, goal, equipment, limitazioni) -> List[Dict]:
        """Pull day (back/biceps) - SMART SELECTION"""
        exercises = []
        used_ids = []

        # Main pull
        main_pull = self.exercise_db.select_best_for_pattern(
            pattern='pull',
            equipment=equipment,
            level=difficulty,
            exclude_contraindications=limitazioni
        )
        if main_pull:
            exercises.append(self._format_exercise(main_pull, goal, is_main=True))
            used_ids.append(main_pull.id)

        # Accessori pull
        pull_muscles = [MuscleGroup.BACK, MuscleGroup.LATS, MuscleGroup.BICEPS, MuscleGroup.TRAPS]
        accessory_exercises = self.exercise_db.select_balanced_workout(
            muscles=pull_muscles,
            count=4,
            equipment=equipment,
            level=difficulty,
            exclude_ids=used_ids
        )
        
        for acc_ex in accessory_exercises:
            exercises.append(self._format_exercise(acc_ex, goal, is_main=False))

        return exercises

    def _select_leg_exercises(self, difficulty, goal, equipment, limitazioni) -> List[Dict]:
        """Leg day - SMART SELECTION"""
        return self._select_lower_body_exercises(difficulty, goal, equipment, limitazioni, day=1)

    def _format_exercise(
        self,
        exercise,
        goal: Goal,
        is_main: bool = False
    ) -> Dict:
        """
        Formatta esercizio per output

        Returns:
            {
                'id': str,
                'name': str,
                'italian_name': str,
                'primary_muscles': List[str],
                'equipment': List[str],
                'sets': int,
                'reps': str,  # es. "8-12" o "3-5"
                'rest_seconds': int,
                'notes': str,
                'is_main_lift': bool,
                'video_url': str (se disponibile)
            }
        """

        # Determina sets/reps in base a goal e se main lift
        if goal == Goal.STRENGTH:
            if is_main:
                sets, reps_range = 5, exercise.rep_range_strength
            else:
                sets, reps_range = 3, exercise.rep_range_hypertrophy
        elif goal == Goal.HYPERTROPHY:
            if is_main:
                sets, reps_range = 4, exercise.rep_range_hypertrophy
            else:
                sets, reps_range = 3, exercise.rep_range_hypertrophy
        elif goal == Goal.ENDURANCE:
            sets, reps_range = 3, exercise.rep_range_endurance
        else:  # FAT_LOSS, POWER
            sets, reps_range = 4, (8, 12)

        # Crea dict base
        base_dict = {
            'id': exercise.id,
            'name': exercise.name,
            'italian_name': exercise.italian_name,
            'description': exercise.description,
            'primary_muscles': [m.value for m in exercise.primary_muscles],
            'secondary_muscles': [m.value for m in exercise.secondary_muscles],
            'equipment': exercise.equipment,
            'difficulty': exercise.difficulty.value,
            'sets': sets,
            'reps': f"{reps_range[0]}-{reps_range[1]}",
            'rest_seconds': 180 if is_main else 90,
            'notes': exercise.notes,
            'is_main_lift': is_main,
            'video_url': getattr(exercise, 'video_url', ''),
            'contraindications': exercise.contraindications,

            # ENHANCED FIELDS (se disponibili nell'esercizio)
            'video_thumbnail': getattr(exercise, 'video_thumbnail', ''),
            'image_url': getattr(exercise, 'image_url', ''),
            'setup_instructions': getattr(exercise, 'setup_instructions', []),
            'execution_steps': getattr(exercise, 'execution_steps', []),
            'breathing_cues': getattr(exercise, 'breathing_cues', ''),
            'form_cues': getattr(exercise, 'form_cues', []),
            'common_mistakes': getattr(exercise, 'common_mistakes', []),
            'safety_tips': getattr(exercise, 'safety_tips', []),
            'movement_pattern': getattr(exercise, 'movement_pattern', ''),
            'plane_of_movement': getattr(exercise, 'plane_of_movement', []),
        }

        # Note: professional details già inclusi nel database unificato
        return base_dict

    def _apply_periodization_to_template(
        self,
        weekly_template: Dict,
        periodization_plan: PeriodizationPlan,
        weeks: int
    ) -> Dict:
        """
        Applica periodizzazione a template settimanale

        Returns:
            {
                'week_1': {...},
                'week_2': {...},
                ...
            }
        """
        complete_program = {}

        for week_num in range(1, weeks + 1):
            # Ottieni parametri periodizzazione per questa settimana
            week_params = periodization_plan.weeks[week_num - 1]

            # Clona template e applica parametri
            week_program = {}
            for day_name, exercises in weekly_template.items():
                week_program[day_name] = []

                for exercise in exercises:
                    # Clona esercizio
                    ex = exercise.copy()

                    # Sovrascrivi con parametri periodizzazione
                    if not week_params.is_deload:
                        ex['sets'] = week_params.volume_sets if ex['is_main_lift'] else max(2, week_params.volume_sets - 1)
                        ex['reps'] = f"{week_params.reps_per_set[0]}-{week_params.reps_per_set[1]}"
                        ex['rest_seconds'] = week_params.rest_seconds
                        ex['intensity_percent'] = week_params.intensity_percent
                    else:
                        # Deload: ridurre volume
                        ex['sets'] = max(2, ex['sets'] - 1)
                        ex['intensity_percent'] = week_params.intensity_percent
                        ex['notes'] = f"DELOAD WEEK - {ex['notes']}"

                    week_program[day_name].append(ex)

            complete_program[f'week_{week_num}'] = {
                'week_number': week_num,
                'focus': week_params.focus,
                'is_deload': week_params.is_deload,
                'intensity_percent': week_params.intensity_percent,
                'notes': week_params.notes,
                'sessions': week_program
            }

        return complete_program

    def _add_warmup_cooldown(self, program: Dict) -> Dict:
        """Aggiunge warm-up e cool-down a ogni sessione"""

        warmup = {
            'duration_minutes': 10,
            'exercises': [
                {'name': 'Light Cardio', 'duration': '5 min', 'notes': 'Tapis roulant, bike, o jumping jacks'},
                {'name': 'Dynamic Stretching', 'duration': '5 min', 'notes': 'Leg swings, arm circles, torso twists'}
            ]
        }

        cooldown = {
            'duration_minutes': 10,
            'exercises': [
                {'name': 'Static Stretching', 'duration': '5 min', 'notes': 'Focus muscoli allenati'},
                {'name': 'Foam Rolling', 'duration': '5 min', 'notes': 'Auto-miofascial release'}
            ]
        }

        # Aggiungi a ogni sessione
        for week_name, week_data in program.items():
            if isinstance(week_data, dict) and 'sessions' in week_data:
                for session_name, exercises in week_data['sessions'].items():
                    week_data['sessions'][session_name] = {
                        'warmup': warmup,
                        'main_workout': exercises,
                        'cooldown': cooldown
                    }

        return program

    def _generate_progression_guidelines(self, goal: Goal) -> str:
        """Genera linee guida progressive overload"""

        guidelines = {
            Goal.STRENGTH: """
**Progressive Overload (Forza):**
- Aumenta peso 2.5-5% ogni settimana (se completi tutte le rep)
- Se non riesci a completare le rep, mantieni peso
- Deload ogni 4 settimane (-10% peso)
- Focus: aumento carico assoluto
            """,
            Goal.HYPERTROPHY: """
**Progressive Overload (Ipertrofia):**
- Aumenta reps prima (double progression)
- Quando raggiungi reps massime, aumenta peso 2.5%
- Focus: volume totale (sets × reps × peso)
- Deload ogni 4 settimane
            """,
            Goal.ENDURANCE: """
**Progressive Overload (Resistenza):**
- Aumenta reps/durata progressivamente
- Riduci tempi recupero gradualmente
- Focus: density training (lavoro/tempo)
            """
        }

        return guidelines.get(goal, guidelines[Goal.STRENGTH])

    def _generate_recovery_guidelines(self, goal: Goal) -> str:
        """Genera raccomandazioni recupero"""
        return """
**Recupero Ottimale:**
- Sonno: 7-9 ore/notte
- Proteine: 1.6-2.2g/kg peso corporeo
- Idratazione: 2-3L acqua/giorno
- Giorni riposo: Almeno 1-2/settimana
- Stretching: 10-15 min post-workout
- Gestione stress: Meditazione, yoga, camminate
        """

    def _generate_program_notes(self, client_profile: Dict) -> str:
        """Genera note programma personalizzate"""

        notes = f"""
**Note Programma per {client_profile.get('nome', 'Cliente')}:**

- Obiettivo: {client_profile['goal'].upper()}
- Livello: {client_profile['level'].capitalize()}
        """

        if client_profile.get('limitazioni'):
            notes += f"\n- Limitazioni: {', '.join(client_profile['limitazioni'])}"
            notes += "\n- IMPORTANTE: Ascolta il tuo corpo. Se un esercizio causa dolore, FERMATI."

        notes += """

**Sicurezza:**
- Usa sempre un compagno di allenamento per esercizi pesanti
- Warm-up obbligatorio prima di ogni sessione
- Tecnica > Peso (sempre!)
- Se hai dubbi su un esercizio, chiedi a un coach

**Progressione:**
- Registra ogni allenamento (peso, reps, sensazioni)
- Aumenta carico/volume solo se tecnica è perfetta
- Sii paziente: i risultati arrivano con costanza
        """

        return notes


    # ══════════════════════════════════════════════════════════════
    # NEW V3: EXERCISE ROTATION, VOLUME TRACKING, SMART WARM-UP
    # ══════════════════════════════════════════════════════════════

    def _apply_exercise_rotation(
        self,
        weekly_template: Dict,
        weeks: int,
        equipment: List[str],
        limitazioni: List[str]
    ) -> Dict[int, Dict]:
        """
        Applica rotazione esercizi ogni 2-4 settimane per varietà
        
        Returns:
            {
                1: weekly_template (week 1-2),
                3: weekly_template_variant (week 3-4),
                5: weekly_template_variant2 (week 5-6),
                ...
            }
        """
        rotation_frequency = 2 if weeks >= 8 else 4  # Ruota ogni 2-4 settimane
        templates = {}
        
        for week_start in range(1, weeks + 1, rotation_frequency):
            # Usa template originale per prime settimane
            if week_start == 1:
                templates[week_start] = weekly_template
            else:
                # Genera variante usando alternative exercises
                variant_template = {}
                for day_name, exercises in weekly_template.items():
                    variant_exercises = []
                    for ex in exercises:
                        # Per esercizi principali, trova variante
                        if ex.get('is_main_lift', False):
                            original_id = ex.get('id', ex['name'])
                            alternatives = self.exercise_db.get_alternative_exercises(
                                exercise_id=original_id,
                                reason='variety',
                                equipment=equipment
                            )
                            # Prendi prima alternativa safe
                            if alternatives:
                                variant_ex = alternatives[0]
                                # Ricostruisci dict
                                variant_exercises.append({
                                    'id': variant_ex.id,
                                    'name': variant_ex.name,
                                    'italian_name': variant_ex.italian_name,
                                    'primary_muscles': [m.value for m in variant_ex.primary_muscles],
                                    'equipment': variant_ex.equipment,
                                    'is_main_lift': True,
                                    'sets': ex['sets'],
                                    'reps': ex['reps'],
                                    'rest_seconds': ex['rest_seconds'],
                                    'notes': f"Variante di {ex['name']}",
                                    'contraindications': variant_ex.contraindications,
                                })
                            else:
                                # Nessuna alternativa, tieni originale
                                variant_exercises.append(ex)
                        else:
                            # Esercizi accessori, tieni uguali
                            variant_exercises.append(ex)
                    
                    variant_template[day_name] = variant_exercises
                
                templates[week_start] = variant_template
        
        return templates

    def _apply_periodization_to_template_v2(
        self,
        rotated_templates: Dict[int, Dict],
        periodization_plan: PeriodizationPlan,
        weeks: int
    ) -> Dict:
        """
        Applica periodizzazione con DELOAD automatico ogni 3-4 settimane
        
        Returns:
            {
                'week_1': {...},
                'week_2': {...},
                ...
            }
        """
        complete_program = {}
        deload_frequency = 4  # Deload ogni 4 settimane
        
        for week_num in range(1, weeks + 1):
            # Determina se è deload week
            is_deload = (week_num % deload_frequency == 0) and week_num > 1
            
            # Ottieni parametri periodizzazione
            week_params = periodization_plan.weeks[min(week_num - 1, len(periodization_plan.weeks) - 1)]
            
            # Trova template corretto (rotazione)
            template_week = max([w for w in rotated_templates.keys() if w <= week_num])
            weekly_template = rotated_templates[template_week]
            
            # Applica parametri
            week_program = {}
            for day_name, exercises in weekly_template.items():
                week_program[day_name] = []
                
                for exercise in exercises:
                    ex = exercise.copy()
                    
                    if is_deload:
                        # DELOAD: Riduci volume 40-60%, intensità -10%
                        ex['sets'] = max(2, int(ex.get('sets', 3) * 0.6))  # -40% sets
                        ex['intensity_percent'] = max(60, week_params.intensity_percent - 10)
                        ex['notes'] = f"🔵 DELOAD WEEK - {ex.get('notes', '')}"
                        ex['reps'] = f"{week_params.reps_per_set[0]}-{week_params.reps_per_set[1]}"
                    else:
                        # Normal week
                        ex['sets'] = week_params.volume_sets if ex.get('is_main_lift') else max(2, week_params.volume_sets - 1)
                        ex['reps'] = f"{week_params.reps_per_set[0]}-{week_params.reps_per_set[1]}"
                        ex['rest_seconds'] = week_params.rest_seconds
                        ex['intensity_percent'] = week_params.intensity_percent
                    
                    week_program[day_name].append(ex)
            
            complete_program[f'week_{week_num}'] = {
                'week_number': week_num,
                'focus': "Deload & Recovery" if is_deload else week_params.focus,
                'is_deload': is_deload,
                'intensity_percent': week_params.intensity_percent - 10 if is_deload else week_params.intensity_percent,
                'notes': "Settimana di scarico: volume ridotto 40%, intensità -10%. Focus su recupero e tecnica." if is_deload else week_params.notes,
                'sessions': week_program
            }
        
        return complete_program

    def _validate_weekly_volume(self, weekly_template: Dict) -> Dict:
        """
        Calcola e valida volume settimanale per muscolo
        
        Returns:
            {
                'total_sets_per_muscle': {...},
                'warnings': [...],
                'recommendations': [...]
            }
        """
        muscle_volume = {}
        
        # Conta sets per muscolo
        for day_name, exercises in weekly_template.items():
            for ex in exercises:
                # Estrai muscoli primari
                primary_muscles = ex.get('primary_muscles', [])
                sets = ex.get('sets', 3)
                
                for muscle_str in primary_muscles:
                    # Converti stringa a MuscleGroup
                    try:
                        muscle = MuscleGroup(muscle_str)
                        if muscle not in muscle_volume:
                            muscle_volume[muscle] = 0
                        muscle_volume[muscle] += sets
                    except ValueError:
                        continue  # Skip se non è MuscleGroup valido
        
        # Valida contro range ottimali
        warnings = []
        recommendations = []
        
        for muscle, total_sets in muscle_volume.items():
            if muscle in self.optimal_volume_ranges:
                min_sets, max_sets = self.optimal_volume_ranges[muscle]
                
                if total_sets < min_sets:
                    warnings.append(f"⚠️  {muscle.value}: {total_sets} sets/week (sotto range ottimale {min_sets}-{max_sets})")
                    recommendations.append(f"Aggiungi 1-2 esercizi per {muscle.value}")
                elif total_sets > max_sets:
                    warnings.append(f"⚠️  {muscle.value}: {total_sets} sets/week (sopra range ottimale {min_sets}-{max_sets})")
                    recommendations.append(f"Riduci volume per {muscle.value} per evitare overtraining")
        
        return {
            'total_sets_per_muscle': {m.value: s for m, s in muscle_volume.items()},
            'optimal_ranges': {m.value: f"{r[0]}-{r[1]} sets/week" for m, r in self.optimal_volume_ranges.items()},
            'warnings': warnings,
            'recommendations': recommendations,
            'status': 'optimal' if not warnings else 'needs_adjustment'
        }

    def _add_smart_warmup_cooldown(self, program: Dict) -> Dict:
        """
        Aggiunge warm-up SPECIFICO e cool-down a ogni sessione
        
        Warm-up include:
        - General warm-up (cardio leggero)
        - Dynamic stretching specifico
        - Specific warm-up sets (50%, 75%, 90% del working weight)
        """
        
        for week_name, week_data in program.items():
            if isinstance(week_data, dict) and 'sessions' in week_data:
                for session_name, exercises in week_data['sessions'].items():
                    if not exercises:
                        continue
                    
                    # Identifica main lifts
                    main_lifts = [ex for ex in exercises if ex.get('is_main_lift', False)]
                    
                    # SMART WARM-UP
                    warmup = {
                        'duration_minutes': 15,
                        'phases': [
                            {
                                'phase': '1. General Warm-up',
                                'duration': '5 min',
                                'exercises': [
                                    {'name': 'Light Cardio', 'details': 'Tapis roulant, bike, rowing @ RPE 4-5'}
                                ]
                            },
                            {
                                'phase': '2. Dynamic Mobility',
                                'duration': '5 min',
                                'exercises': self._get_dynamic_warmup_for_session(main_lifts)
                            },
                            {
                                'phase': '3. Specific Warm-up Sets',
                                'duration': '5 min',
                                'exercises': self._get_specific_warmup_sets(main_lifts)
                            }
                        ]
                    }
                    
                    # COOL-DOWN
                    cooldown = {
                        'duration_minutes': 10,
                        'phases': [
                            {
                                'phase': '1. Light Active Recovery',
                                'duration': '3 min',
                                'exercises': [
                                    {'name': 'Walking', 'details': '3 min camminata lenta per abbassare HR'}
                                ]
                            },
                            {
                                'phase': '2. Static Stretching',
                                'duration': '4 min',
                                'exercises': self._get_static_stretch_for_session(main_lifts)
                            },
                            {
                                'phase': '3. Foam Rolling',
                                'duration': '3 min',
                                'exercises': [
                                    {'name': 'Foam Roll', 'details': 'Focus muscoli allenati oggi (30 sec per muscolo)'}
                                ]
                            }
                        ]
                    }
                    
                    # Inserisci all'inizio e fine sessione
                    week_data['sessions'][session_name] = {
                        'warmup': warmup,
                        'main_workout': exercises,
                        'cooldown': cooldown
                    }
        
        return program

    def _get_dynamic_warmup_for_session(self, main_lifts: List[Dict]) -> List[Dict]:
        """Genera dynamic warm-up specifico per esercizi sessione"""
        
        # Analizza muscoli target
        has_lower = any('squat' in ex.get('name', '').lower() or 
                       'deadlift' in ex.get('name', '').lower() or
                       'leg' in ex.get('name', '').lower() 
                       for ex in main_lifts)
        
        has_upper_push = any('bench' in ex.get('name', '').lower() or 
                            'press' in ex.get('name', '').lower() 
                            for ex in main_lifts)
        
        has_upper_pull = any('row' in ex.get('name', '').lower() or 
                            'pull' in ex.get('name', '').lower() 
                            for ex in main_lifts)
        
        dynamic_exercises = []
        
        if has_lower:
            dynamic_exercises.extend([
                {'name': 'Leg Swings', 'reps': '10 per lato', 'details': 'Avanti/indietro e laterali'},
                {'name': 'Bodyweight Squats', 'reps': '10', 'details': 'Lento e controllato'},
                {'name': 'Walking Lunges', 'reps': '10 per lato', 'details': 'Focus mobilità anca'}
            ])
        
        if has_upper_push or has_upper_pull:
            dynamic_exercises.extend([
                {'name': 'Arm Circles', 'reps': '10 avanti + 10 indietro', 'details': 'Piccoli e grandi cerchi'},
                {'name': 'Scapular Push-ups', 'reps': '10', 'details': 'Focus retrazione scapole'},
                {'name': 'Band Pull-aparts', 'reps': '15', 'details': 'Attivazione upper back'}
            ])
        
        return dynamic_exercises if dynamic_exercises else [
            {'name': 'Full Body Dynamic Stretch', 'reps': '5 min', 'details': 'Movimenti dinamici multi-articolari'}
        ]

    def _get_specific_warmup_sets(self, main_lifts: List[Dict]) -> List[Dict]:
        """Genera specific warm-up sets per main lifts (50%, 75%, 90%)"""
        
        warmup_sets = []
        
        for lift in main_lifts[:2]:  # Primi 2 main lifts
            name = lift.get('name', 'Exercise')
            warmup_sets.append({
                'name': f"{name} Warm-up",
                'sets': '3 sets',
                'details': '1×8 @ 50%, 1×5 @ 75%, 1×3 @ 90% del peso di lavoro'
            })
        
        return warmup_sets if warmup_sets else [
            {'name': 'Light Sets', 'details': 'Inizia con peso leggero e aumenta gradualmente'}
        ]

    def _get_static_stretch_for_session(self, main_lifts: List[Dict]) -> List[Dict]:
        """Genera static stretching specifico per muscoli allenati"""
        
        has_lower = any('squat' in ex.get('name', '').lower() or 
                       'deadlift' in ex.get('name', '').lower() or
                       'leg' in ex.get('name', '').lower() 
                       for ex in main_lifts)
        
        has_upper = any('bench' in ex.get('name', '').lower() or 
                       'press' in ex.get('name', '').lower() or
                       'row' in ex.get('name', '').lower() or
                       'pull' in ex.get('name', '').lower()
                       for ex in main_lifts)
        
        stretches = []
        
        if has_lower:
            stretches.extend([
                {'name': 'Quad Stretch', 'duration': '30 sec per lato'},
                {'name': 'Hamstring Stretch', 'duration': '30 sec per lato'},
                {'name': 'Glute Stretch (Pigeon)', 'duration': '30 sec per lato'},
            ])
        
        if has_upper:
            stretches.extend([
                {'name': 'Chest Doorway Stretch', 'duration': '30 sec'},
                {'name': 'Shoulder Cross-body Stretch', 'duration': '30 sec per lato'},
                {'name': 'Tricep Overhead Stretch', 'duration': '30 sec per lato'},
            ])
        
        return stretches if stretches else [
            {'name': 'Full Body Stretch', 'duration': '5 min', 'details': 'Focus muscoli allenati'}
        ]


# ══════════════════════════════════════════════════════════════
# UTILITY per backward compatibility
# ══════════════════════════════════════════════════════════════

def generate_workout_v2(client_profile: Dict, weeks: int = 4, **kwargs) -> Dict:
    """
    Wrapper per generazione workout V2 professionale

    Usare questa funzione invece di WorkoutGenerator vecchio
    """
    generator = WorkoutGeneratorV2()
    return generator.generate_professional_workout(
        client_profile=client_profile,
        weeks=weeks,
        **kwargs
    )


if __name__ == "__main__":
    # Test: Genera programma per Laura (dal tuo esempio)
    print("="*60)
    print("TEST: Programma per Laura (Beginner, Forza)")
    print("="*60)

    laura_profile = {
        'nome': 'Laura',
        'cognome': 'Rossi',
        'goal': 'strength',
        'level': 'beginner',
        'disponibilita_giorni': 3,
        'equipment': ['barbell', 'dumbbell', 'machine'],
        'limitazioni': ['collo']
    }

    generator = WorkoutGeneratorV2()
    program = generator.generate_professional_workout(
        client_profile=laura_profile,
        weeks=4,
        periodization_model='linear',
        sessions_per_week=3
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"PROGRAMMA GENERATO: {program['client_name']}")
    print(f"{'='*60}")
    print(f"Goal: {program['goal'].upper()}")
    print(f"Livello: {program['level'].capitalize()}")
    print(f"Durata: {program['duration_weeks']} settimane")
    print(f"Split: {program['split_type'].upper()}")
    print(f"Periodizzazione: {program['periodization_model']}")

    print(f"\n{'─'*60}")
    print("SETTIMANA 1 - SESSIONE 1 (Day 1):")
    print(f"{'─'*60}")

    week1_day1 = program['weekly_schedule']['week_1']['sessions']['day_1']

    # Warmup
    print("\n🔥 WARM-UP (10 min):")
    for ex in week1_day1['warmup']['exercises']:
        print(f"  - {ex['name']}: {ex['duration']} ({ex['notes']})")

    # Main workout
    print("\n💪 ALLENAMENTO PRINCIPALE:")
    for i, ex in enumerate(week1_day1['main_workout'], 1):
        print(f"\n{i}. {ex['italian_name']} ({ex['name']})")
        print(f"   Muscoli: {', '.join(ex['primary_muscles'])}")
        print(f"   Sets: {ex['sets']} × {ex['reps']} rep")
        print(f"   Recupero: {ex['rest_seconds']}s")
        print(f"   Intensità: {ex.get('intensity_percent', 0)*100:.0f}% 1RM")
        if ex['notes']:
            print(f"   Note: {ex['notes']}")

    # Cooldown
    print("\n🧘 COOL-DOWN (10 min):")
    for ex in week1_day1['cooldown']['exercises']:
        print(f"  - {ex['name']}: {ex['duration']} ({ex['notes']})")

    print(f"\n{'='*60}")
    print("✅ Test completato con successo!")
    print(f"{'='*60}\n")

    # Esporta JSON per debug
    output_file = Path(__file__).parent.parent / "test_workout_laura.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(program, f, indent=2, ensure_ascii=False)

    print(f"📄 Programma completo salvato in: {output_file}")
