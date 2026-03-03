#!/usr/bin/env python3
"""
Seed QA Clinical — 30 clienti x 6 lotti per stress-test pipeline clinica.

Crea un database di test dedicato con profili clinici completi per verificare:
- Safety Engine (extract_conditions -> safety_map -> UI 3-severity)
- Clinical Analysis (derived metrics, rate assessment, composition phases,
  bilateral symmetry, risk profile)
- Smart Programming Engine (safety/strength/bilateral scorer)
- Goal tracking + auto-completion

6 LOTTI (5 clienti ciascuno):
  Lotto 1: Baseline Sano (nessuna condizione, 5 composition phases)
  Lotto 2: Singola Condizione Ortopedica (keyword matching preciso)
  Lotto 3: Cardiovascolare + Farmacologico (structural flags + medication rules)
  Lotto 4: Multi-Condizione + Composizione Critica (3-5 condizioni, CRITICAL/MUSCLE_LOSS)
  Lotto 5: Popolazioni Speciali (gravidanza, anziani, colonna complessa)
  Lotto 6: Atleti + Edge Cases (FFMI alto, dati insufficienti, bilateral alert)

COPERTURA: 47/47 condizioni, 5/5 medication flags, 7/8 composition phases.

PREREQUISITO: crm.db deve esistere con esercizi e tassonomia.
Il script copia automaticamente esercizi/tassonomia da crm.db se necessario.

Uso: python -m tools.admin_scripts.seed_qa_clinical
"""

import json
import os
import random
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ── Forza DATABASE_URL su crm_dev.db PRIMA di qualsiasi import ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
os.environ["DATABASE_URL"] = f"sqlite:///{DATA_DIR / 'crm_dev.db'}"

sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, create_engine, text  # noqa: E402

from api.auth.service import hash_password  # noqa: E402
from api.models.client import Client  # noqa: E402
from api.models.goal import ClientGoal  # noqa: E402
from api.models.measurement import (  # noqa: E402
    ClientMeasurement,
    MeasurementValue,
    Metric,
)
from api.models.trainer import Trainer  # noqa: E402

# Determinismo
random.seed(42)

TODAY = date(2026, 2, 23)


# ═══════════════════════════════════════════════════════════════
# SECTION 1: Helpers
# ═══════════════════════════════════════════════════════════════

def _mk_anamnesi(**kwargs):
    """Build AnamnesiData dict con defaults (tutti false/vuoti).

    Shorthand: passare stringa per un campo setta presente=True + dettaglio=str.
    Campi speciali (limitazioni_funzionali, note, obiettivi_specifici): stringa diretta.
    """
    base = {
        "infortuni_attuali": {"presente": False, "dettaglio": ""},
        "infortuni_pregressi": {"presente": False, "dettaglio": ""},
        "interventi_chirurgici": {"presente": False, "dettaglio": ""},
        "dolori_cronici": {"presente": False, "dettaglio": ""},
        "patologie": {"presente": False, "dettaglio": ""},
        "farmaci": {"presente": False, "dettaglio": ""},
        "problemi_cardiovascolari": {"presente": False, "dettaglio": ""},
        "problemi_respiratori": {"presente": False, "dettaglio": ""},
        "dieta_particolare": {"presente": False, "dettaglio": ""},
        # Metadata richiesti da isStructuredAnamnesi() nel frontend
        "data_compilazione": "2025-06-01",
        "data_ultimo_aggiornamento": "2025-06-01",
    }
    for key, val in kwargs.items():
        if key in ("limitazioni_funzionali", "note", "obiettivi_specifici",
                    "data_compilazione", "data_ultimo_aggiornamento"):
            base[key] = val
        elif isinstance(val, str):
            base[key] = {"presente": True, "dettaglio": val}
        elif isinstance(val, dict):
            base[key] = val
    return base


def _gen_series(start_val, end_val, n, noise_pct=0.005):
    """Genera serie con trend lineare + rumore gaussiano."""
    values = []
    for i in range(n):
        t = i / max(1, n - 1)
        base = start_val + (end_val - start_val) * t
        noise = random.gauss(0, abs(base) * noise_pct) if base != 0 else 0
        values.append(round(base + noise, 1))
    return values


def _gen_measurements(profile):
    """Genera lista di sessioni di misurazione da un profilo compatto.

    Profile format: {
        "n": int, "start": date, "iv": int (interval days),
        "metrics": [(metric_id, start_val, end_val), ...]
        # end_val = None → solo prima sessione (es. altezza)
    }
    Returns: list of (date, dict[metric_id, value])
    """
    n = profile["n"]
    start = profile["start"]
    iv = profile["iv"]
    sessions = []

    for i in range(n):
        d = start + timedelta(days=iv * i)
        values = {}
        for metric_id, s_val, e_val in profile["metrics"]:
            if e_val is None:
                # Solo prima sessione
                if i == 0:
                    values[metric_id] = s_val
                continue
            t = i / max(1, n - 1)
            base = s_val + (e_val - s_val) * t
            noise_pct = 0.003 if metric_id in (17, 18, 19) else 0.005
            noise = random.gauss(0, abs(base) * noise_pct) if base != 0 else 0
            values[metric_id] = round(base + noise, 1)
        sessions.append((d, values))

    return sessions


METRICS_SEED = [
    ("Peso Corporeo", "Body Weight", "kg", "antropometrica", 1),
    ("Altezza", "Height", "cm", "antropometrica", 2),
    ("Massa Grassa", "Body Fat", "%", "composizione", 1),
    ("Massa Magra", "Lean Mass", "kg", "composizione", 2),
    ("BMI", "BMI", "kg/m\u00b2", "composizione", 3),
    ("Acqua Corporea", "Body Water", "%", "composizione", 4),
    ("Collo", "Neck", "cm", "circonferenza", 1),
    ("Petto", "Chest", "cm", "circonferenza", 2),
    ("Vita", "Waist", "cm", "circonferenza", 3),
    ("Fianchi", "Hips", "cm", "circonferenza", 4),
    ("Braccio Destro", "Right Arm", "cm", "circonferenza", 5),
    ("Braccio Sinistro", "Left Arm", "cm", "circonferenza", 6),
    ("Coscia Destra", "Right Thigh", "cm", "circonferenza", 7),
    ("Coscia Sinistra", "Left Thigh", "cm", "circonferenza", 8),
    ("Polpaccio Destro", "Right Calf", "cm", "circonferenza", 9),
    ("Polpaccio Sinistro", "Left Calf", "cm", "circonferenza", 10),
    ("FC Riposo", "Resting HR", "bpm", "cardiovascolare", 1),
    ("PA Sistolica", "Systolic BP", "mmHg", "cardiovascolare", 2),
    ("PA Diastolica", "Diastolic BP", "mmHg", "cardiovascolare", 3),
    ("Squat 1RM", "Squat 1RM", "kg", "forza", 1),
    ("Panca Piana 1RM", "Bench Press 1RM", "kg", "forza", 2),
    ("Stacco da Terra 1RM", "Deadlift 1RM", "kg", "forza", 3),
]


# ═══════════════════════════════════════════════════════════════
# SECTION 2: 30 Clienti (6 lotti x 5)
# ═══════════════════════════════════════════════════════════════

CLIENTS_DATA = [
    # ── Lotto 1: Baseline Sano ──
    {"nome": "Alessia",    "cognome": "Marchetti",  "tel": "333-1001001", "email": "alessia.marchetti@gmail.com",    "nascita": date(1991, 4, 12),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Marco",      "cognome": "Bianchi",    "tel": "320-4004004", "email": "marco.bianchi@libero.it",       "nascita": date(1985, 7, 18),  "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Sara",       "cognome": "Romano",     "tel": "338-5005005", "email": "sara.romano@gmail.com",         "nascita": date(1993, 3, 9),   "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Luca",       "cognome": "Colombo",    "tel": "340-6006006", "email": "luca.colombo@outlook.it",       "nascita": date(1990, 11, 30), "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Elena",      "cognome": "Vitale",     "tel": "350-2610026", "email": "elena.vitale@gmail.com",        "nascita": date(1999, 1, 16),  "sesso": "Donna", "stato": "Attivo"},
    # ── Lotto 2: Singola Condizione Ortopedica ──
    {"nome": "Francesco",  "cognome": "Russo",      "tel": "339-2002002", "email": "f.russo@hotmail.it",            "nascita": date(1988, 9, 5),   "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Giulia",     "cognome": "Ferrari",    "tel": "347-3003003", "email": "giulia.ferrari@gmail.com",      "nascita": date(1995, 1, 22),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Andrea",     "cognome": "Moretti",    "tel": "328-8008008", "email": "andrea.moretti@gmail.com",      "nascita": date(1992, 2, 28),  "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Valentina",  "cognome": "Ricci",      "tel": "349-7007007", "email": "vale.ricci@gmail.com",          "nascita": date(1987, 6, 14),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Davide",     "cognome": "Gallo",      "tel": "331-1010010", "email": "davide.gallo@gmail.com",        "nascita": date(1983, 12, 25), "sesso": "Uomo",  "stato": "Attivo"},
    # ── Lotto 3: Cardiovascolare + Farmacologico ──
    {"nome": "Stefano",    "cognome": "Leone",      "tel": "341-1810018", "email": "stefano.leone@gmail.com",       "nascita": date(1982, 1, 6),   "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Roberta",    "cognome": "Longo",      "tel": "330-1910019", "email": "roberta.longo@yahoo.it",        "nascita": date(1993, 9, 14),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Giovanni",   "cognome": "Ferri",      "tel": "348-4210042", "email": "giovanni.ferri@gmail.com",      "nascita": date(1977, 12, 7),  "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Teresa",     "cognome": "Vitali",     "tel": "335-4310043", "email": "teresa.vitali@libero.it",       "nascita": date(1980, 3, 18),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Grazia",     "cognome": "Lombardo",   "tel": "336-4510045", "email": "grazia.lombardo@yahoo.it",      "nascita": date(1981, 5, 13),  "sesso": "Donna", "stato": "Attivo"},
    # ── Lotto 4: Multi-Condizione + Composizione Critica ──
    {"nome": "Massimo",    "cognome": "Lombardi",   "tel": "342-3810038", "email": "massimo.lombardi@yahoo.it",     "nascita": date(1978, 8, 14),  "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Patrizia",   "cognome": "Parisi",     "tel": "331-3710037", "email": "patrizia.parisi@gmail.com",     "nascita": date(1975, 4, 3),   "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Giuseppe",   "cognome": "Gentile",    "tel": "327-4010040", "email": "giuseppe.gentile@gmail.com",    "nascita": date(1976, 6, 10),  "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Antonella",  "cognome": "Valentini",  "tel": "334-4110041", "email": "antonella.v@hotmail.it",        "nascita": date(1983, 9, 25),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Vincenzo",   "cognome": "Amato",      "tel": "329-4410044", "email": "vincenzo.amato@gmail.com",      "nascita": date(1974, 7, 31),  "sesso": "Uomo",  "stato": "Inattivo"},
    # ── Lotto 5: Popolazioni Speciali ──
    {"nome": "Francesca",  "cognome": "Fabbri",     "tel": "340-3310033", "email": "francesca.fabbri@gmail.com",    "nascita": date(1993, 9, 20),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Nicola",     "cognome": "Marchese",   "tel": "349-3410034", "email": "nicola.marchese@hotmail.it",    "nascita": date(1980, 2, 8),   "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Paola",      "cognome": "Sorrentino", "tel": "345-3910039", "email": "paola.sorrentino@gmail.com",    "nascita": date(1982, 1, 29),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Roberto",    "cognome": "Palumbo",    "tel": "335-3610036", "email": "roberto.palumbo@libero.it",     "nascita": date(1979, 11, 22), "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Ilaria",     "cognome": "Sartori",    "tel": "328-3510035", "email": "ilaria.sartori@gmail.com",      "nascita": date(1993, 10, 1),  "sesso": "Donna", "stato": "Attivo"},
    # ── Lotto 6: Atleti + Edge Cases ──
    {"nome": "Lorenzo",    "cognome": "Santoro",    "tel": "329-1610016", "email": "lorenzo.santoro@outlook.it",    "nascita": date(1984, 3, 17),  "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Sofia",      "cognome": "Gatti",      "tel": "328-3512035", "email": "sofia.gatti@gmail.com",         "nascita": date(1998, 6, 17),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Edoardo",    "cognome": "Neri",       "tel": "330-4710047", "email": "edoardo.neri@outlook.it",       "nascita": date(1999, 8, 6),   "sesso": "Uomo",  "stato": "Attivo"},
    {"nome": "Claudia",    "cognome": "Pellegrini", "tel": "326-2310023", "email": "claudia.pellegrini@gmail.com",  "nascita": date(1994, 6, 30),  "sesso": "Donna", "stato": "Attivo"},
    {"nome": "Simone",     "cognome": "Giordano",   "tel": "345-1210012", "email": "simone.giordano@gmail.com",     "nascita": date(1989, 10, 19), "sesso": "Uomo",  "stato": "Attivo"},
]


# ═══════════════════════════════════════════════════════════════
# SECTION 3: Anamnesi (formato AnamnesiData strutturato)
# ═══════════════════════════════════════════════════════════════
# Indici corrispondono a CLIENTS_DATA. None = nessuna anamnesi.
# _mk_anamnesi(): shorthand per dati strutturati.

ANAMNESI = {
    # ── Lotto 1: Baseline Sano (nessuna condizione) ──
    0: None,
    1: _mk_anamnesi(),  # tutti false → 0 condizioni
    2: _mk_anamnesi(
        obiettivi_specifici="Perdere peso e tonificare gambe e glutei",
    ),  # obiettivi esclusi da scanning → 0 condizioni
    3: None,
    4: None,

    # ── Lotto 2: Singola Condizione Ortopedica ──
    # Client 5: Ernia L4-L5 → {1, 39}
    5: _mk_anamnesi(
        infortuni_pregressi="Ernia L4-L5 operata nel 2021, microdiscectomia",
        dolori_cronici="Lombalgia cronica residua, gestita con stretching quotidiano",
        interventi_chirurgici="Microdiscectomia L4-L5 ottobre 2021",
        limitazioni_funzionali="Evitare carichi assiali pesanti e flessione lombare sotto carico",
        obiettivi_specifici="Rinforzare il core e migliorare la stabilita lombare",
    ),
    # Client 6: Post-ACL + menisco → {10, 11, 32}
    6: _mk_anamnesi(
        interventi_chirurgici="Ricostruzione LCA e meniscectomia parziale ginocchio destro, maggio 2023",
        infortuni_pregressi="Distorsione ginocchio destro con rottura LCA e lesione menisco mediale",
        limitazioni_funzionali="Deficit propriocettivo ginocchio destro residuo",
    ),
    # Client 7: Impingement spalla + cuffia rotatori + cortisone → {6, 7, 33}
    7: _mk_anamnesi(
        infortuni_attuali="Impingement subacromiale spalla destra con tendinopatia cuffia dei rotatori",
        farmaci="Cortisone locale, infiltrazioni periodiche ogni 3-4 mesi",
        limitazioni_funzionali="ROM spalla destra limitato in abduzione oltre 120 gradi",
    ),
    # Client 8: Fascite plantare → {18, 34}
    8: _mk_anamnesi(
        dolori_cronici="Fascite plantare bilaterale, dolore al piede durante attivita in carico",
        limitazioni_funzionali="Evitare impatto ripetuto e stazione eretta prolungata",
    ),
    # Client 9: Scoliosi → {3}
    9: _mk_anamnesi(
        patologie="Scoliosi dorsale diagnosticata in eta adolescenziale, convessita destra",
        note="Monitoraggio annuale con ortopedico, no intervento previsto",
    ),

    # ── Lotto 3: Cardiovascolare + Farmacologico ──
    # Client 10: Ipertensione controllata → {20, 21}, meds: [beta_blocker]
    10: _mk_anamnesi(
        problemi_cardiovascolari="Ipertensione arteriosa essenziale, in trattamento farmacologico da 5 anni",
        farmaci="Bisoprololo 5mg giornaliero per controllo pressione arteriosa",
    ),
    # Client 11: Diabete T2 → {23}, meds: [statin]
    11: _mk_anamnesi(
        patologie="Diabete tipo 2 diagnosticato nel 2020, controllato con dieta e farmaci",
        farmaci="Metformina 1000mg due volte al giorno. Atorvastatina 20mg per colesterolo",
        dieta_particolare="Dieta ipoglicemica, pasti regolari ogni 3-4 ore",
    ),
    # Client 12: Insufficienza cardiaca → {20, 21, 22}, meds: [beta_blocker, anticoagulant]
    12: _mk_anamnesi(
        problemi_cardiovascolari="Insufficienza cardiaca cronica NYHA classe II, cardiopatia ischemica",
        farmaci="Metoprololo 50mg mattina e sera. Eliquis 5mg due volte al giorno",
        limitazioni_funzionali="Evitare sforzi massimali e manovra di Valsalva. FC max 70% teorica",
    ),
    # Client 13: Diabete T1 → {23, 44}, meds: [insulin]
    13: _mk_anamnesi(
        patologie="Diabete tipo 1 dall'eta di 12 anni, insulinodipendente",
        farmaci="Insulina Novorapid ai pasti, Lantus 20 unita serale",
        note="Porta sempre zuccheri rapidi durante allenamento. Sensore glicemia Libre",
    ),
    # Client 14: Asma + BPCO → {28, 43}
    14: _mk_anamnesi(
        problemi_respiratori="Asma da sforzo dall'infanzia, BPCO lieve diagnosticata nel 2022",
        farmaci="Ventolin al bisogno, Spiriva inalatore giornaliero",
        limitazioni_funzionali="Dispnea sotto sforzo intenso. Evitare allenamenti in ambiente freddo",
    ),

    # ── Lotto 4: Multi-Condizione + Composizione Critica ──
    # Client 15: Obesita + ipertensione + artrosi ginocchio + femoro-rotulea
    #   → {12, 13, 20, 21, 25, 32}
    15: _mk_anamnesi(
        problemi_cardiovascolari="Ipertensione arteriosa in trattamento",
        patologie="Obesita di secondo grado, artrosi ginocchio destro con sindrome femoro-rotulea",
        dolori_cronici="Dolore al ginocchio destro durante le scale e squat",
        limitazioni_funzionali="Evitare impatto e flessione profonda ginocchio",
    ),
    # Client 16: Diabete T2 + obesita + sciatica + piriforme → {23, 25, 26, 27, 35}
    16: _mk_anamnesi(
        patologie="Diabete tipo 2, obesita di primo grado",
        dolori_cronici="Sciatica ricorrente con sindrome del piriforme destro",
        limitazioni_funzionali="Dolore irradiato gamba destra in flessione anca sotto carico",
    ),
    # Client 17: Cardiopatia + ernia cervicale + tunnel carpale + polso
    #   → {1, 2, 17, 20, 21, 31, 38}
    17: _mk_anamnesi(
        problemi_cardiovascolari="Cardiopatia ipertensiva",
        patologie="Ernia cervicale C5-C6, sindrome del tunnel carpale bilaterale",
        dolori_cronici="Dolore cervicale cronico, formicolio e dolore al polso bilaterale",
        limitazioni_funzionali="Evitare posizioni cervicali estreme e presa prolungata",
    ),
    # Client 18: Fibromialgia + ipermobilita + cervicalgia → {38, 40, 41}
    18: _mk_anamnesi(
        patologie="Fibromialgia diagnosticata nel 2019",
        limitazioni_funzionali="Ipermobilita articolare generalizzata, cervicalgia cronica",
        note="Dolore diffuso variabile, peggiorato da stress. Preferire intensita bassa-moderata",
    ),
    # Client 19: Osteoporosi + neuropatia + diabete T2 → {23, 24, 45}
    19: _mk_anamnesi(
        patologie="Osteoporosi vertebrale, diabete tipo 2 in compenso farmacologico",
        dolori_cronici="Neuropatia periferica arti inferiori con formicolio piedi",
        limitazioni_funzionali="Propriocezione ridotta piedi, rischio caduta",
    ),

    # ── Lotto 5: Popolazioni Speciali ──
    # Client 20: Post-partum + diastasi → {29, 30}
    20: _mk_anamnesi(
        patologie="Diastasi dei retti addominali di circa 2.5cm",
        note="Parto naturale 4 mesi fa, gravidanza decorso regolare",
        limitazioni_funzionali="Evitare crunch e movimenti che aumentano pressione intra-addominale",
    ),
    # Client 21: FAI anca + coxartrosi → {14, 15, 35}
    21: _mk_anamnesi(
        patologie="Coxartrosi anca destra, conflitto femoro-acetabolare",
        interventi_chirurgici="Artroscopia anca destra 2020 per rimozione osteofiti",
        limitazioni_funzionali="Flessione anca limitata a 90 gradi, evitare squat profondo",
    ),
    # Client 22: Capsulite + instabilita scapolare + artrosi spalla → {8, 9, 33, 46}
    22: _mk_anamnesi(
        patologie="Capsulite adesiva spalla sinistra con instabilita scapolare associata",
        dolori_cronici="Artrosi gleno-omerale spalla sinistra con limitazione ROM severa",
        limitazioni_funzionali="ROM spalla sinistra: abduzione 80, flessione 90, rotazione esterna 20",
    ),
    # Client 23: Spondilolistesi + stenosi spinale → {1, 4, 5, 36}
    23: _mk_anamnesi(
        patologie="Spondilolistesi L5-S1 grado I, stenosi spinale lombare",
        interventi_chirurgici="Intervento colonna vertebrale di stabilizzazione L5-S1 nel 2019",
        limitazioni_funzionali="Evitare iperestensione lombare e carichi assiali pesanti",
    ),
    # Client 24: Ipotiroidismo + artrosi mani → {42, 47}
    24: _mk_anamnesi(
        patologie="Ipotiroidismo in trattamento con Eutirox, rizoartrosi bilaterale mani",
        farmaci="Eutirox 75mcg giornaliero a digiuno",
        limitazioni_funzionali="Presa dolorosa con carichi pesanti, adattare impugnature",
    ),

    # ── Lotto 6: Atleti + Edge Cases ──
    # Client 25: Epicondilite + polso generico → {16, 31, 37}
    25: _mk_anamnesi(
        infortuni_attuali="Epicondilite al gomito destro, in fase di risoluzione",
        limitazioni_funzionali="Evitare presa forte e movimenti ripetitivi polso",
    ),
    # Client 26: Sana (optimal growth)
    26: None,
    # Client 27: Sano (prospect, dati insufficienti)
    27: None,
    # Client 28: Instabilita caviglia + frattura polso → {19, 31, 34}
    28: _mk_anamnesi(
        infortuni_pregressi="Distorsione caviglia destra recidivante, caviglia instabile",
        interventi_chirurgici="Frattura al polso sinistro 2021, fissazione con placca e viti",
        limitazioni_funzionali="Instabilita caviglia destra su superfici irregolari, grip sx limitato",
    ),
    # Client 29: Sano (borderline PA)
    29: None,
}


# ═══════════════════════════════════════════════════════════════
# SECTION 4: Profili Misurazione (30 clienti)
# ═══════════════════════════════════════════════════════════════
# Format: "n" sessions, "start" date, "iv" interval days
# metrics: [(metric_id, start_value, end_value)]
#   end_value = None → solo prima sessione (altezza)

MEASUREMENT_PROFILES = {
    # ── Lotto 1: Baseline Sano ──

    # #0 Alessia 35F — CUTTING (peso↓ grasso%↓)
    0: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 68.0, 63.0), (2, 165.0, None), (3, 22.0, 17.0),
        (9, 74.0, 69.0), (10, 98.0, 95.0), (17, 68, 62),
        (11, 28.0, 28.0), (12, 27.8, 27.8), (13, 52.0, 52.0),
        (14, 51.8, 51.8), (15, 36.0, 36.0), (16, 35.9, 35.9),
        (20, 55.0, 80.0), (21, 30.0, 45.0), (22, 65.0, 95.0),
    ]},
    # #1 Marco 41M — RECOMP (peso= grasso%↓)
    1: {"n": 10, "start": date(2025, 5, 15), "iv": 14, "metrics": [
        (1, 82.0, 82.0), (2, 178.0, None), (3, 22.0, 18.0),
        (9, 90.0, 86.0), (10, 100.0, 98.0), (17, 72, 66),
        (11, 33.0, 33.5), (12, 32.8, 33.3), (13, 55.0, 55.0),
        (14, 54.8, 54.8), (15, 39.0, 39.0), (16, 38.8, 38.8),
        (20, 100.0, 120.0), (21, 70.0, 85.0), (22, 110.0, 135.0),
    ]},
    # #2 Sara 33F — PLATEAU (tutto stabile)
    2: {"n": 6, "start": date(2025, 7, 1), "iv": 14, "metrics": [
        (1, 62.0, 62.0), (2, 163.0, None), (3, 24.0, 24.0),
        (9, 70.0, 70.0), (10, 96.0, 96.0), (17, 70, 70),
        (11, 26.0, 26.0), (12, 25.8, 25.8), (13, 50.0, 50.0),
        (14, 49.8, 49.8), (15, 35.0, 35.0), (16, 34.8, 34.8),
    ]},
    # #3 Luca 36M — LEAN BULK (peso↑ grasso%=)
    3: {"n": 10, "start": date(2025, 5, 1), "iv": 14, "metrics": [
        (1, 78.0, 84.0), (2, 180.0, None), (3, 14.0, 14.0),
        (9, 82.0, 83.0), (10, 96.0, 98.0), (17, 62, 60),
        (11, 34.0, 35.5), (12, 33.8, 35.3), (13, 55.0, 57.0),
        (14, 54.8, 56.8), (15, 38.0, 39.0), (16, 37.8, 38.8),
        (20, 120.0, 160.0), (21, 80.0, 110.0), (22, 140.0, 185.0),
    ]},
    # #4 Elena 27F — POCHI DATI (solo 4 sessioni)
    4: {"n": 4, "start": date(2025, 12, 1), "iv": 14, "metrics": [
        (1, 65.0, 63.0), (2, 168.0, None), (3, 24.0, 22.0),
        (9, 72.0, 70.0), (10, 98.0, 96.0), (17, 72, 68),
    ]},

    # ── Lotto 2: Singola Condizione Ortopedica ──

    # #5 Francesco 38M — Ernia (cautious progressions)
    5: {"n": 8, "start": date(2025, 6, 15), "iv": 14, "metrics": [
        (1, 83.0, 82.0), (2, 175.0, None), (3, 18.0, 16.0),
        (9, 86.0, 84.0), (10, 98.0, 97.0), (17, 66, 62),
        (11, 33.0, 33.5), (12, 32.8, 33.3), (13, 54.0, 54.5),
        (14, 53.8, 54.3), (15, 38.0, 38.0), (16, 37.8, 37.8),
        (20, 70.0, 90.0), (21, 75.0, 90.0), (22, 80.0, 100.0),
    ]},
    # #6 Giulia 31F — Post-ACL (asymmetria coscia DX/SX 3→1cm)
    6: {"n": 8, "start": date(2025, 7, 1), "iv": 14, "metrics": [
        (1, 63.0, 62.0), (2, 170.0, None), (3, 20.0, 18.0),
        (9, 68.0, 66.0), (10, 96.0, 94.0), (17, 68, 64),
        (11, 27.0, 27.0), (12, 26.8, 26.8),
        (13, 50.0, 52.0), (14, 53.0, 53.0),   # DX 50→52 (recovery), SX 53 stable
        (15, 35.0, 35.5), (16, 35.5, 35.5),
    ]},
    # #7 Andrea 34M — Impingement spalla (upper body limited)
    7: {"n": 6, "start": date(2025, 8, 1), "iv": 14, "metrics": [
        (1, 80.0, 79.0), (2, 177.0, None), (3, 16.0, 15.0),
        (9, 84.0, 83.0), (10, 96.0, 95.0), (17, 64, 62),
        (11, 32.0, 32.5), (12, 31.5, 32.0),
        (21, 60.0, 70.0), (22, 100.0, 115.0),
    ]},
    # #8 Valentina 39F — Fascite plantare (no 1RM)
    8: {"n": 6, "start": date(2025, 9, 1), "iv": 14, "metrics": [
        (1, 58.0, 57.0), (2, 162.0, None), (3, 21.0, 19.0),
        (9, 68.0, 66.0), (10, 94.0, 92.0), (17, 72, 68),
    ]},
    # #9 Davide 43M — Scoliosi (progressive squat/hinge)
    9: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 85.0, 83.0), (2, 182.0, None), (3, 20.0, 17.0),
        (9, 90.0, 87.0), (10, 100.0, 98.0), (17, 70, 64),
        (20, 80.0, 110.0), (21, 65.0, 82.0), (22, 90.0, 120.0),
    ]},

    # ── Lotto 3: Cardiovascolare ──

    # #10 Stefano 44M — Ipertensione (PA↓)
    10: {"n": 10, "start": date(2025, 5, 1), "iv": 14, "metrics": [
        (1, 88.0, 84.0), (2, 176.0, None), (3, 26.0, 22.0),
        (9, 96.0, 90.0), (10, 102.0, 99.0), (17, 78, 70),
        (18, 145.0, 130.0), (19, 92.0, 82.0),
        (20, 80.0, 100.0), (21, 60.0, 75.0), (22, 90.0, 115.0),
    ]},
    # #11 Roberta 33F — Diabete T2 (peso↓ forte)
    11: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 88.0, 82.0), (2, 164.0, None), (3, 34.0, 30.0),
        (9, 92.0, 86.0), (10, 108.0, 104.0), (17, 76, 70),
    ]},
    # #12 Giovanni 49M — Insuff cardiaca (FC/PA monitorate, low intensity)
    12: {"n": 6, "start": date(2025, 8, 1), "iv": 14, "metrics": [
        (1, 78.0, 77.0), (2, 174.0, None), (3, 24.0, 23.0),
        (9, 88.0, 87.0), (10, 98.0, 97.0), (17, 72, 68),
        (18, 135.0, 130.0), (19, 82.0, 80.0),
    ]},
    # #13 Teresa 46F — Diabete T1 (stable, moderate training)
    13: {"n": 8, "start": date(2025, 6, 15), "iv": 14, "metrics": [
        (1, 66.0, 65.0), (2, 160.0, None), (3, 26.0, 24.0),
        (9, 74.0, 72.0), (10, 98.0, 96.0), (17, 70, 66),
        (20, 45.0, 60.0), (21, 25.0, 35.0), (22, 55.0, 75.0),
    ]},
    # #14 Grazia 45F — Asma+BPCO (FC riposo migliora)
    14: {"n": 6, "start": date(2025, 9, 1), "iv": 14, "metrics": [
        (1, 64.0, 63.0), (2, 158.0, None), (3, 28.0, 26.0),
        (9, 76.0, 74.0), (10, 100.0, 98.0), (17, 80, 72),
    ]},

    # ── Lotto 4: Multi-Condizione ──

    # #15 Massimo 48M — CRITICAL (peso↑ grasso%↑)
    15: {"n": 6, "start": date(2025, 10, 1), "iv": 14, "metrics": [
        (1, 105.0, 116.0), (2, 172.0, None), (3, 36.0, 39.0),
        (9, 112.0, 118.0), (10, 108.0, 112.0), (17, 82, 86),
        (18, 148.0, 155.0), (19, 94.0, 98.0),
    ]},
    # #16 Patrizia 51F — MUSCLE_LOSS (peso↓ grasso%=)
    16: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 95.0, 88.0), (2, 162.0, None), (3, 40.0, 40.0),
        (9, 102.0, 99.0), (10, 116.0, 113.0), (17, 80, 76),
    ]},
    # #17 Giuseppe 50M — PLATEAU + rischio CV alto
    17: {"n": 6, "start": date(2025, 8, 1), "iv": 14, "metrics": [
        (1, 85.0, 85.0), (2, 175.0, None), (3, 25.0, 25.0),
        (9, 94.0, 94.0), (10, 100.0, 100.0), (17, 78, 76),
        (18, 150.0, 148.0), (19, 95.0, 94.0),
    ]},
    # #18 Antonella 43F — CUTTING lento (fibromialgia)
    18: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 68.0, 64.0), (2, 166.0, None), (3, 28.0, 25.0),
        (9, 80.0, 76.0), (10, 100.0, 97.0), (17, 72, 68),
    ]},
    # #19 Vincenzo 52M — PLATEAU + rischio metabolico
    19: {"n": 6, "start": date(2025, 8, 1), "iv": 14, "metrics": [
        (1, 82.0, 82.0), (2, 170.0, None), (3, 30.0, 30.0),
        (9, 100.0, 100.0), (10, 100.0, 100.0), (17, 78, 76),
    ]},

    # ── Lotto 5: Popolazioni Speciali ──

    # #20 Francesca 33F — Post-partum (vita↓, peso↓)
    20: {"n": 6, "start": date(2025, 9, 1), "iv": 14, "metrics": [
        (1, 72.0, 68.0), (2, 167.0, None), (3, 30.0, 26.0),
        (9, 90.0, 84.0), (10, 106.0, 102.0), (17, 74, 68),
    ]},
    # #21 Nicola 46M — FAI anca (limited ROM, no deep squat)
    21: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 82.0, 80.0), (2, 178.0, None), (3, 20.0, 18.0),
        (9, 86.0, 84.0), (10, 98.0, 96.0), (17, 66, 62),
        (13, 53.0, 54.0), (14, 55.0, 55.0),   # coscia DX→SX asymmetry
    ]},
    # #22 Paola 44F — Capsulite spalla (ROM limitatissimo)
    22: {"n": 6, "start": date(2025, 9, 1), "iv": 14, "metrics": [
        (1, 62.0, 61.0), (2, 163.0, None), (3, 24.0, 23.0),
        (9, 72.0, 71.0), (10, 96.0, 95.0), (17, 70, 68),
        (11, 27.0, 28.0), (12, 29.0, 29.0),   # braccio SX (affected) → DX
    ]},
    # #23 Roberto 47M — Spondilolistesi (core focus, no heavy loads)
    23: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 80.0, 78.0), (2, 176.0, None), (3, 22.0, 20.0),
        (9, 88.0, 86.0), (10, 98.0, 96.0), (17, 68, 64),
    ]},
    # #24 Ilaria 33F — Ipotiroidismo (PLATEAU nonostante dieta)
    24: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 66.0, 66.0), (2, 164.0, None), (3, 26.0, 26.0),
        (9, 74.0, 74.0), (10, 98.0, 98.0), (17, 68, 66),
    ]},

    # ── Lotto 6: Atleti + Edge Cases ──

    # #25 Lorenzo 42M — Pre-competition (FFMI alto, forza avanzata)
    25: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 82.0, 83.0), (2, 178.0, None), (3, 12.0, 10.0),
        (9, 80.0, 79.0), (10, 94.0, 94.0), (17, 52, 48),
        (11, 36.0, 36.5), (12, 35.8, 36.3), (13, 58.0, 58.5),
        (14, 57.8, 58.3), (15, 40.0, 40.0), (16, 39.8, 39.8),
        (20, 160.0, 180.0), (21, 120.0, 135.0), (22, 190.0, 210.0),
    ]},
    # #26 Sofia 28F — OPTIMAL GROWTH (peso↑ grasso%↓)
    26: {"n": 10, "start": date(2025, 5, 1), "iv": 14, "metrics": [
        (1, 58.0, 62.0), (2, 168.0, None), (3, 20.0, 16.0),
        (9, 66.0, 67.0), (10, 94.0, 96.0), (17, 64, 58),
        (11, 26.0, 27.5), (12, 25.8, 27.3), (13, 50.0, 52.0),
        (14, 49.8, 51.8), (15, 35.0, 36.0), (16, 34.8, 35.8),
        (20, 60.0, 85.0), (21, 35.0, 50.0), (22, 70.0, 100.0),
    ]},
    # #27 Edoardo 27M — DATI INSUFFICIENTI (solo 2 sessioni!)
    27: {"n": 2, "start": date(2025, 12, 1), "iv": 28, "metrics": [
        (1, 76.0, 75.0), (2, 180.0, None), (3, 18.0, 17.0),
        (17, 64, 62),
    ]},
    # #28 Claudia 32F — BILATERAL ALERT (polpaccio DX-SX >3cm)
    28: {"n": 6, "start": date(2025, 9, 1), "iv": 14, "metrics": [
        (1, 60.0, 59.0), (2, 165.0, None), (3, 22.0, 21.0),
        (9, 68.0, 67.0), (10, 96.0, 95.0), (17, 70, 68),
        (11, 28.0, 28.0), (12, 27.0, 27.5),
        (13, 51.0, 51.0), (14, 50.0, 50.5),
        (15, 37.0, 37.5), (16, 33.0, 33.5),   # delta 4cm! alert
    ]},
    # #29 Simone 37M — BORDERLINE PA (130/85 = normale-alta)
    29: {"n": 8, "start": date(2025, 6, 1), "iv": 14, "metrics": [
        (1, 80.0, 79.0), (2, 179.0, None), (3, 18.0, 16.0),
        (9, 84.0, 82.0), (10, 96.0, 95.0), (17, 62, 58),
        (18, 129.0, 131.0), (19, 84.0, 86.0),   # crosses normale→normale-alta
        (20, 100.0, 120.0), (21, 80.0, 95.0), (22, 120.0, 145.0),
    ]},
}


# ═══════════════════════════════════════════════════════════════
# SECTION 5: Obiettivi per Cliente
# ═══════════════════════════════════════════════════════════════
# Format: list of dicts per client index
# Stato calcolato dal seed basandosi sull'ultimo valore misurato.

GOALS_DATA = {
    # ── Lotto 1 ──
    0: [
        {"id_metrica": 3, "direzione": "diminuire", "target": 16.0,
         "baseline": 22.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2025, 12, 1),
         "tipo": "corporeo", "priorita": 1},
        {"id_metrica": 20, "direzione": "aumentare", "target": 80.0,
         "baseline": 55.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2025, 12, 1),
         "tipo": "atletico", "priorita": 2},
    ],
    1: [
        {"id_metrica": 3, "direzione": "diminuire", "target": 18.0,
         "baseline": 22.0, "data_baseline": date(2025, 5, 15),
         "inizio": date(2025, 5, 15), "scadenza": date(2025, 11, 15),
         "tipo": "corporeo", "priorita": 1},
        {"id_metrica": 1, "direzione": "mantenere", "target": None,
         "baseline": 82.0, "data_baseline": date(2025, 5, 15),
         "inizio": date(2025, 5, 15), "scadenza": date(2025, 11, 15),
         "tipo": "corporeo", "priorita": 3},
    ],
    2: [
        {"id_metrica": 1, "direzione": "mantenere", "target": None,
         "baseline": 62.0, "data_baseline": date(2025, 7, 1),
         "inizio": date(2025, 7, 1), "scadenza": date(2026, 1, 1),
         "tipo": "corporeo", "priorita": 2},
    ],
    3: [
        {"id_metrica": 20, "direzione": "aumentare", "target": 160.0,
         "baseline": 120.0, "data_baseline": date(2025, 5, 1),
         "inizio": date(2025, 5, 1), "scadenza": date(2025, 11, 1),
         "tipo": "atletico", "priorita": 1},
        {"id_metrica": 21, "direzione": "aumentare", "target": 110.0,
         "baseline": 80.0, "data_baseline": date(2025, 5, 1),
         "inizio": date(2025, 5, 1), "scadenza": date(2025, 11, 1),
         "tipo": "atletico", "priorita": 1},
    ],
    4: [
        {"id_metrica": 3, "direzione": "diminuire", "target": 20.0,
         "baseline": 24.0, "data_baseline": date(2025, 12, 1),
         "inizio": date(2025, 12, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 1},
    ],

    # ── Lotto 2 ──
    5: [
        {"id_metrica": 20, "direzione": "aumentare", "target": 100.0,
         "baseline": 70.0, "data_baseline": date(2025, 6, 15),
         "inizio": date(2025, 6, 15), "scadenza": date(2025, 12, 15),
         "tipo": "atletico", "priorita": 1},
    ],
    7: [
        {"id_metrica": 22, "direzione": "aumentare", "target": 130.0,
         "baseline": 100.0, "data_baseline": date(2025, 8, 1),
         "inizio": date(2025, 8, 1), "scadenza": date(2026, 2, 1),
         "tipo": "atletico", "priorita": 1},
    ],
    8: [
        {"id_metrica": 3, "direzione": "diminuire", "target": 18.0,
         "baseline": 21.0, "data_baseline": date(2025, 9, 1),
         "inizio": date(2025, 9, 1), "scadenza": date(2026, 3, 1),
         "tipo": "corporeo", "priorita": 1},
    ],
    9: [
        {"id_metrica": 20, "direzione": "aumentare", "target": 120.0,
         "baseline": 80.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2025, 12, 1),
         "tipo": "atletico", "priorita": 1},
    ],

    # ── Lotto 3 ──
    10: [
        {"id_metrica": 18, "direzione": "diminuire", "target": 130.0,
         "baseline": 145.0, "data_baseline": date(2025, 5, 1),
         "inizio": date(2025, 5, 1), "scadenza": date(2025, 11, 1),
         "tipo": "corporeo", "priorita": 1},
        {"id_metrica": 3, "direzione": "diminuire", "target": 20.0,
         "baseline": 26.0, "data_baseline": date(2025, 5, 1),
         "inizio": date(2025, 5, 1), "scadenza": date(2026, 5, 1),
         "tipo": "corporeo", "priorita": 2},
    ],
    11: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 78.0,
         "baseline": 88.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 1},
        {"id_metrica": 3, "direzione": "diminuire", "target": 26.0,
         "baseline": 34.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 2},
    ],
    13: [
        {"id_metrica": 20, "direzione": "aumentare", "target": 70.0,
         "baseline": 45.0, "data_baseline": date(2025, 6, 15),
         "inizio": date(2025, 6, 15), "scadenza": date(2026, 6, 15),
         "tipo": "atletico", "priorita": 2},
    ],
    14: [
        {"id_metrica": 17, "direzione": "diminuire", "target": 70.0,
         "baseline": 80.0, "data_baseline": date(2025, 9, 1),
         "inizio": date(2025, 9, 1), "scadenza": date(2026, 3, 1),
         "tipo": "corporeo", "priorita": 1},
    ],

    # ── Lotto 4 ──
    15: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 95.0,
         "baseline": 105.0, "data_baseline": date(2025, 10, 1),
         "inizio": date(2025, 10, 1), "scadenza": date(2026, 4, 1),
         "tipo": "corporeo", "priorita": 1},
    ],
    16: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 85.0,
         "baseline": 95.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 1},
    ],
    18: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 62.0,
         "baseline": 68.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 2},
    ],

    # ── Lotto 5 ──
    20: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 65.0,
         "baseline": 72.0, "data_baseline": date(2025, 9, 1),
         "inizio": date(2025, 9, 1), "scadenza": date(2026, 3, 1),
         "tipo": "corporeo", "priorita": 1},
    ],
    23: [
        {"id_metrica": 3, "direzione": "diminuire", "target": 18.0,
         "baseline": 22.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 2},
    ],
    24: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 60.0,
         "baseline": 66.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 1},
    ],

    # ── Lotto 6 ──
    25: [
        {"id_metrica": 20, "direzione": "aumentare", "target": 200.0,
         "baseline": 160.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 3, 31),
         "tipo": "atletico", "priorita": 1},
        {"id_metrica": 3, "direzione": "diminuire", "target": 9.0,
         "baseline": 12.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 3, 31),
         "tipo": "corporeo", "priorita": 2},
    ],
    26: [
        {"id_metrica": 20, "direzione": "aumentare", "target": 90.0,
         "baseline": 60.0, "data_baseline": date(2025, 5, 1),
         "inizio": date(2025, 5, 1), "scadenza": date(2025, 11, 1),
         "tipo": "atletico", "priorita": 1},
        {"id_metrica": 3, "direzione": "diminuire", "target": 16.0,
         "baseline": 20.0, "data_baseline": date(2025, 5, 1),
         "inizio": date(2025, 5, 1), "scadenza": date(2025, 11, 1),
         "tipo": "corporeo", "priorita": 2},
    ],
    27: [
        {"id_metrica": 1, "direzione": "diminuire", "target": 72.0,
         "baseline": 76.0, "data_baseline": date(2025, 12, 1),
         "inizio": date(2025, 12, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 2},
    ],
    29: [
        {"id_metrica": 3, "direzione": "diminuire", "target": 14.0,
         "baseline": 18.0, "data_baseline": date(2025, 6, 1),
         "inizio": date(2025, 6, 1), "scadenza": date(2026, 6, 1),
         "tipo": "corporeo", "priorita": 1},
    ],
}


# ═══════════════════════════════════════════════════════════════
# SECTION 6: Expected Conditions (per verifica)
# ═══════════════════════════════════════════════════════════════

EXPECTED_CONDITIONS = {
    0: set(),
    1: set(),
    2: set(),
    3: set(),
    4: set(),
    5: {1, 39},
    6: {10, 11, 32},
    7: {6, 7, 33},
    8: {18, 34},
    9: {3},
    10: {20, 21},
    11: {23},
    12: {20, 21, 22},
    13: {23, 44},
    14: {28, 43},
    15: {12, 13, 20, 21, 25, 32},
    16: {23, 25, 26, 27, 35},  # 35 da "anca" in limitazioni_funzionali
    17: {1, 2, 17, 20, 21, 31, 38},
    18: {38, 40, 41},
    19: {23, 24, 45},
    20: {29, 30},
    21: {14, 15, 35},
    22: {8, 9, 33, 46},
    23: {1, 4, 5, 36},
    24: {42, 47},
    25: {16, 31, 37},  # 31 da "polso" in limitazioni_funzionali
    26: set(),
    27: set(),
    28: {19, 31, 34},
    29: set(),
}

EXPECTED_MEDICATION_FLAGS = {
    7: {"corticosteroid"},
    10: {"beta_blocker"},
    11: {"statin"},
    12: {"beta_blocker", "anticoagulant"},
    13: {"insulin"},
}


# ═══════════════════════════════════════════════════════════════
# SECTION 7: Database Setup
# ═══════════════════════════════════════════════════════════════

def _ensure_exercises(engine):
    """Verifica esercizi nel DB. Se assenti, copia da crm.db."""
    try:
        with Session(engine) as session:
            n_ex = session.exec(
                text("SELECT COUNT(*) FROM esercizi WHERE in_subset = 1")
            ).scalar_one()
    except Exception:
        n_ex = 0

    if n_ex >= 50:
        print(f"   Esercizi: {n_ex} attivi trovati")
        return

    # Copia da crm.db
    prod_path = DATA_DIR / "crm.db"
    dev_path = DATA_DIR / "crm_dev.db"

    if not prod_path.exists():
        print("   ERRORE: crm.db non trovato e crm_dev.db senza esercizi.")
        print("   Assicurati che crm.db esista con esercizi e tassonomia.")
        sys.exit(1)

    # Backup crm_dev.db se esiste
    if dev_path.exists():
        backup = DATA_DIR / f"crm_dev_pre_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(dev_path, backup)
        print(f"   Backup: {backup.name}")

    # Copia crm.db intero → crm_dev.db (include esercizi + tassonomia)
    shutil.copy2(prod_path, dev_path)
    n_ex_new = 0
    new_engine = create_engine(
        f"sqlite:///{dev_path}", echo=False,
        connect_args={"check_same_thread": False},
    )
    with Session(new_engine) as s:
        n_ex_new = s.exec(
            text("SELECT COUNT(*) FROM esercizi WHERE in_subset = 1")
        ).scalar_one()
    print(f"   crm_dev.db copiato da crm.db ({n_ex_new} esercizi attivi)")


def _selective_reset(engine):
    """Cancella solo dati clinici e finanziari, preserva esercizi e tassonomia."""
    tables_to_clear = [
        "valori_misurazione", "misurazioni_cliente", "obiettivi_cliente",
        "allenamenti_eseguiti", "esercizi_sessione", "sessioni_scheda",
        "schede_allenamento", "eventi", "movimenti_cassa", "rate",
        "contratti", "spese_ricorrenti", "clienti", "trainers",
    ]
    with Session(engine) as session:
        session.exec(text("PRAGMA foreign_keys = OFF"))
        for table in tables_to_clear:
            try:
                session.exec(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        session.exec(text("PRAGMA foreign_keys = ON"))
        session.commit()
    print("   Reset selettivo: dati clinici azzerati, esercizi preservati")


def _ensure_metriche(engine):
    """Seed catalogo metriche se assente."""
    with Session(engine) as session:
        n = session.exec(text("SELECT COUNT(*) FROM metriche")).scalar_one()
        if n >= 22:
            return
        # Seed 22 metriche
        for nome, nome_en, unita, cat, ordine in METRICS_SEED:
            m = Metric(
                nome=nome, nome_en=nome_en,
                unita_misura=unita, categoria=cat, ordinamento=ordine,
            )
            session.add(m)
        session.commit()
        print("   Metriche catalogo: 22 metriche inserite")


def setup_qa_database():
    """Setup crm_dev.db per QA: esercizi + reset selettivo + metriche."""
    dev_path = DATA_DIR / "crm_dev.db"
    db_url = f"sqlite:///{dev_path}"
    engine = create_engine(
        db_url, echo=False, connect_args={"check_same_thread": False},
    )

    _ensure_exercises(engine)

    # Re-create engine dopo eventuale copia
    engine = create_engine(
        db_url, echo=False, connect_args={"check_same_thread": False},
    )

    _selective_reset(engine)
    _ensure_metriche(engine)

    return engine


# ═══════════════════════════════════════════════════════════════
# SECTION 8: Main Seed Function
# ═══════════════════════════════════════════════════════════════

def seed_qa_clinical(engine):
    """Popola crm_dev.db con 30 clienti QA clinici."""

    with Session(engine) as session:

        # ── Step A: Trainer ──
        trainer = Trainer(
            email="chiarabassani96@gmail.com",
            nome="Chiara",
            cognome="Bassani",
            hashed_password=hash_password("Fitness2026!"),
            is_active=True,
        )
        session.add(trainer)
        session.flush()
        tid = trainer.id
        print(f"   Trainer: {trainer.nome} {trainer.cognome} (id={tid})")

        # ── Step B: 30 Clienti con Anamnesi ──
        clients: list[Client] = []
        for i, cd in enumerate(CLIENTS_DATA):
            anamnesi_data = ANAMNESI.get(i)
            anamnesi_json = (
                json.dumps(anamnesi_data, ensure_ascii=False)
                if anamnesi_data else None
            )
            c = Client(
                trainer_id=tid,
                nome=cd["nome"],
                cognome=cd["cognome"],
                telefono=cd.get("tel"),
                email=cd.get("email"),
                data_nascita=cd.get("nascita"),
                sesso=cd.get("sesso"),
                stato=cd.get("stato", "Attivo"),
                anamnesi_json=anamnesi_json,
            )
            session.add(c)
            clients.append(c)
        session.flush()

        n_with_anamnesi = sum(1 for i in range(30) if ANAMNESI.get(i) is not None)
        print(f"   Clienti: {len(clients)} creati ({n_with_anamnesi} con anamnesi)")

        # ── Step J: Misurazioni Cliniche ──
        # Pre-genera TUTTE le misurazioni (determinismo: random state unico)
        generated_data: dict[int, list[tuple[date, dict[int, float]]]] = {}
        for client_idx, profile in MEASUREMENT_PROFILES.items():
            generated_data[client_idx] = _gen_measurements(profile)

        n_sessions_total = 0
        n_values_total = 0

        for client_idx, measurement_sessions in generated_data.items():
            client = clients[client_idx]

            for meas_date, values in measurement_sessions:
                measurement = ClientMeasurement(
                    id_cliente=client.id,
                    trainer_id=tid,
                    data_misurazione=meas_date,
                )
                session.add(measurement)
                session.flush()

                for metric_id, value in values.items():
                    mv = MeasurementValue(
                        id_misurazione=measurement.id,
                        id_metrica=metric_id,
                        valore=value,
                    )
                    session.add(mv)
                    n_values_total += 1

                n_sessions_total += 1

        session.flush()
        print(f"   Misurazioni: {n_sessions_total} sessioni, {n_values_total} valori")

        # ── Step K: Obiettivi Cliente ──
        n_goals = 0
        n_raggiunto = 0

        for client_idx, goals_list in GOALS_DATA.items():
            client = clients[client_idx]
            client_sessions = generated_data.get(client_idx, [])

            for g in goals_list:
                # Determina stato basandosi sull'ultimo valore REALMENTE inserito
                stato = "attivo"
                completed_at_val = None

                if client_sessions and g.get("target") is not None:
                    last_value = None
                    last_date = None
                    for meas_date, values in client_sessions:
                        if g["id_metrica"] in values:
                            last_value = values[g["id_metrica"]]
                            last_date = meas_date

                    if last_value is not None:
                        reached = False
                        if g["direzione"] == "diminuire" and last_value <= g["target"]:
                            reached = True
                        elif g["direzione"] == "aumentare" and last_value >= g["target"]:
                            reached = True

                        if reached:
                            stato = "raggiunto"
                            n_raggiunto += 1
                            completed_at_val = datetime(
                                last_date.year, last_date.month, last_date.day,
                                tzinfo=timezone.utc,
                            )

                goal = ClientGoal(
                    id_cliente=client.id,
                    trainer_id=tid,
                    id_metrica=g["id_metrica"],
                    direzione=g["direzione"],
                    valore_target=g.get("target"),
                    valore_baseline=g.get("baseline"),
                    data_baseline=g.get("data_baseline"),
                    data_inizio=g["inizio"],
                    data_scadenza=g.get("scadenza"),
                    tipo_obiettivo=g.get("tipo", "corporeo"),
                    priorita=g.get("priorita", 2),
                    stato=stato,
                    completed_at=completed_at_val,
                    completato_automaticamente=stato == "raggiunto",
                )
                session.add(goal)
                n_goals += 1

        session.flush()
        print(f"   Obiettivi: {n_goals} creati ({n_raggiunto} raggiunto, "
              f"{n_goals - n_raggiunto} attivo)")

        # ── Commit atomico ──
        session.commit()

    # ── Summary per lotto ──
    lotto_names = [
        "Baseline Sano", "Singola Ortopedica", "Cardiovascolare + Farmaci",
        "Multi-Condizione + Critico", "Popolazioni Speciali", "Atleti + Edge Cases",
    ]
    print("\n   Riepilogo per lotto:")
    for lotto_idx, name in enumerate(lotto_names):
        start = lotto_idx * 5
        end = start + 5
        n_cond = sum(len(EXPECTED_CONDITIONS.get(i, set())) for i in range(start, end))
        n_meas = sum(MEASUREMENT_PROFILES[i]["n"] for i in range(start, end)
                     if i in MEASUREMENT_PROFILES)
        n_goal = sum(len(GOALS_DATA.get(i, [])) for i in range(start, end))
        print(f"     Lotto {lotto_idx + 1}: {name}")
        print(f"       Condizioni: {n_cond}, Sessioni: {n_meas}, Obiettivi: {n_goal}")

    # Copertura condizioni
    all_conds = set()
    for s in EXPECTED_CONDITIONS.values():
        all_conds |= s
    print(f"\n   Copertura: {len(all_conds)}/47 condizioni, "
          f"{len(EXPECTED_MEDICATION_FLAGS)}/5 profili con medication flags")



# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("FitManager -- Seed QA Clinical (30 Clienti x 6 Lotti)")
    print("=" * 60)
    print()

    print("[1/2] Setup database QA...")
    engine = setup_qa_database()
    print()

    print("[2/2] Seed profili clinici...")
    seed_qa_clinical(engine)
    print()

    print("=" * 60)
    print("QA DATABASE PRONTO!")
    print("=" * 60)
    print()
    print("Prossimi step:")
    print("  1. python -m tools.admin_scripts.verify_qa_clinical --lotto all")
    print("  2. bash tools/scripts/restart-backend.sh dev")
    print("  3. cd frontend && npm run dev")
    print("  4. Verificare nell'app: profilo cliente -> Anamnesi / Progressi")
