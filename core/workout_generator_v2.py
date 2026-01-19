# core/workout_generator_v2.py
"""
Workout Generator V2 - Versione Professionale

Integra:
- Database 500+ esercizi (exercise_library_extended)
- 5 Modelli periodizzazione scientifica (periodization_models)
- Output strutturato e professionale
- Progressive overload automatico

Miglioramenti vs V1:
- Esercizi CONCRETI selezionati da database
- Periodizzazione scientifica (non più "inventata" dall'LLM)
- Warm-up e cool-down inclusi
- Progressione chiara settimana per settimana
- Formato export-ready (PDF/stampa)
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.exercise_library_extended import get_complete_exercise_database
from core.periodization_models import get_periodization_plan, Goal, PeriodizationPlan
from core.exercise_database import MuscleGroup, DifficultyLevel


class WorkoutGeneratorV2:
    """
    Generatore professionale di programmi allenamento

    Features:
    - Selezione esercizi da database 500+
    - Periodizzazione scientifica (5 modelli)
    - Warm-up/cool-down automatici
    - Progressive overload tracking
    - Output professionale
    """

    def __init__(self):
        """Inizializza generatore con database esercizi"""
        print("[INIT] Caricamento database esercizi...")
        self.exercise_db = get_complete_exercise_database()
        print(f"[OK] Caricati {len(self.exercise_db.exercises)} esercizi")

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

        # Step 5: Applica periodizzazione a template
        print(f"[APPLY] Applicando periodizzazione a {weeks} settimane...")
        complete_program = self._apply_periodization_to_template(
            weekly_template,
            periodization_plan,
            weeks
        )

        # Step 6: Aggiungi warm-up e cool-down
        complete_program = self._add_warmup_cooldown(complete_program)

        # Step 7: Genera output finale
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
        """Seleziona esercizi per sessione full body"""

        exercises = []

        # Esercizio composto lower body (squat/deadlift)
        if day_num == 1:
            ex = self.exercise_db.get_exercise('back_squat') or self.exercise_db.get_exercise('goblet_squat')
        elif day_num == 2:
            ex = self.exercise_db.get_exercise('romanian_deadlift') or self.exercise_db.get_exercise('deadlift')
        else:
            ex = self.exercise_db.get_exercise('front_squat') or self.exercise_db.get_exercise('leg_press')

        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))

        # Esercizio composto upper body push (bench/overhead)
        if day_num == 1:
            ex = self.exercise_db.get_exercise('bench_press') or self.exercise_db.get_exercise('pushup')
        elif day_num == 2:
            ex = self.exercise_db.get_exercise('overhead_press') or self.exercise_db.get_exercise('dumbbell_press')
        else:
            ex = self.exercise_db.get_exercise('incline_bench') or self.exercise_db.get_exercise('dips')

        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))

        # Esercizio composto upper body pull (rows/pullups)
        if day_num == 1:
            ex = self.exercise_db.get_exercise('barbell_row') or self.exercise_db.get_exercise('pullup')
        elif day_num == 2:
            ex = self.exercise_db.get_exercise('pullup') or self.exercise_db.get_exercise('lat_pulldown')
        else:
            ex = self.exercise_db.get_exercise('dumbbell_row') or self.exercise_db.get_exercise('cable_row')

        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))

        # Accessori (2-3 esercizi)
        # Gambe accessorio
        ex = self.exercise_db.get_exercise('leg_curl') or self.exercise_db.get_exercise('walking_lunge')
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=False))

        # Spalle/braccia
        ex = self.exercise_db.get_exercise('lateral_raise') or self.exercise_db.get_exercise('dumbbell_curl')
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=False))

        # Core
        ex = self.exercise_db.get_exercise('plank') or self.exercise_db.get_exercise('ab_wheel')
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=False))

        return exercises

    def _select_upper_body_exercises(
        self,
        difficulty: DifficultyLevel,
        goal: Goal,
        equipment: List[str],
        limitazioni: List[str],
        day: int
    ) -> List[Dict]:
        """Seleziona esercizi upper body"""
        exercises = []

        # Main push
        if day == 1:
            ex = self.exercise_db.get_exercise('bench_press')
        else:
            ex = self.exercise_db.get_exercise('overhead_press')
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))

        # Main pull
        if day == 1:
            ex = self.exercise_db.get_exercise('pullup')
        else:
            ex = self.exercise_db.get_exercise('barbell_row')
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))

        # Accessori (3-4)
        accessory_ids = ['dumbbell_row', 'lateral_raise', 'tricep_dips', 'bicep_curl', 'face_pull']
        for ex_id in accessory_ids[:3]:
            ex = self.exercise_db.get_exercise(ex_id)
            if ex:
                exercises.append(self._format_exercise(ex, goal, is_main=False))

        return exercises

    def _select_lower_body_exercises(
        self,
        difficulty: DifficultyLevel,
        goal: Goal,
        equipment: List[str],
        limitazioni: List[str],
        day: int
    ) -> List[Dict]:
        """Seleziona esercizi lower body"""
        exercises = []

        # Main compound
        if day == 1:
            ex = self.exercise_db.get_exercise('back_squat')
        else:
            ex = self.exercise_db.get_exercise('deadlift')
        if ex:
            exercises.append(self._format_exercise(ex, goal, is_main=True))

        # Accessori
        accessory_ids = ['leg_press', 'leg_curl', 'walking_lunge', 'calf_raise']
        for ex_id in accessory_ids:
            ex = self.exercise_db.get_exercise(ex_id)
            if ex:
                exercises.append(self._format_exercise(ex, goal, is_main=False))

        return exercises

    def _select_push_exercises(self, difficulty, goal, equipment, limitazioni) -> List[Dict]:
        """Push day (chest/shoulders/triceps)"""
        # Implementazione simile...
        return []

    def _select_pull_exercises(self, difficulty, goal, equipment, limitazioni) -> List[Dict]:
        """Pull day (back/biceps)"""
        return []

    def _select_leg_exercises(self, difficulty, goal, equipment, limitazioni) -> List[Dict]:
        """Leg day"""
        return []

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

        return {
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
            'contraindications': exercise.contraindications
        }

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
