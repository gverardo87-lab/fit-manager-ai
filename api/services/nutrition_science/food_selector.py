"""
Selettore alimenti v2 per il generatore LARN.

Risolve nomi food → ID da nutrition.db, seleziona alimenti dai pool
con vincoli di varieta' (no ripetizioni consecutive).

v2: gestisce pietanze composte (primo/secondo piatto) e ingredienti singoli.
La rotazione proteica settimanale si applica al secondo piatto (CENA).
"""

import random
from typing import Optional

from sqlmodel import Session, select

from api.models.nutrition import Food
from api.services.nutrition_science.meal_archetypes import (
    ARCHETYPES,
    FOOD_POOLS,
    MEAL_ORDER,
    WEEKLY_SECONDO_ROTATION,
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


def _pick_from_pool(
    pool: list[Food],
    used_today: set[int],
    used_yesterday: set[int],
    rng: random.Random,
) -> Optional[Food]:
    """Seleziona un alimento dal pool evitando ripetizioni."""
    avoid = used_today | used_yesterday
    candidates = [f for f in pool if f.id not in avoid]
    if not candidates:
        candidates = [f for f in pool if f.id not in used_today]
    if not candidates:
        candidates = pool
    if not candidates:
        return None
    return rng.choice(candidates)


def build_day_selections(
    giorno: int,
    pools: dict[str, list[Food]],
    used_yesterday: set[int],
    rng: random.Random,
) -> list[tuple[str, list[tuple[Food, float]]]]:
    """
    Costruisce le selezioni per un giorno completo.

    v2: PRANZO usa primo_piatto, CENA usa secondo_piatto (protein-rotated).
    Contorno e' un pool unificato (pietanze + ingredienti).

    Ritorna: [(tipo_pasto, [(Food, grammi), ...]), ...]
    """
    # Pool secondo piatto per oggi (da rotazione settimanale)
    secondo_pool_name = WEEKLY_SECONDO_ROTATION[giorno - 1]

    used_today: set[int] = set()
    day_meals: list[tuple[str, list[tuple[Food, float]]]] = []

    for tipo_pasto in MEAL_ORDER:
        arch = ARCHETYPES.get(tipo_pasto)
        if not arch:
            continue

        meal_foods: list[tuple[Food, float]] = []

        for slot in arch.slots:
            food: Optional[Food] = None

            if slot.ruolo == "secondo_piatto":
                # Secondo piatto: usa il pool proteico del giorno
                pool = pools.get(secondo_pool_name, [])
                food = _pick_from_pool(pool, used_today, used_yesterday, rng)
            else:
                # Tutti gli altri slot: usa il pool del ruolo
                pool = pools.get(slot.ruolo, [])
                food = _pick_from_pool(pool, used_today, used_yesterday, rng)

            if food:
                meal_foods.append((food, slot.grammi))
                used_today.add(food.id)
            elif slot.obbligatorio:
                pass  # skip silenzioso se pool vuoto

        if meal_foods:
            day_meals.append((tipo_pasto, meal_foods))

    return day_meals
