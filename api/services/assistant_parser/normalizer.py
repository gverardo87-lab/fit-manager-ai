"""
Normalizer — prepara testo italiano per il pattern matching.

Steps:
  1. Strip + lowercase
  2. Normalizza accenti italiani (e' -> e, a' -> a)
  3. Collapse whitespace
  4. Separa unita' attaccate ai numeri (80kg -> 80 kg)
  5. Normalizza formato numeri italiano (1.200,50 -> 1200.50)
  6. Espandi abbreviazioni giorni (lun -> lunedi)
"""

import re
import unicodedata


_ACCENT_MAP = {
    "a'": "a\u0300",
    "e'": "e\u0300",
    "i'": "i\u0300",
    "o'": "o\u0300",
    "u'": "u\u0300",
}

_DAY_ABBREVIATIONS = {
    "lun": "lunedi",
    "mar": "martedi",
    "merc": "mercoledi",
    "giov": "giovedi",
    "ven": "venerdi",
    "sab": "sabato",
    "dom": "domenica",
}

# Unita' da separare: 80kg -> 80 kg, 18% -> 18 %, 130mmhg -> 130 mmhg
_UNIT_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|cm|%|mmhg|bpm|euro|€)", re.IGNORECASE)

# Numero italiano con separatore migliaia: 1.200 o 1.200,50
_ITALIAN_NUMBER = re.compile(r"\b(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?)\b")

# Numero con virgola decimale senza migliaia: 82,5
_DECIMAL_COMMA = re.compile(r"\b(\d+),(\d{1,2})\b")


def normalize(text: str) -> str:
    """Normalizza testo italiano per il parser."""
    if not text:
        return ""

    result = text.strip()

    # 1. Accenti apostrofo -> Unicode composto, poi strip diacritici
    for pattern, replacement in _ACCENT_MAP.items():
        result = result.replace(pattern, replacement)

    # Rimuovi diacritici Unicode (NFD decompose + strip combining marks)
    result = unicodedata.normalize("NFD", result)
    result = "".join(c for c in result if unicodedata.category(c) != "Mn")

    # 2. Lowercase
    result = result.lower()

    # 3. Numeri italiani: 1.200,50 -> 1200.50 (PRIMA di collassare spazi)
    def _fix_italian_number(m: re.Match[str]) -> str:
        num = m.group(1).replace(".", "").replace(",", ".")
        return num

    result = _ITALIAN_NUMBER.sub(_fix_italian_number, result)

    # Virgola decimale semplice: 82,5 -> 82.5
    result = _DECIMAL_COMMA.sub(r"\1.\2", result)

    # 4. Separa unita' attaccate: 80kg -> 80 kg
    result = _UNIT_PATTERN.sub(r"\1 \2", result)

    # 5. Collapse whitespace
    result = re.sub(r"\s+", " ", result).strip()

    # 6. Espandi abbreviazioni giorni (solo parola intera)
    for abbr, full in _DAY_ABBREVIATIONS.items():
        result = re.sub(rf"\b{abbr}\b", full, result)

    return result
