# api/routers/measurements.py
"""
Endpoint Misurazioni Corporee — CRUD con Bouncer Pattern + Deep Relational IDOR.

Endpoint:
  GET    /metrics                                  -> catalogo metriche
  GET    /clients/{id}/measurements                -> lista sessioni con valori
  GET    /clients/{id}/measurements/latest         -> ultima sessione
  POST   /clients/{id}/measurements                -> crea sessione + valori batch
  PUT    /clients/{id}/measurements/{session_id}   -> modifica sessione + valori
  DELETE /clients/{id}/measurements/{session_id}   -> soft-delete sessione

Deep IDOR: id_cliente -> Client.trainer_id == JWT trainer_id
           session_id -> ClientMeasurement.trainer_id == JWT trainer_id
"""

from datetime import date, datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.measurement import Metric, ClientMeasurement, MeasurementValue
from api.schemas.measurement import (
    MeasurementCreate, MeasurementUpdate,
    MetricResponse, MeasurementResponse,
    MeasurementValueResponse, MeasurementListResponse,
)

router = APIRouter(tags=["measurements"])


# ════════════════════════════════════════════════════════════
# HELPERS — Bouncer Pattern
# ════════════════════════════════════════════════════════════

def _bouncer_client(session: Session, client_id: int, trainer_id: int) -> Client:
    """Bouncer: verifica ownership cliente. 404 se non trovato o non proprio."""
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer_id,
            Client.deleted_at == None,
        )
    ).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )
    return client


def _bouncer_measurement(
    session: Session, measurement_id: int, trainer_id: int
) -> ClientMeasurement:
    """Bouncer: verifica ownership sessione misurazione. 404 se non trovata."""
    measurement = session.exec(
        select(ClientMeasurement).where(
            ClientMeasurement.id == measurement_id,
            ClientMeasurement.trainer_id == trainer_id,
            ClientMeasurement.deleted_at == None,
        )
    ).first()
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Misurazione non trovata",
        )
    return measurement


def _load_metric_map(session: Session) -> dict[int, Metric]:
    """Carica catalogo metriche in memoria per enrichment (anti-N+1)."""
    metrics = session.exec(select(Metric)).all()
    return {m.id: m for m in metrics}


def _build_measurement_response(
    measurement: ClientMeasurement,
    values: List[MeasurementValue],
    metric_map: dict[int, Metric],
) -> MeasurementResponse:
    """Costruisce response enriched con nomi metriche."""
    valori = []
    for v in values:
        m = metric_map.get(v.id_metrica)
        if m:
            valori.append(MeasurementValueResponse(
                id_metrica=v.id_metrica,
                nome_metrica=m.nome,
                unita=m.unita_misura,
                valore=v.valore,
            ))
    return MeasurementResponse(
        id=measurement.id,
        id_cliente=measurement.id_cliente,
        data_misurazione=str(measurement.data_misurazione),
        note=measurement.note,
        valori=valori,
    )


# ════════════════════════════════════════════════════════════
# CATALOGO METRICHE (pubblico, autenticato)
# ════════════════════════════════════════════════════════════

@router.get("/metrics", response_model=List[MetricResponse])
def list_metrics(
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Catalogo metriche standard — raggruppabili per categoria lato frontend."""
    metrics = session.exec(
        select(Metric).order_by(Metric.categoria, Metric.ordinamento)
    ).all()
    return metrics


# ════════════════════════════════════════════════════════════
# CRUD MISURAZIONI CLIENTE
# ════════════════════════════════════════════════════════════

@router.get(
    "/clients/{client_id}/measurements",
    response_model=MeasurementListResponse,
)
def list_measurements(
    client_id: int,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Lista sessioni di misurazione per cliente — anti-N+1 con batch fetch."""
    _bouncer_client(session, client_id, trainer.id)

    # Fetch sessioni attive ordinate per data DESC
    measurements = session.exec(
        select(ClientMeasurement).where(
            ClientMeasurement.id_cliente == client_id,
            ClientMeasurement.trainer_id == trainer.id,
            ClientMeasurement.deleted_at == None,
        ).order_by(ClientMeasurement.data_misurazione.desc())
    ).all()

    if not measurements:
        return MeasurementListResponse(items=[], total=0)

    # Batch fetch valori (anti-N+1)
    measurement_ids = [m.id for m in measurements]
    values = session.exec(
        select(MeasurementValue).where(
            MeasurementValue.id_misurazione.in_(measurement_ids)
        )
    ).all()

    # Group values by measurement_id
    values_by_measurement: dict[int, list[MeasurementValue]] = {}
    for v in values:
        values_by_measurement.setdefault(v.id_misurazione, []).append(v)

    # Metric map per enrichment
    metric_map = _load_metric_map(session)

    items = [
        _build_measurement_response(m, values_by_measurement.get(m.id, []), metric_map)
        for m in measurements
    ]

    return MeasurementListResponse(items=items, total=len(items))


@router.get(
    "/clients/{client_id}/measurements/latest",
    response_model=MeasurementResponse,
)
def get_latest_measurement(
    client_id: int,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Ultima sessione di misurazione per un cliente — per KPI/preview."""
    _bouncer_client(session, client_id, trainer.id)

    measurement = session.exec(
        select(ClientMeasurement).where(
            ClientMeasurement.id_cliente == client_id,
            ClientMeasurement.trainer_id == trainer.id,
            ClientMeasurement.deleted_at == None,
        ).order_by(ClientMeasurement.data_misurazione.desc())
    ).first()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessuna misurazione trovata",
        )

    values = session.exec(
        select(MeasurementValue).where(
            MeasurementValue.id_misurazione == measurement.id
        )
    ).all()

    metric_map = _load_metric_map(session)
    return _build_measurement_response(measurement, values, metric_map)


@router.post(
    "/clients/{client_id}/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_measurement(
    client_id: int,
    data: MeasurementCreate,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Crea sessione di misurazione + valori batch. Atomica."""
    _bouncer_client(session, client_id, trainer.id)

    # Valida data
    try:
        parsed_date = date.fromisoformat(data.data_misurazione)
    except ValueError:
        raise HTTPException(status_code=422, detail="Data non valida")

    if parsed_date > date.today():
        raise HTTPException(status_code=422, detail="Data futura non ammessa")

    # Valida metric IDs
    metric_map = _load_metric_map(session)
    valid_metric_ids = set(metric_map.keys())
    for v in data.valori:
        if v.id_metrica not in valid_metric_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Metrica id={v.id_metrica} non trovata nel catalogo",
            )

    # Crea sessione
    measurement = ClientMeasurement(
        id_cliente=client_id,
        trainer_id=trainer.id,
        data_misurazione=parsed_date,
        note=data.note,
    )
    session.add(measurement)
    session.flush()  # get ID before inserting values

    # Crea valori
    values = []
    for v in data.valori:
        value = MeasurementValue(
            id_misurazione=measurement.id,
            id_metrica=v.id_metrica,
            valore=v.valore,
        )
        session.add(value)
        values.append(value)

    session.commit()
    session.refresh(measurement)

    return _build_measurement_response(measurement, values, metric_map)


@router.put(
    "/clients/{client_id}/measurements/{measurement_id}",
    response_model=MeasurementResponse,
)
def update_measurement(
    client_id: int,
    measurement_id: int,
    data: MeasurementUpdate,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Aggiorna sessione di misurazione. Full-replace valori se forniti."""
    _bouncer_client(session, client_id, trainer.id)
    measurement = _bouncer_measurement(session, measurement_id, trainer.id)

    # Verifica che la sessione appartenga al cliente
    if measurement.id_cliente != client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Misurazione non trovata per questo cliente",
        )

    # Update data
    if data.data_misurazione is not None:
        try:
            parsed_date = date.fromisoformat(data.data_misurazione)
        except ValueError:
            raise HTTPException(status_code=422, detail="Data non valida")
        if parsed_date > date.today():
            raise HTTPException(status_code=422, detail="Data futura non ammessa")
        measurement.data_misurazione = parsed_date

    # Update note
    if data.note is not None:
        measurement.note = data.note

    # Full-replace valori (se forniti)
    metric_map = _load_metric_map(session)
    if data.valori is not None:
        valid_metric_ids = set(metric_map.keys())
        for v in data.valori:
            if v.id_metrica not in valid_metric_ids:
                raise HTTPException(
                    status_code=422,
                    detail=f"Metrica id={v.id_metrica} non trovata nel catalogo",
                )

        # Delete old values
        old_values = session.exec(
            select(MeasurementValue).where(
                MeasurementValue.id_misurazione == measurement.id
            )
        ).all()
        for ov in old_values:
            session.delete(ov)

        # Insert new values
        new_values = []
        for v in data.valori:
            value = MeasurementValue(
                id_misurazione=measurement.id,
                id_metrica=v.id_metrica,
                valore=v.valore,
            )
            session.add(value)
            new_values.append(value)
    else:
        new_values = session.exec(
            select(MeasurementValue).where(
                MeasurementValue.id_misurazione == measurement.id
            )
        ).all()

    session.commit()
    session.refresh(measurement)

    return _build_measurement_response(measurement, new_values, metric_map)


@router.delete(
    "/clients/{client_id}/measurements/{measurement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_measurement(
    client_id: int,
    measurement_id: int,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Soft-delete sessione di misurazione."""
    _bouncer_client(session, client_id, trainer.id)
    measurement = _bouncer_measurement(session, measurement_id, trainer.id)

    if measurement.id_cliente != client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Misurazione non trovata per questo cliente",
        )

    measurement.deleted_at = datetime.now(timezone.utc)
    session.commit()
