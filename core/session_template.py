# core/session_template.py
"""
Session Template Engine - Struttura slot-based per sessioni di allenamento.

Due modalita':
- Hardcoded: templates predefiniti per ogni split (Full Body, Upper/Lower, PPL)
- DNA-derived: template creato dagli esercizi delle schede importate

Hard cap: max 8 esercizi per sessione.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from core.error_handler import logger


MAX_EXERCISES_PER_SESSION = 8


@dataclass
class TemplateSlot:
    """Singolo slot in un template di sessione.

    Attributes:
        role: Ruolo nello schema (main_compound, secondary_compound, accessory, finisher)
        movement_pattern: Pattern richiesto (push_h, pull_v, squat, hinge, core, any...)
        target_muscles: Muscoli target per questo slot
        required: Se False, lo slot puo' essere omesso se non ci sono candidati
        sets: Numero serie (dal DNA, se disponibile)
        reps: Range ripetizioni (dal DNA, se disponibile)
    """
    role: str
    movement_pattern: str
    target_muscles: List[str]
    required: bool = True
    sets: Optional[int] = None
    reps: Optional[str] = None


@dataclass
class SessionTemplate:
    """Template per una singola sessione di allenamento."""
    name: str
    slots: List[TemplateSlot] = field(default_factory=list)

    def __post_init__(self):
        # Enforce hard cap
        if len(self.slots) > MAX_EXERCISES_PER_SESSION:
            logger.warning(
                f"SessionTemplate '{self.name}': {len(self.slots)} slots "
                f"troncati a {MAX_EXERCISES_PER_SESSION}"
            )
            self.slots = self.slots[:MAX_EXERCISES_PER_SESSION]

    # ─────────────── STRADA A: Templates hardcoded ───────────────

    @classmethod
    def full_body_a(cls) -> 'SessionTemplate':
        """Full body A: squat focus + push orizzontale + pull orizzontale + accessori."""
        return cls(name="Full Body A", slots=[
            TemplateSlot('main_compound', 'squat', ['quadriceps', 'glutes']),
            TemplateSlot('main_compound', 'push_h', ['chest', 'triceps']),
            TemplateSlot('secondary_compound', 'pull_h', ['back', 'biceps']),
            TemplateSlot('accessory', 'push_v', ['shoulders']),
            TemplateSlot('accessory', 'hinge', ['hamstrings', 'glutes']),
            TemplateSlot('finisher', 'core', ['core'], required=False),
        ])

    @classmethod
    def full_body_b(cls) -> 'SessionTemplate':
        """Full body B: hinge focus + push verticale + pull verticale + accessori."""
        return cls(name="Full Body B", slots=[
            TemplateSlot('main_compound', 'hinge', ['hamstrings', 'glutes', 'back']),
            TemplateSlot('main_compound', 'push_v', ['shoulders', 'triceps']),
            TemplateSlot('secondary_compound', 'pull_v', ['back', 'lats']),
            TemplateSlot('accessory', 'squat', ['quadriceps']),
            TemplateSlot('accessory', 'pull_h', ['back', 'biceps']),
            TemplateSlot('finisher', 'core', ['core'], required=False),
        ])

    @classmethod
    def full_body_c(cls) -> 'SessionTemplate':
        """Full body C: varianti + unilaterali + carry."""
        return cls(name="Full Body C", slots=[
            TemplateSlot('main_compound', 'squat', ['quadriceps', 'glutes']),
            TemplateSlot('main_compound', 'pull_h', ['back', 'lats']),
            TemplateSlot('secondary_compound', 'push_h', ['chest', 'triceps']),
            TemplateSlot('accessory', 'hinge', ['hamstrings', 'glutes']),
            TemplateSlot('accessory', 'push_v', ['shoulders']),
            TemplateSlot('finisher', 'carry', ['core', 'forearms'], required=False),
        ])

    @classmethod
    def upper_push(cls) -> 'SessionTemplate':
        """Upper body push dominant."""
        return cls(name="Upper Push", slots=[
            TemplateSlot('main_compound', 'push_h', ['chest', 'triceps']),
            TemplateSlot('main_compound', 'push_v', ['shoulders', 'triceps']),
            TemplateSlot('secondary_compound', 'pull_h', ['back', 'biceps']),
            TemplateSlot('accessory', 'push_h', ['chest']),
            TemplateSlot('accessory', 'push_v', ['shoulders']),
            TemplateSlot('accessory', 'pull_h', ['biceps']),
        ])

    @classmethod
    def upper_pull(cls) -> 'SessionTemplate':
        """Upper body pull dominant."""
        return cls(name="Upper Pull", slots=[
            TemplateSlot('main_compound', 'pull_v', ['back', 'lats']),
            TemplateSlot('main_compound', 'pull_h', ['back', 'biceps']),
            TemplateSlot('secondary_compound', 'push_h', ['chest', 'triceps']),
            TemplateSlot('accessory', 'pull_v', ['lats']),
            TemplateSlot('accessory', 'pull_h', ['biceps']),
            TemplateSlot('accessory', 'push_v', ['shoulders']),
        ])

    @classmethod
    def lower_squat(cls) -> 'SessionTemplate':
        """Lower body squat dominant."""
        return cls(name="Lower Squat", slots=[
            TemplateSlot('main_compound', 'squat', ['quadriceps', 'glutes']),
            TemplateSlot('secondary_compound', 'squat', ['quadriceps']),
            TemplateSlot('accessory', 'hinge', ['hamstrings', 'glutes']),
            TemplateSlot('accessory', 'squat', ['quadriceps']),
            TemplateSlot('accessory', 'hinge', ['calves']),
            TemplateSlot('finisher', 'core', ['core'], required=False),
        ])

    @classmethod
    def lower_hinge(cls) -> 'SessionTemplate':
        """Lower body hinge dominant."""
        return cls(name="Lower Hinge", slots=[
            TemplateSlot('main_compound', 'hinge', ['hamstrings', 'glutes']),
            TemplateSlot('secondary_compound', 'hinge', ['glutes']),
            TemplateSlot('accessory', 'squat', ['quadriceps']),
            TemplateSlot('accessory', 'hinge', ['hamstrings']),
            TemplateSlot('accessory', 'hinge', ['calves']),
            TemplateSlot('finisher', 'core', ['core'], required=False),
        ])

    @classmethod
    def push_day(cls) -> 'SessionTemplate':
        """Push day per PPL split."""
        return cls(name="Push", slots=[
            TemplateSlot('main_compound', 'push_h', ['chest', 'triceps']),
            TemplateSlot('secondary_compound', 'push_v', ['shoulders', 'triceps']),
            TemplateSlot('accessory', 'push_h', ['chest']),
            TemplateSlot('accessory', 'push_v', ['shoulders']),
            TemplateSlot('accessory', 'push_h', ['triceps']),
            TemplateSlot('finisher', 'push_v', ['triceps'], required=False),
        ])

    @classmethod
    def pull_day(cls) -> 'SessionTemplate':
        """Pull day per PPL split."""
        return cls(name="Pull", slots=[
            TemplateSlot('main_compound', 'pull_v', ['back', 'lats']),
            TemplateSlot('secondary_compound', 'pull_h', ['back', 'biceps']),
            TemplateSlot('accessory', 'pull_v', ['lats']),
            TemplateSlot('accessory', 'pull_h', ['back']),
            TemplateSlot('accessory', 'pull_h', ['biceps']),
            TemplateSlot('finisher', 'pull_h', ['biceps'], required=False),
        ])

    @classmethod
    def legs_day(cls) -> 'SessionTemplate':
        """Legs day per PPL split."""
        return cls(name="Legs", slots=[
            TemplateSlot('main_compound', 'squat', ['quadriceps', 'glutes']),
            TemplateSlot('secondary_compound', 'hinge', ['hamstrings', 'glutes']),
            TemplateSlot('accessory', 'squat', ['quadriceps']),
            TemplateSlot('accessory', 'hinge', ['hamstrings']),
            TemplateSlot('accessory', 'hinge', ['calves']),
            TemplateSlot('finisher', 'core', ['core'], required=False),
        ])

    # ─────────────── STRADA B: Template da DNA ───────────────

    @classmethod
    def from_dna_card(cls, card_exercises: List[Dict], card_metadata: Dict) -> 'SessionTemplate':
        """Crea template dagli esercizi di una scheda importata.

        Analizza gli esercizi della scheda, identifica i movement_pattern,
        e crea slot corrispondenti. Cap a MAX_EXERCISES_PER_SESSION.
        I set/rep del trainer vengono preservati negli slot.

        Args:
            card_exercises: Lista di esercizi parsati dalla scheda
            card_metadata: Metadati della scheda (day_name, detected_goal, ecc.)
        """
        slots = []
        for ex in card_exercises[:MAX_EXERCISES_PER_SESSION]:
            pattern = _infer_pattern(ex)
            muscles = ex.get('primary_muscles', [])
            if isinstance(muscles, str):
                muscles = [muscles]

            # Determina ruolo dallo slot position
            if len(slots) < 2:
                role = 'main_compound'
            elif len(slots) < 4:
                role = 'secondary_compound' if ex.get('category') == 'compound' else 'accessory'
            else:
                role = 'accessory'

            # Estrai set/rep dal DNA
            sets_val = ex.get('sets')
            reps_val = ex.get('reps')
            if isinstance(sets_val, str):
                try:
                    sets_val = int(sets_val)
                except (ValueError, TypeError):
                    sets_val = None

            slots.append(TemplateSlot(
                role=role,
                movement_pattern=pattern,
                target_muscles=muscles if muscles else ['core'],
                sets=sets_val,
                reps=str(reps_val) if reps_val else None,
            ))

        day_name = card_metadata.get('day_name', 'DNA Session')
        return cls(name=day_name, slots=slots)


def _infer_pattern(exercise: Dict) -> str:
    """Inferisce movement_pattern da un esercizio parsato.

    Cerca prima il campo esplicito, poi inferisce dal nome/muscoli.
    """
    # Campo esplicito
    pattern = exercise.get('movement_pattern', '').lower()
    valid = {'push_h', 'push_v', 'pull_h', 'pull_v', 'squat', 'hinge', 'carry', 'rotation', 'core'}
    if pattern in valid:
        return pattern

    # Mappa pattern legacy
    legacy_map = {'push': 'push_h', 'pull': 'pull_h'}
    if pattern in legacy_map:
        return legacy_map[pattern]

    # Inferisci dal nome
    name = exercise.get('name', '').lower()
    canonical = exercise.get('canonical_name', '').lower()
    combined = f"{name} {canonical}"

    if any(w in combined for w in ['squat', 'lunge', 'leg press', 'step up']):
        return 'squat'
    if any(w in combined for w in ['deadlift', 'rdl', 'hip thrust', 'swing', 'good morning', 'leg curl']):
        return 'hinge'
    if any(w in combined for w in ['bench', 'push-up', 'pushup', 'fly', 'pec']):
        return 'push_h'
    if any(w in combined for w in ['overhead press', 'shoulder press', 'lateral raise', 'dip', 'military']):
        return 'push_v'
    if any(w in combined for w in ['pull-up', 'pullup', 'chin-up', 'lat pull', 'pulldown']):
        return 'pull_v'
    if any(w in combined for w in ['row', 'curl', 'face pull']):
        return 'pull_h'
    if any(w in combined for w in ['plank', 'crunch', 'ab ', 'dead bug']):
        return 'core'
    if any(w in combined for w in ['carry', 'farmer', 'walk']):
        return 'carry'
    if any(w in combined for w in ['twist', 'rotation', 'woodchop']):
        return 'rotation'

    return 'push_h'  # Default


class WeekPlanner:
    """Assegna templates ai giorni della settimana."""

    def plan_week_from_archive(self, sessions_per_week: int,
                                level: str = 'intermediate') -> List[SessionTemplate]:
        """STRADA A: templates hardcoded in base a sessioni/settimana.

        Returns:
            Lista di SessionTemplate (uno per sessione della settimana)
        """
        if sessions_per_week <= 2:
            templates = [SessionTemplate.full_body_a(), SessionTemplate.full_body_b()]
            return templates[:sessions_per_week]

        elif sessions_per_week == 3:
            return [
                SessionTemplate.full_body_a(),
                SessionTemplate.full_body_b(),
                SessionTemplate.full_body_c(),
            ]

        elif sessions_per_week == 4:
            return [
                SessionTemplate.upper_push(),
                SessionTemplate.lower_squat(),
                SessionTemplate.upper_pull(),
                SessionTemplate.lower_hinge(),
            ]

        else:  # 5-6
            base = [
                SessionTemplate.push_day(),
                SessionTemplate.pull_day(),
                SessionTemplate.legs_day(),
                SessionTemplate.push_day(),
                SessionTemplate.pull_day(),
                SessionTemplate.legs_day(),
            ]
            return base[:sessions_per_week]

    def plan_week_from_dna(self, dna_cards: List[Dict]) -> List[SessionTemplate]:
        """STRADA B: crea templates dalle schede DNA.

        Args:
            dna_cards: Lista di dict con chiavi 'exercises' e 'metadata'
        """
        templates = []
        for card in dna_cards:
            exercises = card.get('exercises', [])
            metadata = card.get('metadata', {})
            if exercises:
                template = SessionTemplate.from_dna_card(exercises, metadata)
                templates.append(template)
        return templates

    def plan_week_combined(self, sessions_per_week: int, level: str,
                           dna_cards: List[Dict]) -> List[SessionTemplate]:
        """STRADA C: struttura DNA, fallback archivio per sessioni mancanti.

        Usa le schede DNA come base. Se non coprono tutte le sessioni
        della settimana, completa con templates hardcoded.
        """
        dna_templates = self.plan_week_from_dna(dna_cards)

        if len(dna_templates) >= sessions_per_week:
            return dna_templates[:sessions_per_week]

        # Completa con templates hardcoded
        remaining = sessions_per_week - len(dna_templates)
        hardcoded = self.plan_week_from_archive(remaining, level)
        return dna_templates + hardcoded
