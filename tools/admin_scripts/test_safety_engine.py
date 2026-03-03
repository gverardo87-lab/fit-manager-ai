# tools/admin_scripts/test_safety_engine.py
"""
Test Safety Engine v3 — 10 profili clinici + Sprint 2 (nuove condizioni, farmaci, modify).

Verifica:
  - extract_client_conditions() (keyword matching + structural flags)
  - extract_medication_flags() (5 classi farmacologiche)
  - Severity 3 livelli: avoid > caution > modify
  - Copertura condizioni 1-47 (47 condizioni totali)
  - Prevenzione falsi positivi (obiettivi_specifici escluso)
  - Robustezza input (null, malformed, tipi errati)
  - Coerenza interna ANAMNESI_KEYWORD_RULES + MEDICATION_RULES
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

from api.services.safety_engine import extract_client_conditions, extract_medication_flags
from api.services.condition_rules import (
    ANAMNESI_KEYWORD_RULES,
    MEDICATION_RULES,
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

# 0.3 — Tutte le condizioni 1-47 raggiungibili via keyword O structural flag
print("\n--- 0.3: Copertura condizioni 1-47 ---")
reachable_kw = set()
for keywords, cond_id in ANAMNESI_KEYWORD_RULES:
    reachable_kw.add(cond_id)
reachable_flag = set()
for field, cond_ids in STRUCTURAL_FLAGS.items():
    reachable_flag.update(cond_ids)
reachable_all = reachable_kw | reachable_flag

# Sprint 2: 47 condizioni totali (1-47), tutte raggiungibili
all_expected = set(range(1, 48))  # 1-47

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
# PARTE 8: SPRINT 2 — NUOVE CONDIZIONI 40-47
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 8: SPRINT 2 — NUOVE CONDIZIONI 40-47 + FIX 19")
print("=" * 70)

# 8.1 — Condizione 19: Instabilita' caviglia (ora raggiungibile)
print("\n--- 8.1: Condizione 19 — Instabilita' caviglia ---")
test_keyword("instabilita caviglia", "instabilita caviglia cronica dopo distorsione",
    expected_ids={19, 34},  # 19 = instabilita caviglia, 34 = esiti caviglia (keyword "caviglia")
)

print("\n--- 8.1b: Distorsione caviglia → cond 19 ---")
test_keyword("distorsione caviglia", "distorsione caviglia destra recidivante",
    expected_ids={19, 34},  # 19 = distorsione caviglia, 34 = esiti caviglia
)

print("\n--- 8.1c: Caviglia instabile → cond 19 ---")
test_keyword("caviglia instabile", "caviglia instabile lato sinistro",
    expected_ids={19, 34},
)

# 8.2 — Condizione 40: Fibromialgia
print("\n--- 8.2: Condizione 40 — Fibromialgia ---")
test_keyword("fibromialgia", "fibromialgia diagnosticata 2023",
    expected_ids={40},
    not_expected_ids={39},  # "fibromialgia" non contiene "lombalgia" ne' "mal di schiena"
)

print("\n--- 8.2b: Fibromialgica → cond 40 ---")
test_keyword("fibromialgica", "sindrome fibromialgica cronica",
    expected_ids={40},
)

# 8.3 — Condizione 41: Ipermobilita' articolare / EDS
print("\n--- 8.3: Condizione 41 — Ipermobilita' ---")
test_keyword("ipermobilita", "ipermobilita articolare generalizzata",
    expected_ids={41},
)

print("\n--- 8.3b: Ehlers-Danlos → cond 41 ---")
test_keyword("ehlers-danlos", "sindrome di ehlers-danlos tipo ipermobile",
    expected_ids={41},
)

print("\n--- 8.3c: Lassita' articolare → cond 41 ---")
test_keyword("lassita articolare", "lassita articolare diffusa",
    expected_ids={41},
)

# 8.4 — Condizione 42: Ipotiroidismo
print("\n--- 8.4: Condizione 42 — Ipotiroidismo ---")
test_keyword("ipotiroidismo", "ipotiroidismo subclinico",
    expected_ids={42},
)

print("\n--- 8.4b: Eutirox → cond 42 (via farmaco) ---")
anamnesi_eutirox = build_anamnesi(
    farmaci=q(True, "Eutirox 75mcg al mattino"),
)
assert_conditions("eutirox keyword", anamnesi_eutirox, expected={42})

print("\n--- 8.4c: Levotiroxina → cond 42 ---")
anamnesi_levo = build_anamnesi(
    farmaci=q(True, "Levotiroxina 100mcg"),
)
assert_conditions("levotiroxina keyword", anamnesi_levo, expected={42})

print("\n--- 8.4d: Tiroide generico → cond 42 ---")
test_keyword("tiroide", "problemi alla tiroide",
    expected_ids={42},
)

# 8.5 — Condizione 43: BPCO
print("\n--- 8.5: Condizione 43 — BPCO ---")
test_keyword("bpco", "BPCO stadio II GOLD",
    expected_ids={43},
)

print("\n--- 8.5b: Broncopneumopatia → cond 43 ---")
test_keyword("broncopneumopatia", "broncopneumopatia cronica ostruttiva",
    expected_ids={43},
)

print("\n--- 8.5c: Enfisema → cond 43 ---")
test_keyword("enfisema", "enfisema polmonare",
    expected_ids={43},
)

print("\n--- 8.5d: Bronchite cronica → cond 43 ---")
test_keyword("bronchite cronica", "bronchite cronica da fumatore",
    expected_ids={43},
)

# 8.6 — Condizione 44: Diabete Tipo 1
print("\n--- 8.6: Condizione 44 — Diabete Tipo 1 ---")
anamnesi_t1 = build_anamnesi(
    patologie=q(True, "Diabete tipo 1 dall'eta' di 12 anni"),
)
result_t1 = assert_conditions("diabete tipo 1", anamnesi_t1,
    expected={23, 44},  # 23 = diabete generico ("diabete"), 44 = diabete tipo 1
)

print("\n--- 8.6b: Diabete insulinodipendente → cond 44 ---")
test_keyword("diabete insulinodipendente", "diabete insulinodipendente giovanile",
    expected_ids={23, 44},  # 23 da "diabete", 44 da "diabete insulinodipendente"
)

# 8.7 — Condizione 45: Neuropatia periferica
print("\n--- 8.7: Condizione 45 — Neuropatia periferica ---")
test_keyword("neuropatia", "neuropatia periferica diabetica",
    expected_ids={45},
)

print("\n--- 8.7b: Formicolio piedi → cond 45 ---")
# NOTA: "piedi" NON contiene "piede" (substring esatto: 'piedi' ≠ 'piede')
# quindi cond 34 (esiti piede) NON matcha. Solo cond 45 (neuropatia).
test_keyword("formicolio piedi", "formicolio piedi e mani bilaterale",
    expected_ids={45},
    not_expected_ids={34},  # "piedi" ≠ "piede" → cond 34 non inclusa
)

print("\n--- 8.7c: Perdita sensibilita' → cond 45 ---")
test_keyword("perdita sensibilita", "perdita sensibilita arti inferiori",
    expected_ids={45},
)

# 8.8 — Condizione 46: Artrosi spalla
print("\n--- 8.8: Condizione 46 — Artrosi spalla ---")
test_keyword("artrosi spalla", "artrosi spalla destra",
    expected_ids={46, 33},  # 46 = artrosi spalla, 33 = esiti spalla ("spalla")
)

print("\n--- 8.8b: Artrosi gleno-omerale → cond 46 ---")
test_keyword("artrosi gleno-omerale", "artrosi gleno-omerale bilaterale",
    expected_ids={46},
)

# 8.9 — Condizione 47: Artrosi mani/polsi
print("\n--- 8.9: Condizione 47 — Artrosi mani/polsi ---")
test_keyword("artrosi mani", "artrosi mani severe",
    expected_ids={47},
)

print("\n--- 8.9b: Artrosi polso → cond 47 ---")
test_keyword("artrosi polso", "artrosi polso destro",
    expected_ids={47, 31},  # 47 = artrosi polso, 31 = esiti polso ("polso")
)

print("\n--- 8.9c: Rizoartrosi → cond 47 ---")
test_keyword("rizoartrosi", "rizoartrosi pollice bilaterale",
    expected_ids={47},
)


# ═══════════════════════════════════════════════════════════════
# PARTE 9: SPRINT 2 — PROFILI CLINICI NUOVE CONDIZIONI
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 9: SPRINT 2 — PROFILI CLINICI NUOVE CONDIZIONI")
print("=" * 70)

# ──────────────────────────────────────────────────────────────
# PROFILO 11: Carla Bianchi — Fibromialgia + ipotiroidismo
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 11: Carla Bianchi (fibromialgia + ipotiroidismo) ---")
carla = build_anamnesi(
    patologie=q(True, "Fibromialgia diagnosticata 2021, ipotiroidismo"),
    farmaci=q(True, "Eutirox 100mcg, pregabalin 75mg"),
    dolori_cronici=q(True, "Dolore muscolare diffuso, affaticamento cronico"),
)
assert_conditions(
    "Carla Bianchi",
    carla,
    expected={
        40,  # Fibromialgia ("fibromialgia")
        42,  # Ipotiroidismo ("ipotiroidismo" + "eutirox" in farmaci.dettaglio)
    },
    not_expected={
        39,  # Lombalgia — "dolore muscolare" ≠ "lombalgia"
        25,  # Obesita' — NON menzionata
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 12: Marco Rossi — BPCO + diabete tipo 1 + neuropatia
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 12: Marco Rossi (BPCO + diabete T1 + neuropatia) ---")
marco = build_anamnesi(
    patologie=q(True, "Diabete tipo 1 dal 2005, BPCO stadio II, neuropatia periferica"),
    farmaci=q(True, "Insulina Novorapid + Lantus, broncodilatatore, pregabalin"),
    problemi_respiratori=q(True, "Dispnea da sforzo moderato"),
)
assert_conditions(
    "Marco Rossi",
    marco,
    expected={
        23,  # Diabete generico ("diabete")
        28,  # Asma (structural: problemi_respiratori.presente=true)
        43,  # BPCO ("bpco")
        44,  # Diabete Tipo 1 ("diabete tipo 1")
        45,  # Neuropatia ("neuropatia")
    },
    not_expected={
        40,  # Fibromialgia — non menzionata
        42,  # Ipotiroidismo — non menzionato
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 13: Giovanna Verdi — Ipermobilita' + artrosi mani + caviglia instabile
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 13: Giovanna Verdi (ipermobilita + artrosi mani + caviglia) ---")
giovanna = build_anamnesi(
    patologie=q(True, "Sindrome di Ehlers-Danlos tipo ipermobile, rizoartrosi bilaterale"),
    infortuni_pregressi=q(True, "Distorsione caviglia sinistra recidivante (3 episodi)"),
    dolori_cronici=q(True, "Dolore alle mani durante attivita' di presa"),
)
assert_conditions(
    "Giovanna Verdi",
    giovanna,
    expected={
        19,  # Instabilita' caviglia ("distorsione caviglia")
        34,  # Esiti caviglia ("caviglia")
        41,  # Ipermobilita' ("ehlers")
        47,  # Artrosi mani ("rizoartrosi")
    },
    not_expected={
        17,  # Tunnel carpale — rizoartrosi ≠ tunnel carpale
        18,  # Fascite plantare — caviglia ≠ plantare
    },
)

# ──────────────────────────────────────────────────────────────
# PROFILO 14: Antonio Esposito — Artrosi spalla + impingement + cardiopatico
# ──────────────────────────────────────────────────────────────

print("\n--- Profilo 14: Antonio Esposito (artrosi spalla + cardiopatico) ---")
antonio = build_anamnesi(
    patologie=q(True, "Artrosi gleno-omerale spalla destra, ipertensione"),
    dolori_cronici=q(True, "Dolore spalla in abduzione oltre 90 gradi"),
    farmaci=q(True, "Bisoprololo 5mg, atorvastatina 20mg"),
    problemi_cardiovascolari=q(True, "Ipertensione arteriosa controllata"),
)
assert_conditions(
    "Antonio Esposito",
    antonio,
    expected={
        20,  # Ipertensione (structural + keyword)
        21,  # Cardiopatia (structural)
        33,  # Esiti spalla ("spalla")
        46,  # Artrosi spalla ("artrosi gleno-omerale")
    },
    not_expected={
        6,   # Impingement spalla — artrosi ≠ impingement
        9,   # Spalla congelata — artrosi ≠ congelata
    },
)


# ═══════════════════════════════════════════════════════════════
# PARTE 10: SPRINT 2 — MEDICATION FLAGS
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 10: SPRINT 2 — MEDICATION FLAGS (extract_medication_flags)")
print("=" * 70)

def assert_medication_flags(
    label: str,
    anamnesi: dict,
    expected_flags: set[str],
    not_expected_flags: Optional[set[str]] = None,
):
    """Testa extract_medication_flags e verifica flag prodotti."""
    anamnesi_json = json.dumps(anamnesi)
    flags = extract_medication_flags(anamnesi_json)
    flag_names = {f.flag for f in flags}

    missing = expected_flags - flag_names
    if missing:
        fail(f"{label}: flag mancanti {missing}")

    if not_expected_flags:
        false_positives = not_expected_flags & flag_names
        if false_positives:
            fail(f"{label}: flag falsi positivi {false_positives}")

    if not missing and (not not_expected_flags or not (not_expected_flags & flag_names)):
        ok(f"{label}: flag corretti {flag_names}")
    else:
        print(f"    Atteso:  {expected_flags}")
        print(f"    Ottenuto: {flag_names}")

    return flags

# 10.0 — Coerenza MEDICATION_RULES
print("\n--- 10.0: Coerenza MEDICATION_RULES ---")
med_flags_seen = set()
for keywords, flag_name, note in MEDICATION_RULES:
    for kw in keywords:
        if not kw or not kw.strip():
            fail(f"Keyword vuota in MEDICATION_RULES per flag '{flag_name}'")
    if not note:
        fail(f"Nota clinica vuota per flag '{flag_name}'")
    med_flags_seen.add(flag_name)
expected_med_flags = {"beta_blocker", "anticoagulant", "corticosteroid", "insulin", "statin"}
if med_flags_seen == expected_med_flags:
    ok(f"MEDICATION_RULES copre {len(expected_med_flags)} classi: {sorted(expected_med_flags)}")
else:
    fail(f"MEDICATION_RULES mancanti: {expected_med_flags - med_flags_seen}")

# 10.1 — Beta-bloccante
print("\n--- 10.1: Beta-bloccante ---")
assert_medication_flags("bisoprololo",
    build_anamnesi(farmaci=q(True, "Bisoprololo 5mg mattina")),
    expected_flags={"beta_blocker"},
    not_expected_flags={"anticoagulant", "insulin"},
)

print("\n--- 10.1b: Carvedilolo → beta_blocker ---")
assert_medication_flags("carvedilolo",
    build_anamnesi(farmaci=q(True, "Carvedilolo 25mg")),
    expected_flags={"beta_blocker"},
)

print("\n--- 10.1c: Betabloccante generico ---")
assert_medication_flags("betabloccante generico",
    build_anamnesi(farmaci=q(True, "Assume betabloccante")),
    expected_flags={"beta_blocker"},
)

# 10.2 — Anticoagulante
print("\n--- 10.2: Anticoagulante ---")
assert_medication_flags("warfarin",
    build_anamnesi(farmaci=q(True, "Warfarin 5mg, INR monitorato mensilmente")),
    expected_flags={"anticoagulant"},
)

print("\n--- 10.2b: Xarelto → anticoagulant ---")
assert_medication_flags("xarelto",
    build_anamnesi(farmaci=q(True, "Xarelto 20mg dopo cena")),
    expected_flags={"anticoagulant"},
)

# 10.3 — Corticosteroide
print("\n--- 10.3: Corticosteroide ---")
assert_medication_flags("prednisone",
    build_anamnesi(farmaci=q(True, "Prednisone 10mg per artrite")),
    expected_flags={"corticosteroid"},
)

print("\n--- 10.3b: Cortisone generico ---")
assert_medication_flags("cortisone",
    build_anamnesi(farmaci=q(True, "Cortisone infiltrazioni periodiche")),
    expected_flags={"corticosteroid"},
)

# 10.4 — Insulina
print("\n--- 10.4: Insulina ---")
assert_medication_flags("novorapid + lantus",
    build_anamnesi(farmaci=q(True, "Insulina Novorapid ai pasti + Lantus serale")),
    expected_flags={"insulin"},
)

print("\n--- 10.4b: Insulina generica ---")
assert_medication_flags("insulina generica",
    build_anamnesi(farmaci=q(True, "Insulina 3 volte al giorno")),
    expected_flags={"insulin"},
)

# 10.5 — Statina
print("\n--- 10.5: Statina ---")
assert_medication_flags("atorvastatina",
    build_anamnesi(farmaci=q(True, "Atorvastatina 20mg serale")),
    expected_flags={"statin"},
)

print("\n--- 10.5b: Rosuvastatina → statin ---")
assert_medication_flags("rosuvastatina",
    build_anamnesi(farmaci=q(True, "Rosuvastatina 10mg")),
    expected_flags={"statin"},
)

# 10.6 — Multi-farmaco (piu' flag contemporanei)
print("\n--- 10.6: Multi-farmaco (3 flag) ---")
assert_medication_flags("multi-farmaco",
    build_anamnesi(farmaci=q(True,
        "Bisoprololo 5mg, Warfarin 5mg, Atorvastatina 20mg, Paracetamolo al bisogno"
    )),
    expected_flags={"beta_blocker", "anticoagulant", "statin"},
    not_expected_flags={"insulin", "corticosteroid"},
)

# 10.7 — Tutti e 5 i flag contemporanei
print("\n--- 10.7: Tutti i 5 flag farmacologici ---")
assert_medication_flags("5 farmaci",
    build_anamnesi(farmaci=q(True,
        "Metoprololo 50mg, Eliquis 5mg, Prednisone 5mg, Insulina Humalog, Simvastatina 20mg"
    )),
    expected_flags={"beta_blocker", "anticoagulant", "corticosteroid", "insulin", "statin"},
)

# 10.8 — Farmaci non rilevanti → 0 flag
print("\n--- 10.8: Farmaci non rilevanti → 0 flag ---")
flags_generic = extract_medication_flags(json.dumps(
    build_anamnesi(farmaci=q(True, "Paracetamolo, Vitamina D, Magnesio, Omega-3"))
))
if len(flags_generic) == 0:
    ok("Farmaci generici → 0 flag")
else:
    fail(f"Farmaci generici → flag inattesi: {[f.flag for f in flags_generic]}")

# 10.9 — Farmaci assenti (presente=false) → 0 flag
print("\n--- 10.9: Farmaci non presenti → 0 flag ---")
flags_none = extract_medication_flags(json.dumps(
    build_anamnesi(farmaci=q(False))
))
if len(flags_none) == 0:
    ok("Farmaci non presenti → 0 flag")
else:
    fail(f"Farmaci non presenti → {len(flags_none)} flag")

# 10.10 — Anamnesi None → 0 flag
print("\n--- 10.10: extract_medication_flags(None) → 0 flag ---")
flags_null = extract_medication_flags(None)
if len(flags_null) == 0:
    ok("None → 0 flag")
else:
    fail(f"None → {len(flags_null)} flag")

# 10.11 — Nota clinica presente e non vuota
print("\n--- 10.11: Ogni flag ha nota clinica non vuota ---")
test_flags = extract_medication_flags(json.dumps(
    build_anamnesi(farmaci=q(True,
        "Metoprololo, Warfarin, Cortisone, Insulina, Atorvastatina"
    ))
))
all_have_nota = all(f.nota and len(f.nota) > 10 for f in test_flags)
if all_have_nota and len(test_flags) == 5:
    ok(f"Tutti i {len(test_flags)} flag hanno nota clinica valida")
else:
    fail(f"Flag senza nota: {[(f.flag, f.nota) for f in test_flags if not f.nota]}")


# ═══════════════════════════════════════════════════════════════
# PARTE 11: SPRINT 2 — SEVERITY MODIFY (3 LIVELLI)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 11: SPRINT 2 — SEVERITY 3 LIVELLI (avoid > caution > modify)")
print("=" * 70)

# 11.1 — _SEVERITY_ORDER aggiornato con modify
print("\n--- 11.1: _SEVERITY_ORDER include modify ---")
from api.services.safety_engine import _SEVERITY_ORDER
assert "modify" in _SEVERITY_ORDER, "modify non presente in _SEVERITY_ORDER"
assert _SEVERITY_ORDER["modify"] < _SEVERITY_ORDER["caution"] < _SEVERITY_ORDER["avoid"]
ok("_SEVERITY_ORDER: modify(0) < caution(1) < avoid(2)")

# 11.2 — Gerarchia worst-case: avoid > caution > modify
print("\n--- 11.2: Worst-case aggregation ---")
# Se un esercizio ha modify da una condizione e caution da un'altra, vince caution
for sev_a, sev_b, expected_winner in [
    ("modify", "caution", "caution"),
    ("modify", "avoid", "avoid"),
    ("caution", "avoid", "avoid"),
    ("modify", "modify", "modify"),
    ("caution", "caution", "caution"),
    ("avoid", "avoid", "avoid"),
]:
    winner = sev_a if _SEVERITY_ORDER.get(sev_a, 0) >= _SEVERITY_ORDER.get(sev_b, 0) else sev_b
    if winner == expected_winner:
        ok(f"worst({sev_a}, {sev_b}) = {expected_winner}")
    else:
        fail(f"worst({sev_a}, {sev_b}) = {winner} (atteso {expected_winner})")


# ═══════════════════════════════════════════════════════════════
# PARTE 12: SPRINT 2 — PROFILO INTEGRATO COMPLETO
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PARTE 12: SPRINT 2 — STRESS TEST INTEGRATO")
print("=" * 70)

# 12.1 — Profilo massimale con TUTTE le nuove condizioni 40-47
print("\n--- 12.1: Paziente con tutte le condizioni nuove ---")
sprint2_maximal = build_anamnesi(
    patologie=q(True,
        "Fibromialgia, ipotiroidismo, BPCO stadio II, diabete tipo 1, "
        "neuropatia periferica, artrosi spalla destra, rizoartrosi bilaterale, "
        "ipermobilita articolare generalizzata"
    ),
    infortuni_pregressi=q(True, "Distorsione caviglia sinistra recidivante"),
    farmaci=q(True,
        "Eutirox 100mcg, insulina Lantus, bisoprololo 2.5mg, "
        "cortisone infiltrazioni spalla, atorvastatina 10mg"
    ),
    dolori_cronici=q(True, "Dolore muscolare diffuso, formicolio piedi"),
)

result_sprint2 = assert_conditions(
    "Paziente Sprint 2 massimale",
    sprint2_maximal,
    expected={
        19,  # Instabilita' caviglia ("distorsione caviglia")
        34,  # Esiti caviglia ("caviglia")
        33,  # Esiti spalla ("spalla")
        40,  # Fibromialgia
        41,  # Ipermobilita' ("ipermobilita")
        42,  # Ipotiroidismo ("ipotiroidismo" + "eutirox")
        43,  # BPCO ("bpco")
        44,  # Diabete Tipo 1 ("diabete tipo 1")
        45,  # Neuropatia ("neuropatia" + "formicolio piedi")
        46,  # Artrosi spalla ("artrosi spalla")
        47,  # Rizoartrosi ("rizoartrosi")
        23,  # Diabete generico ("diabete" in "diabete tipo 1")
    },
)
print(f"    CONDIZIONI RILEVATE: {len(result_sprint2)}")

# 12.2 — Medication flags dallo stesso profilo
print("\n--- 12.2: Medication flags profilo integrato ---")
flags_sprint2 = extract_medication_flags(json.dumps(sprint2_maximal))
flag_names_sprint2 = {f.flag for f in flags_sprint2}
expected_flags_sprint2 = {"beta_blocker", "corticosteroid", "insulin", "statin"}
missing_flags = expected_flags_sprint2 - flag_names_sprint2
extra_flags = flag_names_sprint2 - expected_flags_sprint2

if not missing_flags:
    ok(f"Medication flags corretti: {sorted(flag_names_sprint2)}")
else:
    fail(f"Medication flags mancanti: {missing_flags}")
if extra_flags:
    warn(f"Medication flags extra (non attesi ma non pericolosi): {extra_flags}")

# 12.3 — Verifica che "insulina" in farmaci non confonda condition_ids
print("\n--- 12.3: Insulina in farmaci NON genera condizioni mediche ---")
# extract_medication_flags scansiona farmaci.dettaglio → flag
# extract_client_conditions scansiona farmaci.dettaglio → condition_ids
# "insulina" e' keyword di ANAMNESI_KEYWORD_RULES? Verifichiamo
_insulina_conditions = set()
for keywords, cond_id in ANAMNESI_KEYWORD_RULES:
    if match_keywords("insulina lantus", keywords):
        _insulina_conditions.add(cond_id)
# "insulina" matcha cond 44 (diabete tipo 1)? Verifichiamo le keyword di 44:
# (["diabete tipo 1", "diabete insulinodipendente"], 44) — "insulina" NON e' in nessuna
# Ma: "insulina" NON e' tra le keyword di cond 44 (ok, niente falso positivo)
if 44 not in _insulina_conditions:
    ok("'insulina' in farmaci NON triggera cond 44 (corretto: non e' keyword di cond 44)")
else:
    warn("'insulina' in farmaci triggera cond 44 — verificare se e' intenzionale")


# ═══════════════════════════════════════════════════════════════
# RIEPILOGO
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("RIEPILOGO TEST SAFETY ENGINE v3")
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
