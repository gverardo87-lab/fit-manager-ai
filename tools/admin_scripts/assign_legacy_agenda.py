# tools/admin_scripts/assign_legacy_agenda.py
"""
Migrazione eventi legacy: assegna gli eventi con trainer_id=NULL al primo trainer.

Perche' serve:
    La tabella 'agenda' esisteva prima della multi-tenancy.
    I 19 eventi storici hanno trainer_id=NULL, quindi l'API (che filtra
    per trainer_id) non li restituisce. Questo script li assegna.

Strategia di assegnazione:
    - Eventi CON id_cliente: assegna al trainer del cliente (se il cliente
      ha gia' trainer_id). Questo garantisce coerenza relazionale.
    - Eventi SENZA id_cliente (SALA, CORSO): assegna al primo trainer registrato.
    - Se il cliente non ha ancora trainer_id: assegna entrambi al primo trainer.

Uso:
    python tools/admin_scripts/assign_legacy_agenda.py
    python tools/admin_scripts/assign_legacy_agenda.py --dry-run
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, select
from api.database import engine
from api.models.trainer import Trainer
from api.models.event import Event
from api.models.client import Client


def get_first_trainer(session: Session) -> Trainer | None:
    """Primo trainer attivo per ID."""
    return session.exec(
        select(Trainer).where(Trainer.is_active == True).order_by(Trainer.id)
    ).first()


def assign_events(session: Session, default_trainer: Trainer, dry_run: bool = False) -> int:
    """
    Assegna trainer_id agli eventi orfani.

    Logica:
    1. Evento con id_cliente -> usa il trainer del cliente
    2. Evento senza id_cliente -> usa default_trainer
    3. Cliente senza trainer -> assegna anche il cliente
    """
    orphans = list(session.exec(
        select(Event).where(Event.trainer_id.is_(None))  # type: ignore[union-attr]
    ).all())

    if not orphans:
        print("Nessun evento orfano. Tutti hanno gia' un trainer_id.")
        return 0

    print(f"Trovati {len(orphans)} eventi senza trainer_id:\n")
    count = 0

    for event in orphans:
        target_trainer = default_trainer

        # Se l'evento ha un cliente, usa il trainer del cliente
        if event.id_cliente:
            client = session.get(Client, event.id_cliente)
            if client and client.trainer_id:
                target_trainer_obj = session.get(Trainer, client.trainer_id)
                if target_trainer_obj:
                    target_trainer = target_trainer_obj
            elif client and not client.trainer_id and not dry_run:
                # Assegna anche il cliente al default trainer
                client.trainer_id = default_trainer.id
                session.add(client)
                print(f"  {'[DRY-RUN] ' if dry_run else ''}(bonus) Cliente '{client.cognome} {client.nome}' assegnato a trainer {default_trainer.id}")

        prefix = "[DRY-RUN] " if dry_run else ""
        cat = event.categoria or "?"
        cli = f"cliente={event.id_cliente}" if event.id_cliente else "generico"
        print(f"  {prefix}Evento id={event.id} [{cat}] ({cli}) -> trainer {target_trainer.nome} {target_trainer.cognome} (id={target_trainer.id})")

        if not dry_run:
            event.trainer_id = target_trainer.id
            session.add(event)
        count += 1

    if not dry_run and count > 0:
        session.commit()

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Assegna eventi legacy (trainer_id=NULL) a un trainer."
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
        count = assign_events(session, trainer, dry_run=args.dry_run)

        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Completato: {count} eventi aggiornati.")
        if args.dry_run:
            print("Riesegui SENZA --dry-run per applicare.")


if __name__ == "__main__":
    main()
