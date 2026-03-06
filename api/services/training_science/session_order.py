"""
Training Science Engine — Ordinamento fisiologico degli esercizi in sessione.

L'ordine degli esercizi in una sessione NON e' arbitrario.
Il sistema nervoso centrale (SNC) ha risorse limitate: gli esercizi
piu' impegnativi vanno eseguiti per primi, quando il SNC e' fresco.

Gerarchia NSCA (Haff & Triplett 2016, cap. 17):
  1. WARMUP         — Attivazione e preparazione articolare
  2. COMPOUND HEAVY — Multi-articolari pesanti (squat, stacco, panca)
  3. COMPOUND LIGHT — Multi-articolari leggeri (carry, rotation, core compound)
  4. ISOLATION      — Mono-articolari (curl, lateral raise, leg curl)
  5. CORE STABILITY — Lavoro di stabilizzazione (plank, anti-rotation)
  6. COOLDOWN       — Stretching e mobilita'

All'interno dello stesso livello, l'ordine segue la regola
"Large to Small" (NSCA): muscoli grandi prima dei piccoli.
Rationale: i muscoli grandi consumano piu' risorse del SNC.

Sottoprincipio (Israetel RP 2020):
  Se la sessione ha un pattern primario (es. squat nel Lower Day),
  questo va SEMPRE prima di pattern secondari dello stesso livello
  (es. hinge). Il pattern primario riceve il beneficio massimo del SNC fresco.

Fonti:
  - NSCA — "Essentials of Strength Training" (2016) cap. 17
  - Simao et al. — "Exercise order in resistance training" (2012)
  - Israetel — "Scientific Principles of Hypertrophy Training" (2020)
  - Sforzo & Touey — "Manipulating exercise order" (1996)
"""

from .types import (
    PatternMovimento as P,
    OrdinePriorita as OP,
)


# ════════════════════════════════════════════════════════════
# CLASSIFICAZIONE PATTERN → PRIORITA'
# ════════════════════════════════════════════════════════════
#
# Ogni pattern ha una priorita' fisiologica intrinseca.
# Basata su:
#   - Numero di articolazioni coinvolte (NSCA 2016)
#   - Carico assoluto tipico (indicatore demand SNC)
#   - Complessita' motoria (coordinazione multi-segmento)

PRIORITA_PATTERN: dict[P, OP] = {
    # ── Compound Heavy (Squat, hinge, push/pull compound) ──
    # Multi-articolari, alto carico, alta domanda SNC
    P.SQUAT: OP.COMPOUND_HEAVY,
    P.HINGE: OP.COMPOUND_HEAVY,
    P.PUSH_H: OP.COMPOUND_HEAVY,
    P.PUSH_V: OP.COMPOUND_HEAVY,
    P.PULL_H: OP.COMPOUND_HEAVY,
    P.PULL_V: OP.COMPOUND_HEAVY,

    # ── Compound Light (funzionali, medio carico) ──
    P.CARRY: OP.COMPOUND_LIGHT,
    P.ROTATION: OP.COMPOUND_LIGHT,
    P.CORE: OP.CORE_STABILITY,

    # ── Isolation (mono-articolari) ──
    P.CURL: OP.ISOLATION,
    P.EXTENSION_TRI: OP.ISOLATION,
    P.LATERAL_RAISE: OP.ISOLATION,
    P.FACE_PULL: OP.ISOLATION,
    P.LEG_EXTENSION: OP.ISOLATION,
    P.LEG_CURL: OP.ISOLATION,
    P.CALF_RAISE: OP.ISOLATION,
    P.HIP_THRUST: OP.ISOLATION,
    P.ADDUCTOR: OP.ISOLATION,
}


# ════════════════════════════════════════════════════════════
# REGOLA LARGE-TO-SMALL — Ordine secondario dentro stesso livello
# ════════════════════════════════════════════════════════════
#
# A parita' di priorita', i pattern che attivano muscoli piu' grandi
# vanno prima. La "grandezza" e' approssimata dalla massa muscolare
# relativa (Holzbaur et al. 2007, PCSA data).
#
# L'ordine numerico basso = priorita' alta (va prima).

ORDINE_PATTERN_SECONDARIO: dict[P, int] = {
    # Compound heavy: lower body first (piu' massa), poi upper
    P.SQUAT: 1,       # quadricipiti + glutei = massa massima
    P.HINGE: 2,       # femorali + glutei + dorsali
    P.PULL_H: 3,      # dorsali (gruppo grande)
    P.PULL_V: 4,      # dorsali (variante)
    P.PUSH_H: 5,      # petto (gruppo grande)
    P.PUSH_V: 6,      # deltoidi (gruppo medio)

    # Compound light
    P.CARRY: 10,      # grip + core + trapezio
    P.ROTATION: 11,   # core + deltoidi

    # Isolation: grandi prima, piccoli dopo
    P.HIP_THRUST: 20,   # glutei (grande)
    P.LEG_EXTENSION: 21, # quadricipiti
    P.LEG_CURL: 22,      # femorali
    P.ADDUCTOR: 23,      # adduttori
    P.LATERAL_RAISE: 24, # deltoidi laterali
    P.FACE_PULL: 25,     # deltoidi posteriori
    P.CURL: 26,          # bicipiti (piccolo)
    P.EXTENSION_TRI: 27, # tricipiti (piccolo)
    P.CALF_RAISE: 28,    # polpacci (piccolo)

    # Core stability
    P.CORE: 30,
}


def get_priority(pattern: P) -> OP:
    """Ritorna la priorita' fisiologica di un pattern."""
    return PRIORITA_PATTERN[pattern]


def get_secondary_order(pattern: P) -> int:
    """Ritorna l'ordine secondario (large-to-small) di un pattern."""
    return ORDINE_PATTERN_SECONDARIO.get(pattern, 99)


def sort_key(pattern: P) -> tuple[int, int]:
    """
    Chiave di ordinamento composita per un pattern.

    Ordina per:
      1. Priorita' fisiologica (NSCA: SNC-demanding first)
      2. Ordine secondario large-to-small (Holzbaur PCSA)

    Esempio ordinamento sessione Full Body:
      squat → hinge → pull_h → push_h → carry → lateral_raise → curl → core
    """
    return (PRIORITA_PATTERN[pattern].value, ORDINE_PATTERN_SECONDARIO.get(pattern, 99))


def order_patterns(patterns: list[P]) -> list[P]:
    """
    Ordina una lista di pattern secondo la gerarchia fisiologica.

    Input: pattern in ordine qualsiasi
    Output: pattern ordinati per esecuzione ottimale

    Esempio:
        order_patterns([P.CURL, P.SQUAT, P.PUSH_H, P.CORE])
        → [P.SQUAT, P.PUSH_H, P.CURL, P.CORE]
    """
    return sorted(patterns, key=sort_key)


def validate_order(patterns: list[P]) -> list[str]:
    """
    Valida l'ordine di una sequenza di pattern.

    Ritorna lista di violazioni (vuota se ordine corretto).
    Ogni violazione e' una stringa descrittiva del problema.
    """
    violations: list[str] = []

    for i in range(len(patterns) - 1):
        curr = patterns[i]
        next_p = patterns[i + 1]

        curr_pri = PRIORITA_PATTERN[curr]
        next_pri = PRIORITA_PATTERN[next_p]

        # Violazione: isolamento prima di compound
        if curr_pri.value > next_pri.value:
            violations.append(
                f"Ordine non ottimale: {next_p.value} ({next_pri.name}) "
                f"dopo {curr.value} ({curr_pri.name})"
            )

    return violations
