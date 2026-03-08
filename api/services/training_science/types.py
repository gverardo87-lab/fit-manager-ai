"""
Training Science Engine — Tipi fondamentali.

Ogni tipo riflette un concetto della programmazione dell'allenamento.
Nomi in italiano (dominio utente), docstring con fonte scientifica.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# ENUM — Vocabolario del dominio
# ════════════════════════════════════════════════════════════


class Obiettivo(str, Enum):
    """Obiettivo di allenamento — determina TUTTI i parametri di carico."""

    FORZA = "forza"
    IPERTROFIA = "ipertrofia"
    RESISTENZA = "resistenza"
    DIMAGRIMENTO = "dimagrimento"
    TONIFICAZIONE = "tonificazione"


class Livello(str, Enum):
    """Livello di esperienza — determina volume tollerabile (MEV→MAV→MRV)."""

    PRINCIPIANTE = "principiante"
    INTERMEDIO = "intermedio"
    AVANZATO = "avanzato"


class GruppoMuscolare(str, Enum):
    """
    15 gruppi muscolari funzionali.

    Nota: i deltoidi sono divisi in 3 porzioni perche' hanno ruoli
    diversi nella programmazione (anteriore lavora nei push,
    laterale richiede isolamento, posteriore lavora nei pull).
    Fonte: NSCA (Haff & Triplett 2016), Contreras 2010.
    """

    PETTO = "petto"
    DORSALI = "dorsali"
    DELT_ANT = "deltoide_anteriore"
    DELT_LAT = "deltoide_laterale"
    DELT_POST = "deltoide_posteriore"
    BICIPITI = "bicipiti"
    TRICIPITI = "tricipiti"
    QUADRICIPITI = "quadricipiti"
    FEMORALI = "femorali"
    GLUTEI = "glutei"
    POLPACCI = "polpacci"
    TRAPEZIO = "trapezio"
    CORE = "core"
    AVAMBRACCI = "avambracci"
    ADDUTTORI = "adduttori"


class PatternMovimento(str, Enum):
    """
    Pattern di movimento — classificazione funzionale degli esercizi.

    9 pattern compound (multi-articolari) + 9 pattern isolation (mono-articolari).
    Ogni esercizio nel DB mappa a uno di questi pattern.
    """

    # Compound (multi-articolari)
    PUSH_H = "push_h"
    PUSH_V = "push_v"
    SQUAT = "squat"
    HINGE = "hinge"
    PULL_H = "pull_h"
    PULL_V = "pull_v"
    CORE = "core"
    ROTATION = "rotation"
    CARRY = "carry"

    # Isolation (mono-articolari)
    HIP_THRUST = "hip_thrust"
    CURL = "curl"
    EXTENSION_TRI = "extension_tri"
    LATERAL_RAISE = "lateral_raise"
    FACE_PULL = "face_pull"
    CALF_RAISE = "calf_raise"
    LEG_CURL = "leg_curl"
    LEG_EXTENSION = "leg_extension"
    ADDUCTOR = "adductor"


class TipoSplit(str, Enum):
    """Tipo di suddivisione settimanale."""

    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"


class RuoloSessione(str, Enum):
    """Ruolo funzionale della sessione all'interno dello split."""

    FULL_BODY = "full_body"
    UPPER = "upper"
    LOWER = "lower"
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"


class OrdinePriorita(int, Enum):
    """
    Priorita' di ordinamento nella sessione.
    Gerarchia fisiologica (NSCA): SNC-demanding first.
    """

    WARMUP = 1
    COMPOUND_HEAVY = 2
    COMPOUND_LIGHT = 3
    ISOLATION = 4
    CORE_STABILITY = 5
    COOLDOWN = 6


# ════════════════════════════════════════════════════════════
# MODELLI — Strutture dati del dominio
# ════════════════════════════════════════════════════════════


class ParametriCarico(BaseModel):
    """
    Parametri di carico per un obiettivo di allenamento.
    Fonte: NSCA 2016, ACSM 2009, Schoenfeld 2010/2017.
    """

    obiettivo: Obiettivo
    intensita_min: float = Field(description="% 1RM minima")
    intensita_max: float = Field(description="% 1RM massima")
    rep_min: int = Field(description="Ripetizioni minime per serie")
    rep_max: int = Field(description="Ripetizioni massime per serie")
    serie_compound: tuple[int, int] = Field(description="Range serie per esercizio compound (min, max)")
    serie_isolation: tuple[int, int] = Field(description="Range serie per esercizio isolation (min, max)")
    riposo_compound: tuple[int, int] = Field(description="Riposo compound in secondi (min, max)")
    riposo_isolation: tuple[int, int] = Field(description="Riposo isolation in secondi (min, max)")
    percentuale_compound: float = Field(description="% esercizi compound sul totale (0-1)")
    freq_per_muscolo: tuple[int, int] = Field(description="Frequenza per muscolo/sett (min, max)")
    fattore_volume: float = Field(
        description="Moltiplicatore sul MAV ipertrofia (1.0 = ipertrofia, 0.7 = forza, ecc.)"
    )
    fonte: str = Field(description="Fonte bibliografica principale")


class VolumeTarget(BaseModel):
    """
    Volume target per un gruppo muscolare ad un dato livello.
    Unita': serie dirette effettive per settimana.
    Fonte: Israetel (RP), Schoenfeld 2017, Krieger 2010.
    """

    muscolo: GruppoMuscolare
    mev: float = Field(description="Minimum Effective Volume — sotto = nessuno stimolo")
    mav_min: float = Field(description="Maximum Adaptive Volume — inizio range ottimale")
    mav_max: float = Field(description="Maximum Adaptive Volume — fine range ottimale")
    mrv: float = Field(description="Maximum Recoverable Volume — oltre = overtraining")
    note: str = Field(default="", description="Note specifiche (es. 'volume indiretto sufficiente')")


class ContributoMuscolare(BaseModel):
    """
    Contributo di un pattern di movimento ad un gruppo muscolare.
    Scala 0-1 basata su attivazione EMG.
    """

    muscolo: GruppoMuscolare
    contributo: float = Field(ge=0.0, le=1.0, description="0=non coinvolto, 1=motore primario")


class RapportoBiomeccanico(BaseModel):
    """Rapporto target tra catene muscolari per equilibrio posturale."""

    nome: str = Field(description="Nome del rapporto (es. 'Push:Pull')")
    numeratore: list[str] = Field(description="Pattern/muscoli al numeratore")
    denominatore: list[str] = Field(description="Pattern/muscoli al denominatore")
    target: float = Field(description="Valore target del rapporto")
    tolleranza: float = Field(default=0.15, description="Scostamento ammesso dal target")
    fonte: str = Field(description="Fonte bibliografica")


class SlotSessione(BaseModel):
    """
    Uno slot in una sessione di allenamento.
    Rappresenta 'qui va un esercizio di questo tipo con questi parametri'.
    """

    pattern: PatternMovimento
    priorita: OrdinePriorita
    serie: int
    rep_min: int
    rep_max: int
    riposo_sec: int
    muscolo_target: Optional[GruppoMuscolare] = Field(
        default=None,
        description="Se specificato, lo slot mira a questo muscolo (isolation). Altrimenti segue il pattern."
    )
    note: str = Field(default="", description="Nota per il trainer (es. 'enfasi eccentrica')")
    carico_kg: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=500.0,
        description=(
            "Carico in kg (opzionale). Se presente, abilita il calcolo del "
            "tonnellaggio (serie × rep × kg) e dell'intensita' relativa (% 1RM). "
            "Fonte: Haff & Triplett (NSCA 2016) cap. 15."
        ),
    )


class TemplateSessione(BaseModel):
    """Template di una sessione con slot tipizzati."""

    nome: str
    ruolo: RuoloSessione
    focus: str = Field(description="Descrizione focus (es. 'petto, spalle, tricipiti')")
    slots: list[SlotSessione]


class TemplatePiano(BaseModel):
    """Piano settimanale completo generato dal sistema."""

    frequenza: int = Field(ge=2, le=6)
    obiettivo: Obiettivo
    livello: Livello
    tipo_split: TipoSplit
    sessioni: list[TemplateSessione]
    note_generazione: list[str] = Field(
        default_factory=list,
        description="Note e warning dal processo di generazione (es. frequenza clampata)",
    )

    # ── Profilo demografico (opzionale) ──
    # Se presenti, i target di volume vengono scalati per sesso ed eta'.
    # Fonti: Vingren (2010) testosterone sex differences,
    #        Häkkinen (2001) age-related recovery, Peterson (2011) dose-response aging.
    sesso: Optional[str] = Field(
        default=None,
        description=(
            "Sesso biologico del cliente ('M' o 'F'). Se presente, scala i target MAV: "
            "le donne hanno ~15x meno testosterone (Vingren 2010), rispondono ~85% "
            "dello stimolo maschile a parita' di volume relativo (Schoenfeld 2017)."
        ),
    )
    eta: Optional[int] = Field(
        default=None,
        ge=10,
        le=100,
        description=(
            "Eta' del cliente in anni. Se presente, scala i target MAV per capacita' "
            "di recupero: under 30 = 1.0, 30-45 = 0.95, 45-60 = 0.85, 60+ = 0.75. "
            "Fonti: Häkkinen (2001), Peterson (2011)."
        ),
    )


class VolumeEffettivo(BaseModel):
    """Volume effettivo calcolato per un gruppo muscolare."""

    muscolo: GruppoMuscolare
    serie_effettive: float = Field(description="Serie dirette effettive/settimana (pesate per carico se disponibile)")
    target_mev: float
    target_mav_min: float
    target_mav_max: float
    target_mrv: float
    stato: str = Field(description="sotto_mev | mev_mav | ottimale | sopra_mav | sopra_mrv")
    tensione_kg: Optional[float] = Field(
        default=None,
        description=(
            "Tensione meccanica in kg (tonnage x EMG). "
            "Presente solo se almeno uno slot ha carico_kg. "
            "Schoenfeld 2010: mechanical tension = driver primario ipertrofia."
        ),
    )


class AnalisiVolume(BaseModel):
    """Risultato dell'analisi volume di un piano."""

    per_muscolo: list[VolumeEffettivo]
    volume_totale_settimana: float
    muscoli_sotto_mev: list[str]
    muscoli_sopra_mrv: list[str]
    has_load_data: bool = Field(
        default=False,
        description=(
            "True se almeno uno slot ha carico_kg compilato. "
            "Quando True, le serie_effettive sono pesate per intensita' "
            "(dose-response model: Israetel RP 2020, NSCA 2016)."
        ),
    )
    tonnellaggio_totale: Optional[float] = Field(
        default=None,
        description="Volume-Load totale settimanale in kg (NSCA 2016). Presente solo con carico.",
    )
    zona_prevalente: Optional[str] = Field(
        default=None,
        description="Zona NSCA prevalente (massimale/sub_massimale/ipertrofia/resistenza/attivazione).",
    )


class AnalisiBalance(BaseModel):
    """Risultato dell'analisi dei rapporti biomeccanici."""

    rapporti: dict[str, float] = Field(description="Valore calcolato per ogni rapporto")
    target: dict[str, float] = Field(description="Valore target per ogni rapporto")
    squilibri: list[str] = Field(description="Rapporti fuori tolleranza")


class ContributoEsercizio(BaseModel):
    """Volume ipertrofico di un singolo esercizio su un muscolo."""

    nome_esercizio: str = Field(description="Nome dello slot (pattern + indice)")
    pattern: PatternMovimento
    serie: int
    contributo_emg: float = Field(ge=0.0, le=1.0, description="Contributo EMG 0-1")
    serie_ipertrofiche: float = Field(description="serie × peso ipertrofico")
    carico_kg: Optional[float] = Field(
        default=None,
        description="Carico in kg dello slot (se presente nel piano)",
    )


class DettaglioMuscolo(BaseModel):
    """Dettaglio completo per un muscolo — drill-down nella tab analisi."""

    muscolo: GruppoMuscolare
    serie_effettive: float
    target_mev: float
    target_mav_min: float
    target_mav_max: float
    target_mrv: float
    stato: str = Field(description="sotto_mev | mev_mav | ottimale | sopra_mav | sopra_mrv")
    frequenza: int = Field(description="Sessioni/settimana che stimolano questo muscolo")
    contributi: list[ContributoEsercizio] = Field(
        default_factory=list,
        description="Breakdown volume per esercizio (drill-down)",
    )
    tensione_kg: Optional[float] = Field(
        default=None,
        description="Tensione meccanica in kg (Schoenfeld 2010). Presente solo con carico.",
    )


class DettaglioRapporto(BaseModel):
    """Dettaglio di un rapporto biomeccanico con volume per lato."""

    nome: str
    valore: float
    target: float
    tolleranza: float
    in_tolleranza: bool
    volume_numeratore: float = Field(description="Volume totale lato numeratore")
    volume_denominatore: float = Field(description="Volume totale lato denominatore")
    fonte: str


class DettaglioRecovery(BaseModel):
    """Overlap muscolare tra due sessioni consecutive."""

    sessione_a: str
    sessione_b: str
    muscoli_overlap: list[str]
    serie_overlap_a: dict[str, float] = Field(description="muscolo → serie nella sessione A")
    serie_overlap_b: dict[str, float] = Field(description="muscolo → serie nella sessione B")


class TonnellaggioSlotAnalisi(BaseModel):
    """Tonnellaggio calcolato per un singolo slot con carico assegnato."""

    pattern: str = Field(description="Pattern di movimento")
    sessione: str = Field(description="Nome della sessione")
    serie: int
    rep_medie: float = Field(description="Media rep range (rep_min+rep_max)/2")
    carico_kg: float = Field(description="Carico in kg")
    tonnellaggio: float = Field(
        description="serie × rep_medie × carico_kg (Haff & Triplett, NSCA 2016)"
    )
    intensita_relativa: Optional[float] = Field(
        default=None,
        description="%1RM se 1RM noto (carico_kg / 1RM). Kraemer & Ratamess 2004.",
    )
    zona_intensita: Optional[str] = Field(
        default=None,
        description="Zona NSCA (massimale/sub_massimale/ipertrofia/resistenza/attivazione)",
    )


class AnalisiTonnellaggio(BaseModel):
    """
    Analisi biomeccanica volume-load di un piano con carichi assegnati.

    Due livelli di analisi:

    1. **Tonnellaggio grezzo** — Σ(serie × rep × kg) per slot e sessione.
       Metrica gold standard per carico totale (Haff & Triplett, NSCA 2016).

    2. **Tensione meccanica per muscolo** — tonnellaggio × coefficiente EMG
       dalla matrice di contribuzione muscolare. Questo e' il dato biomeccanico
       reale: la forza meccanica che ogni gruppo muscolare sostiene, pesata
       per il suo livello di attivazione in ciascun pattern.

       Formula: tensione[M] = Σ(tonnage_slot × contribution[pattern][M])

       La tensione meccanica e' il driver primario dell'ipertrofia
       (Schoenfeld 2010, "mechanical tension hypothesis").

    Fonti:
      - Haff & Triplett (NSCA 2016) cap. 15 — Volume-Load definition
      - McBride et al. (2009) — Tonnage as training load metric
      - Schoenfeld (2010) — Mechanical tension as hypertrophy driver
      - Contreras (2010) — EMG analysis of resistance exercises
    """

    tonnellaggio_totale: float = Field(description="Σ(serie × rep × kg) settimanale")
    tonnellaggio_per_sessione: dict[str, float] = Field(
        description="Tonnellaggio per nome sessione"
    )
    intensita_media_ponderata: Optional[float] = Field(
        default=None,
        description="Media %1RM pesata per tonnellaggio (se 1RM disponibili)",
    )
    slot_detail: list[TonnellaggioSlotAnalisi] = Field(
        default_factory=list,
        description="Dettaglio per ogni slot con carico",
    )
    zona_prevalente: Optional[str] = Field(
        default=None,
        description="Zona NSCA prevalente (per serie)",
    )

    # ── Biomeccanica muscolare ──
    tensione_per_muscolo: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Tensione meccanica per gruppo muscolare (kg). "
            "tonnage × EMG activation coefficient per pattern. "
            "Schoenfeld 2010, Contreras 2010."
        ),
    )
    tensione_ipertrofica_per_muscolo: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Tensione ipertrofica per muscolo (kg) — pesata con "
            "hypertrophy weights (Israetel RP 2020 half-set rule). "
            "Esclude lavoro sotto soglia EMG 40% MVC."
        ),
    )

    fonte: str = Field(
        default=(
            "Haff & Triplett (NSCA 2016) cap. 15; McBride (2009); "
            "Schoenfeld (2010) mechanical tension; Contreras (2010) EMG"
        ),
    )


class AnalisiPiano(BaseModel):
    """Analisi completa di un piano di allenamento."""

    volume: AnalisiVolume
    balance: AnalisiBalance
    warnings: list[str] = Field(default_factory=list)
    score: float = Field(ge=0, le=100, description="Punteggio globale 0-100")

    # Dati strutturati per la Scientific Analysis Tab (v2)
    dettaglio_muscoli: list[DettaglioMuscolo] = Field(default_factory=list)
    dettaglio_rapporti: list[DettaglioRapporto] = Field(default_factory=list)
    frequenza_per_muscolo: dict[str, int] = Field(default_factory=dict)
    recovery_overlaps: list[DettaglioRecovery] = Field(default_factory=list)

    # Volume-Load (v3) — disponibile solo con carico_kg
    tonnellaggio: Optional[AnalisiTonnellaggio] = Field(
        default=None,
        description=(
            "Analisi tonnellaggio (Volume-Load). Presente solo se almeno "
            "uno slot ha carico_kg compilato. Fonte: NSCA 2016."
        ),
    )
