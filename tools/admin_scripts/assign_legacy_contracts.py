# tools/admin_scripts/assign_legacy_contracts.py
"""
Migrazione contratti legacy: assegna trainer_id ai contratti con trainer_id=NULL.

Perche' serve:
    La tabella 'contratti' esisteva prima della multi-tenancy.
    I 7 contratti storici hanno trainer_id=NULL, quindi l'API (che filtra
    per trainer_id) non li restituisce. Questo script li assegna.

Strategia di assegnazione:
    - Ogni contratto ha id_cliente. Se quel cliente ha gia' un trainer_id,
      il contratto viene assegnato allo STESSO trainer (coerenza relazionale).
    - Se il cliente non ha trainer_id (non ancora migrato), entrambi vengono
      assegnati al primo trainer registrato.

NOTE:
    - Le rate_programmate NON hanno trainer_id (ownership via contratto).
      Quindi basta migrare i contratti: le rate sono automaticamente assegnate.
    - Idempotente: se non ci sono orfani, non fa nulla.
    - Eseguire DOPO assign_legacy_clients.py (i clienti devono avere trainer_id).

Uso:
    python tools/admin_scripts/assign_legacy_contracts.py
    python tools/admin_scripts/assign_legacy_contracts.py --dry-run
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, select
from api.database import engine
from api.models.trainer import Trainer
from api.models.contract import Contract
from api.models.client import Client


def get_first_trainer(session: Session) -> Trainer | None:
    """Primo trainer attivo per ID."""
    return session.exec(
        select(Trainer).where(Trainer.is_active == True).order_by(Trainer.id)
    ).first()


def assign_contracts(session: Session, default_trainer: Trainer, dry_run: bool = False) -> int:
    """
    Assegna trainer_id ai contratti orfani.

    Logica:
    1. Contratto con id_cliente che ha trainer_id -> usa il trainer del cliente
    2. Cliente senza trainer_id -> assegna entrambi al default_trainer
    """
    orphans = list(session.exec(
        select(Contract).where(Contract.trainer_id.is_(None))  # type: ignore[union-attr]
    ).all())

    if not orphans:
        print("Nessun contratto orfano. Tutti hanno gia' un trainer_id.")
        return 0

    print(f"Trovati {len(orphans)} contratti senza trainer_id:\n")
    count = 0

    for contract in orphans:
        target_trainer = default_trainer

        # Cerca il trainer del cliente associato
        client = session.get(Client, contract.id_cliente)
        if client and client.trainer_id:
            trainer_obj = session.get(Trainer, client.trainer_id)
            if trainer_obj:
                target_trainer = trainer_obj
        elif client and not client.trainer_id and not dry_run:
            # Bonus: assegna anche il cliente al default trainer
            client.trainer_id = default_trainer.id
            session.add(client)
            print(f"  {'[DRY-RUN] ' if dry_run else ''}(bonus) Cliente '{client.cognome} {client.nome}' assegnato a trainer {default_trainer.id}")

        prefix = "[DRY-RUN] " if dry_run else ""
        pacchetto = contract.tipo_pacchetto or "?"
        prezzo = f"{contract.prezzo_totale:.0f}€" if contract.prezzo_totale else "?"
        print(f"  {prefix}Contratto id={contract.id} [{pacchetto}] ({prezzo}, cliente={contract.id_cliente}) -> trainer {target_trainer.nome} {target_trainer.cognome} (id={target_trainer.id})")

        if not dry_run:
            contract.trainer_id = target_trainer.id
            session.add(contract)
        count += 1

    if not dry_run and count > 0:
        session.commit()

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Assegna contratti legacy (trainer_id=NULL) a un trainer."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview senza scrivere")
    args = parser.parse_args()

    with Session(engine) as session:
        trainer = get_first_trainer(session)
        if not trainer:
            print("ERRORE: Nessun trainer registrato.")
            print("  Registrane uno prima via POST /api/auth/register")
            sys.exit(1)

        print(f"Trainer default: {trainer.nome} {trainer.cognome} (id={trainer.id})\n")
        count = assign_contracts(session, trainer, dry_run=args.dry_run)

        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Completato: {count} contratti aggiornati.")
        if args.dry_run:
            print("Riesegui SENZA --dry-run per applicare.")


if __name__ == "__main__":
    main()
