"""
Piano template statici — profili nutrizionali pre-impostati.

Nessun DB: dati puramente statici, zero migrazioni.
Usati come punto di partenza rapido per nuovi piani alimentari.

8 profili: Uomo/Donna × <30/>30 × Sedentario/Attivo/Sportivo
Macro calcolati secondo linee guida LARN 2014 + ISSN 2017.
"""

from typing import Optional
from pydantic import BaseModel


class PlanTemplateItem(BaseModel):
    id: str
    nome: str
    descrizione: str
    tags: list[str]        # ["uomo", "under30", "sportivo"]
    obiettivo_calorico: int
    proteine_g_target: int
    carboidrati_g_target: int
    grassi_g_target: int
    note_cliniche: str


# ---------------------------------------------------------------------------
# Catalogo statico — 8 profili
# ---------------------------------------------------------------------------

_TEMPLATES: list[PlanTemplateItem] = [
    PlanTemplateItem(
        id="uomo_under30_sedentario",
        nome="Uomo under 30 — Sedentario",
        descrizione="Ufficio/studio, <3h attività fisica a settimana",
        tags=["uomo", "under30", "sedentario"],
        obiettivo_calorico=1900,
        proteine_g_target=140,
        carboidrati_g_target=220,
        grassi_g_target=65,
        note_cliniche=(
            "Profilo sedentario maschile under 30. "
            "Priorità: mantenimento massa muscolare con deficit moderato. "
            "P 1.6g/kg (70kg), C ~45% kcal, G ~30% kcal. "
            "Colazione + pranzo + cena + 1 spuntino pomeriggio."
        ),
    ),
    PlanTemplateItem(
        id="uomo_under30_attivo",
        nome="Uomo under 30 — Attivo",
        descrizione="3-5 sessioni allenamento a settimana",
        tags=["uomo", "under30", "attivo"],
        obiettivo_calorico=2400,
        proteine_g_target=175,
        carboidrati_g_target=290,
        grassi_g_target=80,
        note_cliniche=(
            "Profilo attivo maschile under 30. "
            "P 2.0g/kg (87kg), C ~48% kcal per sostenere le sessioni, G ~30% kcal. "
            "Pre e post-workout consigliati nei giorni di allenamento."
        ),
    ),
    PlanTemplateItem(
        id="uomo_under30_sportivo",
        nome="Uomo under 30 — Sportivo",
        descrizione="Atleta o >5 sessioni intense a settimana",
        tags=["uomo", "under30", "sportivo"],
        obiettivo_calorico=2900,
        proteine_g_target=210,
        carboidrati_g_target=360,
        grassi_g_target=85,
        note_cliniche=(
            "Profilo agonistico maschile under 30. "
            "P 2.2g/kg, C elevati per performance e recupero, G moderati. "
            "6 pasti giornalieri consigliati. Pre/post-workout obbligatori."
        ),
    ),
    PlanTemplateItem(
        id="uomo_over30_mantenimento",
        nome="Uomo over 30 — Mantenimento",
        descrizione="Adulto attivo, obiettivo composizione corporea",
        tags=["uomo", "over30", "attivo"],
        obiettivo_calorico=2200,
        proteine_g_target=170,
        carboidrati_g_target=240,
        grassi_g_target=75,
        note_cliniche=(
            "Profilo maschile over 30 con metabolismo rallentato. "
            "Proteina elevata per prevenire catabolismo muscolare (età-dipendente). "
            "P 2.0g/kg, C moderati, G 30% kcal. Timing post-workout critico."
        ),
    ),
    PlanTemplateItem(
        id="donna_under30_sedentaria",
        nome="Donna under 30 — Sedentaria",
        descrizione="Ufficio/studio, <2h attività fisica a settimana",
        tags=["donna", "under30", "sedentaria"],
        obiettivo_calorico=1500,
        proteine_g_target=110,
        carboidrati_g_target=175,
        grassi_g_target=52,
        note_cliniche=(
            "Profilo sedentario femminile under 30. "
            "Deficit calorico moderato per dimagrimento controllato. "
            "P 1.8g/kg (61kg), C ~46% kcal, G ~31% kcal. "
            "Attenzione al ferro e calcio. Colazione sostanziosa consigliata."
        ),
    ),
    PlanTemplateItem(
        id="donna_under30_attiva",
        nome="Donna under 30 — Attiva",
        descrizione="3-4 sessioni allenamento a settimana",
        tags=["donna", "under30", "attiva"],
        obiettivo_calorico=1900,
        proteine_g_target=140,
        carboidrati_g_target=220,
        grassi_g_target=65,
        note_cliniche=(
            "Profilo attivo femminile under 30. "
            "Bilanciato per supportare l'allenamento e la composizione corporea. "
            "P 2.0g/kg, C ~46% kcal. Pre/post-workout leggeri nei giorni di allenamento. "
            "Monitorare ferro e vitamina D."
        ),
    ),
    PlanTemplateItem(
        id="donna_under30_sportiva",
        nome="Donna under 30 — Sportiva",
        descrizione="Atleta o >5 sessioni intensive a settimana",
        tags=["donna", "under30", "sportiva"],
        obiettivo_calorico=2300,
        proteine_g_target=165,
        carboidrati_g_target=280,
        grassi_g_target=72,
        note_cliniche=(
            "Profilo agonistico femminile under 30. "
            "Apporto calorico adeguato a prevenire RED-S (Relative Energy Deficiency in Sport). "
            "P 2.2g/kg, C elevati, G 28% kcal. 5-6 pasti. "
            "Integrazione ferro e calcio da valutare."
        ),
    ),
    PlanTemplateItem(
        id="donna_over30_mantenimento",
        nome="Donna over 30 — Mantenimento",
        descrizione="Adulta attiva, obiettivo benessere e composizione",
        tags=["donna", "over30", "attiva"],
        obiettivo_calorico=1750,
        proteine_g_target=135,
        carboidrati_g_target=195,
        grassi_g_target=60,
        note_cliniche=(
            "Profilo femminile over 30. Metabolismo basale in calo, "
            "proteina elevata per preservare la massa muscolare. "
            "P 2.0g/kg, C 44% kcal, G 31% kcal. "
            "Particolare attenzione a calcio e vitamina D per salute ossea."
        ),
    ),
]

_TEMPLATE_MAP: dict[str, PlanTemplateItem] = {t.id: t for t in _TEMPLATES}


# ---------------------------------------------------------------------------
# API pubblica del modulo
# ---------------------------------------------------------------------------


def get_all_templates() -> list[PlanTemplateItem]:
    """Ritorna la lista di tutti i template disponibili."""
    return _TEMPLATES


def get_template_by_id(template_id: str) -> Optional[PlanTemplateItem]:
    """Ritorna un template per ID o None se non trovato."""
    return _TEMPLATE_MAP.get(template_id)
