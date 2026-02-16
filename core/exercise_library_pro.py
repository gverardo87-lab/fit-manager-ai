# core/exercise_library_pro.py
"""
PROFESSIONAL Exercise Library - Compete con Trainerize/TrueCoach

Features:
- Video YouTube professionali HD per ogni esercizio
- Istruzioni step-by-step dettagliate
- Form cues e common mistakes
- Movement patterns e planes
- Muscle details espansi (primary/secondary/stabilizers)
"""

from typing import List, Dict
from core.exercise_database import Exercise, MuscleGroup, DifficultyLevel


def get_professional_exercises() -> List[Dict]:
    """Ritorna esercizi con TUTTI i dettagli professionali (video, istruzioni, form cues, ecc.)"""

    exercises = []

    # ========== SQUAT PATTERN ==========

    exercises.append({
        'id': 'back_squat',
        'name': 'Back Squat',
        'italian_name': 'Squat Bilanciere',
        'description': 'Il king degli esercizi per le gambe. Squat con bilanciere sulle spalle posteriori.',

        # Anatomia
        'primary_muscles': ['quadricipiti', 'glutei'],
        'secondary_muscles': ['ischio-crurali', 'core'],
        'stabilizers': ['polpacci', 'schiena'],

        # Equipment & Difficulty
        'equipment': ['barbell', 'rack'],
        'difficulty': 'intermedio',
        'space_required': 'medium',

        # Media
        'video_url': 'https://www.youtube.com/watch?v=ultWZbUMPL8',  # Jeff Nippard - Back Squat
        'video_thumbnail': 'https://i.ytimg.com/vi/ultWZbUMPL8/maxresdefault.jpg',
        'image_url': '',

        # Setup Instructions
        'setup_instructions': [
            'Posiziona il bilanciere su un rack all\'altezza delle spalle',
            'Posizionati sotto il bilanciere con i piedi alla larghezza delle spalle',
            'Appoggia il bilanciere sui trapezi superiori (non sul collo)',
            'Afferra il bilanciere con presa ampia, gomiti sotto la barra',
            'Solleva il bilanciere dal rack facendo 2-3 passi indietro',
            'Piedi leggermente extra-ruotati (10-15°)'
        ],

        # Execution Steps
        'execution_steps': [
            'Inspira profondamente e attiva il core (brace)',
            'Inizia la discesa piegando contemporaneamente anche e ginocchia',
            'Scendi mantenendo il petto alto e la schiena neutra',
            'Continua fino a quando le anche sono sotto le ginocchia (parallelo o sotto)',
            'Espira e spingi attraverso i talloni per risalire',
            'Estendi anche e ginocchia simultaneamente',
            'Torna alla posizione eretta mantenendo il core attivo',
            'Respira e ripeti'
        ],

        # Breathing
        'breathing_cues': 'Inspira in alto, trattieni in discesa, espira nella fase concentrica (risalita)',

        # Form Cues
        'form_cues': [
            'Petto alto durante tutto il movimento',
            'Ginocchia in linea con le punte dei piedi',
            'Talloni a terra per tutta l\'esecuzione',
            'Schiena neutra (no cifosi/lordosi eccessiva)',
            'Gomiti sotto il bilanciere',
            'Guarda un punto fisso davanti a te (non in alto/basso)'
        ],

        # Common Mistakes
        'common_mistakes': [
            'Ginocchia che collassano verso l\'interno (valgismo)',
            'Talloni che si sollevano da terra',
            'Schiena che si arrotonda (perdita posizione neutra)',
            'Scendere troppo velocemente senza controllo',
            'Spostare il peso sulle punte dei piedi',
            'Non scendere abbastanza (ROM parziale)',
            'Spingere prima con le anche che con le gambe (good morning squat)'
        ],

        # Safety Tips
        'safety_tips': [
            'Usa sempre un rack con safety bars',
            'Inizia con carichi leggeri per padroneggiare la tecnica',
            'Considera l\'uso di cintura per carichi 85%+ 1RM',
            'Non fare squat se hai dolore acuto alle ginocchia/schiena',
            'Progressione graduale del carico (+2.5-5kg/settimana)',
            'Warm-up adeguato (mobility anche/caviglie)'
        ],

        # Movement Pattern
        'movement_pattern': 'squat',
        'plane_of_movement': ['sagittal', 'frontal'],

        # Rep ranges
        'rep_range_strength': '3-6',
        'rep_range_hypertrophy': '6-12',
        'rep_range_endurance': '12-20',

        # Progressions/Regressions
        'progressions': ['Front Squat', 'Safety Bar Squat', 'Pause Squat'],
        'regressions': ['Goblet Squat', 'Box Squat', 'Bodyweight Squat'],
        'variants': ['High Bar Squat', 'Low Bar Squat', 'Tempo Squat']
    })

    # ========== HINGE PATTERN ==========

    exercises.append({
        'id': 'romanian_deadlift',
        'name': 'Romanian Deadlift',
        'italian_name': 'Stacco Rumeno',
        'description': 'Esercizio hip-hinge per ischio-crurali e glutei. Versione a gambe semi-tese.',

        # Anatomia
        'primary_muscles': ['ischio-crurali', 'glutei'],
        'secondary_muscles': ['schiena', 'core'],
        'stabilizers': ['trapezi', 'avambracci'],

        # Equipment & Difficulty
        'equipment': ['barbell'],
        'difficulty': 'intermedio',
        'space_required': 'medium',

        # Media
        'video_url': 'https://www.youtube.com/watch?v=2SHsk9AzdjA',  # Jeff Cavaliere - RDL
        'video_thumbnail': 'https://i.ytimg.com/vi/2SHsk9AzdjA/maxresdefault.jpg',

        # Setup Instructions
        'setup_instructions': [
            'Posiziona il bilanciere a terra o su rack all\'altezza delle anche',
            'Piedi larghezza anche, leggermente extra-ruotati',
            'Afferra il bilanciere con presa prona (overhand), mani larghezza spalle',
            'Solleva il bilanciere estendendo le anche (posizione eretta)',
            'Spalle indietro, petto alto, core attivo'
        ],

        # Execution Steps
        'execution_steps': [
            'Inspira e attiva il core',
            'Inizia il movimento spingendo le anche INDIETRO (hip hinge)',
            'Abbassa il bilanciere lungo le cosce mantenendo la schiena neutra',
            'Ginocchia leggermente flesse (20-30°), NON uno squat',
            'Scendi fino a sentire stretch negli ischio-crurali (metà tibia)',
            'Inverti il movimento contraendo glutei e ischio-crurali',
            'Spingi le anche in avanti per tornare in posizione eretta',
            'Espira in fase concentrica (risalita)'
        ],

        # Breathing
        'breathing_cues': 'Inspira in alto, trattieni in discesa, espira spingendo le anche avanti',

        # Form Cues
        'form_cues': [
            'Il bilanciere rimane A CONTATTO con le gambe per tutta l\'esecuzione',
            'Schiena neutra (NO arrotondamento lombare)',
            'Movimento guidato dalle ANCHE, non dalle ginocchia',
            'Sentire lo stretch negli ischio-crurali in fondo',
            'Spalle sopra la barra per tutto il movimento',
            'Finire con anche completamente estese (squeeze glutei)'
        ],

        # Common Mistakes
        'common_mistakes': [
            'Arrotondare la schiena (perdere posizione neutra)',
            'Trasformare l\'RDL in uno squat (troppo piegamento ginocchia)',
            'Bilanciere lontano dal corpo (crea leva dannosa)',
            'Non scendere abbastanza (ROM parziale)',
            'Usare momentum invece di controllo',
            'Non estendere completamente le anche in alto'
        ],

        # Safety Tips
        'safety_tips': [
            'Padroneggiare l\'hip hinge con bastone prima di caricare',
            'Iniziare con carichi leggeri (60-70% deadlift 1RM)',
            'Mantenere sempre la schiena neutra (critico)',
            'Non eseguire con schiena dolorante/infortunata',
            'Usare straps se grip limita il lavoro sugli ischio-crurali'
        ],

        # Movement Pattern
        'movement_pattern': 'hinge',
        'plane_of_movement': ['sagittal'],

        # Rep ranges
        'rep_range_strength': '4-8',
        'rep_range_hypertrophy': '8-12',
        'rep_range_endurance': '12-15',

        # Progressions/Regressions
        'progressions': ['Snatch Grip RDL', 'Single Leg RDL', 'Deficit RDL'],
        'regressions': ['Dumbbell RDL', 'Kettlebell RDL', 'Good Morning'],
        'variants': ['B-Stance RDL', 'Stiff Leg Deadlift', 'Trap Bar RDL']
    })

    # ========== HORIZONTAL PUSH ==========

    exercises.append({
        'id': 'bench_press',
        'name': 'Barbell Bench Press',
        'italian_name': 'Panca Piana Bilanciere',
        'description': 'L\'esercizio re per il petto. Distensione orizzontale su panca.',

        # Anatomia
        'primary_muscles': ['petto'],
        'secondary_muscles': ['tricipiti', 'spalle'],
        'stabilizers': ['core', 'dorsali'],

        # Equipment & Difficulty
        'equipment': ['barbell', 'bench'],
        'difficulty': 'intermedio',
        'space_required': 'medium',

        # Media
        'video_url': 'https://www.youtube.com/watch?v=vcBig73ojpE',  # Jeff Nippard - Bench Press
        'video_thumbnail': 'https://i.ytimg.com/vi/vcBig73ojpE/maxresdefault.jpg',

        # Setup Instructions
        'setup_instructions': [
            'Sdraiati sulla panca, occhi sotto il bilanciere',
            'Piedi piatti a terra, ginocchia piegate 90°',
            'Retrarre le scapole (spalle indietro e verso il basso)',
            'Creare un leggero arch lombare (non eccessivo)',
            'Afferra il bilanciere con presa leggermente più larga delle spalle',
            'Polsi dritti, avambracci perpendicolari al suolo',
            'Unrack con aiuto se carichi pesanti'
        ],

        # Execution Steps
        'execution_steps': [
            'Posiziona il bilanciere sopra il petto con braccia estese',
            'Inspira profondamente, attiva dorsali e core',
            'Abbassa il bilanciere in modo controllato verso il petto',
            'Gomiti a 45-75° rispetto al busto (NON 90° flared)',
            'Tocca il petto all\'altezza dei capezzoli',
            'Pausa brevissima (no bounce)',
            'Spingi esplosivamente verso l\'alto',
            'Espira nella fase finale della spinta',
            'Riporta il bilanciere sopra le spalle (non la faccia)'
        ],

        # Breathing
        'breathing_cues': 'Inspira profondamente in alto, trattieni in discesa, espira spingendo',

        # Form Cues
        'form_cues': [
            'Scapole retratte per tutta l\'esecuzione (CRITICO)',
            'Gomiti a 45-75° (non flare completo a 90°)',
            'Piedi attivi, spingono a terra (leg drive)',
            'Polsi dritti sopra gli avambracci',
            'Il bilanciere si muove leggermente indietro verso le spalle',
            'Toccare il petto ogni rep (full ROM)',
            'Tensione continua su petto, non rilassare in alto'
        ],

        # Common Mistakes
        'common_mistakes': [
            'Gomiti troppo flared (90°) - stress spalle',
            'Perdere retrazione scapolare (spalle avanti)',
            'Bounce del bilanciere sul petto',
            'Sollevare i glutei dalla panca',
            'Polsi piegati all\'indietro (stress)',
            'ROM parziale (non toccare il petto)',
            'Arco lombare eccessivo (iperestensione)',
            'Bilanciere che va verso la faccia in discesa'
        ],

        # Safety Tips
        'safety_tips': [
            'USA SEMPRE uno spotter per carichi massimali',
            'Imposta safety pins se alleni da solo',
            'Warm-up progressivo (bar → 50% → 70% → work sets)',
            'Non fare bench press con spalla infortunata',
            'Grip del pollice SOPRA la barra (no suicide grip)',
            'Progressione lenta del carico per evitare infortuni'
        ],

        # Movement Pattern
        'movement_pattern': 'push',
        'plane_of_movement': ['sagittal'],

        # Rep ranges
        'rep_range_strength': '1-5',
        'rep_range_hypertrophy': '6-12',
        'rep_range_endurance': '12-20',

        # Progressions/Regressions
        'progressions': ['Pause Bench Press', 'Close Grip Bench', 'Board Press'],
        'regressions': ['Dumbbell Bench Press', 'Incline Bench Press', 'Machine Press'],
        'variants': ['Wide Grip Bench', 'Larsen Press', 'Floor Press']
    })

    # ========== VERTICAL PULL ==========

    exercises.append({
        'id': 'pull_up',
        'name': 'Pull-Up',
        'italian_name': 'Trazioni alla Sbarra',
        'description': 'Esercizio fondamentale di trazione verticale a corpo libero.',

        # Anatomia
        'primary_muscles': ['dorsali', 'bicipiti'],
        'secondary_muscles': ['trapezi', 'romboidi'],
        'stabilizers': ['core', 'avambracci'],

        # Equipment & Difficulty
        'equipment': ['pull_up_bar'],
        'difficulty': 'intermedio',
        'space_required': 'small',

        # Media
        'video_url': 'https://www.youtube.com/watch?v=eGo4IYlbE5g',  # Jeff Cavaliere - Pull-ups
        'video_thumbnail': 'https://i.ytimg.com/vi/eGo4IYlbE5g/maxresdefault.jpg',

        # Setup Instructions
        'setup_instructions': [
            'Afferra la sbarra con presa prona (palmi avanti)',
            'Mani larghezza spalle o leggermente più larghe',
            'Appendi con braccia completamente estese (dead hang)',
            'Gambe dritte o leggermente piegate',
            'Attiva scapole (depressione scapolare)',
            'Core attivo per evitare oscillazioni'
        ],

        # Execution Steps
        'execution_steps': [
            'Dalla posizione dead hang, inspira',
            'Inizia retraendo le scapole (spalle indietro)',
            'Tira il corpo verso l\'alto concentrandoti sui dorsali',
            'Gomiti verso il basso e indietro',
            'Continua fino a portare il mento sopra la sbarra',
            'Pausa brevissima in alto',
            'Scendi in modo controllato fino a braccia estese',
            'Mantieni tensione in basso (no oscillazione)',
            'Espira durante la fase concentrica (salita)'
        ],

        # Breathing
        'breathing_cues': 'Inspira in basso, espira tirando verso l\'alto',

        # Form Cues
        'form_cues': [
            'Iniziare SEMPRE con retrazione scapolare',
            'Petto verso la sbarra, non mento',
            'Gomiti verso il basso, non ai lati',
            'Corpo dritto, no oscillazioni (no kipping)',
            'Full ROM: da braccia estese a mento sopra la barra',
            'Scendere in modo controllato (3-4 secondi)',
            'Pensare "gomiti verso le tasche posteriori"'
        ],

        # Common Mistakes
        'common_mistakes': [
            'Usare momentum/kipping (no CrossFit-style qui)',
            'ROM parziale (non estendere completamente)',
            'Tirare solo con le braccia (ignorare dorsali)',
            'Protrazione scapolare in basso (spalle avanti)',
            'Oscillare le gambe per aiutarsi',
            'Scendere troppo velocemente (drop)',
            'Guardare in alto (iperestensione cervicale)'
        ],

        # Safety Tips
        'safety_tips': [
            'Warm-up spalle e scapole (band pull-aparts)',
            'Se principiante, inizia con lat pulldown o bande',
            'Non fare pull-ups con dolore alla spalla',
            'Progressione: Negative → Band Assisted → Full Pull-up',
            'Non saltare giù dalla sbarra (scendi gradualmente)'
        ],

        # Movement Pattern
        'movement_pattern': 'pull',
        'plane_of_movement': ['sagittal'],

        # Rep ranges
        'rep_range_strength': '1-5',
        'rep_range_hypertrophy': '6-12',
        'rep_range_endurance': '12-20',

        # Progressions/Regressions
        'progressions': ['Weighted Pull-Up', 'L-Sit Pull-Up', 'Muscle-Up'],
        'regressions': ['Band Assisted Pull-Up', 'Negative Pull-Up', 'Lat Pulldown'],
        'variants': ['Chin-Up', 'Neutral Grip Pull-Up', 'Wide Grip Pull-Up']
    })

    return exercises


def apply_professional_details_to_exercise(exercise_dict: Dict) -> Dict:
    """Prende un esercizio standard e aggiunge dettagli professionali se disponibili"""

    pro_exercises = get_professional_exercises()

    # Cerca esercizio nel database PRO
    for pro_ex in pro_exercises:
        if pro_ex['id'] == exercise_dict.get('id'):
            # Merge dei dati (PRO sovrascrive standard)
            return {**exercise_dict, **pro_ex}

    # Se non trovato nel DB PRO, ritorna quello standard
    return exercise_dict
