# api/services/workout_copilot.py
"""
Copilot AI per il workout builder — agente conversazionale.

Due modalita':
1. suggest_next_exercise() — suggerimento rapido 3 esercizi (button click)
2. handle_chat() — agente conversazionale con intent routing

Pipeline chat:
  message → route_intent() → capability dispatcher → Ollama → parse → response

8 intent supportati:
- suggest: suggerisci esercizi
- analyze: analisi strutturale scheda
- chat: conversazione libera contestuale
- explain: spiega un esercizio (skeleton)
- search: cerca esercizio per criterio (skeleton)
- swap: proponi sostituzione (skeleton)
- modify: modifica parametri (skeleton)
- review: revisione sessione (skeleton)

Privacy-first: nessun dato personale nel prompt Ollama.
"""

import json
import logging
import re
from typing import Optional

from sqlmodel import Session, select, or_

from api.models.client import Client
from api.models.exercise import Exercise
from api.models.workout import WorkoutPlan
from api.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotActionAddExercise,
    ChatWorkoutState,
)
from api.services.ollama_client import (
    call_ollama,
    parse_json_field,
    format_anamnesi_for_prompt,
)

logger = logging.getLogger("fitmanager.services.copilot")

# ═══════════════════════════════════════════════════════════
# COSTANTI
# ═══════════════════════════════════════════════════════════

SECTION_CATEGORIES: dict[str, list[str]] = {
    "avviamento": ["avviamento"],
    "principale": ["compound", "isolation", "bodyweight", "cardio"],
    "stretching": ["stretching", "mobilita"],
}

# Piano livello → difficolta' esercizi ammesse
DIFFICULTY_CEILING: dict[str, list[str]] = {
    "beginner": ["beginner"],
    "intermedio": ["beginner", "intermediate"],
    "avanzato": ["beginner", "intermediate", "advanced"],
}

FUNDAMENTAL_PATTERNS = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v"}
COMPLEMENTARY_PATTERNS = {"core", "rotation", "carry"}

PATTERN_LABELS_IT = {
    "squat": "Squat",
    "hinge": "Hinge (stacco/hip hinge)",
    "push_h": "Push orizzontale (panca, push-up)",
    "push_v": "Push verticale (military, shoulder press)",
    "pull_h": "Pull orizzontale (rematore)",
    "pull_v": "Pull verticale (lat machine, trazioni)",
    "core": "Core",
    "rotation": "Rotazione/anti-rotazione",
    "carry": "Carry/trasporto",
}

MAX_CANDIDATES = 30

# ═══════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════

SYSTEM_SUGGEST = """\
Sei un personal trainer con laurea in scienze motorie e certificazione NSCA-CSCS.
Il tuo collega sta costruendo una scheda allenamento e ti chiede un consiglio \
sul prossimo esercizio da inserire.

REGOLE:
1. Rispondi SOLO con un JSON array valido, NESSUN testo prima o dopo
2. Il JSON deve contenere esattamente 3 oggetti con: "exercise_id" (int) e "reasoning" (string)
3. Scegli SOLO tra gli ID della lista CANDIDATI fornita
4. Il reasoning deve essere 1-2 frasi in italiano, da collega esperto
5. Priorita' di scelta:
   - Pattern di movimento mancanti nella sessione (se indicati)
   - Complementarita' muscolare con esercizi gia' presenti
   - Varieta' di attrezzatura
   - Adeguatezza al livello e obiettivo
6. Se ci sono controindicazioni dal profilo cliente, evita esercizi problematici

Formato risposta ESATTO:
[{"exercise_id": 42, "reasoning": "..."}, {"exercise_id": 15, "reasoning": "..."}, {"exercise_id": 88, "reasoning": "..."}]"""


SYSTEM_CHAT = """\
Sei un personal trainer con laurea in scienze motorie e certificazione NSCA-CSCS.
Stai aiutando un collega a costruire una scheda allenamento tramite chat.

REGOLE:
1. Rispondi SEMPRE con un JSON valido con questa struttura:
   {"message": "...", "actions": [...], "context_notes_update": [...]}
2. "message": risposta in italiano, 2-5 frasi, tono da collega esperto.
   Usa formattazione pulita (no markdown pesante, solo testo scorrevole).
3. "actions": array di azioni proposte (puo' essere vuoto).
   Ogni azione: {"type": "add_exercise", "exercise_id": int, "label": "testo bottone", "reasoning": "1 frase"}
   SOLO exercise_id dalla lista CANDIDATI se fornita. Ometti se non pertinente.
4. "context_notes_update": array di stringhe con preferenze/note estraibili dal messaggio.
   Es. se dice "odia i bilancieri" → ["Preferisce evitare bilancieri"].
   Array vuoto se nessuna nota estraibile.
5. Non inventare esercizi. Se servono candidati e non sono forniti, rispondi testualmente.
6. Se ci sono controindicazioni dall'anamnesi, menzionale."""


SYSTEM_ANALYZE = """\
Sei un personal trainer con laurea in scienze motorie e certificazione NSCA-CSCS.
Stai facendo una revisione strutturale della scheda di un collega.

REGOLE:
1. Rispondi con un JSON valido: {"message": "...", "actions": [...], "context_notes_update": []}
2. "message": analisi strutturata in italiano, 3-6 frasi. Includi:
   - Punti di forza (pattern, bilanciamento, progressione)
   - Punti deboli (lacune, sbilanciamenti, problemi di volume)
   - 1-2 suggerimenti concreti
3. "actions": se hai candidati, proponi 1-2 esercizi per colmare le lacune.
   {"type": "add_exercise", "exercise_id": int, "label": "...", "reasoning": "..."}
4. Sii diretto e specifico, evita generalita'. Fai riferimento a esercizi per nome."""


SYSTEM_SUGGEST_CHAT = """\
Sei un personal trainer con laurea in scienze motorie e certificazione NSCA-CSCS.
Il tuo collega chiede suggerimenti per la scheda tramite chat.

REGOLE:
1. Rispondi con un JSON valido: {"message": "...", "actions": [...], "context_notes_update": []}
2. "message": spiega brevemente perche' suggerisci questi esercizi (2-3 frasi, italiano).
3. "actions": array di 2-3 suggerimenti dalla lista CANDIDATI.
   {"type": "add_exercise", "exercise_id": int, "label": "Aggiungi [nome]", "reasoning": "1 frase"}
   SOLO ID dalla lista CANDIDATI.
4. Considera il messaggio del collega per personalizzare la scelta."""


SYSTEM_INTENT = """\
Classifica l'intento del seguente messaggio di un personal trainer che sta costruendo una scheda.
Rispondi con UNA SOLA parola tra: suggest, analyze, explain, search, swap, modify, review, chat"""


# ═══════════════════════════════════════════════════════════
# INTENT ROUTING
# ═══════════════════════════════════════════════════════════

# Keyword patterns → intent (ordine: piu' specifico prima)
INTENT_KEYWORDS: list[tuple[list[str], str]] = [
    # suggest
    (["sugger", "consiglia", "proponi", "aggiungi un", "cosa metto",
      "quale esercizio", "prossimo esercizio", "manca un"], "suggest"),
    # analyze
    (["analiz", "valuta", "rivedi", "come va", "bilanciata", "bilanciamento",
      "struttura", "revisione", "bilancio", "che ne pensi"], "analyze"),
    # explain
    (["spiega", "spiegami", "come si fa", "come si esegue",
      "a cosa serve", "differenza tra"], "explain"),
    # search
    (["cerca", "trova", "esiste un", "conosci un", "alternativa a",
      "esercizio per", "esercizio con"], "search"),
    # swap
    (["sostituisci", "scambia", "cambia", "rimpiazza",
      "al posto di", "invece di"], "swap"),
    # modify
    (["modifica", "aumenta", "diminuisci", "cambia serie",
      "cambia ripetizioni", "cambia riposo", "troppe serie",
      "poche serie", "troppo riposo"], "modify"),
    # review
    (["controlla", "verifica", "problemi", "errori",
      "qualcosa che non va"], "review"),
    # chat (preferenze/informazioni, priorita' bassa)
    (["odia", "preferisce", "non gli piace", "ama usare",
      "gli piace", "vuole solo", "evita", "ha paura"], "chat"),
]


def route_intent(message: str, use_ollama_fallback: bool = True) -> str:
    """
    Classifica l'intento del messaggio del PT.

    Strategia a 2 livelli:
    1. Keyword match (deterministico, ~0ms)
    2. Fallback Ollama (prompt minimale, ~3s) — solo se nessun keyword match

    Ritorna: "suggest" | "analyze" | "explain" | "search" | "swap" |
             "modify" | "review" | "chat"
    """
    msg_lower = message.lower().strip()

    # Fase 1: keyword match
    for keywords, intent in INTENT_KEYWORDS:
        for kw in keywords:
            if kw in msg_lower:
                logger.debug("Intent keyword match: '%s' → %s", kw, intent)
                return intent

    # Fase 2: Ollama fallback per casi ambigui
    if use_ollama_fallback:
        try:
            raw = call_ollama(SYSTEM_INTENT, message, num_predict=16)
            intent = raw.strip().lower().split()[0] if raw.strip() else "chat"
            valid_intents = {
                "suggest", "analyze", "explain", "search",
                "swap", "modify", "review", "chat",
            }
            if intent in valid_intents:
                logger.debug("Intent Ollama: %s", intent)
                return intent
            logger.debug("Intent Ollama invalido '%s', fallback chat", intent)
        except RuntimeError:
            logger.debug("Intent Ollama fallback failed, defaulting to chat")

    return "chat"


# ═══════════════════════════════════════════════════════════
# CANDIDATE QUERY (usato da suggest e suggest-chat)
# ═══════════════════════════════════════════════════════════


def _get_current_patterns(
    session: Session, exercise_ids: list[int],
) -> tuple[set[str], dict[str, list[str]]]:
    """
    Analizza gli esercizi gia' nella sessione.
    Ritorna: (patterns usati, {pattern: [nomi esercizi]}).
    """
    if not exercise_ids:
        return set(), {}

    exercises = session.exec(
        select(Exercise).where(Exercise.id.in_(exercise_ids))
    ).all()

    patterns: set[str] = set()
    pattern_exercises: dict[str, list[str]] = {}
    for ex in exercises:
        p = ex.pattern_movimento
        patterns.add(p)
        pattern_exercises.setdefault(p, []).append(ex.nome)

    return patterns, pattern_exercises


def _query_candidates(
    session: Session,
    sezione: str,
    livello: str,
    exclude_ids: list[int],
    missing_patterns: set[str],
    trainer_id: int,
) -> list[Exercise]:
    """
    Query SQL pre-filtraggio candidati. Target: ~30 esercizi.

    Strategia a 2 fasi:
    1. Priorita' alta: esercizi con pattern mancanti
    2. Riempimento: altri esercizi della stessa categoria fino a MAX_CANDIDATES
    """
    categories = SECTION_CATEGORIES.get(sezione, SECTION_CATEGORIES["principale"])
    allowed_diff = DIFFICULTY_CEILING.get(livello, DIFFICULTY_CEILING["avanzato"])

    # Filtri base comuni
    base_filters = [
        Exercise.deleted_at == None,
        Exercise.categoria.in_(categories),
        Exercise.difficolta.in_(allowed_diff),
        or_(Exercise.trainer_id == None, Exercise.trainer_id == trainer_id),
        Exercise.in_subset == True,  # noqa: E712 — subset attivo
    ]
    if exclude_ids:
        base_filters.append(Exercise.id.notin_(exclude_ids))

    candidates: list[Exercise] = []
    seen_ids: set[int] = set()

    # Fase 1: pattern mancanti (solo per sezione principale)
    if missing_patterns and sezione == "principale":
        priority = session.exec(
            select(Exercise)
            .where(*base_filters, Exercise.pattern_movimento.in_(missing_patterns))
            .limit(MAX_CANDIDATES)
        ).all()
        for ex in priority:
            if ex.id not in seen_ids:
                candidates.append(ex)
                seen_ids.add(ex.id)

    # Fase 2: riempimento fino a MAX_CANDIDATES
    remaining = MAX_CANDIDATES - len(candidates)
    if remaining > 0:
        filler = session.exec(
            select(Exercise)
            .where(*base_filters)
            .limit(remaining + len(seen_ids))
        ).all()
        for ex in filler:
            if ex.id not in seen_ids:
                candidates.append(ex)
                seen_ids.add(ex.id)
                if len(candidates) >= MAX_CANDIDATES:
                    break

    return candidates


# ═══════════════════════════════════════════════════════════
# PROMPT BUILDING — SUGGEST (button endpoint)
# ═══════════════════════════════════════════════════════════


def _format_candidate_compact(ex: Exercise) -> str:
    """Formato compatto per prompt: 1 riga per candidato."""
    muscoli = parse_json_field(ex.muscoli_primari)
    muscles_str = ",".join(muscoli[:3]) if muscoli else "-"
    return f"{ex.id}|{ex.nome}|{ex.pattern_movimento}|{muscles_str}|{ex.attrezzatura}|{ex.difficolta}"


def _build_suggest_prompt(
    plan: WorkoutPlan,
    sezione: str,
    current_patterns: set[str],
    pattern_exercises: dict[str, list[str]],
    missing_patterns: set[str],
    candidates: list[Exercise],
    anamnesi: Optional[dict],
    focus_muscolare: Optional[str],
) -> str:
    """Costruisce il prompt utente per suggest_next_exercise."""
    lines: list[str] = []

    # Contesto scheda
    lines.append(f"SCHEDA: {plan.nome}")
    lines.append(f"Obiettivo: {plan.obiettivo} | Livello: {plan.livello}")
    lines.append(f"Sezione: {sezione.upper()}")
    if focus_muscolare:
        lines.append(f"Focus sessione: {focus_muscolare}")

    # Esercizi gia' presenti
    if pattern_exercises:
        lines.append("\nGIA' IN SESSIONE:")
        for pattern, nomi in pattern_exercises.items():
            label = PATTERN_LABELS_IT.get(pattern, pattern)
            lines.append(f"  {label}: {', '.join(nomi)}")

    # Pattern analysis (solo per principale)
    if sezione == "principale":
        if missing_patterns:
            labels = [PATTERN_LABELS_IT.get(p, p) for p in sorted(missing_patterns)]
            lines.append(f"\nPATTERN MANCANTI: {', '.join(labels)}")
            lines.append("→ Dai priorita' a esercizi che coprono questi pattern")
        elif current_patterns:
            lines.append("\nTutti i pattern fondamentali sono coperti.")

    # Anamnesi (se disponibile)
    if anamnesi:
        lines.append(f"\nPROFILO CLIENTE:")
        lines.append(format_anamnesi_for_prompt(anamnesi))

    # Candidati (formato compatto)
    lines.append(f"\nCANDIDATI ({len(candidates)}):")
    lines.append("ID|Nome|Pattern|Muscoli|Attrezzatura|Difficolta")
    for ex in candidates:
        lines.append(_format_candidate_compact(ex))

    lines.append("\nScegli i 3 migliori. Rispondi SOLO con il JSON array.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# PROMPT BUILDING — CHAT (conversazionale)
# ═══════════════════════════════════════════════════════════


def _format_workout_state(state: ChatWorkoutState) -> str:
    """Serializza workout state dal frontend per il prompt."""
    if not state.sessions:
        return "Scheda vuota (nessuna sessione)."

    lines: list[str] = []
    for i, sess in enumerate(state.sessions, 1):
        focus = f" ({sess.focus})" if sess.focus else ""
        lines.append(f"Sessione {i}: {sess.nome}{focus}")
        if not sess.exercises:
            lines.append("  (vuota)")
            continue
        for ex in sess.exercises:
            lines.append(
                f"  - {ex.nome} [{ex.pattern}] {ex.serie}x{ex.ripetizioni} "
                f"riposo {ex.riposo}s ({ex.sezione})"
            )
    return "\n".join(lines)


def _format_conversation(
    history: list, message: str, max_turns: int = 6,
) -> str:
    """Formatta gli ultimi N messaggi + il messaggio corrente."""
    lines: list[str] = []
    recent = history[-max_turns:] if len(history) > max_turns else history
    for msg in recent:
        role = "PT" if msg.role == "user" else "Copilot"
        lines.append(f"{role}: {msg.content}")
    lines.append(f"PT: {message}")
    return "\n".join(lines)


def _build_chat_prompt(
    plan: WorkoutPlan,
    workout_state: ChatWorkoutState,
    anamnesi: Optional[dict],
    context_notes: list[str],
    conversation: str,
    extra_context: str = "",
) -> str:
    """Prompt base per tutte le capability conversazionali."""
    lines: list[str] = []

    lines.append(f"SCHEDA: {plan.nome}")
    lines.append(f"Obiettivo: {plan.obiettivo} | Livello: {plan.livello}")

    lines.append(f"\nSTATO SESSIONI:")
    lines.append(_format_workout_state(workout_state))

    if anamnesi:
        lines.append(f"\nPROFILO CLIENTE:")
        lines.append(format_anamnesi_for_prompt(anamnesi))

    if context_notes:
        lines.append(f"\nNOTE CONTESTO:")
        for note in context_notes[:10]:
            lines.append(f"- {note}")

    if extra_context:
        lines.append(f"\n{extra_context}")

    lines.append(f"\nCONVERSAZIONE:")
    lines.append(conversation)

    lines.append("\nRispondi con il JSON richiesto.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# RESPONSE PARSING
# ═══════════════════════════════════════════════════════════


def _parse_suggestions(
    raw: str, candidate_map: dict[int, Exercise],
) -> list[dict]:
    """
    Parsa la risposta Ollama e valida gli ID.
    Ritorna lista di {exercise_id, nome, reasoning}.
    """
    # Estrai JSON dall'output (Ollama a volte aggiunge testo attorno)
    text = raw.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        logger.warning("Risposta Ollama senza JSON array: %s", text[:200])
        return []

    json_str = text[start:end + 1]

    # Ollama a volte inserisce newline dentro le stringhe JSON → invalida.
    # Pulizia: sostituisci newline reali con spazio (solo dentro valori stringa).
    json_str = re.sub(r'(?<=\w)\n(?=\s*\w)', ' ', json_str)

    try:
        items = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("JSON parse fallito: %s", json_str[:200])
        return []

    suggestions: list[dict] = []
    seen_ids: set[int] = set()

    for item in items:
        if not isinstance(item, dict):
            continue
        eid = item.get("exercise_id")
        reasoning = item.get("reasoning", "")

        # Valida: ID deve essere tra i candidati e non duplicato
        if eid not in candidate_map or eid in seen_ids:
            continue

        ex = candidate_map[eid]
        suggestions.append({
            "exercise_id": eid,
            "nome": ex.nome,
            "categoria": ex.categoria,
            "pattern_movimento": ex.pattern_movimento,
            "attrezzatura": ex.attrezzatura,
            "muscoli_primari": parse_json_field(ex.muscoli_primari),
            "reasoning": str(reasoning),
        })
        seen_ids.add(eid)

        if len(suggestions) >= 3:
            break

    return suggestions


def _parse_chat_response(raw: str) -> dict:
    """
    Parsa risposta JSON da Ollama per capability conversazionali.
    Ritorna dict con message, actions, context_notes_update.
    Fallback graceful se il JSON e' malformato.
    """
    text = raw.strip()

    # Cerca il JSON object nella risposta
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        # Fallback: tratta tutta la risposta come messaggio testuale
        return {"message": text[:500], "actions": [], "context_notes_update": []}

    json_str = text[start:end + 1]
    json_str = re.sub(r'(?<=\w)\n(?=\s*\w)', ' ', json_str)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("Chat JSON parse fallito: %s", json_str[:300])
        # Fallback: estrai messaggio dal testo grezzo
        return {"message": text[:500], "actions": [], "context_notes_update": []}

    if not isinstance(data, dict):
        return {"message": str(data)[:500], "actions": [], "context_notes_update": []}

    return {
        "message": str(data.get("message", ""))[:1000],
        "actions": data.get("actions", []) if isinstance(data.get("actions"), list) else [],
        "context_notes_update": (
            data.get("context_notes_update", [])
            if isinstance(data.get("context_notes_update"), list)
            else []
        ),
    }


# ═══════════════════════════════════════════════════════════
# STRUCTURAL ANALYSIS (deterministico, usato da analyze)
# ═══════════════════════════════════════════════════════════


def _analyze_workout_structure(state: ChatWorkoutState) -> str:
    """
    Analisi strutturale deterministica della scheda.
    Genera un report compatto per il prompt Ollama.
    """
    all_exercises = []
    for sess in state.sessions:
        all_exercises.extend(sess.exercises)

    if not all_exercises:
        return "La scheda e' vuota."

    # Pattern coverage
    patterns = {ex.pattern for ex in all_exercises}
    fundamental_present = patterns & FUNDAMENTAL_PATTERNS
    fundamental_missing = FUNDAMENTAL_PATTERNS - patterns
    complementary_present = patterns & COMPLEMENTARY_PATTERNS

    # Push/Pull ratio
    push_count = sum(1 for ex in all_exercises if ex.pattern in ("push_h", "push_v"))
    pull_count = sum(1 for ex in all_exercises if ex.pattern in ("pull_h", "pull_v"))

    # Volume per sessione
    session_volumes = []
    for sess in state.sessions:
        total_sets = sum(ex.serie for ex in sess.exercises)
        session_volumes.append(f"{sess.nome}: {total_sets} serie, {len(sess.exercises)} esercizi")

    lines: list[str] = [
        f"Esercizi totali: {len(all_exercises)} in {len(state.sessions)} sessioni",
        f"Pattern fondamentali: {len(fundamental_present)}/6",
    ]

    if fundamental_missing:
        labels = [PATTERN_LABELS_IT.get(p, p) for p in sorted(fundamental_missing)]
        lines.append(f"MANCANTI: {', '.join(labels)}")

    if complementary_present:
        labels = [PATTERN_LABELS_IT.get(p, p) for p in sorted(complementary_present)]
        lines.append(f"Complementari: {', '.join(labels)}")

    lines.append(f"Push/Pull: {push_count}/{pull_count}")

    for vol in session_volumes:
        lines.append(f"  {vol}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# CAPABILITIES
# ═══════════════════════════════════════════════════════════


def _cap_suggest(
    db: Session,
    plan: WorkoutPlan,
    request: CopilotChatRequest,
    anamnesi: Optional[dict],
    trainer_id: int,
) -> CopilotChatResponse:
    """Capability SUGGEST: suggerisci esercizi via chat."""
    # Raccogli tutti gli exercise_id dal workout state
    all_exercise_ids = []
    for sess in request.workout_state.sessions:
        all_exercise_ids.extend(ex.id for ex in sess.exercises)

    # Query candidati (sezione principale di default)
    current_patterns = {ex.pattern for sess in request.workout_state.sessions
                        for ex in sess.exercises}
    missing_patterns = FUNDAMENTAL_PATTERNS - current_patterns

    candidates = _query_candidates(
        session=db,
        sezione="principale",
        livello=plan.livello,
        exclude_ids=all_exercise_ids,
        missing_patterns=missing_patterns,
        trainer_id=trainer_id,
    )

    if not candidates:
        return CopilotChatResponse(
            message="Non ho trovato candidati adatti. Prova a specificare una sezione o un pattern.",
            intent="suggest",
        )

    candidate_map = {ex.id: ex for ex in candidates}

    # Prompt con candidati
    cand_lines = ["ID|Nome|Pattern|Muscoli|Attrezzatura|Difficolta"]
    for ex in candidates[:20]:  # limita per token budget
        cand_lines.append(_format_candidate_compact(ex))

    conversation = _format_conversation(
        request.conversation_history, request.message,
    )

    prompt = _build_chat_prompt(
        plan=plan,
        workout_state=request.workout_state,
        anamnesi=anamnesi,
        context_notes=request.context_notes,
        conversation=conversation,
        extra_context=f"CANDIDATI ({len(candidates)}):\n" + "\n".join(cand_lines),
    )

    raw = call_ollama(SYSTEM_SUGGEST_CHAT, prompt, num_predict=600)
    parsed = _parse_chat_response(raw)

    # Valida e arricchisci le azioni con dati dal DB
    actions = _validate_add_actions(parsed.get("actions", []), candidate_map)

    return CopilotChatResponse(
        message=parsed["message"] or "Ecco i miei suggerimenti.",
        actions=actions,
        context_notes_update=[str(n) for n in parsed.get("context_notes_update", [])],
        intent="suggest",
    )


def _cap_analyze(
    db: Session,
    plan: WorkoutPlan,
    request: CopilotChatRequest,
    anamnesi: Optional[dict],
    trainer_id: int,
) -> CopilotChatResponse:
    """Capability ANALYZE: analisi strutturale della scheda."""
    structure = _analyze_workout_structure(request.workout_state)

    # Query candidati per colmare lacune (opzionale)
    all_exercise_ids = []
    for sess in request.workout_state.sessions:
        all_exercise_ids.extend(ex.id for ex in sess.exercises)

    current_patterns = {ex.pattern for sess in request.workout_state.sessions
                        for ex in sess.exercises}
    missing_patterns = FUNDAMENTAL_PATTERNS - current_patterns

    candidates = _query_candidates(
        session=db,
        sezione="principale",
        livello=plan.livello,
        exclude_ids=all_exercise_ids,
        missing_patterns=missing_patterns,
        trainer_id=trainer_id,
    )

    candidate_map = {ex.id: ex for ex in candidates}

    extra = f"ANALISI STRUTTURALE:\n{structure}"
    if candidates:
        cand_lines = ["ID|Nome|Pattern|Muscoli|Attrezzatura|Difficolta"]
        for ex in candidates[:15]:
            cand_lines.append(_format_candidate_compact(ex))
        extra += f"\n\nCANDIDATI PER COLMARE LACUNE ({len(candidates)}):\n" + "\n".join(cand_lines)

    conversation = _format_conversation(
        request.conversation_history, request.message,
    )

    prompt = _build_chat_prompt(
        plan=plan,
        workout_state=request.workout_state,
        anamnesi=anamnesi,
        context_notes=request.context_notes,
        conversation=conversation,
        extra_context=extra,
    )

    raw = call_ollama(SYSTEM_ANALYZE, prompt, num_predict=800)
    parsed = _parse_chat_response(raw)

    actions = _validate_add_actions(parsed.get("actions", []), candidate_map)

    return CopilotChatResponse(
        message=parsed["message"] or "Non sono riuscito a generare un'analisi. Riprova.",
        actions=actions,
        context_notes_update=[str(n) for n in parsed.get("context_notes_update", [])],
        intent="analyze",
    )


def _cap_chat(
    db: Session,
    plan: WorkoutPlan,
    request: CopilotChatRequest,
    anamnesi: Optional[dict],
    trainer_id: int,
) -> CopilotChatResponse:
    """Capability CHAT: conversazione libera contestuale."""
    conversation = _format_conversation(
        request.conversation_history, request.message,
    )

    prompt = _build_chat_prompt(
        plan=plan,
        workout_state=request.workout_state,
        anamnesi=anamnesi,
        context_notes=request.context_notes,
        conversation=conversation,
    )

    raw = call_ollama(SYSTEM_CHAT, prompt, num_predict=512)
    parsed = _parse_chat_response(raw)

    return CopilotChatResponse(
        message=parsed["message"] or "Non ho capito bene. Puoi riformulare?",
        actions=[],  # Chat libera non genera azioni
        context_notes_update=[str(n) for n in parsed.get("context_notes_update", [])],
        intent="chat",
    )


# ── Skeleton capabilities ──

def _cap_skeleton(intent: str) -> CopilotChatResponse:
    """Placeholder per capability non ancora implementate."""
    labels = {
        "explain": "Spiegazione esercizi",
        "search": "Ricerca esercizi",
        "swap": "Sostituzione esercizi",
        "modify": "Modifica parametri",
        "review": "Revisione sessione",
    }
    label = labels.get(intent, intent)
    return CopilotChatResponse(
        message=(
            f"La funzionalita' \"{label}\" sara' disponibile a breve. "
            "Per ora puoi chiedermi suggerimenti per esercizi o un'analisi della scheda."
        ),
        intent=intent,
    )


# ═══════════════════════════════════════════════════════════
# ACTION VALIDATION
# ═══════════════════════════════════════════════════════════


def _validate_add_actions(
    raw_actions: list, candidate_map: dict[int, Exercise],
) -> list[CopilotActionAddExercise]:
    """
    Valida e arricchisce le azioni add_exercise dalla risposta Ollama.
    Solo ID presenti in candidate_map vengono accettati.
    """
    validated: list[CopilotActionAddExercise] = []
    seen_ids: set[int] = set()

    for action in raw_actions:
        if not isinstance(action, dict):
            continue
        if action.get("type") != "add_exercise":
            continue

        eid = action.get("exercise_id")
        if not isinstance(eid, int) or eid not in candidate_map or eid in seen_ids:
            continue

        ex = candidate_map[eid]
        muscoli = parse_json_field(ex.muscoli_primari)

        # Dedurre sezione dalla categoria
        sezione = "principale"
        cat = ex.categoria
        if cat == "avviamento":
            sezione = "avviamento"
        elif cat in ("stretching", "mobilita"):
            sezione = "stretching"

        validated.append(CopilotActionAddExercise(
            exercise_id=eid,
            nome=ex.nome,
            categoria=ex.categoria,
            pattern_movimento=ex.pattern_movimento,
            attrezzatura=ex.attrezzatura,
            muscoli_primari=muscoli,
            sezione=sezione,
            label=str(action.get("label", f"Aggiungi {ex.nome}"))[:80],
            reasoning=str(action.get("reasoning", ""))[:200],
        ))
        seen_ids.add(eid)

        if len(validated) >= 3:
            break

    return validated


# ═══════════════════════════════════════════════════════════
# PUBLIC API — SUGGEST (button endpoint, backward compatible)
# ═══════════════════════════════════════════════════════════


def suggest_next_exercise(
    session: Session,
    plan: WorkoutPlan,
    sezione: str,
    current_exercise_ids: list[int],
    trainer_id: int,
    focus_muscolare: Optional[str] = None,
) -> list[dict]:
    """
    Suggerisce 3 esercizi per la sessione corrente.

    Pipeline:
    1. Analizza pattern gia' coperti
    2. Query SQL candidati pre-filtrati (~30 max)
    3. Prompt compatto → Ollama gemma2:9b
    4. Parse + valida risposta
    5. Ritorna [{exercise_id, nome, categoria, pattern, attrezzatura, muscoli, reasoning}]

    Raises:
        ValueError: se sezione non valida o zero candidati
        RuntimeError: se Ollama non risponde (propagato da call_ollama)
    """
    if sezione not in SECTION_CATEGORIES:
        raise ValueError(
            f"Sezione non valida: '{sezione}'. "
            f"Valide: {sorted(SECTION_CATEGORIES.keys())}"
        )

    # 1. Analizza cosa c'e' gia' nella sessione
    current_patterns, pattern_exercises = _get_current_patterns(
        session, current_exercise_ids,
    )

    # 2. Calcola pattern mancanti (solo per principale)
    missing_patterns: set[str] = set()
    if sezione == "principale":
        missing_patterns = FUNDAMENTAL_PATTERNS - current_patterns

    # 3. Query candidati
    candidates = _query_candidates(
        session=session,
        sezione=sezione,
        livello=plan.livello,
        exclude_ids=current_exercise_ids,
        missing_patterns=missing_patterns,
        trainer_id=trainer_id,
    )

    if not candidates:
        raise ValueError("Nessun esercizio candidato trovato per i criteri specificati")

    candidate_map = {ex.id: ex for ex in candidates}

    # 4. Anamnesi (se c'e' un cliente assegnato)
    anamnesi: Optional[dict] = None
    if plan.id_cliente:
        client = session.get(Client, plan.id_cliente)
        if client and client.anamnesi_json:
            try:
                anamnesi = json.loads(client.anamnesi_json)
            except json.JSONDecodeError:
                pass

    # 5. Costruisci prompt
    prompt = _build_suggest_prompt(
        plan=plan,
        sezione=sezione,
        current_patterns=current_patterns,
        pattern_exercises=pattern_exercises,
        missing_patterns=missing_patterns,
        candidates=candidates,
        anamnesi=anamnesi,
        focus_muscolare=focus_muscolare,
    )

    logger.info(
        "Copilot suggest: plan=%d, sezione=%s, current=%d, candidates=%d, missing=%s",
        plan.id, sezione, len(current_exercise_ids), len(candidates),
        sorted(missing_patterns) if missing_patterns else "none",
    )

    # 6. Chiama Ollama
    raw = call_ollama(SYSTEM_SUGGEST, prompt, num_predict=512)

    # 7. Parse e valida
    suggestions = _parse_suggestions(raw, candidate_map)

    if not suggestions:
        logger.warning("Copilot: zero suggerimenti validi da Ollama, fallback deterministico")
        # Fallback: 1 per pattern diverso (varieta'), poi riempi
        seen_patterns: set[str] = set()
        for ex in candidates:
            if ex.pattern_movimento not in seen_patterns:
                suggestions.append({
                    "exercise_id": ex.id,
                    "nome": ex.nome,
                    "categoria": ex.categoria,
                    "pattern_movimento": ex.pattern_movimento,
                    "attrezzatura": ex.attrezzatura,
                    "muscoli_primari": parse_json_field(ex.muscoli_primari),
                    "reasoning": "Suggerimento automatico basato su pattern e livello.",
                })
                seen_patterns.add(ex.pattern_movimento)
                if len(suggestions) >= 3:
                    break

    return suggestions


# ═══════════════════════════════════════════════════════════
# PUBLIC API — CHAT (agente conversazionale)
# ═══════════════════════════════════════════════════════════


def handle_chat(
    db: Session,
    plan: WorkoutPlan,
    request: CopilotChatRequest,
    trainer_id: int,
) -> CopilotChatResponse:
    """
    Gestisce un messaggio chat dal PT nel workout builder.

    Pipeline:
    1. route_intent() classifica il messaggio
    2. Carica anamnesi se il piano ha un cliente
    3. Dispatcha alla capability giusta
    4. Ritorna CopilotChatResponse con message + actions + context_notes

    Non lancia eccezioni — errori gestiti internamente con graceful fallback.
    """
    # 1. Classifica intent
    intent = route_intent(request.message)
    logger.info("Copilot chat: plan=%d, intent=%s, msg='%s'",
                plan.id, intent, request.message[:80])

    # 2. Carica anamnesi
    anamnesi: Optional[dict] = None
    if plan.id_cliente:
        client = db.get(Client, plan.id_cliente)
        if client and client.anamnesi_json:
            try:
                anamnesi = json.loads(client.anamnesi_json)
            except json.JSONDecodeError:
                pass

    # 3. Dispatch capability
    try:
        if intent == "suggest":
            return _cap_suggest(db, plan, request, anamnesi, trainer_id)
        elif intent == "analyze":
            return _cap_analyze(db, plan, request, anamnesi, trainer_id)
        elif intent == "chat":
            return _cap_chat(db, plan, request, anamnesi, trainer_id)
        else:
            # Skeleton capabilities
            return _cap_skeleton(intent)

    except RuntimeError as e:
        # Ollama non raggiungibile — graceful fallback
        logger.warning("Copilot chat Ollama error: %s", e)
        return CopilotChatResponse(
            message=(
                "Non riesco a connettermi all'AI in questo momento. "
                "Verifica che Ollama sia attivo e riprova."
            ),
            intent=intent,
        )
