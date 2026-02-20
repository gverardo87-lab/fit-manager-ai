# tools/admin_scripts/assign_legacy_clients.py
"""
Migrazione clienti legacy: assegna i clienti con trainer_id=NULL al primo trainer registrato.

Perche' serve:
    La tabella 'clienti' esisteva prima dell'introduzione della multi-tenancy.
    I 7 clienti storici hanno trainer_id=NULL, quindi l'API (che filtra per trainer_id)
    non li restituisce. Questo script li "adotta" assegnandoli al primo trainer.

Quando eseguirlo:
    1. DOPO aver registrato almeno un trainer via POST /api/auth/register
    2. Una sola volta (e' idempotente: se non ci sono orfani, non fa nulla)

Uso:
    python tools/admin_scripts/assign_legacy_clients.py
    python tools/admin_scripts/assign_legacy_clients.py --trainer-id 2   # assegna a trainer specifico
    python tools/admin_scripts/assign_legacy_clients.py --dry-run        # mostra cosa farebbe senza scrivere
"""

import argparse
import sys
from pathlib import Path

# Aggiungi root progetto al path per importare api/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, select, func
from api.database import engine
from api.models.trainer import Trainer
from api.models.client import Client


def get_orphan_clients(session: Session) -> list[Client]:
    """Trova tutti i clienti senza trainer_id (legacy data)."""
    return list(session.exec(
        select(Client).where(Client.trainer_id.is_(None))  # type: ignore[union-attr]
    ).all())


def get_target_trainer(session: Session, trainer_id: int | None = None) -> Trainer | None:
    """
    Trova il trainer a cui assegnare i clienti.

    Se trainer_id e' specificato, usa quello.
    Altrimenti prende il primo trainer registrato (id piu' basso).
    """
    if trainer_id:
        return session.get(Trainer, trainer_id)

    return session.exec(
        select(Trainer).where(Trainer.is_active == True).order_by(Trainer.id)
    ).first()


def assign_clients(session: Session, trainer: Trainer, clients: list[Client], dry_run: bool = False) -> int:
    """
    Assegna trainer_id ai clienti orfani.

    Ritorna il numero di clienti aggiornati.
    """
    count = 0
    for client in clients:
        print(f"  {'[DRY-RUN] ' if dry_run else ''}Assegno: {client.cognome} {client.nome} (id={client.id}) -> trainer {trainer.nome} {trainer.cognome} (id={trainer.id})")
        if not dry_run:
            client.trainer_id = trainer.id
            session.add(client)
        count += 1

    if not dry_run and count > 0:
        session.commit()

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Assegna clienti legacy (trainer_id=NULL) a un trainer."
    )
    parser.add_argument(
        "--trainer-id", type=int, default=None,
        help="ID del trainer target. Se omesso, usa il primo trainer registrato."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra cosa verrebbe fatto senza scrivere nel DB."
    )
    args = parser.parse_args()

    with Session(engine) as session:
        # 1. Trova trainer target
        trainer = get_target_trainer(session, args.trainer_id)
        if not trainer:
            if args.trainer_id:
                print(f"ERRORE: Trainer con id={args.trainer_id} non trovato o disattivato.")
            else:
                print("ERRORE: Nessun trainer registrato. Registrane uno prima:")
                print("  curl -X POST http://localhost:8000/api/auth/register \\")
                print('    -H "Content-Type: application/json" \\')
                print('    -d \'{"email":"tu@email.com","password":"..","nome":"..","cognome":".."}\'')
            sys.exit(1)

        print(f"Trainer target: {trainer.nome} {trainer.cognome} (id={trainer.id})")

        # 2. Trova clienti orfani
        orphans = get_orphan_clients(session)
        if not orphans:
            print("Nessun cliente orfano trovato. Tutti hanno gia' un trainer_id.")
            sys.exit(0)

        print(f"Trovati {len(orphans)} clienti senza trainer_id:\n")

        # 3. Assegna
        count = assign_clients(session, trainer, orphans, dry_run=args.dry_run)

        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Completato: {count} clienti aggiornati.")
        if args.dry_run:
            print("Riesegui SENZA --dry-run per applicare le modifiche.")


if __name__ == "__main__":
    main()
