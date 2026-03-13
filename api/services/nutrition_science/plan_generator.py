"""
Generatore piano alimentare LARN-compliant.

Orchestratore: profilo cliente → piano settimanale 7 giorni × 5 pasti.

Pipeline:
1. Risolvi food pool da nutrition.db
2. Per ogni giorno: seleziona alimenti con rotazione proteica
3. Ottimizza porzioni per target calorico e macro
4. Valida vs LARN
5. Ritorna struttura pronta per il salvataggio

L'output e' una lista di (giorno, tipo_pasto, [(food_id, grammi)]) che
il router converte in PlanMeal + MealComponent nel crm.db.
"""

import random
from dataclasses import dataclass, field

from sqlmodel import Session

from api.models.nutrition import Food
from api.services.nutrition_science.food_selector import (
    build_day_selections,
    resolve_food_pools,
)
from api.services.nutrition_science.meal_archetypes import (
    ARCHETYPES,
    MEAL_ORDER,
    WEEKLY_PROTEIN_ROTATION,
)
from api.services.nutrition_science.portion_optimizer import optimize_day
from api.services.nutrition_science.plan_validator import validate_plan
from api.services.nutrition_science.types import ClientProfile


@dataclass
class GeneratedMealComponent:
    """Componente generato (alimento × grammi)."""
    food_id: int
    food_nome: str
    quantita_g: float


@dataclass
class GeneratedMeal:
    """Pasto generato."""
    giorno_settimana: int   # 1-7
    tipo_pasto: str         # COLAZIONE, PRANZO, etc.
    ordine: int
    componenti: list[GeneratedMealComponent] = field(default_factory=list)


@dataclass
class GeneratedPlan:
    """Piano generato completo."""
    pasti: list[GeneratedMeal] = field(default_factory=list)
    kcal_die_media: float = 0
    score_larn: int = 0
    warnings: list[str] = field(default_factory=list)


def generate_plan(
    session: Session,
    profile: ClientProfile,
    target_kcal: int,
    target_prot_g: int | None = None,
    target_carb_g: int | None = None,
    target_fat_g: int | None = None,
    seed: int | None = None,
) -> GeneratedPlan:
    """
    Genera un piano alimentare settimanale LARN-compliant.

    Args:
        session: sessione nutrition.db
        profile: profilo cliente (eta', sesso, peso)
        target_kcal: obiettivo calorico /die
        target_prot_g: obiettivo proteine g/die (auto-calcolato se None)
        target_carb_g: obiettivo carboidrati g/die (auto-calcolato se None)
        target_fat_g: obiettivo grassi g/die (auto-calcolato se None)
        seed: seed per riproducibilita' (None = random)

    Returns:
        GeneratedPlan pronto per il salvataggio
    """
    rng = random.Random(seed)

    # Auto-calcolo macro se non specificati (LARN range)
    if target_prot_g is None:
        # 15% kcal da proteine (centro range LARN 12-20%)
        target_prot_g = round(target_kcal * 0.15 / 4)
    if target_carb_g is None:
        # 52.5% kcal da carboidrati (centro range LARN 45-60%)
        target_carb_g = round(target_kcal * 0.525 / 4)
    if target_fat_g is None:
        # 27.5% kcal da grassi (centro range LARN 20-35%)
        target_fat_g = round(target_kcal * 0.275 / 9)

    # Se peso disponibile, aggiusta proteine per g/kg
    if profile.peso_kg and profile.peso_kg > 0:
        prot_gkg = target_prot_g / profile.peso_kg
        if prot_gkg < 0.90:  # sotto PRI LARN
            target_prot_g = round(profile.peso_kg * 0.90)

    # 1. Risolvi food pool
    pools = resolve_food_pools(session)

    # 2-3. Per ogni giorno: seleziona + ottimizza
    all_meals: list[GeneratedMeal] = []
    used_yesterday: set[int] = set()

    for giorno in range(1, 8):  # Lun-Dom
        # Seleziona alimenti
        day_selections = build_day_selections(giorno, pools, used_yesterday, rng)

        # Converti in formato optimizer: [(tipo, [(Food, grammi, ruolo)])]
        # Determina pool proteici del giorno per mappare ruoli corretti
        pranzo_pool, cena_pool = WEEKLY_PROTEIN_ROTATION[giorno - 1]

        day_for_opt: list[tuple[str, list[tuple[Food, float, str]]]] = []
        for tipo_pasto, food_list in day_selections:
            arch = ARCHETYPES.get(tipo_pasto)
            items: list[tuple[Food, float, str]] = []
            for i, (food, grammi) in enumerate(food_list):
                ruolo = arch.slots[i].ruolo if arch and i < len(arch.slots) else "other"
                # Mappa protein_main → pool specifico per limiti porzione corretti
                if ruolo == "protein_main":
                    ruolo = pranzo_pool if tipo_pasto == "PRANZO" else cena_pool
                items.append((food, grammi, ruolo))
            day_for_opt.append((tipo_pasto, items))

        # Ottimizza porzioni
        optimized = optimize_day(day_for_opt, target_kcal, target_prot_g, target_fat_g)

        # Converti in GeneratedMeal
        used_today: set[int] = set()
        for tipo_pasto, foods in optimized:
            ordine = MEAL_ORDER.index(tipo_pasto) if tipo_pasto in MEAL_ORDER else 0
            meal = GeneratedMeal(
                giorno_settimana=giorno,
                tipo_pasto=tipo_pasto,
                ordine=ordine,
            )
            for food, grammi, _ in foods:
                meal.componenti.append(GeneratedMealComponent(
                    food_id=food.id,
                    food_nome=food.nome,
                    quantita_g=round(grammi),
                ))
                used_today.add(food.id)
            all_meals.append(meal)

        used_yesterday = used_today

    # 4. Valida vs LARN (calcola media settimanale)
    micro_fields = [
        "calcio_mg", "ferro_mg", "zinco_mg", "magnesio_mg", "fosforo_mg",
        "potassio_mg", "selenio_ug", "sodio_mg", "fibra_g",
        "vitamina_a_ug", "vitamina_d_ug", "vitamina_e_mg", "vitamina_c_mg",
        "vitamina_b1_mg", "vitamina_b2_mg", "vitamina_b3_mg", "vitamina_b6_mg",
        "vitamina_b9_ug", "vitamina_b12_ug",
    ]

    # Build food_map per il calcolo
    all_food_ids = {c.food_id for m in all_meals for c in m.componenti}
    from sqlmodel import select
    foods_db = session.exec(select(Food).where(Food.id.in_(list(all_food_ids)))).all()
    food_map = {f.id: f for f in foods_db}

    # Somma totali settimanali
    total_kcal = 0.0
    total_prot = 0.0
    total_carb = 0.0
    total_fat = 0.0
    micro_totals: dict[str, float] = {f: 0.0 for f in micro_fields}

    for meal in all_meals:
        for comp in meal.componenti:
            food = food_map.get(comp.food_id)
            if not food:
                continue
            ratio = comp.quantita_g / 100.0
            total_kcal += food.energia_kcal * ratio
            total_prot += food.proteine_g * ratio
            total_carb += food.carboidrati_g * ratio
            total_fat += food.grassi_g * ratio
            for field_name in micro_fields:
                val = getattr(food, field_name, None)
                if val is not None:
                    micro_totals[field_name] += val * ratio

    n_giorni = 7
    daily_nutrients = {k: v / n_giorni for k, v in micro_totals.items()}

    validation = validate_plan(
        profile=profile,
        daily_nutrients=daily_nutrients,
        kcal_die=total_kcal / n_giorni,
        proteine_g_die=total_prot / n_giorni,
        carboidrati_g_die=total_carb / n_giorni,
        grassi_g_die=total_fat / n_giorni,
    )

    return GeneratedPlan(
        pasti=all_meals,
        kcal_die_media=round(total_kcal / n_giorni, 1),
        score_larn=validation.score,
        warnings=validation.warnings,
    )
