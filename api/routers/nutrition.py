"""
Router nutrizione — CRUD piani alimentari + catalogo alimenti.

Struttura endpoint:
  Catalogo (nutrition.db, read-only):
    GET  /nutrition/categories          — tutte le categorie
    GET  /nutrition/foods               — ricerca alimenti (q, categoria_id)
    GET  /nutrition/foods/{id}          — dettaglio alimento + porzioni

  Piani alimentari (crm.db, trainer-owned):
    GET  /clients/{id}/nutrition/summary           — snapshot nutrizionale
    GET  /clients/{id}/nutrition/plans             — lista piani
    POST /clients/{id}/nutrition/plans             — crea piano
    GET  /clients/{id}/nutrition/plans/{plan_id}   — dettaglio piano + pasti
    PUT  /clients/{id}/nutrition/plans/{plan_id}   — aggiorna piano
    DELETE /clients/{id}/nutrition/plans/{plan_id} — soft delete piano

    POST   /nutrition/plans/{plan_id}/meals              — aggiungi pasto
    PUT    /nutrition/plans/{plan_id}/meals/{meal_id}    — aggiorna pasto
    DELETE /nutrition/plans/{plan_id}/meals/{meal_id}    — elimina pasto

    POST   /nutrition/plans/{plan_id}/meals/{meal_id}/components            — aggiungi alimento
    PUT    /nutrition/plans/{plan_id}/meals/{meal_id}/components/{comp_id}  — aggiorna quantita'
    DELETE /nutrition/plans/{plan_id}/meals/{meal_id}/components/{comp_id}  — rimuovi alimento

Bouncer Pattern: ogni piano verificato con trainer_id prima di qualsiasi operazione.
Deep IDOR: pasto → piano → trainer_id | componente → pasto → piano → trainer_id
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from api.database import get_nutrition_session, get_session
from api.dependencies import get_current_trainer
from api.models.nutrition import (
    FoodCategory,
    Food,
    MealComponent,
    MealTemplate,
    NutritionPlan,
    PlanMeal,
    PlanTemplate,
    StandardPortion,
    TemplateComponent,
    TemplatePlanComponent,
    TemplatePlanMeal,
)
from api.models.trainer import Trainer
from api.schemas.nutrition import (
    ApplyTemplateResult,
    CopyDayInput,
    CopyDayResult,
    CreateFromTemplateInput,
    FoodCategoryResponse,
    FoodDetailResponse,
    FoodResponse,
    MealComponentCreate,
    MealComponentDetail,
    MealComponentUpdate,
    MealTemplateCreate,
    MealTemplateDetail,
    NutritionPlanCreate,
    NutritionPlanDetail,
    NutritionPlanResponse,
    NutritionPlanUpdate,
    NutritionSummary,
    PlanMealCreate,
    PlanMealDetail,
    PlanMealResponse,
    PlanMealUpdate,
    PlanTemplateItem,
    SaveAsTemplateInput,
    StandardPortionResponse,
    TemplateComponentDetail,
    TIPO_PASTO_LABELS,
    GIORNO_LABELS,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["nutrition"])


# ---------------------------------------------------------------------------
# Helper: calcolo macro scalati per quantita' (da 100g a X grammi)
# ---------------------------------------------------------------------------


def _scale_macro(value: Optional[float], quantita_g: float) -> Optional[float]:
    if value is None:
        return None
    return round(value * quantita_g / 100, 2)


def _enrich_component(
    comp: MealComponent,
    food: Optional[Food],
    categoria_nome: Optional[str] = None,
) -> MealComponentDetail:
    """Costruisce MealComponentDetail arricchito con macro calcolati."""
    if food is None:
        return MealComponentDetail(
            id=comp.id,
            pasto_id=comp.pasto_id,
            alimento_id=comp.alimento_id,
            quantita_g=comp.quantita_g,
            note=comp.note,
        )
    return MealComponentDetail(
        id=comp.id,
        pasto_id=comp.pasto_id,
        alimento_id=comp.alimento_id,
        alimento_nome=food.nome,
        alimento_categoria=categoria_nome,
        quantita_g=comp.quantita_g,
        note=comp.note,
        energia_kcal=round(food.energia_kcal * comp.quantita_g / 100, 1),
        proteine_g=round(food.proteine_g * comp.quantita_g / 100, 1),
        carboidrati_g=round(food.carboidrati_g * comp.quantita_g / 100, 1),
        grassi_g=round(food.grassi_g * comp.quantita_g / 100, 1),
        fibra_g=_scale_macro(food.fibra_g, comp.quantita_g),
    )


def _enrich_meal(
    meal: PlanMeal,
    components: list[MealComponent],
    food_map: dict[int, Food],
    cat_map: dict[int, str],
) -> PlanMealDetail:
    """Costruisce PlanMealDetail con componenti arricchiti e totali macro."""
    enriched_comps = [
        _enrich_component(c, food_map.get(c.alimento_id), cat_map.get(food_map[c.alimento_id].categoria_id) if c.alimento_id in food_map else None)
        for c in components
    ]
    totale_kcal = sum(c.energia_kcal for c in enriched_comps)
    totale_prot = sum(c.proteine_g for c in enriched_comps)
    totale_carb = sum(c.carboidrati_g for c in enriched_comps)
    totale_gras = sum(c.grassi_g for c in enriched_comps)

    return PlanMealDetail(
        id=meal.id,
        piano_id=meal.piano_id,
        giorno_settimana=meal.giorno_settimana,
        giorno_label=GIORNO_LABELS.get(meal.giorno_settimana),
        tipo_pasto=meal.tipo_pasto,
        tipo_pasto_label=TIPO_PASTO_LABELS.get(meal.tipo_pasto),
        ordine=meal.ordine,
        nome=meal.nome,
        note=meal.note,
        componenti=enriched_comps,
        totale_kcal=round(totale_kcal, 1),
        totale_proteine_g=round(totale_prot, 1),
        totale_carboidrati_g=round(totale_carb, 1),
        totale_grassi_g=round(totale_gras, 1),
    )


# ---------------------------------------------------------------------------
# Bouncer helpers
# ---------------------------------------------------------------------------


def _bouncer_plan(session: Session, plan_id: int, trainer_id: int) -> NutritionPlan:
    """Verifica ownership piano e ritorna il record. 404 se non trovato/non owned."""
    plan = session.exec(
        select(NutritionPlan).where(
            NutritionPlan.id == plan_id,
            NutritionPlan.trainer_id == trainer_id,
            NutritionPlan.deleted_at == None,
        )
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Piano alimentare non trovato")
    return plan


def _bouncer_meal(session: Session, meal_id: int, trainer_id: int) -> PlanMeal:
    """Deep IDOR: pasto → piano → trainer_id."""
    meal = session.exec(
        select(PlanMeal)
        .join(NutritionPlan, PlanMeal.piano_id == NutritionPlan.id)
        .where(
            PlanMeal.id == meal_id,
            PlanMeal.deleted_at == None,
            NutritionPlan.trainer_id == trainer_id,
            NutritionPlan.deleted_at == None,
        )
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Pasto non trovato")
    return meal


def _bouncer_component(
    session: Session, comp_id: int, trainer_id: int
) -> MealComponent:
    """Deep IDOR: componente → pasto → piano → trainer_id."""
    comp = session.exec(
        select(MealComponent)
        .join(PlanMeal, MealComponent.pasto_id == PlanMeal.id)
        .join(NutritionPlan, PlanMeal.piano_id == NutritionPlan.id)
        .where(
            MealComponent.id == comp_id,
            MealComponent.deleted_at == None,
            PlanMeal.deleted_at == None,
            NutritionPlan.trainer_id == trainer_id,
            NutritionPlan.deleted_at == None,
        )
    ).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Componente pasto non trovato")
    return comp


def _bouncer_client(session: Session, client_id: int, trainer_id: int) -> None:
    """Verifica che il cliente appartenga al trainer (Relational IDOR)."""
    from api.models.client import Client
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer_id,
            Client.deleted_at == None,
        )
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")


# ---------------------------------------------------------------------------
# CATALOGO — GET /nutrition/categories
# ---------------------------------------------------------------------------


@router.get("/nutrition/categories", response_model=list[FoodCategoryResponse])
def get_food_categories(
    trainer: Trainer = Depends(get_current_trainer),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Lista tutte le categorie alimentari (da nutrition.db)."""
    cats = nutrition_session.exec(
        select(FoodCategory).order_by(FoodCategory.nome)
    ).all()
    return [FoodCategoryResponse.model_validate(c) for c in cats]


# ---------------------------------------------------------------------------
# CATALOGO — GET /nutrition/foods
# ---------------------------------------------------------------------------


@router.get("/nutrition/foods", response_model=list[FoodResponse])
def search_foods(
    q: Optional[str] = Query(None, description="Ricerca per nome (min 2 caratteri)"),
    categoria_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    trainer: Trainer = Depends(get_current_trainer),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Ricerca alimenti nel catalogo.

    Usata dalla searchbar nel piano alimentare per trovare alimenti da aggiungere.
    Ritorna al massimo 50 risultati per default.
    """
    query = select(Food, FoodCategory).join(
        FoodCategory, Food.categoria_id == FoodCategory.id
    ).where(Food.is_active == True)

    if q and len(q) >= 2:
        query = query.where(Food.nome.ilike(f"%{q}%"))
    if categoria_id is not None:
        query = query.where(Food.categoria_id == categoria_id)

    query = query.order_by(Food.nome).offset(offset).limit(limit)
    rows = nutrition_session.exec(query).all()

    results = []
    for food, cat in rows:
        resp = FoodResponse.model_validate(food)
        resp.categoria_nome = cat.nome
        results.append(resp)
    return results


# ---------------------------------------------------------------------------
# CATALOGO — GET /nutrition/foods/{food_id}
# ---------------------------------------------------------------------------


@router.get("/nutrition/foods/{food_id}", response_model=FoodDetailResponse)
def get_food_detail(
    food_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Dettaglio alimento con macro completi e porzioni standard."""
    row = nutrition_session.exec(
        select(Food, FoodCategory)
        .join(FoodCategory, Food.categoria_id == FoodCategory.id)
        .where(Food.id == food_id, Food.is_active == True)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Alimento non trovato")
    food, cat = row

    porzioni = nutrition_session.exec(
        select(StandardPortion).where(StandardPortion.alimento_id == food_id)
    ).all()

    resp = FoodDetailResponse.model_validate(food)
    resp.categoria_nome = cat.nome
    resp.porzioni = [StandardPortionResponse.model_validate(p) for p in porzioni]
    return resp


# ---------------------------------------------------------------------------
# Helper: costruisce NutritionPlanResponse con client info opzionale
# ---------------------------------------------------------------------------


def _plan_to_response(
    plan: NutritionPlan,
    client_nome: Optional[str] = None,
    client_cognome: Optional[str] = None,
    num_pasti: Optional[int] = None,
) -> NutritionPlanResponse:
    """Costruisce NutritionPlanResponse da ORM object + dati cliente opzionali."""
    return NutritionPlanResponse(
        id=plan.id,
        trainer_id=plan.trainer_id,
        id_cliente=plan.id_cliente,
        nome=plan.nome,
        obiettivo_calorico=plan.obiettivo_calorico,
        proteine_g_target=plan.proteine_g_target,
        carboidrati_g_target=plan.carboidrati_g_target,
        grassi_g_target=plan.grassi_g_target,
        note_cliniche=plan.note_cliniche,
        data_inizio=plan.data_inizio,
        data_fine=plan.data_fine,
        attivo=plan.attivo,
        created_at=plan.created_at,
        client_nome=client_nome,
        client_cognome=client_cognome,
        num_pasti=num_pasti,
    )


# ---------------------------------------------------------------------------
# PIANI — GET /nutrition/plans  (cross-client, tutti i piani del trainer)
# ---------------------------------------------------------------------------


@router.get("/nutrition/plans", response_model=list[NutritionPlanResponse])
def list_all_nutrition_plans(
    attivo: Optional[bool] = Query(None, description="Filtra per stato attivo/inattivo"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Lista tutti i piani alimentari del trainer (cross-client).

    Arricchisce ogni piano con: nome cliente + conteggio pasti.
    Usato dalla pagina /nutrizione (lista piani globale).
    """
    from api.models.client import Client

    query = select(NutritionPlan).where(
        NutritionPlan.trainer_id == trainer.id,
        NutritionPlan.deleted_at == None,
    )
    if attivo is not None:
        query = query.where(NutritionPlan.attivo == attivo)
    query = query.order_by(NutritionPlan.created_at.desc())
    plans = session.exec(query).all()

    if not plans:
        return []

    # Batch fetch clienti
    client_ids = list({p.id_cliente for p in plans})
    clients = session.exec(select(Client).where(Client.id.in_(client_ids))).all()
    client_map = {c.id: c for c in clients}

    # Batch fetch conteggio pasti per piano
    plan_ids = [p.id for p in plans]
    meal_counts_rows = session.exec(
        select(PlanMeal.piano_id, func.count(PlanMeal.id))
        .where(PlanMeal.piano_id.in_(plan_ids), PlanMeal.deleted_at == None)
        .group_by(PlanMeal.piano_id)
    ).all()
    meal_count_map: dict[int, int] = {row[0]: row[1] for row in meal_counts_rows}

    return [
        _plan_to_response(
            plan=p,
            client_nome=client_map[p.id_cliente].nome if p.id_cliente in client_map else None,
            client_cognome=client_map[p.id_cliente].cognome if p.id_cliente in client_map else None,
            num_pasti=meal_count_map.get(p.id, 0),
        )
        for p in plans
    ]


# ---------------------------------------------------------------------------
# PIANI — GET /nutrition/plans/{plan_id}  (by id, senza clientId)
# ---------------------------------------------------------------------------


@router.get("/nutrition/plans/{plan_id}", response_model=NutritionPlanDetail)
def get_nutrition_plan_by_id(
    plan_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Dettaglio piano per id diretto (senza clientId).

    Bouncer verifica trainer_id dal JWT — nessun clientId richiesto.
    Usato dalla pagina /nutrizione/{id} per navigazione cross-client.
    """
    plan = _bouncer_plan(session, plan_id, trainer.id)

    meals = session.exec(
        select(PlanMeal).where(
            PlanMeal.piano_id == plan_id,
            PlanMeal.deleted_at == None,
        ).order_by(PlanMeal.giorno_settimana, PlanMeal.ordine)
    ).all()
    meal_ids = [m.id for m in meals]

    components_all: list[MealComponent] = []
    food_map: dict[int, Food] = {}
    cat_map: dict[int, str] = {}

    if meal_ids:
        components_all = session.exec(
            select(MealComponent).where(
                MealComponent.pasto_id.in_(meal_ids),
                MealComponent.deleted_at == None,
            )
        ).all()

        if components_all:
            food_ids = list({c.alimento_id for c in components_all})
            foods = nutrition_session.exec(
                select(Food).where(Food.id.in_(food_ids))
            ).all()
            food_map = {f.id: f for f in foods}

            cat_ids = list({f.categoria_id for f in foods})
            cats = nutrition_session.exec(
                select(FoodCategory).where(FoodCategory.id.in_(cat_ids))
            ).all()
            cat_map = {c.id: c.nome for c in cats}

    comp_by_meal: dict[int, list[MealComponent]] = {m.id: [] for m in meals}
    for c in components_all:
        comp_by_meal[c.pasto_id].append(c)

    pasti_detail = [
        _enrich_meal(m, comp_by_meal[m.id], food_map, cat_map)
        for m in meals
    ]

    totale_kcal = sum(p.totale_kcal for p in pasti_detail)
    totale_prot = sum(p.totale_proteine_g for p in pasti_detail)
    totale_carb = sum(p.totale_carboidrati_g for p in pasti_detail)
    totale_gras = sum(p.totale_grassi_g for p in pasti_detail)

    giorni_unici = {m.giorno_settimana for m in meals}
    n_giorni = max(len(giorni_unici), 1)

    detail = NutritionPlanDetail.model_validate(plan)
    detail.pasti = pasti_detail
    detail.totale_kcal = round(totale_kcal / n_giorni, 1)
    detail.totale_proteine_g = round(totale_prot / n_giorni, 1)
    detail.totale_carboidrati_g = round(totale_carb / n_giorni, 1)
    detail.totale_grassi_g = round(totale_gras / n_giorni, 1)
    return detail


# ---------------------------------------------------------------------------
# SUMMARY — GET /clients/{client_id}/nutrition/summary
# ---------------------------------------------------------------------------


@router.get(
    "/clients/{client_id}/nutrition/summary",
    response_model=NutritionSummary,
)
def get_nutrition_summary(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Snapshot nutrizionale del cliente per il tab Nutrizione nel profilo.

    Calcola media macro giornaliera dal piano attivo (se presente).
    """
    _bouncer_client(session, client_id, trainer.id)

    totale_piani = session.exec(
        select(func.count(NutritionPlan.id)).where(
            NutritionPlan.id_cliente == client_id,
            NutritionPlan.trainer_id == trainer.id,
            NutritionPlan.deleted_at == None,
        )
    ).one()

    piano_attivo = session.exec(
        select(NutritionPlan).where(
            NutritionPlan.id_cliente == client_id,
            NutritionPlan.trainer_id == trainer.id,
            NutritionPlan.attivo == True,
            NutritionPlan.deleted_at == None,
        ).order_by(NutritionPlan.created_at.desc())
    ).first()

    if not piano_attivo:
        return NutritionSummary(
            ha_piano_attivo=False,
            totale_piani=totale_piani,
        )

    # Calcola media macro giornaliera dai componenti del piano attivo
    meals = session.exec(
        select(PlanMeal).where(
            PlanMeal.piano_id == piano_attivo.id,
            PlanMeal.deleted_at == None,
        )
    ).all()
    meal_ids = [m.id for m in meals]

    media_kcal = media_prot = media_carb = media_gras = None

    if meal_ids:
        components = session.exec(
            select(MealComponent).where(
                MealComponent.pasto_id.in_(meal_ids),
                MealComponent.deleted_at == None,
            )
        ).all()

        if components:
            food_ids = list({c.alimento_id for c in components})
            foods = nutrition_session.exec(
                select(Food).where(Food.id.in_(food_ids))
            ).all()
            food_map = {f.id: f for f in foods}

            # Giorni unici nel piano (0 = ogni giorno conta come 1)
            giorni_unici = {m.giorno_settimana for m in meals}
            n_giorni = max(len(giorni_unici), 1)

            totale_kcal = totale_prot = totale_carb = totale_gras = 0.0
            for comp in components:
                food = food_map.get(comp.alimento_id)
                if food:
                    factor = comp.quantita_g / 100
                    totale_kcal += food.energia_kcal * factor
                    totale_prot += food.proteine_g * factor
                    totale_carb += food.carboidrati_g * factor
                    totale_gras += food.grassi_g * factor

            media_kcal = round(totale_kcal / n_giorni, 1)
            media_prot = round(totale_prot / n_giorni, 1)
            media_carb = round(totale_carb / n_giorni, 1)
            media_gras = round(totale_gras / n_giorni, 1)

    delta_kcal = None
    if media_kcal is not None and piano_attivo.obiettivo_calorico:
        delta_kcal = round(media_kcal - piano_attivo.obiettivo_calorico, 1)

    return NutritionSummary(
        ha_piano_attivo=True,
        piano_attivo=NutritionPlanResponse.model_validate(piano_attivo),
        totale_piani=totale_piani,
        media_kcal_die=media_kcal,
        media_proteine_g_die=media_prot,
        media_carboidrati_g_die=media_carb,
        media_grassi_g_die=media_gras,
        obiettivo_calorico=piano_attivo.obiettivo_calorico,
        delta_kcal=delta_kcal,
    )


# ---------------------------------------------------------------------------
# PIANI — GET /clients/{client_id}/nutrition/plans
# ---------------------------------------------------------------------------


@router.get(
    "/clients/{client_id}/nutrition/plans",
    response_model=list[NutritionPlanResponse],
)
def list_nutrition_plans(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Lista piani alimentari del cliente (dal piu' recente)."""
    _bouncer_client(session, client_id, trainer.id)
    plans = session.exec(
        select(NutritionPlan).where(
            NutritionPlan.id_cliente == client_id,
            NutritionPlan.trainer_id == trainer.id,
            NutritionPlan.deleted_at == None,
        ).order_by(NutritionPlan.created_at.desc())
    ).all()
    return [NutritionPlanResponse.model_validate(p) for p in plans]


# ---------------------------------------------------------------------------
# PIANI — POST /clients/{client_id}/nutrition/plans
# ---------------------------------------------------------------------------


@router.post(
    "/clients/{client_id}/nutrition/plans",
    response_model=NutritionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_nutrition_plan(
    client_id: int,
    data: NutritionPlanCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo piano alimentare per il cliente.

    Se attivo=True, disattiva automaticamente tutti gli altri piani attivi
    del cliente (un solo piano attivo alla volta).
    """
    _bouncer_client(session, client_id, trainer.id)

    if data.attivo:
        # Disattiva piani attivi precedenti (atomic)
        piani_attivi = session.exec(
            select(NutritionPlan).where(
                NutritionPlan.id_cliente == client_id,
                NutritionPlan.trainer_id == trainer.id,
                NutritionPlan.attivo == True,
                NutritionPlan.deleted_at == None,
            )
        ).all()
        for p in piani_attivi:
            p.attivo = False
            session.add(p)

    plan = NutritionPlan(
        trainer_id=trainer.id,
        id_cliente=client_id,
        nome=data.nome,
        obiettivo_calorico=data.obiettivo_calorico,
        proteine_g_target=data.proteine_g_target,
        carboidrati_g_target=data.carboidrati_g_target,
        grassi_g_target=data.grassi_g_target,
        note_cliniche=data.note_cliniche,
        data_inizio=data.data_inizio,
        data_fine=data.data_fine,
        attivo=data.attivo,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return NutritionPlanResponse.model_validate(plan)


# ---------------------------------------------------------------------------
# PIANI — GET /clients/{client_id}/nutrition/plans/{plan_id}
# ---------------------------------------------------------------------------


@router.get(
    "/clients/{client_id}/nutrition/plans/{plan_id}",
    response_model=NutritionPlanDetail,
)
def get_nutrition_plan(
    client_id: int,
    plan_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Dettaglio piano con tutti i pasti, componenti e macro calcolati."""
    _bouncer_client(session, client_id, trainer.id)
    plan = _bouncer_plan(session, plan_id, trainer.id)

    meals = session.exec(
        select(PlanMeal).where(
            PlanMeal.piano_id == plan_id,
            PlanMeal.deleted_at == None,
        ).order_by(PlanMeal.giorno_settimana, PlanMeal.ordine)
    ).all()
    meal_ids = [m.id for m in meals]

    components_all: list[MealComponent] = []
    food_map: dict[int, Food] = {}
    cat_map: dict[int, str] = {}

    if meal_ids:
        components_all = session.exec(
            select(MealComponent).where(
                MealComponent.pasto_id.in_(meal_ids),
                MealComponent.deleted_at == None,
            )
        ).all()

        if components_all:
            food_ids = list({c.alimento_id for c in components_all})
            foods = nutrition_session.exec(
                select(Food).where(Food.id.in_(food_ids))
            ).all()
            food_map = {f.id: f for f in foods}

            cat_ids = list({f.categoria_id for f in foods})
            cats = nutrition_session.exec(
                select(FoodCategory).where(FoodCategory.id.in_(cat_ids))
            ).all()
            cat_map = {c.id: c.nome for c in cats}

    # Raggruppa componenti per pasto
    comp_by_meal: dict[int, list[MealComponent]] = {m.id: [] for m in meals}
    for c in components_all:
        comp_by_meal[c.pasto_id].append(c)

    pasti_detail = [
        _enrich_meal(m, comp_by_meal[m.id], food_map, cat_map)
        for m in meals
    ]

    # Totali del piano
    totale_kcal = sum(p.totale_kcal for p in pasti_detail)
    totale_prot = sum(p.totale_proteine_g for p in pasti_detail)
    totale_carb = sum(p.totale_carboidrati_g for p in pasti_detail)
    totale_gras = sum(p.totale_grassi_g for p in pasti_detail)

    # Media giornaliera
    giorni_unici = {m.giorno_settimana for m in meals}
    n_giorni = max(len(giorni_unici), 1)

    detail = NutritionPlanDetail.model_validate(plan)
    detail.pasti = pasti_detail
    detail.totale_kcal = round(totale_kcal / n_giorni, 1)
    detail.totale_proteine_g = round(totale_prot / n_giorni, 1)
    detail.totale_carboidrati_g = round(totale_carb / n_giorni, 1)
    detail.totale_grassi_g = round(totale_gras / n_giorni, 1)
    return detail


# ---------------------------------------------------------------------------
# PIANI — PUT /clients/{client_id}/nutrition/plans/{plan_id}
# ---------------------------------------------------------------------------


@router.put(
    "/clients/{client_id}/nutrition/plans/{plan_id}",
    response_model=NutritionPlanResponse,
)
def update_nutrition_plan(
    client_id: int,
    plan_id: int,
    data: NutritionPlanUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna metadati piano (nome, target macro, note, date, attivo)."""
    _bouncer_client(session, client_id, trainer.id)
    plan = _bouncer_plan(session, plan_id, trainer.id)

    # Se si attiva questo piano, disattiva gli altri
    if data.attivo is True and not plan.attivo:
        piani_attivi = session.exec(
            select(NutritionPlan).where(
                NutritionPlan.id_cliente == client_id,
                NutritionPlan.trainer_id == trainer.id,
                NutritionPlan.attivo == True,
                NutritionPlan.deleted_at == None,
                NutritionPlan.id != plan_id,
            )
        ).all()
        for p in piani_attivi:
            p.attivo = False
            session.add(p)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    session.add(plan)
    session.commit()
    session.refresh(plan)
    return NutritionPlanResponse.model_validate(plan)


# ---------------------------------------------------------------------------
# PIANI — DELETE /clients/{client_id}/nutrition/plans/{plan_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/clients/{client_id}/nutrition/plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_nutrition_plan(
    client_id: int,
    plan_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete piano alimentare (cascade su pasti e componenti)."""
    _bouncer_client(session, client_id, trainer.id)
    plan = _bouncer_plan(session, plan_id, trainer.id)

    now = datetime.now(timezone.utc)

    # Cascade soft-delete: componenti → pasti → piano
    meals = session.exec(
        select(PlanMeal).where(
            PlanMeal.piano_id == plan_id, PlanMeal.deleted_at == None
        )
    ).all()
    for meal in meals:
        components = session.exec(
            select(MealComponent).where(
                MealComponent.pasto_id == meal.id, MealComponent.deleted_at == None
            )
        ).all()
        for comp in components:
            comp.deleted_at = now
            session.add(comp)
        meal.deleted_at = now
        session.add(meal)

    plan.deleted_at = now
    session.add(plan)
    session.commit()


# ---------------------------------------------------------------------------
# PASTI — POST /nutrition/plans/{plan_id}/meals
# ---------------------------------------------------------------------------


@router.post(
    "/nutrition/plans/{plan_id}/meals",
    response_model=PlanMealResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meal(
    plan_id: int,
    data: PlanMealCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiunge un pasto al piano alimentare."""
    _bouncer_plan(session, plan_id, trainer.id)

    meal = PlanMeal(
        piano_id=plan_id,
        giorno_settimana=data.giorno_settimana,
        tipo_pasto=data.tipo_pasto,
        ordine=data.ordine,
        nome=data.nome,
        note=data.note,
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)

    resp = PlanMealResponse.model_validate(meal)
    resp.giorno_label = GIORNO_LABELS.get(meal.giorno_settimana)
    resp.tipo_pasto_label = TIPO_PASTO_LABELS.get(meal.tipo_pasto)
    return resp


# ---------------------------------------------------------------------------
# PASTI — PUT /nutrition/plans/{plan_id}/meals/{meal_id}
# ---------------------------------------------------------------------------


@router.put(
    "/nutrition/plans/{plan_id}/meals/{meal_id}",
    response_model=PlanMealResponse,
)
def update_meal(
    plan_id: int,
    meal_id: int,
    data: PlanMealUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna tipo, giorno, ordine o note di un pasto."""
    _bouncer_plan(session, plan_id, trainer.id)
    meal = _bouncer_meal(session, meal_id, trainer.id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(meal, key, value)

    session.add(meal)
    session.commit()
    session.refresh(meal)

    resp = PlanMealResponse.model_validate(meal)
    resp.giorno_label = GIORNO_LABELS.get(meal.giorno_settimana)
    resp.tipo_pasto_label = TIPO_PASTO_LABELS.get(meal.tipo_pasto)
    return resp


# ---------------------------------------------------------------------------
# PASTI — DELETE /nutrition/plans/{plan_id}/meals/{meal_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/nutrition/plans/{plan_id}/meals/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_meal(
    plan_id: int,
    meal_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete pasto (cascade sui componenti)."""
    _bouncer_plan(session, plan_id, trainer.id)
    meal = _bouncer_meal(session, meal_id, trainer.id)

    now = datetime.now(timezone.utc)
    components = session.exec(
        select(MealComponent).where(
            MealComponent.pasto_id == meal_id, MealComponent.deleted_at == None
        )
    ).all()
    for comp in components:
        comp.deleted_at = now
        session.add(comp)
    meal.deleted_at = now
    session.add(meal)
    session.commit()


# ---------------------------------------------------------------------------
# COMPONENTI — POST /nutrition/plans/{plan_id}/meals/{meal_id}/components
# ---------------------------------------------------------------------------


@router.post(
    "/nutrition/plans/{plan_id}/meals/{meal_id}/components",
    response_model=MealComponentDetail,
    status_code=status.HTTP_201_CREATED,
)
def add_component(
    plan_id: int,
    meal_id: int,
    data: MealComponentCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Aggiunge un alimento a un pasto con la quantita' in grammi.

    Verifica che l'alimento esista in nutrition.db prima di salvare
    (integrità applicativa per cross-DB reference).
    """
    _bouncer_plan(session, plan_id, trainer.id)
    _bouncer_meal(session, meal_id, trainer.id)

    # Verifica esistenza alimento in nutrition.db (integrità cross-DB)
    food = nutrition_session.exec(
        select(Food).where(Food.id == data.alimento_id, Food.is_active == True)
    ).first()
    if not food:
        raise HTTPException(status_code=404, detail="Alimento non trovato nel catalogo")

    cat = nutrition_session.exec(
        select(FoodCategory).where(FoodCategory.id == food.categoria_id)
    ).first()

    comp = MealComponent(
        pasto_id=meal_id,
        alimento_id=data.alimento_id,
        quantita_g=data.quantita_g,
        note=data.note,
    )
    session.add(comp)
    session.commit()
    session.refresh(comp)

    return _enrich_component(comp, food, cat.nome if cat else None)


# ---------------------------------------------------------------------------
# COMPONENTI — PUT /nutrition/plans/{plan_id}/meals/{meal_id}/components/{comp_id}
# ---------------------------------------------------------------------------


@router.put(
    "/nutrition/plans/{plan_id}/meals/{meal_id}/components/{comp_id}",
    response_model=MealComponentDetail,
)
def update_component(
    plan_id: int,
    meal_id: int,
    comp_id: int,
    data: MealComponentUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Aggiorna grammi o note di un componente pasto."""
    _bouncer_plan(session, plan_id, trainer.id)
    comp = _bouncer_component(session, comp_id, trainer.id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(comp, key, value)

    session.add(comp)
    session.commit()
    session.refresh(comp)

    food = nutrition_session.exec(
        select(Food).where(Food.id == comp.alimento_id)
    ).first()
    cat = None
    if food:
        cat = nutrition_session.exec(
            select(FoodCategory).where(FoodCategory.id == food.categoria_id)
        ).first()
    return _enrich_component(comp, food, cat.nome if cat else None)


# ---------------------------------------------------------------------------
# COMPONENTI — DELETE /nutrition/plans/{plan_id}/meals/{meal_id}/components/{comp_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/nutrition/plans/{plan_id}/meals/{meal_id}/components/{comp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component(
    plan_id: int,
    meal_id: int,
    comp_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Rimuove un alimento da un pasto (soft-delete)."""
    _bouncer_plan(session, plan_id, trainer.id)
    comp = _bouncer_component(session, comp_id, trainer.id)

    comp.deleted_at = datetime.now(timezone.utc)
    session.add(comp)
    session.commit()


# ---------------------------------------------------------------------------
# COPY DAY — POST /nutrition/plans/{plan_id}/copy-day
# ---------------------------------------------------------------------------


@router.post(
    "/nutrition/plans/{plan_id}/copy-day",
    response_model=CopyDayResult,
    status_code=status.HTTP_200_OK,
)
def copy_day(
    plan_id: int,
    data: CopyDayInput,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Copia tutti i pasti e i relativi alimenti da source_giorno a target_giorno.

    I pasti del target_giorno NON vengono cancellati — i nuovi si aggiungono.
    Utile per replicare una struttura giornaliera su piu' giorni.
    """
    _bouncer_plan(session, plan_id, trainer.id)

    if data.source_giorno == data.target_giorno:
        raise HTTPException(status_code=400, detail="source_giorno e target_giorno devono essere diversi")

    # Carica pasti sorgente (non eliminati)
    source_meals = session.exec(
        select(PlanMeal).where(
            PlanMeal.piano_id == plan_id,
            PlanMeal.giorno_settimana == data.source_giorno,
            PlanMeal.deleted_at == None,
        )
    ).all()

    pasti_copiati = 0
    componenti_copiati = 0

    for meal in source_meals:
        new_meal = PlanMeal(
            piano_id=plan_id,
            giorno_settimana=data.target_giorno,
            tipo_pasto=meal.tipo_pasto,
            ordine=meal.ordine,
            nome=meal.nome,
            note=meal.note,
        )
        session.add(new_meal)
        session.flush()  # ottieni new_meal.id senza commit

        # Carica componenti del pasto sorgente
        source_components = session.exec(
            select(MealComponent).where(
                MealComponent.pasto_id == meal.id,
                MealComponent.deleted_at == None,
            )
        ).all()

        for comp in source_components:
            new_comp = MealComponent(
                pasto_id=new_meal.id,
                alimento_id=comp.alimento_id,
                quantita_g=comp.quantita_g,
                note=comp.note,
            )
            session.add(new_comp)
            componenti_copiati += 1

        pasti_copiati += 1

    session.commit()
    return CopyDayResult(pasti_copiati=pasti_copiati, componenti_copiati=componenti_copiati)


# ---------------------------------------------------------------------------
# TEMPLATE PASTI — helper
# ---------------------------------------------------------------------------


def _enrich_template_component(
    tc: TemplateComponent,
    food: Optional[Food],
) -> TemplateComponentDetail:
    if food is None:
        return TemplateComponentDetail(
            id=tc.id, template_id=tc.template_id,
            alimento_id=tc.alimento_id, quantita_g=tc.quantita_g, note=tc.note,
        )
    return TemplateComponentDetail(
        id=tc.id, template_id=tc.template_id,
        alimento_id=tc.alimento_id,
        alimento_nome=food.nome,
        quantita_g=tc.quantita_g, note=tc.note,
        energia_kcal=round(food.energia_kcal * tc.quantita_g / 100, 1),
        proteine_g=round(food.proteine_g * tc.quantita_g / 100, 1),
        carboidrati_g=round(food.carboidrati_g * tc.quantita_g / 100, 1),
        grassi_g=round(food.grassi_g * tc.quantita_g / 100, 1),
        fibra_g=_scale_macro(food.fibra_g, tc.quantita_g),
    )


def _bouncer_template(session: Session, template_id: int, trainer_id: int) -> MealTemplate:
    tmpl = session.exec(
        select(MealTemplate).where(
            MealTemplate.id == template_id,
            MealTemplate.trainer_id == trainer_id,
            MealTemplate.deleted_at == None,
        )
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return tmpl


def _build_template_detail(
    tmpl: MealTemplate,
    session: Session,
    nutrition_session: Session,
) -> MealTemplateDetail:
    comps = session.exec(
        select(TemplateComponent).where(
            TemplateComponent.template_id == tmpl.id,
            TemplateComponent.deleted_at == None,
        )
    ).all()
    food_ids = list({c.alimento_id for c in comps})
    food_map: dict[int, Food] = {}
    if food_ids:
        foods = nutrition_session.exec(select(Food).where(Food.id.in_(food_ids))).all()
        food_map = {f.id: f for f in foods}

    enriched = [_enrich_template_component(c, food_map.get(c.alimento_id)) for c in comps]
    return MealTemplateDetail(
        id=tmpl.id, trainer_id=tmpl.trainer_id, nome=tmpl.nome,
        tipo_pasto=tmpl.tipo_pasto, created_at=tmpl.created_at,
        componenti=enriched,
        totale_kcal=round(sum(c.energia_kcal for c in enriched), 1),
        totale_proteine_g=round(sum(c.proteine_g for c in enriched), 1),
        totale_carboidrati_g=round(sum(c.carboidrati_g for c in enriched), 1),
        totale_grassi_g=round(sum(c.grassi_g for c in enriched), 1),
    )


# ---------------------------------------------------------------------------
# TEMPLATE — GET /nutrition/meal-templates
# ---------------------------------------------------------------------------


@router.get("/nutrition/meal-templates", response_model=list[MealTemplateDetail])
def list_meal_templates(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Lista tutti i template pasto del trainer con componenti arricchiti."""
    templates = session.exec(
        select(MealTemplate).where(
            MealTemplate.trainer_id == trainer.id,
            MealTemplate.deleted_at == None,
        ).order_by(MealTemplate.nome)
    ).all()
    return [_build_template_detail(t, session, nutrition_session) for t in templates]


# ---------------------------------------------------------------------------
# TEMPLATE — DELETE /nutrition/meal-templates/{template_id}
# ---------------------------------------------------------------------------


@router.delete("/nutrition/meal-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_template(
    template_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete template pasto e tutti i suoi componenti."""
    tmpl = _bouncer_template(session, template_id, trainer.id)
    now = datetime.now(timezone.utc)
    comps = session.exec(
        select(TemplateComponent).where(
            TemplateComponent.template_id == template_id,
            TemplateComponent.deleted_at == None,
        )
    ).all()
    for c in comps:
        c.deleted_at = now
        session.add(c)
    tmpl.deleted_at = now
    session.add(tmpl)
    session.commit()


# ---------------------------------------------------------------------------
# TEMPLATE — POST /nutrition/plans/{plan_id}/meals/{meal_id}/save-as-template
# ---------------------------------------------------------------------------


@router.post(
    "/nutrition/plans/{plan_id}/meals/{meal_id}/save-as-template",
    response_model=MealTemplateDetail,
    status_code=status.HTTP_201_CREATED,
)
def save_meal_as_template(
    plan_id: int,
    meal_id: int,
    data: SaveAsTemplateInput,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Salva i componenti di un pasto come template riutilizzabile."""
    _bouncer_plan(session, plan_id, trainer.id)
    meal = _bouncer_meal(session, meal_id, trainer.id)

    components = session.exec(
        select(MealComponent).where(
            MealComponent.pasto_id == meal.id,
            MealComponent.deleted_at == None,
        )
    ).all()

    tmpl = MealTemplate(
        trainer_id=trainer.id,
        nome=data.nome,
        tipo_pasto=data.tipo_pasto or meal.tipo_pasto,
    )
    session.add(tmpl)
    session.flush()

    for comp in components:
        tc = TemplateComponent(
            template_id=tmpl.id,
            alimento_id=comp.alimento_id,
            quantita_g=comp.quantita_g,
            note=comp.note,
        )
        session.add(tc)

    session.commit()
    session.refresh(tmpl)
    return _build_template_detail(tmpl, session, nutrition_session)


# ---------------------------------------------------------------------------
# TEMPLATE — POST /nutrition/plans/{plan_id}/meals/{meal_id}/apply-template/{template_id}
# ---------------------------------------------------------------------------


@router.post(
    "/nutrition/plans/{plan_id}/meals/{meal_id}/apply-template/{template_id}",
    response_model=ApplyTemplateResult,
)
def apply_template_to_meal(
    plan_id: int,
    meal_id: int,
    template_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Applica un template a un pasto: aggiunge i componenti del template al pasto.

    Operazione ADDITIVA — non svuota il pasto prima.
    Verifica cross-DB che ogni alimento del template esista in nutrition.db.
    """
    _bouncer_plan(session, plan_id, trainer.id)
    _bouncer_meal(session, meal_id, trainer.id)
    tmpl = _bouncer_template(session, template_id, trainer.id)

    tc_list = session.exec(
        select(TemplateComponent).where(
            TemplateComponent.template_id == tmpl.id,
            TemplateComponent.deleted_at == None,
        )
    ).all()

    # Batch verifica alimenti in nutrition.db
    food_ids = list({tc.alimento_id for tc in tc_list})
    if food_ids:
        foods = nutrition_session.exec(select(Food).where(Food.id.in_(food_ids))).all()
        valid_ids = {f.id for f in foods}
    else:
        valid_ids = set()

    count = 0
    for tc in tc_list:
        if tc.alimento_id not in valid_ids:
            continue   # alimento rimosso dal catalogo — skip silenzioso
        comp = MealComponent(
            pasto_id=meal_id,
            alimento_id=tc.alimento_id,
            quantita_g=tc.quantita_g,
            note=tc.note,
        )
        session.add(comp)
        count += 1

    session.commit()
    return ApplyTemplateResult(componenti_aggiunti=count)


# ---------------------------------------------------------------------------
# PIANO TEMPLATE (nutrition.db)
# GET  /nutrition/plan-templates          — lista template da DB
# POST /nutrition/plans/from-template     — crea piano con pasti da template
# ---------------------------------------------------------------------------


@router.get("/nutrition/plan-templates", response_model=list[PlanTemplateItem])
def list_plan_templates(
    _trainer: Trainer = Depends(get_current_trainer),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """Lista dei template piano da nutrition.db, arricchiti con meal_count."""
    templates = nutrition_session.exec(
        select(PlanTemplate).where(PlanTemplate.is_active == True)
    ).all()

    if not templates:
        return []

    # Batch count meals per template (anti N+1)
    tmpl_ids = [t.id for t in templates]
    meal_counts = nutrition_session.exec(
        select(
            TemplatePlanMeal.template_id,
            func.count(TemplatePlanMeal.id).label("cnt"),
        )
        .where(TemplatePlanMeal.template_id.in_(tmpl_ids))
        .group_by(TemplatePlanMeal.template_id)
    ).all()
    count_map = {row[0]: row[1] for row in meal_counts}

    result = []
    for t in templates:
        item = PlanTemplateItem.model_validate(t)
        item.meal_count = count_map.get(t.id, 0)
        item.has_meals = item.meal_count > 0
        result.append(item)

    return result


@router.post(
    "/nutrition/plans/from-template",
    response_model=NutritionPlanResponse,
    status_code=201,
)
def create_plan_from_template(
    body: CreateFromTemplateInput,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    nutrition_session: Session = Depends(get_nutrition_session),
):
    """
    Crea un piano alimentare da un template DB.

    Se il template ha pasti (has_meals), vengono copiati nel piano.
    """
    tmpl = nutrition_session.exec(
        select(PlanTemplate).where(
            PlanTemplate.id == body.template_id,
            PlanTemplate.is_active == True,
        )
    ).first()
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Template non trovato")

    # Verifica che il cliente appartenga al trainer (Relational IDOR)
    _bouncer_client(session, body.id_cliente, trainer.id)

    plan = NutritionPlan(
        trainer_id=trainer.id,
        id_cliente=body.id_cliente,
        nome=body.nome,
        obiettivo_calorico=tmpl.obiettivo_calorico,
        proteine_g_target=tmpl.proteine_g_target,
        carboidrati_g_target=tmpl.carboidrati_g_target,
        grassi_g_target=tmpl.grassi_g_target,
        note_cliniche=tmpl.note_cliniche,
        data_inizio=body.data_inizio,
        attivo=body.attivo,
    )

    # Se attivo=True, disattiva gli altri piani dello stesso cliente
    if body.attivo:
        for existing in session.exec(
            select(NutritionPlan).where(
                NutritionPlan.trainer_id == trainer.id,
                NutritionPlan.id_cliente == body.id_cliente,
                NutritionPlan.attivo == True,
                NutritionPlan.deleted_at == None,
            )
        ).all():
            existing.attivo = False
            session.add(existing)

    session.add(plan)
    session.flush()  # get plan.id

    # Fetch template meals + components in batch
    tmpl_meals = nutrition_session.exec(
        select(TemplatePlanMeal)
        .where(TemplatePlanMeal.template_id == tmpl.id)
        .order_by(TemplatePlanMeal.giorno_settimana, TemplatePlanMeal.ordine)
    ).all()

    if tmpl_meals:
        meal_ids = [m.id for m in tmpl_meals]
        tmpl_components = nutrition_session.exec(
            select(TemplatePlanComponent)
            .where(TemplatePlanComponent.meal_id.in_(meal_ids))
        ).all()
        comp_by_meal: dict[int, list] = {}
        for c in tmpl_components:
            comp_by_meal.setdefault(c.meal_id, []).append(c)

        for tmpl_meal in tmpl_meals:
            meal = PlanMeal(
                piano_id=plan.id,
                giorno_settimana=tmpl_meal.giorno_settimana,
                tipo_pasto=tmpl_meal.tipo_pasto,
                ordine=tmpl_meal.ordine,
                nome=tmpl_meal.nome,
                note=tmpl_meal.note,
            )
            session.add(meal)
            session.flush()  # get meal.id

            for tc in comp_by_meal.get(tmpl_meal.id, []):
                comp = MealComponent(
                    pasto_id=meal.id,
                    alimento_id=tc.alimento_id,
                    quantita_g=tc.quantita_g,
                    note=tc.note,
                )
                session.add(comp)

    session.commit()
    session.refresh(plan)
    logger.info(
        "Piano creato da template '%s' (id=%d) per cliente %d (trainer %d), %d pasti copiati",
        tmpl.slug,
        tmpl.id,
        body.id_cliente,
        trainer.id,
        len(tmpl_meals) if tmpl_meals else 0,
    )
    return NutritionPlanResponse.model_validate(plan)
