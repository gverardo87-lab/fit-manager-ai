"""
Validatore frequenze alimentari vs Linee Guida CREA 2018.

Conta le porzioni standard LARN consumate per sotto-gruppo in un piano
settimanale e confronta con le frequenze raccomandate.

Pipeline:
1. Per ogni giorno × pasto × componente: identifica sotto-gruppo LARN
2. Conta porzioni standard (quantita_g / porzione_standard_g)
3. Confronta vs LARN_WEEKLY_FREQUENCIES
4. Genera assessment per sotto-gruppo + warning specifici

Fonte: CREA 2018, Linee Guida per una Sana Alimentazione, Dir. 1-13.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from api.services.nutrition_science.larn_portions import (
    LARN_STANDARD_PORTIONS,
    LARN_WEEKLY_FREQUENCIES,
    PROTEIN_SUB_FREQUENCIES,
    ROLE_TO_LARN_PORTION,
)


class FrequencyStatus(str, Enum):
    """Stato compliance di una frequenza."""
    OTTIMALE = "ottimale"       # entro il range CREA
    BASSO = "basso"             # sotto il minimo
    ALTO = "alto"               # sopra il massimo
    NON_VALUTABILE = "non_valutabile"


@dataclass
class FrequencyAssessment:
    """Valutazione frequenza per un sotto-gruppo."""
    sotto_gruppo: str
    label: str
    porzioni_contate: float
    range_min: int
    range_max: int
    status: FrequencyStatus
    nota: Optional[str] = None


@dataclass
class FrequencyValidationResult:
    """Risultato completo della validazione frequenze."""
    assessments: list[FrequencyAssessment] = field(default_factory=list)
    protein_assessments: list[FrequencyAssessment] = field(default_factory=list)
    score: int = 0              # 0-100
    warnings: list[str] = field(default_factory=list)


def _count_portions_by_role(
    weekly_meals: list[dict],
) -> dict[str, float]:
    """
    Conta porzioni standard per sotto-gruppo LARN da un piano settimanale.

    Args:
        weekly_meals: lista di dict con:
            - ruolo: str (ruolo da meal_archetypes)
            - quantita_g: float

    Returns:
        {sotto_gruppo_larn: n_porzioni}
    """
    counts: dict[str, float] = {}

    for item in weekly_meals:
        ruolo = item.get("ruolo", "")
        grammi = item.get("quantita_g", 0)

        sotto_gruppo = ROLE_TO_LARN_PORTION.get(ruolo)
        if not sotto_gruppo:
            continue

        porzione_std = LARN_STANDARD_PORTIONS.get(sotto_gruppo)
        if not porzione_std or porzione_std <= 0:
            continue

        n_porzioni = grammi / porzione_std
        counts[sotto_gruppo] = counts.get(sotto_gruppo, 0) + n_porzioni

    return counts


def _count_protein_sub_frequencies(
    weekly_meals: list[dict],
) -> dict[str, float]:
    """
    Conta occorrenze per sotto-categoria proteica.

    Conta il numero di PASTI (non porzioni) in cui appare ogni tipo proteico.
    Es. pesce a pranzo = 1 occorrenza, pesce a pranzo + cena = 2.
    """
    # Raggruppa per (giorno, pasto) per contare pasti, non grammi
    meal_proteins: dict[str, set[str]] = {}

    for item in weekly_meals:
        ruolo = item.get("ruolo", "")
        key = f"{item.get('giorno', 0)}_{item.get('tipo_pasto', '')}"

        for sub_name, sub_def in PROTEIN_SUB_FREQUENCIES.items():
            if ruolo in sub_def["ruoli"]:
                if sub_name not in meal_proteins:
                    meal_proteins[sub_name] = set()
                meal_proteins[sub_name].add(key)

    return {name: len(meals) for name, meals in meal_proteins.items()}


def validate_frequencies(
    weekly_meals: list[dict],
) -> FrequencyValidationResult:
    """
    Valida le frequenze di un piano settimanale vs CREA 2018.

    Args:
        weekly_meals: lista di dict per ogni componente del piano:
            {ruolo, quantita_g, giorno (1-7), tipo_pasto}

    Returns:
        FrequencyValidationResult con assessment e score 0-100
    """
    warnings: list[str] = []

    # --- Frequenze per sotto-gruppo LARN ---
    portion_counts = _count_portions_by_role(weekly_meals)
    assessments: list[FrequencyAssessment] = []

    for sotto_gruppo, (freq_min, freq_max) in LARN_WEEKLY_FREQUENCIES.items():
        contate = round(portion_counts.get(sotto_gruppo, 0), 1)

        # Label leggibile
        label = sotto_gruppo.replace("_", " ").title()

        if contate < freq_min * 0.7:  # sotto il 70% del minimo
            status = FrequencyStatus.BASSO
            nota = f"{contate} porzioni/sett, CREA raccomanda almeno {freq_min}"
            warnings.append(f"{label}: {nota}")
        elif contate > freq_max * 1.3:  # sopra il 130% del massimo
            status = FrequencyStatus.ALTO
            nota = f"{contate} porzioni/sett, CREA raccomanda max {freq_max}"
            warnings.append(f"{label}: {nota}")
        else:
            status = FrequencyStatus.OTTIMALE
            nota = None

        assessments.append(FrequencyAssessment(
            sotto_gruppo=sotto_gruppo,
            label=label,
            porzioni_contate=contate,
            range_min=freq_min,
            range_max=freq_max,
            status=status,
            nota=nota,
        ))

    # --- Sub-frequenze proteine ---
    protein_counts = _count_protein_sub_frequencies(weekly_meals)
    protein_assessments: list[FrequencyAssessment] = []

    for sub_name, sub_def in PROTEIN_SUB_FREQUENCIES.items():
        contate = protein_counts.get(sub_name, 0)
        freq_min = sub_def["min"]
        freq_max = sub_def["max"]
        label = sub_def["label"]

        if contate < freq_min:
            status = FrequencyStatus.BASSO
            nota = f"{label}: {contate}x/sett, CREA raccomanda almeno {freq_min}x"
            warnings.append(nota)
        elif contate > freq_max:
            status = FrequencyStatus.ALTO
            nota = f"{label}: {contate}x/sett, CREA raccomanda max {freq_max}x"
            warnings.append(nota)
        else:
            status = FrequencyStatus.OTTIMALE
            nota = None

        protein_assessments.append(FrequencyAssessment(
            sotto_gruppo=sub_name,
            label=label,
            porzioni_contate=contate,
            range_min=freq_min,
            range_max=freq_max,
            status=status,
            nota=nota,
        ))

    # --- Score 0-100 ---
    all_checks = assessments + protein_assessments
    evaluable = [a for a in all_checks if a.status != FrequencyStatus.NON_VALUTABILE]
    if not evaluable:
        score = 0
    else:
        total = 0
        for a in evaluable:
            if a.status == FrequencyStatus.OTTIMALE:
                total += 100
            elif a.status == FrequencyStatus.BASSO:
                # Proporzionale: quanto manca al minimo
                if a.range_min > 0:
                    ratio = a.porzioni_contate / a.range_min
                    total += max(0, min(60, ratio * 60))
                else:
                    total += 50
            elif a.status == FrequencyStatus.ALTO:
                # Eccesso moderato: meno grave di carenza
                if a.range_max > 0:
                    overshoot = a.porzioni_contate / a.range_max
                    total += max(30, 100 - (overshoot - 1) * 50)
                else:
                    total += 40
        score = round(total / len(evaluable))

    return FrequencyValidationResult(
        assessments=assessments,
        protein_assessments=protein_assessments,
        score=min(100, max(0, score)),
        warnings=warnings,
    )
