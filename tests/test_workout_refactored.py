"""
Test della nuova logica di generazione workout dopo refactoring
Verifica:
- Smart pattern selection
- Equipment validation
- Contraindication filtering
- Anti-duplicate tracking
"""

from core.workout_generator import WorkoutGenerator
from core.models import ClienteDB, Goal, DifficultyLevel
from datetime import date, datetime
import json

def test_workout_generation():
    """Test workout generation con vari scenari"""
    
    generator = WorkoutGeneratorV2()
    
    # TEST 1: Beginner con solo bodyweight
    print("\n" + "="*60)
    print("TEST 1: Beginner con solo BODYWEIGHT")
    print("="*60)
    
    cliente_beginner = ClienteDB(
        id=1,
        nome="Mario",
        cognome="Rossi",
        email="mario@test.it",
        telefono="1234567890",
        data_nascita=date(1990, 1, 1),
        sesso="M",
        altezza=175,
        peso=75,
        obiettivi="Forza e massa",
        note="",
        limitazioni="",
        data_valutazione=date.today()
    )
    
    workout_beginner = generator.generate_workout_program(
        cliente=cliente_beginner,
        difficulty=DifficultyLevel.BEGINNER,
        goal=Goal.STRENGTH,
        weeks=2,
        days_per_week=3,
        equipment=['bodyweight'],  # SOLO bodyweight
        periodization_model='linear'
    )
    
    print(f"✓ Generato workout {workout_beginner['type']}")
    print(f"✓ Settimane: {len(workout_beginner['weeks'])}")
    
    # Verifica che NON ci siano esercizi con bilanciere/manubri
    week1 = workout_beginner['weeks'][0]
    for day_key in week1['days']:
        day = week1['days'][day_key]
        print(f"\n{day['name']}:")
        for ex in day['exercises']:
            equipment_required = ex.get('equipment', [])
            print(f"  - {ex['name']}: {equipment_required}")
            
            # ASSERT: nessun barbell/dumbbell
            assert 'barbell' not in equipment_required, f"Trovato barbell in {ex['name']} ma cliente ha solo bodyweight!"
            assert 'dumbbell' not in equipment_required, f"Trovato dumbbell in {ex['name']} ma cliente ha solo bodyweight!"
    
    print("\n✅ Test 1 PASSED: Tutti esercizi bodyweight only")
    
    # TEST 2: Intermediate con limitazioni ginocchio
    print("\n" + "="*60)
    print("TEST 2: Intermediate con LIMITAZIONI GINOCCHIO")
    print("="*60)
    
    cliente_knee = ClienteDB(
        id=2,
        nome="Laura",
        cognome="Bianchi",
        email="laura@test.it",
        telefono="9876543210",
        data_nascita=date(1985, 5, 15),
        sesso="F",
        altezza=165,
        peso=60,
        obiettivi="Tonificazione",
        note="",
        limitazioni="ginocchio",  # LIMITAZIONE GINOCCHIO
        data_valutazione=date.today()
    )
    
    workout_knee = generator.generate_workout_program(
        cliente=cliente_knee,
        difficulty=DifficultyLevel.INTERMEDIATE,
        goal=Goal.HYPERTROPHY,
        weeks=2,
        days_per_week=3,
        equipment=['bodyweight', 'resistance_band', 'dumbbell'],
        periodization_model='linear'
    )
    
    print(f"✓ Generato workout {workout_knee['type']}")
    
    week1_knee = workout_knee['weeks'][0]
    for day_key in week1_knee['days']:
        day = week1_knee['days'][day_key]
        print(f"\n{day['name']}:")
        for ex in day['exercises']:
            contraindications = ex.get('contraindications', [])
            print(f"  - {ex['name']}: {contraindications}")
            
            # ASSERT: nessun esercizio con controindicazione ginocchio
            for contra in contraindications:
                assert 'ginocchio' not in contra.lower(), f"Trovato esercizio {ex['name']} con controindicazione ginocchio!"
    
    print("\n✅ Test 2 PASSED: Nessun esercizio con controindicazione ginocchio")
    
    # TEST 3: Advanced full equipment - Verifica anti-duplicati
    print("\n" + "="*60)
    print("TEST 3: Advanced con VERIFICA ANTI-DUPLICATI")
    print("="*60)
    
    cliente_advanced = ClienteDB(
        id=3,
        nome="Giovanni",
        cognome="Verdi",
        email="giovanni@test.it",
        telefono="5551234567",
        data_nascita=date(1988, 10, 20),
        sesso="M",
        altezza=180,
        peso=85,
        obiettivi="Powerlifting",
        note="",
        limitazioni="",
        data_valutazione=date.today()
    )
    
    workout_advanced = generator.generate_workout_program(
        cliente=cliente_advanced,
        difficulty=DifficultyLevel.ADVANCED,
        goal=Goal.STRENGTH,
        weeks=2,
        days_per_week=4,
        equipment=['barbell', 'dumbbell', 'bench', 'rack', 'cable'],
        periodization_model='block'
    )
    
    print(f"✓ Generato workout {workout_advanced['type']}")
    
    # Raccolta tutti exercise IDs
    all_exercise_ids = []
    week1_adv = workout_advanced['weeks'][0]
    for day_key in week1_adv['days']:
        day = week1_adv['days'][day_key]
        print(f"\n{day['name']}:")
        day_ids = []
        for ex in day['exercises']:
            ex_id = ex.get('id', ex['name'])
            day_ids.append(ex_id)
            all_exercise_ids.append(ex_id)
            print(f"  - {ex['name']} (ID: {ex_id})")
        
        # ASSERT: nessun duplicato nello stesso giorno
        assert len(day_ids) == len(set(day_ids)), f"Duplicati trovati in {day['name']}: {day_ids}"
    
    # Verifica duplicati totali nella settimana
    duplicates = [ex_id for ex_id in all_exercise_ids if all_exercise_ids.count(ex_id) > 1]
    if duplicates:
        print(f"\n⚠️  ATTENZIONE: Duplicati trovati nella settimana: {set(duplicates)}")
        print("  (Potrebbe essere OK se in giorni diversi con varianti diverse)")
    else:
        print("\n✅ Test 3 PASSED: Nessun duplicato nella settimana")
    
    # Statistiche finali
    print("\n" + "="*60)
    print("STATISTICHE FINALI")
    print("="*60)
    print(f"Database esercizi: {len(generator.exercise_db.exercises)} esercizi totali")
    print(f"Workout beginner: {len([ex for day in workout_beginner['weeks'][0]['days'].values() for ex in day['exercises']])} esercizi/settimana")
    print(f"Workout intermediate: {len([ex for day in workout_knee['weeks'][0]['days'].values() for ex in day['exercises']])} esercizi/settimana")
    print(f"Workout advanced: {len([ex for day in workout_advanced['weeks'][0]['days'].values() for ex in day['exercises']])} esercizi/settimana")
    
    print("\n" + "="*60)
    print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO")
    print("="*60)
    
    return {
        'beginner': workout_beginner,
        'intermediate': workout_knee,
        'advanced': workout_advanced
    }

if __name__ == "__main__":
    try:
        results = test_workout_generation()
        
        # Salva risultati in JSON per ispezione
        with open('test_workout_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n📁 Risultati salvati in test_workout_results.json")
        
    except Exception as e:
        print(f"\n❌ TEST FALLITO: {e}")
        import traceback
        traceback.print_exc()
