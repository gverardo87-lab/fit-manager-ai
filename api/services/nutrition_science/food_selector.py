"""
Selettore alimenti per il generatore LARN.

Risolve nomi food → ID da nutrition.db, seleziona alimenti dai pool
con vincoli di varieta' (no ripetizioni consecutive), gestisce la
rotazione proteica settimanale.
"""

import random
from typing import Optional

from sqlmodel import Session, select

from api.models.nutrition import Food
from api.services.nutrition_science.meal_archetypes import (
    FOOD_POOLS,
    MEAL_ORDER,
    WEEKLY_PROTEIN_ROTATION,
    MealSlot,
)


def resolve_food_pools(session: Session) -> dict[str, list[Food]]:
    """
    Carica i food pool da nutrition.db.

    Ritorna: {ruolo: [Food, ...]} con oggetti ORM completi.
    Ignora nomi non trovati (warning silenzioso).
    """
    # Batch: carica tutti i nomi necessari in una query
    all_names: set[str] = set()
    for pool_names in FOOD_POOLS.values():
        all_names.update(pool_names)

    foods = session.exec(
        select(Food).where(Food.nome.in_(list(all_names)), Food.is_active == True)
    ).all()
    name_to_food = {f.nome: f for f in foods}

    pools: dict[str, list[Food]] = {}
    for role, names in FOOD_POOLS.items():
        pool = [name_to_food[n] for n in names if n in name_to_food]
        if pool:
            pools[role] = pool

    return pools


def select_food_for_slot(
    slot: MealSlot,
    pools: dict[str, list[Food]],
    giorno: int,
    used_today: set[int],
    used_yesterday: set[int],
    rng: random.Random,
    protein_pool_override: Optional[str] = None,
) -> Optional[Food]:
    """
    Seleziona un alimento per uno slot, rispettando varieta'.

    Args:
        slot: lo slot da riempire (ruolo + grammi)
        pools: pool risolti da resolve_food_pools()
        giorno: 1-7
        used_today: set di food.id gia' usati oggi
        used_yesterday: set di food.id usati il giorno prima
        rng: generatore random (seed deterministico)
        protein_pool_override: se presente, usa questo pool invece di slot.ruolo
    """
    ruolo = protein_pool_override or slot.ruolo

    # protein_main → risolvi dal pool specifico del giorno
    if ruolo == "protein_main":
        return None  # gestito dal caller tramite protein_pool_override

    pool = pools.get(ruolo, [])
    if not pool:
        return None

    # Filtra: evita ripetizioni oggi e ieri
    avoid = used_today | used_yesterday
    candidates = [f for f in pool if f.id not in avoid]

    # Fallback: se nessun candidato, rilassa vincolo ieri
    if not candidates:
        candidates = [f for f in pool if f.id not in used_today]
    if not candidates:
        candidates = pool

    return rng.choice(candidates)


def build_day_selections(
    giorno: int,
    pools: dict[str, list[Food]],
    used_yesterday: set[int],
    rng: random.Random,
) -> list[tuple[str, list[tuple[Food, float]]]]:
    """
    Costruisce le selezioni per un giorno completo.

    Ritorna: [(tipo_pasto, [(Food, grammi), ...]), ...]
    """
    from api.services.nutrition_science.meal_archetypes import ARCHETYPES

    pranzo_pool, cena_pool = WEEKLY_PROTEIN_ROTATION[giorno - 1]
    used_today: set[int] = set()
    day_meals: list[tuple[str, list[tuple[Food, float]]]] = []

    for tipo_pasto in MEAL_ORDER:
        arch = ARCHETYPES.get(tipo_pasto)
        if not arch:
            continue

        meal_foods: list[tuple[Food, float]] = []

        for slot in arch.slots:
            food: Optional[Food] = None

            if slot.ruolo == "protein_main":
                # Usa il pool proteico specifico per questo pasto
                if tipo_pasto == "PRANZO":
                    prot_pool = pools.get(pranzo_pool, [])
                elif tipo_pasto == "CENA":
                    prot_pool = pools.get(cena_pool, [])
                else:
                    prot_pool = []

                if prot_pool:
                    avoid = used_today | used_yesterday
                    candidates = [f for f in prot_pool if f.id not in avoid]
                    if not candidates:
                        candidates = [f for f in prot_pool if f.id not in used_today]
                    if not candidates:
                        candidates = prot_pool
                    food = rng.choice(candidates)
            else:
                food = select_food_for_slot(
                    slot, pools, giorno, used_today, used_yesterday, rng,
                )

            if food:
                # Uova: porzione in unita' (1 uovo ~60g), 2-3 uova per pasto
                grammi = slot.grammi
                if food.nome == "Uovo intero, crudo" and slot.ruolo == "protein_main":
                    grammi = 180  # ~3 uova
                meal_foods.append((food, grammi))
                used_today.add(food.id)
            elif slot.obbligatorio:
                pass  # skip silenzioso se pool vuoto

        if meal_foods:
            day_meals.append((tipo_pasto, meal_foods))

    return day_meals
