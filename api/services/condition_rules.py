# api/services/condition_rules.py
"""
Regole condivise per keyword → condition_id mapping.

Usato da:
  - api/services/safety_engine.py (runtime: anamnesi → condizioni rilevanti)
  - tools/admin_scripts/populate_conditions.py (batch: esercizi → mapping)

Le keyword sono in italiano, lowercase. Il matching e' case-insensitive substring.
I condition_id corrispondono alla tabella condizioni_mediche (39 condizioni).

v2: keyword generiche body-part spostate su condizioni generiche (31-39).
    Condizioni specifiche matchano solo per keyword specifiche.
    Condizioni irraggiungibili ora coperte (22, 23, 25, 28).
"""

# ═══════════════════════════════════════════════════════════════
# KEYWORD → CONDITION ID (estrazione anamnesi cliente)
# ═══════════════════════════════════════════════════════════════
# Ogni entry: (keyword_list, condition_id)
# Basta che UNA keyword sia presente nella stringa per matchare.
#
# ORDINE: specifiche prima, generiche dopo. Il sistema aggiunge
# TUTTI i match (non first-match), quindi l'ordine non influisce
# sul risultato, ma aiuta la leggibilita'.

ANAMNESI_KEYWORD_RULES: list[tuple[list[str], int]] = [
    # ═══════════════════════════════════════════════════════
    # CONDIZIONI SPECIFICHE (diagnosi precisa nel testo)
    # ═══════════════════════════════════════════════════════

    # ── SCHIENA / LOMBARE ──
    (["ernia", "hernia discale"], 1),
    (["lombare"], 1),
    (["scoliosi"], 3),
    (["stenosi spinale"], 4),
    (["spondilolistesi"], 5),

    # ── CERVICALE / COLLO ──
    (["ernia cervicale", "ernia del disco cervicale", "cervicobrachialgia"], 2),

    # ── SPALLA ──
    (["subacromiale", "impingement spalla"], 6),
    (["cuffia dei rotatori", "cuffia rotatori"], 7),
    (["instabilit\u00e0 scapolare", "instabilit\u00e0 gleno"], 8),
    (["spalla congelata", "capsulite"], 9),

    # ── GINOCCHIO ──
    (["crociato", "lca"], 10),
    (["menisco"], 11),
    (["femoro-rotulea", "rotula", "sindrome femoro"], 12),
    (["artrosi ginocchio", "artrosi grave del ginocchio",
      "artrosi grave delle ginocchia", "gonartrosi"], 13),

    # ── ANCA ──
    (["artrosi anca", "coxartrosi", "artrosi severa dell'anca",
      "artrosi dell'anca"], 14),
    (["conflitto femoro-acetabolare", "impingement anca"], 15),

    # ── GOMITO ──
    (["epicondilite", "gomito del tennista"], 16),

    # ── POLSO ──
    (["tunnel carpale"], 17),

    # ── CAVIGLIA / PIEDE ──
    (["fascite plantare", "plantare"], 18),

    # ── CARDIOVASCOLARE ──
    (["ipertensione", "pressione sanguigna"], 20),
    (["cardiopatia", "cardiaci gravi", "cardiovascol"], 21),
    (["problemi cardiaci"], 20),
    (["insufficienza cardiaca", "scompenso cardiaco", "scompenso"], 22),

    # ── METABOLICO ──
    (["osteoporosi"], 24),
    (["diabete", "diabetico", "glicemia alta"], 23),
    (["obeso", "obesit"], 25),

    # ── NEUROLOGICO ──
    (["sciatica", "radicolopatia", "nervo sciatico"], 26),
    (["piriforme"], 27),

    # ── RESPIRATORIO ──
    (["asma"], 28),

    # ── SPECIAL ──
    (["gravidanza"], 29),
    (["diastasi"], 30),

    # ═══════════════════════════════════════════════════════
    # CONDIZIONI GENERICHE POST-TRAUMATICHE (31-37)
    # Keyword: body-part generico + compound frattura/intervento
    # ═══════════════════════════════════════════════════════

    # ── Polso/Mano (31) ──
    (["frattura polso", "frattura radio", "frattura al polso",
      "frattura al radio", "intervento polso", "operato polso"], 31),
    (["polso", "avambraccio"], 31),

    # ── Ginocchio (32) ──
    (["frattura ginocchio", "frattura al ginocchio",
      "intervento ginocchio", "operato ginocchio",
      "artroscopia ginocchio"], 32),
    (["ginocchio", "ginocchia"], 32),

    # ── Spalla (33) ──
    (["frattura spalla", "frattura clavicola", "frattura omero",
      "lussazione spalla", "intervento spalla", "operato spalla",
      "artroscopia spalla"], 33),
    (["spalla", "spalle"], 33),

    # ── Caviglia/Piede (34) ──
    (["frattura caviglia", "frattura piede", "frattura metatarso",
      "distorsione grave caviglia", "intervento caviglia"], 34),
    (["caviglia", "achille", "piede"], 34),

    # ── Anca (35) ──
    (["frattura femore", "frattura anca", "protesi anca",
      "intervento anca", "operato anca"], 35),
    (["anca", "anche"], 35),

    # ── Colonna (36) ──
    (["frattura vertebrale", "frattura vertebra",
      "intervento colonna", "operato schiena"], 36),

    # ── Gomito (37) ──
    (["frattura gomito", "intervento gomito", "operato gomito"], 37),
    (["gomito"], 37),

    # ═══════════════════════════════════════════════════════
    # CONDIZIONI GENERICHE SINTOMATOLOGICHE (38-39)
    # Keyword: sintomi generici (cervicalgia, lombalgia)
    # ═══════════════════════════════════════════════════════

    # ── Cervicalgia (38) ──
    (["cervicalgia", "cervical", "collo", "dolore cervicale",
      "rigidita' cervicale"], 38),

    # ── Lombalgia (39) ──
    (["lombalgia", "mal di schiena", "dolore lombare",
      "rigidita' lombare"], 39),
]

# ═══════════════════════════════════════════════════════════════
# FLAG STRUTTURALI ANAMNESI → CONDITION IDS
# ═══════════════════════════════════════════════════════════════
# Campi AnamnesiData con `.presente == true` mappano direttamente a condizioni.

STRUCTURAL_FLAGS: dict[str, list[int]] = {
    "problemi_cardiovascolari": [20, 21],   # ipertensione + cardiopatia
    "problemi_respiratori": [28],           # asma da sforzo
}


def _normalize_accents(text: str) -> str:
    """Normalizza accenti Unicode e apostrofi italiani per matching robusto.

    Gestisce 2 convenzioni di scrittura italiana:
      - Unicode: instabilità, attività, rigidità
      - Apostrofo: instabilita', attivita', rigidita'

    Entrambe vengono normalizzate alla forma base (senza accento ne' apostrofo).
    Preserva apostrofi di elisione: l'ernia, dell'anca, un'artroscopia.
    """
    import re

    t = text
    for accented, base in [
        ('\u00e0', 'a'), ('\u00e8', 'e'), ('\u00ec', 'i'),
        ('\u00f2', 'o'), ('\u00f9', 'u'),
        ('\u00e1', 'a'), ('\u00e9', 'e'), ('\u00ed', 'i'),
        ('\u00f3', 'o'), ('\u00fa', 'u'),
    ]:
        t = t.replace(accented, base)
    # Apostrofo dopo vocale a fine parola (accento italiano): rimuovi
    # "instabilita'" → "instabilita", "attivita'" → "attivita"
    # Ma preserva elisione: "l'ernia" (consonante+apostrofo+vocale)
    t = re.sub(r"([aeiou])'(?=\s|$|[,;.\-])", r"\1", t)
    return t


def match_keywords(text: str, keywords: list[str]) -> bool:
    """Ritorna True se almeno una keyword e' presente nel testo.

    Case-insensitive + accent-insensitive (à == a' == a).
    """
    text_norm = _normalize_accents(text.lower().strip())
    return any(_normalize_accents(kw.lower()) in text_norm for kw in keywords)
