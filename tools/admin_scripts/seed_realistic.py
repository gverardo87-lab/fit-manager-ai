#!/usr/bin/env python3
"""
Seed Realistico — Database di 1 anno con 50 clienti per test e sviluppo.

Simula l'attivita' annuale di Chiara Bassani, personal trainer P.IVA
con studio a gestione diretta. La titolare vive coi soldi dell'azienda:
contabilita' unica con spese business e personali.

COSA CREA:
- 1 Trainer (Chiara Bassani)
- 50 Clienti (35 attivi, 10 inattivi, 5 nuovi)
- 15 Spese ricorrenti (affitto, utenze, INPS, commercialista, ...)
- ~45 Contratti con rate e pagamenti (7 scenari diversi)
- ~1000 Eventi day-by-day senza sovrapposizioni
- ~670 CashMovement (entrate rate + uscite fisse/variabili/personali)

INVARIANTI GARANTITI:
- Ogni rata SALDATA ha CashMovement ENTRATA corrispondente
- contract.totale_versato = acconto + sum(rate.importo_saldato)
- Zero eventi sovrapposti (SlotGrid engine)
- mese_anno UNIQUE per spese ricorrenti confermate

ESEGUI dalla root del progetto (ferma il server API prima!):
    python -m tools.admin_scripts.seed_realistic
"""

import os
import sys
import random
import calendar
from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

# ── Setup path ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, create_engine
from api.config import DATABASE_URL
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.rate import Rate
from api.models.event import Event
from api.models.movement import CashMovement
from api.models.recurring_expense import RecurringExpense
from api.auth.service import hash_password

# Riusa reset_database() dallo script originale
from tools.admin_scripts.reset_and_seed import reset_database

# Determinismo: stesso DB ad ogni esecuzione
random.seed(42)


# ═══════════════════════════════════════════════════════════════
# SECTION 2: Costanti di configurazione
# ═══════════════════════════════════════════════════════════════

YEAR_START = date(2025, 3, 1)
YEAR_END = date(2026, 2, 28)
TODAY = date(2026, 2, 23)

# Peso stagionale (1.0 = baseline). Modula contratti/mese e densita' eventi.
SEASONAL = {
    1: 1.5,   # gen — boom buoni propositi
    2: 1.2,   # feb — ancora forte
    3: 1.3,   # mar — post-inverno
    4: 1.2,   # apr — prova costume
    5: 1.1,   # mag — steady
    6: 0.8,   # giu — calo estivo
    7: 0.6,   # lug — ridotto
    8: 0.3,   # ago — Ferragosto
    9: 1.3,   # set — ripresa
    10: 1.2,  # ott — forte
    11: 1.0,  # nov — steady
    12: 0.7,  # dic — feste
}

# Studio chiuso (nessun evento in questi range)
CLOSED = [
    (date(2025, 8, 10), date(2025, 8, 24)),   # Ferragosto
    (date(2025, 12, 24), date(2025, 12, 26)),  # Natale
    (date(2025, 12, 31), date(2026, 1, 1)),    # Capodanno
]

# Slot orari disponibili (ora inizio)
MORNING = [7, 8, 9, 10, 11]
AFTERNOON = [15, 16, 17, 18, 19, 20]
SATURDAY = [8, 9, 10, 11, 12]

# Pacchetti PT (pricing italiano reale)
PACKAGES = [
    {"nome": "PT 10 Sedute",      "crediti": 10, "p_min": 350,  "p_max": 450,  "mesi": 3},
    {"nome": "PT 20 Sedute",      "crediti": 20, "p_min": 600,  "p_max": 800,  "mesi": 5},
    {"nome": "PT 30 Sedute",      "crediti": 30, "p_min": 850,  "p_max": 1100, "mesi": 8},
    {"nome": "Sala Mensile",      "crediti": 0,  "p_min": 40,   "p_max": 70,   "mesi": 1},
    {"nome": "Sala Trimestrale",  "crediti": 0,  "p_min": 100,  "p_max": 180,  "mesi": 3},
]
PKG_WEIGHTS = [35, 30, 15, 10, 10]  # PT dominante

# Quanti contratti creare per mese (indice = mese 1-12)
CONTRACTS_PER_MONTH = {
    3: 4, 4: 4, 5: 3, 6: 2, 7: 2, 8: 1,
    9: 5, 10: 4, 11: 3, 12: 2, 1: 6, 2: 4,
}

PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"]
PM_WEIGHTS = [30, 40, 30]

CORSO_TITLES = [
    "Pilates Gruppo", "Functional Training", "Stretching Posturale",
    "Circuit Training", "Ginnastica Dolce", "Core Stability",
]


# ═══════════════════════════════════════════════════════════════
# SECTION 3: Tabelle dati statici
# ═══════════════════════════════════════════════════════════════

CLIENTS_DATA = [
    # ── 35 Attivi ──
    {"nome": "Alessia",    "cognome": "Marchetti",  "tel": "333-1001001", "email": "alessia.marchetti@gmail.com",    "nascita": date(1991, 4, 12),  "sesso": "Donna"},
    {"nome": "Francesco",  "cognome": "Russo",      "tel": "339-2002002", "email": "f.russo@hotmail.it",            "nascita": date(1988, 9, 5),   "sesso": "Uomo"},
    {"nome": "Giulia",     "cognome": "Ferrari",    "tel": "347-3003003", "email": "giulia.ferrari@gmail.com",      "nascita": date(1995, 1, 22),  "sesso": "Donna"},
    {"nome": "Marco",      "cognome": "Bianchi",    "tel": "320-4004004", "email": "marco.bianchi@libero.it",       "nascita": date(1985, 7, 18),  "sesso": "Uomo"},
    {"nome": "Sara",       "cognome": "Romano",     "tel": "338-5005005", "email": "sara.romano@gmail.com",         "nascita": date(1993, 3, 9),   "sesso": "Donna"},
    {"nome": "Luca",       "cognome": "Colombo",    "tel": "340-6006006", "email": "luca.colombo@outlook.it",       "nascita": date(1990, 11, 30), "sesso": "Uomo"},
    {"nome": "Valentina",  "cognome": "Ricci",      "tel": "349-7007007", "email": "vale.ricci@gmail.com",          "nascita": date(1987, 6, 14),  "sesso": "Donna"},
    {"nome": "Andrea",     "cognome": "Moretti",    "tel": "328-8008008", "email": "andrea.moretti@gmail.com",      "nascita": date(1992, 2, 28),  "sesso": "Uomo"},
    {"nome": "Chiara",     "cognome": "Conti",      "tel": "335-9009009", "email": "chiara.conti@yahoo.it",         "nascita": date(1996, 8, 3),   "sesso": "Donna"},
    {"nome": "Davide",     "cognome": "Gallo",      "tel": "331-1010010", "email": "davide.gallo@gmail.com",        "nascita": date(1983, 12, 25), "sesso": "Uomo"},
    {"nome": "Federica",   "cognome": "Costa",      "tel": "342-1110011", "email": "fede.costa@hotmail.it",         "nascita": date(1994, 5, 7),   "sesso": "Donna"},
    {"nome": "Simone",     "cognome": "Giordano",   "tel": "345-1210012", "email": "simone.giordano@gmail.com",     "nascita": date(1989, 10, 19), "sesso": "Uomo"},
    {"nome": "Elisa",      "cognome": "Mancini",    "tel": "327-1310013", "email": "elisa.mancini@gmail.com",       "nascita": date(1997, 4, 1),   "sesso": "Donna"},
    {"nome": "Matteo",     "cognome": "Barbieri",   "tel": "334-1410014", "email": "matteo.barbieri@libero.it",     "nascita": date(1986, 8, 29),  "sesso": "Uomo"},
    {"nome": "Martina",    "cognome": "Fontana",    "tel": "348-1510015", "email": "martina.fontana@gmail.com",     "nascita": date(1991, 12, 10), "sesso": "Donna"},
    {"nome": "Lorenzo",    "cognome": "Santoro",    "tel": "329-1610016", "email": "lorenzo.santoro@outlook.it",    "nascita": date(1984, 3, 17),  "sesso": "Uomo"},
    {"nome": "Anna",       "cognome": "Marini",     "tel": "336-1710017", "email": "anna.marini@gmail.com",         "nascita": date(1998, 7, 23),  "sesso": "Donna"},
    {"nome": "Stefano",    "cognome": "Leone",      "tel": "341-1810018", "email": "stefano.leone@gmail.com",       "nascita": date(1982, 1, 6),   "sesso": "Uomo"},
    {"nome": "Roberta",    "cognome": "Longo",      "tel": "330-1910019", "email": "roberta.longo@yahoo.it",        "nascita": date(1993, 9, 14),  "sesso": "Donna"},
    {"nome": "Alessandro", "cognome": "Greco",      "tel": "337-2010020", "email": "ale.greco@gmail.com",           "nascita": date(1990, 5, 2),   "sesso": "Uomo"},
    {"nome": "Silvia",     "cognome": "Bruno",      "tel": "343-2110021", "email": "silvia.bruno@gmail.com",        "nascita": date(1996, 11, 8),  "sesso": "Donna"},
    {"nome": "Giacomo",    "cognome": "De Luca",    "tel": "346-2210022", "email": "giacomo.deluca@hotmail.it",     "nascita": date(1987, 2, 19),  "sesso": "Uomo"},
    {"nome": "Claudia",    "cognome": "Pellegrini", "tel": "326-2310023", "email": "claudia.pellegrini@gmail.com",  "nascita": date(1994, 6, 30),  "sesso": "Donna"},
    {"nome": "Fabio",      "cognome": "Caruso",     "tel": "332-2410024", "email": "fabio.caruso@libero.it",        "nascita": date(1981, 10, 12), "sesso": "Uomo"},
    {"nome": "Laura",      "cognome": "Rinaldi",    "tel": "344-2510025", "email": "laura.rinaldi@gmail.com",       "nascita": date(1992, 4, 5),   "sesso": "Donna"},
    {"nome": "Elena",      "cognome": "Vitale",     "tel": "350-2610026", "email": "elena.vitale@gmail.com",        "nascita": date(1999, 1, 16),  "sesso": "Donna"},
    {"nome": "Paolo",      "cognome": "Ferrara",    "tel": "333-2710027", "email": "paolo.ferrara@outlook.it",      "nascita": date(1985, 8, 22),  "sesso": "Uomo"},
    {"nome": "Monica",     "cognome": "Esposito",   "tel": "339-2810028", "email": "monica.esposito@gmail.com",     "nascita": date(1988, 12, 4),  "sesso": "Donna"},
    {"nome": "Cristina",   "cognome": "De Rosa",    "tel": "347-2910029", "email": "cristina.derosa@yahoo.it",      "nascita": date(1995, 3, 28),  "sesso": "Donna"},
    {"nome": "Michele",    "cognome": "Rizzo",      "tel": "320-3010030", "email": "michele.rizzo@gmail.com",       "nascita": date(1991, 7, 9),   "sesso": "Uomo"},
    {"nome": "Ilaria",     "cognome": "Sartori",    "tel": None,          "email": "ilaria.sartori@gmail.com",      "nascita": date(1993, 10, 1),  "sesso": "Donna"},
    {"nome": "Daniele",    "cognome": "Villa",      "tel": "338-3210032", "email": None,                            "nascita": date(1986, 5, 15),  "sesso": "Uomo"},
    {"nome": "Francesca",  "cognome": "Fabbri",     "tel": "340-3310033", "email": "francesca.fabbri@gmail.com",    "nascita": date(1997, 9, 20),  "sesso": "Donna"},
    {"nome": "Nicola",     "cognome": "Marchese",   "tel": "349-3410034", "email": "nicola.marchese@hotmail.it",    "nascita": date(1980, 2, 8),   "sesso": "Uomo"},
    {"nome": "Sofia",      "cognome": "Gatti",      "tel": "328-3510035", "email": "sofia.gatti@gmail.com",         "nascita": date(1998, 6, 17),  "sesso": "Donna"},
    # ── 10 Inattivi (hanno smesso durante l'anno) ──
    {"nome": "Roberto",    "cognome": "Palumbo",    "tel": "335-3610036", "email": "roberto.palumbo@libero.it",     "nascita": date(1979, 11, 22), "sesso": "Uomo",  "stato": "Inattivo"},
    {"nome": "Patrizia",   "cognome": "Parisi",     "tel": "331-3710037", "email": "patrizia.parisi@gmail.com",     "nascita": date(1975, 4, 3),   "sesso": "Donna", "stato": "Inattivo"},
    {"nome": "Massimo",    "cognome": "Lombardi",   "tel": "342-3810038", "email": "massimo.lombardi@yahoo.it",     "nascita": date(1978, 8, 14),  "sesso": "Uomo",  "stato": "Inattivo"},
    {"nome": "Paola",      "cognome": "Sorrentino", "tel": "345-3910039", "email": "paola.sorrentino@gmail.com",    "nascita": date(1982, 1, 29),  "sesso": "Donna", "stato": "Inattivo"},
    {"nome": "Giuseppe",   "cognome": "Gentile",    "tel": "327-4010040", "email": None,                            "nascita": date(1976, 6, 10),  "sesso": "Uomo",  "stato": "Inattivo"},
    {"nome": "Antonella",  "cognome": "Valentini",  "tel": "334-4110041", "email": "antonella.v@hotmail.it",        "nascita": date(1983, 9, 25),  "sesso": "Donna", "stato": "Inattivo"},
    {"nome": "Giovanni",   "cognome": "Ferri",      "tel": "348-4210042", "email": "giovanni.ferri@gmail.com",      "nascita": date(1977, 12, 7),  "sesso": "Uomo",  "stato": "Inattivo"},
    {"nome": "Teresa",     "cognome": "Vitali",     "tel": None,          "email": "teresa.vitali@libero.it",       "nascita": date(1980, 3, 18),  "sesso": "Donna", "stato": "Inattivo"},
    {"nome": "Vincenzo",   "cognome": "Amato",      "tel": "329-4410044", "email": "vincenzo.amato@gmail.com",      "nascita": date(1974, 7, 31),  "sesso": "Uomo",  "stato": "Inattivo"},
    {"nome": "Grazia",     "cognome": "Lombardo",   "tel": "336-4510045", "email": "grazia.lombardo@yahoo.it",      "nascita": date(1981, 5, 13),  "sesso": "Donna", "stato": "Inattivo"},
    # ── 5 Nuovi (registrati da poco, senza contratto) ──
    {"nome": "Beatrice",   "cognome": "Testa",      "tel": "341-4610046", "email": "beatrice.testa@gmail.com",      "nascita": date(2000, 2, 14),  "sesso": "Donna"},
    {"nome": "Edoardo",    "cognome": "Neri",       "tel": "330-4710047", "email": "edoardo.neri@outlook.it",       "nascita": date(1999, 8, 6),   "sesso": "Uomo"},
    {"nome": "Giorgia",    "cognome": "Pellegrino", "tel": "337-4810048", "email": "giorgia.pellegrino@gmail.com",  "nascita": date(2001, 11, 23), "sesso": "Donna"},
    {"nome": "Tommaso",    "cognome": "Piras",      "tel": "343-4910049", "email": "tommaso.piras@gmail.com",       "nascita": date(2000, 4, 9),   "sesso": "Uomo"},
    {"nome": "Aurora",     "cognome": "Serra",      "tel": "346-5010050", "email": "aurora.serra@hotmail.it",       "nascita": date(2001, 7, 1),   "sesso": "Donna"},
]

# Anamnesi per alcuni clienti (JSON string)
ANAMNESI = {
    3:  '{"note": "Ernia L4-L5, evitare carichi assiali pesanti"}',
    9:  '{"note": "Problemi posturali, cifosi dorsale"}',
    17: '{"note": "Operata al ginocchio dx 2023, riabilitazione completata"}',
    23: '{"note": "Ipertensione controllata con farmaci"}',
    33: '{"note": "Gravidanza recente, ripresa graduale"}',
}

RECURRING_EXPENSES_DATA = [
    {"nome": "Affitto sala",                "importo": 800.0,  "freq": "MENSILE",      "giorno": 5,  "cat": "Affitto",       "inizio": date(2025, 1, 1)},
    {"nome": "Utenze (luce+gas)",           "importo": 180.0,  "freq": "MENSILE",      "giorno": 10, "cat": "Utenze",        "inizio": date(2025, 1, 1)},
    {"nome": "Internet fibra",              "importo": 34.90,  "freq": "MENSILE",      "giorno": 20, "cat": "Utenze",        "inizio": date(2025, 1, 1)},
    {"nome": "Software gestionale",         "importo": 29.0,   "freq": "MENSILE",      "giorno": 1,  "cat": "Software",      "inizio": date(2025, 1, 1)},
    {"nome": "Pulizia studio",              "importo": 120.0,  "freq": "MENSILE",      "giorno": 28, "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "POS commissioni bancarie",    "importo": 25.0,   "freq": "MENSILE",      "giorno": 5,  "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Acqua distributore",          "importo": 45.0,   "freq": "MENSILE",      "giorno": 15, "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Telefono cellulare",          "importo": 14.99,  "freq": "MENSILE",      "giorno": 12, "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Musica Spotify Business",     "importo": 14.99,  "freq": "MENSILE",      "giorno": 1,  "cat": "Software",      "inizio": date(2025, 3, 1)},
    {"nome": "Manutenzione attrezzi",       "importo": 150.0,  "freq": "TRIMESTRALE",  "giorno": 10, "cat": "Attrezzatura",  "inizio": date(2025, 1, 1)},
    {"nome": "TARI (tassa rifiuti)",        "importo": 280.0,  "freq": "TRIMESTRALE",  "giorno": 20, "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Contributi INPS",             "importo": 950.0,  "freq": "TRIMESTRALE",  "giorno": 16, "cat": "Altro",         "inizio": date(2025, 2, 1)},
    {"nome": "Revisione estintori",         "importo": 180.0,  "freq": "SEMESTRALE",   "giorno": 1,  "cat": "Altro",         "inizio": date(2025, 1, 1)},
    {"nome": "Assicurazione professionale", "importo": 600.0,  "freq": "ANNUALE",      "giorno": 15, "cat": "Assicurazione", "inizio": date(2025, 1, 1)},
    {"nome": "Commercialista",              "importo": 1200.0, "freq": "ANNUALE",      "giorno": 15, "cat": "Commercialista","inizio": date(2025, 4, 1)},
]

VARIABLE_BUSINESS = [
    ("Elastici fitness",            "Attrezzatura",  30,   80),
    ("Tappetini nuovi",            "Attrezzatura",  40,  120),
    ("Pesi/manubri ricambio",      "Attrezzatura", 100,  300),
    ("Volantini pubblicitari",     "Marketing",     25,   60),
    ("Facebook/Instagram Ads",     "Marketing",     30,  100),
    ("Biglietti da visita",        "Marketing",     20,   45),
    ("Corso aggiornamento CONI",   "Formazione",   150,  400),
    ("Workshop nutrizione",        "Formazione",   100,  250),
    ("Disinfettante/igienizzante", "Altro",         15,   40),
    ("Carta stampante",            "Altro",         10,   25),
    ("Toner stampante",            "Altro",         30,   50),
    ("Riparazione attrezzo",       "Attrezzatura",  50,  200),
]

PERSONAL_EXPENSES = [
    ("Spesa alimentare",  "Personale",  25,  65,  8, 12),
    ("Benzina",           "Trasporto",  40,  60,  2,  3),
    ("Pranzo fuori",      "Personale",  12,  25,  3,  5),
    ("Cena fuori",        "Personale",  25,  45,  1,  3),
    ("Aperitivo",         "Personale",   8,  18,  2,  4),
    ("Cinema/svago",      "Personale",  10,  25,  1,  2),
    ("Abbigliamento",     "Personale",  25, 100,  0,  1),
    ("Farmacia",          "Personale",   8,  35,  0,  2),
    ("Amazon/acquisti",   "Personale",  15,  80,  1,  3),
]


# ═══════════════════════════════════════════════════════════════
# SECTION 4: Helpers
# ═══════════════════════════════════════════════════════════════

def _is_open(d: date) -> bool:
    """Studio aperto? False per domeniche e chiusure programmate."""
    if d.weekday() == 6:
        return False
    for start, end in CLOSED:
        if start <= d <= end:
            return False
    return True


def _slots_for(d: date) -> list[int]:
    """Ore disponibili per un dato giorno."""
    if not _is_open(d):
        return []
    if d.weekday() == 5:
        return SATURDAY[:]
    return MORNING + AFTERNOON


class SlotGrid:
    """Griglia slot orari per prevenire sovrapposizioni eventi."""

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
    """Clampa il giorno al massimo del mese."""
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d, last))


def _make_dt(d: date, hour: int = 0) -> datetime:
    """date + hour → datetime UTC."""
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
    """Genera (anno, mese) da start a end inclusi."""
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def _get_occurrences(freq: str, giorno: int, data_inizio: date, anno: int, mese: int):
    """
    Replica la logica dell'API per calcolare le occorrenze di una spesa
    ricorrente in un dato mese. Returns: list[(date, mese_anno_key)].
    """
    days_in = calendar.monthrange(anno, mese)[1]
    last_day = date(anno, mese, days_in)

    if data_inizio > last_day:
        return []

    if freq == "MENSILE":
        g = min(giorno, days_in)
        return [(_safe_date(anno, mese, g), f"{anno:04d}-{mese:02d}")]

    if freq == "SETTIMANALE":
        base = min(giorno, 7)
        result = []
        day, week = base, 1
        while day <= days_in:
            result.append((_safe_date(anno, mese, day), f"{anno:04d}-{mese:02d}-W{week}"))
            day += 7
            week += 1
        return result

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


# ═══════════════════════════════════════════════════════════════
# SECTION 5: Generazione orchestrata
# ═══════════════════════════════════════════════════════════════

def seed_realistic(engine):
    """Popola il database con 1 anno di dati realistici."""

    movements: list[CashMovement] = []
    all_events: list[Event] = []
    all_rates: list[Rate] = []
    all_contracts: list[Contract] = []
    credit_pool: dict[int, int] = {}     # contract_id → crediti rimanenti
    credits_used: dict[int, int] = defaultdict(int)  # contract_id → crediti usati
    client_contracts: dict[int, list[Contract]] = defaultdict(list)

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

        # ── Step B: 50 Clienti ──
        clients: list[Client] = []
        for i, cd in enumerate(CLIENTS_DATA):
            c = Client(
                trainer_id=tid,
                nome=cd["nome"],
                cognome=cd["cognome"],
                telefono=cd.get("tel"),
                email=cd.get("email"),
                data_nascita=cd.get("nascita"),
                sesso=cd.get("sesso"),
                stato=cd.get("stato", "Attivo"),
                anamnesi_json=ANAMNESI.get(i),
            )
            session.add(c)
            clients.append(c)
        session.flush()

        active_clients = [c for c in clients if c.stato == "Attivo"]
        n_active = len([c for c in clients if c.stato == "Attivo"])
        n_inactive = len([c for c in clients if c.stato == "Inattivo"])
        print(f"   Clienti: {len(clients)} creati ({n_active} attivi, {n_inactive} inattivi, {len(clients) - n_active - n_inactive} nuovi)")

        # Clienti che possono avere contratti (attivi + inattivi, escludi ultimi 5 = nuovi)
        contractable = clients[:45]

        # ── Step C: Spese Ricorrenti ──
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
        print(f"   Spese ricorrenti: {len(rec_expenses)} create")

        # ── Step D: Contratti + Rate + Pagamenti ──
        # Iteriamo mese per mese da marzo 2025 a febbraio 2026
        available_clients = list(contractable)
        random.shuffle(available_clients)
        client_idx = 0

        for y, m in _months_range(YEAR_START, YEAR_END):
            n_contracts = CONTRACTS_PER_MONTH.get(m, 3)

            for _ in range(n_contracts):
                # Scegli cliente: preferisci chi non ha contratti attivi
                client = None
                for _ in range(len(contractable)):
                    candidate = contractable[client_idx % len(contractable)]
                    client_idx += 1
                    # OK se non ha contratti o se il suo ultimo e' chiuso/scaduto
                    existing = client_contracts.get(candidate.id, [])
                    if not existing or existing[-1].chiuso or (
                        existing[-1].data_scadenza and existing[-1].data_scadenza < _safe_date(y, m, 1)
                    ):
                        client = candidate
                        break
                if not client:
                    client = random.choice(contractable)

                # Pacchetto
                pkg = random.choices(PACKAGES, PKG_WEIGHTS)[0]
                prezzo = _rand_price(pkg)
                sale_date = _rand_date_in_month(y, m)
                start_date = sale_date + timedelta(days=random.randint(0, 5))
                end_date = start_date + timedelta(days=pkg["mesi"] * 30)

                # Acconto: 0% (20%), 10-30% (60%), 100% (20%)
                acconto_choice = random.choices(["zero", "partial", "full"], [20, 60, 20])[0]
                if acconto_choice == "zero":
                    acconto = 0.0
                elif acconto_choice == "full":
                    acconto = prezzo
                else:
                    acconto = round(prezzo * random.uniform(0.1, 0.3) / 10) * 10

                # Scenario basato sulla timeline
                if end_date < TODAY - timedelta(days=30):
                    scenario = random.choices(["completed", "expired"], [80, 20])[0]
                elif start_date > TODAY - timedelta(days=14):
                    scenario = random.choices(["new", "acconto_only"], [70, 30])[0]
                else:
                    scenario = "active"

                contract = Contract(
                    trainer_id=tid,
                    id_cliente=client.id,
                    tipo_pacchetto=pkg["nome"],
                    crediti_totali=pkg["crediti"] if pkg["crediti"] > 0 else None,
                    prezzo_totale=prezzo,
                    acconto=acconto,
                    data_vendita=sale_date,
                    data_inizio=start_date,
                    data_scadenza=end_date,
                    totale_versato=acconto,
                    stato_pagamento="PENDENTE",
                    chiuso=False,
                )
                session.add(contract)
                session.flush()
                all_contracts.append(contract)
                client_contracts[client.id].append(contract)

                if pkg["crediti"] > 0:
                    credit_pool[contract.id] = pkg["crediti"]

                # Acconto → CashMovement
                if acconto > 0:
                    movements.append(_make_movement(
                        tid, "ENTRATA", acconto, "ACCONTO_CONTRATTO", sale_date,
                        id_cliente=client.id, id_contratto=contract.id,
                        note=f"Acconto {pkg['nome']} - {client.nome} {client.cognome}",
                    ))
                    if acconto >= prezzo - 0.01:
                        contract.stato_pagamento = "SALDATO"
                    else:
                        contract.stato_pagamento = "PARZIALE" if acconto > 0 else "PENDENTE"

                # Rate (skip se acconto_only o pagato interamente)
                if scenario == "acconto_only" or acconto >= prezzo - 0.01:
                    # Se saldato completamente e crediti 0, chiudi
                    if acconto >= prezzo - 0.01 and not pkg["crediti"]:
                        contract.chiuso = True
                    continue

                residuo = prezzo - acconto
                n_rate = max(2, min(8, int(residuo / 100)))
                base_amt = round(residuo / n_rate, 2)
                rate_amounts = [base_amt] * n_rate
                rate_amounts[-1] = round(residuo - base_amt * (n_rate - 1), 2)

                totale_saldato = acconto
                for i, amt in enumerate(rate_amounts):
                    rata_date = start_date + timedelta(days=30 * (i + 1))

                    if scenario == "completed":
                        stato_rata, saldato = "SALDATA", amt
                    elif scenario == "expired":
                        # Prime meta' saldate, resto pendente (arretrato)
                        if i < n_rate // 2:
                            stato_rata, saldato = "SALDATA", amt
                        else:
                            stato_rata, saldato = "PENDENTE", 0.0
                    elif scenario == "active":
                        if rata_date < TODAY - timedelta(days=15):
                            # Passata: 75% saldata, 15% parziale, 10% arretrata
                            roll = random.random()
                            if roll < 0.75:
                                stato_rata, saldato = "SALDATA", amt
                            elif roll < 0.90:
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
                        descrizione=f"Rata {i + 1}/{n_rate}",
                    )
                    session.add(rate)
                    session.flush()
                    all_rates.append(rate)

                    if saldato > 0:
                        totale_saldato += saldato
                        movements.append(_make_movement(
                            tid, "ENTRATA", saldato, "PAGAMENTO_RATA",
                            rata_date if rata_date < TODAY else TODAY,
                            id_cliente=client.id, id_contratto=contract.id,
                            id_rata=rate.id,
                            note=f"Rata {i + 1}/{n_rate} - {client.nome} {client.cognome}",
                        ))

                # Aggiorna stato finanziario contratto
                contract.totale_versato = round(totale_saldato, 2)
                if contract.totale_versato >= prezzo - 0.01:
                    contract.stato_pagamento = "SALDATO"
                elif contract.totale_versato > 0:
                    contract.stato_pagamento = "PARZIALE"
                else:
                    contract.stato_pagamento = "PENDENTE"

        session.flush()
        n_saldate = sum(1 for r in all_rates if r.stato == "SALDATA")
        n_parziali = sum(1 for r in all_rates if r.stato == "PARZIALE")
        n_pendenti = sum(1 for r in all_rates if r.stato == "PENDENTE")
        print(f"   Contratti: {len(all_contracts)} creati")
        print(f"   Rate: {len(all_rates)} create ({n_saldate} SALDATE, {n_parziali} PARZIALI, {n_pendenti} PENDENTI)")

        # ── Step E: Eventi (day-by-day) ──
        grid = SlotGrid()
        # Build lookup: contract → client
        contract_client = {c.id: c.id_cliente for c in all_contracts}

        # Contratti PT attivi con crediti
        def _eligible_contracts(event_date: date) -> list[Contract]:
            return [
                c for c in all_contracts
                if c.crediti_totali and c.crediti_totali > 0
                and credit_pool.get(c.id, 0) > 0
                and not c.chiuso
                and c.data_inizio and c.data_inizio <= event_date
                and c.data_scadenza and event_date <= c.data_scadenza
            ]

        ghost_count = 0  # Alcuni eventi passati restano "Programmato" (ghost)
        current = YEAR_START

        while current <= YEAR_END:
            if not _is_open(current):
                current += timedelta(days=1)
                continue

            slots = _slots_for(current)
            weight = SEASONAL.get(current.month, 1.0)
            base_n = 7 if current.weekday() < 5 else 4
            target = max(2, int(base_n * weight))

            shuffled = slots[:]
            random.shuffle(shuffled)

            # PT events
            pt_target = int(target * 0.7)
            for _ in range(pt_target):
                eligible = _eligible_contracts(current)
                if not eligible:
                    break
                # Preferisci contratti con piu' crediti residui
                weights = [credit_pool[c.id] for c in eligible]
                contract = random.choices(eligible, weights)[0]
                hour = grid.find_free(current, shuffled)
                if hour is None:
                    break
                grid.book(current, hour)

                # Stato
                if current < TODAY - timedelta(days=3):
                    if ghost_count < 12 and random.random() < 0.015:
                        stato = "Programmato"
                        ghost_count += 1
                    else:
                        stato = random.choices(
                            ["Completato", "Cancellato", "Rinviato"],
                            [85, 10, 5],
                        )[0]
                elif current <= TODAY:
                    stato = random.choices(["Completato", "Programmato"], [60, 40])[0]
                else:
                    stato = "Programmato"

                # Crediti
                if stato != "Cancellato":
                    credits_used[contract.id] += 1
                    credit_pool[contract.id] -= 1

                cid = contract_client[contract.id]
                cl = next(c for c in clients if c.id == cid)

                all_events.append(Event(
                    trainer_id=tid,
                    categoria="PT",
                    titolo=f"PT {cl.nome} {cl.cognome}",
                    id_cliente=cid,
                    id_contratto=contract.id,
                    data_inizio=_make_dt(current, hour),
                    data_fine=_make_dt(current, hour + 1),
                    stato=stato,
                ))

            # CORSO (lun/mer/ven pomeriggio)
            if current.weekday() in (0, 2, 4):
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

            # COLLOQUIO (probabilita' ~30% al giorno)
            if random.random() < 0.3:
                h = grid.find_free(current, [9, 10, 15, 16])
                if h:
                    grid.book(current, h)
                    cl = random.choice(active_clients)
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

        # Insert events
        for e in all_events:
            session.add(e)
        session.flush()

        st_comp = sum(1 for e in all_events if e.stato == "Completato")
        st_canc = sum(1 for e in all_events if e.stato == "Cancellato")
        st_rinv = sum(1 for e in all_events if e.stato == "Rinviato")
        st_prog = sum(1 for e in all_events if e.stato == "Programmato")
        print(f"   Agenda: {len(all_events)} eventi ({st_comp} Completato, {st_canc} Cancellato, {st_rinv} Rinviato, {st_prog} Programmato)")
        print(f"   Ghost events (passati Programmato): {ghost_count}")

        # ── Step F: Conferme spese ricorrenti ──
        n_rec_mov = 0
        for y, m in _months_range(YEAR_START, date(2026, 1, 31)):
            for exp in rec_expenses:
                occs = _get_occurrences(exp.frequenza, exp.giorno_scadenza, exp.data_inizio, y, m)
                for data_eff, key in occs:
                    movements.append(_make_movement(
                        tid, "USCITA", exp.importo, exp.categoria or "Altro",
                        data_eff, id_spesa=exp.id, mese_anno=key,
                        note=f"{exp.nome}", operatore="CONFERMA_UTENTE",
                    ))
                    n_rec_mov += 1

        # Febbraio 2026: parziale (solo fino a oggi)
        for exp in rec_expenses:
            occs = _get_occurrences(exp.frequenza, exp.giorno_scadenza, exp.data_inizio, 2026, 2)
            for data_eff, key in occs:
                if data_eff <= TODAY:
                    movements.append(_make_movement(
                        tid, "USCITA", exp.importo, exp.categoria or "Altro",
                        data_eff, id_spesa=exp.id, mese_anno=key,
                        note=f"{exp.nome}", operatore="CONFERMA_UTENTE",
                    ))
                    n_rec_mov += 1

        # ── Step G: Spese variabili business ──
        n_var_mov = 0
        for y, m in _months_range(YEAR_START, TODAY):
            n = random.randint(2, 4)
            for _ in range(n):
                item = random.choice(VARIABLE_BUSINESS)
                nome, cat, lo, hi = item
                importo = round(random.uniform(lo, hi), 2)
                day = random.randint(3, 25)
                movements.append(_make_movement(
                    tid, "USCITA", importo, cat, _safe_date(y, m, day),
                    note=nome, operatore="MANUALE",
                ))
                n_var_mov += 1

        # ── Step H: Spese personali ──
        n_pers_mov = 0
        for y, m in _months_range(YEAR_START, TODAY):
            for nome, cat, lo, hi, freq_min, freq_max in PERSONAL_EXPENSES:
                n = random.randint(freq_min, freq_max)
                for _ in range(n):
                    day = random.randint(1, 28)
                    importo = round(random.uniform(lo, hi), 2)
                    metodo = "CONTANTI" if cat == "Personale" and random.random() < 0.4 else _rand_method()
                    movements.append(_make_movement(
                        tid, "USCITA", importo, cat, _safe_date(y, m, day),
                        note=nome, metodo=metodo, operatore="MANUALE",
                    ))
                    n_pers_mov += 1

        # ── Step I: Integrita' + Commit ──

        # 1. Aggiorna chiuso flag
        for contract in all_contracts:
            if contract.crediti_totali and contract.crediti_totali > 0:
                used = credits_used.get(contract.id, 0)
                contract.chiuso = (
                    contract.stato_pagamento == "SALDATO"
                    and used >= contract.crediti_totali
                )
            elif contract.stato_pagamento == "SALDATO":
                contract.chiuso = True

        # 2. Validazione integrita' finanziaria
        for contract in all_contracts:
            rate_sum = sum(
                r.importo_saldato for r in all_rates
                if r.id_contratto == contract.id and r.importo_saldato > 0
            )
            expected = round(contract.acconto + rate_sum, 2)
            if abs(contract.totale_versato - expected) > 0.02:
                print(f"   ⚠ Contract {contract.id}: totale_versato={contract.totale_versato}, expected={expected}")
                contract.totale_versato = expected

        # 3. Insert all movements
        for m in movements:
            session.add(m)
        session.flush()

        # 4. COMMIT atomico
        session.commit()

        # ── Summary ──
        tot_entrate = sum(m.importo for m in movements if m.tipo == "ENTRATA")
        tot_uscite_fisse = sum(m.importo for m in movements if m.tipo == "USCITA" and m.id_spesa_ricorrente)
        tot_uscite_var = sum(m.importo for m in movements if m.tipo == "USCITA" and not m.id_spesa_ricorrente and m.operatore == "MANUALE" and m.categoria not in ("Personale", "Trasporto"))
        tot_uscite_pers = sum(m.importo for m in movements if m.tipo == "USCITA" and m.categoria in ("Personale", "Trasporto"))

        print(f"\n   Movimenti: {len(movements)} CashMovement creati")
        print(f"     - {sum(1 for m in movements if m.tipo == 'ENTRATA')} ENTRATA (acconti + rate)")
        print(f"     - {n_rec_mov} USCITA spese fisse (confermate)")
        print(f"     - {n_var_mov} USCITA variabili business")
        print(f"     - {n_pers_mov} USCITA personali")

        print(f"\n   Riepilogo contabile annuo:")
        print(f"     Entrate totali:     {tot_entrate:>10,.2f} EUR")
        print(f"     Uscite fisse:       {tot_uscite_fisse:>10,.2f} EUR")
        print(f"     Uscite var. biz:    {tot_uscite_var:>10,.2f} EUR")
        print(f"     Uscite personali:   {tot_uscite_pers:>10,.2f} EUR")
        print(f"     {'-' * 34}")
        margine = tot_entrate - tot_uscite_fisse - tot_uscite_var - tot_uscite_pers
        print(f"     Margine netto:      {margine:>10,.2f} EUR")

        n_chiusi = sum(1 for c in all_contracts if c.chiuso)
        print(f"\n   Contratti chiusi: {n_chiusi}/{len(all_contracts)}")

    print("\n   COMMIT OK — database realistico pronto!")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("FitManager — Seed Realistico (1 Anno, 50 Clienti)")
    print("=" * 60)
    print()

    # Chiudi l'engine globale di api.database PRIMA di eliminare il file DB.
    # L'import dei modelli api/models/* importa transitivamente api/database.py
    # che crea un engine module-level → connessione aperta → file locked su Windows.
    from api.database import engine as api_engine
    api_engine.dispose()

    print("[1/2] Reset database...")
    engine = reset_database()
    print()

    print("[2/2] Seed dati realistici...")
    seed_realistic(engine)
    print()

    print("=" * 60)
    print("Database pronto! Avvia API + frontend per verificare.")
    print("Login: chiarabassani96@gmail.com / Fitness2026!")
    print("=" * 60)
