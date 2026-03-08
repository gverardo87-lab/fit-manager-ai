"""
Training Science Engine — Periodizzazione del mesociclo.

La periodizzazione organizza il volume di allenamento nel TEMPO.
Un piano settimanale (build_plan) definisce la STRUTTURA — questo modulo
definisce come il volume VARIA settimana per settimana all'interno di un
mesociclo (tipicamente 4-6 settimane).

Modello: Periodizzazione Ondulata a Blocchi (Block Periodization)
basata sul modello Israetel/Renaissance Periodization:

  Settimana 1 → Volume base (MAV_min) — adattamento strutturale
  Settimana 2 → Volume crescente (interpolazione lineare)
  ...
  Settimana N-1 → Volume picco (avvicinamento MRV) — overreaching funzionale
  Settimana N → DELOAD — volume ridotto a ~MEV (recupero + supercompensazione)

Il fattore di progressione e' DETERMINISTICO: ogni settimana ha un moltiplicatore
preciso calcolato per interpolazione lineare tra la base e il picco.

Principi fondanti:
  1. Il volume DEVE crescere nel tempo per continuare a stimolare (progressive overload)
  2. Il volume NON puo' crescere indefinitamente (MRV = tetto fisiologico)
  3. Il deload e' NECESSARIO per la supercompensazione (Bompa 2019, Israetel 2020)
  4. La durata del mesociclo dipende dal livello (principianti recuperano prima)

Fonti:
  - Israetel — "Scientific Principles of Hypertrophy Training" (2020) cap. 8-9
  - Bompa & Buzzichelli — "Periodization: Theory and Methodology" (6th ed, 2019)
  - Schoenfeld — "Dose-response relationship for RT volume" (2017)
  - Zourdos et al. — "DUP vs traditional periodization" (2016)
  - NSCA — "Essentials of Strength Training" (2016) cap. 21-22
  - Helms — "The Muscle and Strength Pyramid: Training" (2019)
"""

from .types import (
    Livello,
    TemplatePiano,
    SlotSessione,
    TemplateSessione,
)
from .load_model import IntensityPrescription, get_intensity_prescription
from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# FASI DEL MESOCICLO — Nomenclatura standard
# ════════════════════════════════════════════════════════════
#
# Ogni fase ha un obiettivo fisiologico specifico.
# La sequenza e' fissa e validata dalla letteratura (Israetel 2020).

FASE_ACCUMULAZIONE = "accumulazione"
FASE_INTENSIFICAZIONE = "intensificazione"
FASE_OVERREACHING = "overreaching"
FASE_DELOAD = "deload"


# ════════════════════════════════════════════════════════════
# DURATA MESOCICLO — Per livello di esperienza
# ════════════════════════════════════════════════════════════
#
# Principianti: mesociclo breve (3-4 sett + deload).
#   Rispondono a meno stimolo e faticano di piu' (NSCA 2016).
# Intermedi: mesociclo medio (4-5 sett + deload).
# Avanzati: mesociclo lungo (5-6 sett + deload).
#   Servono piu' settimane per accumulare stimolo sufficiente.
#
# Formato: (settimane_di_carico, include_deload)
# Il deload e' SEMPRE l'ultima settimana.

DURATA_MESOCICLO: dict[Livello, int] = {
    Livello.PRINCIPIANTE: 4,   # 3 sett carico + 1 deload
    Livello.INTERMEDIO: 5,     # 4 sett carico + 1 deload
    Livello.AVANZATO: 6,       # 5 sett carico + 1 deload
}


# ════════════════════════════════════════════════════════════
# FATTORE VOLUME SETTIMANALE
# ════════════════════════════════════════════════════════════
#
# Il volume di ogni settimana e' espresso come moltiplicatore
# rispetto al piano base (output di build_plan).
#
# Il piano base e' calibrato su MAV — il range ottimale.
# La progressione scala le serie linearmente:
#
#   Settimana 1: fattore_base (partenza conservativa)
#   ...
#   Settimana N-1: fattore_picco (avvicinamento MRV)
#   Settimana N: fattore_deload (recupero attivo)
#
# I fattori sono differenziati per livello perche':
# - Principianti partono da piu' basso (meno volume tollerato)
# - Avanzati hanno un range di progressione piu' ampio
#
# Fonti:
#   Israetel RP 2020: volume progression 5-20% per settimana
#   Bompa 2019: supercompensation curve validation
#   Helms 2019: deload at 40-60% of peak volume

FATTORI_VOLUME: dict[Livello, dict[str, float]] = {
    Livello.PRINCIPIANTE: {
        "base": 0.85,      # Settimana 1: partenza bassa (sotto MAV)
        "picco": 1.10,     # Settimana N-1: leggero overreaching
        "deload": 0.50,    # Settimana N: 50% del base (Helms 2019)
    },
    Livello.INTERMEDIO: {
        "base": 0.90,      # Settimana 1: partenza moderata
        "picco": 1.20,     # Settimana N-1: overreaching moderato
        "deload": 0.50,    # Settimana N: 50% del base
    },
    Livello.AVANZATO: {
        "base": 0.90,      # Settimana 1: partenza moderata
        "picco": 1.30,     # Settimana N-1: overreaching significativo
        "deload": 0.50,    # Settimana N: 50% del base
    },
}


# ════════════════════════════════════════════════════════════
# MODELLI OUTPUT
# ════════════════════════════════════════════════════════════


class SettimanaConfig(BaseModel):
    """
    Configurazione di una settimana nel mesociclo.

    Combina la progressione VOLUME (fattore_volume, serie scalate)
    con la progressione INTENSITA' (RPE target, %1RM di riferimento).

    Principio: volume e intensita' non si muovono sempre nella stessa
    direzione. Il deload riduce il volume mantenendo l'intensita'.
    Fonte: Israetel RP 2020, Helms 2019.
    """

    numero: int = Field(ge=1, description="Numero settimana (1-based)")
    fase: str = Field(description="accumulazione | intensificazione | overreaching | deload")
    fattore_volume: float = Field(
        description="Moltiplicatore serie rispetto al piano base (1.0 = piano base invariato)"
    )
    intensita: IntensityPrescription = Field(
        description=(
            "Prescrizione di intensita' per la settimana: RPE/RIR target + "
            "%1RM di riferimento + zona NSCA. Fonte: Zourdos 2016, NSCA 2016."
        ),
    )
    note: str = Field(default="", description="Nota descrittiva della fase")


class Mesociclo(BaseModel):
    """
    Mesociclo completo: piano base + configurazione per ogni settimana.

    Il piano base (TemplatePiano) definisce la struttura settimanale.
    Le SettimanaConfig definiscono come il volume varia nel tempo.
    I piani settimanali (piani_settimanali) sono i piani effettivi
    con le serie gia' scalate per ogni settimana.
    """

    piano_base: TemplatePiano
    settimane: list[SettimanaConfig]
    piani_settimanali: list[TemplatePiano]
    durata_settimane: int = Field(description="Numero totale di settimane")


# ════════════════════════════════════════════════════════════
# CALCOLO FATTORI — Interpolazione lineare
# ════════════════════════════════════════════════════════════


def _compute_weekly_factors(livello: Livello) -> list[float]:
    """
    Calcola il fattore di volume per ogni settimana del mesociclo.

    Interpolazione lineare tra base e picco per le settimane di carico,
    poi deload fisso per l'ultima settimana.

    Esempio (intermedio, 5 settimane):
      Sett 1: 0.90 (base)
      Sett 2: 1.00 (interpolazione)
      Sett 3: 1.10 (interpolazione)
      Sett 4: 1.20 (picco)
      Sett 5: 0.50 (deload)

    La progressione e' lineare perche':
    - E' deterministica e prevedibile
    - E' validata dalla letteratura (Israetel 2020, Bompa 2019)
    - Permette al trainer di capire esattamente il carico atteso
    """
    durata = DURATA_MESOCICLO[livello]
    fattori = FATTORI_VOLUME[livello]

    settimane_carico = durata - 1  # Ultima settimana = deload
    factors: list[float] = []

    for i in range(settimane_carico):
        if settimane_carico == 1:
            # Solo 1 settimana di carico → usa il base
            f = fattori["base"]
        else:
            # Interpolazione lineare: base → picco
            t = i / (settimane_carico - 1)
            f = fattori["base"] + t * (fattori["picco"] - fattori["base"])
        factors.append(round(f, 3))

    # Ultima settimana: deload
    factors.append(fattori["deload"])

    return factors


def _classify_phase(
    week_index: int,
    total_weeks: int,
    factor: float,
    fattori: dict[str, float],
) -> str:
    """
    Classifica la fase della settimana in base alla posizione e al fattore.

    La classificazione e' deterministica:
    - Ultima settimana → deload (sempre)
    - Fattore <= base + 33% del range → accumulazione
    - Fattore <= base + 66% del range → intensificazione
    - Fattore > base + 66% del range → overreaching
    """
    if week_index == total_weeks - 1:
        return FASE_DELOAD

    volume_range = fattori["picco"] - fattori["base"]
    if volume_range <= 0:
        return FASE_ACCUMULAZIONE

    progress = (factor - fattori["base"]) / volume_range
    if progress <= 0.33:
        return FASE_ACCUMULAZIONE
    if progress <= 0.66:
        return FASE_INTENSIFICAZIONE
    return FASE_OVERREACHING


# ════════════════════════════════════════════════════════════
# GENERAZIONE NOTE — Descrizioni fisiologiche per fase
# ════════════════════════════════════════════════════════════

_NOTE_FASE: dict[str, str] = {
    FASE_ACCUMULAZIONE: (
        "Volume base — adattamento strutturale. "
        "Focus su tecnica e connessione mente-muscolo. "
        "Fonte: Israetel RP 2020 cap. 8."
    ),
    FASE_INTENSIFICAZIONE: (
        "Volume crescente — stimolo progressivo. "
        "Incremento graduale delle serie per forzare l'adattamento. "
        "Fonte: Bompa 2019, progressive overload."
    ),
    FASE_OVERREACHING: (
        "Volume vicino a MRV — overreaching funzionale. "
        "Settimana di picco: massimo stimolo prima del deload. "
        "Aspettarsi fatica accumulata. Fonte: Israetel RP 2020 cap. 9."
    ),
    FASE_DELOAD: (
        "Volume ridotto a ~50% — recupero attivo e supercompensazione. "
        "Mantenere intensita' (carico), ridurre solo il volume (serie). "
        "Fonte: Helms 2019, Israetel RP 2020."
    ),
}


# ════════════════════════════════════════════════════════════
# SCALATURA PIANO — Applica fattore volume a un piano
# ════════════════════════════════════════════════════════════


def _scale_plan(piano: TemplatePiano, fattore: float) -> TemplatePiano:
    """
    Crea una copia del piano con le serie scalate per il fattore.

    Il fattore viene applicato alle serie di ogni slot.
    Regole di arrotondamento:
    - Le serie sono arrotondate all'intero piu' vicino
    - Minimo 1 serie per slot (anche in deload, per mantenere il pattern)
    - L'intensita' (rep range, riposo) NON cambia — solo il volume

    Fonte: Israetel RP 2020 — "durante il deload, mantieni il carico
    e riduci il volume. Mai ridurre entrambi simultaneamente."
    """
    scaled_sessioni: list[TemplateSessione] = []

    for sessione in piano.sessioni:
        scaled_slots: list[SlotSessione] = []
        for slot in sessione.slots:
            scaled_serie = max(1, round(slot.serie * fattore))
            scaled_slots.append(SlotSessione(
                pattern=slot.pattern,
                priorita=slot.priorita,
                serie=scaled_serie,
                rep_min=slot.rep_min,
                rep_max=slot.rep_max,
                riposo_sec=slot.riposo_sec,
                muscolo_target=slot.muscolo_target,
                note=slot.note,
            ))
        scaled_sessioni.append(TemplateSessione(
            nome=sessione.nome,
            ruolo=sessione.ruolo,
            focus=sessione.focus,
            slots=scaled_slots,
        ))

    return TemplatePiano(
        frequenza=piano.frequenza,
        obiettivo=piano.obiettivo,
        livello=piano.livello,
        tipo_split=piano.tipo_split,
        sessioni=scaled_sessioni,
        note_generazione=piano.note_generazione.copy(),
    )


# ════════════════════════════════════════════════════════════
# API PUBBLICA — Generazione mesociclo
# ════════════════════════════════════════════════════════════


def get_mesocycle_duration(livello: Livello) -> int:
    """
    Ritorna la durata del mesociclo in settimane per il livello.

    Fonte: Israetel RP 2020 — principianti 4 sett, intermedi 5, avanzati 6.
    """
    return DURATA_MESOCICLO[livello]


def get_weekly_config(livello: Livello) -> list[SettimanaConfig]:
    """
    Ritorna la configurazione di ogni settimana del mesociclo.

    Output deterministico: dato un livello, le settimane e i fattori
    sono sempre gli stessi. Utile per preview/planning.
    """
    factors = _compute_weekly_factors(livello)
    durata = DURATA_MESOCICLO[livello]
    fattori = FATTORI_VOLUME[livello]

    configs: list[SettimanaConfig] = []
    for i, factor in enumerate(factors):
        fase = _classify_phase(i, durata, factor, fattori)
        configs.append(SettimanaConfig(
            numero=i + 1,
            fase=fase,
            fattore_volume=factor,
            intensita=get_intensity_prescription(fase),
            note=_NOTE_FASE[fase],
        ))

    return configs


def build_mesocycle(piano_base: TemplatePiano) -> Mesociclo:
    """
    Genera un mesociclo completo da un piano settimanale base.

    Il piano base (output di build_plan) definisce la struttura.
    Questo modulo la modula nel tempo creando una progressione
    di volume scientificamente calibrata.

    Input: TemplatePiano (da build_plan)
    Output: Mesociclo con N settimane, ognuna con il piano scalato

    Algoritmo:
      1. Determina la durata del mesociclo dal livello
      2. Calcola i fattori di volume per ogni settimana (interpolazione lineare)
      3. Classifica ogni settimana nella fase corretta
      4. Scala il piano base per ogni settimana (solo serie, non intensita')

    Esempio (intermedio, ipertrofia, 4x/sett):
      Sett 1: 0.90x → 3 serie base diventano 3, 4 serie diventano 4
      Sett 2: 1.00x → piano invariato
      Sett 3: 1.10x → 3 serie diventano 3, 4 serie diventano 4
      Sett 4: 1.20x → 3 serie diventano 4, 4 serie diventano 5
      Sett 5: 0.50x → 3 serie diventano 2, 4 serie diventano 2

    Fonti:
      - Israetel RP 2020 cap. 8-9 (volume progression model)
      - Bompa 2019 (supercompensation theory)
      - Helms 2019 (deload protocol)
    """
    livello = piano_base.livello
    settimane = get_weekly_config(livello)

    piani: list[TemplatePiano] = []
    for config in settimane:
        piano_settimana = _scale_plan(piano_base, config.fattore_volume)
        piani.append(piano_settimana)

    return Mesociclo(
        piano_base=piano_base,
        settimane=settimane,
        piani_settimanali=piani,
        durata_settimane=len(settimane),
    )
