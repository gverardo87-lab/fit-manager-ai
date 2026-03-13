"""
Validatore piano alimentare vs LARN 2014 + Linee Guida CREA 2018.

Scoring v2 a 3 assi:
  - Asse 1 (25%): Distribuzione macro (% kcal P/C/G nel range LARN)
  - Asse 2 (35%): Micronutrienti (19 nutrienti vs AR/PRI/AI/UL)
  - Asse 3 (40%): Frequenze alimentari (porzioni/settimana vs CREA 2018)

Il punteggio a 3 assi risolve il cap ~70% del v1 che pesava 70% micro
(penalizzando nutrienti come Vit.D intrinsecamente carenti dalla dieta).

Logica:
1. Calcola apporto medio giornaliero di ogni nutriente dal piano
2. Lookup riferimento LARN per profilo (eta', sesso, stato fisiologico)
3. Classifica ogni nutriente: ottimale / sufficiente / carente / eccesso
4. Valuta frequenze settimanali vs CREA 2018 (se dati disponibili)
5. Calcola score composito 3-assi 0-100
6. Genera warnings per criticita'
"""

from typing import Optional

from api.services.nutrition_science.larn_portions import DIET_LIMITED_NUTRIENTS
from api.services.nutrition_science.larn_tables import (
    LARN_LACTATION_ADD,
    LARN_PREGNANCY_ADD,
    LARN_PROTEINE_G_KG,
    NUTRIENT_REGISTRY,
    lookup_larn,
)
from api.services.nutrition_science.types import (
    ClientProfile,
    ComplianceStatus,
    MacroDistribution,
    NutrientAssessment,
    NutrientReference,
    PlanValidationResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_physiological_add(
    ref: dict,
    campo_db: str,
    profile: ClientProfile,
) -> dict:
    """Applica addendi gravidanza/allattamento al riferimento LARN."""
    if not profile.gravidanza and not profile.allattamento:
        return ref

    add_table = LARN_PREGNANCY_ADD if profile.gravidanza else LARN_LACTATION_ADD
    adds = add_table.get(campo_db)
    if not adds:
        return ref

    delta_ar, delta_pri, delta_ai = adds
    result = dict(ref)
    if result.get("ar") is not None and delta_ar:
        result["ar"] = result["ar"] + delta_ar
    if result.get("pri") is not None and delta_pri:
        result["pri"] = result["pri"] + delta_pri
    if result.get("ai") is not None and delta_ai:
        result["ai"] = result["ai"] + delta_ai
    return result


def _assess_nutrient(
    apporto: Optional[float],
    ref: dict,
    label: str,
    unita: str,
) -> NutrientAssessment:
    """Valuta un singolo nutriente vs il suo riferimento LARN."""
    nr = NutrientReference(
        nutriente=label,
        unita=unita,
        ar=ref.get("ar"),
        pri=ref.get("pri"),
        ai=ref.get("ai"),
        ul=ref.get("ul"),
    )

    if apporto is None:
        return NutrientAssessment(
            nutriente=label,
            unita=unita,
            apporto_die=None,
            riferimento=nr,
            status=ComplianceStatus.NON_VALUTABILE,
            nota="Dati nutrizionali insufficienti per questo nutriente",
        )

    # Determina target primario (PRI > AI)
    target = nr.pri if nr.pri is not None else nr.ai
    pct = round(apporto / target * 100, 1) if target and target > 0 else None

    # Classifica
    status = ComplianceStatus.NON_VALUTABILE
    nota = None

    if nr.ul is not None and apporto > nr.ul:
        status = ComplianceStatus.ECCESSO
        nota = f"Supera il livello massimo tollerabile (UL={nr.ul} {unita})"
    elif target is not None and apporto >= target:
        status = ComplianceStatus.OTTIMALE
    elif nr.ar is not None and apporto >= nr.ar:
        status = ComplianceStatus.SUFFICIENTE
        nota = f"Sopra AR ({nr.ar}) ma sotto PRI ({nr.pri})"
    elif nr.ar is not None:
        status = ComplianceStatus.CARENTE
        nota = f"Sotto il fabbisogno medio (AR={nr.ar} {unita})"
    elif target is not None:
        # Solo AI, no AR: sotto AI = carente
        status = ComplianceStatus.CARENTE
        nota = f"Sotto l'assunzione adeguata (AI={target} {unita})"
    else:
        status = ComplianceStatus.NON_VALUTABILE

    return NutrientAssessment(
        nutriente=label,
        unita=unita,
        apporto_die=round(apporto, 2) if apporto else None,
        riferimento=nr,
        status=status,
        percentuale_pri=pct,
        nota=nota,
    )


def _compute_micro_score(assessments: list[NutrientAssessment]) -> int:
    """
    Score 0-100 per asse micronutrienti.

    Nutrienti con fonti alimentari limitate (es. Vit.D) ricevono
    peso attenuato: se carenti, contribuiscono 60 invece di 0-40.
    Questo evita che nutrienti irraggiungibili dalla sola dieta
    penalizzino ingiustamente il piano.

    Fonte: LARN 2014 riconosce che Vit.D richiede supplementazione.
    """
    evaluable = [a for a in assessments if a.status != ComplianceStatus.NON_VALUTABILE]
    if not evaluable:
        return 0

    total = 0
    for a in evaluable:
        # Nutriente con fonte alimentare limitata (es. Vit.D)
        is_limited = any(
            a.nutriente.lower() in key.lower() or key.replace("_ug", "").replace("_mg", "").replace("vitamina_", "vitamina ") in a.nutriente.lower()
            for key in DIET_LIMITED_NUTRIENTS
        )

        if a.status == ComplianceStatus.OTTIMALE:
            total += 100
        elif a.status == ComplianceStatus.SUFFICIENTE:
            total += 70
        elif a.status == ComplianceStatus.CARENTE:
            if is_limited:
                # Nutriente intrinsecamente carente: penalita' attenuata
                total += 60
            else:
                pct = a.percentuale_pri or 0
                total += max(0, min(45, pct * 0.45))
        elif a.status == ComplianceStatus.ECCESSO:
            total += 35

    return round(total / len(evaluable))


def _compute_macro_score(
    prot_pct: float,
    carb_pct: float,
    fat_pct: float,
    macro: MacroDistribution,
) -> int:
    """
    Score 0-100 per asse distribuzione macro.

    100 = tutti e 3 nel range LARN.
    Ogni macro fuori range penalizza proporzionalmente alla distanza.
    """
    score = 0
    for val, rng in [
        (prot_pct, macro.proteine_range),
        (carb_pct, macro.carboidrati_range),
        (fat_pct, macro.grassi_range),
    ]:
        if rng[0] <= val <= rng[1]:
            score += 33  # nel range
        else:
            # Distanza dal range piu' vicino, penalita' proporzionale
            if val < rng[0]:
                distance_pct = (rng[0] - val) / rng[0] * 100
            else:
                distance_pct = (val - rng[1]) / rng[1] * 100
            # Penalita' graduale: 5% fuori = 25pt, 10% fuori = 18pt, 20%+ = 0pt
            partial = max(0, 33 - distance_pct * 1.5)
            score += partial
    return round(min(100, score + 1))  # +1 per arrotondamento 3×33=99


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------


def validate_plan(
    profile: ClientProfile,
    daily_nutrients: dict[str, Optional[float]],
    kcal_die: float,
    proteine_g_die: float,
    carboidrati_g_die: float,
    grassi_g_die: float,
    frequency_score: Optional[int] = None,
    frequency_warnings: Optional[list[str]] = None,
) -> PlanValidationResult:
    """
    Valida un piano alimentare contro LARN 2014 + CREA 2018.

    Scoring v2 a 3 assi:
      - Asse 1 (25%): Distribuzione macro (% kcal P/C/G)
      - Asse 2 (35%): Micronutrienti (19 nutrienti vs LARN)
      - Asse 3 (40%): Frequenze alimentari (vs CREA 2018)

    Se frequency_score non e' fornito, il peso viene ridistribuito
    su macro (35%) e micro (65%) per backward-compat.

    Args:
        profile: profilo del cliente (eta', sesso, peso, ecc.)
        daily_nutrients: media giornaliera micronutrienti {campo_db: valore}
        kcal_die: kcal medie giornaliere
        proteine_g_die: grammi proteine /die
        carboidrati_g_die: grammi carboidrati /die
        grassi_g_die: grammi grassi /die
        frequency_score: score frequenze 0-100 (da frequency_validator)
        frequency_warnings: warning frequenze (da frequency_validator)

    Returns:
        PlanValidationResult con assessment completo
    """
    sesso = profile.sesso
    eta = profile.eta
    warnings: list[str] = []

    # --- Distribuzione macro (% kcal) ---
    if kcal_die <= 0:
        return PlanValidationResult(
            profilo=profile,
            kcal_die=0,
            macro=MacroDistribution(proteine_pct=0, carboidrati_pct=0, grassi_pct=0),
            score=0,
            warnings=["Piano vuoto o senza calorie"],
            note_metodologiche="LARN 2014 — SINU IV Revisione + CREA 2018",
        )

    prot_pct = round(proteine_g_die * 4 / kcal_die * 100, 1)
    carb_pct = round(carboidrati_g_die * 4 / kcal_die * 100, 1)
    fat_pct = round(grassi_g_die * 9 / kcal_die * 100, 1)
    macro = MacroDistribution(
        proteine_pct=prot_pct,
        carboidrati_pct=carb_pct,
        grassi_pct=fat_pct,
    )

    # Warnings macro distribution
    if prot_pct < macro.proteine_range[0]:
        warnings.append(f"Proteine basse ({prot_pct}% kcal, LARN: {macro.proteine_range[0]}-{macro.proteine_range[1]}%)")
    elif prot_pct > macro.proteine_range[1]:
        warnings.append(f"Proteine elevate ({prot_pct}% kcal, LARN: {macro.proteine_range[0]}-{macro.proteine_range[1]}%)")

    if carb_pct < macro.carboidrati_range[0]:
        warnings.append(f"Carboidrati bassi ({carb_pct}% kcal, LARN: {macro.carboidrati_range[0]}-{macro.carboidrati_range[1]}%)")
    elif carb_pct > macro.carboidrati_range[1]:
        warnings.append(f"Carboidrati elevati ({carb_pct}% kcal, LARN: {macro.carboidrati_range[0]}-{macro.carboidrati_range[1]}%)")

    if fat_pct < macro.grassi_range[0]:
        warnings.append(f"Grassi bassi ({fat_pct}% kcal, LARN: {macro.grassi_range[0]}-{macro.grassi_range[1]}%)")
    elif fat_pct > macro.grassi_range[1]:
        warnings.append(f"Grassi elevati ({fat_pct}% kcal, LARN: {macro.grassi_range[0]}-{macro.grassi_range[1]}%)")

    # --- Proteine g/kg ---
    assessments: list[NutrientAssessment] = []

    prot_ref = lookup_larn(LARN_PROTEINE_G_KG, eta, sesso)
    if prot_ref and profile.peso_kg and profile.peso_kg > 0:
        prot_g_kg = proteine_g_die / profile.peso_kg
        prot_ref_adj = _apply_physiological_add(prot_ref, "proteine_g_kg", profile)
        assessments.append(_assess_nutrient(
            prot_g_kg, prot_ref_adj, "Proteine", "g/kg",
        ))
    elif prot_ref:
        assessments.append(NutrientAssessment(
            nutriente="Proteine",
            unita="g/kg",
            apporto_die=proteine_g_die,
            riferimento=NutrientReference(
                nutriente="Proteine", unita="g/kg",
                ar=prot_ref.get("ar"), pri=prot_ref.get("pri"),
            ),
            status=ComplianceStatus.NON_VALUTABILE,
            nota="Peso corporeo non disponibile — impossibile valutare g/kg",
        ))

    # --- Micronutrienti ---
    for reg in NUTRIENT_REGISTRY:
        campo = reg["campo_db"]
        label = reg["label"]
        unita = reg["unita"]
        tabella = reg["tabella"]

        ref = lookup_larn(tabella, eta, sesso)
        if not ref:
            continue

        ref = _apply_physiological_add(ref, campo, profile)
        apporto = daily_nutrients.get(campo)
        assessment = _assess_nutrient(apporto, ref, label, unita)
        assessments.append(assessment)

        # Warning specifici
        if assessment.status == ComplianceStatus.CARENTE:
            # Nutriente con fonte alimentare limitata: nota clinica, non warning
            if campo in DIET_LIMITED_NUTRIENTS:
                assessment.nota = DIET_LIMITED_NUTRIENTS[campo]
            else:
                warnings.append(f"{label} carente: {assessment.apporto_die or 0} {unita} "
                                f"(target: {ref.get('pri') or ref.get('ai')} {unita})")
        elif assessment.status == ComplianceStatus.ECCESSO:
            warnings.append(f"{label} in eccesso: {assessment.apporto_die} {unita} "
                            f"(UL: {ref.get('ul')} {unita})")

    # Sodio: warning OMS se > 2000 mg
    sodio = daily_nutrients.get("sodio_mg")
    if sodio is not None and sodio > 2000:
        warnings.append(f"Sodio elevato ({round(sodio)} mg/die, OMS raccomanda < 2000 mg)")

    # --- Score composito v2 (3 assi) ---
    axis_macro = _compute_macro_score(prot_pct, carb_pct, fat_pct, macro)
    axis_micro = _compute_micro_score(assessments)

    if frequency_score is not None:
        # 3 assi: 25% macro + 35% micro + 40% frequenze
        final_score = round(
            axis_macro * 0.25
            + axis_micro * 0.35
            + frequency_score * 0.40
        )
        if frequency_warnings:
            warnings.extend(frequency_warnings)
    else:
        # Fallback 2 assi: 35% macro + 65% micro (backward-compat)
        final_score = round(
            axis_macro * 0.35
            + axis_micro * 0.65
        )

    final_score = max(0, min(100, final_score))

    return PlanValidationResult(
        profilo=profile,
        kcal_die=round(kcal_die, 1),
        macro=macro,
        nutrienti=assessments,
        score=final_score,
        warnings=warnings,
        note_metodologiche=(
            "Valutazione basata su LARN 2014 (SINU — IV Revisione) + "
            "Linee Guida CREA 2018. "
            "Score composito 3 assi: macro (25%), micro (35%), frequenze CREA (40%). "
            "Nutrienti con fonte alimentare limitata (es. Vitamina D) hanno "
            "penalita' attenuata — LARN raccomanda supplementazione. "
            "Range macro: Proteine 12-20%, Carboidrati 45-60%, Grassi 20-35%."
        ),
    )
