"""
Training Science Engine — Modello di carico e intensita'.

Questo modulo gestisce la relazione tra carico (kg), intensita' relativa (% 1RM),
percezione dello sforzo (RPE/RIR) e tonnellaggio (volume-load).

Il modello di carico e' la terza dimensione della programmazione:
  1. Volume = serie x muscolo (volume_model.py)
  2. Distribuzione = pattern biomeccanici (balance_ratios.py)
  3. Intensita' = carico relativo al massimale (QUESTO MODULO)

Principio fondante: "Il volume senza intensita' e' attivita' fisica.
L'intensita' senza volume e' dimostrazione. L'allenamento e' il prodotto
dei due." (Israetel RP 2020, cap. 4)

Metriche implementate:
  - Tonnellaggio (Volume-Load): serie x rep x carico_kg (Haff & Triplett 2016)
  - Intensita' relativa: carico_kg / 1RM (Kraemer & Ratamess 2004)
  - RPE/RIR: autoregolazione basata su RIR (Zourdos et al. 2016)
  - Zone di intensita': classificazione NSCA 5 zone

Fonti:
  - Haff & Triplett — NSCA Essentials of S&C (2016) cap. 15, 21-22
  - Kraemer & Ratamess — "Fundamentals of RT: progression and exercise prescription" (2004)
  - Zourdos et al. — "Novel RT-specific RPE scale measuring RIR" (2016)
  - Helms et al. — "Application of RIR-Based RPE for RT" (2016)
  - Helms et al. — "RPE and velocity-based training" (2017)
  - Israetel — "Scientific Principles of Hypertrophy Training" (RP, 2020) cap. 4-5
  - Bompa & Buzzichelli — "Periodization" (2019) cap. 7
"""

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# TABELLA REP-MAX → %1RM (NSCA 2016, Tabella 15.1)
# ════════════════════════════════════════════════════════════
#
# Relazione tra ripetizioni massimali (RM) e percentuale del
# massimale (1RM). Derivata empiricamente da test su popolazione
# di atleti intermedi-avanzati.
#
# Fonte primaria: Haff & Triplett, NSCA (2016) Table 15.1
# Validazione: Brzycki (1993), Epley (1985), Mayhew et al. (1995)
#
# Questa tabella e' la BASE per tutte le conversioni.
# L'aggiustamento per RIR si applica SOPRA questi valori.

NSCA_REP_MAX_PCT: dict[int, float] = {
    1:  1.00,
    2:  0.95,
    3:  0.93,
    4:  0.90,
    5:  0.87,
    6:  0.85,
    7:  0.83,
    8:  0.80,
    9:  0.77,
    10: 0.75,
    11: 0.72,
    12: 0.70,
    15: 0.65,
    20: 0.60,
    25: 0.55,
}


# ════════════════════════════════════════════════════════════
# RPE/RIR → AGGIUSTAMENTO %1RM (Zourdos et al. 2016)
# ════════════════════════════════════════════════════════════
#
# La scala RPE basata su RIR (Repetitions In Reserve) permette
# l'autoregolazione dell'intensita'. Ogni RIR aggiuntivo
# corrisponde a ~2.5-3% in meno rispetto al massimale per
# quel numero di ripetizioni.
#
# Fonte: Zourdos et al. (2016) — J Strength Cond Res
# Validazione: Helms et al. (2016, 2017)
#
# La relazione e' approssimata come lineare: -3% per ogni RIR
# (media validata per range 1-5 RIR su esercizi compound).

PCT_DECREMENT_PER_RIR = 0.025
"""
Decremento %1RM per ogni RIR aggiuntivo.

Zourdos 2016: ~2.5% per RIR (range osservato 2-3%).
Helms 2017: validazione su squat, panca, stacco.
Usiamo 2.5% (conservativo, reduce overestimation risk).
"""


# ════════════════════════════════════════════════════════════
# ZONE DI INTENSITA' (NSCA 2016, cap. 15)
# ════════════════════════════════════════════════════════════
#
# Classificazione standard dell'intensita' di allenamento.
# Ogni zona ha effetti fisiologici distinti.

INTENSITY_ZONES: list[tuple[float, float, str, str]] = [
    # (min_pct, max_pct, nome_zona, effetto_fisiologico)
    (0.90, 1.00, "massimale", "Forza massimale, reclutamento neurale completo (NSCA 2016)"),
    (0.80, 0.90, "sub_massimale", "Forza-ipertrofia, alto stress meccanico (Schoenfeld 2010)"),
    (0.67, 0.80, "ipertrofia", "Volume ottimale per ipertrofia, tensione meccanica (Schoenfeld 2017)"),
    (0.50, 0.67, "resistenza", "Resistenza muscolare, adattamento metabolico (ACSM 2009)"),
    (0.00, 0.50, "attivazione", "Riscaldamento, apprendimento motorio (NSCA 2016)"),
]


# ════════════════════════════════════════════════════════════
# PRESCRIZIONE INTENSITA' PER FASE MESOCICLO
# ════════════════════════════════════════════════════════════
#
# Come l'intensita' varia nelle fasi del mesociclo.
# Principio chiave: "volume e intensita' non si muovono sempre
# nella stessa direzione" (Israetel RP 2020).
#
# - Accumulazione: intensita' moderata, volume crescente
# - Intensificazione: intensita' cresce, volume stabile
# - Overreaching: intensita' alta, volume al picco
# - Deload: intensita' MANTENUTA, volume ridotto
#
# "Non ridurre mai volume E intensita' simultaneamente.
# Il deload riduce il volume mantenendo l'intensita' per
# preservare gli adattamenti neurali." (Helms 2019, cap. 12)

FASE_INTENSITA_RPE: dict[str, tuple[float, float]] = {
    # fase: (rpe_min, rpe_max)
    "accumulazione":    (6.0, 7.5),
    "intensificazione": (7.0, 8.5),
    "overreaching":     (8.0, 9.5),
    "deload":           (5.0, 6.5),
}
"""
Range RPE per fase del mesociclo.

Accumulazione: RPE 6-7.5 (3-4 RIR) — focus su tecnica e volume
  Fonte: Helms 2019, Zourdos 2016

Intensificazione: RPE 7-8.5 (1.5-3 RIR) — stimolo progressivo
  Fonte: Israetel RP 2020 cap. 9

Overreaching: RPE 8-9.5 (0.5-2 RIR) — picco prima del deload
  Fonte: Israetel RP 2020 cap. 9, Bompa 2019

Deload: RPE 5-6.5 (3.5-5 RIR) — recovery attivo
  Fonte: Helms 2019 cap. 12 "maintain intensity reduce volume"
  NOTA: RPE basso ma carico in kg NON scende proporzionalmente
  perche' le serie sono dimezzate → meno fatica cumulativa
"""


FASE_INTENSITA_PCT: dict[str, tuple[float, float]] = {
    # fase: (pct_1rm_min, pct_1rm_max) — reference per obiettivo ipertrofia
    "accumulazione":    (0.60, 0.72),
    "intensificazione": (0.70, 0.80),
    "overreaching":     (0.75, 0.85),
    "deload":           (0.55, 0.65),
}
"""
Range %1RM indicativo per fase (obiettivo ipertrofia, rep range 6-12).

Questi sono RANGE DI RIFERIMENTO. L'intensita' effettiva dipende
dal numero di ripetizioni e dal livello (see get_intensity_for_reps).

Fonte: NSCA 2016, Israetel RP 2020, Schoenfeld 2017.
"""


# ════════════════════════════════════════════════════════════
# MODELLI OUTPUT
# ════════════════════════════════════════════════════════════


class IntensityPrescription(BaseModel):
    """
    Prescrizione di intensita' per una settimana del mesociclo.

    Combina RPE/RIR target con %1RM di riferimento.
    Il trainer usa RPE come guida primaria (autoregolazione),
    %1RM come reference per la programmazione.
    """

    rpe_min: float = Field(ge=1.0, le=10.0, description="RPE minimo della settimana")
    rpe_max: float = Field(ge=1.0, le=10.0, description="RPE massimo della settimana")
    rir_min: float = Field(ge=0.0, description="RIR minimo (derivato da RPE max)")
    rir_max: float = Field(ge=0.0, description="RIR massimo (derivato da RPE min)")
    pct_1rm_min: float = Field(ge=0.0, le=1.0, description="%1RM minimo di riferimento")
    pct_1rm_max: float = Field(ge=0.0, le=1.0, description="%1RM massimo di riferimento")
    zona: str = Field(description="Zona di intensita' prevalente (NSCA 2016)")
    nota: str = Field(default="", description="Indicazione fisiologica")


class TonnellaggioSlot(BaseModel):
    """Tonnellaggio calcolato per un singolo slot della sessione."""

    pattern: str = Field(description="Pattern di movimento")
    serie: int
    rep_medie: float = Field(description="Media rep range (rep_min+rep_max)/2")
    carico_kg: float = Field(description="Carico in kg")
    tonnellaggio: float = Field(
        description="serie × rep_medie × carico_kg (Haff & Triplett 2016)"
    )
    intensita_relativa: float | None = Field(
        default=None,
        description="%1RM se 1RM noto (carico_kg / 1RM)",
    )
    zona_intensita: str | None = Field(
        default=None,
        description="Zona NSCA (massimale/sub_massimale/ipertrofia/resistenza/attivazione)",
    )


class AnalisiTonnellaggio(BaseModel):
    """
    Analisi volume-load di un piano con carichi assegnati.

    Il tonnellaggio (Volume-Load) e' la metrica gold standard per
    quantificare il carico di allenamento totale.
    Fonte: Haff & Triplett (NSCA 2016), McBride et al. (2009).
    """

    tonnellaggio_totale: float = Field(description="Σ(serie × rep × kg) settimanale")
    tonnellaggio_per_sessione: dict[str, float] = Field(
        description="Tonnellaggio per nome sessione"
    )
    intensita_media_ponderata: float | None = Field(
        default=None,
        description="Media %1RM pesata per serie (se 1RM disponibili)",
    )
    slot_detail: list[TonnellaggioSlot] = Field(
        default_factory=list,
        description="Dettaglio per ogni slot con carico",
    )
    zona_prevalente: str | None = Field(
        default=None,
        description="Zona NSCA prevalente (per serie)",
    )
    fonte: str = Field(
        default="Haff & Triplett (NSCA 2016) cap. 15; McBride et al. (2009)",
    )


# ════════════════════════════════════════════════════════════
# FUNZIONI — Conversioni e calcoli
# ════════════════════════════════════════════════════════════


def rpe_to_rir(rpe: float) -> float:
    """
    Converti RPE in RIR (Repetitions In Reserve).

    Formula: RIR = 10 - RPE
    Fonte: Zourdos et al. (2016) — definizione originale della scala.
    Validazione: Helms et al. (2016).
    """
    return max(0.0, 10.0 - rpe)


def rir_to_rpe(rir: float) -> float:
    """
    Converti RIR in RPE.

    Formula: RPE = 10 - RIR
    Fonte: Zourdos et al. (2016).
    """
    return min(10.0, max(1.0, 10.0 - rir))


def get_intensity_for_reps(reps: int, rir: float = 0.0) -> float:
    """
    Calcola l'intensita' relativa (%1RM) per un dato numero di
    ripetizioni e RIR.

    Algoritmo:
      1. Lookup nella tabella NSCA per le rep massimali (RIR=0)
      2. Interpolazione lineare se le rep non sono in tabella
      3. Aggiustamento per RIR: -2.5% per ogni RIR aggiuntivo

    Esempio: 8 rep con 2 RIR
      → NSCA: 8RM = 80% 1RM
      → RIR adjustment: 80% - (2 × 2.5%) = 75% 1RM
      → Il carico target e' 75% del massimale

    Fonti:
      - NSCA 2016 Table 15.1 (rep-max %)
      - Zourdos 2016 (RIR adjustment)
      - Helms 2017 (validation)
    """
    # Clamp reps
    reps = max(1, min(25, reps))

    # Lookup diretto se in tabella
    if reps in NSCA_REP_MAX_PCT:
        base_pct = NSCA_REP_MAX_PCT[reps]
    else:
        # Interpolazione lineare tra i punti della tabella
        sorted_reps = sorted(NSCA_REP_MAX_PCT.keys())
        lower = max(r for r in sorted_reps if r <= reps)
        upper = min(r for r in sorted_reps if r >= reps)
        if lower == upper:
            base_pct = NSCA_REP_MAX_PCT[lower]
        else:
            t = (reps - lower) / (upper - lower)
            base_pct = NSCA_REP_MAX_PCT[lower] + t * (
                NSCA_REP_MAX_PCT[upper] - NSCA_REP_MAX_PCT[lower]
            )

    # Aggiustamento RIR (Zourdos 2016)
    adjusted_pct = base_pct - (rir * PCT_DECREMENT_PER_RIR)
    return max(0.30, round(adjusted_pct, 4))


def classify_intensity_zone(pct_1rm: float) -> tuple[str, str]:
    """
    Classifica una %1RM nella zona di intensita' NSCA corrispondente.

    Ritorna: (nome_zona, descrizione_effetto_fisiologico)
    Fonte: NSCA 2016 cap. 15.
    """
    for min_pct, max_pct, nome, effetto in INTENSITY_ZONES:
        if min_pct <= pct_1rm <= max_pct:
            return (nome, effetto)
    return ("attivazione", INTENSITY_ZONES[-1][3])


def compute_tonnage(
    serie: int,
    rep_min: int,
    rep_max: int,
    carico_kg: float,
) -> float:
    """
    Calcola il tonnellaggio (Volume-Load) per un singolo slot.

    Formula: tonnellaggio = serie × rep_medie × carico_kg
    Dove: rep_medie = (rep_min + rep_max) / 2

    Fonte: Haff & Triplett (NSCA 2016) cap. 15:
    "Volume-load is calculated as the total weight lifted
    (sets × repetitions × load) and provides a more complete
    picture of training stress than sets alone."

    McBride et al. (2009): validazione del tonnellaggio come
    metrica primaria per la quantificazione del carico.
    """
    if carico_kg <= 0 or serie <= 0:
        return 0.0
    rep_medie = (rep_min + rep_max) / 2
    return round(serie * rep_medie * carico_kg, 1)


def get_intensity_prescription(fase: str) -> IntensityPrescription:
    """
    Genera la prescrizione di intensita' per una fase del mesociclo.

    Combina:
    - RPE target (autoregolazione, Zourdos 2016)
    - %1RM di riferimento (programmazione, NSCA 2016)
    - Zona NSCA prevalente
    - Nota fisiologica per il trainer

    Il trainer usa l'RPE come guida primaria perche':
    1. Si adatta alla readiness giornaliera (autoregolazione)
    2. Non richiede test 1RM (safety)
    3. E' validato dalla letteratura (Zourdos 2016, Helms 2017)

    La %1RM e' un reference per la pianificazione a lungo termine.
    """
    rpe_range = FASE_INTENSITA_RPE.get(fase, (6.0, 7.5))
    pct_range = FASE_INTENSITA_PCT.get(fase, (0.60, 0.72))

    rpe_min, rpe_max = rpe_range
    pct_min, pct_max = pct_range

    rir_min = rpe_to_rir(rpe_max)  # RPE alto → RIR basso
    rir_max = rpe_to_rir(rpe_min)  # RPE basso → RIR alto

    # Zona prevalente basata sulla media del range %1RM
    avg_pct = (pct_min + pct_max) / 2
    zona, _ = classify_intensity_zone(avg_pct)

    note_map = {
        "accumulazione": (
            "Intensita' moderata. Focus su tecnica e connessione mente-muscolo. "
            "Il carico permette di completare tutte le serie con riserva (3-4 RIR). "
            "Fonte: Helms 2019, Zourdos 2016."
        ),
        "intensificazione": (
            "Intensita' crescente. Le serie diventano piu' impegnative (1.5-3 RIR). "
            "Il carico si avvicina al range ipertrofico alto. "
            "Fonte: Israetel RP 2020 cap. 9."
        ),
        "overreaching": (
            "Intensita' alta. Le serie finiscono vicino al cedimento (0.5-2 RIR). "
            "Settimana di massimo stimolo — aspettarsi fatica accumulata. "
            "Fonte: Israetel RP 2020 cap. 9, Bompa 2019."
        ),
        "deload": (
            "Carico MANTENUTO ma volume (serie) ridotto a ~50%. "
            "L'intensita' preserva gli adattamenti neurali durante il recupero. "
            "Fonte: Helms 2019 — 'maintain load, reduce volume, never both'."
        ),
    }

    return IntensityPrescription(
        rpe_min=rpe_min,
        rpe_max=rpe_max,
        rir_min=rir_min,
        rir_max=rir_max,
        pct_1rm_min=pct_min,
        pct_1rm_max=pct_max,
        zona=zona,
        nota=note_map.get(fase, ""),
    )
