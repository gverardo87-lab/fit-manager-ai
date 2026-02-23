#!/usr/bin/env python3
"""
Reset & Seed — Ricrea il database da zero con dati di test realistici.

COSA FA:
1. Elimina il DB esistente (dopo backup automatico)
2. Ricrea tutte le tabelle via SQLModel
3. Stampa la versione Alembic (cosi' le migrazioni sanno che e' aggiornato)
4. Popola con dati di test coerenti e contabilmente corretti

IMPORTANTE: Ferma il server API prima di eseguire!
Esegui dalla root del progetto:
    python -m tools.admin_scripts.reset_and_seed

PERCHE' E' FATTO COSI':
- Usa direttamente SQLModel + Session (stesso ORM dell'API)
- NON usa gli endpoint HTTP (non serve il server avviato)
- Ogni inserimento e' atomico: se qualcosa fallisce, niente dati sporchi
- I dati sono contabilmente coerenti: se una rata e' SALDATA,
  esiste il CashMovement corrispondente e il contratto ha totale_versato aggiornato
"""

import os
import sys
import shutil
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

# ── Setup path (per import da root progetto) ──
# Questo trucco serve perche' Python non sa che siamo dentro un progetto.
# Aggiungiamo la root del progetto al sys.path cosi' "from api.xxx" funziona.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# ── Imports progetto (DOPO il sys.path setup) ──
from sqlmodel import SQLModel, Session, create_engine, text
from api.config import DATABASE_URL, DATA_DIR

# Importa TUTTI i modelli — necessario perche' SQLModel.metadata.create_all()
# crea le tabelle SOLO per i modelli che sono stati importati in memoria.
# Se dimentichi un import, quella tabella non viene creata.
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.rate import Rate
from api.models.event import Event
from api.models.movement import CashMovement
from api.models.recurring_expense import RecurringExpense

# Per l'hash della password (bcrypt)
from api.auth.service import hash_password

# ═══════════════════════════════════════════════════════════════
# STEP 1: Backup + Reset del database
# ═══════════════════════════════════════════════════════════════

def reset_database():
    """
    Elimina il DB e lo ricrea vuoto con tutte le tabelle.

    Perche' non usiamo Alembic per creare da zero?
    - Alembic e' fatto per MODIFICARE uno schema esistente (ALTER TABLE)
    - SQLModel.metadata.create_all() crea lo schema COMPLETO in un colpo
    - Poi stampiamo la versione Alembic cosi' lui sa che e' gia' aggiornato

    Se non stampassimo la versione, la prossima volta che esegui
    `alembic upgrade head`, proverebbe ad applicare migrazioni
    su tabelle che hanno gia' le colonne giuste → errore.
    """
    db_path = DATA_DIR / "crm.db"

    # Backup automatico (se il DB esiste)
    if db_path.exists():
        backup_name = f"crm_pre_seed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = DATA_DIR / backup_name
        shutil.copy2(db_path, backup_path)
        print(f"   Backup salvato: {backup_name}")

        # Elimina il DB originale
        os.remove(db_path)
        print(f"   Database eliminato: {db_path.name}")
    else:
        print("   Nessun database esistente da eliminare")

    # Crea engine NUOVO (punta al file che non esiste ancora → SQLite lo crea)
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Crea TUTTE le tabelle definite nei modelli
    # Questo e' equivalente a: CREATE TABLE IF NOT EXISTS per ogni modello
    SQLModel.metadata.create_all(engine)
    print(f"   Schema creato: {len(SQLModel.metadata.tables)} tabelle")

    # Stampa la versione Alembic — CRITICO!
    # Senza questo, `alembic upgrade head` proverebbe a riapplicare
    # tutte le migrazioni su un DB che ha gia' lo schema finale.
    #
    # La versione "be919715d0b5" e' l'ultima migrazione (data_inizio).
    # Se aggiungi nuove migrazioni in futuro, aggiorna questa stringa.
    LATEST_ALEMBIC_VERSION = "be919715d0b5"

    with Session(engine) as session:
        # Crea la tabella alembic_version (Alembic la crea normalmente lui)
        session.exec(text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
        session.exec(text(
            f"INSERT INTO alembic_version (version_num) VALUES ('{LATEST_ALEMBIC_VERSION}')"
        ))
        session.commit()
    print(f"   Alembic version stampata: {LATEST_ALEMBIC_VERSION}")

    # Crea l'indice UNIQUE per le spese ricorrenti (normalmente creato da migration)
    # Questo indice impedisce che la stessa spesa venga confermata due volte
    # nello stesso mese. Il filtro WHERE esclude i record soft-deleted.
    with Session(engine) as session:
        session.exec(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_recurring_per_month
            ON movimenti_cassa (trainer_id, id_spesa_ricorrente, mese_anno)
            WHERE id_spesa_ricorrente IS NOT NULL AND deleted_at IS NULL
        """))
        session.commit()
    print("   Indice UNIQUE spese ricorrenti creato")

    return engine


# ═══════════════════════════════════════════════════════════════
# STEP 2: Seed — Dati di test
# ═══════════════════════════════════════════════════════════════

def seed_database(engine):
    """
    Popola il database con dati realistici per testare ogni feature.

    REGOLA D'ORO della coerenza contabile:
    Se una rata e' SALDATA con importo_saldato = X, DEVE esistere
    un CashMovement ENTRATA con importo = X e id_rata = rata.id.
    E il contratto deve avere totale_versato incrementato di X.

    Questo e' il motivo per cui non puoi semplicemente "inventare" numeri:
    ogni dato dipende dagli altri.
    """
    with Session(engine) as session:
        # ── Trainer (il proprietario di tutti i dati) ──
        # In produzione: 1 trainer = 1 professionista.
        # La password viene hashata con bcrypt (salt random ogni volta).
        trainer = Trainer(
            email="chiarabassani96@gmail.com",
            nome="Chiara",
            cognome="Bassani",
            hashed_password=hash_password("Fitness2026!"),
            is_active=True,
        )
        session.add(trainer)
        session.flush()  # flush() assegna l'ID senza committare
        # Perche' flush e non commit? Perche' vogliamo che TUTTO
        # sia in una transazione unica. Se qualcosa fallisce dopo,
        # niente viene salvato (atomicita').
        tid = trainer.id
        print(f"   Trainer: {trainer.nome} {trainer.cognome} (id={tid})")

        # ── Clienti ──
        # Mix realistico: nomi italiani, eta' diverse, alcuni con dati completi,
        # altri con dati parziali (come nella vita reale).
        clients_data = [
            {"nome": "Marco",    "cognome": "Rossi",    "telefono": "333-1111111", "email": "marco.rossi@email.it",    "data_nascita": date(1990, 3, 15), "sesso": "Uomo"},
            {"nome": "Laura",    "cognome": "Bianchi",  "telefono": "333-2222222", "email": "laura.bianchi@email.it",  "data_nascita": date(1985, 7, 22), "sesso": "Donna"},
            {"nome": "Andrea",   "cognome": "Verdi",    "telefono": "333-3333333", "email": "andrea.verdi@email.it",   "data_nascita": date(1992, 11, 8), "sesso": "Uomo"},
            {"nome": "Sofia",    "cognome": "Marino",   "telefono": "333-4444444", "email": None,                      "data_nascita": date(1988, 1, 30), "sesso": "Donna"},
            {"nome": "Luca",     "cognome": "Romano",   "telefono": "333-5555555", "email": "luca.romano@email.it",    "data_nascita": None,              "sesso": "Uomo"},
            {"nome": "Giulia",   "cognome": "Colombo",  "telefono": None,          "email": "giulia.c@email.it",       "data_nascita": date(1995, 5, 12), "sesso": "Donna"},
            {"nome": "Davide",   "cognome": "Ricci",    "telefono": "333-7777777", "email": None,                      "data_nascita": date(1982, 9, 3),  "sesso": "Uomo"},
            {"nome": "Valentina","cognome": "Gallo",    "telefono": "333-8888888", "email": "vale.gallo@email.it",     "data_nascita": date(1998, 12, 25),"sesso": "Donna"},
            # Cliente inattivo (ha smesso di allenarsi)
            {"nome": "Roberto",  "cognome": "Conti",    "telefono": "333-9999999", "email": None,                      "data_nascita": date(1975, 4, 18), "sesso": "Uomo",  "stato": "Inattivo"},
            # Cliente appena iscritto (nessun contratto ancora)
            {"nome": "Elisa",    "cognome": "Ferrari",  "telefono": "333-0000000", "email": "elisa.f@email.it",        "data_nascita": date(2000, 6, 1),  "sesso": "Donna"},
        ]

        clients = []
        for cd in clients_data:
            c = Client(trainer_id=tid, **cd)
            session.add(c)
            clients.append(c)
        session.flush()
        print(f"   Clienti: {len(clients)} creati")

        # ── Contratti + Rate + Movimenti ──
        # Ogni scenario testa una situazione diversa.
        # La lista movement_buffer accumula i CashMovement da creare.
        movement_buffer: list[CashMovement] = []
        all_rates: list[Rate] = []

        # Contatore per i movimenti (serve per le note)
        def make_movement(
            tipo: str, importo: float, categoria: str,
            data_eff: date, id_cliente: int | None = None,
            id_contratto: int | None = None, id_rata: int | None = None,
            note: str | None = None, metodo: str = "POS",
        ) -> CashMovement:
            """Helper per creare un CashMovement coerente."""
            return CashMovement(
                trainer_id=tid,
                tipo=tipo,
                importo=importo,
                categoria=categoria,
                data_effettiva=data_eff,
                data_movimento=datetime.combine(data_eff, datetime.min.time()).replace(tzinfo=timezone.utc),
                id_cliente=id_cliente,
                id_contratto=id_contratto,
                id_rata=id_rata,
                metodo=metodo,
                note=note,
                operatore="API",
            )

        # ────────────────────────────────────────
        # Contratto 1: Marco — SALDATO (pagato tutto, crediti finiti, chiuso)
        # Questo e' il caso "perfetto": tutto pagato, tutte le sessioni fatte.
        # ────────────────────────────────────────
        c1 = Contract(
            trainer_id=tid, id_cliente=clients[0].id,
            tipo_pacchetto="Gold 10", crediti_totali=10, crediti_usati=0,
            prezzo_totale=500.0, acconto=100.0, totale_versato=500.0,
            data_vendita=date(2025, 10, 1), data_inizio=date(2025, 10, 1),
            data_scadenza=date(2026, 4, 1),
            stato_pagamento="SALDATO", chiuso=True,
        )
        session.add(c1)
        session.flush()

        # Acconto → CashMovement
        movement_buffer.append(make_movement(
            "ENTRATA", 100.0, "ACCONTO", date(2025, 10, 1),
            id_cliente=clients[0].id, id_contratto=c1.id,
            note=f"Acconto {clients[0].nome} {clients[0].cognome}",
            metodo="CONTANTI",
        ))

        # 4 rate da 100€ ciascuna (tutte SALDATE)
        for i, dt in enumerate([
            date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)
        ]):
            r = Rate(
                id_contratto=c1.id, data_scadenza=dt,
                importo_previsto=100.0, importo_saldato=100.0,
                stato="SALDATA", descrizione=f"Rata {i+1}/4",
            )
            session.add(r)
            session.flush()
            all_rates.append(r)
            movement_buffer.append(make_movement(
                "ENTRATA", 100.0, "RATA_CONTRATTO", dt,
                id_cliente=clients[0].id, id_contratto=c1.id, id_rata=r.id,
                note=f"Rata {i+1}/4 — {clients[0].nome} {clients[0].cognome}",
            ))
        print(f"   Contratto 1 (Marco): SALDATO + CHIUSO, 4 rate saldate")

        # ────────────────────────────────────────
        # Contratto 2: Laura — PARZIALE (alcune rate pagate, alcune scadute)
        # Scenario comune: il cliente paga in ritardo.
        # ────────────────────────────────────────
        c2 = Contract(
            trainer_id=tid, id_cliente=clients[1].id,
            tipo_pacchetto="Silver 8", crediti_totali=8, crediti_usati=0,
            prezzo_totale=400.0, acconto=0.0, totale_versato=200.0,
            data_vendita=date(2025, 12, 15), data_inizio=date(2026, 1, 1),
            data_scadenza=date(2026, 6, 30),
            stato_pagamento="PARZIALE",
        )
        session.add(c2)
        session.flush()

        # 4 rate: 2 saldate, 1 scaduta (PENDENTE con data passata), 1 futura
        rate_2_data = [
            (date(2026, 1, 15), 100.0, "SALDATA", 100.0),
            (date(2026, 2, 15), 100.0, "SALDATA", 100.0),
            (date(2026, 3, 15), 100.0, "PENDENTE", 0.0),    # SCADUTA!
            (date(2026, 4, 15), 100.0, "PENDENTE", 0.0),    # futura
        ]
        for i, (dt, imp, stato, saldato) in enumerate(rate_2_data):
            r = Rate(
                id_contratto=c2.id, data_scadenza=dt,
                importo_previsto=imp, importo_saldato=saldato,
                stato=stato, descrizione=f"Rata {i+1}/4",
            )
            session.add(r)
            session.flush()
            all_rates.append(r)
            if stato == "SALDATA":
                movement_buffer.append(make_movement(
                    "ENTRATA", saldato, "RATA_CONTRATTO", dt,
                    id_cliente=clients[1].id, id_contratto=c2.id, id_rata=r.id,
                    note=f"Rata {i+1}/4 — {clients[1].nome} {clients[1].cognome}",
                ))
        print(f"   Contratto 2 (Laura): PARZIALE, 2 rate scadute")

        # ────────────────────────────────────────
        # Contratto 3: Andrea — PENDENTE (appena creato, nessun pagamento)
        # Scenario: contratto nuovo, prima rata a fine mese.
        # ────────────────────────────────────────
        c3 = Contract(
            trainer_id=tid, id_cliente=clients[2].id,
            tipo_pacchetto="Bronze 5", crediti_totali=5, crediti_usati=0,
            prezzo_totale=250.0, acconto=50.0, totale_versato=50.0,
            data_vendita=date(2026, 2, 20), data_inizio=date(2026, 3, 1),
            data_scadenza=date(2026, 8, 31),
            stato_pagamento="PENDENTE",
        )
        session.add(c3)
        session.flush()

        # Acconto
        movement_buffer.append(make_movement(
            "ENTRATA", 50.0, "ACCONTO", date(2026, 2, 20),
            id_cliente=clients[2].id, id_contratto=c3.id,
            note=f"Acconto {clients[2].nome} {clients[2].cognome}",
            metodo="BONIFICO",
        ))

        # 4 rate future (tutte PENDENTI)
        for i, dt in enumerate([
            date(2026, 3, 31), date(2026, 4, 30), date(2026, 5, 31), date(2026, 6, 30)
        ]):
            r = Rate(
                id_contratto=c3.id, data_scadenza=dt,
                importo_previsto=50.0, importo_saldato=0.0,
                stato="PENDENTE", descrizione=f"Rata {i+1}/4",
            )
            session.add(r)
            all_rates.append(r)
        session.flush()
        print(f"   Contratto 3 (Andrea): PENDENTE, 4 rate future")

        # ────────────────────────────────────────
        # Contratto 4: Sofia — PARZIALE con pagamento parziale su una rata
        # Scenario: la cliente ha pagato meta' di una rata (test pagamenti parziali).
        # ────────────────────────────────────────
        c4 = Contract(
            trainer_id=tid, id_cliente=clients[3].id,
            tipo_pacchetto="Platinum 20", crediti_totali=20, crediti_usati=0,
            prezzo_totale=900.0, acconto=100.0, totale_versato=350.0,
            data_vendita=date(2025, 11, 1), data_inizio=date(2025, 11, 15),
            data_scadenza=date(2026, 11, 15),
            stato_pagamento="PARZIALE",
        )
        session.add(c4)
        session.flush()

        # Acconto
        movement_buffer.append(make_movement(
            "ENTRATA", 100.0, "ACCONTO", date(2025, 11, 1),
            id_cliente=clients[3].id, id_contratto=c4.id,
            note=f"Acconto {clients[3].nome} {clients[3].cognome}",
        ))

        # Rata 1: SALDATA (200€)
        r4_1 = Rate(
            id_contratto=c4.id, data_scadenza=date(2025, 12, 15),
            importo_previsto=200.0, importo_saldato=200.0,
            stato="SALDATA", descrizione="Rata 1/4",
        )
        session.add(r4_1)
        session.flush()
        all_rates.append(r4_1)
        movement_buffer.append(make_movement(
            "ENTRATA", 200.0, "RATA_CONTRATTO", date(2025, 12, 15),
            id_cliente=clients[3].id, id_contratto=c4.id, id_rata=r4_1.id,
            note=f"Rata 1/4 — {clients[3].nome} {clients[3].cognome}",
        ))

        # Rata 2: PARZIALE (previsto 200, pagato 50 — mancano 150)
        r4_2 = Rate(
            id_contratto=c4.id, data_scadenza=date(2026, 1, 15),
            importo_previsto=200.0, importo_saldato=50.0,
            stato="PARZIALE", descrizione="Rata 2/4",
        )
        session.add(r4_2)
        session.flush()
        all_rates.append(r4_2)
        movement_buffer.append(make_movement(
            "ENTRATA", 50.0, "RATA_CONTRATTO", date(2026, 1, 15),
            id_cliente=clients[3].id, id_contratto=c4.id, id_rata=r4_2.id,
            note=f"Rata 2/4 (parziale) — {clients[3].nome} {clients[3].cognome}",
        ))

        # Rata 3 e 4: PENDENTI (future)
        for i, dt in enumerate([date(2026, 3, 15), date(2026, 5, 15)]):
            r = Rate(
                id_contratto=c4.id, data_scadenza=dt,
                importo_previsto=200.0, importo_saldato=0.0,
                stato="PENDENTE", descrizione=f"Rata {i+3}/4",
            )
            session.add(r)
            all_rates.append(r)
        session.flush()
        print(f"   Contratto 4 (Sofia): PARZIALE, 1 rata parziale (50/200)")

        # ────────────────────────────────────────
        # Contratto 5: Luca — scaduto da poco
        # Scenario: contratto scaduto ma non chiuso (ha ancora rate pendenti)
        # ────────────────────────────────────────
        c5 = Contract(
            trainer_id=tid, id_cliente=clients[4].id,
            tipo_pacchetto="Gold 10", crediti_totali=10, crediti_usati=0,
            prezzo_totale=500.0, acconto=0.0, totale_versato=200.0,
            data_vendita=date(2025, 8, 1), data_inizio=date(2025, 8, 1),
            data_scadenza=date(2026, 2, 1),  # SCADUTO!
            stato_pagamento="PARZIALE",
        )
        session.add(c5)
        session.flush()

        # 5 rate: 2 saldate (passato), 3 scadute (non pagate)
        for i in range(5):
            dt = date(2025, 9, 1) + timedelta(days=30 * i)
            is_paid = i < 2
            r = Rate(
                id_contratto=c5.id, data_scadenza=dt,
                importo_previsto=100.0,
                importo_saldato=100.0 if is_paid else 0.0,
                stato="SALDATA" if is_paid else "PENDENTE",
                descrizione=f"Rata {i+1}/5",
            )
            session.add(r)
            session.flush()
            all_rates.append(r)
            if is_paid:
                movement_buffer.append(make_movement(
                    "ENTRATA", 100.0, "RATA_CONTRATTO", dt,
                    id_cliente=clients[4].id, id_contratto=c5.id, id_rata=r.id,
                    note=f"Rata {i+1}/5 — {clients[4].nome} {clients[4].cognome}",
                ))
        print(f"   Contratto 5 (Luca): SCADUTO, 3 rate arretrate")

        # ────────────────────────────────────────
        # Contratto 6: Giulia — nuovissimo (solo acconto)
        # Scenario: contratto appena firmato, nessuna rata generata.
        # ────────────────────────────────────────
        c6 = Contract(
            trainer_id=tid, id_cliente=clients[5].id,
            tipo_pacchetto="Silver 8", crediti_totali=8, crediti_usati=0,
            prezzo_totale=380.0, acconto=80.0, totale_versato=80.0,
            data_vendita=date(2026, 2, 22), data_inizio=date(2026, 3, 1),
            data_scadenza=date(2026, 9, 30),
            stato_pagamento="PENDENTE",
        )
        session.add(c6)
        session.flush()

        movement_buffer.append(make_movement(
            "ENTRATA", 80.0, "ACCONTO", date(2026, 2, 22),
            id_cliente=clients[5].id, id_contratto=c6.id,
            note=f"Acconto {clients[5].nome} {clients[5].cognome}",
            metodo="CONTANTI",
        ))
        print(f"   Contratto 6 (Giulia): PENDENTE, solo acconto, zero rate")

        # ────────────────────────────────────────
        # Contratto 7: Davide — contratto chiuso con crediti esauriti
        # Scenario: tutto completato, perfetto per test auto-close.
        # ────────────────────────────────────────
        c7 = Contract(
            trainer_id=tid, id_cliente=clients[6].id,
            tipo_pacchetto="Bronze 5", crediti_totali=5, crediti_usati=0,
            prezzo_totale=200.0, acconto=200.0, totale_versato=200.0,
            data_vendita=date(2025, 6, 1), data_inizio=date(2025, 6, 1),
            data_scadenza=date(2025, 12, 31),
            stato_pagamento="SALDATO", chiuso=True,
        )
        session.add(c7)
        session.flush()

        movement_buffer.append(make_movement(
            "ENTRATA", 200.0, "ACCONTO", date(2025, 6, 1),
            id_cliente=clients[6].id, id_contratto=c7.id,
            note=f"Acconto (saldo) {clients[6].nome} {clients[6].cognome}",
            metodo="BONIFICO",
        ))
        print(f"   Contratto 7 (Davide): SALDATO + CHIUSO, pagato tutto con acconto")

        # Nessun contratto per Roberto (inattivo) e Elisa (appena iscritta)
        # — Valentina ha un contratto sotto

        # ────────────────────────────────────────
        # Contratto 8: Valentina — attivo con acconto e piano rate
        # ────────────────────────────────────────
        c8 = Contract(
            trainer_id=tid, id_cliente=clients[7].id,
            tipo_pacchetto="Gold 10", crediti_totali=10, crediti_usati=0,
            prezzo_totale=480.0, acconto=80.0, totale_versato=180.0,
            data_vendita=date(2026, 1, 10), data_inizio=date(2026, 1, 15),
            data_scadenza=date(2026, 7, 15),
            stato_pagamento="PARZIALE",
        )
        session.add(c8)
        session.flush()

        movement_buffer.append(make_movement(
            "ENTRATA", 80.0, "ACCONTO", date(2026, 1, 10),
            id_cliente=clients[7].id, id_contratto=c8.id,
            note=f"Acconto {clients[7].nome} {clients[7].cognome}",
            metodo="POS",
        ))

        # 4 rate da 100€: prima saldata, seconda in scadenza, altre future
        rate_8_data = [
            (date(2026, 2, 1),  100.0, "SALDATA",  100.0),
            (date(2026, 3, 1),  100.0, "PENDENTE",  0.0),  # in scadenza
            (date(2026, 4, 1),  100.0, "PENDENTE",  0.0),
            (date(2026, 5, 1),  100.0, "PENDENTE",  0.0),
        ]
        for i, (dt, imp, stato, saldato) in enumerate(rate_8_data):
            r = Rate(
                id_contratto=c8.id, data_scadenza=dt,
                importo_previsto=imp, importo_saldato=saldato,
                stato=stato, descrizione=f"Rata {i+1}/4",
            )
            session.add(r)
            session.flush()
            all_rates.append(r)
            if stato == "SALDATA":
                movement_buffer.append(make_movement(
                    "ENTRATA", saldato, "RATA_CONTRATTO", dt,
                    id_cliente=clients[7].id, id_contratto=c8.id, id_rata=r.id,
                    note=f"Rata {i+1}/4 — {clients[7].nome} {clients[7].cognome}",
                ))
        print(f"   Contratto 8 (Valentina): PARZIALE, 1 saldata + 3 future")

        # ── Inserisci tutti i CashMovement ──
        for m in movement_buffer:
            session.add(m)
        session.flush()
        print(f"   Movimenti: {len(movement_buffer)} CashMovement creati")

        # ── Spese Ricorrenti (con frequenze diverse) ──
        expenses_data = [
            {"nome": "Affitto Sala",          "importo": 800.0,  "frequenza": "MENSILE",      "giorno_scadenza": 5,  "categoria": "Affitto",      "data_inizio": date(2025, 1, 1)},
            {"nome": "Assicurazione RC",      "importo": 450.0,  "frequenza": "SEMESTRALE",   "giorno_scadenza": 1,  "categoria": "Assicurazione","data_inizio": date(2025, 1, 1)},
            {"nome": "Commercialista",        "importo": 1200.0, "frequenza": "ANNUALE",      "giorno_scadenza": 15, "categoria": "Commercialista","data_inizio": date(2025, 3, 1)},
            {"nome": "Software gestionale",   "importo": 29.90,  "frequenza": "MENSILE",      "giorno_scadenza": 1,  "categoria": "Software",     "data_inizio": date(2025, 6, 1)},
            {"nome": "Manutenzione attrezzi", "importo": 350.0,  "frequenza": "TRIMESTRALE",  "giorno_scadenza": 10, "categoria": "Attrezzatura", "data_inizio": date(2025, 1, 1)},
            {"nome": "Internet fibra",        "importo": 34.90,  "frequenza": "MENSILE",      "giorno_scadenza": 20, "categoria": "Utenze",       "data_inizio": date(2025, 1, 1)},
        ]
        for ed in expenses_data:
            session.add(RecurringExpense(trainer_id=tid, attiva=True, **ed))
        session.flush()
        print(f"   Spese ricorrenti: {len(expenses_data)} create (3 MENSILI, 1 TRIM, 1 SEM, 1 ANN)")

        # ── Movimenti manuali (uscite variabili) ──
        # Queste sono spese non ricorrenti, registrate manualmente dall'utente.
        manual_uscite = [
            (date(2026, 1, 5),   45.0,  "Elastici e fasce", "Attrezzatura"),
            (date(2026, 1, 18),  120.0, "Corso aggiornamento CONI", "Formazione"),
            (date(2026, 2, 3),   35.0,  "Toner stampante", "Altro"),
            (date(2026, 2, 12),  89.0,  "Volantini palestra", "Marketing"),
        ]
        for dt, imp, note, cat in manual_uscite:
            session.add(CashMovement(
                trainer_id=tid, tipo="USCITA", importo=imp,
                data_effettiva=dt,
                data_movimento=datetime.combine(dt, datetime.min.time()).replace(tzinfo=timezone.utc),
                categoria=cat, note=note, metodo="POS", operatore="API",
            ))
        session.flush()
        print(f"   Uscite manuali: {len(manual_uscite)} create")

        # ── Agenda (eventi PT + generici) ──
        # Creiamo sessioni PT per i contratti attivi e qualche evento generico.
        events_data = []

        # Sessioni PT per Marco (contratto 1, chiuso — tutti Completati)
        for i in range(5):
            dt = datetime(2025, 10, 15 + i * 3, 9, 0, tzinfo=timezone.utc)
            events_data.append(Event(
                trainer_id=tid, categoria="PT", titolo=f"PT Marco #{i+1}",
                id_cliente=clients[0].id, id_contratto=c1.id,
                data_inizio=dt, data_fine=dt + timedelta(hours=1),
                stato="Completato",
            ))

        # Sessioni PT per Laura (contratto 2 — mix Completato/Programmato)
        for i in range(4):
            dt = datetime(2026, 1, 10 + i * 7, 10, 0, tzinfo=timezone.utc)
            events_data.append(Event(
                trainer_id=tid, categoria="PT", titolo=f"PT Laura #{i+1}",
                id_cliente=clients[1].id, id_contratto=c2.id,
                data_inizio=dt, data_fine=dt + timedelta(hours=1),
                stato="Completato" if i < 3 else "Programmato",
            ))

        # Sessioni PT per Sofia (contratto 4 — alcune completate)
        for i in range(6):
            dt = datetime(2025, 12, 1 + i * 5, 14, 0, tzinfo=timezone.utc)
            events_data.append(Event(
                trainer_id=tid, categoria="PT", titolo=f"PT Sofia #{i+1}",
                id_cliente=clients[3].id, id_contratto=c4.id,
                data_inizio=dt, data_fine=dt + timedelta(hours=1),
                stato="Completato" if i < 4 else "Programmato",
            ))

        # Sessioni PT per Valentina (contratto 8)
        for i in range(3):
            dt = datetime(2026, 2, 3 + i * 7, 11, 0, tzinfo=timezone.utc)
            events_data.append(Event(
                trainer_id=tid, categoria="PT", titolo=f"PT Valentina #{i+1}",
                id_cliente=clients[7].id, id_contratto=c8.id,
                data_inizio=dt, data_fine=dt + timedelta(hours=1),
                stato="Completato" if i < 2 else "Programmato",
            ))

        # Eventi futuri prossima settimana
        next_monday = date.today() + timedelta(days=(7 - date.today().weekday()))
        for i, (cat, titolo, ore) in enumerate([
            ("PT",    "PT Valentina", 9),
            ("PT",    "PT Laura", 10),
            ("CORSO", "Pilates Gruppo", 17),
            ("SALA",  "Apertura sala", 7),
            ("PT",    "PT Andrea (prova)", 15),
        ]):
            dt = datetime(next_monday.year, next_monday.month, next_monday.day + i % 5, ore, 0, tzinfo=timezone.utc)
            ev = Event(
                trainer_id=tid, categoria=cat, titolo=titolo,
                data_inizio=dt, data_fine=dt + timedelta(hours=1),
                stato="Programmato",
            )
            if cat == "PT" and i == 0:
                ev.id_cliente = clients[7].id
                ev.id_contratto = c8.id
            elif cat == "PT" and i == 1:
                ev.id_cliente = clients[1].id
                ev.id_contratto = c2.id
            elif cat == "PT" and i == 4:
                ev.id_cliente = clients[2].id
                ev.id_contratto = c3.id
            events_data.append(ev)

        for ev in events_data:
            session.add(ev)
        session.flush()
        print(f"   Agenda: {len(events_data)} eventi creati")

        # ── COMMIT ATOMICO ──
        # Tutto o niente. Se qualsiasi riga sopra avesse fallito,
        # session.commit() non verrebbe mai chiamato e il DB resterebbe vuoto.
        session.commit()
        print("\n   COMMIT OK — tutti i dati sono nel database")

        # ── Riepilogo contabile ──
        tot_entrate = sum(m.importo for m in movement_buffer)
        tot_uscite = sum(imp for _, imp, _, _ in manual_uscite)
        print(f"\n   Riepilogo contabile:")
        print(f"   Entrate (acconti + rate): {tot_entrate:,.2f} EUR")
        print(f"   Uscite manuali:           {tot_uscite:,.2f} EUR")
        print(f"   Rate totali:              {len(all_rates)}")
        print(f"   Rate saldate:             {sum(1 for r in all_rates if r.stato == 'SALDATA')}")
        print(f"   Rate pendenti:            {sum(1 for r in all_rates if r.stato == 'PENDENTE')}")
        print(f"   Rate parziali:            {sum(1 for r in all_rates if r.stato == 'PARZIALE')}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("FitManager — Reset & Seed Database")
    print("=" * 60)
    print()

    print("[1/2] Reset database...")
    engine = reset_database()
    print()

    print("[2/2] Seed dati di test...")
    seed_database(engine)
    print()

    print("=" * 60)
    print("FATTO! Il database e' pronto.")
    print()
    print("Credenziali login:")
    print("  Email:    chiarabassani96@gmail.com")
    print("  Password: Fitness2026!")
    print()
    print("Per avviare:")
    print("  uvicorn api.main:app --reload --port 8000")
    print("  cd frontend && npm run dev")
    print("=" * 60)
