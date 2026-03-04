"""
Entity Resolver — risolve entita' estratte contro il DB.

Usa difflib.SequenceMatcher (stdlib) per fuzzy matching clienti.
Zero dipendenze esterne.
"""

import difflib
from dataclasses import dataclass

from sqlmodel import Session, select

from api.models.client import Client


@dataclass
class ClientMatch:
    """Risultato del matching cliente."""

    client: Client
    score: float  # 0.0 - 1.0
    matched_name: str  # nome usato per il match

    @property
    def full_name(self) -> str:
        return f"{self.client.nome} {self.client.cognome}"


# Soglie di risoluzione
THRESHOLD_AUTO = 0.90  # Auto-resolve senza ambiguita'
THRESHOLD_AMBIGUOUS = 0.70  # Mostra come ambiguo
THRESHOLD_MIN = 0.50  # Sotto questo, ignora


def resolve_client(
    name_parts: list[str],
    session: Session,
    trainer_id: int,
) -> list[ClientMatch]:
    """
    Fuzzy match nome persona contro clienti attivi del trainer.

    Ritorna lista di ClientMatch ordinata per score DESC.
    Solo matches con score >= THRESHOLD_MIN.
    """
    clients = session.exec(
        select(Client).where(
            Client.trainer_id == trainer_id,
            Client.deleted_at == None,  # noqa: E711
            Client.stato == "Attivo",
        )
    ).all()

    if not clients:
        return []

    input_name = " ".join(name_parts).lower().strip()
    results: list[ClientMatch] = []

    for client in clients:
        full_name = f"{client.nome} {client.cognome}".lower()
        reversed_name = f"{client.cognome} {client.nome}".lower()

        score_direct = difflib.SequenceMatcher(
            None, input_name, full_name,
        ).ratio()
        score_reversed = difflib.SequenceMatcher(
            None, input_name, reversed_name,
        ).ratio()
        best_score = max(score_direct, score_reversed)
        matched_name = full_name if score_direct >= score_reversed else reversed_name

        # Partial match: se input e' solo un nome (1 parola)
        if len(name_parts) == 1:
            nome_score = difflib.SequenceMatcher(
                None, input_name, client.nome.lower(),
            ).ratio()
            cognome_score = difflib.SequenceMatcher(
                None, input_name, client.cognome.lower(),
            ).ratio()
            partial_best = max(nome_score, cognome_score) * 0.85
            if partial_best > best_score:
                best_score = partial_best
                matched_name = (
                    client.nome.lower()
                    if nome_score >= cognome_score
                    else client.cognome.lower()
                )

        if best_score >= THRESHOLD_MIN:
            results.append(ClientMatch(
                client=client,
                score=round(best_score, 3),
                matched_name=matched_name,
            ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def is_auto_resolved(matches: list[ClientMatch]) -> bool:
    """True se c'e' un solo match con score >= THRESHOLD_AUTO."""
    if not matches:
        return False
    if matches[0].score >= THRESHOLD_AUTO:
        # Check che non ci sia un secondo match troppo vicino
        if len(matches) == 1:
            return True
        return matches[0].score - matches[1].score > 0.10
    return False


def is_ambiguous(matches: list[ClientMatch]) -> bool:
    """True se ci sono piu' match con score simile."""
    if len(matches) < 2:
        return False
    return (
        matches[0].score >= THRESHOLD_AMBIGUOUS
        and matches[1].score >= THRESHOLD_AMBIGUOUS
        and matches[0].score - matches[1].score < 0.10
    )
