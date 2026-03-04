#!/usr/bin/env python3
"""
Seed Dev Complete — Database realistico per sviluppo con 30 clienti e 4 mesi di attivita'.

Simula l'attivita' di Chiara Bassani (personal trainer P.IVA) da dicembre 2025 a marzo 2026.
Ogni cliente ha profilo completo: contratti, pagamenti, anamnesi, misurazioni, obiettivi,
schede allenamento, sessioni in agenda, log di allenamento.

COSA CREA:
- 1 Trainer (Chiara Bassani)
- 30 Clienti con anamnesi diversificate (sano, ortopedico, metabolico, cardiovascolare)
- ~35 Contratti PT/Sala con rate e pagamenti
- ~12 Spese ricorrenti (business + personali P.IVA)
- ~300 CashMovement (entrate rate + uscite fisse + variabili + personali)
- ~200 Eventi agenda (PT + Corso + Colloqui) con SlotGrid anti-overlap
- Anamnesi JSON completa per ogni cliente
- 4-6 Misurazioni progressi per cliente (mensili, metric IDs corretti da catalog.db)
- 1-2 Obiettivi fitness per cliente con baseline e target
- 1-2 Schede allenamento per cliente (con sessioni, esercizi reali, carico_kg)
- ~80 WorkoutLog (esecuzioni sessioni registrate)

PERIODO: 1 dicembre 2025 -> 4 marzo 2026 (4 mesi)
TODAY: 4 marzo 2026

INVARIANTI GARANTITI:
- Nomi campi ESATTI (tipo_pacchetto, data_vendita, metodo, anamnesi_json, tempo_riposo_sec)
- Metric IDs da catalog.db (Peso=1, Grasso%=3, Vita=9, Fianchi=10, etc.)
- contract.totale_versato = acconto + sum(rate.importo_saldato)
- stato_pagamento coerente (PENDENTE/PARZIALE/SALDATO)
- Rate pagate hanno stato="SALDATA"
- Zero eventi sovrapposti (SlotGrid engine)
- mese_anno UNIQUE per spese ricorrenti confermate
- Client.stato sincronizzato con stato reale contratti
- Exercise IDs validi (query da DB, in_subset=1)

Uso: python -m tools.admin_scripts.seed_dev
"""

import json
import os
import random
import calendar
import sys
from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

# ── Forza DATABASE_URL su crm_dev.db PRIMA di import ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
os.environ["DATABASE_URL"] = f"sqlite:///{DATA_DIR / 'crm_dev.db'}"

sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import SQLModel, Session, create_engine, select, text, func  # noqa: E402
from api.auth.service import hash_password  # noqa: E402
from api.models.trainer import Trainer  # noqa: E402
from api.models.client import Client  # noqa: E402
from api.models.contract import Contract  # noqa: E402
from api.models.rate import Rate  # noqa: E402
from api.models.event import Event  # noqa: E402
from api.models.movement import CashMovement  # noqa: E402
from api.models.recurring_expense import RecurringExpense  # noqa: E402
from api.models.measurement import ClientMeasurement, MeasurementValue  # noqa: E402
from api.models.goal import ClientGoal  # noqa: E402
from api.models.workout import WorkoutPlan, WorkoutSession, WorkoutExercise  # noqa: E402
from api.models.workout_log import WorkoutLog  # noqa: E402
from api.models.exercise import Exercise  # noqa: E402
from api.seed_exercises import seed_builtin_exercises  # noqa: E402

# Determinismo
random.seed(42)


# ═══════════════════════════════════════════════════════════════
# CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════

PERIOD_START = date(2025, 12, 1)
TODAY = date(2026, 3, 4)

# Metric IDs da catalog.db (FISSI, corrispondono a seed_metrics)
MET_PESO = 1           # Peso Corporeo (kg)
MET_ALTEZZA = 2        # Altezza (cm)
MET_GRASSO = 3         # Massa Grassa (%)
MET_MASSA_MAGRA = 4    # Massa Magra (kg)
MET_BMI = 5            # BMI (kg/m²)
MET_ACQUA = 6          # Acqua Corporea (%)
MET_COLLO = 7          # Collo (cm)
MET_PETTO = 8          # Petto (cm)
MET_VITA = 9           # Vita (cm)
MET_FIANCHI = 10       # Fianchi (cm)
MET_BRACCIO_DX = 11    # Braccio Destro (cm)
MET_BRACCIO_SX = 12    # Braccio Sinistro (cm)
MET_COSCIA_DX = 13     # Coscia Destra (cm)
MET_COSCIA_SX = 14     # Coscia Sinistra (cm)
MET_POLPACCIO_DX = 15  # Polpaccio Destro (cm)
MET_POLPACCIO_SX = 16  # Polpaccio Sinistro (cm)
MET_FC_RIPOSO = 17     # FC Riposo (bpm)
MET_PA_SIS = 18        # PA Sistolica (mmHg)
MET_PA_DIA = 19        # PA Diastolica (mmHg)
MET_SQUAT_1RM = 20     # Squat 1RM (kg)
MET_PANCA_1RM = 21     # Panca Piana 1RM (kg)
MET_STACCO_1RM = 22    # Stacco da Terra 1RM (kg)

# Metriche standard per seed nel business DB (per FK integrity)
METRICS_SEED = [
    ("Peso Corporeo", "Body Weight", "kg", "antropometrica", 1),
    ("Altezza", "Height", "cm", "antropometrica", 2),
    ("Massa Grassa", "Body Fat", "%", "composizione", 1),
    ("Massa Magra", "Lean Mass", "kg", "composizione", 2),
    ("BMI", "BMI", "kg/m²", "composizione", 3),
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

# Chiusure studio
CLOSED = [
    (date(2025, 12, 24), date(2025, 12, 26)),  # Natale
    (date(2025, 12, 31), date(2026, 1, 1)),     # Capodanno
]

# Slot orari
MORNING = [7, 8, 9, 10, 11]
AFTERNOON = [15, 16, 17, 18, 19, 20]
SATURDAY = [8, 9, 10, 11, 12]

# Pacchetti PT (pricing italiano reale)
PACKAGES = [
    {"nome": "PT 10 Sedute",     "crediti": 10, "p_min": 350,  "p_max": 450,  "mesi": 3},
    {"nome": "PT 20 Sedute",     "crediti": 20, "p_min": 600,  "p_max": 800,  "mesi": 5},
    {"nome": "PT 30 Sedute",     "crediti": 30, "p_min": 850,  "p_max": 1100, "mesi": 8},
    {"nome": "Sala Mensile",     "crediti": 0,  "p_min": 40,   "p_max": 70,   "mesi": 1},
    {"nome": "Sala Trimestrale", "crediti": 0,  "p_min": 100,  "p_max": 180,  "mesi": 3},
]
PKG_WEIGHTS = [35, 30, 15, 10, 10]

PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"]
PM_WEIGHTS = [30, 40, 30]
OBIETTIVI_FITNESS = ["dimagrimento", "ipertrofia", "forza", "resistenza", "generale"]
LIVELLI_FITNESS = ["beginner", "intermedio", "avanzato"]

CORSO_TITLES = [
    "Pilates Gruppo", "Functional Training", "Stretching Posturale",
    "Circuit Training", "Ginnastica Dolce", "Core Stability",
]


# ═══════════════════════════════════════════════════════════════
# DATI CLIENTI (30) — 24 attivi, 3 prospect, 3 inattivi
# ═══════════════════════════════════════════════════════════════

CLIENTS_DATA = [
    # ── 24 Attivi (con contratto) ──
    {"nome": "Alessia",    "cognome": "Marchetti",  "tel": "333-1001001", "email": "alessia.marchetti@gmail.com",   "nascita": date(1991, 4, 12),  "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Francesco",  "cognome": "Russo",      "tel": "339-2002002", "email": "f.russo@hotmail.it",           "nascita": date(1988, 9, 5),   "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Giulia",     "cognome": "Ferrari",    "tel": "347-3003003", "email": "giulia.ferrari@gmail.com",     "nascita": date(1995, 1, 22),  "sesso": "Donna",  "profilo": "ortopedico_spalla"},
    {"nome": "Marco",      "cognome": "Bianchi",    "tel": "320-4004004", "email": "marco.bianchi@libero.it",      "nascita": date(1985, 7, 18),  "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Sara",       "cognome": "Romano",     "tel": "338-5005005", "email": "sara.romano@gmail.com",        "nascita": date(1993, 3, 9),   "sesso": "Donna",  "profilo": "metabolico"},
    {"nome": "Luca",       "cognome": "Colombo",    "tel": "340-6006006", "email": "luca.colombo@outlook.it",      "nascita": date(1990, 11, 30), "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Valentina",  "cognome": "Ricci",      "tel": "349-7007007", "email": "vale.ricci@gmail.com",         "nascita": date(1987, 6, 14),  "sesso": "Donna",  "profilo": "ortopedico_schiena"},
    {"nome": "Andrea",     "cognome": "Moretti",    "tel": "328-8008008", "email": "andrea.moretti@gmail.com",     "nascita": date(1992, 2, 28),  "sesso": "Uomo",   "profilo": "cardiovascolare"},
    {"nome": "Chiara",     "cognome": "Conti",      "tel": "335-9009009", "email": "chiara.conti@yahoo.it",        "nascita": date(1996, 8, 3),   "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Davide",     "cognome": "Gallo",      "tel": "331-1010010", "email": "davide.gallo@gmail.com",       "nascita": date(1983, 12, 25), "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Federica",   "cognome": "Costa",      "tel": "342-1110011", "email": "fede.costa@hotmail.it",        "nascita": date(1994, 5, 7),   "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Simone",     "cognome": "Giordano",   "tel": "345-1210012", "email": "simone.giordano@gmail.com",    "nascita": date(1989, 10, 19), "sesso": "Uomo",   "profilo": "ortopedico_ginocchio"},
    {"nome": "Elisa",      "cognome": "Mancini",    "tel": "327-1310013", "email": "elisa.mancini@gmail.com",      "nascita": date(1997, 4, 1),   "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Matteo",     "cognome": "Barbieri",   "tel": "334-1410014", "email": "matteo.barbieri@libero.it",    "nascita": date(1986, 8, 29),  "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Martina",    "cognome": "Fontana",    "tel": "348-1510015", "email": "martina.fontana@gmail.com",    "nascita": date(1991, 12, 10), "sesso": "Donna",  "profilo": "metabolico"},
    {"nome": "Lorenzo",    "cognome": "Santoro",    "tel": "329-1610016", "email": "lorenzo.santoro@outlook.it",   "nascita": date(1984, 3, 17),  "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Anna",       "cognome": "Marini",     "tel": "336-1710017", "email": "anna.marini@gmail.com",        "nascita": date(1998, 7, 23),  "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Stefano",    "cognome": "Leone",      "tel": "341-1810018", "email": "stefano.leone@gmail.com",      "nascita": date(1982, 1, 6),   "sesso": "Uomo",   "profilo": "cardiovascolare"},
    {"nome": "Roberta",    "cognome": "Longo",      "tel": "330-1910019", "email": "roberta.longo@yahoo.it",       "nascita": date(1993, 9, 14),  "sesso": "Donna",  "profilo": "ortopedico_caviglia"},
    {"nome": "Paolo",      "cognome": "Martini",    "tel": "337-2010020", "email": "paolo.martini@gmail.com",      "nascita": date(1987, 5, 8),   "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Silvia",     "cognome": "Greco",      "tel": "343-2110021", "email": "silvia.greco@hotmail.it",      "nascita": date(1995, 11, 3),  "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Alberto",    "cognome": "Vitale",     "tel": "326-2210022", "email": "alberto.vitale@gmail.com",     "nascita": date(1981, 2, 19),  "sesso": "Uomo",   "profilo": "metabolico"},
    {"nome": "Francesca",  "cognome": "Serra",      "tel": "332-2310023", "email": "francesca.serra@yahoo.it",     "nascita": date(1994, 8, 12),  "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Riccardo",   "cognome": "De Luca",    "tel": "346-2410024", "email": "riccardo.deluca@gmail.com",    "nascita": date(1990, 4, 28),  "sesso": "Uomo",   "profilo": "sano"},
    # ── 3 Inattivi (contratto scaduto, non rinnovano) ──
    {"nome": "Giovanni",   "cognome": "Messina",    "tel": "333-2610026", "email": "giovanni.messina@gmail.com",   "nascita": date(1985, 6, 7),   "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Elena",      "cognome": "Rizzo",      "tel": "344-2710027", "email": "elena.rizzo@outlook.it",       "nascita": date(1996, 12, 21), "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Nicola",     "cognome": "Gatti",      "tel": "324-2810028", "email": "nicola.gatti@gmail.com",       "nascita": date(1988, 3, 4),   "sesso": "Uomo",   "profilo": "sano"},
    # ── 3 Prospect (registrati, nessun contratto) ──
    {"nome": "Cristina",   "cognome": "Pellegrini", "tel": "339-2910029", "email": "cristina.pellegrini@yahoo.it", "nascita": date(1993, 7, 18),  "sesso": "Donna",  "profilo": "sano"},
    {"nome": "Michele",    "cognome": "Neri",       "tel": "347-3010030", "email": "michele.neri@gmail.com",       "nascita": date(1989, 1, 9),   "sesso": "Uomo",   "profilo": "sano"},
    {"nome": "Laura",      "cognome": "Bruno",      "tel": "325-2510025", "email": "laura.bruno@libero.it",       "nascita": date(1992, 10, 15), "sesso": "Donna",  "profilo": "sano"},
]


# ═══════════════════════════════════════════════════════════════
# SPESE RICORRENTI P.IVA
# ═══════════════════════════════════════════════════════════════

RECURRING_EXPENSES_DATA = [
    # Business
    {"nome": "Affitto sala",             "importo": 800.0,  "freq": "MENSILE",     "giorno": 5,  "cat": "Affitto",       "inizio": date(2025, 1, 1)},
    {"nome": "Utenze (luce+gas)",        "importo": 180.0,  "freq": "MENSILE",     "giorno": 10, "cat": "Utenze",        "inizio": date(2025, 1, 1)},
    {"nome": "Internet fibra",           "importo": 34.90,  "freq": "MENSILE",     "giorno": 20, "cat": "Utenze",        "inizio": date(2025, 1, 1)},
    {"nome": "Software gestionale",      "importo": 29.0,   "freq": "MENSILE",     "giorno": 1,  "cat": "Software",      "inizio": date(2025, 1, 1)},
    {"nome": "Pulizia studio",           "importo": 120.0,  "freq": "MENSILE",     "giorno": 28, "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "POS commissioni bancarie", "importo": 25.0,   "freq": "MENSILE",     "giorno": 5,  "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Telefono cellulare",       "importo": 14.99,  "freq": "MENSILE",     "giorno": 12, "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Manutenzione attrezzi",    "importo": 150.0,  "freq": "TRIMESTRALE", "giorno": 10, "cat": "Attrezzatura",  "inizio": date(2025, 1, 1)},
    {"nome": "Contributi INPS",          "importo": 950.0,  "freq": "TRIMESTRALE", "giorno": 16, "cat": "Altro",         "inizio": date(2025, 2, 1)},
    {"nome": "Commercialista",           "importo": 1200.0, "freq": "ANNUALE",     "giorno": 15, "cat": "Commercialista", "inizio": date(2025, 4, 1)},
    {"nome": "Assicurazione RC",         "importo": 600.0,  "freq": "ANNUALE",     "giorno": 15, "cat": "Assicurazione", "inizio": date(2025, 1, 1)},
]

VARIABLE_BUSINESS = [
    ("Elastici fitness",            "Attrezzatura",  30,   80),
    ("Tappetini nuovi",            "Attrezzatura",  40,  120),
    ("Facebook/Instagram Ads",     "Marketing",     30,  100),
    ("Disinfettante/igienizzante", "Altro",         15,   40),
    ("Acqua distributore",         "Altro",         20,   50),
]

PERSONAL_EXPENSES = [
    # (nome, categoria, min_eur, max_eur, freq_min/mese, freq_max/mese)
    ("Spesa alimentare",  "Personale",  25,  65,  8, 12),
    ("Benzina",           "Trasporto",  40,  60,  2,  3),
    ("Pranzo fuori",      "Personale",  12,  25,  3,  5),
    ("Cena fuori",        "Personale",  25,  45,  1,  3),
    ("Aperitivo",         "Personale",   8,  18,  2,  4),
    ("Farmacia",          "Personale",   8,  35,  0,  2),
    ("Amazon/acquisti",   "Personale",  15,  80,  1,  3),
]

# Sessioni workout tipiche per obiettivo
SESSION_TEMPLATES = {
    "ipertrofia": [
        {"nome": "Push Day",  "focus": "Petto, Spalle, Tricipiti", "patterns": ["push_h", "push_v"],    "durata": 70},
        {"nome": "Pull Day",  "focus": "Dorso, Bicipiti",          "patterns": ["pull_h", "pull_v"],    "durata": 70},
        {"nome": "Leg Day",   "focus": "Gambe, Glutei",            "patterns": ["squat", "hinge"],      "durata": 75},
    ],
    "forza": [
        {"nome": "Upper Body",  "focus": "Forza parte superiore", "patterns": ["push_h", "pull_h"],     "durata": 60},
        {"nome": "Lower Body",  "focus": "Forza parte inferiore", "patterns": ["squat", "hinge"],       "durata": 60},
        {"nome": "Full Body",   "focus": "Forza totale",          "patterns": ["push_h", "squat", "hinge"], "durata": 75},
    ],
    "dimagrimento": [
        {"nome": "Circuit A",   "focus": "Full body metabolico",  "patterns": ["squat", "push_h"],      "durata": 50},
        {"nome": "Circuit B",   "focus": "Full body metabolico",  "patterns": ["hinge", "pull_h"],      "durata": 50},
        {"nome": "Cardio Mix",  "focus": "Resistenza + core",     "patterns": ["core", "squat"],        "durata": 45},
    ],
    "resistenza": [
        {"nome": "Endurance A",  "focus": "Resistenza muscolare",  "patterns": ["push_h", "squat"],     "durata": 55},
        {"nome": "Endurance B",  "focus": "Resistenza muscolare",  "patterns": ["pull_h", "hinge"],     "durata": 55},
        {"nome": "Core & Cardio", "focus": "Core e condizionamento", "patterns": ["core", "rotation"],  "durata": 45},
    ],
    "generale": [
        {"nome": "Giorno A",  "focus": "Upper body",          "patterns": ["push_h", "pull_h"],          "durata": 60},
        {"nome": "Giorno B",  "focus": "Lower body",          "patterns": ["squat", "hinge"],            "durata": 60},
        {"nome": "Giorno C",  "focus": "Full body + core",    "patterns": ["push_v", "pull_v", "core"],  "durata": 65},
    ],
}


# ═══════════════════════════════════════════════════════════════
# ANAMNESI GENERATOR
# ═══════════════════════════════════════════════════════════════

def _build_anamnesi(profilo: str, data_compilazione: date) -> str:
    """Genera JSON anamnesi realistico basato sul profilo clinico."""
    base = {
        "data_compilazione": data_compilazione.isoformat(),
        "data_ultimo_aggiornamento": data_compilazione.isoformat(),
        "infortuni_attuali": {"presente": False, "dettaglio": ""},
        "infortuni_pregressi": {"presente": False, "dettaglio": ""},
        "interventi_chirurgici": {"presente": False, "dettaglio": ""},
        "dolori_cronici": {"presente": False, "dettaglio": ""},
        "patologie": {"presente": False, "dettaglio": ""},
        "farmaci": {"presente": False, "dettaglio": ""},
        "problemi_cardiovascolari": {"presente": False, "dettaglio": ""},
        "problemi_respiratori": {"presente": False, "dettaglio": ""},
        "dieta_particolare": {"presente": False, "dettaglio": ""},
        "limitazioni_funzionali": "",
        "note": "",
        "obiettivi_specifici": "",
    }

    if profilo == "sano":
        base["obiettivi_specifici"] = random.choice([
            "Migliorare forma fisica generale",
            "Tonificazione e perdita peso",
            "Aumentare massa muscolare",
            "Preparazione per gara amatoriale",
            "Migliorare postura e mobilita'",
            "Aumentare forza e resistenza",
        ])

    elif profilo == "ortopedico_spalla":
        base["infortuni_pregressi"]["presente"] = True
        base["infortuni_pregressi"]["dettaglio"] = "Tendinite spalla destra da sovraccarico (2024)"
        base["dolori_cronici"]["presente"] = True
        base["dolori_cronici"]["dettaglio"] = "Dolore spalla destra su abduzione oltre 90 gradi"
        base["limitazioni_funzionali"] = "Evitare overhead press pesante e dip profondi"
        base["obiettivi_specifici"] = "Rinforzare cuffia rotatori, riprendere allenamento completo"

    elif profilo == "ortopedico_schiena":
        base["infortuni_pregressi"]["presente"] = True
        base["infortuni_pregressi"]["dettaglio"] = "Protrusione discale L4-L5 diagnosticata 2023"
        base["dolori_cronici"]["presente"] = True
        base["dolori_cronici"]["dettaglio"] = "Lombalgia cronica, peggiorata da sedentarieta'"
        base["limitazioni_funzionali"] = "Evitare flessione lombare sotto carico, squat ATG con bilanciere"
        base["obiettivi_specifici"] = "Rinforzare core, ridurre dolore lombare"

    elif profilo == "ortopedico_ginocchio":
        base["interventi_chirurgici"]["presente"] = True
        base["interventi_chirurgici"]["dettaglio"] = "Ricostruzione LCA ginocchio sinistro (2023)"
        base["limitazioni_funzionali"] = "Evitare pivot improvvisi, deep squat monopodalico"
        base["obiettivi_specifici"] = "Recupero funzionale completo, simmetria bilaterale"

    elif profilo == "ortopedico_caviglia":
        base["infortuni_pregressi"]["presente"] = True
        base["infortuni_pregressi"]["dettaglio"] = "Distorsione caviglia sinistra grado 2 (2024)"
        base["limitazioni_funzionali"] = "Instabilita' residua caviglia sx su terreno irregolare"
        base["obiettivi_specifici"] = "Propriocezione caviglia, rinforzo peronei"

    elif profilo == "metabolico":
        patologia = random.choice([
            ("Ipotiroidismo in trattamento farmacologico", "Eutirox 75mcg/die"),
            ("Prediabete, glicemia a digiuno 108 mg/dL", "Metformina 500mg"),
            ("Dislipidemia, colesterolo totale 235 mg/dL", "Statina 20mg"),
        ])
        base["patologie"]["presente"] = True
        base["patologie"]["dettaglio"] = patologia[0]
        base["farmaci"]["presente"] = True
        base["farmaci"]["dettaglio"] = patologia[1]
        base["dieta_particolare"]["presente"] = True
        base["dieta_particolare"]["dettaglio"] = "Dieta mediterranea ipocalorica, seguita da nutrizionista"
        base["obiettivi_specifici"] = "Perdita di peso, miglioramento parametri metabolici"

    elif profilo == "cardiovascolare":
        cv = random.choice([
            ("Ipertensione stadio 1, PA abituale 145/92", "Ramipril 5mg/die"),
            ("Extrasistoli ventricolari benigne, ECG nella norma", "Magnesio pidolato"),
        ])
        base["problemi_cardiovascolari"]["presente"] = True
        base["problemi_cardiovascolari"]["dettaglio"] = cv[0]
        base["farmaci"]["presente"] = True
        base["farmaci"]["dettaglio"] = cv[1]
        base["limitazioni_funzionali"] = "Evitare Valsalva, monitorare FC durante sforzo intenso"
        base["obiettivi_specifici"] = "Migliorare capacita' aerobica, controllare pressione arteriosa"

    return json.dumps(base, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _is_open(d: date) -> bool:
    if d.weekday() == 6:  # domenica
        return False
    for start, end in CLOSED:
        if start <= d <= end:
            return False
    return True


def _slots_for(d: date) -> list[int]:
    if not _is_open(d):
        return []
    if d.weekday() == 5:  # sabato
        return SATURDAY[:]
    return MORNING + AFTERNOON


class SlotGrid:
    """Griglia slot orari anti-overlap."""
    def __init__(self):
        self.booked: dict[date, set[int]] = defaultdict(set)

    def is_free(self, d: date, hour: int) -> bool:
        return hour not in self.booked[d]

    def book(self, d: date, hour: int) -> bool:
        if not self.is_free(d, hour):
            return False
        self.booked[d].add(hour)
        return True

    def find_free(self, d: date, preferred: list[int]) -> int | None:
        for h in preferred:
            if self.is_free(d, h):
                return h
        return None


def _rand_method() -> str:
    return random.choices(PAYMENT_METHODS, PM_WEIGHTS)[0]


def _rand_price(pkg: dict) -> float:
    raw = random.uniform(pkg["p_min"], pkg["p_max"])
    return round(raw / 10) * 10


def _rand_date_in_month(y: int, m: int) -> date:
    last = calendar.monthrange(y, m)[1]
    return date(y, m, random.randint(1, last))


def _safe_date(y: int, m: int, d: int) -> date:
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d, last))


def _make_dt(d: date, hour: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, 0, tzinfo=timezone.utc)


def _make_movement(
    tid: int, tipo: str, importo: float, categoria: str, data_eff: date,
    id_cliente: int | None = None, id_contratto: int | None = None,
    id_rata: int | None = None, id_spesa: int | None = None,
    mese_anno: str | None = None, note: str | None = None,
    metodo: str | None = None, operatore: str = "API",
) -> CashMovement:
    return CashMovement(
        trainer_id=tid,
        tipo=tipo,
        importo=importo,
        categoria=categoria,
        data_effettiva=data_eff,
        data_movimento=_make_dt(data_eff),
        id_cliente=id_cliente,
        id_contratto=id_contratto,
        id_rata=id_rata,
        id_spesa_ricorrente=id_spesa,
        mese_anno=mese_anno,
        metodo=metodo or _rand_method(),
        note=note,
        operatore=operatore,
    )


def _months_range(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def _get_occurrences(freq: str, giorno: int, data_inizio: date, anno: int, mese: int):
    """Replica la logica API per occorrenze spese ricorrenti."""
    days_in = calendar.monthrange(anno, mese)[1]
    last_day = date(anno, mese, days_in)
    if data_inizio > last_day:
        return []

    if freq == "MENSILE":
        g = min(giorno, days_in)
        return [(_safe_date(anno, mese, g), f"{anno:04d}-{mese:02d}")]

    abs_target = anno * 12 + mese
    abs_start = data_inizio.year * 12 + data_inizio.month

    if freq == "TRIMESTRALE":
        if (abs_target - abs_start) % 3 != 0:
            return []
        g = min(giorno, days_in)
        return [(_safe_date(anno, mese, g), f"{anno:04d}-{mese:02d}")]

    if freq == "SEMESTRALE":
        if (abs_target - abs_start) % 6 != 0:
            return []
        g = min(giorno, days_in)
        return [(_safe_date(anno, mese, g), f"{anno:04d}-{mese:02d}")]

    if freq == "ANNUALE":
        if mese != data_inizio.month:
            return []
        g = min(giorno, days_in)
        return [(_safe_date(anno, mese, g), f"{anno:04d}")]

    return []


def _is_donna(sesso: str) -> bool:
    """True se sesso e' 'Donna' o 'F'."""
    return sesso in ("Donna", "F")


# ═══════════════════════════════════════════════════════════════
# DATABASE RESET
# ═══════════════════════════════════════════════════════════════

def reset_database():
    """Drop e ricrea tutte le tabelle nel business DB."""
    from api.config import DATABASE_URL

    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    print("   Dropping all tables...")
    SQLModel.metadata.drop_all(engine)

    print("   Creating all tables...")
    SQLModel.metadata.create_all(engine)
    print(f"   Schema: {len(SQLModel.metadata.tables)} tabelle create")

    # Alembic version stamp
    LATEST_ALEMBIC_VERSION = "a1b2c3d4e5f6"
    with Session(engine) as session:
        session.exec(text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
        session.exec(text("DELETE FROM alembic_version"))
        session.exec(text(
            f"INSERT INTO alembic_version (version_num) "
            f"VALUES ('{LATEST_ALEMBIC_VERSION}')"
        ))
        session.commit()

    # UNIQUE index per spese ricorrenti
    with Session(engine) as session:
        session.exec(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_recurring_per_month
            ON movimenti_cassa (trainer_id, id_spesa_ricorrente, mese_anno)
            WHERE id_spesa_ricorrente IS NOT NULL AND deleted_at IS NULL
        """))
        session.commit()

    print(f"   Alembic: {LATEST_ALEMBIC_VERSION}")
    return engine


# ═══════════════════════════════════════════════════════════════
# MAIN SEED
# ═══════════════════════════════════════════════════════════════

def _copy_exercises_from_prod():
    """Copia esercizi da crm.db a crm_dev.db PRIMA di aprire la session SQLAlchemy.

    Usa sqlite3 raw per evitare lock conflicts con SQLAlchemy.
    """
    import sqlite3

    source_db = DATA_DIR / "crm.db"
    dev_db = DATA_DIR / "crm_dev.db"
    if not source_db.exists():
        print("   crm.db non trovato, si usera' seed builtin")
        return 0

    conn = sqlite3.connect(str(dev_db))
    try:
        # Check se esercizi gia' presenti
        n = conn.execute("SELECT COUNT(*) FROM esercizi").fetchone()[0]
        if n > 0:
            conn.close()
            return n

        conn.execute(f"ATTACH DATABASE '{source_db}' AS src")
        # Colonne esplicite — ordine diverso tra crm.db e crm_dev.db
        cols = (
            "id, trainer_id, nome, nome_en, categoria, pattern_movimento, "
            "force_type, lateral_pattern, muscoli_primari, muscoli_secondari, "
            "attrezzatura, difficolta, rep_range_forza, rep_range_ipertrofia, "
            "rep_range_resistenza, ore_recupero, descrizione_anatomica, "
            "descrizione_biomeccanica, setup, esecuzione, respirazione, "
            "tempo_consigliato, coaching_cues, errori_comuni, note_sicurezza, "
            "controindicazioni, catena_cinetica, piano_movimento, tipo_contrazione, "
            "muscle_map_url, is_builtin, in_subset, created_at, deleted_at"
        )
        conn.execute(f"INSERT INTO esercizi ({cols}) SELECT {cols} FROM src.esercizi")
        # Copia media e relazioni (se presenti)
        for table in ("esercizi_media", "esercizi_relazioni"):
            try:
                conn.execute(f"INSERT INTO {table} SELECT * FROM src.{table}")
            except Exception:
                pass
        conn.commit()  # PRIMA di DETACH (pitfall: transazione implicita blocca DETACH)
        conn.execute("DETACH DATABASE src")

        n_total = conn.execute("SELECT COUNT(*) FROM esercizi").fetchone()[0]
        n_active = conn.execute("SELECT COUNT(*) FROM esercizi WHERE in_subset = 1").fetchone()[0]
        print(f"   {n_total} esercizi copiati da crm.db ({n_active} attivi)")
        return n_total
    finally:
        conn.close()


def seed_complete(engine):
    """Seed completo: trainer, clienti, contratti, rate, eventi, misurazioni, goals, schede."""

    movements: list[CashMovement] = []
    all_events: list[Event] = []
    all_rates: list[Rate] = []
    all_contracts: list[Contract] = []
    credit_pool: dict[int, int] = {}
    credits_used: dict[int, int] = defaultdict(int)
    client_contracts: dict[int, list[Contract]] = defaultdict(list)
    grid = SlotGrid()

    with Session(engine) as session:

        # ────────────────────────────────────────────────
        # Step 0: Metriche (per FK integrity nel business DB)
        # ────────────────────────────────────────────────
        print("\n[0/10] Seed metriche...")
        from api.models.measurement import Metric
        n_existing = session.exec(text("SELECT COUNT(*) FROM metriche")).scalar_one()
        if n_existing < 22:
            for nome, nome_en, unita, cat, ordine in METRICS_SEED:
                session.add(Metric(
                    nome=nome, nome_en=nome_en, unita_misura=unita,
                    categoria=cat, ordinamento=ordine,
                ))
            session.flush()
            print(f"   22 metriche create (per FK integrity)")
        else:
            print(f"   {n_existing} metriche gia' presenti")

        # ────────────────────────────────────────────────
        # Step 0b: Esercizi (copiati da crm.db pre-session)
        # ────────────────────────────────────────────────
        print("\n[0b/10] Seed esercizi...")
        n_existing = session.exec(select(func.count(Exercise.id))).one()
        if n_existing == 0:
            # Fallback: usa seed builtin (esercizi copiati pre-session, vedi _copy_exercises)
            n_ex = seed_builtin_exercises(session)
            if n_ex > 0:
                print(f"   {n_ex} esercizi builtin (fallback)")
                session.exec(text("UPDATE esercizi SET in_subset = 1"))
                session.flush()
        else:
            n_active_ex = session.exec(
                select(func.count(Exercise.id)).where(Exercise.in_subset == True)  # noqa: E712
            ).one()
            print(f"   {n_existing} esercizi presenti ({n_active_ex} attivi)")

        # Carica IDs esercizi attivi per categoria
        active_exercises: dict[str, list[int]] = defaultdict(list)
        rows = session.exec(
            select(Exercise.id, Exercise.categoria, Exercise.pattern_movimento)
            .where(Exercise.in_subset == True)  # noqa: E712
        ).all()
        for eid, ecat, epat in rows:
            active_exercises[ecat].append(eid)
            active_exercises[f"pat_{epat}"].append(eid)
        n_active = sum(len(v) for k, v in active_exercises.items() if not k.startswith("pat_"))
        print(f"   {n_active} esercizi attivi caricati per workout")

        # ────────────────────────────────────────────────
        # Step 1: Trainer
        # ────────────────────────────────────────────────
        print("\n[1/10] Trainer...")
        trainer = Trainer(
            email="chiarabassani96@gmail.com",
            nome="Chiara",
            cognome="Bassani",
            hashed_password=hash_password("Fitness2026!"),
            is_active=True,
            saldo_iniziale_cassa=2500.0,
            data_saldo_iniziale=PERIOD_START,
        )
        session.add(trainer)
        session.flush()
        tid = trainer.id
        print(f"   Chiara Bassani (id={tid}), saldo iniziale 2.500 EUR")

        # ────────────────────────────────────────────────
        # Step 2: 30 Clienti con anamnesi
        # ────────────────────────────────────────────────
        print("\n[2/10] Clienti...")
        clients: list[Client] = []
        for cd in CLIENTS_DATA:
            data_compilazione = PERIOD_START + timedelta(days=random.randint(0, 14))
            anamnesi_json = _build_anamnesi(cd["profilo"], data_compilazione)
            client = Client(
                trainer_id=tid,
                nome=cd["nome"],
                cognome=cd["cognome"],
                telefono=cd.get("tel"),
                email=cd.get("email"),
                data_nascita=cd.get("nascita"),
                sesso=cd["sesso"],
                anamnesi_json=anamnesi_json,
                stato="Attivo",
            )
            session.add(client)
            clients.append(client)
        session.flush()
        print(f"   {len(clients)} clienti creati (24 attivi + 3 inattivi + 3 prospect)")

        # Primi 24 = clienti attivi con contratto
        # 24-26 = inattivi (contratto scaduto corto)
        # 27-29 = prospect (nessun contratto)
        contractable = clients[:27]  # 24 attivi + 3 inattivi

        # ────────────────────────────────────────────────
        # Step 3: Spese Ricorrenti
        # ────────────────────────────────────────────────
        print("\n[3/10] Spese ricorrenti...")
        rec_expenses: list[RecurringExpense] = []
        for rd in RECURRING_EXPENSES_DATA:
            exp = RecurringExpense(
                trainer_id=tid,
                nome=rd["nome"],
                categoria=rd["cat"],
                importo=rd["importo"],
                frequenza=rd["freq"],
                giorno_scadenza=rd["giorno"],
                data_inizio=rd["inizio"],
                attiva=True,
            )
            session.add(exp)
            rec_expenses.append(exp)
        session.flush()
        print(f"   {len(rec_expenses)} spese ricorrenti")

        # ────────────────────────────────────────────────
        # Step 4: Contratti + Rate + Pagamenti
        # ────────────────────────────────────────────────
        print("\n[4/10] Contratti + Rate...")

        # 3 inattivi: contratto corto iniziato a novembre, scaduto a dicembre
        for client in clients[24:27]:
            pkg = PACKAGES[0]  # PT 10
            prezzo = 400.0
            sale_date = date(2025, 11, random.randint(1, 15))
            start_date = sale_date + timedelta(days=2)
            end_date = date(2025, 12, 31)

            contract = Contract(
                trainer_id=tid, id_cliente=client.id,
                tipo_pacchetto=pkg["nome"], crediti_totali=10,
                prezzo_totale=prezzo, acconto=prezzo,
                data_vendita=sale_date, data_inizio=start_date,
                data_scadenza=end_date, totale_versato=prezzo,
                stato_pagamento="SALDATO", chiuso=True,
            )
            session.add(contract)
            session.flush()
            all_contracts.append(contract)
            client_contracts[client.id].append(contract)
            credit_pool[contract.id] = 0
            credits_used[contract.id] = 10

            movements.append(_make_movement(
                tid, "ENTRATA", prezzo, "ACCONTO_CONTRATTO", sale_date,
                id_cliente=client.id, id_contratto=contract.id,
                note=f"Pagamento completo {pkg['nome']} - {client.nome} {client.cognome}",
            ))

        # 24 attivi: contratti nel periodo dic-mar
        random.shuffle(contractable[:24])
        for i, client in enumerate(contractable[:24]):
            # Mese di inizio: distribuzione realistica
            if i < 8:
                sale_month = (2025, 12)    # 8 clienti dicembre
            elif i < 16:
                sale_month = (2026, 1)     # 8 clienti gennaio (buoni propositi)
            elif i < 22:
                sale_month = (2026, 2)     # 6 clienti febbraio
            else:
                sale_month = (2026, 3)     # 2 clienti marzo (recenti)

            pkg = random.choices(PACKAGES, PKG_WEIGHTS)[0]
            prezzo = _rand_price(pkg)
            sale_date = _rand_date_in_month(*sale_month)
            start_date = sale_date + timedelta(days=random.randint(0, 5))
            end_date = start_date + timedelta(days=pkg["mesi"] * 30)

            # Scenario basato su timeline
            if sale_month == (2026, 3):
                scenario = "new"
            elif end_date < TODAY - timedelta(days=20):
                scenario = "completed"
            else:
                scenario = "active"

            # Acconto (meno pagamenti totali per avere piu' rate)
            acconto_choice = random.choices(["zero", "partial", "full"], [15, 60, 25])[0]
            if acconto_choice == "zero":
                acconto = 0.0
            elif acconto_choice == "full":
                acconto = prezzo
            else:
                acconto = round(prezzo * random.uniform(0.15, 0.35) / 10) * 10

            contract = Contract(
                trainer_id=tid, id_cliente=client.id,
                tipo_pacchetto=pkg["nome"],
                crediti_totali=pkg["crediti"] if pkg["crediti"] > 0 else None,
                prezzo_totale=prezzo, acconto=acconto,
                data_vendita=sale_date, data_inizio=start_date,
                data_scadenza=end_date, totale_versato=acconto,
                stato_pagamento="PENDENTE", chiuso=False,
            )
            session.add(contract)
            session.flush()
            all_contracts.append(contract)
            client_contracts[client.id].append(contract)
            if pkg["crediti"] > 0:
                credit_pool[contract.id] = pkg["crediti"]

            # Acconto movement
            if acconto > 0:
                movements.append(_make_movement(
                    tid, "ENTRATA", acconto, "ACCONTO_CONTRATTO", sale_date,
                    id_cliente=client.id, id_contratto=contract.id,
                    note=f"Acconto {pkg['nome']} - {client.nome} {client.cognome}",
                ))
                if acconto >= prezzo - 0.01:
                    contract.stato_pagamento = "SALDATO"
                else:
                    contract.stato_pagamento = "PARZIALE"

            # Rate (skip se interamente pagato con acconto)
            if acconto >= prezzo - 0.01:
                if not pkg["crediti"]:
                    contract.chiuso = True
                continue

            residuo = prezzo - acconto
            n_rate = max(2, min(6, int(residuo / 100)))
            base_amt = round(residuo / n_rate, 2)
            rate_amounts = [base_amt] * n_rate
            rate_amounts[-1] = round(residuo - base_amt * (n_rate - 1), 2)

            totale_saldato = acconto
            for j, amt in enumerate(rate_amounts):
                rata_date = start_date + timedelta(days=30 * (j + 1))
                if rata_date > end_date:
                    rata_date = end_date

                if scenario == "completed":
                    stato_rata, saldato = "SALDATA", amt
                elif scenario == "active":
                    if rata_date <= TODAY:
                        # Rate gia' scadute: alta probabilita' di pagamento
                        roll = random.random()
                        if roll < 0.72:
                            stato_rata, saldato = "SALDATA", amt
                        elif roll < 0.88:
                            saldato = round(amt * random.uniform(0.3, 0.7), 2)
                            stato_rata = "PARZIALE"
                        else:
                            stato_rata, saldato = "PENDENTE", 0.0
                    else:
                        stato_rata, saldato = "PENDENTE", 0.0
                else:  # new
                    stato_rata, saldato = "PENDENTE", 0.0

                rate = Rate(
                    id_contratto=contract.id,
                    data_scadenza=rata_date,
                    importo_previsto=amt,
                    importo_saldato=saldato,
                    stato=stato_rata,
                    descrizione=f"Rata {j + 1}/{n_rate}",
                )
                session.add(rate)
                session.flush()
                all_rates.append(rate)

                if saldato > 0:
                    totale_saldato += saldato
                    pay_date = rata_date if rata_date < TODAY else TODAY
                    pay_date = pay_date + timedelta(days=random.randint(-3, 7))
                    if pay_date > TODAY:
                        pay_date = TODAY
                    movements.append(_make_movement(
                        tid, "ENTRATA", saldato, "PAGAMENTO_RATA", pay_date,
                        id_cliente=client.id, id_contratto=contract.id,
                        id_rata=rate.id,
                        note=f"Rata {j + 1}/{n_rate} - {client.nome} {client.cognome}",
                    ))

            # Aggiorna stato finanziario contratto
            contract.totale_versato = round(totale_saldato, 2)
            if contract.totale_versato >= prezzo - 0.01:
                contract.stato_pagamento = "SALDATO"
            elif contract.totale_versato > 0:
                contract.stato_pagamento = "PARZIALE"

        session.flush()
        n_saldate = sum(1 for r in all_rates if r.stato == "SALDATA")
        n_parziali = sum(1 for r in all_rates if r.stato == "PARZIALE")
        n_pendenti = sum(1 for r in all_rates if r.stato == "PENDENTE")
        print(f"   {len(all_contracts)} contratti, {len(all_rates)} rate "
              f"({n_saldate} SALDATE, {n_parziali} PARZIALI, {n_pendenti} PENDENTI)")

        # ────────────────────────────────────────────────
        # Step 5: Eventi Agenda (PT + Corso + Colloqui)
        # ────────────────────────────────────────────────
        print("\n[5/10] Eventi agenda...")

        event_end_horizon = TODAY + timedelta(days=21)

        # PT events per contratto
        pt_contracts = sorted(
            [c for c in all_contracts if c.crediti_totali and c.crediti_totali > 0],
            key=lambda c: c.data_inizio or c.data_vendita,
        )

        for contract in pt_contracts:
            cl_id = contract.id_cliente
            cl = next(c for c in clients if c.id == cl_id)
            crediti = contract.crediti_totali
            duration = ((contract.data_scadenza or end_date) - (contract.data_inizio or contract.data_vendita)).days
            session_interval = max(3, duration // max(crediti, 1))

            n_pref_days = 2 if crediti <= 10 else 3
            preferred_days = sorted(random.sample([0, 1, 2, 3, 4], n_pref_days))

            if random.random() < 0.45:
                pref_hours = random.sample(MORNING, min(3, len(MORNING)))
            else:
                pref_hours = random.sample(AFTERNOON, min(3, len(AFTERNOON)))

            consumed = 0
            start = contract.data_inizio or contract.data_vendita
            last_session = start - timedelta(days=session_interval)
            current = start
            schedule_end = min(contract.data_scadenza or event_end_horizon, event_end_horizon)

            while consumed < crediti and current <= schedule_end:
                days_since_last = (current - last_session).days
                is_preferred = current.weekday() in preferred_days
                interval_ok = days_since_last >= session_interval - 1

                if _is_open(current) and is_preferred and interval_ok:
                    hours = SATURDAY[:] if current.weekday() == 5 else pref_hours
                    hour = grid.find_free(current, hours)
                    if not hour:
                        hour = grid.find_free(current, _slots_for(current))

                    if hour:
                        grid.book(current, hour)

                        if current < TODAY - timedelta(days=3):
                            r = random.random()
                            if r < 0.82:
                                stato = "Completato"
                            elif r < 0.92:
                                stato = "Cancellato"
                            else:
                                stato = "Programmato"
                        elif current <= TODAY:
                            stato = random.choices(["Completato", "Programmato"], [65, 35])[0]
                        else:
                            stato = "Programmato"

                        all_events.append(Event(
                            trainer_id=tid,
                            categoria="PT",
                            titolo=f"PT {cl.nome} {cl.cognome}",
                            id_cliente=cl_id,
                            id_contratto=contract.id,
                            data_inizio=_make_dt(current, hour),
                            data_fine=_make_dt(current, hour + 1),
                            stato=stato,
                        ))

                        if stato != "Cancellato":
                            consumed += 1
                            credits_used[contract.id] = consumed
                            credit_pool[contract.id] = crediti - consumed

                        last_session = current

                current += timedelta(days=1)

        # Corsi (lun/mer/ven pomeriggio)
        current = PERIOD_START
        while current <= min(TODAY + timedelta(days=14), event_end_horizon):
            if _is_open(current) and current.weekday() in (0, 2, 4):
                for corso_h in [17, 18]:
                    if grid.is_free(current, corso_h):
                        grid.book(current, corso_h)
                        all_events.append(Event(
                            trainer_id=tid,
                            categoria="CORSO",
                            titolo=random.choice(CORSO_TITLES),
                            data_inizio=_make_dt(current, corso_h),
                            data_fine=_make_dt(current, corso_h + 1),
                            stato="Completato" if current < TODAY else "Programmato",
                        ))
                        break
            current += timedelta(days=1)

        # Colloqui (~20% al giorno)
        current = PERIOD_START
        while current <= TODAY:
            if _is_open(current) and random.random() < 0.20:
                h = grid.find_free(current, [9, 10, 15, 16])
                if h:
                    grid.book(current, h)
                    cl = random.choice(clients[:24])
                    all_events.append(Event(
                        trainer_id=tid,
                        categoria="COLLOQUIO",
                        titolo=f"Colloquio {cl.nome} {cl.cognome}",
                        id_cliente=cl.id,
                        data_inizio=_make_dt(current, h),
                        data_fine=_make_dt(current, h) + timedelta(minutes=45),
                        stato="Completato" if current < TODAY else "Programmato",
                    ))
            current += timedelta(days=1)

        for e in all_events:
            session.add(e)
        session.flush()

        st_comp = sum(1 for e in all_events if e.stato == "Completato")
        st_prog = sum(1 for e in all_events if e.stato == "Programmato")
        st_canc = sum(1 for e in all_events if e.stato == "Cancellato")
        print(f"   {len(all_events)} eventi ({st_comp} Completato, {st_prog} Programmato, {st_canc} Cancellato)")

        # ────────────────────────────────────────────────
        # Step 6: Spese confermate + variabili + personali
        # ────────────────────────────────────────────────
        print("\n[6/10] Movimenti uscita...")

        # Spese ricorrenti confermate
        n_rec_mov = 0
        for y, m in _months_range(PERIOD_START, TODAY):
            for exp in rec_expenses:
                occs = _get_occurrences(exp.frequenza, exp.giorno_scadenza, exp.data_inizio, y, m)
                for data_eff, key in occs:
                    if data_eff <= TODAY:
                        movements.append(_make_movement(
                            tid, "USCITA", exp.importo, exp.categoria or "Altro",
                            data_eff, id_spesa=exp.id, mese_anno=key,
                            note=exp.nome, operatore="CONFERMA_UTENTE",
                        ))
                        n_rec_mov += 1

        # Spese variabili business
        n_var_mov = 0
        for y, m in _months_range(PERIOD_START, TODAY):
            n = random.randint(1, 3)
            for _ in range(n):
                item = random.choice(VARIABLE_BUSINESS)
                nome, cat, lo, hi = item
                importo = round(random.uniform(lo, hi), 2)
                day = random.randint(3, 25)
                d = _safe_date(y, m, day)
                if d <= TODAY:
                    movements.append(_make_movement(
                        tid, "USCITA", importo, cat, d,
                        note=nome, operatore="MANUALE",
                    ))
                    n_var_mov += 1

        # Spese personali
        n_pers_mov = 0
        for y, m in _months_range(PERIOD_START, TODAY):
            for nome, cat, lo, hi, freq_min, freq_max in PERSONAL_EXPENSES:
                n = random.randint(freq_min, freq_max)
                for _ in range(n):
                    day = random.randint(1, 28)
                    importo = round(random.uniform(lo, hi), 2)
                    metodo = "CONTANTI" if cat == "Personale" and random.random() < 0.4 else _rand_method()
                    d = _safe_date(y, m, day)
                    if d <= TODAY:
                        movements.append(_make_movement(
                            tid, "USCITA", importo, cat, d,
                            note=nome, metodo=metodo, operatore="MANUALE",
                        ))
                        n_pers_mov += 1

        print(f"   {n_rec_mov} fisse + {n_var_mov} variabili + {n_pers_mov} personali")

        # ────────────────────────────────────────────────
        # Step 7: Misurazioni (4-6 per cliente attivo)
        # ────────────────────────────────────────────────
        print("\n[7/10] Misurazioni...")

        n_measurements_total = 0
        for client in clients[:24]:  # solo 24 attivi
            is_donna = _is_donna(client.sesso)
            n_mis = random.randint(4, 6)

            # Baseline realistici
            if is_donna:
                peso_base = random.uniform(55, 72)
                grasso_base = random.uniform(24, 32)
                altezza = random.uniform(158, 172)
                vita_base = random.uniform(68, 82)
                fianchi_base = random.uniform(92, 106)
                petto_base = random.uniform(84, 96)
                braccio_base = random.uniform(24, 28)
                coscia_base = random.uniform(52, 60)
                polpaccio_base = random.uniform(33, 38)
                fc_base = random.randint(64, 80)
                pa_sis_base = random.randint(105, 128)
                pa_dia_base = random.randint(65, 82)
                squat_1rm = round(random.uniform(40, 80), 1)
                panca_1rm = round(random.uniform(25, 50), 1)
                stacco_1rm = round(random.uniform(50, 90), 1)
            else:
                peso_base = random.uniform(70, 95)
                grasso_base = random.uniform(14, 24)
                altezza = random.uniform(170, 188)
                vita_base = random.uniform(78, 96)
                fianchi_base = random.uniform(90, 104)
                petto_base = random.uniform(94, 112)
                braccio_base = random.uniform(30, 36)
                coscia_base = random.uniform(54, 64)
                polpaccio_base = random.uniform(35, 42)
                fc_base = random.randint(58, 76)
                pa_sis_base = random.randint(115, 140)
                pa_dia_base = random.randint(70, 88)
                squat_1rm = round(random.uniform(70, 140), 1)
                panca_1rm = round(random.uniform(50, 100), 1)
                stacco_1rm = round(random.uniform(80, 160), 1)

            # Asimmetria bilaterale realistica (0.2-1.0 cm)
            asim_braccio = random.uniform(0.2, 1.0)
            asim_coscia = random.uniform(0.3, 1.2)
            asim_polpaccio = random.uniform(0.1, 0.6)

            for i in range(n_mis):
                days_offset = i * 28 + random.randint(-3, 3)  # ~mensile
                data_mis = PERIOD_START + timedelta(days=max(0, days_offset))
                if data_mis > TODAY:
                    break

                progress = i / max(1, n_mis - 1)

                # Trend realistici
                peso = round(peso_base - (progress * random.uniform(1.0, 3.5)) + random.uniform(-0.3, 0.3), 1)
                grasso = round(grasso_base - (progress * random.uniform(0.8, 2.5)) + random.uniform(-0.2, 0.2), 1)
                massa_magra = round(peso * (1 - grasso / 100), 1)
                bmi = round(peso / (altezza / 100) ** 2, 1)
                acqua = round(random.uniform(48, 62), 1)
                vita = round(vita_base - (progress * random.uniform(1.0, 4.0)) + random.uniform(-0.5, 0.5), 1)
                fianchi = round(fianchi_base - (progress * random.uniform(0.5, 2.0)) + random.uniform(-0.3, 0.3), 1)
                petto = round(petto_base + (progress * random.uniform(-0.5, 0.5)), 1)
                collo = round(random.uniform(34, 42) if not is_donna else random.uniform(30, 36), 1)

                braccio_dx = round(braccio_base + (progress * random.uniform(0.2, 0.8)), 1)
                braccio_sx = round(braccio_dx - asim_braccio, 1)
                coscia_dx = round(coscia_base + (progress * random.uniform(0.1, 0.5)), 1)
                coscia_sx = round(coscia_dx - asim_coscia, 1)
                polpaccio_dx = round(polpaccio_base + (progress * random.uniform(0, 0.3)), 1)
                polpaccio_sx = round(polpaccio_dx - asim_polpaccio, 1)

                fc = fc_base - int(progress * random.uniform(2, 6))
                pa_sis = pa_sis_base - int(progress * random.uniform(2, 8))
                pa_dia = pa_dia_base - int(progress * random.uniform(1, 4))

                # Forza cresce nel tempo
                squat = round(squat_1rm + (progress * random.uniform(5, 15)), 1)
                panca = round(panca_1rm + (progress * random.uniform(3, 10)), 1)
                stacco = round(stacco_1rm + (progress * random.uniform(5, 15)), 1)

                mis = ClientMeasurement(
                    id_cliente=client.id,
                    trainer_id=tid,
                    data_misurazione=data_mis,
                    note=f"Misurazione {i + 1}" if i == 0 else None,
                )
                session.add(mis)
                session.flush()

                # Tutte e 22 le metriche
                values = [
                    (MET_PESO, peso),
                    (MET_ALTEZZA, altezza),
                    (MET_GRASSO, grasso),
                    (MET_MASSA_MAGRA, massa_magra),
                    (MET_BMI, bmi),
                    (MET_ACQUA, acqua),
                    (MET_COLLO, collo),
                    (MET_PETTO, petto),
                    (MET_VITA, vita),
                    (MET_FIANCHI, fianchi),
                    (MET_BRACCIO_DX, braccio_dx),
                    (MET_BRACCIO_SX, braccio_sx),
                    (MET_COSCIA_DX, coscia_dx),
                    (MET_COSCIA_SX, coscia_sx),
                    (MET_POLPACCIO_DX, polpaccio_dx),
                    (MET_POLPACCIO_SX, polpaccio_sx),
                    (MET_FC_RIPOSO, fc),
                    (MET_PA_SIS, pa_sis),
                    (MET_PA_DIA, pa_dia),
                    (MET_SQUAT_1RM, squat),
                    (MET_PANCA_1RM, panca),
                    (MET_STACCO_1RM, stacco),
                ]
                for met_id, val in values:
                    session.add(MeasurementValue(
                        id_misurazione=mis.id,
                        id_metrica=met_id,
                        valore=val,
                    ))

                n_measurements_total += 1

        session.flush()
        print(f"   {n_measurements_total} misurazioni (22 metriche ciascuna)")

        # ────────────────────────────────────────────────
        # Step 8: Obiettivi (1-2 per cliente attivo)
        # ────────────────────────────────────────────────
        print("\n[8/10] Obiettivi...")

        n_goals = 0
        for client in clients[:24]:
            is_donna = _is_donna(client.sesso)
            profilo = next(cd for cd in CLIENTS_DATA if cd["nome"] == client.nome and cd["cognome"] == client.cognome)["profilo"]

            # Goal primario: quasi sempre peso o grasso
            if profilo in ("metabolico",):
                goal_primary = {
                    "id_metrica": MET_PESO, "direzione": "diminuire",
                    "target_delta": random.uniform(-6, -3),
                    "tipo": "corporeo", "priorita": 1,
                }
            elif profilo.startswith("ortopedico"):
                goal_primary = {
                    "id_metrica": MET_GRASSO, "direzione": "diminuire",
                    "target_delta": random.uniform(-4, -2),
                    "tipo": "corporeo", "priorita": 2,
                }
            elif profilo == "cardiovascolare":
                goal_primary = {
                    "id_metrica": MET_PA_SIS, "direzione": "diminuire",
                    "target_delta": random.uniform(-12, -5),
                    "tipo": "corporeo", "priorita": 1,
                }
            else:
                goal_primary = random.choice([
                    {"id_metrica": MET_PESO, "direzione": "diminuire", "target_delta": random.uniform(-5, -2), "tipo": "corporeo", "priorita": 2},
                    {"id_metrica": MET_GRASSO, "direzione": "diminuire", "target_delta": random.uniform(-4, -2), "tipo": "corporeo", "priorita": 2},
                    {"id_metrica": MET_PANCA_1RM, "direzione": "aumentare", "target_delta": random.uniform(10, 25), "tipo": "atletico", "priorita": 2},
                ])

            # Ottieni baseline dalla prima misurazione (se esiste)
            first_mis = session.exec(
                select(ClientMeasurement)
                .where(ClientMeasurement.id_cliente == client.id)
                .order_by(ClientMeasurement.data_misurazione)
            ).first()
            baseline_val = None
            baseline_date = PERIOD_START + timedelta(days=random.randint(0, 14))
            if first_mis:
                baseline_date = first_mis.data_misurazione
                val_row = session.exec(
                    select(MeasurementValue)
                    .where(
                        MeasurementValue.id_misurazione == first_mis.id,
                        MeasurementValue.id_metrica == goal_primary["id_metrica"],
                    )
                ).first()
                if val_row:
                    baseline_val = val_row.valore

            target_val = round(baseline_val + goal_primary["target_delta"], 1) if baseline_val else None

            # Stato: la maggior parte attivi, qualcuno raggiunto
            stato = "attivo"
            completed_at = None
            if baseline_val and target_val:
                latest_mis = session.exec(
                    select(ClientMeasurement)
                    .where(ClientMeasurement.id_cliente == client.id)
                    .order_by(ClientMeasurement.data_misurazione.desc())
                ).first()
                if latest_mis:
                    latest_val_row = session.exec(
                        select(MeasurementValue)
                        .where(
                            MeasurementValue.id_misurazione == latest_mis.id,
                            MeasurementValue.id_metrica == goal_primary["id_metrica"],
                        )
                    ).first()
                    if latest_val_row:
                        latest_val = latest_val_row.valore
                        if goal_primary["direzione"] == "diminuire" and latest_val <= target_val:
                            stato = "raggiunto"
                            completed_at = datetime.combine(latest_mis.data_misurazione, datetime.min.time())
                        elif goal_primary["direzione"] == "aumentare" and latest_val >= target_val:
                            stato = "raggiunto"
                            completed_at = datetime.combine(latest_mis.data_misurazione, datetime.min.time())

            goal = ClientGoal(
                id_cliente=client.id,
                trainer_id=tid,
                id_metrica=goal_primary["id_metrica"],
                direzione=goal_primary["direzione"],
                valore_target=target_val,
                valore_baseline=baseline_val,
                data_baseline=baseline_date,
                data_inizio=baseline_date,
                data_scadenza=baseline_date + timedelta(days=120),
                tipo_obiettivo=goal_primary["tipo"],
                priorita=goal_primary["priorita"],
                stato=stato,
                completed_at=completed_at,
                completato_automaticamente=stato == "raggiunto",
            )
            session.add(goal)
            n_goals += 1

            # Goal secondario per ~60% dei clienti
            if random.random() < 0.60:
                secondary = random.choice([
                    {"id_metrica": MET_VITA, "direzione": "diminuire", "tipo": "corporeo"},
                    {"id_metrica": MET_SQUAT_1RM, "direzione": "aumentare", "tipo": "atletico"},
                    {"id_metrica": MET_FC_RIPOSO, "direzione": "diminuire", "tipo": "corporeo"},
                ])

                sec_baseline = None
                if first_mis:
                    sec_val_row = session.exec(
                        select(MeasurementValue)
                        .where(
                            MeasurementValue.id_misurazione == first_mis.id,
                            MeasurementValue.id_metrica == secondary["id_metrica"],
                        )
                    ).first()
                    if sec_val_row:
                        sec_baseline = sec_val_row.valore

                delta = random.uniform(-5, -2) if secondary["direzione"] == "diminuire" else random.uniform(10, 30)
                sec_target = round(sec_baseline + delta, 1) if sec_baseline else None

                session.add(ClientGoal(
                    id_cliente=client.id,
                    trainer_id=tid,
                    id_metrica=secondary["id_metrica"],
                    direzione=secondary["direzione"],
                    valore_target=sec_target,
                    valore_baseline=sec_baseline,
                    data_baseline=baseline_date,
                    data_inizio=baseline_date,
                    data_scadenza=baseline_date + timedelta(days=150),
                    tipo_obiettivo=secondary["tipo"],
                    priorita=3,
                    stato="attivo",
                ))
                n_goals += 1

        session.flush()
        print(f"   {n_goals} obiettivi creati")

        # ────────────────────────────────────────────────
        # Step 9: Schede Allenamento + Workout Logs
        # ────────────────────────────────────────────────
        print("\n[9/10] Schede allenamento + log...")

        n_plans = 0
        n_sessions = 0
        n_exercises = 0
        n_logs = 0

        for client in clients[:24]:
            n_schede = 1 if random.random() < 0.70 else 2

            for s_idx in range(n_schede):
                obiettivo = random.choice(OBIETTIVI_FITNESS)
                livello = random.choice(LIVELLI_FITNESS)

                data_creazione = PERIOD_START + timedelta(days=random.randint(0, 60 + s_idx * 30))
                if data_creazione > TODAY:
                    data_creazione = TODAY - timedelta(days=7)

                data_inizio = data_creazione + timedelta(days=random.randint(0, 5))
                data_fine = data_inizio + timedelta(weeks=8)

                plan = WorkoutPlan(
                    trainer_id=tid,
                    id_cliente=client.id,
                    nome=f"Scheda {'ABCD'[s_idx]}",
                    obiettivo=obiettivo,
                    livello=livello,
                    durata_settimane=8,
                    sessioni_per_settimana=3,
                    data_inizio=data_inizio,
                    data_fine=data_fine if data_fine <= TODAY else None,
                    note=f"Piano {obiettivo} - livello {livello}",
                )
                session.add(plan)
                session.flush()
                n_plans += 1

                # Sessioni da template
                templates = SESSION_TEMPLATES.get(obiettivo, SESSION_TEMPLATES["generale"])

                plan_sessions: list[WorkoutSession] = []
                for i, tpl in enumerate(templates, 1):
                    ws = WorkoutSession(
                        id_scheda=plan.id,
                        numero_sessione=i,
                        nome_sessione=tpl["nome"],
                        focus_muscolare=tpl["focus"],
                        durata_minuti=tpl["durata"],
                    )
                    session.add(ws)
                    session.flush()
                    n_sessions += 1
                    plan_sessions.append(ws)

                    # Esercizi per sessione: 1 avviamento + 4-5 principali + 1 stretching
                    ordine = 1

                    # Avviamento
                    avv_ids = active_exercises.get("avviamento", [])
                    if avv_ids:
                        session.add(WorkoutExercise(
                            id_sessione=ws.id,
                            id_esercizio=random.choice(avv_ids),
                            ordine=ordine,
                            serie=2,
                            ripetizioni="10-12",
                            tempo_riposo_sec=30,
                            categoria_esercizio="avviamento",
                        ))
                        ordine += 1
                        n_exercises += 1

                    # Principali (4-5 esercizi dai pattern della sessione)
                    n_main = random.randint(4, 5)
                    used_ids: set[int] = set()
                    for _ in range(n_main):
                        pattern = random.choice(tpl["patterns"])
                        candidates = [eid for eid in active_exercises.get(f"pat_{pattern}", []) if eid not in used_ids]
                        if not candidates:
                            candidates = [eid for eid in active_exercises.get("compound", []) + active_exercises.get("isolation", []) if eid not in used_ids]
                        if candidates:
                            ex_id = random.choice(candidates)
                            used_ids.add(ex_id)

                            serie = random.choice([3, 4]) if livello != "beginner" else 3
                            rip = random.choice(["6-8", "8-10", "10-12"]) if obiettivo in ("forza", "ipertrofia") else random.choice(["12-15", "15-20"])
                            riposo = random.choice([90, 120]) if obiettivo in ("forza", "ipertrofia") else random.choice([45, 60])
                            carico = round(random.uniform(10, 80), 1) if random.random() < 0.6 else None

                            session.add(WorkoutExercise(
                                id_sessione=ws.id,
                                id_esercizio=ex_id,
                                ordine=ordine,
                                serie=serie,
                                ripetizioni=rip,
                                tempo_riposo_sec=riposo,
                                carico_kg=carico,
                                categoria_esercizio="principale",
                            ))
                            ordine += 1
                            n_exercises += 1

                    # Stretching
                    stretch_ids = active_exercises.get("stretching", [])
                    if stretch_ids:
                        session.add(WorkoutExercise(
                            id_sessione=ws.id,
                            id_esercizio=random.choice(stretch_ids),
                            ordine=ordine,
                            serie=2,
                            ripetizioni="30s",
                            tempo_riposo_sec=15,
                            categoria_esercizio="stretching",
                        ))
                        n_exercises += 1

                # Workout Logs: esecuzioni passate (~60-80% delle settimane)
                if plan.data_inizio and plan.data_inizio < TODAY:
                    weeks_elapsed = min(8, (TODAY - plan.data_inizio).days // 7)
                    for week in range(weeks_elapsed):
                        # ~70% compliance
                        if random.random() < 0.70:
                            for ws in plan_sessions:
                                if random.random() < 0.75:  # non tutte le sessioni
                                    log_date = plan.data_inizio + timedelta(weeks=week, days=random.randint(0, 6))
                                    if log_date <= TODAY:
                                        session.add(WorkoutLog(
                                            id_scheda=plan.id,
                                            id_sessione=ws.id,
                                            id_cliente=client.id,
                                            trainer_id=tid,
                                            data_esecuzione=log_date,
                                        ))
                                        n_logs += 1

        session.flush()
        print(f"   {n_plans} schede, {n_sessions} sessioni, {n_exercises} esercizi, {n_logs} log")

        # ────────────────────────────────────────────────
        # Step 10: Integrita' + Stato Clienti + Commit
        # ────────────────────────────────────────────────
        print("\n[10/10] Integrita' e commit...")

        # Aggiorna crediti_usati e chiuso su contratti
        for contract in all_contracts:
            if contract.crediti_totali and contract.crediti_totali > 0:
                used = credits_used.get(contract.id, 0)
                contract.crediti_usati = used
                contract.chiuso = (
                    contract.stato_pagamento == "SALDATO"
                    and used >= contract.crediti_totali
                )
            elif contract.stato_pagamento == "SALDATO":
                contract.chiuso = True

        # Sincronizza Client.stato
        n_synced_inactive = 0
        for client in clients:
            clist = client_contracts.get(client.id, [])
            if not clist:
                client.stato = "Attivo"  # prospect
                continue

            has_active = False
            for c in clist:
                if c.chiuso:
                    continue
                if c.crediti_totali and credit_pool.get(c.id, 0) > 0:
                    has_active = True
                    break
                if not c.crediti_totali and c.data_scadenza and c.data_scadenza >= TODAY:
                    has_active = True
                    break

            if has_active:
                client.stato = "Attivo"
            else:
                last = max(clist, key=lambda c: c.data_scadenza or date.min)
                if last.data_scadenza and last.data_scadenza < TODAY - timedelta(days=45):
                    client.stato = "Inattivo"
                    n_synced_inactive += 1
                else:
                    client.stato = "Attivo"

        # Validazione integrita' finanziaria
        n_fixes = 0
        for contract in all_contracts:
            rate_sum = sum(
                r.importo_saldato for r in all_rates
                if r.id_contratto == contract.id and r.importo_saldato > 0
            )
            expected = round(contract.acconto + rate_sum, 2)
            if abs(contract.totale_versato - expected) > 0.02:
                contract.totale_versato = expected
                n_fixes += 1

        # Insert tutti i movimenti
        for m in movements:
            session.add(m)
        session.flush()

        # COMMIT atomico
        session.commit()

        # ── Summary ──
        n_active = sum(1 for c in clients if c.stato == "Attivo")
        n_inactive = sum(1 for c in clients if c.stato == "Inattivo")
        tot_entrate = sum(m.importo for m in movements if m.tipo == "ENTRATA")
        tot_uscite = sum(m.importo for m in movements if m.tipo == "USCITA")

        print(f"\n   Stato clienti: {n_active} Attivo, {n_inactive} Inattivo")
        if n_fixes > 0:
            print(f"   {n_fixes} contratti corretti (integrity)")

        print(f"\n{'=' * 60}")
        print(f"SEED COMPLETATO")
        print(f"{'=' * 60}")
        print(f"   Trainer:          1 (Chiara Bassani)")
        print(f"   Clienti:          {len(clients)} (24 attivi + 3 inattivi + 3 prospect)")
        print(f"   Contratti:        {len(all_contracts)}")
        print(f"   Rate:             {len(all_rates)} ({n_saldate} SALDATE)")
        print(f"   Eventi:           {len(all_events)}")
        print(f"   Movimenti:        {len(movements)}")
        print(f"   Misurazioni:      {n_measurements_total}")
        print(f"   Obiettivi:        {n_goals}")
        print(f"   Schede:           {n_plans}")
        print(f"   Workout Logs:     {n_logs}")
        print(f"   Entrate totali:   {tot_entrate:>10,.2f} EUR")
        print(f"   Uscite totali:    {tot_uscite:>10,.2f} EUR")
        print(f"   Periodo: {PERIOD_START} -> {TODAY}")
        print(f"\n   Login: chiarabassani96@gmail.com / Fitness2026!")
        print(f"   Porta dev: 8001")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SEED DEV COMPLETE - Database Realistico 30 Clienti x 4 Mesi")
    print("=" * 60)
    print(f"Target: data/crm_dev.db")
    print(f"Periodo: {PERIOD_START} -> {TODAY}")
    print("=" * 60)
    print("\n⚠️  ATTENZIONE: Questo resetta completamente crm_dev.db!")
    print("Procedendo in 3 secondi...\n")

    import time
    time.sleep(3)

    engine = reset_database()
    seed_complete(engine)
