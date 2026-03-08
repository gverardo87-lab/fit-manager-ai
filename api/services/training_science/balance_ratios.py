"""
Training Science Engine — Rapporti biomeccanici e equilibrio posturale.

Squilibri tra catene muscolari sono la causa principale di infortuni
e problemi posturali. Questo modulo definisce i rapporti target e
analizza l'equilibrio di un piano di allenamento.

Fonti:
  - Sahrmann — "Movement System Impairment Syndromes" (2002)
  - Janda — "Muscles: Testing and Function" (1983)
  - NSCA — "Essentials of Strength Training" (2016) cap. 21
  - Alentorn-Geli — "Prevention of ACL injuries" (2009)
"""

from .types import (
    GruppoMuscolare as M,
    PatternMovimento as P,
    RapportoBiomeccanico,
    AnalisiBalance,
)
from .muscle_contribution import compute_hypertrophy_sets


# ════════════════════════════════════════════════════════════
# RAPPORTI TARGET
# ════════════════════════════════════════════════════════════

BALANCE_RATIOS: list[RapportoBiomeccanico] = [
    # ── 1. Push : Pull ──────────────────────────────────────
    # Evidenza: FORTE — prescrizione diretta da 3 testi madre.
    RapportoBiomeccanico(
        nome="Push : Pull",
        numeratore=["push_h", "push_v"],
        denominatore=["pull_h", "pull_v"],
        target=1.0,
        tolleranza=0.15,
        fonte="NSCA 2016 cap. 21: il principio agonista-antagonista richiede "
        "volume bilanciato tra pushing e pulling per salute articolare. "
        "Sahrmann 2002: la upper crossed syndrome origina da dominanza "
        "della catena anteriore (pettorali, deltoide anteriore) rispetto "
        "alla posteriore (romboidi, trapezio medio/basso). "
        "Janda 1983: lo squilibrio push-pull guida i pattern di "
        "compensazione posturale. Range [0.85, 1.15].",
    ),
    # ── 2. Push Orizzontale : Push Verticale ────────────────
    # Evidenza: MODERATA — ragionamento biomeccanico convergente,
    # nessuna fonte prescrive un rapporto numerico specifico.
    RapportoBiomeccanico(
        nome="Push Orizz : Push Vert",
        numeratore=["push_h"],
        denominatore=["push_v"],
        target=1.5,
        tolleranza=1.0,
        fonte="Sahrmann 2002: il deltoide anteriore e' classificato come "
        "'overactive' nella upper crossed syndrome — push_v lo usa come "
        "motore primario (EMG ~100%% MVC), push_h come sinergista (~70%% MVC). "
        "Preferire push_h riduce l'iperattivazione del deltoide anteriore. "
        "Boettcher et al. 2008: la posizione overhead aumenta il rischio "
        "di impingement subacromiale — limitare il volume push_v e' protettivo. "
        "Schoenfeld 2010: bench press (push_h) produce attivazione del "
        "pectoralis major superiore all'overhead press. "
        "Target 1.5: preferenza moderata orizzontale. "
        "Tolleranza ampia [0.5, 2.5] — nessuna fonte prescrive un rapporto "
        "specifico, la tolleranza riflette il livello di evidenza.",
    ),
    # ── 3. Pull Orizzontale : Pull Verticale ────────────────
    # Evidenza: MODERATA — Sahrmann raccomanda rows ma senza
    # quantificare il rapporto ideale.
    RapportoBiomeccanico(
        nome="Pull Orizz : Pull Vert",
        numeratore=["pull_h"],
        denominatore=["pull_v"],
        target=1.2,
        tolleranza=0.80,
        fonte="Sahrmann 2002: gli esercizi di row sono raccomandati "
        "specificamente per il rinforzo della retrazione scapolare "
        "(trapezio medio/basso, romboidi) — correttivo primario della "
        "upper crossed syndrome. La trazione orizzontale attiva il "
        "deltoide posteriore come sinergista maggiore (EMG ~70%% MVC, "
        "Contreras 2010), contro il ~40%% della trazione verticale. "
        "NSCA 2016: entrambi i pattern sono 'core exercises' senza "
        "prescrizione volumetrica reciproca. "
        "Target 1.2: leggera preferenza orizzontale (Sahrmann). "
        "Tolleranza ampia [0.4, 2.0] — riflette evidenza limitata.",
    ),
    # ── 4. Quadricipiti : Femorali ──────────────────────────
    # Evidenza: MODERATA-FORTE — derivazione algebrica dalla matrice
    # EMG combinata con il principio di bilanciamento squat/hinge.
    RapportoBiomeccanico(
        nome="Quad : Ham",
        numeratore=["quadricipiti"],
        denominatore=["femorali"],
        target=0.80,
        tolleranza=0.30,
        fonte="NSCA 2016 cap. 21: il lower body richiede pattern squat "
        "(knee-dominant) e hinge (hip-dominant) in equilibrio. "
        "Alentorn-Geli 2009: il rapporto H:Q < 0.6 (forza isocinetica) "
        "e' fattore di rischio ACL — principio tradotto in volume: i femorali "
        "necessitano volume adeguato rispetto ai quadricipiti. "
        "Israetel RP 2020: serie dirette quadricipiti e femorali approssimativamente "
        "pari per sviluppo bilanciato. "
        "Target 0.80: derivazione algebrica dalla matrice EMG con programmazione "
        "squat:hinge bilanciata — squat contribuisce quad 1.0 + ham 0.25 (hyp), "
        "hinge contribuisce ham 1.0, dunque quad:ham = n/(0.25n+n) = 0.80. "
        "Nota: il rapporto FORZA isocinetico (H:Q ~0.6, Alentorn-Geli 2009) "
        "e' un concetto diverso dal rapporto VOLUME ipertrofico. "
        "Range [0.50, 1.10].",
    ),
    # ── 5. Catena Anteriore : Catena Posteriore ─────────────
    # Evidenza: FORTE — prescrizione clinica diretta.
    RapportoBiomeccanico(
        nome="Anteriore : Posteriore",
        numeratore=["petto", "deltoide_anteriore", "quadricipiti"],
        denominatore=["dorsali", "deltoide_posteriore", "femorali"],
        target=0.80,
        tolleranza=0.25,
        fonte="Sahrmann 2002: upper crossed syndrome (pettorali + deltoide "
        "anteriore iperattivi) e lower crossed syndrome (flessori anca + "
        "quadricipiti iperattivi) sono i due pattern principali di disfunzione "
        "posturale — la catena posteriore necessita volume pari o superiore. "
        "Janda 1983: i muscoli 'tonici' (catena anteriore) tendono ad "
        "accorciarsi e ipertivarsi, i muscoli 'fasici' (catena posteriore) "
        "tendono a indebolirsi — il volume deve favorire la catena posteriore. "
        "NSCA 2016: i compound posteriori (hinge, pull) accumulano "
        "naturalmente piu' volume muscolo-specifico per sinergie "
        "multi-articolari. Target 0.80: la catena anteriore e' ~80%% della "
        "posteriore (Sahrmann/Janda: posteriore >= anteriore). "
        "Range [0.55, 1.05].",
    ),
]


# ════════════════════════════════════════════════════════════
# PATTERN → CATENA per il calcolo rapporti
# ════════════════════════════════════════════════════════════

# Quali pattern contano come "push" e "pull" nel rapporto volume
_PUSH_PATTERNS = {P.PUSH_H, P.PUSH_V}
_PULL_PATTERNS = {P.PULL_H, P.PULL_V}


def _sum_pattern_sets(
    slots: list[tuple[P, int]],
    patterns: set[P],
    intensity_weights: list[float] | None = None,
) -> float:
    """Somma le serie (pesate per intensita' se disponibile) per un gruppo di pattern."""
    if intensity_weights is None:
        return sum(s for p, s in slots if p in patterns)
    return sum(
        s * w for (p, s), w in zip(slots, intensity_weights) if p in patterns
    )


def _sum_muscle_sets(
    effective: dict[M, float], muscle_names: list[str]
) -> float:
    """Somma le serie effettive per una lista di nomi muscolo."""
    total = 0.0
    for name in muscle_names:
        for m in M:
            if m.value == name:
                total += effective.get(m, 0.0)
                break
    return total


def analyze_balance(
    slots: list[tuple[P, int]],
    intensity_weights: list[float] | None = None,
) -> AnalisiBalance:
    """
    Analizza i rapporti biomeccanici di un piano settimanale.

    Input: lista di (pattern, serie) per l'intera settimana.
    Se intensity_weights e' fornito (dose-response model), le serie
    vengono pesate per intensita' nei calcoli dei rapporti.
    Output: rapporti calcolati vs target, con lista squilibri.
    """
    # Volume ipertrofico per rapporti muscolari (Quad:Ham, Ant:Post).
    # Il volume meccanico (compute_effective_sets) gonfia i denominatori
    # con contributi indiretti EMG < 40% MVC che non producono stimolo
    # ipertrofico (Schoenfeld 2017), rendendo i target irraggiungibili.
    # Il volume ipertrofico (compute_hypertrophy_sets) sconta i contributi
    # sotto soglia — allineato alla stessa metrica usata per l'analisi volume.
    hypertrophy = compute_hypertrophy_sets(slots, intensity_weights)
    rapporti: dict[str, float] = {}
    target: dict[str, float] = {}
    squilibri: list[str] = []

    for ratio in BALANCE_RATIOS:
        # Determina se il rapporto e' su pattern o muscoli
        is_pattern_ratio = ratio.numeratore[0] in {p.value for p in P}

        if is_pattern_ratio:
            num_patterns = {P(v) for v in ratio.numeratore if v in {p.value for p in P}}
            den_patterns = {P(v) for v in ratio.denominatore if v in {p.value for p in P}}
            num_val = _sum_pattern_sets(slots, num_patterns, intensity_weights)
            den_val = _sum_pattern_sets(slots, den_patterns, intensity_weights)
        else:
            num_val = _sum_muscle_sets(hypertrophy, ratio.numeratore)
            den_val = _sum_muscle_sets(hypertrophy, ratio.denominatore)

        if den_val > 0:
            computed = round(num_val / den_val, 2)
        elif num_val > 0:
            computed = 99.0  # denominatore zero con numeratore presente = squilibrio totale
        else:
            computed = ratio.target  # entrambi zero = neutro

        rapporti[ratio.nome] = computed
        target[ratio.nome] = ratio.target

        if abs(computed - ratio.target) > ratio.tolleranza:
            direction = "alto" if computed > ratio.target else "basso"
            squilibri.append(
                f"{ratio.nome}: {computed:.2f} (target {ratio.target:.2f}, troppo {direction})"
            )

    return AnalisiBalance(
        rapporti=rapporti,
        target=target,
        squilibri=squilibri,
    )
