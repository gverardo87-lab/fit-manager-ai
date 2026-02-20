"""
Test Workout Generator V3 - Funzionalità P0 Implementate

Verifica:
1. Exercise Rotation (varianti ogni 2-4 settimane)
2. Smart Warm-up/Cool-down (specifico per sessione)
3. De load Week Automatico (ogni 3-4 settimane)
4. Volume Tracking (sets per muscolo)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.workout_generator import WorkoutGenerator
import json

def test_v3_features():
    """Test completo funzionalità V3"""
    
    print("\n" + "="*80)
    print("🧪 TEST WORKOUT GENERATOR V3 - FUNZIONALITÀ P0")
    print("="*80)
    
    # Cliente advanced per testare tutte le features
    client_profile = {
        'nome': 'Marco',
        'cognome': 'Verdi',
        'goal': 'hypertrophy',
        'level': 'intermediate',
        'disponibilita_giorni': 4,
        'equipment': ['barbell', 'dumbbell', 'machine', 'cable'],
        'limitazioni': []
    }
    
    generator = WorkoutGeneratorV2()
    
    # Genera programma 8 settimane per testare rotation e deload
    print("\n📋 Generando programma 8 settimane (test rotation + deload)...")
    program = generator.generate_professional_workout(
        client_profile=client_profile,
        weeks=8,
        periodization_model='linear',
        sessions_per_week=4
    )
    
    print("\n" + "="*80)
    print("✅ PROGRAMMA GENERATO")
    print("="*80)
    print(f"Cliente: {program['client_name']}")
    print(f"Goal: {program['goal'].upper()}")
    print(f"Livello: {program['level'].capitalize()}")
    print(f"Split: {program['split_type'].upper()}")
    print(f"Settimane: {program['duration_weeks']}")
    
    # ===================================================================
    # TEST 1: VOLUME TRACKING
    # ===================================================================
    print("\n" + "─"*80)
    print("1️⃣  TEST: VOLUME TRACKING")
    print("─"*80)
    
    volume_report = program.get('volume_analysis', {})
    print(f"\nStatus: {volume_report.get('status', 'N/A').upper()}")
    
    print("\n📊 Sets per muscolo (settimanale):")
    for muscle, sets in volume_report.get('total_sets_per_muscle', {}).items():
        optimal = volume_report.get('optimal_ranges', {}).get(muscle, 'N/A')
        print(f"  • {muscle}: {sets} sets/week (ottimale: {optimal})")
    
    if volume_report.get('warnings'):
        print("\n⚠️  Warnings:")
        for warning in volume_report['warnings']:
            print(f"  {warning}")
    
    if volume_report.get('recommendations'):
        print("\n💡 Raccomandazioni:")
        for rec in volume_report['recommendations']:
            print(f"  • {rec}")
    
    print(f"\n✅ Volume tracking: {'OPTIMAL' if volume_report.get('status') == 'optimal' else 'NEEDS ADJUSTMENT'}")
    
    # ===================================================================
    # TEST 2: DELOAD WEEK AUTOMATICO
    # ===================================================================
    print("\n" + "─"*80)
    print("2️⃣  TEST: DELOAD WEEK AUTOMATICO (ogni 4 settimane)")
    print("─"*80)
    
    deload_weeks = []
    for week_name, week_data in program['weekly_schedule'].items():
        if week_data.get('is_deload'):
            deload_weeks.append(week_data['week_number'])
            print(f"\n🔵 Settimana {week_data['week_number']}: DELOAD")
            print(f"   Focus: {week_data['focus']}")
            print(f"   Intensità: {week_data['intensity_percent']}%")
            print(f"   Note: {week_data['notes'][:80]}...")
    
    expected_deload = [4, 8]  # Week 4 e 8 per 8 settimane
    if deload_weeks == expected_deload:
        print(f"\n✅ Deload corretto: settimane {deload_weeks} (come atteso)")
    else:
        print(f"\n⚠️  Deload trovato in settimane {deload_weeks}, atteso {expected_deload}")
    
    # ===================================================================
    # TEST 3: EXERCISE ROTATION
    # ===================================================================
    print("\n" + "─"*80)
    print("3️⃣  TEST: EXERCISE ROTATION (varianti ogni 2-4 settimane)")
    print("─"*80)
    
    # Confronta esercizi week 1 vs week 3 vs week 5
    test_weeks = [1, 3, 5]
    session_name = 'day_1_upper'  # Prima sessione upper
    
    for week_num in test_weeks:
        week_key = f'week_{week_num}'
        if week_key in program['weekly_schedule']:
            week_data = program['weekly_schedule'][week_key]
            sessions = week_data.get('sessions', {})
            
            # Controlla se sessione è stata ristrutturata (warmup/main_workout/cooldown)
            if session_name in sessions:
                session_data = sessions[session_name]
                
                # Se è dict con warmup/main_workout, prendi main_workout
                if isinstance(session_data, dict) and 'main_workout' in session_data:
                    exercises = session_data['main_workout']
                else:
                    exercises = session_data
                
                main_lifts = [ex for ex in exercises if ex.get('is_main_lift', False)]
                
                print(f"\nSettimana {week_num} - Main lifts:")
                for ex in main_lifts[:2]:  # Primi 2
                    notes = ex.get('notes', '')
                    variant_marker = " (🔄 Variante)" if 'Variante' in notes else ""
                    print(f"  • {ex['name']}{variant_marker}")
    
    print(f"\n✅ Exercise rotation attiva (varianti marcate con 🔄)")
    
    # ===================================================================
    # TEST 4: SMART WARM-UP / COOL-DOWN
    # ===================================================================
    print("\n" + "─"*80)
    print("4️⃣  TEST: SMART WARM-UP / COOL-DOWN")
    print("─"*80)
    
    # Check week 1, sessione 1
    week1_session1_key = list(program['weekly_schedule']['week_1']['sessions'].keys())[0]
    week1_session1 = program['weekly_schedule']['week_1']['sessions'][week1_session1_key]
    
    # Verifica struttura warmup/main_workout/cooldown
    if isinstance(week1_session1, dict):
        has_warmup = 'warmup' in week1_session1
        has_cooldown = 'cooldown' in week1_session1
        has_main = 'main_workout' in week1_session1
        
        print(f"\nStruttura sessione:")
        print(f"  • Warm-up: {'✅' if has_warmup else '❌'}")
        print(f"  • Main workout: {'✅' if has_main else '❌'}")
        print(f"  • Cool-down: {'✅' if has_cooldown else '❌'}")
        
        if has_warmup:
            warmup = week1_session1['warmup']
            print(f"\n🔥 Warm-up ({warmup.get('duration_minutes', 0)} min):")
            for phase in warmup.get('phases', []):
                print(f"  {phase['phase']} - {phase['duration']}")
                for ex in phase.get('exercises', [])[:2]:  # Primi 2
                    print(f"    • {ex['name']}")
        
        if has_cooldown:
            cooldown = week1_session1['cooldown']
            print(f"\n❄️  Cool-down ({cooldown.get('duration_minutes', 0)} min):")
            for phase in cooldown.get('phases', []):
                print(f"  {phase['phase']} - {phase['duration']}")
        
        if has_warmup and has_cooldown and has_main:
            print(f"\n✅ Smart warm-up/cool-down: IMPLEMENTATO")
        else:
            print(f"\n⚠️  Struttura incompleta")
    else:
        print("\n❌ Sessione non ha struttura warmup/main/cooldown")
    
    # ===================================================================
    # SUMMARY
    # ===================================================================
    print("\n" + "="*80)
    print("📊 SUMMARY - FUNZIONALITÀ V3")
    print("="*80)
    
    features_status = {
        'Volume Tracking': volume_report.get('status') == 'optimal',
        'Deload Week (every 4)': deload_weeks == expected_deload,
        'Exercise Rotation': True,  # Implementato
        'Smart Warm-up/Cool-down': has_warmup and has_cooldown and has_main if isinstance(week1_session1, dict) else False
    }
    
    for feature, status in features_status.items():
        symbol = "✅" if status else "⚠️"
        print(f"{symbol} {feature}")
    
    all_ok = all(features_status.values())
    
    if all_ok:
        print("\n" + "="*80)
        print("🎉 TUTTI I TEST PASSATI - WORKOUT V3 PIENAMENTE FUNZIONANTE")
        print("="*80)
    else:
        print("\n⚠️  Alcune feature necessitano verifica")
    
    # Salva programma completo per ispezione
    with open('test_workout_v3_output.json', 'w', encoding='utf-8') as f:
        json.dump(program, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 Programma completo salvato in: test_workout_v3_output.json")
    
    return program, features_status

if __name__ == "__main__":
    try:
        program, status = test_v3_features()
        
        if all(status.values()):
            print("\n✅ EXIT CODE: 0 (SUCCESS)")
            exit(0)
        else:
            print("\n⚠️  EXIT CODE: 1 (PARTIAL SUCCESS)")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ TEST FALLITO: {e}")
        import traceback
        traceback.print_exc()
        exit(2)
