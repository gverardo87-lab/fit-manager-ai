"""
Entity Extractor — estrae entita' tipizzate dal testo normalizzato.

Tipi di entita':
  person_name     — 2 parole consecutive (pattern nome persona)
  date_relative   — oggi, domani, dopodomani, lunedi, martedi...
  date_absolute   — 15 marzo, 15/03, 15-03-2026
  time            — alle 18, 18:30, ore 14
  amount          — 800 euro, €200
  duration        — 1 ora, 45 minuti
  category_event  — pt, sala, corso, colloquio
  category_text   — testo libero per categoria movimento
  method_payment  — contanti, pos, bonifico
  tipo_movement   — ENTRATA/USCITA (inferito da trigger)
  metric_value    — peso 82, massa grassa 18
"""

import re
from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Any, Optional


@dataclass
class ExtractedEntity:
    """Entita' grezza estratta prima della risoluzione DB."""

    type: str
    raw: str
    value: Any
    start: int = 0
    end: int = 0


# ── Date relative ────────────────────────────────────────────

_RELATIVE_DATES: dict[str, Any] = {
    "oggi": lambda: date.today(),
    "domani": lambda: date.today() + timedelta(days=1),
    "dopodomani": lambda: date.today() + timedelta(days=2),
    "ieri": lambda: date.today() - timedelta(days=1),
}

_WEEKDAY_NAMES: dict[str, int] = {
    "lunedi": 0,
    "martedi": 1,
    "mercoledi": 2,
    "giovedi": 3,
    "venerdi": 4,
    "sabato": 5,
    "domenica": 6,
}

# ── Mesi italiani ─────────────────────────────────────────────

_MONTH_NAMES: dict[str, int] = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

# ── Time patterns ─────────────────────────────────────────────

_TIME_PATTERNS = [
    # "18:30" o "18.30" (con o senza "alle")
    re.compile(r"(?:alle?\s+)?(\d{1,2})[:\.](\d{2})(?!\s*(?:euro|€|kg|%|cm))"),
    # "alle ore 18" o "ore 14"
    re.compile(r"(?:alle?\s+)?ore?\s+(\d{1,2})\b"),
    # "alle 18" (ma non "18 euro" o "18 kg" o "18 %")
    re.compile(r"alle?\s+(\d{1,2})\b(?!\s*(?:euro|€|kg|%|cm|mmhg|bpm))"),
]

# ── Amount patterns ───────────────────────────────────────────

_AMOUNT_PATTERNS = [
    # "800 euro", "800,50 euro", "800.50 euro"
    re.compile(r"(\d+(?:\.\d{1,2})?)\s*(?:euro|€)"),
    # "€ 800", "euro 800"
    re.compile(r"(?:euro|€)\s*(\d+(?:\.\d{1,2})?)"),
]

# ── Category event ────────────────────────────────────────────

_EVENT_CATEGORIES: dict[str, str] = {
    "pt": "PT",
    "personal training": "PT",
    "personal": "PT",
    "sala": "SALA",
    "allenamento libero": "SALA",
    "corso": "CORSO",
    "colloquio": "COLLOQUIO",
    "consulenza": "COLLOQUIO",
    "personale": "PERSONALE",
}

# ── Payment methods ───────────────────────────────────────────

_PAYMENT_METHODS: dict[str, str] = {
    "contanti": "CONTANTI",
    "cash": "CONTANTI",
    "pos": "POS",
    "carta": "POS",
    "bancomat": "POS",
    "bonifico": "BONIFICO",
    "assegno": "ASSEGNO",
}

# ── Movement type triggers ────────────────────────────────────

_USCITA_TRIGGERS = {
    "spesa", "spese", "uscita", "uscite", "pago", "pagamento", "pagare",
    "pagato", "affitto", "bolletta", "utenza", "attrezzatura", "commercialista",
}
_ENTRATA_TRIGGERS = {
    "incasso", "incassi", "incassato", "entrata", "entrate",
    "ricevo", "ricevuto", "fattura",
}

# ── Metric synonyms -> catalog ID ────────────────────────────

METRIC_SYNONYMS: dict[str, int] = {
    "peso": 1,
    "peso corporeo": 1,
    "massa grassa": 3,
    "grasso": 3,
    "body fat": 3,
    "bf": 3,
    "girovita": 9,
    "vita": 9,
    "circonferenza vita": 9,
    "fianchi": 10,
    "circonferenza fianchi": 10,
    "frequenza cardiaca": 11,
    "fc riposo": 11,
    "fc": 11,
    "battiti": 11,
    "pressione sistolica": 12,
    "sistolica": 12,
    "pressione diastolica": 13,
    "diastolica": 13,
    "braccio destro": 14,
    "braccio sinistro": 15,
    "coscia destra": 16,
    "coscia sinistra": 17,
    "polpaccio destro": 18,
    "polpaccio sinistro": 19,
}

# Metric names ordinati per lunghezza DESC (greedy match)
_METRIC_NAMES_SORTED = sorted(METRIC_SYNONYMS.keys(), key=len, reverse=True)

# ── Categoria movimento (testo libero) ───────────────────────

_MOVEMENT_CATEGORIES = [
    "affitto", "bolletta", "utenza", "attrezzatura", "commercialista",
    "assicurazione", "pubblicita", "marketing", "carburante", "benzina",
    "lezione privata", "consulenza", "formazione", "manutenzione",
    "pulizia", "materiale", "integratori", "abbigliamento",
]


def extract_entities(normalized_text: str, original_text: str = "") -> list[ExtractedEntity]:
    """
    Estrae tutte le entita' dal testo. Ritorna lista ordinata per posizione.

    Args:
        normalized_text: testo gia' normalizzato (lowercase, accenti rimossi)
        original_text: testo originale (per rilevare nomi con maiuscole)
    """
    entities: list[ExtractedEntity] = []

    # ── Person names (dal testo originale se disponibile) ──
    name_source = original_text.strip() if original_text else normalized_text
    entities.extend(_extract_person_names(name_source, normalized_text))

    # ── Dates ──
    entities.extend(_extract_dates(normalized_text))

    # ── Times ──
    entities.extend(_extract_times(normalized_text))

    # ── Amounts ──
    entities.extend(_extract_amounts(normalized_text))

    # ── Event category ──
    entities.extend(_extract_event_categories(normalized_text))

    # ── Payment method ──
    entities.extend(_extract_payment_methods(normalized_text))

    # ── Movement type ──
    entities.extend(_extract_movement_type(normalized_text))

    # ── Metric values ──
    entities.extend(_extract_metric_values(normalized_text))

    # ── Movement category (testo libero) ──
    entities.extend(_extract_movement_categories(normalized_text))

    entities.sort(key=lambda e: e.start)
    return entities


# ═══════════════════════════════════════════════════════════════
# Estrattori specifici
# ═══════════════════════════════════════════════════════════════


def _extract_person_names(
    original: str, normalized: str,
) -> list[ExtractedEntity]:
    """Estrae nomi persona — 2+ parole capitalizzate consecutive."""
    entities: list[ExtractedEntity] = []

    # Pattern: 2 parole consecutive che iniziano con maiuscola
    for m in re.finditer(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", original):
        raw = m.group(0)
        # Escludi parole che sono trigger noti (es. "Massa Grassa")
        lower = raw.lower()
        if lower in METRIC_SYNONYMS or lower in _EVENT_CATEGORIES:
            continue
        entities.append(ExtractedEntity(
            type="person_name",
            raw=raw,
            value=raw.lower().split(),
            start=m.start(),
            end=m.end(),
        ))

    # Fallback: cerca nel testo normalizzato parole che non sono keyword
    if not entities:
        entities.extend(_extract_names_from_normalized(normalized))

    return entities


def _extract_names_from_normalized(normalized: str) -> list[ExtractedEntity]:
    """Fallback: cerca sequenze di 2 parole all'inizio del testo che non sono keyword."""
    words = normalized.split()
    if len(words) < 2:
        return []

    # Primo e secondo token — se non sono keyword, potrebbero essere un nome
    first_two = f"{words[0]} {words[1]}"
    all_keywords = (
        set(_RELATIVE_DATES) | set(_WEEKDAY_NAMES) | set(_MONTH_NAMES)
        | set(_EVENT_CATEGORIES) | set(_PAYMENT_METHODS)
        | _USCITA_TRIGGERS | _ENTRATA_TRIGGERS
        | {"alle", "ore", "euro", "con", "per", "del", "della"}
    )

    if words[0] not in all_keywords and words[1] not in all_keywords:
        # Potrebbe essere un nome
        if not re.match(r"^\d", words[0]) and not re.match(r"^\d", words[1]):
            return [ExtractedEntity(
                type="person_name",
                raw=first_two,
                value=first_two.split(),
                start=0,
                end=len(first_two),
            )]

    return []


def _extract_dates(text: str) -> list[ExtractedEntity]:
    """Estrae date relative e assolute."""
    entities: list[ExtractedEntity] = []

    # Relative: oggi, domani, dopodomani
    for word, fn in _RELATIVE_DATES.items():
        m = re.search(rf"\b{word}\b", text)
        if m:
            entities.append(ExtractedEntity(
                type="date",
                raw=word,
                value=fn(),
                start=m.start(),
                end=m.end(),
            ))
            return entities  # Una sola data per frase

    # Giorno della settimana: lunedi, martedi, ...
    for day_name, weekday in _WEEKDAY_NAMES.items():
        m = re.search(rf"\b{day_name}\b", text)
        if m:
            entities.append(ExtractedEntity(
                type="date",
                raw=day_name,
                value=_next_weekday(weekday),
                start=m.start(),
                end=m.end(),
            ))
            return entities

    # Assoluta: "15 marzo", "15/03", "15-03-2026"
    entities.extend(_extract_absolute_dates(text))

    return entities


def _next_weekday(target_weekday: int) -> date:
    """Prossima occorrenza del giorno della settimana (oggi incluso)."""
    today = date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def _extract_absolute_dates(text: str) -> list[ExtractedEntity]:
    """Estrae date assolute: '15 marzo', '15/03', '15/03/2026'."""
    entities: list[ExtractedEntity] = []

    # "15 marzo" o "15 mar"
    for month_name, month_num in _MONTH_NAMES.items():
        m = re.search(rf"\b(\d{{1,2}})\s+{month_name}\b", text)
        if m:
            day = int(m.group(1))
            year = date.today().year
            try:
                d = date(year, month_num, day)
                # Se la data e' gia' passata, usa anno prossimo
                if d < date.today():
                    d = date(year + 1, month_num, day)
                entities.append(ExtractedEntity(
                    type="date", raw=m.group(0), value=d,
                    start=m.start(), end=m.end(),
                ))
            except ValueError:
                pass

    # "15/03" o "15/03/2026" o "15-03-2026"
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
    if m and not entities:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else date.today().year
        if year < 100:
            year += 2000
        try:
            d = date(year, month, day)
            entities.append(ExtractedEntity(
                type="date", raw=m.group(0), value=d,
                start=m.start(), end=m.end(),
            ))
        except ValueError:
            pass

    return entities


def _extract_times(text: str) -> list[ExtractedEntity]:
    """Estrae orari: alle 18, 18:30, ore 14."""
    entities: list[ExtractedEntity] = []

    for pattern in _TIME_PATTERNS:
        for m in pattern.finditer(text):
            groups = m.groups()
            hour = int(groups[0])
            minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0

            if 0 <= hour <= 23 and 0 <= minute <= 59:
                entities.append(ExtractedEntity(
                    type="time",
                    raw=m.group(0).strip(),
                    value=time(hour, minute),
                    start=m.start(),
                    end=m.end(),
                ))
                return entities  # Un solo orario per frase

    return entities


def _extract_amounts(text: str) -> list[ExtractedEntity]:
    """Estrae importi: 800 euro, €200."""
    for pattern in _AMOUNT_PATTERNS:
        m = pattern.search(text)
        if m:
            amount = float(m.group(1))
            if amount > 0:
                return [ExtractedEntity(
                    type="amount",
                    raw=m.group(0),
                    value=amount,
                    start=m.start(),
                    end=m.end(),
                )]
    return []


def _extract_event_categories(text: str) -> list[ExtractedEntity]:
    """Estrae categoria evento: pt, sala, corso, colloquio."""
    # Ordina per lunghezza DESC (match greedy)
    for trigger, category in sorted(
        _EVENT_CATEGORIES.items(), key=lambda x: len(x[0]), reverse=True,
    ):
        m = re.search(rf"\b{re.escape(trigger)}\b", text)
        if m:
            return [ExtractedEntity(
                type="category_event",
                raw=m.group(0),
                value=category,
                start=m.start(),
                end=m.end(),
            )]
    return []


def _extract_payment_methods(text: str) -> list[ExtractedEntity]:
    """Estrae metodo pagamento: contanti, pos, bonifico."""
    for trigger, method in _PAYMENT_METHODS.items():
        m = re.search(rf"\b{re.escape(trigger)}\b", text)
        if m:
            return [ExtractedEntity(
                type="method_payment",
                raw=m.group(0),
                value=method,
                start=m.start(),
                end=m.end(),
            )]
    return []


def _extract_movement_type(text: str) -> list[ExtractedEntity]:
    """Inferisce tipo movimento: ENTRATA o USCITA."""
    for word in text.split():
        if word in _USCITA_TRIGGERS:
            return [ExtractedEntity(type="tipo_movement", raw=word, value="USCITA")]
        if word in _ENTRATA_TRIGGERS:
            return [ExtractedEntity(type="tipo_movement", raw=word, value="ENTRATA")]
    return []


def _extract_metric_values(text: str) -> list[ExtractedEntity]:
    """
    Estrae coppie metrica+valore: 'peso 82 massa grassa 18'.

    Strategia greedy left-to-right: matcha il nome metrica piu' lungo,
    poi cattura il prossimo numero.
    """
    entities: list[ExtractedEntity] = []
    remaining = text

    for metric_name in _METRIC_NAMES_SORTED:
        pattern = re.compile(
            rf"\b{re.escape(metric_name)}\s+(\d+(?:\.\d+)?)\s*(?:kg|%|cm|mmhg|bpm)?",
        )
        m = pattern.search(remaining)
        if m:
            metric_id = METRIC_SYNONYMS[metric_name]
            value = float(m.group(1))
            entities.append(ExtractedEntity(
                type="metric_value",
                raw=m.group(0),
                value={"id_metrica": metric_id, "valore": value, "nome": metric_name},
                start=m.start(),
                end=m.end(),
            ))

    # Caso speciale: "pressione 130 85" -> sistolica 130, diastolica 85
    if not any(e.value.get("id_metrica") in (12, 13) for e in entities if isinstance(e.value, dict)):
        m = re.search(r"\bpressione\s+(\d{2,3})\s+(\d{2,3})\b", text)
        if m:
            entities.append(ExtractedEntity(
                type="metric_value",
                raw=f"pressione sistolica {m.group(1)}",
                value={"id_metrica": 12, "valore": float(m.group(1)), "nome": "sistolica"},
            ))
            entities.append(ExtractedEntity(
                type="metric_value",
                raw=f"pressione diastolica {m.group(2)}",
                value={"id_metrica": 13, "valore": float(m.group(2)), "nome": "diastolica"},
            ))

    return entities


def _extract_movement_categories(text: str) -> list[ExtractedEntity]:
    """Estrae categoria movimento dal testo libero."""
    for cat in _MOVEMENT_CATEGORIES:
        m = re.search(rf"\b{re.escape(cat)}\b", text)
        if m:
            return [ExtractedEntity(
                type="category_text",
                raw=m.group(0),
                value=cat.capitalize(),
                start=m.start(),
                end=m.end(),
            )]
    return []


def get_entities_by_type(
    entities: list[ExtractedEntity], entity_type: str,
) -> list[ExtractedEntity]:
    """Filtra entita' per tipo."""
    return [e for e in entities if e.type == entity_type]


def get_first_entity(
    entities: list[ExtractedEntity], entity_type: str,
) -> Optional[ExtractedEntity]:
    """Prima entita' del tipo specificato, o None."""
    for e in entities:
        if e.type == entity_type:
            return e
    return None
