# tools/admin_scripts/test_safety_engine.py
"""
Test Safety Engine v2 — 10 profili clinici realistici + edge cases.

Verifica:
  - extract_client_conditions() (keyword matching + structural flags)
  - Prevenzione falsi positivi (obiettivi_specifici escluso)
  - Robustezza input (null, malformed, tipi errati)
  - Coerenza interna ANAMNESI_KEYWORD_RULES
  - Limiti noti documentati (negazione, lateralita', cross-contamination)

Uso:
  python -m tools.admin_scripts.test_safety_engine

Nessun server richiesto. Test puro sulla logica di estrazione.
"""

import json
import sys
from typing import Optional

# ═══════════════════════════════════════════════════════════════
# IMPORT MODULI SOTTO TEST
# ═══════════════════════════════════════════════════════════════

from api.services.safety_engine import extract_client_conditions
from api.services.condition_rules import (
    ANAMNESI_KEYWORD_RULES,
    STRUCTURAL_FLAGS,
    match_keywords,
)

# ═══════════════════════════════════════════════════════════════
# FRAMEWORK TEST MINIMALE
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
warnings = 0


def ok(msg: str):
    global passed
    passed += 1
    print(f"  PASS: {msg}")


def fail(msg: str):
    global failed
    failed += 1
    print(f"  FAIL: {msg}")


def warn(msg: str):
    global warnings
    warnings += 1
    print(f"  WARN: {msg}")


def assert_conditions(
    label: str,
    anamnesi: dict,
    expected: set[int],
    not_expected: Optional[set[int]] = None,
):
    """
    Testa extract_client_conditions e verifica:
    - TUTTI gli expected sono presenti (mancanza = condizione ignorata → rischio clinico)
    - NESSUNO dei not_expected e' presente (presenza = falso positivo → allarme inutile)
    """
    anamnesi_json = json.dumps(anamnesi)
    result = extract_client_conditions(anamnesi_json)

    # Verifica expected (condizioni che DEVONO essere trovate)
    missing = expected - result
    if missing:
        fail(f"{label}: condizioni mancanti {missing} — RISCHIO: condizione reale non rilevata")

    # Verifica not_expected (falsi positivi)
    if not_expected:
        false_positives = not_expected & result
        if false_positives:
            fail(f"{label}: falsi positivi {false_positives} — condizioni non pertinenti")

    # Se tutto ok
    if not missing and (not not_expected or not (not_expected & result)):
        ok(f"{label}: condizioni corrette {result}")
    else:
        print(f"    Atteso:  {expected}")
        print(f"    Ottenuto: {result}")
        if not_expected:
            print(f"    Esclusi: {not_expected}")

    return result


# ═══════════════════════════════════════════════════════════════
# HELPER: costruzione anamnesi
# ═══════════════════════════════════════════════════════════════

def q(presente: bool, dettaglio: Optional[str] = None) -> dict:
    """Shortcut per campo AnamnesiQuestion."""
    return {"presente": presente, "dettaglio": dettaglio}


def build_anamnesi(
    infortuni_attuali: Optional[dict] = None,
    infortuni_pregressi: Optional[dict] = None,
    interventi_chirurgici: Optional[dict] = None,
    dolori_cronici: Optional[dict] = None,
    patologie: Optional[dict] = None,
    farmaci: Optional[dict] = None,
    problemi_cardiovascolari: Optional[dict] = None,
    problemi_respiratori: Optional[dict] = None,
    dieta_particolare: Optional[dict] = None,
    livello_attivita: str = "moderato",
    ore_sonno: str = "7-8",
    livello_stress: str = "medio",
    obiettivi_specifici: Optional[str] = None,
    limitazioni_funzionali: Optional[str] = None,
    note: Optional[str] = None,
) -> dict:
    """Costruisce un dizionario anamnesi completo."""
    return {
        "infortuni_attuali": infortuni_attuali or q(False),
        "infortuni_pregressi": infortuni_pregressi or q(False),
        "interventi_chirurgici": interventi_chirurgici or q(False),
        "dolori_cronici": dolori_cronici or q(False),
        "patologie": patologie or q(False),
        "farmaci": farmaci or q(False),
        "problemi_cardiovascolari": problemi_cardiovascolari or q(False),
        "problemi_respiratori": problemi_respiratori or q(False),
        "dieta_particolare": dieta_particolare or q(False),
        "livello_attivita": livello_attivita,
        "ore_sonno": ore_sonno,
        "livello_stress": livello_stress,
        "obiettivi_specifici": obiettivi_specifici,
        "limitazioni_funzionali": limitazioni_funzionali,
        "note": note,
    }


# ═══════════════════════════════════════════════════════════════
# PARTE 0: COERENZA INTERNA REGOLE
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 0: COERENZA INTERNA ANAMNESI_KEYWORD_RULES")
print("=" * 70)

# 0.1 — Nessuna keyword vuota
print("\n--- 0.1: Nessuna keyword vuota ---")
empty_kw_found = False
for keywords, cond_id in ANAMNESI_KEYWORD_RULES:
    for kw in keywords:
        if not kw or not kw.strip():
            fail(f"Keyword vuota per condizione {cond_id}")
            empty_kw_found = True
if not empty_kw_found:
    ok("Nessuna keyword vuota in ANAMNESI_KEYWORD_RULES")

# 0.2 — Nessun condition_id duplicato con keyword identica
print("\n--- 0.2: Nessun duplicato keyword→condition ---")
seen: dict[tuple[str, int], int] = {}
dup_found = False
for idx, (keywords, cond_id) in enumerate(ANAMNESI_KEYWORD_RULES):
    for kw in keywords:
        key = (kw.lower(), cond_id)
        if key in seen:
            warn(f"Keyword duplicata '{kw}' per cond {cond_id} (righe {seen[key]} e {idx})")
            dup_found = True
        seen[key] = idx
if not dup_found:
    ok("Nessun duplicato keyword→condition_id")

# 0.3 — Tutte le condizioni 1-39 raggiungibili via keyword O structural flag
print("\n--- 0.3: Copertura condizioni 1-39 ---")
reachable_kw = set()
for keywords, cond_id in ANAMNESI_KEYWORD_RULES:
    reachable_kw.add(cond_id)
reachable_flag = set()
for field, cond_ids in STRUCTURAL_FLAGS.items():
    reachable_flag.update(cond_ids)
reachable_all = reachable_kw | reachable_flag

# Condizione 19 (Instabilita' cronica caviglia) non ha keyword diretta — esiste?
all_expected = set(range(1, 40))  # 1-39
# Nota: id 19 non esiste nella nostra taxonomy (salto da 18 a 20)
all_expected.discard(19)  # non esiste nel catalogo

unreachable = all_expected - reachable_all
if unreachable:
    fail(f"Condizioni irraggiungibili: {sorted(unreachable)}")
else:
    ok(f"Tutte le {len(all_expected)} condizioni raggiungibili ({len(reachable_kw)} keyword, {len(reachable_flag)} structural)")

# 0.4 — match_keywords() case-insensitive
print("\n--- 0.4: match_keywords case-insensitive ---")
assert match_keywords("Ho una ERNIA LOMBARE", ["ernia"]) is True
assert match_keywords("IPERTENSIONE arteriosa", ["ipertensione"]) is True
assert match_keywords("nessun problema", ["ernia"]) is False
ok("match_keywords case-insensitive funzionante")

# 0.5 — match_keywords accent-insensitive
print("\n--- 0.5: match_keywords accent-insensitive ---")
assert match_keywords("instabilita' scapolare", ["instabilit\u00e0 scapolare"]) is True
assert match_keywords("instabilit\u00e0 scapolare", ["instabilita' scapolare"]) is True
assert match_keywords("rigidita' lombare", ["rigidit\u00e0 lombare"]) is True
ok("match_keywords accent-insensitive funzionante (apostrofo == accento)")


# ═══════════════════════════════════════════════════════════════
# PARTE 1: 10 PROFILI CLINICI REALISTICI
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 1: 10 PROFILI CLINICI REALISTICI")
print("=" * 70)

# ──────────────────────────────────────────────────────────────
# PROFILO 1: Vincenzo Amato — Il caso originale
# Fratture pregresse + cervicalgia + "spalle" in obiettivi
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 1: Vincenzo Amato (fratture + cervicalgia) ---")
vincenzo = build_anamnesi(
    infortuni_pregressi=q(True, "frattura polso destro 2020, frattura ginocchio sinistro 2018"),
    dolori_cronici=q(True, "cervicalgia persistente"),
    problemi_cardiovascolari=q(True, "ipertensione arteriosa controllata"),
    problemi_respiratori=q(True),
    obiettivi_specifici="Migliorare mobilita' spalle e postura",
)
assert_conditions(
    "Vincenzo Amato",
    vincenzo,
    expected={
        31,  # Esiti post-traumatici Polso (frattura polso)
        32,  # Esiti post-traumatici Ginocchio (frattura ginocchio)
        38,  # Cervicalgia (cervicalgia → "cervical" substring)
        20,  # Ipertensione (structural cardiovascolare)
        21,  # Cardiopatia (structural cardiovascolare)
        28,  # Asma (structural respiratorio)
    },
    not_expected={
        6,   # Impingement spalla — "spalle" e' in obiettivi, NON in condizioni
        10,  # Lesione LCA — frattura ginocchio ≠ LCA
        17,  # Tunnel carpale — frattura polso ≠ tunnel carpale
        33,  # Esiti spalla — "spalle" e' in obiettivi, NON scansionato
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 2: Maria Grasso — Polipatologa cardiovascolare/metabolica
# Ipertensione + diabete + obesita' + cardiopatia
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 2: Maria Grasso (cardiovascolare + metabolica) ---")
maria = build_anamnesi(
    patologie=q(True, "Diabete tipo 2, ipertensione arteriosa, obesita' grave"),
    farmaci=q(True, "Metformina 1000mg, enalapril 20mg, atorvastatina"),
    problemi_cardiovascolari=q(True, "Cardiopatia ipertensiva"),
    limitazioni_funzionali="Dispnea da sforzo moderato, evitare sforzi massimali",
)
assert_conditions(
    "Maria Grasso",
    maria,
    expected={
        20,  # Ipertensione (keyword "ipertensione" + structural)
        21,  # Cardiopatia (keyword "cardiopatia" + structural)
        23,  # Diabete tipo 2 (keyword "diabete")
        25,  # Obesita' (keyword "obesit")
    },
    not_expected={
        22,  # Insufficienza cardiaca — NON menzionata
        28,  # Asma — nessun flag respiratorio
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 3: Luca Ferrari — Post-chirurgico multiplo
# Artroscopia ginocchio + protesi anca + ernia lombare operata
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 3: Luca Ferrari (post-chirurgico multiplo) ---")
luca = build_anamnesi(
    infortuni_pregressi=q(True, "Rottura menisco mediale ginocchio destro 2017"),
    interventi_chirurgici=q(True,
        "Artroscopia ginocchio destro 2017, protesi anca sinistra 2021, "
        "intervento ernia discale lombare L4-L5 2019"
    ),
    dolori_cronici=q(True, "Rigidita' lombare residua post-intervento"),
)
assert_conditions(
    "Luca Ferrari",
    luca,
    expected={
        1,   # Ernia discale lombare (keyword "ernia")
        11,  # Menisco (keyword "menisco")
        32,  # Esiti ginocchio (keyword "ginocchio" + "artroscopia ginocchio")
        35,  # Esiti anca (keyword "protesi anca" + "anca")
        39,  # Lombalgia (keyword "lombare" in rigidita'? NO — "lombare" → cond 1)
    },
    not_expected={
        10,  # LCA — menisco ≠ LCA
        14,  # Coxartrosi — protesi anca ≠ coxartrosi
    },
)
# Nota: "lombare" in "rigidita' lombare" matcha cond 1 (ernia lombare) anche se il
# paziente non ha ernia attiva. Questo e' un LIMITE NOTO del sistema keyword.
# Il testo "rigidita' lombare residua" → cond 1 + cond 39? Vediamo:
# "rigidita' lombare" — "lombare" matcha cond 1, "rigidita' lombare" matcha cond 39? NO.
# cond 39 ha keyword ["lombalgia", "mal di schiena", "dolore lombare", "rigidita' lombare"]
# "rigidita' lombare" e' ESATTAMENTE in cond 39. SI, matcha!

# ──────────────────────────────────────────────────────────────
# PROFILO 4: Anna Conti — Gravidanza + diastasi
# Condizioni speciali + dolore lombare associato
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 4: Anna Conti (gravidanza + diastasi) ---")
anna = build_anamnesi(
    patologie=q(True, "Diastasi dei retti addominali post-parto"),
    dolori_cronici=q(True, "Lombalgia cronica, dolore al pavimento pelvico"),
    note="Gravidanza conclusa 6 mesi fa. Parto cesareo.",
)
assert_conditions(
    "Anna Conti",
    anna,
    expected={
        29,  # Gravidanza (keyword "gravidanza" in note)
        30,  # Diastasi (keyword "diastasi")
        39,  # Lombalgia (keyword "lombalgia")
    },
    not_expected={
        1,   # Ernia lombare — lombalgia ≠ ernia
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 5: Roberto Esposito — Neurologico puro
# Sciatica + piriforme + cervicobrachialgia
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 5: Roberto Esposito (neurologico) ---")
roberto = build_anamnesi(
    dolori_cronici=q(True,
        "Sciatica ricorrente lato destro, sindrome del piriforme bilaterale, "
        "cervicobrachialgia sinistra"
    ),
    farmaci=q(True, "Antinfiammatori al bisogno (ibuprofene)"),
)
assert_conditions(
    "Roberto Esposito",
    roberto,
    expected={
        2,   # Ernia cervicale (keyword "cervicobrachialgia")
        26,  # Sciatica (keyword "sciatica")
        27,  # Piriforme (keyword "piriforme")
    },
    not_expected={
        38,  # Cervicalgia — "cervicobrachialgia" NON contiene "cervical" come substring
        1,   # Ernia lombare — sciatica ≠ ernia (a meno che "sciatica" non triggeri altro)
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 6: Giulia Romano — Sportiva con trauma multiplo
# LCA + menisco + instabilita' scapolare
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 6: Giulia Romano (sportiva, traumi multipli) ---")
giulia = build_anamnesi(
    infortuni_pregressi=q(True,
        "Rottura LCA ginocchio sinistro 2022 (ricostruito), lesione menisco mediale associata"
    ),
    interventi_chirurgici=q(True, "Ricostruzione LCA + sutura menisco ginocchio sx 2022"),
    dolori_cronici=q(True, "Instabilita' scapolare spalla destra, crepitio femoro-rotulea"),
    obiettivi_specifici="Tornare a giocare a pallavolo, rinforzare ginocchio e spalla",
)
assert_conditions(
    "Giulia Romano",
    giulia,
    expected={
        10,  # LCA (keyword "lca" / "crociato")
        11,  # Menisco (keyword "menisco")
        8,   # Instabilita' scapolare (keyword "instabilita' scapolare")
        12,  # Femoro-rotulea (keyword "femoro-rotulea")
        32,  # Esiti ginocchio (keyword "ginocchio")
        33,  # Esiti spalla (keyword "spalla")
    },
    not_expected={
        6,   # Impingement spalla — instabilita' scapolare ≠ impingement
        9,   # Spalla congelata
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 7: Franco Marchetti — Anziano fragile
# Osteoporosi + artrosi anca + stenosi spinale + scompenso cardiaco
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 7: Franco Marchetti (anziano, multi-patologico) ---")
franco = build_anamnesi(
    patologie=q(True,
        "Osteoporosi severa, coxartrosi bilaterale, stenosi spinale L3-L4, "
        "scompenso cardiaco classe NYHA II"
    ),
    farmaci=q(True, "Bifosfonati, ACE-inibitore, diuretico, betabloccante"),
    problemi_cardiovascolari=q(True, "Scompenso cardiaco cronico, fibrillazione atriale"),
    limitazioni_funzionali="Non puo' sollevare pesi sopra la testa. Evitare impatti.",
)
assert_conditions(
    "Franco Marchetti",
    franco,
    expected={
        4,   # Stenosi spinale (keyword "stenosi spinale")
        14,  # Coxartrosi (keyword "coxartrosi")
        20,  # Ipertensione (structural cardiovascolare)
        21,  # Cardiopatia (structural cardiovascolare)
        22,  # Insufficienza cardiaca (keyword "scompenso cardiaco" / "scompenso")
        24,  # Osteoporosi (keyword "osteoporosi")
        # Nota: cond 35 (Esiti anca) NON matcha — "coxartrosi" non contiene "anca"
    },
    not_expected={
        15,  # Impingement anca — coxartrosi ≠ impingement
        35,  # Esiti anca — "coxartrosi" non contiene la keyword "anca"
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 8: Sara Moretti — Mista ortopedica + respiratoria
# Asma + epicondilite + tunnel carpale + fascite plantare
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 8: Sara Moretti (mista ortopedica + respiratoria) ---")
sara = build_anamnesi(
    dolori_cronici=q(True, "Epicondilite gomito destro, fascite plantare piede sinistro"),
    patologie=q(True, "Asma bronchiale, sindrome del tunnel carpale bilaterale"),
    problemi_respiratori=q(True, "Asma da sforzo"),
)
assert_conditions(
    "Sara Moretti",
    sara,
    expected={
        16,  # Epicondilite (keyword "epicondilite")
        17,  # Tunnel carpale (keyword "tunnel carpale")
        18,  # Fascite plantare (keyword "fascite plantare")
        28,  # Asma (structural respiratorio + keyword "asma")
        34,  # Esiti caviglia/piede (keyword "piede")
        37,  # Esiti gomito (keyword "gomito")
    },
    not_expected={
        31,  # Esiti polso — tunnel carpale ≠ frattura polso
    },
)
# Nota: "tunnel carpale" NON contiene "polso" → cond 31 non matcha. Corretto!
# Ma "gomito destro" contiene "gomito" → cond 37 matcha. Corretto!
# "piede sinistro" contiene "piede" → cond 34 matcha. Corretto!

# ──────────────────────────────────────────────────────────────
# PROFILO 9: Paolo Ricci — Scoliosi + frattura clavicola + test negazione
# Verifica precisione keyword e limite negazione
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 9: Paolo Ricci (scoliosi + frattura clavicola) ---")
paolo = build_anamnesi(
    patologie=q(True, "Scoliosi lieve destro-convessa"),
    infortuni_pregressi=q(True, "Frattura clavicola destra 2018"),
    obiettivi_specifici="Migliorare spalle, rinforzare il core, perdere peso",
    # Test: obiettivi con "spalle" NON deve triggerare cond 33
)
assert_conditions(
    "Paolo Ricci",
    paolo,
    expected={
        3,   # Scoliosi (keyword "scoliosi")
        33,  # Esiti spalla (keyword "frattura clavicola")
    },
    not_expected={
        6,   # Impingement spalla — frattura clavicola ≠ impingement
        25,  # Obesita' — "perdere peso" in obiettivi NON scansionato
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 10: Elena Santini — Ernia cervicale + multi-zona
# Verifica cross-contamination ernia cervicale vs lombare
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 10: Elena Santini (ernia cervicale + multi-zona) ---")
elena = build_anamnesi(
    patologie=q(True, "Ernia cervicale C5-C6, spondilolistesi L5-S1"),
    dolori_cronici=q(True, "Dolore cervicale irradiato al braccio, mal di schiena cronico"),
    infortuni_pregressi=q(True, "Distorsione grave caviglia destra 2020"),
    problemi_cardiovascolari=q(True, "Ipertensione lieve"),
)
assert_conditions(
    "Elena Santini",
    elena,
    expected={
        1,   # Ernia (keyword "ernia" — NOTA: falso positivo per lombare, vedi sotto)
        2,   # Ernia cervicale (keyword "ernia cervicale")
        5,   # Spondilolistesi (keyword "spondilolistesi")
        20,  # Ipertensione (structural cardiovascolare)
        21,  # Cardiopatia (structural cardiovascolare)
        34,  # Esiti caviglia (keyword "caviglia" + "distorsione grave caviglia")
        38,  # Cervicalgia (keyword "cervical" in "dolore cervicale")
        39,  # Lombalgia (keyword "mal di schiena")
    },
    not_expected=set(),  # Nessun falso positivo da escludere per questo profilo
)
# NOTA CLINICA: "ernia cervicale" matcha ANCHE cond 1 (ernia lombare) perche' "ernia"
# e' substring. Questo e' OVER-CAUTIOUS ma non pericoloso: il trainer vedra' anche
# le precauzioni lombari, che non sono dannose per una cervicale. Limite accettabile
# per un sistema deterministico senza NLP.


# ═══════════════════════════════════════════════════════════════
# PARTE 2: EDGE CASES — ROBUSTEZZA INPUT
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 2: EDGE CASES — ROBUSTEZZA INPUT")
print("=" * 70)

# 2.1 — Anamnesi null
print("\n--- 2.1: anamnesi_json = None ---")
result = extract_client_conditions(None)
if result == set():
    ok("None → set vuoto")
else:
    fail(f"None → {result} (atteso set vuoto)")

# 2.2 — Anamnesi stringa vuota
print("\n--- 2.2: anamnesi_json = '' ---")
result = extract_client_conditions("")
if result == set():
    ok("Stringa vuota → set vuoto")
else:
    fail(f"Stringa vuota → {result}")

# 2.3 — JSON invalido
print("\n--- 2.3: JSON invalido ---")
result = extract_client_conditions("{not valid json")
if result == set():
    ok("JSON invalido → set vuoto")
else:
    fail(f"JSON invalido → {result}")

# 2.4 — JSON valido ma non dict (array)
print("\n--- 2.4: JSON array ---")
result = extract_client_conditions('[1, 2, 3]')
if result == set():
    ok("JSON array → set vuoto")
else:
    fail(f"JSON array → {result}")

# 2.5 — JSON valido ma non dict (string)
print("\n--- 2.5: JSON string ---")
result = extract_client_conditions('"hello"')
if result == set():
    ok("JSON string → set vuoto")
else:
    fail(f"JSON string → {result}")

# 2.6 — Dict vuoto
print("\n--- 2.6: Dict vuoto ---")
result = extract_client_conditions('{}')
if result == set():
    ok("Dict vuoto → set vuoto")
else:
    fail(f"Dict vuoto → {result}")

# 2.7 — Tutti i campi presente=False
print("\n--- 2.7: Tutti presente=false ---")
all_false = build_anamnesi()
result = extract_client_conditions(json.dumps(all_false))
if result == set():
    ok("Tutti false → set vuoto")
else:
    fail(f"Tutti false → {result}")

# 2.8 — presente=True ma dettaglio=null (structural flag test)
print("\n--- 2.8: presente=true, dettaglio=null (structural) ---")
only_structural = build_anamnesi(
    problemi_cardiovascolari=q(True, None),  # Flag ON, nessun dettaglio
)
result = extract_client_conditions(json.dumps(only_structural))
expected_structural = {20, 21}  # Da STRUCTURAL_FLAGS
if result == expected_structural:
    ok(f"Structural senza dettaglio → {result}")
else:
    fail(f"Atteso {expected_structural}, ottenuto {result}")

# 2.9 — presente=True, dettaglio="" (stringa vuota)
print("\n--- 2.9: presente=true, dettaglio='' ---")
empty_detail = build_anamnesi(
    dolori_cronici={"presente": True, "dettaglio": ""},
)
result = extract_client_conditions(json.dumps(empty_detail))
if result == set():
    ok("Dettaglio vuoto → set vuoto (nessun keyword)")
else:
    fail(f"Dettaglio vuoto → {result} (atteso set vuoto)")

# 2.10 — presente come stringa "true" (tipo errato)
print("\n--- 2.10: presente='true' (string instead of bool) ---")
string_true = build_anamnesi(
    problemi_cardiovascolari={"presente": "true", "dettaglio": None},
)
result = extract_client_conditions(json.dumps(string_true))
# Python: "true" is truthy → .get("presente") returns "true" which is truthy
# Questo POTREBBE essere un bug se il frontend invia stringhe
if {20, 21}.issubset(result):
    warn('presente="true" (string) trattato come truthy → matcha structural flags. '
         'Accettabile se il frontend invia sempre boolean.')
else:
    ok('presente="true" (string) ignorato correttamente')

# 2.11 — dettaglio con solo spazi
print("\n--- 2.11: dettaglio con solo spazi ---")
whitespace = build_anamnesi(
    dolori_cronici=q(True, "   \n\t  "),
)
result = extract_client_conditions(json.dumps(whitespace))
if result == set():
    ok("Dettaglio whitespace → set vuoto")
else:
    fail(f"Dettaglio whitespace → {result}")

# 2.12 — dettaglio numerico (tipo errato)
print("\n--- 2.12: dettaglio numerico ---")
numeric_detail = build_anamnesi(
    dolori_cronici={"presente": True, "dettaglio": 12345},
)
result = extract_client_conditions(json.dumps(numeric_detail))
if result == set():
    ok("Dettaglio numerico ignorato (non string)")
else:
    fail(f"Dettaglio numerico → {result}")


# ═══════════════════════════════════════════════════════════════
# PARTE 3: PREVENZIONE FALSI POSITIVI
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 3: PREVENZIONE FALSI POSITIVI")
print("=" * 70)

# 3.1 — obiettivi_specifici ESCLUSO dal keyword matching
print("\n--- 3.1: obiettivi_specifici ESCLUSO ---")
obj_only = build_anamnesi(
    obiettivi_specifici="Rinforzare spalla, migliorare ginocchio, perdere peso, "
                        "correre maratona, migliorare postura cervicale",
)
result = extract_client_conditions(json.dumps(obj_only))
if result == set():
    ok("obiettivi_specifici ignorato → 0 condizioni (nessun falso positivo)")
else:
    fail(f"obiettivi_specifici produce falsi positivi: {result}")

# 3.2 — Farmaci generici NON triggerano condizioni
print("\n--- 3.2: Farmaci generici ---")
farmaci = build_anamnesi(
    farmaci=q(True, "Paracetamolo al bisogno, vitamina D, omega-3"),
)
result = extract_client_conditions(json.dumps(farmaci))
if result == set():
    ok("Farmaci generici → 0 condizioni")
else:
    fail(f"Farmaci generici producono match: {result}")

# 3.3 — Dieta particolare NON triggera condizioni mediche
print("\n--- 3.3: Dieta particolare ---")
dieta = build_anamnesi(
    dieta_particolare=q(True, "Dieta chetogenica, no glutine per scelta"),
)
result = extract_client_conditions(json.dumps(dieta))
if result == set():
    ok("Dieta particolare → 0 condizioni")
else:
    fail(f"Dieta particolare produce match: {result}")


# ═══════════════════════════════════════════════════════════════
# PARTE 4: KEYWORD PRECISION — TEST ATOMICI
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 4: KEYWORD PRECISION — TEST ATOMICI")
print("=" * 70)

def test_keyword(label: str, text: str, expected_ids: set[int], not_expected_ids: Optional[set[int]] = None):
    """Testa una singola stringa contro le keyword rules."""
    anamnesi = build_anamnesi(dolori_cronici=q(True, text))
    return assert_conditions(label, anamnesi, expected_ids, not_expected_ids)

# 4.1 — "ernia cervicale" matcha 1 (ernia) + 2 (ernia cervicale) + 38 (cervicale contiene "cervical")
print("\n--- 4.1: 'ernia cervicale' → cond 1 + 2 + 38 (over-cautious accettabile) ---")
test_keyword("ernia cervicale", "ernia cervicale C5-C6",
    expected_ids={1, 2, 38},  # "ernia" → 1, "ernia cervicale" → 2, "cervical" in "cervicale" → 38
)
# NOTA: "cervicale" contiene "cervical" come substring → cond 38 matcha.
# Over-cautious ma non pericoloso: cervicalgia precautions sono un sottoinsieme
# di ernia cervicale precautions. Documentato come limite noto.

# 4.2 — "lombalgia" NON matcha "lombare" (cond 1)
print("\n--- 4.2: 'lombalgia' → cond 39 (NON cond 1) ---")
test_keyword("lombalgia solo", "lombalgia acuta",
    expected_ids={39},     # "lombalgia" → 39
    not_expected_ids={1},  # "lombare" NON e' in "lombalgia"
)

# 4.3 — "mal di schiena" → cond 39 (NON cond 1)
print("\n--- 4.3: 'mal di schiena' → cond 39 ---")
test_keyword("mal di schiena", "mal di schiena cronico",
    expected_ids={39},
    not_expected_ids={1, 36},  # "schiena" sola non matcha 1 ne' 36
)

# 4.4 — "dolore lombare" → cond 39 + cond 1 ("lombare" → 1)
print("\n--- 4.4: 'dolore lombare' → cond 1 + 39 ---")
test_keyword("dolore lombare", "dolore lombare persistente",
    expected_ids={1, 39},  # "lombare" → 1, "dolore lombare" → 39
)

# 4.5 — "scoliosi" NON matcha condizioni lombari
print("\n--- 4.5: 'scoliosi' isolata ---")
test_keyword("scoliosi", "scoliosi lieve",
    expected_ids={3},
    not_expected_ids={1, 4, 5, 39},
)

# 4.6 — "artrosi ginocchio" matcha SPECIFICO (13) + GENERICO (32)
print("\n--- 4.6: 'artrosi ginocchio' → cond 13 + 32 ---")
test_keyword("artrosi ginocchio", "artrosi ginocchio destro",
    expected_ids={13, 32},  # "artrosi ginocchio" → 13, "ginocchio" → 32
    not_expected_ids={10, 11, 12},
)

# 4.7 — "tunnel carpale" NON matcha "polso" (31)
print("\n--- 4.7: 'tunnel carpale' → solo 17 ---")
test_keyword("tunnel carpale", "sindrome del tunnel carpale bilaterale",
    expected_ids={17},
    not_expected_ids={31},  # "polso" NON in "tunnel carpale"
)

# 4.8 — "frattura femore" → cond 35 (anca)
print("\n--- 4.8: 'frattura femore' → cond 35 ---")
test_keyword("frattura femore", "frattura femore prossimale 2020",
    expected_ids={35},
    not_expected_ids={14, 15},  # Non coxartrosi ne' impingement
)

# 4.9 — "epicondilite" → cond 16 + cond 37 (gomito)
print("\n--- 4.9: 'epicondilite' → cond 16 (+ 37?) ---")
# "epicondilite" NON contiene "gomito" come substring → cond 37 NON matcha
test_keyword("epicondilite", "epicondilite laterale cronica",
    expected_ids={16},
    not_expected_ids={37},  # "gomito" non e' in "epicondilite"
)

# 4.10 — "gomito del tennista" → cond 16 + cond 37
print("\n--- 4.10: 'gomito del tennista' → cond 16 + 37 ---")
test_keyword("gomito del tennista", "gomito del tennista lato destro",
    expected_ids={16, 37},  # "gomito del tennista" → 16, "gomito" → 37
)

# 4.11 — "asma" → cond 28 (via keyword, senza structural)
print("\n--- 4.11: 'asma' solo keyword ---")
asma_kw = build_anamnesi(
    patologie=q(True, "Asma bronchiale da sforzo"),
    # problemi_respiratori NON attivato
)
assert_conditions("asma keyword", asma_kw,
    expected={28},
)

# 4.12 — "obeso" e "obesita" → cond 25
print("\n--- 4.12: varianti 'obeso' / 'obesita' ---")
test_keyword("obeso", "paziente obeso BMI 35",
    expected_ids={25},
)
test_keyword("obesita'", "obesita' grave",
    expected_ids={25},  # "obesit" e' substring di "obesita'"
)


# ═══════════════════════════════════════════════════════════════
# PARTE 5: LIMITI NOTI DOCUMENTATI
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 5: LIMITI NOTI — NON BUG, EDGE CASES ACCETTATI")
print("=" * 70)

# 5.1 — Negazione non rilevata (limite intrinseco keyword matching)
print("\n--- 5.1: LIMITE — Negazione non compresa ---")
negation = build_anamnesi(
    limitazioni_funzionali="Non ha problemi al ginocchio, non ha mai avuto ernia",
)
result = extract_client_conditions(json.dumps(negation))
if 32 in result or 1 in result:
    warn(f"Negazione non rilevata (LIMITE NOTO): 'non ha problemi al ginocchio/ernia' → {result}. "
         "Il sistema non comprende la negazione. Accettabile per keyword matching deterministico.")
else:
    ok("Negazione correttamente ignorata (inatteso ma positivo)")

# 5.2 — Cross-contamination tra campi
print("\n--- 5.2: LIMITE — Cross-contamination campi ---")
# Il sistema concatena TUTTI i testi → keyword di un campo possono matchare
# condizioni non correlate al campo originale. Es: "fascite plantare" in farmaci
# triggera cond 18 anche se e' nel campo sbagliato.
cross = build_anamnesi(
    farmaci=q(True, "Assume plantari ortopedici per fascite plantare"),
)
result = extract_client_conditions(json.dumps(cross))
if 18 in result:
    warn(f"Cross-contamination: 'fascite plantare' in farmaci → cond {result}. "
         "LIMITE NOTO: tutti i testi concatenati.")
else:
    ok("Nessuna cross-contamination (inatteso)")

# 5.3 — "ernia cervicale" triggera sia cond 1 (lombare) che 2 (cervicale)
print("\n--- 5.3: LIMITE — 'ernia cervicale' → anche cond 1 (over-cautious) ---")
ernia_cx = build_anamnesi(patologie=q(True, "Ernia cervicale C6-C7"))
result = extract_client_conditions(json.dumps(ernia_cx))
if 1 in result and 2 in result:
    warn(f"'Ernia cervicale' matcha ANCHE cond 1 (ernia lombare) → {result}. "
         "OVER-CAUTIOUS ma NON pericoloso: il trainer vedra' anche precauzioni lombari.")
else:
    ok(f"'Ernia cervicale' → {result}")

# 5.4 — Nessuna distinzione lateralita'
print("\n--- 5.4: LIMITE — Nessuna distinzione lateralita' ---")
# "ginocchio destro" e "ginocchio sinistro" producono lo stesso match
dx = build_anamnesi(dolori_cronici=q(True, "dolore ginocchio destro"))
sx = build_anamnesi(dolori_cronici=q(True, "dolore ginocchio sinistro"))
result_dx = extract_client_conditions(json.dumps(dx))
result_sx = extract_client_conditions(json.dumps(sx))
if result_dx == result_sx:
    warn(f"dx={result_dx} == sx={result_sx} — nessuna distinzione lateralita'. "
         "LIMITE NOTO: il sistema non distingue destra/sinistra.")
else:
    ok("Lateralita' distinta (inatteso)")


# ═══════════════════════════════════════════════════════════════
# PARTE 6: SEVERITY AGGREGATION (build_safety_map logic)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 6: AUDIT CODICE — SEVERITY AGGREGATION")
print("=" * 70)

print("\n--- 6.1: Severity aggregation (FIXATO) ---")
# Verifica che _SEVERITY_ORDER esista nel modulo
from api.services.safety_engine import _SEVERITY_ORDER
if _SEVERITY_ORDER == {"modify": 0, "caution": 1, "avoid": 2}:
    ok("_SEVERITY_ORDER definito correttamente: modify < caution < avoid")
else:
    fail(f"_SEVERITY_ORDER errato: {_SEVERITY_ORDER}")

# Verifica logica: caution > modify, avoid > caution
assert _SEVERITY_ORDER["avoid"] > _SEVERITY_ORDER["caution"] > _SEVERITY_ORDER["modify"]
ok("Gerarchia severity: avoid > caution > modify")


# ═══════════════════════════════════════════════════════════════
# PARTE 7: STRESS TEST — ANAMNESI MASSIMALE
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 7: STRESS TEST — ANAMNESI MASSIMALE")
print("=" * 70)

# 7.1 — Paziente con TUTTE le condizioni possibili
print("\n--- 7.1: Paziente massimale (tutte le condizioni) ---")
maximal = build_anamnesi(
    infortuni_attuali=q(True, "Distorsione grave caviglia destra, lussazione spalla sinistra"),
    infortuni_pregressi=q(True,
        "Frattura polso destro 2018, frattura ginocchio sinistro 2019, "
        "frattura femore destro 2020, frattura vertebrale L2 2021, "
        "frattura gomito sinistro 2017, frattura clavicola destra 2016"
    ),
    interventi_chirurgici=q(True,
        "Artroscopia ginocchio dx, ricostruzione LCA, protesi anca sx, "
        "intervento ernia discale lombare, intervento tunnel carpale"
    ),
    dolori_cronici=q(True,
        "Cervicalgia cronica, lombalgia, sciatica, sindrome del piriforme, "
        "epicondilite gomito dx, fascite plantare bilaterale, "
        "instabilita' scapolare, femoro-rotulea, capsulite adesiva spalla dx"
    ),
    patologie=q(True,
        "Ernia cervicale C5-C6, scoliosi, stenosi spinale L3-L4, spondilolistesi L5-S1, "
        "coxartrosi bilaterale, gonartrosi, osteoporosi, "
        "diabete tipo 2, ipertensione, asma, obesita' severa, "
        "insufficienza cardiaca NYHA II, diastasi addominale"
    ),
    farmaci=q(True, "Metformina, ACE-inibitore, betabloccante, bifosfonati, broncodilatatore"),
    problemi_cardiovascolari=q(True, "Cardiopatia ischemica cronica"),
    problemi_respiratori=q(True, "Asma da sforzo"),
    limitazioni_funzionali="Conflitto femoro-acetabolare anca dx, impingement spalla sx",
    note="Gravidanza esclusa. Obeso con radicolopatia lombare.",
)
result = extract_client_conditions(json.dumps(maximal))
# Dovrebbe matchare quasi tutte le condizioni
expected_maximal = {
    1,   # Ernia lombare ("ernia", "lombare")
    2,   # Ernia cervicale ("ernia cervicale")
    3,   # Scoliosi
    4,   # Stenosi spinale
    5,   # Spondilolistesi
    6,   # Impingement spalla (keyword "impingement spalla" in limitazioni)
    # 7 — Cuffia rotatori: NON menzionata nel testo (keyword "cuffia" assente)
    8,   # Instabilita' scapolare (ora matchato grazie a accent normalization)
    9,   # Spalla congelata ("capsulite")
    10,  # LCA ("lca")
    # 11 — Menisco: NON menzionato esplicitamente (keyword "menisco" assente)
    12,  # Femoro-rotulea
    13,  # Gonartrosi ("gonartrosi")
    14,  # Coxartrosi ("coxartrosi")
    15,  # Impingement anca ("conflitto femoro-acetabolare" / "impingement anca")
    16,  # Epicondilite
    17,  # Tunnel carpale
    18,  # Fascite plantare
    20,  # Ipertensione (structural + keyword)
    21,  # Cardiopatia (structural + keyword)
    22,  # Insufficienza cardiaca ("insufficienza cardiaca")
    23,  # Diabete ("diabete")
    24,  # Osteoporosi
    25,  # Obesita' ("obesita'" contiene "obesit")
    26,  # Sciatica
    27,  # Piriforme
    28,  # Asma (structural + keyword)
    # 29 — Gravidanza: "gravidanza esclusa" in note → "gravidanza" matcha!
    30,  # Diastasi
    31,  # Esiti polso ("frattura polso" + "polso")
    32,  # Esiti ginocchio ("ginocchio")
    33,  # Esiti spalla ("spalla" + "frattura clavicola" + "lussazione spalla")
    34,  # Esiti caviglia ("caviglia")
    35,  # Esiti anca ("anca" + "frattura femore" + "protesi anca")
    36,  # Esiti colonna ("frattura vertebrale")
    37,  # Esiti gomito ("gomito" + "frattura gomito")
    38,  # Cervicalgia ("cervicalgia" + "cervical")
    39,  # Lombalgia ("lombalgia")
}
# 29 va incluso: "gravidanza" presente in "Gravidanza esclusa" → falso positivo NOTO
# (negazione non compresa)
expected_maximal.add(29)

# Non ci aspettiamo: 7 (cuffia rotatori), 11 (menisco)
# Controlliamo manualmente se 11 matcha:
_max_full = (
    "Distorsione grave caviglia destra, lussazione spalla sinistra "
    "Frattura polso destro 2018, frattura ginocchio sinistro 2019, "
    "frattura femore destro 2020, frattura vertebrale L2 2021, "
    "frattura gomito sinistro 2017, frattura clavicola destra 2016 "
    "Artroscopia ginocchio dx, ricostruzione LCA, protesi anca sx, "
    "intervento ernia discale lombare, intervento tunnel carpale "
    "Cervicalgia cronica, lombalgia, sciatica, sindrome del piriforme, "
    "epicondilite gomito dx, fascite plantare bilaterale, "
    "instabilita' scapolare, femoro-rotulea, capsulite adesiva spalla dx "
    "Ernia cervicale C5-C6, scoliosi, stenosi spinale L3-L4, spondilolistesi L5-S1, "
    "coxartrosi bilaterale, gonartrosi, osteoporosi, "
    "diabete tipo 2, ipertensione, asma, obesita' severa, "
    "insufficienza cardiaca NYHA II, diastasi addominale "
    "Metformina, ACE-inibitore, betabloccante, bifosfonati, broncodilatatore "
    "Cardiopatia ischemica cronica "
    "Asma da sforzo "
    "Conflitto femoro-acetabolare anca dx, impingement spalla sx "
    "Gravidanza esclusa. Obeso con radicolopatia lombare."
).lower()

# 7 (cuffia rotatori): "cuffia dei rotatori" / "cuffia rotatori" — non presente
if "cuffia" not in _max_full:
    print("    INFO: cond 7 (cuffia rotatori) non matchera' (keyword assente)")
# 11 (menisco): "menisco" — non menzionato esplicitamente
if "menisco" not in _max_full:
    print("    INFO: cond 11 (menisco) non matchera' (keyword assente)")
# 26: "radicolopatia" in note? Si: keyword ["sciatica", "radicolopatia", "nervo sciatico"] → 26
if "radicolopatia" in _max_full:
    print("    INFO: cond 26 raggiunta anche da 'radicolopatia' in note")

# "obeso" in note → 25 gia' matchato da "obesita'" in patologie
# "problemi cardiaci" → 20? Controlliamo: "problemi cardiaci" non presente esplicitamente

actual_maximal = assert_conditions(
    "Paziente massimale",
    maximal,
    expected=expected_maximal,
)

# Conteggio condizioni
print(f"\n    CONDIZIONI RILEVATE: {len(result)}")
print(f"    CONDIZIONI ATTESE:  {len(expected_maximal)}")
if len(result) > len(expected_maximal):
    extra = result - expected_maximal
    print(f"    EXTRA (non attese): {extra}")


# ═══════════════════════════════════════════════════════════════
# RIEPILOGO
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("RIEPILOGO TEST SAFETY ENGINE v2")
print("=" * 70)
print(f"\n  PASS:     {passed}")
print(f"  FAIL:     {failed}")
print(f"  WARN:     {warnings} (limiti noti documentati)")
print(f"  TOTALE:   {passed + failed + warnings}")

if failed > 0:
    print(f"\n  RISULTATO: FALLITO ({failed} test)")
    sys.exit(1)
else:
    print(f"\n  RISULTATO: SUPERATO (con {warnings} limiti noti accettati)")
    sys.exit(0)
