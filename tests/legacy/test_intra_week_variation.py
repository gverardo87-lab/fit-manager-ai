"""
Test per verificare VARIAZIONE INTRA-SETTIMANA in Upper_Lower split

OBIETTIVO: Verificare che Day 1 ≠ Day 3 e Day 2 ≠ Day 4

PROBLEMA RISOLTO:
- Prima: Day 1 = Day 3 (identici)
- Ora: Day 1 (Press Focus) ≠ Day 3 (Pull Focus)

PROBLEMA RISOLTO:
- Prima: Day 2 = Day 4 (identici)
- Ora: Day 2 (Squat Focus) ≠ Day 4 (Hinge Focus)
"""

from core.workout_generator import WorkoutGenerator
from core.periodization_models import Goal
# DifficultyLevel removed from core.exercise_database (module deleted)

def test_upper_lower_intra_week_variation():
    print("=" * 80)
    print("TEST: VARIAZIONE INTRA-SETTIMANA - Upper_Lower Split")
    print("=" * 80)
    
    generator = WorkoutGeneratorV2()
    
    # Client profile per Upper_Lower (4 giorni/settimana)
    client_profile = {
        'nome': 'Test',
        'cognome': 'Cliente',
        'goal': 'hypertrophy',
        'level': 'intermediate',
        'disponibilita_giorni': 4,
        'equipment': ['barbell', 'dumbbell', 'cable', 'bodyweight', 'machine'],
        'limitazioni': []
    }
    
    # Genera programma Upper_Lower 8 settimane
    program = generator.generate_professional_workout(
        client_profile=client_profile,
        weeks=8,
        periodization_model='linear',
        sessions_per_week=4  # Upper_Lower = 4 giorni
    )
    
    print("\n📅 Program keys:", list(program.keys()))
    
    # Accedi a weekly_schedule
    weekly_schedule = program.get('weekly_schedule', {})
    
    if not weekly_schedule:
        print("❌ Nessun weekly_schedule trovato")
        return
    
    week_keys = list(weekly_schedule.keys())
    print(f"📅 Week keys: {week_keys[:3]}")  # Prime 3 settimane
    
    print("\n📅 SETTIMANA 1 - Analisi giorni:")
    print("-" * 80)
    
    # Prendi la prima settimana
    first_week_key = week_keys[0] if week_keys else None
    if not first_week_key:
        print("❌ Nessuna settimana disponibile")
        return
    
    week1 = weekly_schedule[first_week_key]
    print(f"Week 1 keys: {list(week1.keys())}")
    
    sessions = week1.get('sessions', {})
    if not sessions or len(sessions) < 4:
        print(f"❌ Sessioni insufficienti: {len(sessions)}, expected 4")
        print(f"   Sessions type: {type(sessions)}")
        print(f"   Sessions keys: {list(sessions.keys()) if isinstance(sessions, dict) else 'N/A'}")
        return
    
    print(f"Sessions count: {len(sessions)}")
    print(f"Sessions keys: {list(sessions.keys())[:4] if isinstance(sessions, dict) else 'N/A'}")
    
    # Accedi alle sessioni (possono essere dict o list)
    if isinstance(sessions, dict):
        session_keys = list(sessions.keys())
        day1 = sessions[session_keys[0]]
        day2 = sessions[session_keys[1]]
        day3 = sessions[session_keys[2]]
        day4 = sessions[session_keys[3]]
    else:
        day1 = sessions[0]
        day2 = sessions[1]
        day3 = sessions[2]
        day4 = sessions[3]
    
    # ========================
    # DAY 1 vs DAY 3 (UPPER)
    # ========================
    print("\n🔴 DAY 1 UPPER (PRESS FOCUS - HEAVY):")
    day1_exercises = [ex['name'] for ex in day1.get('main_workout', [])]
    print(f"   Exercises: {', '.join(day1_exercises[:3])}")
    print(f"   Total: {len(day1_exercises)} exercises")
    
    print("\n🔵 DAY 3 UPPER (PULL FOCUS - VOLUME):")
    day3_exercises = [ex['name'] for ex in day3.get('main_workout', [])]
    print(f"   Exercises: {', '.join(day3_exercises[:3])}")
    print(f"   Total: {len(day3_exercises)} exercises")
    
    # Verifica differenza
    day1_set = set(day1_exercises)
    day3_set = set(day3_exercises)
    overlap = day1_set.intersection(day3_set)
    overlap_percentage = (len(overlap) / max(len(day1_set), len(day3_set))) * 100 if day1_set or day3_set else 0
    
    print(f"\n   📊 Overlap: {len(overlap)}/{max(len(day1_set), len(day3_set))} esercizi ({overlap_percentage:.0f}%)")
    
    if overlap_percentage < 50:
        print("   ✅ PASS: Day 1 e Day 3 sono SIGNIFICATIVAMENTE DIVERSI")
    else:
        print("   ❌ FAIL: Day 1 e Day 3 sono troppo simili")
    
    # ========================
    # DAY 2 vs DAY 4 (LOWER)
    # ========================
    print("\n🟢 DAY 2 LOWER (SQUAT FOCUS - HEAVY):")
    day2_exercises = [ex['name'] for ex in day2.get('main_workout', [])]
    print(f"   Exercises: {', '.join(day2_exercises[:3])}")
    print(f"   Total: {len(day2_exercises)} exercises")
    
    print("\n🟡 DAY 4 LOWER (HINGE FOCUS - VOLUME):")
    day4_exercises = [ex['name'] for ex in day4.get('main_workout', [])]
    print(f"   Exercises: {', '.join(day4_exercises[:3])}")
    print(f"   Total: {len(day4_exercises)} exercises")
    
    # Verifica differenza
    day2_set = set(day2_exercises)
    day4_set = set(day4_exercises)
    overlap_lower = day2_set.intersection(day4_set)
    overlap_lower_percentage = (len(overlap_lower) / max(len(day2_set), len(day4_set))) * 100 if day2_set or day4_set else 0
    
    print(f"\n   📊 Overlap: {len(overlap_lower)}/{max(len(day2_set), len(day4_set))} esercizi ({overlap_lower_percentage:.0f}%)")
    
    if overlap_lower_percentage < 50:
        print("   ✅ PASS: Day 2 e Day 4 sono SIGNIFICATIVAMENTE DIVERSI")
    else:
        print("   ❌ FAIL: Day 2 e Day 4 sono troppo simili")
    
    # ========================
    # DETAILED ANALYSIS
    # ========================
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS - Primi 4 esercizi per giorno:")
    print("=" * 80)
    
    print("\n🔴 DAY 1 UPPER (PRESS FOCUS):")
    for i, ex in enumerate(day1.get('main_workout', [])[:4], 1):
        print(f"   {i}. {ex['name']} - {ex['sets']} sets x {ex['reps']} reps")
    
    print("\n🔵 DAY 3 UPPER (PULL FOCUS):")
    for i, ex in enumerate(day3.get('main_workout', [])[:4], 1):
        print(f"   {i}. {ex['name']} - {ex['sets']} sets x {ex['reps']} reps")
    
    print("\n🟢 DAY 2 LOWER (SQUAT FOCUS):")
    for i, ex in enumerate(day2.get('main_workout', [])[:4], 1):
        print(f"   {i}. {ex['name']} - {ex['sets']} sets x {ex['reps']} reps")
    
    print("\n🟡 DAY 4 LOWER (HINGE FOCUS):")
    for i, ex in enumerate(day4.get('main_workout', [])[:4], 1):
        print(f"   {i}. {ex['name']} - {ex['sets']} sets x {ex['reps']} reps")
    
    # ========================
    # FINAL VERDICT
    # ========================
    print("\n" + "=" * 80)
    print("FINAL VERDICT:")
    print("=" * 80)
    
    if overlap_percentage < 50 and overlap_lower_percentage < 50:
        print("✅ TEST PASSED - VARIAZIONE INTRA-SETTIMANA IMPLEMENTATA CORRETTAMENTE!")
        print("   - Day 1 (Press) ≠ Day 3 (Pull)")
        print("   - Day 2 (Squat) ≠ Day 4 (Hinge)")
    else:
        print("❌ TEST FAILED - Giorni ancora troppo simili")
        print(f"   - Upper overlap: {overlap_percentage:.0f}%")
        print(f"   - Lower overlap: {overlap_lower_percentage:.0f}%")

if __name__ == "__main__":
    test_upper_lower_intra_week_variation()
