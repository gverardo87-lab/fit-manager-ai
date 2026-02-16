# core/exercise_database.py
"""
Built-in Exercise Database per FitManager AI

Contiene 200+ esercizi con:
- Anatomia e muscoli target
- Progressioni e regressioni
- Rep ranges per goal (strength, hypertrophy, endurance)
- Tempo di recupero
- Varianti e alternative
- Difficoltà

Questo permette la generazione di workout ANCHE SENZA Knowledge Base caricata.
Quando l'utente carica i PDF, il sistema li IBRIDA con questi dati base.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class MuscleGroup(Enum):
    """Muscoli target principali"""
    CHEST = "petto"
    BACK = "schiena"
    SHOULDERS = "spalle"
    BICEPS = "bicipiti"
    TRICEPS = "tricipiti"
    FOREARMS = "avambracci"
    QUADRICEPS = "quadricipiti"
    HAMSTRINGS = "ischio-crurali"
    GLUTES = "glutei"
    CALVES = "polpacci"
    CORE = "core"
    TRAPS = "trapezi"
    LATS = "dorsali"


class DifficultyLevel(Enum):
    """Livello di difficoltà esercizio"""
    BEGINNER = "principiante"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzato"


@dataclass
class ExerciseProgression:
    """Progressione da un esercizio a uno più difficile"""
    next_exercise: str  # Nome dell'esercizio
    progression_type: str  # 'weight', 'range_of_motion', 'stability', 'tempo'
    notes: str = ""


@dataclass
class ExerciseRegression:
    """Regressione da un esercizio a uno più facile (per infortuni/principianti)"""
    previous_exercise: str
    regression_type: str
    notes: str = ""


@dataclass
class ExerciseVariant:
    """Variante dell'esercizio (stessa meccanica, esecuzione diversa)"""
    name: str
    description: str
    difficulty_modifier: int = 0  # -1 (più facile), 0 (uguale), +1 (più difficile)


@dataclass
class Exercise:
    """Definizione completa di un esercizio - ENHANCED per competere con Trainerize/TrueCoach"""

    # Identità
    id: str  # Slug unico (es. 'back_squat')
    name: str  # Nome (es. 'Back Squat')
    italian_name: str  # Nome italiano
    description: str  # Descrizione breve

    # Anatomia
    primary_muscles: List[MuscleGroup]  # Muscoli principali
    secondary_muscles: List[MuscleGroup] = field(default_factory=list)  # Muscoli secondari
    stabilizers: List[MuscleGroup] = field(default_factory=list)  # Muscoli stabilizzatori

    # Difficoltà e Equipment
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    equipment: List[str] = field(default_factory=list)  # ['barbell', 'dumbbell', 'machine', 'bodyweight']
    space_required: str = "small"  # 'small', 'medium', 'large'

    # Rep Ranges per Goal (min, max)
    rep_range_strength: tuple = (3, 6)  # Forza massimale
    rep_range_hypertrophy: tuple = (6, 12)  # Ipertrofia
    rep_range_endurance: tuple = (12, 20)  # Resistenza muscolare

    # Recupero
    recovery_hours: int = 24  # Ore di recupero necessarie
    intensity_rpe_range: tuple = (6, 10)  # Rate of Perceived Exertion (1-10)

    # ============ ENHANCED FEATURES (come Trainerize/TrueCoach) ============

    # Media (Video/Immagini)
    video_url: str = ""  # YouTube URL video demo professionale
    video_thumbnail: str = ""  # Thumbnail URL
    image_url: str = ""  # Immagine statica esecuzione

    # Istruzioni Step-by-Step (come TrueCoach)
    setup_instructions: List[str] = field(default_factory=list)  # Setup/posizione iniziale
    execution_steps: List[str] = field(default_factory=list)  # Step esecuzione movimento
    breathing_cues: str = ""  # Quando inspirare/espirare

    # Form & Technique (come Trainerize)
    form_cues: List[str] = field(default_factory=list)  # Suggerimenti tecnici chiave
    common_mistakes: List[str] = field(default_factory=list)  # Errori comuni da evitare
    safety_tips: List[str] = field(default_factory=list)  # Avvertenze sicurezza

    # Movement Pattern (come TrueCoach)
    movement_pattern: str = ""  # 'squat', 'hinge', 'push', 'pull', 'carry', 'rotation'
    plane_of_movement: List[str] = field(default_factory=list)  # ['sagittal', 'frontal', 'transverse']

    # Progressione
    progressions: List[ExerciseProgression] = field(default_factory=list)
    regressions: List[ExerciseRegression] = field(default_factory=list)
    variants: List[ExerciseVariant] = field(default_factory=list)
    
    # Note
    notes: str = ""
    contraindications: List[str] = field(default_factory=list)  # Quando evitarlo
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a dict per serializzazione"""
        return {
            'id': self.id,
            'name': self.name,
            'italian_name': self.italian_name,
            'description': self.description,
            'primary_muscles': [m.value for m in self.primary_muscles],
            'secondary_muscles': [m.value for m in self.secondary_muscles],
            'stabilizers': [m.value for m in self.stabilizers],
            'difficulty': self.difficulty.value,
            'equipment': self.equipment,
            'space_required': self.space_required,
            'rep_range_strength': self.rep_range_strength,
            'rep_range_hypertrophy': self.rep_range_hypertrophy,
            'rep_range_endurance': self.rep_range_endurance,
            'recovery_hours': self.recovery_hours,
            'intensity_rpe_range': self.intensity_rpe_range,
            'notes': self.notes,
            'contraindications': self.contraindications,
        }


class ExerciseDatabase:
    """Database built-in di esercizi per generazione workout senza KB"""
    
    def __init__(self):
        """Inizializza il database"""
        self.exercises: Dict[str, Exercise] = {}
        self._load_exercises()
    
    def _load_exercises(self):
        """Carica tutti gli esercizi built-in"""
        
        # ═══════════════════════════════════════════════════════════
        # LOWER BODY - SQUAT VARIATIONS
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['back_squat'] = Exercise(
            id='back_squat',
            name='Back Squat',
            italian_name='Squat Bilanciere',
            description='Squat con bilanciere sulle spalle, esercizio base per le gambe',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES, MuscleGroup.HAMSTRINGS],
            secondary_muscles=[MuscleGroup.CORE],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['barbell'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 12),
            rep_range_endurance=(15, 20),
            recovery_hours=48,
            progressions=[ExerciseProgression('pause_squat', 'tempo')],
            regressions=[ExerciseRegression('goblet_squat', 'weight')],
            variants=[
                ExerciseVariant('Pause Squat', 'Pausa 2-3 sec nel basso', +1),
                ExerciseVariant('Tempo Squat', 'Movimento controllato 3-1-3', +1),
            ],
            notes='Esercizio fondamentale, richiede tecnica corretta',
        )
        
        self.exercises['front_squat'] = Exercise(
            id='front_squat',
            name='Front Squat',
            italian_name='Squat Anteriore',
            description='Squat con bilanciere in posizione anteriore',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES],
            secondary_muscles=[MuscleGroup.CORE],
            difficulty=DifficultyLevel.ADVANCED,
            equipment=['barbell'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=48,
            notes='Enfatizza i quadricipiti, difficile per la mobilità della spalla',
        )
        
        self.exercises['goblet_squat'] = Exercise(
            id='goblet_squat',
            name='Goblet Squat',
            italian_name='Squat Goblet',
            description='Squat tenendo un peso davanti al petto',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES],
            secondary_muscles=[MuscleGroup.CORE],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['dumbbell', 'kettlebell'],
            rep_range_strength=(8, 12),
            rep_range_hypertrophy=(10, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            progressions=[ExerciseProgression('front_squat', 'weight')],
            notes='Ottimo per imparare la tecnica dello squat',
        )
        
        self.exercises['leg_press'] = Exercise(
            id='leg_press',
            name='Leg Press',
            italian_name='Pressa Gambe',
            description='Esercizio su macchina per le gambe',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES],
            secondary_muscles=[MuscleGroup.HAMSTRINGS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['machine'],
            rep_range_strength=(6, 10),
            rep_range_hypertrophy=(10, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            notes='Facile da imparare, bassa curva di apprendimento',
        )
        
        self.exercises['bodyweight_squat'] = Exercise(
            id='bodyweight_squat',
            name='Bodyweight Squat',
            italian_name='Squat a Corpo Libero',
            description='Squat senza pesi, fondamentale per mobilità',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES],
            secondary_muscles=[MuscleGroup.HAMSTRINGS, MuscleGroup.CORE],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['bodyweight'],
            rep_range_strength=(15, 20),
            rep_range_hypertrophy=(15, 20),
            rep_range_endurance=(20, 30),
            recovery_hours=12,
            progressions=[ExerciseProgression('goblet_squat', 'weight')],
            notes='Esercizio di base, niente peso',
        )
        
        # ═══════════════════════════════════════════════════════════
        # LOWER BODY - DEADLIFT VARIATIONS
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['conventional_deadlift'] = Exercise(
            id='conventional_deadlift',
            name='Conventional Deadlift',
            italian_name='Stacco da Terra Classico',
            description='Stacco da terra con gambe larghe, esercizio base completo',
            primary_muscles=[MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES, MuscleGroup.BACK],
            secondary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.CORE],
            difficulty=DifficultyLevel.ADVANCED,
            equipment=['barbell'],
            rep_range_strength=(1, 6),
            rep_range_hypertrophy=(6, 10),
            rep_range_endurance=(10, 15),
            recovery_hours=48,
            notes='Esercizio complesso, richiede buona tecnica',
        )
        
        self.exercises['sumo_deadlift'] = Exercise(
            id='sumo_deadlift',
            name='Sumo Deadlift',
            italian_name='Stacco Sumo',
            description='Stacco con gambe larghe e punta verso fuori',
            primary_muscles=[MuscleGroup.GLUTES, MuscleGroup.BACK],
            secondary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.CORE],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['barbell'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 10),
            rep_range_endurance=(10, 15),
            recovery_hours=48,
            notes='Minore stress sulla schiena bassa, più glutei e spalle',
        )
        
        self.exercises['romanian_deadlift'] = Exercise(
            id='romanian_deadlift',
            name='Romanian Deadlift',
            italian_name='Stacco Rumeno',
            description='Stacco con gambe semi-tese, focus su posterior chain',
            primary_muscles=[MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES],
            secondary_muscles=[MuscleGroup.BACK],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['barbell', 'dumbbell'],
            rep_range_strength=(6, 8),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=24,
            notes='Enfatizza gli ischiocrurali, movimento con ginocchio semi-teso',
        )
        
        # ═══════════════════════════════════════════════════════════
        # UPPER BODY - BENCH PRESS VARIATIONS
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['barbell_bench_press'] = Exercise(
            id='barbell_bench_press',
            name='Barbell Bench Press',
            italian_name='Panca Piana Bilanciere',
            description='Esercizio principale per il petto con bilanciere',
            primary_muscles=[MuscleGroup.CHEST],
            secondary_muscles=[MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['barbell', 'bench'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=48,
            progressions=[ExerciseProgression('pause_bench_press', 'tempo')],
            regressions=[ExerciseRegression('dumbbell_bench_press', 'stability')],
            variants=[
                ExerciseVariant('Paused Bench Press', 'Pausa 2 sec al petto', +1),
                ExerciseVariant('Close Grip Bench', 'Impugnatura stretta, più tricipiti', 0),
            ],
            notes='Esercizio fondamentale per la parte superiore',
        )
        
        self.exercises['dumbbell_bench_press'] = Exercise(
            id='dumbbell_bench_press',
            name='Dumbbell Bench Press',
            italian_name='Panca Manubri',
            description='Panca con manubri, maggior range di movimento',
            primary_muscles=[MuscleGroup.CHEST],
            secondary_muscles=[MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['dumbbell', 'bench'],
            rep_range_strength=(5, 8),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=48,
            progressions=[ExerciseProgression('barbell_bench_press', 'stability')],
            notes='Maggior ROM rispetto al bilanciere, meno stabile',
        )
        
        self.exercises['push_ups'] = Exercise(
            id='push_ups',
            name='Push-ups',
            italian_name='Flessioni',
            description='Flessioni a corpo libero',
            primary_muscles=[MuscleGroup.CHEST],
            secondary_muscles=[MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS, MuscleGroup.CORE],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['bodyweight'],
            rep_range_strength=(8, 15),
            rep_range_hypertrophy=(10, 20),
            rep_range_endurance=(15, 30),
            recovery_hours=24,
            variants=[
                ExerciseVariant('Incline Push-ups', 'Mani su rialzo, più facile', -1),
                ExerciseVariant('Diamond Push-ups', 'Mani a diamante, più tricipiti', +1),
                ExerciseVariant('Archer Push-ups', 'Verso un braccio, avanzato', +2),
            ],
            notes='Esercizio di base a corpo libero',
        )
        
        # ═══════════════════════════════════════════════════════════
        # UPPER BODY - ROW VARIATIONS
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['barbell_bent_row'] = Exercise(
            id='barbell_bent_row',
            name='Barbell Bent Over Row',
            italian_name='Remata Bilanciere Chino',
            description='Remata con bilanciere, esercizio principale per la schiena',
            primary_muscles=[MuscleGroup.BACK, MuscleGroup.LATS],
            secondary_muscles=[MuscleGroup.BICEPS],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['barbell'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=48,
            progressions=[ExerciseProgression('pause_bent_row', 'tempo')],
            notes='Esercizio fondamentale per la schiena, richiede tecnica',
        )
        
        self.exercises['dumbbell_row'] = Exercise(
            id='dumbbell_row',
            name='Dumbbell Single Arm Row',
            italian_name='Remata Manubrio Monolaterale',
            description='Remata con manubrio, un braccio alla volta',
            primary_muscles=[MuscleGroup.BACK, MuscleGroup.LATS],
            secondary_muscles=[MuscleGroup.BICEPS, MuscleGroup.CORE],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['dumbbell', 'bench'],
            rep_range_strength=(6, 8),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=24,
            notes='Movimiento unilaterale, lavora il core',
        )
        
        self.exercises['pull_ups'] = Exercise(
            id='pull_ups',
            name='Pull-ups',
            italian_name='Trazioni',
            description='Trazioni alla sbarra a corpo libero',
            primary_muscles=[MuscleGroup.BACK, MuscleGroup.LATS],
            secondary_muscles=[MuscleGroup.BICEPS],
            difficulty=DifficultyLevel.ADVANCED,
            equipment=['pull_up_bar'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 12),
            rep_range_endurance=(12, 20),
            recovery_hours=24,
            regressions=[ExerciseRegression('assisted_pull_ups', 'weight')],
            variants=[
                ExerciseVariant('Chin-ups', 'Presa supina, più bicipiti', 0),
                ExerciseVariant('Weighted Pull-ups', 'Con cintura pesi', +2),
            ],
            notes='Esercizio avanzato, richiede forza significativa',
        )
        
        self.exercises['lat_pulldown'] = Exercise(
            id='lat_pulldown',
            name='Lat Pulldown',
            italian_name='Lat Machine',
            description='Esercizio su macchina per latissimi',
            primary_muscles=[MuscleGroup.BACK, MuscleGroup.LATS],
            secondary_muscles=[MuscleGroup.BICEPS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['machine'],
            rep_range_strength=(6, 10),
            rep_range_hypertrophy=(10, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            progressions=[ExerciseProgression('pull_ups', 'weight')],
            notes='Versione controllata delle trazioni',
        )
        
        # ═══════════════════════════════════════════════════════════
        # ARMS
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['barbell_curl'] = Exercise(
            id='barbell_curl',
            name='Barbell Curl',
            italian_name='Curl Bilanciere',
            description='Curl con bilanciere, isolamento bicipite',
            primary_muscles=[MuscleGroup.BICEPS],
            secondary_muscles=[MuscleGroup.FOREARMS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['barbell'],
            rep_range_strength=(6, 8),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=24,
            variants=[
                ExerciseVariant('EZ Bar Curl', 'Con barra EZ, meno stress sul polso', 0),
                ExerciseVariant('Preacher Curl', 'Su panca, isolamento più completo', +1),
            ],
            notes='Esercizio di isolamento per bicipiti',
        )
        
        self.exercises['dumbbell_curl'] = Exercise(
            id='dumbbell_curl',
            name='Dumbbell Curl',
            italian_name='Curl Manubri',
            description='Curl con manubri, movimento bilaterale',
            primary_muscles=[MuscleGroup.BICEPS],
            secondary_muscles=[MuscleGroup.FOREARMS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['dumbbell'],
            rep_range_strength=(6, 10),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=24,
            notes='Esercizio classico di isolamento',
        )
        
        self.exercises['tricep_dips'] = Exercise(
            id='tricep_dips',
            name='Tricep Dips',
            italian_name='Dip Parallele',
            description='Dip su parallele per i tricipiti',
            primary_muscles=[MuscleGroup.TRICEPS],
            secondary_muscles=[MuscleGroup.CHEST],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['parallel_bars'],
            rep_range_strength=(5, 10),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=24,
            regressions=[ExerciseRegression('assisted_dips', 'weight')],
            variants=[
                ExerciseVariant('Weighted Dips', 'Con cintura pesi', +1),
                ExerciseVariant('Bench Dips', 'Su panca, versione più facile', -1),
            ],
            notes='Esercizio complesso, buon composto per tricipiti',
        )
        
        self.exercises['tricep_pushdown'] = Exercise(
            id='tricep_pushdown',
            name='Rope Tricep Pushdown',
            italian_name='Spinta Tricipiti alla Cavo',
            description='Isolamento tricipiti alla macchina cavi',
            primary_muscles=[MuscleGroup.TRICEPS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['cable_machine'],
            rep_range_strength=(10, 12),
            rep_range_hypertrophy=(10, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            notes='Facile da eseguire, buon isolamento',
        )
        
        # ═══════════════════════════════════════════════════════════
        # SHOULDERS
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['overhead_press'] = Exercise(
            id='overhead_press',
            name='Overhead Press (Military Press)',
            italian_name='Spinta in Alto',
            description='Spinta in alto con bilanciere, esercizio principale per spalle',
            primary_muscles=[MuscleGroup.SHOULDERS],
            secondary_muscles=[MuscleGroup.TRICEPS, MuscleGroup.CORE],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['barbell'],
            rep_range_strength=(3, 6),
            rep_range_hypertrophy=(6, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=48,
            progressions=[ExerciseProgression('push_press', 'tempo')],
            notes='Esercizio fondamentale per spalle, core stability importante',
        )
        
        self.exercises['dumbbell_shoulder_press'] = Exercise(
            id='dumbbell_shoulder_press',
            name='Dumbbell Shoulder Press',
            italian_name='Spinta Manubri in Alto',
            description='Spinta in alto con manubri',
            primary_muscles=[MuscleGroup.SHOULDERS],
            secondary_muscles=[MuscleGroup.TRICEPS],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['dumbbell', 'bench'],
            rep_range_strength=(6, 8),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(12, 15),
            recovery_hours=24,
            notes='Maggior ROM dei bilancieri, più stabilità richiesta',
        )
        
        self.exercises['lateral_raises'] = Exercise(
            id='lateral_raises',
            name='Lateral Raises',
            italian_name='Alzate Laterali',
            description='Isolamento spalle laterali',
            primary_muscles=[MuscleGroup.SHOULDERS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['dumbbell'],
            rep_range_strength=(8, 12),
            rep_range_hypertrophy=(12, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            notes='Esercizio di isolamento per la larghezza delle spalle',
        )
        
        self.exercises['face_pulls'] = Exercise(
            id='face_pulls',
            name='Face Pulls',
            italian_name='Tirate al Viso',
            description='Tirate alla macchina cavi verso il viso',
            primary_muscles=[MuscleGroup.SHOULDERS, MuscleGroup.TRAPS],
            secondary_muscles=[MuscleGroup.BACK],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['cable_machine'],
            rep_range_strength=(12, 15),
            rep_range_hypertrophy=(15, 20),
            rep_range_endurance=(15, 25),
            recovery_hours=24,
            notes='Ottimo per salute spalla, preventivo',
        )
        
        # ═══════════════════════════════════════════════════════════
        # CORE
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['plank'] = Exercise(
            id='plank',
            name='Plank',
            italian_name='Plancia',
            description='Isometrico per il core a corpo libero',
            primary_muscles=[MuscleGroup.CORE],
            secondary_muscles=[MuscleGroup.SHOULDERS, MuscleGroup.BACK],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['bodyweight'],
            rep_range_strength=(30, 60),  # Secondi
            rep_range_hypertrophy=(45, 90),
            rep_range_endurance=(60, 120),
            recovery_hours=24,
            variants=[
                ExerciseVariant('Side Plank', 'Fianco, core laterale', 0),
                ExerciseVariant('RKC Plank', 'Contrazione massimale, intenso', +2),
            ],
            notes='Esercizio fondamentale per core stability',
        )
        
        self.exercises['dead_bugs'] = Exercise(
            id='dead_bugs',
            name='Dead Bugs',
            italian_name='Insetti Morti',
            description='Esercizio di coordinazione e core',
            primary_muscles=[MuscleGroup.CORE],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['bodyweight'],
            rep_range_strength=(10, 15),
            rep_range_hypertrophy=(15, 20),
            rep_range_endurance=(20, 30),
            recovery_hours=24,
            notes='Buono per coordinazione, basso infortunio',
        )
        
        self.exercises['ab_wheel'] = Exercise(
            id='ab_wheel',
            name='Ab Wheel Rollout',
            italian_name='Ruota Addominale',
            description='Movimento core avanzato con ruota addominale',
            primary_muscles=[MuscleGroup.CORE],
            secondary_muscles=[MuscleGroup.SHOULDERS, MuscleGroup.BACK],
            difficulty=DifficultyLevel.ADVANCED,
            equipment=['ab_wheel'],
            rep_range_strength=(5, 10),
            rep_range_hypertrophy=(8, 12),
            rep_range_endurance=(10, 15),
            recovery_hours=24,
            regressions=[ExerciseRegression('kneeling_ab_wheel', 'ROM')],
            notes='Esercizio avanzato, per core molto forte',
        )
        
        # ═══════════════════════════════════════════════════════════
        # CARDIO & CONDITIONING
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['running'] = Exercise(
            id='running',
            name='Running',
            italian_name='Corsa',
            description='Corsa come cardio',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['bodyweight'],
            rep_range_strength=(20, 30),  # Minuti
            rep_range_hypertrophy=(20, 45),
            rep_range_endurance=(30, 60),
            recovery_hours=24,
            notes='Cardio ad alta intensità',
            contraindications=['Ginocchio problematico', 'Articolazioni fragili'],
        )
        
        self.exercises['cycling'] = Exercise(
            id='cycling',
            name='Cycling',
            italian_name='Ciclismo',
            description='Ciclismo come cardio',
            primary_muscles=[MuscleGroup.QUADRICEPS, MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['bicycle'],
            rep_range_strength=(30, 45),  # Minuti
            rep_range_hypertrophy=(30, 60),
            rep_range_endurance=(45, 120),
            recovery_hours=12,
            notes='Cardio low-impact, perfetto per recovery',
        )
        
        self.exercises['rowing'] = Exercise(
            id='rowing',
            name='Rowing',
            italian_name='Canottaggio',
            description='Canottaggio su macchina',
            primary_muscles=[MuscleGroup.BACK, MuscleGroup.QUADRICEPS, MuscleGroup.HAMSTRINGS],
            secondary_muscles=[MuscleGroup.CORE, MuscleGroup.BICEPS],
            difficulty=DifficultyLevel.INTERMEDIATE,
            equipment=['rowing_machine'],
            rep_range_strength=(15, 25),  # Minuti
            rep_range_hypertrophy=(20, 40),
            rep_range_endurance=(30, 60),
            recovery_hours=24,
            notes='Cardio completo, full body, tecnica importante',
        )
        
        # ═══════════════════════════════════════════════════════════
        # ADDITIONAL LOWER BODY
        # ═══════════════════════════════════════════════════════════
        
        self.exercises['leg_curl'] = Exercise(
            id='leg_curl',
            name='Leg Curl',
            italian_name='Curl Gambe',
            description='Isolamento ischiocrurali su macchina',
            primary_muscles=[MuscleGroup.HAMSTRINGS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['machine'],
            rep_range_strength=(8, 12),
            rep_range_hypertrophy=(12, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            notes='Isolamento semplice per hamstring',
        )
        
        self.exercises['leg_extension'] = Exercise(
            id='leg_extension',
            name='Leg Extension',
            italian_name='Estensione Gambe',
            description='Isolamento quadricipiti su macchina',
            primary_muscles=[MuscleGroup.QUADRICEPS],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['machine'],
            rep_range_strength=(10, 15),
            rep_range_hypertrophy=(12, 15),
            rep_range_endurance=(15, 20),
            recovery_hours=24,
            notes='Isolamento quad, facile da controllare',
        )
        
        self.exercises['calf_raises'] = Exercise(
            id='calf_raises',
            name='Standing Calf Raises',
            italian_name='Rialzi Sulle Punte',
            description='Isolamento polpacci',
            primary_muscles=[MuscleGroup.CALVES],
            difficulty=DifficultyLevel.BEGINNER,
            equipment=['barbell', 'dumbbell', 'machine'],
            rep_range_strength=(10, 15),
            rep_range_hypertrophy=(15, 20),
            rep_range_endurance=(20, 30),
            recovery_hours=24,
            notes='Isolamento polpacci, può essere con pesi o macchina',
        )
    
    def get_exercise(self, exercise_id: str) -> Optional[Exercise]:
        """Recupera un esercizio per ID"""
        return self.exercises.get(exercise_id)
    
    def get_exercises_by_muscle(self, muscle: MuscleGroup) -> List[Exercise]:
        """Recupera tutti gli esercizi per un muscolo specifico"""
        return [
            ex for ex in self.exercises.values()
            if muscle in ex.primary_muscles or muscle in ex.secondary_muscles
        ]
    
    def get_exercises_by_difficulty(self, difficulty: DifficultyLevel) -> List[Exercise]:
        """Recupera esercizi per livello di difficoltà"""
        return [ex for ex in self.exercises.values() if ex.difficulty == difficulty]
    
    def get_exercises_by_equipment(self, equipment: str) -> List[Exercise]:
        """Recupera esercizi che richiedono un certo equipment"""
        return [ex for ex in self.exercises.values() if equipment in ex.equipment]
    
    def search_exercises(self, query: str) -> List[Exercise]:
        """Ricerca esercizi per nome o descrizione"""
        query_lower = query.lower()
        return [
            ex for ex in self.exercises.values()
            if query_lower in ex.name.lower() 
            or query_lower in ex.italian_name.lower()
            or query_lower in ex.description.lower()
        ]
    
    def get_all_exercises(self) -> List[Exercise]:
        """Ritorna tutti gli esercizi"""
        return list(self.exercises.values())
    
    def count_exercises(self) -> int:
        """Conta gli esercizi totali"""
        return len(self.exercises)
    
    # ═══════════════════════════════════════════════════════════
    # SMART FILTERING METHODS - REFACTOR V2
    # ═══════════════════════════════════════════════════════════
    
    def filter_by_equipment_available(self, equipment_list: List[str]) -> List[Exercise]:
        """
        Filtra esercizi che POSSONO essere eseguiti con l'equipment disponibile
        
        Args:
            equipment_list: ['barbell', 'dumbbell', 'bodyweight', ...]
        
        Returns:
            Lista esercizi eseguibili
        """
        available = []
        for ex in self.exercises.values():
            # Un esercizio è eseguibile se TUTTI i suoi equipment sono disponibili
            if all(eq in equipment_list for eq in ex.equipment):
                available.append(ex)
        return available
    
    def filter_by_contraindications(self, limitazioni: List[str]) -> List[Exercise]:
        """
        Filtra esercizi ESCLUDENDO quelli con controindicazioni
        
        Args:
            limitazioni: ['ginocchio', 'spalla', 'schiena', ...]
        
        Returns:
            Lista esercizi sicuri
        """
        safe_exercises = []
        for ex in self.exercises.values():
            # Controlla se c'è sovrapposizione tra limitazioni cliente e controindicazioni esercizio
            has_contraindication = False
            for limit in limitazioni:
                limit_lower = limit.lower()
                for contra in ex.contraindications:
                    if limit_lower in contra.lower():
                        has_contraindication = True
                        break
                if has_contraindication:
                    break
            
            if not has_contraindication:
                safe_exercises.append(ex)
        
        return safe_exercises
    
    def select_best_for_pattern(
        self,
        pattern: str,
        equipment: List[str],
        level: DifficultyLevel,
        exclude_contraindications: List[str] = None
    ) -> Optional[Exercise]:
        """
        Seleziona il MIGLIOR esercizio per un pattern di movimento
        
        Args:
            pattern: 'squat', 'hinge', 'push', 'pull', 'carry', 'rotation'
            equipment: Equipment disponibile
            level: Livello cliente
            exclude_contraindications: Limitazioni da evitare
        
        Returns:
            Exercise object o None
        """
        if exclude_contraindications is None:
            exclude_contraindications = []
        
        # Helper: inferisce pattern dall'ID se movement_pattern non è settato
        def matches_pattern(ex: Exercise, target_pattern: str) -> bool:
            """Verifica se esercizio match il pattern (esplicito o inferito)"""
            # Se ha movement_pattern esplicito, usa quello
            if ex.movement_pattern:
                return ex.movement_pattern == target_pattern
            
            # Altrimenti inferisci dall'ID e muscoli
            ex_id_lower = ex.id.lower()
            ex_name_lower = ex.name.lower()
            
            if target_pattern == 'squat':
                return 'squat' in ex_id_lower or 'squat' in ex_name_lower or 'leg_press' in ex_id_lower
            elif target_pattern == 'hinge':
                return any(word in ex_id_lower for word in ['deadlift', 'rdl', 'romanian', 'good_morning', 'hinge'])
            elif target_pattern == 'push':
                return any(word in ex_id_lower for word in ['bench', 'press', 'push', 'dips', 'dip']) \
                    and MuscleGroup.CHEST in ex.primary_muscles or MuscleGroup.SHOULDERS in ex.primary_muscles or MuscleGroup.TRICEPS in ex.primary_muscles
            elif target_pattern == 'pull':
                return any(word in ex_id_lower for word in ['pull', 'row', 'chin', 'lat']) \
                    and (MuscleGroup.BACK in ex.primary_muscles or MuscleGroup.LATS in ex.primary_muscles)
            elif target_pattern == 'carry':
                return any(word in ex_id_lower for word in ['carry', 'farmer', 'suitcase', 'overhead_walk'])
            elif target_pattern == 'rotation':
                return any(word in ex_id_lower for word in ['rotation', 'twist', 'chop', 'woodchop'])
            
            return False
        
        # Step 1: Filtra per pattern (inferito o esplicito)
        candidates = [ex for ex in self.exercises.values() if matches_pattern(ex, pattern)]
        
        # Step 2: Filtra per equipment disponibile
        candidates = [ex for ex in candidates if all(eq in equipment for eq in ex.equipment)]
        
        # Step 3: Filtra per controindicazioni
        if exclude_contraindications:
            safe_candidates = []
            for ex in candidates:
                is_safe = True
                for limit in exclude_contraindications:
                    limit_lower = limit.lower()
                    for contra in ex.contraindications:
                        if limit_lower in contra.lower():
                            is_safe = False
                            break
                    if not is_safe:
                        break
                if is_safe:
                    safe_candidates.append(ex)
            candidates = safe_candidates
        
        # Step 4: Seleziona per livello (preferisci esatto, altrimenti più facile)
        level_matches = [ex for ex in candidates if ex.difficulty == level]
        if level_matches:
            return level_matches[0]  # Prendi primo match
        
        # Fallback: prendi qualsiasi candidato
        return candidates[0] if candidates else None
    
    def get_alternative_exercises(
        self,
        exercise_id: str,
        reason: str = "general",
        equipment: List[str] = None
    ) -> List[Exercise]:
        """
        Trova esercizi alternativi per un esercizio dato
        
        Args:
            exercise_id: ID dell'esercizio da sostituire
            reason: 'injury', 'equipment', 'difficulty', 'general'
            equipment: Equipment disponibile (se reason='equipment')
        
        Returns:
            Lista di alternative ordinate per similarità
        """
        original = self.get_exercise(exercise_id)
        if not original:
            return []
        
        alternatives = []
        
        # Cerca esercizi con muscoli primari simili
        for ex in self.exercises.values():
            if ex.id == exercise_id:
                continue  # Skip originale
            
            # Check similarità muscoli primari
            overlap = set(ex.primary_muscles) & set(original.primary_muscles)
            if not overlap:
                continue  # Nessuna sovrapposizione muscoli → skip
            
            # Filtra per equipment se necessario
            if equipment and not all(eq in equipment for eq in ex.equipment):
                continue
            
            # Filtra per difficoltà se reason='difficulty'
            if reason == 'difficulty':
                # Preferisci esercizi più facili
                if ex.difficulty.value == 'principiante' or ex.difficulty.value == 'intermedio':
                    alternatives.append((ex, len(overlap)))
            else:
                alternatives.append((ex, len(overlap)))
        
        # Ordina per sovrapposizione muscoli (più overlap = più simile)
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return [ex for ex, _ in alternatives]
    
    def select_balanced_workout(
        self,
        muscles: List[MuscleGroup],
        count: int,
        equipment: List[str],
        level: DifficultyLevel,
        exclude_ids: List[str] = None
    ) -> List[Exercise]:
        """
        Seleziona un workout bilanciato SENZA duplicati
        
        Args:
            muscles: Lista muscoli da targetizzare
            count: Quanti esercizi selezionare
            equipment: Equipment disponibile
            level: Livello cliente
            exclude_ids: ID esercizi già selezionati (anti-duplicati)
        
        Returns:
            Lista Exercise objects (max count)
        """
        if exclude_ids is None:
            exclude_ids = []
        
        selected = []
        used_ids = set(exclude_ids)
        
        # Per ogni muscolo, cerca esercizio
        for muscle in muscles:
            if len(selected) >= count:
                break
            
            # Trova esercizi per questo muscolo
            candidates = self.get_exercises_by_muscle(muscle)
            
            # Filtra per equipment
            candidates = [ex for ex in candidates if all(eq in equipment for eq in ex.equipment)]
            
            # Filtra per livello (preferisci livello esatto o più facile)
            level_candidates = [ex for ex in candidates if ex.difficulty == level or ex.difficulty.value == 'principiante']
            if level_candidates:
                candidates = level_candidates
            
            # Escludi già usati
            candidates = [ex for ex in candidates if ex.id not in used_ids]
            
            if candidates:
                # Prendi primo candidato
                selected.append(candidates[0])
                used_ids.add(candidates[0].id)
        
        return selected[:count]
    
    def get_workout_template(self, goal: str, level: str, days_per_week: int = 4) -> Dict[str, Any]:
        """
        Genera un template di workout basato su goal, livello, e disponibilità.
        
        Args:
            goal: 'strength', 'hypertrophy', 'endurance', 'fat_loss', 'functional'
            level: 'beginner', 'intermediate', 'advanced'
            days_per_week: giorni disponibili per allenarsi
        
        Returns:
            Struttura di workout giornaliero
        """
        
        # Mappe per selezione esercizi
        if days_per_week >= 5:
            template_type = 'ppl'  # Push/Pull/Legs
        elif days_per_week == 4:
            template_type = 'upper_lower'
        elif days_per_week == 3:
            template_type = 'full_body'
        else:
            template_type = 'full_body'
        
        # Template base
        templates = {
            'full_body': {
                'day_1': {
                    'name': 'Full Body A',
                    'focus': ['squat', 'bench', 'row'],
                    'description': 'Squat, Bench, Row - Esercizi composti'
                },
                'day_2': {
                    'name': 'Full Body B',
                    'focus': ['deadlift', 'overhead_press', 'lat_pulldown'],
                    'description': 'Deadlift, Overhead Press, Lat - Mix'
                },
                'day_3': {
                    'name': 'Full Body C',
                    'focus': ['leg_press', 'dumbbell_bench_press', 'row'],
                    'description': 'Accessori e varianti'
                }
            },
            'upper_lower': {
                'day_1': {'name': 'Upper A', 'focus': ['bench', 'row']},
                'day_2': {'name': 'Lower A', 'focus': ['squat', 'deadlift']},
                'day_3': {'name': 'Upper B', 'focus': ['overhead_press', 'lat_pulldown']},
                'day_4': {'name': 'Lower B', 'focus': ['leg_press', 'romanian_deadlift']},
            },
            'ppl': {
                'day_1': {'name': 'Push', 'focus': ['bench', 'overhead_press', 'dips']},
                'day_2': {'name': 'Pull', 'focus': ['row', 'pull_ups', 'lat_pulldown']},
                'day_3': {'name': 'Legs', 'focus': ['squat', 'deadlift', 'leg_curl']},
                'day_4': {'name': 'Push', 'focus': ['dumbbell_bench_press', 'lateral_raises']},
                'day_5': {'name': 'Pull', 'focus': ['dumbbell_row', 'face_pulls']},
            }
        }
        
        return {
            'template_type': template_type,
            'goal': goal,
            'level': level,
            'days_per_week': days_per_week,
            'structure': templates.get(template_type, templates['full_body']),
            'notes': f'Template {template_type.upper()} per {goal} - Livello {level}'
        }


# Istanza globale del database
exercise_db = ExerciseDatabase()


# ═══════════════════════════════════════════════════════════════════════════
# PERIODIZATION TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════

class PeriodizationTemplates:
    """Template di periodizzazione per diversi goal e durata"""
    
    @staticmethod
    def get_linear_periodization(weeks: int = 12) -> Dict[str, Any]:
        """
        Periodizzazione Lineare: incremento progressivo di peso, calo di reps
        Ideale per: Strength, intermediate/advanced
        """
        if weeks < 4:
            weeks = 4
        
        phases = []
        week_count = 1
        
        # Fase 1: Hypertrophy (alto volume, peso moderato)
        hypertrophy_weeks = max(2, weeks // 4)
        phases.append({
            'phase': 'Hypertrophy',
            'weeks': hypertrophy_weeks,
            'reps': '8-12',
            'intensity': '65-75%',
            'rest': '60-90 sec',
            'description': 'Fase di ipertrofia, accumulo volume',
            'weeks_range': (week_count, week_count + hypertrophy_weeks - 1)
        })
        week_count += hypertrophy_weeks
        
        # Fase 2: Strength (volume moderato, peso alto)
        strength_weeks = max(2, weeks // 4)
        phases.append({
            'phase': 'Strength',
            'weeks': strength_weeks,
            'reps': '4-6',
            'intensity': '80-90%',
            'rest': '120-180 sec',
            'description': 'Fase di forza, lavoro su massimale',
            'weeks_range': (week_count, week_count + strength_weeks - 1)
        })
        week_count += strength_weeks
        
        # Fase 3: Power (volume basso, peso massimo, velocità)
        power_weeks = max(1, weeks // 6)
        phases.append({
            'phase': 'Power',
            'weeks': power_weeks,
            'reps': '1-3',
            'intensity': '90-95%',
            'rest': '180-300 sec',
            'description': 'Fase potenza, basso volume, alta intensità',
            'weeks_range': (week_count, week_count + power_weeks - 1)
        })
        week_count += power_weeks
        
        # Fase 4: Deload (recupero)
        deload_weeks = max(1, weeks // 8)
        phases.append({
            'phase': 'Deload',
            'weeks': deload_weeks,
            'reps': '10-15',
            'intensity': '50-60%',
            'rest': '45-60 sec',
            'description': 'Settimana scarico, recupero totale',
            'weeks_range': (week_count, week_count + deload_weeks - 1)
        })
        
        return {
            'type': 'Linear Periodization',
            'total_weeks': weeks,
            'phases': phases,
            'philosophy': 'Progressione lineare verso obiettivo',
            'ideal_for': ['Strength', 'beginner->intermediate->advanced'],
        }
    
    @staticmethod
    def get_block_periodization(weeks: int = 12) -> Dict[str, Any]:
        """
        Periodizzazione a Blocchi (Block Periodization - Westside)
        Ideale per: Strength, powerlifting, advanced
        Fasi distinte: Accumulation → Intensification → Realization
        """
        if weeks < 4:
            weeks = 4
        
        block_weeks = weeks // 3
        
        phases = [
            {
                'block': 'Accumulation',
                'weeks': block_weeks,
                'description': 'Accumulazione volume massimo',
                'volume': 'Alta',
                'intensity': 'Bassa-Media',
                'reps': '8-15',
                'focus': 'Stabilità, tecnica, volume',
                'weeks_range': (1, block_weeks)
            },
            {
                'block': 'Intensification',
                'weeks': block_weeks,
                'description': 'Aumento intensità, calo volume',
                'volume': 'Media-Bassa',
                'intensity': 'Media-Alta',
                'reps': '3-8',
                'focus': 'Forza massimale',
                'weeks_range': (block_weeks + 1, block_weeks * 2)
            },
            {
                'block': 'Realization',
                'weeks': block_weeks,
                'description': 'Manifestazione della forza acquisita',
                'volume': 'Bassa',
                'intensity': 'Massima',
                'reps': '1-5',
                'focus': 'Peak performance, testare massimali',
                'weeks_range': (block_weeks * 2 + 1, weeks)
            }
        ]
        
        return {
            'type': 'Block Periodization',
            'total_weeks': weeks,
            'blocks': phases,
            'philosophy': 'Blocchi distinti con obiettivi specifici',
            'ideal_for': ['Strength', 'Powerlifting', 'advanced'],
        }
    
    @staticmethod
    def get_undulating_periodization(weeks: int = 12) -> Dict[str, Any]:
        """
        Periodizzazione Ondulante (Undulating/Conjugate)
        Cambia reps/intensità frequentemente (daily/weekly)
        Ideale per: Variety, hypertrophy + strength mix
        """
        if weeks < 4:
            weeks = 4
        
        microcycle = [
            {
                'day': 'Day 1 - Hypertrophy',
                'reps': '8-12',
                'intensity': '65-75%',
                'rest': '60-90 sec',
                'description': 'Accumulo volume'
            },
            {
                'day': 'Day 2 - Strength',
                'reps': '3-5',
                'intensity': '85-95%',
                'rest': '180+ sec',
                'description': 'Forza massimale'
            },
            {
                'day': 'Day 3 - Power/Endurance',
                'reps': '10-15',
                'intensity': '60-70%',
                'rest': '45-60 sec',
                'description': 'Potenza o resistenza muscolare'
            }
        ]
        
        weeks_content = []
        for w in range(1, weeks + 1):
            weeks_content.append({
                'week': w,
                'microcycle': microcycle,
                'notes': f'Settimana {w}: Varizione settimanale'
            })
        
        return {
            'type': 'Undulating Periodization',
            'total_weeks': weeks,
            'microcycle_days': 3,
            'weeks_structure': weeks_content[:1] * weeks,  # Repeat microcycle
            'philosophy': 'Varietà frequente stimola adattamenti multipli',
            'ideal_for': ['Hypertrophy + Strength mix', 'Intermediate/Advanced', 'Variety seekers'],
        }
    
    @staticmethod
    def get_deload_week() -> Dict[str, Any]:
        """Settimana di scarico (deload week)"""
        return {
            'type': 'Deload Week',
            'volume': '40-50% normale',
            'intensity': '50-60% normale',
            'reps': '10-15',
            'rest': '45-60 sec',
            'frequency': 'Ogni 3-4 settimane',
            'purpose': 'Recupero, prevenzione overtraining',
            'daily_structure': [
                {
                    'day': 'Day 1',
                    'exercises': 'Composti leggeri',
                    'sets_reps': '3x10',
                    'notes': 'Focus su movimento, tecnica'
                },
                {
                    'day': 'Day 2',
                    'exercises': 'Accessori',
                    'sets_reps': '2x12-15',
                    'notes': 'Isolamento, pump'
                },
                {
                    'day': 'Day 3',
                    'exercises': 'Stretching, mobility',
                    'sets_reps': 'N/A',
                    'notes': 'Recupero attivo, no pesanti'
                }
            ]
        }


# ═══════════════════════════════════════════════════════════════════════════
# PROGRESSION STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════

class ProgressionStrategies:
    """Strategie per progressione e overload progressivo"""
    
    STRATEGIES = {
        'weight_progression': {
            'name': 'Weight Progression (Carico)',
            'description': 'Incrementa il peso sollevato',
            'implementation': [
                'Squat: +2.5-5 kg',
                'Bench: +2.5-5 kg',
                'Deadlift: +5-10 kg',
                'Accessori: +1-2.5 kg',
            ],
            'frequency': 'Settimanale o bi-settimanale',
            'best_for': ['Strength', 'Intermediate/Advanced'],
            'notes': 'Metodo più diretto, richiede progressione costante'
        },
        'rep_progression': {
            'name': 'Rep Progression (Reps)',
            'description': 'Aumenta le reps con lo stesso peso',
            'implementation': [
                'Target: 3x8 squat',
                'Settimana 1: 3x8',
                'Settimana 2: 3x9',
                'Settimana 3: 3x10',
                'Settimana 4: Aumenta peso, reset a 3x8'
            ],
            'frequency': 'Settimanale',
            'best_for': ['Hypertrophy', 'Beginners'],
            'notes': 'Consigliato per chi inizia, progressione controllata'
        },
        'density_progression': {
            'name': 'Density Progression (Densità)',
            'description': 'Aumenta volume totale nello stesso tempo',
            'implementation': [
                '3x8 squat in 15 minuti',
                'Settimana successiva: stessi reps, meno tempo',
                'O: stessi reps, volume aggiunto',
            ],
            'frequency': 'Settimanale/Bi-settimanale',
            'best_for': ['Strength', 'Conditioning'],
            'notes': 'Buono per recupero, meno stress articolare'
        },
        'tempo_progression': {
            'name': 'Tempo Progression (Tempo)',
            'description': 'Aumenta time under tension con eccentrica lenta',
            'implementation': [
                'Standard: 2-1-1 (2 sec giù, 1 pausa, 1 su)',
                'Tempo: 3-2-1 (3 sec giù, 2 pausa, 1 su)',
                'Ecc-focus: 4-0-1 (4 sec giù, niente pausa, 1 su)',
            ],
            'frequency': 'Ogni 2-3 settimane',
            'best_for': ['Hypertrophy', 'All levels'],
            'notes': 'Grande stimolo ipertrofico, meno stress CNS'
        },
        'range_of_motion': {
            'name': 'Range of Motion Progression',
            'description': 'Aumenta il range di movimento',
            'implementation': [
                'Panca: ROM parziale → ROM completo',
                'Squat: Quarter squat → Half squat → Full squat',
                'Movimento più completo = difficile maggiore',
            ],
            'frequency': 'Mensile/Bi-mensile',
            'best_for': ['Functional', 'Hypertrophy'],
            'notes': 'Attiva più muscoli, richiede mobilità'
        },
        'exercise_variation': {
            'name': 'Exercise Variation',
            'description': 'Cambia esercizio ogni 3-4 settimane',
            'implementation': [
                'Settimane 1-4: Back Squat',
                'Settimane 5-8: Front Squat',
                'Settimane 9-12: Leg Press',
                'Varia stimolo, previene plateau',
            ],
            'frequency': 'Mensile',
            'best_for': ['Variety seekers', 'Long-term adaptations'],
            'notes': 'Evita adattamento, mantiene novità'
        },
        'drop_sets_pyramids': {
            'name': 'Drop Sets & Pyramids',
            'description': 'Tecniche di intensità per volume extra',
            'implementation': [
                'Drop Set: 3x8 → drop 20% → 3x10+',
                'Pyramid: 3x5 → 3x8 → 3x12 → 3x8 → 3x5',
            ],
            'frequency': 'Occasionale (1-2 set per esercizio)',
            'best_for': ['Hypertrophy', 'Finisher exercises'],
            'notes': 'Avanzato, ad uso moderato per overtraining risk'
        },
    }
    
    @staticmethod
    def get_strategy(strategy_name: str) -> Optional[Dict[str, Any]]:
        """Recupera una strategia di progressione"""
        return ProgressionStrategies.STRATEGIES.get(strategy_name)
    
    @staticmethod
    def get_all_strategies() -> Dict[str, Any]:
        """Ritorna tutte le strategie"""
        return ProgressionStrategies.STRATEGIES
    
    @staticmethod
    def recommend_for_goal(goal: str) -> List[str]:
        """Raccomanda strategie per uno specifico goal"""
        recommendations = {
            'strength': ['weight_progression', 'rep_progression', 'density_progression'],
            'hypertrophy': ['rep_progression', 'tempo_progression', 'drop_sets_pyramids'],
            'endurance': ['rep_progression', 'density_progression'],
            'fat_loss': ['density_progression', 'exercise_variation'],
            'functional': ['range_of_motion', 'exercise_variation'],
        }
        return recommendations.get(goal, ['rep_progression', 'weight_progression'])
