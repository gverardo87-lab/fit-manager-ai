"""
Ottimizzatore porzioni per compliance LARN.

Dato un piano con alimenti selezionati e porzioni default, aggiusta
le quantita' per avvicinarsi ai target calorici e LARN.

Approccio: scaling proporzionale iterativo.
1. Scala tutte le porzioni per centrare il target calorico
2. Aggiusta proteine (scala fonti proteiche)
3. Aggiusta grassi (scala olio + frutta secca)
4. Verifica micro e genera warning se irrecuperabili
"""

from api.models.nutrition import Food


# Limiti porzione ragionevoli (grammi)
PORTION_LIMITS: dict[str, tuple[float, float]] = {
    "dairy":          (100, 250),
    "dairy_light":    (100, 200),
    "cereal":         (25, 70),
    "carb_cooked":    (50, 150),
    "carb_light":     (20, 80),
    "bread":          (20, 60),
    "fruit":          (100, 250),
    "nuts":           (10, 35),
    "vegetable":      (100, 400),
    "fat":            (5, 20),
    "protein_main":   (80, 200),
    "protein_poultry": (80, 200),
    "protein_fish":   (80, 200),
    "protein_legume": (100, 250),
    "protein_egg":    (120, 240),  # 2-4 uova
    "protein_red_meat": (80, 180),
    "protein_deli":   (40, 80),
}


def _calc_day_totals(
    day_meals: list[tuple[str, list[tuple[Food, float, str]]]],
) -> dict[str, float]:
    """Calcola totali giornalieri (kcal + macro + micro)."""
    totals: dict[str, float] = {
        "kcal": 0, "proteine_g": 0, "carboidrati_g": 0, "grassi_g": 0,
        "fibra_g": 0, "calcio_mg": 0, "ferro_mg": 0, "zinco_mg": 0,
        "vitamina_d_ug": 0, "vitamina_c_mg": 0, "vitamina_b12_ug": 0,
    }
    for _, foods in day_meals:
        for food, grammi, _ in foods:
            ratio = grammi / 100.0
            totals["kcal"] += food.energia_kcal * ratio
            totals["proteine_g"] += food.proteine_g * ratio
            totals["carboidrati_g"] += food.carboidrati_g * ratio
            totals["grassi_g"] += food.grassi_g * ratio
            if food.fibra_g:
                totals["fibra_g"] += food.fibra_g * ratio
            if food.calcio_mg:
                totals["calcio_mg"] += food.calcio_mg * ratio
            if food.ferro_mg:
                totals["ferro_mg"] += food.ferro_mg * ratio
            if food.zinco_mg:
                totals["zinco_mg"] += food.zinco_mg * ratio
            if food.vitamina_d_ug:
                totals["vitamina_d_ug"] += food.vitamina_d_ug * ratio
            if food.vitamina_c_mg:
                totals["vitamina_c_mg"] += food.vitamina_c_mg * ratio
            if food.vitamina_b12_ug:
                totals["vitamina_b12_ug"] += food.vitamina_b12_ug * ratio
    return totals


def _clamp(value: float, ruolo: str) -> float:
    """Limita grammi ai range ragionevoli per il ruolo."""
    lo, hi = PORTION_LIMITS.get(ruolo, (10, 500))
    return max(lo, min(hi, value))


def optimize_day(
    day_meals: list[tuple[str, list[tuple[Food, float, str]]]],
    target_kcal: float,
    target_prot_g: float | None = None,
    target_fat_g: float | None = None,
) -> list[tuple[str, list[tuple[Food, float, str]]]]:
    """
    Ottimizza le porzioni di un giorno per avvicinarsi ai target.

    Args:
        day_meals: [(tipo_pasto, [(Food, grammi, ruolo), ...]), ...]
        target_kcal: obiettivo calorico giornaliero
        target_prot_g: obiettivo proteine (opzionale)
        target_fat_g: obiettivo grassi (opzionale)

    Returns:
        day_meals aggiornato con porzioni ottimizzate
    """
    if target_kcal <= 0:
        return day_meals

    # --- Step 1: scala globale per centrare kcal ---
    totals = _calc_day_totals(day_meals)
    if totals["kcal"] <= 0:
        return day_meals

    kcal_ratio = target_kcal / totals["kcal"]
    # Limita scaling a ±60% per coprire range 1400-2800 kcal
    kcal_ratio = max(0.4, min(1.6, kcal_ratio))

    result: list[tuple[str, list[tuple[Food, float, str]]]] = []
    for tipo, foods in day_meals:
        scaled = []
        for food, grammi, ruolo in foods:
            new_g = _clamp(grammi * kcal_ratio, ruolo)
            scaled.append((food, round(new_g), ruolo))
        result.append((tipo, scaled))

    # --- Step 2: aggiusta proteine ---
    if target_prot_g and target_prot_g > 0:
        totals = _calc_day_totals(result)
        prot_delta = target_prot_g - totals["proteine_g"]

        if abs(prot_delta) > 5:  # margine di 5g
            # Trova alimenti proteici e scala
            protein_roles = {
                "protein_main", "protein_poultry", "protein_fish",
                "protein_legume", "protein_egg", "protein_red_meat", "protein_deli",
            }
            adjusted = []
            for tipo, foods in result:
                new_foods = []
                for food, grammi, ruolo in foods:
                    if ruolo in protein_roles and food.proteine_g > 10:
                        # Quanti grammi servono per coprire il delta
                        prot_per_g = food.proteine_g / 100.0
                        extra_g = prot_delta / max(prot_per_g * 3, 0.1)  # distribuisci su ~3 pasti
                        new_g = _clamp(grammi + extra_g, ruolo)
                        new_foods.append((food, round(new_g), ruolo))
                    else:
                        new_foods.append((food, grammi, ruolo))
                adjusted.append((tipo, new_foods))
            result = adjusted

    # --- Step 3: aggiusta grassi (olio + noci) ---
    if target_fat_g and target_fat_g > 0:
        totals = _calc_day_totals(result)
        fat_delta = target_fat_g - totals["grassi_g"]

        if abs(fat_delta) > 3:
            fat_roles = {"fat", "nuts"}
            adjusted = []
            for tipo, foods in result:
                new_foods = []
                for food, grammi, ruolo in foods:
                    if ruolo in fat_roles and food.grassi_g > 5:
                        fat_per_g = food.grassi_g / 100.0
                        extra_g = fat_delta / max(fat_per_g * 2, 0.1)
                        new_g = _clamp(grammi + extra_g, ruolo)
                        new_foods.append((food, round(new_g), ruolo))
                    else:
                        new_foods.append((food, grammi, ruolo))
                adjusted.append((tipo, new_foods))
            result = adjusted

    # --- Step 4: ri-bilancia kcal via carboidrati ---
    # Dopo aggiustamento proteine/grassi, le kcal possono essere sbilanciate.
    # Correggi scalando le fonti di carboidrati.
    totals = _calc_day_totals(result)
    kcal_gap = target_kcal - totals["kcal"]
    if abs(kcal_gap) > 50:  # margine 50 kcal
        carb_roles = {"carb_cooked", "carb_light", "cereal", "bread"}
        # Calcola kcal totali da fonti carb
        carb_kcal = 0
        for _, foods in result:
            for food, grammi, ruolo in foods:
                if ruolo in carb_roles:
                    carb_kcal += food.energia_kcal * grammi / 100.0
        if carb_kcal > 0:
            carb_scale = 1 + (kcal_gap / carb_kcal)
            carb_scale = max(0.5, min(2.0, carb_scale))
            adjusted = []
            for tipo, foods in result:
                new_foods = []
                for food, grammi, ruolo in foods:
                    if ruolo in carb_roles:
                        new_g = _clamp(grammi * carb_scale, ruolo)
                        new_foods.append((food, round(new_g), ruolo))
                    else:
                        new_foods.append((food, grammi, ruolo))
                adjusted.append((tipo, new_foods))
            result = adjusted

    return result
