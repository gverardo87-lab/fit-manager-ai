"""
Training Science Engine — Principi e parametri di carico.

Ogni obiettivo di allenamento ha parametri specifici derivati dalla letteratura.
Questo modulo e' la "costituzione" del motore: i numeri qui determinano
TUTTO il comportamento del sistema.

Fonti:
  - NSCA — Essentials of Strength Training and Conditioning (Haff & Triplett, 2016)
  - ACSM — Guidelines for Exercise Testing and Prescription (2009)
  - Schoenfeld — "The mechanisms of muscle hypertrophy" (2010)
  - Schoenfeld — "Dose-response relationship for RT volume" (2017)
  - Schoenfeld — "Effects of RT frequency on hypertrophy" (2016)
  - Krieger — "Single vs multiple sets of RT" (2010)
  - Ralston et al. — "Strength training: a systematic review" (2017)
"""

from .types import Obiettivo, ParametriCarico


# ════════════════════════════════════════════════════════════
# PARAMETRI DI CARICO PER OBIETTIVO
# ════════════════════════════════════════════════════════════

PARAMETRI_CARICO: dict[Obiettivo, ParametriCarico] = {
    Obiettivo.FORZA: ParametriCarico(
        obiettivo=Obiettivo.FORZA,
        intensita_min=0.85,
        intensita_max=1.00,
        rep_min=1,
        rep_max=5,
        serie_compound=(3, 5),
        serie_isolation=(2, 3),
        riposo_compound=(180, 300),
        riposo_isolation=(120, 180),
        percentuale_compound=0.80,
        freq_per_muscolo=(2, 3),
        fattore_volume=0.70,
        fonte="NSCA 2016, Ralston 2017",
    ),
    Obiettivo.IPERTROFIA: ParametriCarico(
        obiettivo=Obiettivo.IPERTROFIA,
        intensita_min=0.65,
        intensita_max=0.85,
        rep_min=6,
        rep_max=12,
        serie_compound=(3, 4),
        serie_isolation=(3, 4),
        riposo_compound=(90, 120),
        riposo_isolation=(60, 90),
        percentuale_compound=0.60,
        freq_per_muscolo=(2, 2),
        fattore_volume=1.00,
        fonte="Schoenfeld 2010/2017, Krieger 2010",
    ),
    Obiettivo.RESISTENZA: ParametriCarico(
        obiettivo=Obiettivo.RESISTENZA,
        intensita_min=0.50,
        intensita_max=0.65,
        rep_min=15,
        rep_max=25,
        serie_compound=(2, 3),
        serie_isolation=(2, 3),
        riposo_compound=(30, 60),
        riposo_isolation=(30, 45),
        percentuale_compound=0.50,
        freq_per_muscolo=(2, 3),
        fattore_volume=0.60,
        fonte="ACSM 2009, NSCA 2016",
    ),
    Obiettivo.DIMAGRIMENTO: ParametriCarico(
        obiettivo=Obiettivo.DIMAGRIMENTO,
        intensita_min=0.65,
        intensita_max=0.80,
        rep_min=8,
        rep_max=15,
        serie_compound=(3, 4),
        serie_isolation=(2, 3),
        riposo_compound=(45, 90),
        riposo_isolation=(30, 60),
        percentuale_compound=0.70,
        freq_per_muscolo=(2, 3),
        fattore_volume=0.80,
        fonte="NSCA 2016, Schoenfeld 2021",
    ),
    Obiettivo.TONIFICAZIONE: ParametriCarico(
        obiettivo=Obiettivo.TONIFICAZIONE,
        intensita_min=0.60,
        intensita_max=0.75,
        rep_min=10,
        rep_max=15,
        serie_compound=(2, 3),
        serie_isolation=(2, 3),
        riposo_compound=(60, 90),
        riposo_isolation=(45, 60),
        percentuale_compound=0.60,
        freq_per_muscolo=(2, 2),
        fattore_volume=0.70,
        fonte="ACSM 2009",
    ),
}


def get_parametri(obiettivo: Obiettivo) -> ParametriCarico:
    """Ritorna i parametri di carico per l'obiettivo specificato."""
    return PARAMETRI_CARICO[obiettivo]


def get_serie_per_slot(
    obiettivo: Obiettivo, is_compound: bool, is_primary: bool
) -> int:
    """
    Determina le serie per uno slot in base a obiettivo e ruolo.

    is_compound: True per esercizi multi-articolari
    is_primary: True per il primo esercizio compound della sessione
    """
    p = PARAMETRI_CARICO[obiettivo]
    if is_compound:
        return p.serie_compound[1] if is_primary else p.serie_compound[0]
    return p.serie_isolation[0]


def get_rep_range(obiettivo: Obiettivo) -> tuple[int, int]:
    """Ritorna (rep_min, rep_max) per l'obiettivo."""
    p = PARAMETRI_CARICO[obiettivo]
    return (p.rep_min, p.rep_max)


def get_riposo(obiettivo: Obiettivo, is_compound: bool) -> int:
    """Ritorna il riposo in secondi (valore medio del range)."""
    p = PARAMETRI_CARICO[obiettivo]
    r = p.riposo_compound if is_compound else p.riposo_isolation
    return (r[0] + r[1]) // 2
