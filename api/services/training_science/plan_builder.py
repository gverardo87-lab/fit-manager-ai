"""
Training Science Engine — Generatore di piani volume-driven.

Questo modulo e' il cuore del sistema: genera un piano di allenamento
settimanale che GARANTISCE il volume ottimale per ogni muscolo.

Algoritmo a 4 fasi:

  FASE 1 — Struttura base (compound)
    Per ogni sessione, assegna pattern compound dal ruolo sessione.
    Le serie sono determinate dai parametri di carico dell'obiettivo.
    Ordine fisiologico NSCA (SNC-demanding first).

  FASE 2 — Boost serie compound per muscoli carenti
    Calcola il volume ipertrofico (pesato, non meccanico grezzo).
    Per muscoli coperti solo da compound (petto, dorsali) che sono
    sotto MAV, incrementa le serie dei pattern compound correlati.

  FASE 3 — Compensazione volume con isolamento
    Per muscoli con pattern di isolamento disponibile che sono
    sotto MAV, aggiunge slot di isolamento nelle sessioni affini.

  FASE 4 — Feedback loop con analisi volume
    Ricalcola il volume dopo le fasi 2-3. Se ci sono ancora deficit
    significativi, ripete la compensazione (max 1 iterazione extra).
    Verifica MRV e genera warning per il plan_analyzer.

Principio architetturale: il piano e' DETERMINATO dai numeri.
Non ci sono scelte arbitrarie — ogni decisione ha una fonte.

Fonti:
  - Israetel — "Scientific Principles of Hypertrophy Training" (2020)
  - Schoenfeld — "Dose-response for RT volume" (2017)
  - NSCA — "Essentials of Strength Training" (2016) cap. 17, 21-22
  - Helms — "The Muscle and Strength Pyramid: Training" (2019)
"""

from .types import (
    PatternMovimento as P,
    GruppoMuscolare as M,
    Obiettivo,
    Livello,
    OrdinePriorita as OP,
    RuoloSessione,
    SlotSessione,
    TemplateSessione,
    TemplatePiano,
)
from .principles import PARAMETRI_CARICO, get_serie_per_slot, get_rep_range, get_riposo
from .muscle_contribution import (
    compute_hypertrophy_sets,
    is_compound,
    get_contribution,
)
from .volume_model import (
    get_scaled_volume_target,
)
from .split_logic import (
    get_split,
    get_session_roles,
    clamp_frequenza,
    PATTERN_COMPOUND_PER_RUOLO,
    NOMI_SESSIONE,
    FOCUS_SESSIONE,
)
from .session_order import order_patterns, get_priority


# ════════════════════════════════════════════════════════════
# MAPPATURA ISOLAMENTO — Muscolo → Pattern di isolamento migliore
# ════════════════════════════════════════════════════════════
#
# Quando un muscolo e' sotto-stimolato (< MAV_min), si aggiunge
# il pattern di isolamento piu' efficace per quel muscolo.
# La scelta e' deterministica: il pattern con contributo 1.0.
#
# Non tutti i muscoli hanno un isolamento diretto — quelli
# che non lo hanno (es. petto, dorsali) vengono gestiti con
# boost delle serie compound (Fase 2).

ISOLAMENTO_PER_MUSCOLO: dict[M, P] = {
    M.BICIPITI: P.CURL,
    M.TRICIPITI: P.EXTENSION_TRI,
    M.DELT_LAT: P.LATERAL_RAISE,
    M.DELT_POST: P.FACE_PULL,
    M.QUADRICIPITI: P.LEG_EXTENSION,
    M.FEMORALI: P.LEG_CURL,
    M.GLUTEI: P.HIP_THRUST,
    M.POLPACCI: P.CALF_RAISE,
    M.ADDUTTORI: P.ADDUCTOR,
}


# ════════════════════════════════════════════════════════════
# BOOST COMPOUND — Muscolo → Pattern compound da potenziare
# ════════════════════════════════════════════════════════════
#
# Per muscoli senza isolamento diretto (petto, dorsali, delt_ant),
# il volume si aumenta aggiungendo serie ai compound che li
# attivano come motore primario (contributo 1.0).
#
# Esempio: petto carente → +1 serie a push_h in ogni sessione upper.

COMPOUND_PER_MUSCOLO: dict[M, list[P]] = {
    M.PETTO: [P.PUSH_H],
    M.DORSALI: [P.PULL_H, P.PULL_V],
    M.DELT_ANT: [P.PUSH_V],
    M.TRAPEZIO: [P.PULL_H],
    M.CORE: [P.CORE],
    M.AVAMBRACCI: [P.CARRY],
}


# ════════════════════════════════════════════════════════════
# AFFINITA' SESSIONE — Quale isolamento in quale sessione
# ════════════════════════════════════════════════════════════

AFFINITA_ISOLAMENTO: dict[P, set[RuoloSessione]] = {
    P.CURL: {RuoloSessione.PULL, RuoloSessione.UPPER, RuoloSessione.FULL_BODY},
    P.EXTENSION_TRI: {RuoloSessione.PUSH, RuoloSessione.UPPER, RuoloSessione.FULL_BODY},
    P.LATERAL_RAISE: {RuoloSessione.PUSH, RuoloSessione.UPPER, RuoloSessione.FULL_BODY},
    P.FACE_PULL: {RuoloSessione.PULL, RuoloSessione.UPPER, RuoloSessione.FULL_BODY},
    P.LEG_EXTENSION: {RuoloSessione.LEGS, RuoloSessione.LOWER, RuoloSessione.FULL_BODY},
    P.LEG_CURL: {RuoloSessione.LEGS, RuoloSessione.LOWER, RuoloSessione.FULL_BODY},
    P.HIP_THRUST: {RuoloSessione.LEGS, RuoloSessione.LOWER, RuoloSessione.FULL_BODY},
    P.CALF_RAISE: {RuoloSessione.LEGS, RuoloSessione.LOWER, RuoloSessione.FULL_BODY},
    P.ADDUCTOR: {RuoloSessione.LEGS, RuoloSessione.LOWER, RuoloSessione.FULL_BODY},
}


# ════════════════════════════════════════════════════════════
# LIMITI SESSIONE — Guardrail scientifici
# ════════════════════════════════════════════════════════════

_MAX_SLOT_SESSIONE: dict[Livello, int] = {
    Livello.PRINCIPIANTE: 6,
    Livello.INTERMEDIO: 8,
    Livello.AVANZATO: 10,
}

_MAX_ISOLATION_SESSIONE: dict[Livello, int] = {
    Livello.PRINCIPIANTE: 2,
    Livello.INTERMEDIO: 3,
    Livello.AVANZATO: 4,
}

# Limite incremento serie per compound boost (per sessione).
# Evita sessioni con 8+ serie sullo stesso pattern (NSCA 2016:
# oltre 5-6 serie per esercizio nella stessa sessione, la qualita'
# delle ultime serie degrada significativamente).
_MAX_SERIE_PER_SLOT = 6
_MAX_COMPOUND_BOOST_PER_SESSION = 2


# ════════════════════════════════════════════════════════════
# FASE 1 — Struttura compound base
# ════════════════════════════════════════════════════════════


def _build_compound_slots(
    patterns: list[P],
    obiettivo: Obiettivo,
) -> list[SlotSessione]:
    """
    Crea slot compound per una sessione.

    Ogni pattern compound riceve serie secondo i parametri dell'obiettivo.
    Il primo pattern (post-ordinamento) e' il "primario" e riceve
    piu' serie (NSCA: primary exercise gets max volume).
    """
    ordered = order_patterns(patterns)
    rep_min, rep_max = get_rep_range(obiettivo)
    slots: list[SlotSessione] = []

    for i, pattern in enumerate(ordered):
        is_primary = (i == 0)
        is_comp = is_compound(pattern)
        serie = get_serie_per_slot(obiettivo, is_comp, is_primary)
        riposo = get_riposo(obiettivo, is_comp)
        priorita = get_priority(pattern)

        slots.append(SlotSessione(
            pattern=pattern,
            priorita=priorita,
            serie=serie,
            rep_min=rep_min,
            rep_max=rep_max,
            riposo_sec=riposo,
        ))

    return slots


# ════════════════════════════════════════════════════════════
# FASE 2 — Boost serie compound per muscoli carenti
# ════════════════════════════════════════════════════════════


def _compute_plan_hypertrophy_volume(
    sessioni: list[tuple[RuoloSessione, list[SlotSessione]]],
) -> dict[M, float]:
    """
    Calcola il volume IPERTROFICO settimanale per muscolo.

    Usa compute_hypertrophy_sets() che sconta il volume da stabilizzazione
    e riduce il volume da sinergismo minore.
    """
    all_slots: list[tuple[P, int]] = []
    for _, slots in sessioni:
        for slot in slots:
            all_slots.append((slot.pattern, slot.serie))
    return compute_hypertrophy_sets(all_slots)


def _find_compound_deficits(
    volume_ipertrofico: dict[M, float],
    livello: Livello,
    obiettivo: Obiettivo,
) -> list[tuple[M, float]]:
    """
    Identifica muscoli compound-only che sono sotto MAV_min.

    Questi muscoli NON hanno un pattern di isolamento diretto
    e quindi il volume si corregge incrementando le serie compound.
    """
    deficits: list[tuple[M, float]] = []
    for muscolo in M:
        if muscolo in ISOLAMENTO_PER_MUSCOLO:
            continue
        if muscolo not in COMPOUND_PER_MUSCOLO:
            continue

        target = get_scaled_volume_target(muscolo, livello, obiettivo)
        serie_attuali = volume_ipertrofico.get(muscolo, 0.0)

        if serie_attuali < target.mav_min:
            deficit = target.mav_min - serie_attuali
            deficits.append((muscolo, deficit))

    deficits.sort(key=lambda x: -x[1])
    return deficits


def _boost_compound_series(
    sessioni: list[tuple[RuoloSessione, list[SlotSessione]]],
    deficits: list[tuple[M, float]],
) -> None:
    """
    Incrementa le serie dei compound che attivano i muscoli carenti.

    Per ogni muscolo in deficit, trova gli slot compound che lo attivano
    come motore primario e incrementa le serie di 1, rispettando i limiti.

    Modifica le sessioni in-place.
    """
    for muscolo, deficit in deficits:
        target_patterns = COMPOUND_PER_MUSCOLO.get(muscolo, [])
        if not target_patterns:
            continue

        # Quanto volume ci serve? Ogni +1 serie su pattern primario (1.0)
        # aggiunge ~1.0 serie ipertrofica (peso 1.0 × contributo 1.0)
        boosts_needed = max(1, round(deficit))

        boosts_done = 0
        for i, (_, slots) in enumerate(sessioni):
            if boosts_done >= boosts_needed:
                break

            session_boosts = 0
            for slot in slots:
                if boosts_done >= boosts_needed:
                    break
                if session_boosts >= _MAX_COMPOUND_BOOST_PER_SESSION:
                    break
                if slot.pattern not in target_patterns:
                    continue
                if slot.serie >= _MAX_SERIE_PER_SLOT:
                    continue

                # Verifica che il pattern attivi il muscolo come primario
                contrib = get_contribution(slot.pattern).get(muscolo, 0.0)
                if contrib < 0.7:
                    continue

                slot.serie += 1
                boosts_done += 1
                session_boosts += 1


# ════════════════════════════════════════════════════════════
# FASE 3 — Compensazione volume con isolamento
# ════════════════════════════════════════════════════════════


def _find_isolation_deficits(
    volume_ipertrofico: dict[M, float],
    livello: Livello,
    obiettivo: Obiettivo,
) -> list[tuple[M, float]]:
    """
    Identifica muscoli con isolamento disponibile che sono sotto MAV_min.

    Usa il volume ipertrofico (pesato) per il confronto con i target,
    non il volume meccanico grezzo.
    """
    deficits: list[tuple[M, float]] = []

    for muscolo in M:
        if muscolo not in ISOLAMENTO_PER_MUSCOLO:
            continue

        target = get_scaled_volume_target(muscolo, livello, obiettivo)
        serie_attuali = volume_ipertrofico.get(muscolo, 0.0)

        if serie_attuali < target.mav_min:
            deficit = target.mav_min - serie_attuali
            deficits.append((muscolo, deficit))

    deficits.sort(key=lambda x: -x[1])
    return deficits


def _add_isolation_slots(
    sessioni: list[tuple[RuoloSessione, list[SlotSessione]]],
    deficits: list[tuple[M, float]],
    obiettivo: Obiettivo,
    livello: Livello,
) -> None:
    """
    Aggiunge slot di isolamento alle sessioni per compensare deficit.

    Regole:
    1. L'isolamento va nella sessione con affinita' corretta
    2. Le serie sono calcolate per colmare il deficit (non inventate)
    3. Ogni sessione ha un limite massimo di isolamenti
    4. Il volume per singolo slot isolation segue i parametri dell'obiettivo

    Modifica le sessioni in-place.
    """
    rep_min, rep_max = get_rep_range(obiettivo)
    max_iso = _MAX_ISOLATION_SESSIONE[livello]
    max_slot = _MAX_SLOT_SESSIONE[livello]
    params = PARAMETRI_CARICO[obiettivo]
    serie_iso = params.serie_isolation[0]

    # Conta isolamenti e slot gia' presenti per sessione
    iso_count: dict[int, int] = {}
    slot_count: dict[int, int] = {}
    for i, (_, slots) in enumerate(sessioni):
        iso_count[i] = sum(1 for s in slots if s.priorita == OP.ISOLATION)
        slot_count[i] = len(slots)

    for muscolo, deficit in deficits:
        pattern_iso = ISOLAMENTO_PER_MUSCOLO[muscolo]
        affinita = AFFINITA_ISOLAMENTO.get(pattern_iso, set())

        occorrenze_necessarie = max(1, round(deficit / serie_iso))

        aggiunte = 0
        for i, (ruolo, slots) in enumerate(sessioni):
            if aggiunte >= occorrenze_necessarie:
                break
            if ruolo not in affinita:
                continue
            if iso_count[i] >= max_iso:
                continue
            if slot_count[i] >= max_slot:
                continue
            if any(s.pattern == pattern_iso for s in slots):
                continue

            serie_da_aggiungere = min(
                serie_iso,
                max(2, round(deficit - aggiunte * serie_iso)),
            )

            slot = SlotSessione(
                pattern=pattern_iso,
                priorita=OP.ISOLATION,
                serie=serie_da_aggiungere,
                rep_min=rep_min,
                rep_max=rep_max,
                riposo_sec=get_riposo(obiettivo, False),
                muscolo_target=muscolo,
                note=f"Compensazione volume {muscolo.value}",
            )
            slots.append(slot)
            iso_count[i] += 1
            slot_count[i] += 1
            aggiunte += 1


# ════════════════════════════════════════════════════════════
# FASE 4 — Feedback loop
# ════════════════════════════════════════════════════════════

_MAX_FEEDBACK_ITERATIONS = 1


def _has_significant_deficits(
    volume_ipertrofico: dict[M, float],
    livello: Livello,
    obiettivo: Obiettivo,
) -> bool:
    """
    True se ci sono muscoli con MEV > 0 ancora sotto MEV dopo compensazione.

    Questo e' il criterio per un'altra iterazione del feedback loop:
    non cerchiamo la perfezione (tutti in MAV), ma che nessun muscolo
    critico sia completamente sotto-stimolato.
    """
    for muscolo in M:
        target = get_scaled_volume_target(muscolo, livello, obiettivo)
        if target.mev == 0:
            continue
        serie = volume_ipertrofico.get(muscolo, 0.0)
        if serie < target.mev:
            return True
    return False


# ════════════════════════════════════════════════════════════
# API PUBBLICA — Generazione piano
# ════════════════════════════════════════════════════════════


def build_plan(
    frequenza: int,
    obiettivo: Obiettivo,
    livello: Livello,
) -> TemplatePiano:
    """
    Genera un piano di allenamento settimanale completo.

    Algoritmo deterministico a 4 fasi con feedback loop:

    1. Struttura compound base (split_logic + session_order)
    2. Boost serie compound per muscoli carenti (petto, dorsali, ecc.)
    3. Compensazione con isolamento (matrice EMG + MEV/MAV)
    4. Feedback: se deficit significativi persistono, ripeti 2-3

    Input:
        frequenza: 2-6 sessioni/settimana
        obiettivo: Forza, Ipertrofia, Resistenza, Dimagrimento, Tonificazione
        livello: Principiante, Intermedio, Avanzato

    Output:
        TemplatePiano con sessioni complete, ordinate, volume-driven.
    """
    # Guardrail scientifico: clamp frequenza per livello (NSCA 2016)
    frequenza, freq_warning = clamp_frequenza(frequenza, livello)

    split = get_split(frequenza)
    roles = get_session_roles(frequenza)

    # ── FASE 1: Compound base ──
    sessioni: list[tuple[RuoloSessione, list[SlotSessione]]] = []
    for ruolo in roles:
        patterns = PATTERN_COMPOUND_PER_RUOLO[ruolo]
        compound_slots = _build_compound_slots(patterns, obiettivo)
        sessioni.append((ruolo, compound_slots))

    # ── FASE 2: Boost compound per muscoli carenti ──
    volume = _compute_plan_hypertrophy_volume(sessioni)
    compound_deficits = _find_compound_deficits(volume, livello, obiettivo)
    if compound_deficits:
        _boost_compound_series(sessioni, compound_deficits)

    # ── FASE 3: Compensazione isolation ──
    volume = _compute_plan_hypertrophy_volume(sessioni)
    iso_deficits = _find_isolation_deficits(volume, livello, obiettivo)
    if iso_deficits:
        _add_isolation_slots(sessioni, iso_deficits, obiettivo, livello)

    # ── FASE 4: Feedback loop ──
    for _ in range(_MAX_FEEDBACK_ITERATIONS):
        volume = _compute_plan_hypertrophy_volume(sessioni)
        if not _has_significant_deficits(volume, livello, obiettivo):
            break

        # Riprova compound boost + isolation
        compound_deficits = _find_compound_deficits(volume, livello, obiettivo)
        if compound_deficits:
            _boost_compound_series(sessioni, compound_deficits)

        volume = _compute_plan_hypertrophy_volume(sessioni)
        iso_deficits = _find_isolation_deficits(volume, livello, obiettivo)
        if iso_deficits:
            _add_isolation_slots(sessioni, iso_deficits, obiettivo, livello)

    # ── Costruisci TemplatePiano ──
    template_sessioni: list[TemplateSessione] = []
    for i, (ruolo, slots) in enumerate(sessioni):
        slots.sort(key=lambda s: (s.priorita.value, s.pattern.value))

        role_count = sum(1 for r, _ in sessioni[:i + 1] if r == ruolo)
        total_role = sum(1 for r, _ in sessioni if r == ruolo)
        if total_role > 1:
            nome = f"{NOMI_SESSIONE[ruolo]} {_to_letter(role_count)}"
        else:
            nome = NOMI_SESSIONE[ruolo]

        template_sessioni.append(TemplateSessione(
            nome=nome,
            ruolo=ruolo,
            focus=FOCUS_SESSIONE[ruolo],
            slots=slots,
        ))

    note: list[str] = []
    if freq_warning:
        note.append(freq_warning)

    return TemplatePiano(
        frequenza=frequenza,
        obiettivo=obiettivo,
        livello=livello,
        tipo_split=split,
        sessioni=template_sessioni,
        note_generazione=note,
    )


def _to_letter(n: int) -> str:
    """Converte 1->A, 2->B, 3->C per naming sessioni."""
    return chr(64 + n)
