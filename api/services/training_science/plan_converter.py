# api/services/training_science/plan_converter.py
"""
Conversione WorkoutPlan (DB) → TemplatePiano (Training Science).

Replica server-side della logica di `buildTemplatePiano()` nel frontend
(SmartAnalysisPanel.tsx), necessaria per analisi batch in MyTrainer.

Pattern: ogni esercizio con pattern_movimento valido diventa uno SlotSessione.
Esercizi senza pattern (avviamento, stretching, mobilita) vengono ignorati.
"""

import logging
import re
from datetime import date

from api.models.exercise import Exercise
from api.models.workout import WorkoutExercise, WorkoutPlan, WorkoutSession

from .types import (
    Livello,
    Obiettivo,
    OrdinePriorita,
    PatternMovimento,
    RuoloSessione,
    SlotSessione,
    TemplatePiano,
    TemplateSessione,
    TipoSplit,
)

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Mapping costanti
# ════════════════════════════════════════════════════════════

_OBIETTIVO_MAP: dict[str, Obiettivo] = {
    "forza": Obiettivo.FORZA,
    "ipertrofia": Obiettivo.IPERTROFIA,
    "resistenza": Obiettivo.RESISTENZA,
    "dimagrimento": Obiettivo.DIMAGRIMENTO,
    "tonificazione": Obiettivo.TONIFICAZIONE,
    "generale": Obiettivo.IPERTROFIA,  # fallback piu' bilanciato
}

_LIVELLO_MAP: dict[str, Livello] = {
    "beginner": Livello.PRINCIPIANTE,
    "principiante": Livello.PRINCIPIANTE,
    "intermedio": Livello.INTERMEDIO,
    "avanzato": Livello.AVANZATO,
}

_VALID_PATTERNS: set[str] = {p.value for p in PatternMovimento}

_REP_RANGE_RE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
_SINGLE_REP_RE = re.compile(r"^(\d+)$")


# ════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════


def _parse_rep_range(ripetizioni: str) -> tuple[int, int]:
    """
    Parsa stringa ripetizioni in (rep_min, rep_max).

    '8-12' → (8, 12), '5' → (5, 5), '30s' → (8, 12) fallback.
    """
    text = ripetizioni.strip()

    m = _REP_RANGE_RE.match(text)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = _SINGLE_REP_RE.match(text)
    if m:
        v = int(m.group(1))
        return v, v

    # Fallback per stringhe tipo "30s", "AMRAP", ecc.
    return 8, 12


def _compute_age(data_nascita: date | None) -> int | None:
    """Calcola eta' da data di nascita."""
    if not data_nascita:
        return None
    today = date.today()
    age = today.year - data_nascita.year
    if (today.month, today.day) < (data_nascita.month, data_nascita.day):
        age -= 1
    return age


# ════════════════════════════════════════════════════════════
# Conversione principale
# ════════════════════════════════════════════════════════════


def convert_plan_to_template(
    plan: WorkoutPlan,
    sessions: list[WorkoutSession],
    exercises_by_session: dict[int, list[WorkoutExercise]],
    exercise_catalog: dict[int, Exercise],
    client_sesso: str | None = None,
    client_data_nascita: date | None = None,
) -> TemplatePiano | None:
    """
    Converte un WorkoutPlan dal DB in un TemplatePiano per analyze_plan().

    Ritorna None se il piano non ha slot analizzabili (nessun pattern valido).
    """
    obiettivo = _OBIETTIVO_MAP.get(plan.obiettivo, Obiettivo.IPERTROFIA)
    livello = _LIVELLO_MAP.get(plan.livello, Livello.INTERMEDIO)

    template_sessions: list[TemplateSessione] = []

    for sess in sessions:
        exercises = exercises_by_session.get(sess.id, [])
        slots: list[SlotSessione] = []

        for ex in exercises:
            ref = exercise_catalog.get(ex.id_esercizio)
            if not ref:
                continue
            pattern_str = ref.pattern_movimento
            if not pattern_str or pattern_str not in _VALID_PATTERNS:
                continue

            rep_min, rep_max = _parse_rep_range(ex.ripetizioni or "8-12")

            slots.append(
                SlotSessione(
                    pattern=PatternMovimento(pattern_str),
                    priorita=OrdinePriorita.COMPOUND_HEAVY,
                    serie=ex.serie,
                    rep_min=rep_min,
                    rep_max=rep_max,
                    riposo_sec=ex.tempo_riposo_sec or 90,
                    carico_kg=ex.carico_kg,
                )
            )

        template_sessions.append(
            TemplateSessione(
                nome=sess.nome_sessione,
                ruolo=RuoloSessione.FULL_BODY,
                focus=sess.focus_muscolare or "",
                slots=slots,
            )
        )

    # Almeno uno slot analizzabile?
    has_slots = any(s.slots for s in template_sessions)
    if not has_slots:
        return None

    freq = max(2, min(6, plan.sessioni_per_settimana))

    return TemplatePiano(
        frequenza=freq,
        obiettivo=obiettivo,
        livello=livello,
        tipo_split=TipoSplit.FULL_BODY,
        sessioni=template_sessions,
        note_generazione=[],
        sesso=client_sesso,
        eta=_compute_age(client_data_nascita),
    )


# ════════════════════════════════════════════════════════════
# Template effettivo (pesato per compliance reale)
# ════════════════════════════════════════════════════════════


def create_effective_template(
    template: TemplatePiano,
    session_weights: dict[str, float],
) -> TemplatePiano | None:
    """
    Crea un TemplatePiano "effettivo" dove le serie di ogni sessione
    sono scalate per la compliance reale di quella sessione.

    session_weights: {nome_sessione: compliance_ratio (0.0-1.0)}
    Se una sessione ha compliance 0%, i suoi slot hanno serie=0 e vengono esclusi.
    Se una sessione ha compliance 60%, le serie sono scalate al 60%.

    Ritorna None se il template effettivo non ha slot analizzabili.
    """
    effective_sessions: list[TemplateSessione] = []

    for sess in template.sessioni:
        weight = session_weights.get(sess.nome, 0.0)
        if weight <= 0.0:
            # Sessione mai eseguita → esclusa dal template effettivo
            continue

        scaled_slots: list[SlotSessione] = []
        for slot in sess.slots:
            scaled_serie = max(1, round(slot.serie * weight))
            scaled_slots.append(
                SlotSessione(
                    pattern=slot.pattern,
                    priorita=slot.priorita,
                    serie=scaled_serie,
                    rep_min=slot.rep_min,
                    rep_max=slot.rep_max,
                    riposo_sec=slot.riposo_sec,
                    carico_kg=slot.carico_kg,
                )
            )

        if scaled_slots:
            effective_sessions.append(
                TemplateSessione(
                    nome=sess.nome,
                    ruolo=sess.ruolo,
                    focus=sess.focus,
                    slots=scaled_slots,
                )
            )

    if not effective_sessions:
        return None

    # Frequenza effettiva: conta solo sessioni realmente eseguite
    effective_freq = max(2, min(6, len(effective_sessions)))

    return TemplatePiano(
        frequenza=effective_freq,
        obiettivo=template.obiettivo,
        livello=template.livello,
        tipo_split=template.tipo_split,
        sessioni=effective_sessions,
        note_generazione=[],
        sesso=template.sesso,
        eta=template.eta,
    )
