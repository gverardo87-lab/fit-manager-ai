"""
Validatore piano alimentare vs LARN 2014.

Prende un piano alimentare (con pasti e componenti arricchiti) e un profilo
cliente, e produce una valutazione completa di compliance nutrizionale.

Logica:
1. Calcola apporto medio giornaliero di ogni nutriente dal piano
2. Lookup riferimento LARN per profilo (eta', sesso, stato fisiologico)
3. Classifica ogni nutriente: ottimale / sufficiente / carente / eccesso
4. Calcola score complessivo 0-100
5. Genera warnings per criticita'
"""

from typing import Optional

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


def _compute_score(assessments: list[NutrientAssessment]) -> int:
    """
    Score 0-100 composito basato sulla compliance dei nutrienti.

    Pesi:
    - Macro distribution: 30 punti
    - Micronutrienti valutabili: 70 punti distribuiti equamente
    """
    evaluable = [a for a in assessments if a.status != ComplianceStatus.NON_VALUTABILE]
    if not evaluable:
        return 0

    total = 0
    for a in evaluable:
        if a.status == ComplianceStatus.OTTIMALE:
            total += 100
        elif a.status == ComplianceStatus.SUFFICIENTE:
            total += 65
        elif a.status == ComplianceStatus.CARENTE:
            # Proporzionale: se ha il 50% del target, score ~25
            pct = a.percentuale_pri or 0
            total += max(0, min(40, pct * 0.4))
        elif a.status == ComplianceStatus.ECCESSO:
            total += 30  # penalizzazione moderata

    return round(total / len(evaluable))


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
) -> PlanValidationResult:
    """
    Valida un piano alimentare contro i riferimenti LARN 2014.

    Args:
        profile: profilo del cliente (eta', sesso, peso, ecc.)
        daily_nutrients: media giornaliera micronutrienti {campo_db: valore}
        kcal_die: kcal medie giornaliere
        proteine_g_die: grammi proteine /die
        carboidrati_g_die: grammi carboidrati /die
        grassi_g_die: grammi grassi /die

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
            note_metodologiche="LARN 2014 — SINU IV Revisione",
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
        # Senza peso, confronto assoluto con stima peso medio
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
            warnings.append(f"{label} carente: {assessment.apporto_die or 0} {unita} "
                            f"(target: {ref.get('pri') or ref.get('ai')} {unita})")
        elif assessment.status == ComplianceStatus.ECCESSO:
            warnings.append(f"{label} in eccesso: {assessment.apporto_die} {unita} "
                            f"(UL: {ref.get('ul')} {unita})")

    # Sodio: warning OMS se > 2000 mg
    sodio = daily_nutrients.get("sodio_mg")
    if sodio is not None and sodio > 2000:
        warnings.append(f"Sodio elevato ({round(sodio)} mg/die, OMS raccomanda < 2000 mg)")

    # --- Score complessivo ---
    # Macro compliance contribuisce 30 punti
    macro_score = 30
    for val, rng in [
        (prot_pct, macro.proteine_range),
        (carb_pct, macro.carboidrati_range),
        (fat_pct, macro.grassi_range),
    ]:
        if rng[0] <= val <= rng[1]:
            macro_score += 0  # gia' incluso nel base
        else:
            macro_score -= 10

    micro_score = _compute_score(assessments)
    # Peso: 30% macro + 70% micro
    final_score = round(max(0, min(100, macro_score * 0.3 + micro_score * 0.7)))

    return PlanValidationResult(
        profilo=profile,
        kcal_die=round(kcal_die, 1),
        macro=macro,
        nutrienti=assessments,
        score=final_score,
        warnings=warnings,
        note_metodologiche=(
            "Valutazione basata su LARN 2014 (SINU — Societa' Italiana di Nutrizione Umana, "
            "IV Revisione). Livelli di riferimento: AR (Fabbisogno Medio), PRI (Assunzione "
            "Raccomandata), AI (Assunzione Adeguata), UL (Livello Massimo Tollerabile). "
            "Range macro LARN: Proteine 12-20%, Carboidrati 45-60%, Grassi 20-35% dell'energia."
        ),
    )
