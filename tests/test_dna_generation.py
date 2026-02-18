"""
Test DNA-driven workout generation.

Simulates having imported Chiara's card and generating a program from it.
Tests the full pipeline WITHOUT needing actual DB data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
from core.workout_ai_pipeline import WorkoutAIPipeline


# Simulated card data (as it would be stored after import with new parser)
MOCK_CARD = {
    'id': 1,
    'id_cliente': None,
    'file_name': 'scheda_giada.docx',
    'file_type': 'word',
    'parsed_exercises': [
        # GIORNO 1 - Circuit
        {'name': 'THRUSTER', 'canonical_id': 'hip_thrust', 'match_score': 0.67,
         'sets': 3, 'reps': '40"ON 20"OFF', 'rest_seconds': 90,
         'load_note': '5Kg', 'notes': None, 'day_section': 'GIORNO 1'},
        {'name': 'AFFONDI POSTERIORI + ALZATE FRONTALI', 'canonical_id': 'lateral_raises',
         'match_score': 0.73, 'sets': 3, 'reps': '40"ON 20"OFF', 'rest_seconds': 90,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 1'},
        {'name': 'SUMO SQUAT + ROW', 'canonical_id': 'front_squat', 'match_score': 0.67,
         'sets': 3, 'reps': '40"ON 20"OFF', 'rest_seconds': 90,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 1'},
        {'name': 'MOUNTAIN CLIMBER', 'canonical_id': None, 'match_score': 0.3,
         'sets': 4, 'reps': '20+20+20', 'rest_seconds': 60,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 1'},
        # GIORNO 2 - Strength
        {'name': 'HIP-THRUST', 'canonical_id': 'hip_thrust', 'match_score': 0.9,
         'sets': 5, 'reps': '8/10', 'rest_seconds': 90,
         'load_note': '60kg', 'notes': None, 'day_section': 'GIORNO 2'},
        {'name': 'STACCO DA TERRA', 'canonical_id': 'conventional_deadlift',
         'match_score': 0.77, 'sets': 5, 'reps': '8/10', 'rest_seconds': 90,
         'load_note': '50kg', 'notes': None, 'day_section': 'GIORNO 2'},
        {'name': 'SHOULDER PRESS', 'canonical_id': 'dumbbell_shoulder_press',
         'match_score': 0.76, 'sets': 4, 'reps': '12', 'rest_seconds': 60,
         'load_note': '20kg', 'notes': None, 'day_section': 'GIORNO 2'},
        {'name': 'PUSH DOWN', 'canonical_id': 'cable_pushdown', 'match_score': 0.73,
         'sets': 4, 'reps': '12', 'rest_seconds': 60,
         'load_note': '15kg', 'notes': None, 'day_section': 'GIORNO 2'},
        {'name': 'LEG CURL', 'canonical_id': 'leg_curl', 'match_score': 1.0,
         'sets': 4, 'reps': '12 x gamba', 'rest_seconds': 60,
         'load_note': '20kg', 'notes': None, 'day_section': 'GIORNO 2'},
        {'name': 'V-UP', 'canonical_id': None, 'match_score': 0.3,
         'sets': None, 'reps': '20', 'rest_seconds': None,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 2'},
        # GIORNO 3 - PHA
        {'name': 'LAT MACHINE', 'canonical_id': 'lat_pulldown', 'match_score': 1.0,
         'sets': 4, 'reps': '12', 'rest_seconds': 60,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 3'},
        {'name': 'LEG PRESS', 'canonical_id': 'leg_press', 'match_score': 1.0,
         'sets': 4, 'reps': '15', 'rest_seconds': 60,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 3'},
        {'name': 'FROG PUMP', 'canonical_id': None, 'match_score': 0.3,
         'sets': 3, 'reps': '20+20+20', 'rest_seconds': 60,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 3'},
        {'name': 'HIP-THRUST MONOPODALICO', 'canonical_id': 'hip_thrust',
         'match_score': 0.55, 'sets': 4, 'reps': '12 x gamba', 'rest_seconds': 90,
         'load_note': None, 'notes': None, 'day_section': 'GIORNO 3'},
    ],
    'parsed_metadata': {
        'detected_goal': 'functional',
        'detected_split': 'circuit',
        'detected_sessions_per_week': 3,
        'days_found': ['GIORNO 1', 'GIORNO 2', 'GIORNO 3'],
        'client_name': 'GIADA',
    },
    'extraction_status': 'extracted',
    'pattern_extracted': True,
}

# Mock DNA summary
MOCK_DNA_SUMMARY = MagicMock()
MOCK_DNA_SUMMARY.total_cards_imported = 1
MOCK_DNA_SUMMARY.dna_level = "learning"
MOCK_DNA_SUMMARY.preferred_exercises = [
    "HIP-THRUST", "STACCO DA TERRA", "SHOULDER PRESS", "LAT MACHINE",
    "LEG PRESS", "THRUSTER", "AFFONDI POSTERIORI"
]
MOCK_DNA_SUMMARY.preferred_set_scheme = "5x8/10"
MOCK_DNA_SUMMARY.accessory_philosophy = "balanced"
MOCK_DNA_SUMMARY.ordering_style = "compound_first"


def test_dna_driven_generation():
    """Test full DNA-driven generation pipeline."""
    # Patch to avoid LLM initialization and DB calls
    with patch.object(WorkoutAIPipeline, '_init_llm'):
        pipeline = WorkoutAIPipeline()
        pipeline.llm = None  # no LLM needed

        # Mock card_import_repo.get_all_cards
        pipeline.card_import_repo = MagicMock()
        pipeline.card_import_repo.get_all_cards.return_value = [MOCK_CARD]

        # Mock dna_repo
        pipeline.dna_repo = MagicMock()
        pipeline.dna_repo.get_active_patterns.return_value = MOCK_DNA_SUMMARY
        pipeline.dna_repo.get_dna_status.return_value = {
            'total_cards': 1, 'total_patterns': 5, 'dna_level': 'learning'
        }

        # Mock assessment (not used)
        pipeline.assessment_repo = MagicMock()
        pipeline.assessment_repo.get_initial.return_value = None

        # Generate
        client_profile = {
            'nome': 'Test',
            'cognome': 'Cliente',
            'goal': 'functional',
            'level': 'intermediate',
            'disponibilita_giorni': 3,
            'equipment': ['barbell', 'dumbbell', 'machine', 'cable'],
            'limitazioni': 'Nessuna',
        }

        result = pipeline.generate_with_ai(
            client_id=1,
            client_profile=client_profile,
            weeks=4,
            periodization_model='linear',
            sessions_per_week=3,
            use_assessment=False,
            use_trainer_dna=True,
        )

    print("=" * 70)
    print("RISULTATO GENERAZIONE DNA-DRIVEN")
    print("=" * 70)

    errors = []

    # Check basic structure
    if 'error' in result:
        errors.append(f"FAIL: Errore nella generazione: {result['error']}")
        print(f"ERRORE: {result}")
        return False

    ai_meta = result.get('ai_metadata', {})
    print(f"\nAI Metadata:")
    print(f"  DNA used: {ai_meta.get('dna_used')}")
    print(f"  DNA driven: {ai_meta.get('dna_driven')}")
    print(f"  DNA level: {ai_meta.get('dna_level')}")
    print(f"  DNA exercises: {ai_meta.get('dna_exercises_used')}")
    print(f"  Custom exercises: {ai_meta.get('custom_exercises')}")

    if not ai_meta.get('dna_driven'):
        errors.append("FAIL: dna_driven should be True")

    # Check weekly schedule structure
    weekly = result.get('weekly_schedule', {})
    if not weekly:
        errors.append("FAIL: No weekly_schedule")
    else:
        print(f"\nSettimane: {len(weekly)}")
        if len(weekly) != 4:
            errors.append(f"FAIL: {len(weekly)} settimane (attese 4)")
        else:
            print(f"OK: 4 settimane generate")

    # Check week 1 sessions
    week1 = weekly.get('week_1', {})
    sessions = week1.get('sessions', {})
    print(f"\nGiorni settimana 1: {len(sessions)}")

    if len(sessions) != 3:
        errors.append(f"FAIL: {len(sessions)} sessioni (attese 3)")
    else:
        print(f"OK: 3 sessioni")

    # Print exercises for each day
    total_exercises = 0
    for day_key in sorted(sessions.keys()):
        session = sessions[day_key]
        exercises = session.get('main_workout', [])
        total_exercises += len(exercises)
        print(f"\n--- {day_key} ({len(exercises)} esercizi) ---")
        for idx, ex in enumerate(exercises, 1):
            name = ex.get('italian_name', ex.get('name', '?'))
            sets = ex.get('sets', '-')
            reps = ex.get('reps', '-')
            rest = ex.get('rest_seconds', '-')
            load = ex.get('load_note', '')
            custom = " [CUSTOM]" if ex.get('is_custom') else ""
            muscles = ex.get('primary_muscles', [])
            muscle_str = muscles[0][:3].upper() if muscles else 'CUS'
            print(f"  {idx}. {name:40s} [{muscle_str:4s}] Sets:{sets:4} Reps:{str(reps):15s} Rest:{rest}s {load}{custom}")

    print(f"\nTotale esercizi: {total_exercises}")

    if total_exercises < 8:
        errors.append(f"FAIL: Solo {total_exercises} esercizi (attesi >= 8)")
    else:
        print(f"OK: {total_exercises} esercizi totali")

    # Check Chiara's key exercises are present
    all_names = []
    for day_key, session in sessions.items():
        for ex in session.get('main_workout', []):
            all_names.append(ex.get('italian_name', ex.get('name', '')).lower())

    must_have_any = [
        ("hip thrust", "hip-thrust", "hip_thrust"),
        ("stacco", "deadlift"),
        ("lat pulldown", "lat machine"),
        ("leg press", "pressa gambe"),
    ]
    for name_variants in must_have_any:
        found = any(
            any(v in n for v in name_variants)
            for n in all_names
        )
        if found:
            print(f"OK: Trovato esercizio DNA: {name_variants[0]}")
        else:
            errors.append(f"FAIL: Esercizio DNA non trovato: {name_variants[0]}")

    # Check for custom exercises (FROG PUMP, MOUNTAIN CLIMBER should be custom)
    custom_count = sum(
        1 for day_key, session in sessions.items()
        for ex in session.get('main_workout', [])
        if ex.get('is_custom')
    )
    print(f"\nEsercizi custom (non nel DB): {custom_count}")

    # Check periodization (week 4 should be deload)
    week4 = weekly.get('week_4', {})
    if week4.get('is_deload'):
        print(f"OK: Settimana 4 e' deload")
    else:
        errors.append(f"FAIL: Settimana 4 non e' deload")

    # Check DNA sets/reps are preserved (not overwritten by defaults)
    # Specifically check day_2 where HIP-THRUST has 5x8/10 in Chiara's card
    day2_session = sessions.get('day_2', {})
    for ex in day2_session.get('main_workout', []):
        if 'hip' in ex.get('name', '').lower() and 'thrust' in ex.get('name', '').lower():
            if ex.get('sets') == 5:
                print(f"OK: HIP THRUST sets=5 (da DNA)")
            else:
                errors.append(f"FAIL: HIP THRUST sets={ex.get('sets')} (attesi 5 da DNA)")
            if ex.get('reps') and '8' in str(ex.get('reps', '')):
                print(f"OK: HIP THRUST reps={ex.get('reps')} (da DNA)")
            break

    # Summary
    print("\n" + "=" * 70)
    if errors:
        print(f"RISULTATO: {len(errors)} ERRORI")
        for err in errors:
            print(f"  {err}")
    else:
        print("RISULTATO: TUTTI I TEST PASSATI!")
    print("=" * 70)

    return len(errors) == 0


if __name__ == "__main__":
    success = test_dna_driven_generation()
    sys.exit(0 if success else 1)
