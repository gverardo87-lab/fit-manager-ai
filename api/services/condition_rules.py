# api/services/condition_rules.py
"""
Regole condivise per keyword → condition_id mapping.

Usato da:
  - api/services/safety_engine.py (runtime: anamnesi → condizioni rilevanti)
  - tools/admin_scripts/populate_conditions.py (batch: esercizi → mapping)

Le keyword sono in italiano, lowercase. Il matching e' case-insensitive substring.
I condition_id corrispondono alla tabella condizioni_mediche (30 condizioni).
"""

# ═══════════════════════════════════════════════════════════════
# KEYWORD → CONDITION ID
# ═══════════════════════════════════════════════════════════════
# Ogni entry: (keyword_list, condition_id)
# Basta che UNA keyword sia presente nella stringa per matchare.

ANAMNESI_KEYWORD_RULES: list[tuple[list[str], int]] = [
    # ── SCHIENA / LOMBARE ──
    (["ernia", "hernia discale"], 1),
    (["lombalgia", "mal di schiena", "lombare"], 1),
    (["scoliosi"], 3),
    (["stenosi spinale"], 4),
    (["spondilolistesi"], 5),

    # ── CERVICALE / COLLO ──
    (["cervicale", "collo", "cervicobrachialgia"], 2),

    # ── SPALLA ──
    (["subacromiale", "impingement"], 6),
    (["cuffia dei rotatori", "cuffia rotatori"], 7),
    (["instabilit\u00e0 scapolare", "instabilit\u00e0 gleno"], 8),
    (["spalla congelata", "capsulite"], 9),
    (["spalla", "spalle"], 6),

    # ── GINOCCHIO ──
    (["crociato", "lca"], 10),
    (["menisco"], 11),
    (["femoro-rotulea", "rotula", "sindrome femoro"], 12),
    (["artrosi ginocchio", "artrosi grave del ginocchio",
      "artrosi grave delle ginocchia", "gonartrosi"], 13),
    (["ginocchio", "ginocchia"], 10),

    # ── ANCA ──
    (["artrosi anca", "coxartrosi", "artrosi severa dell'anca",
      "artrosi dell'anca"], 14),
    (["conflitto femoro-acetabolare", "impingement anca"], 15),
    (["anca"], 14),

    # ── GOMITO ──
    (["epicondilite", "gomito del tennista"], 16),
    (["gomito"], 16),

    # ── POLSO ──
    (["tunnel carpale"], 17),
    (["polso", "avambraccio", "frattura al polso", "frattura al radio"], 17),

    # ── CAVIGLIA / PIEDE ──
    (["fascite plantare", "plantare"], 18),
    (["caviglia", "achille"], 19),

    # ── CARDIOVASCOLARE ──
    (["ipertensione", "pressione sanguigna"], 20),
    (["cardiopatia", "cardiaci gravi", "cardiovascol"], 21),
    (["problemi cardiaci"], 20),

    # ── METABOLICO ──
    (["osteoporosi"], 24),

    # ── NEUROLOGICO ──
    (["sciatica", "radicolopatia", "nervo sciatico"], 26),
    (["piriforme"], 27),

    # ── SPECIAL ──
    (["gravidanza"], 29),
    (["diastasi"], 30),
]

# ═══════════════════════════════════════════════════════════════
# FLAG STRUTTURALI ANAMNESI → CONDITION IDS
# ═══════════════════════════════════════════════════════════════
# Campi AnamnesiData con `.presente == true` mappano direttamente a condizioni.

STRUCTURAL_FLAGS: dict[str, list[int]] = {
    "problemi_cardiovascolari": [20, 21],   # ipertensione + cardiopatia
    "problemi_respiratori": [28],           # asma da sforzo
}


def match_keywords(text: str, keywords: list[str]) -> bool:
    """Ritorna True se almeno una keyword e' presente nel testo (case-insensitive)."""
    text_lower = text.lower().strip()
    return any(kw.lower() in text_lower for kw in keywords)
