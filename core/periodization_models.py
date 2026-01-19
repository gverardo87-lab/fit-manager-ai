# core/periodization_models.py
"""
5 Modelli di Periodizzazione Scientifica

Implementazione dei modelli di periodizzazione più usati nel strength training:
1. Linear Periodization (LP)
2. Block Periodization (BP)
3. Daily Undulating Periodization (DUP)
4. Conjugate Method (Westside Barbell)
5. Auto-Regulation (RPE-based)

Ogni modello include:
- Schema progressione intensità/volume
- Deload weeks automatici
- Parametri adattabili per goal (strength, hypertrophy, power)
- Output formato workout-ready

References:
- Bompa & Haff (2009) - Periodization Training for Sports
- Zatsiorsky & Kraemer (2006) - Science and Practice of Strength Training
- Simmons (2007) - Westside Barbell Book of Methods
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import date, timedelta


class Goal(Enum):
    """Goal principale allenamento"""
    STRENGTH = "strength"              # Forza massimale (1-5 rep)
    HYPERTROPHY = "hypertrophy"       # Ipertrofia (6-12 rep)
    POWER = "power"                    # Potenza esplosiva (3-6 rep veloce)
    ENDURANCE = "endurance"            # Resistenza (12-20+ rep)
    FAT_LOSS = "fat_loss"             # Perdita grasso (circuit/HIIT)


@dataclass
class WeekParameters:
    """Parametri per una settimana di allenamento"""
    week_number: int
    intensity_percent: float      # % 1RM (es. 70% = 0.70)
    volume_sets: int              # Serie totali per sessione
    reps_per_set: tuple          # (min_rep, max_rep)
    rest_seconds: int            # Recupero tra serie
    is_deload: bool = False      # Settimana scarico
    focus: str = ""              # Focus settimana (es. "hypertrophy", "strength peak")
    notes: str = ""


@dataclass
class PeriodizationPlan:
    """Piano di periodizzazione completo"""
    model_name: str
    goal: Goal
    total_weeks: int
    weeks: List[WeekParameters]
    description: str
    methodology: str
    expected_outcomes: str


class PeriodizationModels:
    """
    Factory per generare piani di periodizzazione
    """

    @staticmethod
    def linear_periodization(
        weeks: int = 12,
        goal: Goal = Goal.STRENGTH,
        starting_intensity: float = 0.60,
        peak_intensity: float = 0.90
    ) -> PeriodizationPlan:
        """
        Linear Periodization (LP) - Classico modello progressivo

        Caratteristiche:
        - Intensità aumenta gradualmente
        - Volume diminuisce progressivamente
        - Fasi: Hypertrophy → Strength → Peak
        - Deload ogni 4 settimane

        Args:
            weeks: Durata totale (8-16 settimane tipico)
            goal: Obiettivo finale (solitamente STRENGTH o HYPERTROPHY)
            starting_intensity: % 1RM iniziale (default: 60%)
            peak_intensity: % 1RM finale (default: 90%)

        Returns:
            PeriodizationPlan con progressione lineare
        """
        week_params = []

        # Calcola incremento intensità per settimana
        intensity_step = (peak_intensity - starting_intensity) / weeks

        # Fase 1: Hypertrophy (settimane 1-4)
        # Fase 2: Strength (settimane 5-8)
        # Fase 3: Peak/Taper (settimane 9-12)
        # Deload ogni 4 settimane

        for week in range(1, weeks + 1):
            # Deload ogni 4 settimane
            is_deload = week % 4 == 0

            if is_deload:
                # Settimana scarico: -30% intensità, -40% volume
                intensity = (starting_intensity + intensity_step * (week - 1)) * 0.70
                volume = 2  # Serie ridotte
                reps = (6, 8)
                rest = 120
                focus = "deload"
                notes = "Settimana recupero - ridurre stress per supercompensazione"
            else:
                # Normale progressione
                intensity = starting_intensity + intensity_step * (week - 1)

                # Fasi basate su settimana
                if week <= 4:
                    # Fase Hypertrophy (volume alto, intensità media)
                    volume = 5
                    reps = (8, 12)
                    rest = 90
                    focus = "hypertrophy"
                    notes = "Focus volume: massimizzare TUT (time under tension)"
                elif week <= 8:
                    # Fase Strength (volume medio, intensità alta)
                    volume = 4
                    reps = (5, 8)
                    rest = 180
                    focus = "strength"
                    notes = "Focus forza: aumentare carico progressivamente"
                else:
                    # Fase Peak (volume basso, intensità massima)
                    volume = 3
                    reps = (3, 5)
                    rest = 240
                    focus = "strength_peak"
                    notes = "Focus peak: massimi carichi, basso volume"

            week_params.append(WeekParameters(
                week_number=week,
                intensity_percent=round(intensity, 2),
                volume_sets=volume,
                reps_per_set=reps,
                rest_seconds=rest,
                is_deload=is_deload,
                focus=focus,
                notes=notes
            ))

        return PeriodizationPlan(
            model_name="Linear Periodization",
            goal=goal,
            total_weeks=weeks,
            weeks=week_params,
            description="""
Modello classico di progressione lineare. Ideale per principianti/intermedi.

Fasi:
1. Hypertrophy (settimane 1-4): Volume alto, intensità 60-70%
2. Strength (settimane 5-8): Volume medio, intensità 70-80%
3. Peak (settimane 9-12): Volume basso, intensità 80-90%

Deload ogni 4 settimane per recupero e supercompensazione.
            """,
            methodology="Progressione lineare intensità con riduzione volume",
            expected_outcomes=f"Incremento {goal.value} del 10-20% in {weeks} settimane"
        )

    @staticmethod
    def block_periodization(
        weeks: int = 12,
        goal: Goal = Goal.STRENGTH
    ) -> PeriodizationPlan:
        """
        Block Periodization (BP) - Modello a blocchi concentrati

        Caratteristiche:
        - Ogni blocco (3-4 settimane) focus su UNA qualità
        - Blocchi sequenziali: Accumulation → Intensification → Realization
        - Minimo fatigue carry-over tra blocchi
        - Deload tra blocchi

        Blocks:
        1. Accumulation: Volume alto, intensità media (fondamenta)
        2. Intensification: Volume medio, intensità alta (specifico)
        3. Realization: Volume basso, intensità massima (peak)

        Args:
            weeks: Durata totale (9-15 settimane tipico)
            goal: Obiettivo (STRENGTH, HYPERTROPHY, POWER)

        Returns:
            PeriodizationPlan con blocchi distinti
        """
        week_params = []

        # Divide in 3 blocchi (Accumulation, Intensification, Realization)
        block_length = weeks // 3

        for week in range(1, weeks + 1):
            # Determina blocco corrente
            if week <= block_length:
                # BLOCK 1: ACCUMULATION (volume alto, intensità media)
                block = "accumulation"
                intensity = 0.65
                volume = 6
                reps = (10, 12)
                rest = 90
                focus = "work_capacity"
                notes = "Blocco Accumulation: costruire capacità lavoro e adattamenti generali"
            elif week <= block_length * 2:
                # BLOCK 2: INTENSIFICATION (volume medio, intensità alta)
                block = "intensification"
                intensity = 0.75
                volume = 4
                reps = (6, 8)
                rest = 150
                focus = "specific_strength"
                notes = "Blocco Intensification: sviluppare qualità specifica (forza/potenza)"
            else:
                # BLOCK 3: REALIZATION (volume basso, intensità massima)
                block = "realization"
                intensity = 0.85
                volume = 3
                reps = (3, 5)
                rest = 240
                focus = "peak_performance"
                notes = "Blocco Realization: esprimere massimo potenziale"

            # Deload ultima settimana di ogni blocco
            is_deload = week % block_length == 0 and week < weeks

            if is_deload:
                intensity *= 0.75
                volume = max(2, volume - 2)
                notes += " | DELOAD: recupero tra blocchi"

            week_params.append(WeekParameters(
                week_number=week,
                intensity_percent=round(intensity, 2),
                volume_sets=volume,
                reps_per_set=reps,
                rest_seconds=rest,
                is_deload=is_deload,
                focus=block,
                notes=notes
            ))

        return PeriodizationPlan(
            model_name="Block Periodization",
            goal=goal,
            total_weeks=weeks,
            weeks=week_params,
            description="""
Modello a blocchi con focus concentrato su singola qualità per blocco.

Blocchi:
1. Accumulation (volume alto): Costruire capacità lavoro
2. Intensification (intensità alta): Sviluppare forza specifica
3. Realization (peak): Esprimere massima performance

Ogni blocco dura 3-4 settimane con deload tra blocchi.
Ideale per atleti intermedi/avanzati.
            """,
            methodology="Concentrazione su singola qualità per blocco sequenziale",
            expected_outcomes=f"Massimizzazione {goal.value} con ridotto fatigue residuo"
        )

    @staticmethod
    def daily_undulating_periodization(
        weeks: int = 8,
        sessions_per_week: int = 3,
        goal: Goal = Goal.HYPERTROPHY
    ) -> PeriodizationPlan:
        """
        Daily Undulating Periodization (DUP) - Variazione giornaliera

        Caratteristiche:
        - Ogni sessione focus diverso (heavy, moderate, light)
        - Variazione intra-settimana (non lineare)
        - Ottimo per adattamenti multipli simultanei
        - Deload ogni 4 settimane

        Esempio settimana:
        - Lunedì: Heavy (85%, 3-5 rep) - Forza
        - Mercoledì: Moderate (75%, 8-10 rep) - Ipertrofia
        - Venerdì: Light (65%, 12-15 rep) - Pump/Tecnica

        Args:
            weeks: Durata totale (6-12 settimane tipico)
            sessions_per_week: Sessioni/settimana (3-4 tipico)
            goal: Obiettivo primario

        Returns:
            PeriodizationPlan con undulating pattern
        """
        week_params = []

        # Pattern DUP ciclico (Heavy → Moderate → Light → repeat)
        dup_patterns = [
            # Heavy Day
            {
                "intensity": 0.85,
                "volume": 3,
                "reps": (3, 5),
                "rest": 240,
                "focus": "max_strength",
                "notes": "Heavy day: focus forza massimale"
            },
            # Moderate Day
            {
                "intensity": 0.75,
                "volume": 4,
                "reps": (8, 10),
                "rest": 120,
                "focus": "hypertrophy",
                "notes": "Moderate day: focus ipertrofia"
            },
            # Light Day
            {
                "intensity": 0.65,
                "volume": 5,
                "reps": (12, 15),
                "rest": 90,
                "focus": "muscular_endurance",
                "notes": "Light day: focus pump e tecnica"
            }
        ]

        for week in range(1, weeks + 1):
            # Deload ogni 4 settimane
            is_deload = week % 4 == 0

            # Scegli pattern per questa settimana (ruota tra i 3)
            pattern_index = (week - 1) % len(dup_patterns)
            pattern = dup_patterns[pattern_index]

            if is_deload:
                intensity = pattern["intensity"] * 0.70
                volume = 2
                reps = (6, 8)
                rest = 120
                focus = "deload"
                notes = "Deload week: recupero e supercompensazione"
            else:
                intensity = pattern["intensity"]
                volume = pattern["volume"]
                reps = pattern["reps"]
                rest = pattern["rest"]
                focus = pattern["focus"]
                notes = pattern["notes"]

            week_params.append(WeekParameters(
                week_number=week,
                intensity_percent=round(intensity, 2),
                volume_sets=volume,
                reps_per_set=reps,
                rest_seconds=rest,
                is_deload=is_deload,
                focus=focus,
                notes=notes
            ))

        return PeriodizationPlan(
            model_name="Daily Undulating Periodization (DUP)",
            goal=goal,
            total_weeks=weeks,
            weeks=week_params,
            description="""
Variazione giornaliera dell'intensità e volume.

Pattern Ciclico (ogni 3 sessioni):
1. Heavy Day (85%, 3-5 rep): Forza massimale
2. Moderate Day (75%, 8-10 rep): Ipertrofia
3. Light Day (65%, 12-15 rep): Pump/Tecnica

Vantaggi:
- Adattamenti multipli simultanei (forza + massa)
- Ridotto rischio overtraining (variazione costante)
- Ottimo per intermedi/avanzati

Deload ogni 4 settimane.
            """,
            methodology="Undulazione giornaliera intensità/volume con pattern ciclico",
            expected_outcomes=f"Sviluppo simultaneo forza e ipertrofia in {weeks} settimane"
        )

    @staticmethod
    def conjugate_method(
        weeks: int = 12
    ) -> PeriodizationPlan:
        """
        Conjugate Method (Westside Barbell) - Metodo coniugato

        Caratteristiche:
        - 4 sessioni/settimana: Max Effort + Dynamic Effort (upper/lower)
        - Variazione esercizio ogni 1-3 settimane (evita plateau)
        - Max Effort: 90%+ per 1-3 rep
        - Dynamic Effort: 50-60% per speed work (6-10 set x 2-3 rep)

        Schedule tipico:
        - Lunedì: Max Effort Lower
        - Mercoledì: Max Effort Upper
        - Venerdì: Dynamic Effort Lower
        - Sabato: Dynamic Effort Upper

        Args:
            weeks: Durata ciclo (8-16 settimane)

        Returns:
            PeriodizationPlan con Westside template
        """
        week_params = []

        for week in range(1, weeks + 1):
            # Deload ogni 4 settimane
            is_deload = week % 4 == 0

            if is_deload:
                intensity = 0.60
                volume = 3
                reps = (5, 8)
                rest = 120
                focus = "deload"
                notes = "Deload: recupero da max efforts"
            else:
                # Alternate between Max Effort and Dynamic Effort focus
                if week % 2 == 1:
                    # Max Effort Week
                    intensity = 0.90
                    volume = 3
                    reps = (1, 3)
                    rest = 300
                    focus = "max_effort"
                    notes = "Max Effort: variare esercizio ogni 1-3 settimane per evitare plateau"
                else:
                    # Dynamic Effort Week
                    intensity = 0.55
                    volume = 8
                    reps = (2, 3)
                    rest = 60
                    focus = "dynamic_effort"
                    notes = "Dynamic Effort: speed work, 50-60% con compensatory acceleration"

            week_params.append(WeekParameters(
                week_number=week,
                intensity_percent=round(intensity, 2),
                volume_sets=volume,
                reps_per_set=reps,
                rest_seconds=rest,
                is_deload=is_deload,
                focus=focus,
                notes=notes
            ))

        return PeriodizationPlan(
            model_name="Conjugate Method (Westside Barbell)",
            goal=Goal.STRENGTH,
            total_weeks=weeks,
            weeks=week_params,
            description="""
Metodo Westside Barbell - Allenamento simultaneo forza e velocità.

Struttura 4 sessioni/settimana:
1. Max Effort Lower (90%+, 1-3 rep): Squat/Deadlift variation
2. Max Effort Upper (90%+, 1-3 rep): Bench Press variation
3. Dynamic Effort Lower (55%, 8x3): Speed Squat/Deadlift
4. Dynamic Effort Upper (55%, 8x3): Speed Bench

Principi chiave:
- Variare esercizio max effort ogni 1-3 settimane
- Dynamic effort con compensatory acceleration (CAT)
- Volume accessori alto per weak points

Ideale per powerlifters e atleti forza avanzati.
            """,
            methodology="Allenamento simultaneo max effort e dynamic effort con variazione costante",
            expected_outcomes=f"Massimizzazione forza massimale e velocità in {weeks} settimane"
        )

    @staticmethod
    def auto_regulation_rpe(
        weeks: int = 8,
        target_rpe: float = 8.0,
        goal: Goal = Goal.STRENGTH
    ) -> PeriodizationPlan:
        """
        Auto-Regulation basata su RPE (Rate of Perceived Exertion)

        Caratteristiche:
        - Carico auto-regolato in base a RPE percepito (scala 1-10)
        - Adatta volume/intensità in base a recupero
        - Evita overtraining con feedback giornaliero
        - Progressione basata su readiness

        RPE Scale:
        - 10: Max effort, nessuna rep in riserva (RIR 0)
        - 9: 1 rep in riserva (RIR 1)
        - 8: 2 rep in riserva (RIR 2)
        - 7: 3 rep in riserva (RIR 3)
        - 6-: Easy work

        Args:
            weeks: Durata programma
            target_rpe: RPE target medio (7-9 tipico)
            goal: Obiettivo allenamento

        Returns:
            PeriodizationPlan con RPE-based auto-regulation
        """
        week_params = []

        for week in range(1, weeks + 1):
            # Deload ogni 4 settimane
            is_deload = week % 4 == 0

            if is_deload:
                intensity = 0.60
                volume = 3
                reps = (6, 8)
                rest = 120
                target_rpe_week = 6.0
                focus = "deload"
                notes = f"Deload: RPE {target_rpe_week} (facile, recupero)"
            else:
                # Progressione RPE nelle settimane (7.5 → 8.5 → 9)
                if week <= weeks // 3:
                    # Fase iniziale: RPE moderato
                    target_rpe_week = 7.5
                    intensity = 0.70
                    volume = 4
                    reps = (6, 8)
                    rest = 150
                    focus = "moderate_rpe"
                    notes = f"RPE {target_rpe_week}: ~2-3 rep in riserva"
                elif week <= (weeks // 3) * 2:
                    # Fase intermedia: RPE alto
                    target_rpe_week = 8.5
                    intensity = 0.80
                    volume = 4
                    reps = (5, 6)
                    rest = 180
                    focus = "high_rpe"
                    notes = f"RPE {target_rpe_week}: ~1 rep in riserva"
                else:
                    # Fase finale: RPE massimo
                    target_rpe_week = 9.0
                    intensity = 0.85
                    volume = 3
                    reps = (3, 5)
                    rest = 240
                    focus = "peak_rpe"
                    notes = f"RPE {target_rpe_week}: ~0-1 rep in riserva, vicino max"

            week_params.append(WeekParameters(
                week_number=week,
                intensity_percent=round(intensity, 2),
                volume_sets=volume,
                reps_per_set=reps,
                rest_seconds=rest,
                is_deload=is_deload,
                focus=focus,
                notes=notes
            ))

        return PeriodizationPlan(
            model_name="RPE-Based Auto-Regulation",
            goal=goal,
            total_weeks=weeks,
            weeks=week_params,
            description=f"""
Auto-regolazione basata su RPE (Rate of Perceived Exertion).

RPE Scale:
- 10: Max, 0 rep riserva
- 9: 1 rep riserva
- 8: 2 rep riserva
- 7: 3 rep riserva

Target RPE Medio: {target_rpe}

Progressione:
1. Settimane 1-{weeks//3}: RPE 7-7.5 (build-up)
2. Settimane {weeks//3+1}-{(weeks//3)*2}: RPE 8-8.5 (intensify)
3. Settimane {(weeks//3)*2+1}-{weeks}: RPE 9+ (peak)

Vantaggi:
- Adatta carico in base a recupero giornaliero
- Riduce rischio overtraining
- Progressione individualizzata

Deload ogni 4 settimane (RPE 6).
            """,
            methodology="Auto-regolazione carico basata su RPE percepito e readiness",
            expected_outcomes=f"Progressione sostenibile {goal.value} con ridotto rischio infortuni in {weeks} settimane"
        )


# ══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════

def get_periodization_plan(
    model: str,
    weeks: int = 12,
    goal: Goal = Goal.STRENGTH,
    **kwargs
) -> PeriodizationPlan:
    """
    Factory per ottenere un piano di periodizzazione

    Args:
        model: Nome modello ("linear", "block", "dup", "conjugate", "rpe")
        weeks: Durata settimane
        goal: Obiettivo
        **kwargs: Parametri aggiuntivi specifici per modello

    Returns:
        PeriodizationPlan configurato

    Raises:
        ValueError se modello non riconosciuto
    """
    models_map = {
        "linear": PeriodizationModels.linear_periodization,
        "block": PeriodizationModels.block_periodization,
        "dup": PeriodizationModels.daily_undulating_periodization,
        "conjugate": PeriodizationModels.conjugate_method,
        "rpe": PeriodizationModels.auto_regulation_rpe
    }

    if model.lower() not in models_map:
        raise ValueError(f"Modello '{model}' non riconosciuto. Disponibili: {list(models_map.keys())}")

    return models_map[model.lower()](weeks=weeks, goal=goal, **kwargs)


def print_periodization_summary(plan: PeriodizationPlan):
    """Stampa summary di un piano di periodizzazione"""
    print(f"\n{'='*60}")
    print(f"📊 {plan.model_name}")
    print(f"{'='*60}")
    print(f"Goal: {plan.goal.value.upper()}")
    print(f"Durata: {plan.total_weeks} settimane")
    print(f"\n{plan.description}")
    print(f"\n{'─'*60}")
    print(f"Settimana | Intensità | Volume | Rep Range | Rest | Focus")
    print(f"{'─'*60}")

    for week in plan.weeks:
        deload_marker = "🔄 " if week.is_deload else "   "
        print(f"{deload_marker}W{week.week_number:2d}      | "
              f"{week.intensity_percent*100:5.1f}%    | "
              f"{week.volume_sets:2d} set | "
              f"{week.reps_per_set[0]:2d}-{week.reps_per_set[1]:2d}    | "
              f"{week.rest_seconds:3d}s | "
              f"{week.focus}")

    print(f"{'─'*60}\n")


if __name__ == "__main__":
    # Test: Genera tutti i 5 modelli
    print("🏋️ Testing Periodization Models\n")

    # 1. Linear
    linear = get_periodization_plan("linear", weeks=12, goal=Goal.STRENGTH)
    print_periodization_summary(linear)

    # 2. Block
    block = get_periodization_plan("block", weeks=12, goal=Goal.STRENGTH)
    print_periodization_summary(block)

    # 3. DUP
    dup = get_periodization_plan("dup", weeks=8, goal=Goal.HYPERTROPHY)
    print_periodization_summary(dup)

    # 4. Conjugate
    conjugate = get_periodization_plan("conjugate", weeks=12)
    print_periodization_summary(conjugate)

    # 5. RPE
    rpe = get_periodization_plan("rpe", weeks=8, goal=Goal.STRENGTH, target_rpe=8.0)
    print_periodization_summary(rpe)
