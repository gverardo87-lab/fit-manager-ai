# api/services/workout_commentary.py
"""
Servizio generazione commento AI per schede allenamento — v2 blocchi.

V2: genera commentary a blocchi (panoramica + 1 per sessione + consigli)
con chiamate Ollama focalizzate. Output JSON strutturato per rendering
inline per sessione nella preview.

Privacy-first: nessun dato personale esce dalla macchina.
"""

import json
import logging
from typing import Optional

from sqlmodel import Session, select

from api.models.client import Client
from api.models.exercise import Exercise
from api.models.workout import WorkoutPlan, WorkoutSession, WorkoutExercise
from api.services.ollama_client import (
    call_ollama,
    parse_json_field,
    format_exercise_for_prompt,
    format_anamnesi_for_prompt,
)

logger = logging.getLogger("fitmanager.services.commentary")

# ═══════════════════════════════════════════════════════════
# DATA ASSEMBLY
# ═══════════════════════════════════════════════════════════


def _fetch_workout_data(session: Session, plan: WorkoutPlan) -> dict:
    """
    Assembla tutti i dati necessari per il prompt.
    4 query batch: sessions -> exercises -> exercise refs -> client.
    """
    # 1. Sessioni
    sessions = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.id_scheda == plan.id)
        .order_by(WorkoutSession.numero_sessione)
    ).all()

    # 2. Esercizi di tutte le sessioni (batch IN)
    session_ids = [s.id for s in sessions]
    workout_exercises: list[WorkoutExercise] = []
    if session_ids:
        workout_exercises = list(session.exec(
            select(WorkoutExercise)
            .where(WorkoutExercise.id_sessione.in_(session_ids))
            .order_by(WorkoutExercise.ordine)
        ).all())

    # 3. Esercizi enriched (batch IN)
    exercise_ref_ids = list({e.id_esercizio for e in workout_exercises})
    exercise_map: dict[int, Exercise] = {}
    if exercise_ref_ids:
        refs = session.exec(
            select(Exercise).where(Exercise.id.in_(exercise_ref_ids))
        ).all()
        exercise_map = {r.id: r for r in refs}

    # 4. Cliente + anamnesi (se assegnato)
    client: Optional[Client] = None
    anamnesi: Optional[dict] = None
    if plan.id_cliente:
        client = session.get(Client, plan.id_cliente)
        if client and client.anamnesi_json:
            try:
                anamnesi = json.loads(client.anamnesi_json)
            except json.JSONDecodeError:
                pass

    # Raggruppa esercizi per sessione
    exercises_by_session: dict[int, list[WorkoutExercise]] = {}
    for we in workout_exercises:
        exercises_by_session.setdefault(we.id_sessione, []).append(we)

    return {
        "plan": plan,
        "sessions": sessions,
        "exercises_by_session": exercises_by_session,
        "exercise_map": exercise_map,
        "client": client,
        "anamnesi": anamnesi,
    }


# ═══════════════════════════════════════════════════════════
# QUALITY ANALYSIS (server-side, arricchisce il prompt)
# ═══════════════════════════════════════════════════════════

PUSH_PATTERNS = {"push_h", "push_v"}
PULL_PATTERNS = {"pull_h", "pull_v"}
FUNDAMENTAL_PATTERNS = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v"}
COMPLEMENTARY_PATTERNS = {"core", "rotation", "carry"}

PATTERN_LABELS = {
    "squat": "Squat",
    "hinge": "Hinge (stacco/hip)",
    "push_h": "Push orizzontale",
    "push_v": "Push verticale",
    "pull_h": "Pull orizzontale",
    "pull_v": "Pull verticale",
    "core": "Core",
    "rotation": "Rotazione",
    "carry": "Carry/Trasporto",
}

MUSCLE_LABELS = {
    "quadriceps": "Quadricipiti",
    "glutes": "Glutei",
    "hamstrings": "Femorali",
    "calves": "Polpacci",
    "adductors": "Adduttori",
    "chest": "Petto",
    "back": "Schiena",
    "lats": "Dorsali",
    "shoulders": "Spalle",
    "traps": "Trapezi",
    "biceps": "Bicipiti",
    "triceps": "Tricipiti",
    "forearms": "Avambracci",
    "core": "Core",
}

REP_RANGES = {
    "forza": (1, 6),
    "ipertrofia": (6, 12),
    "resistenza": (12, 20),
    "dimagrimento": (8, 15),
}


def _parse_reps(ripetizioni: str) -> Optional[float]:
    """Parse '8-12' -> 10.0, '5' -> 5.0, '30s' -> None."""
    import re
    trimmed = ripetizioni.strip().lower()
    if "s" in trimmed:
        return None
    m = re.match(r"^(\d+)\s*-\s*(\d+)$", trimmed)
    if m:
        return (int(m.group(1)) + int(m.group(2))) / 2
    m = re.match(r"^(\d+)$", trimmed)
    if m:
        return float(m.group(1))
    return None


def _analyze_quality(data: dict) -> str:
    """
    Analisi qualita' strutturale per arricchire il commentary AI.

    Analizza: push/pull, pattern mancanti, volume, rep alignment, anamnesi.
    Ritorna stringa testuale da iniettare nel prompt.
    """
    sessions = data["sessions"]
    exercises_by_session = data["exercises_by_session"]
    exercise_map = data["exercise_map"]
    plan = data["plan"]
    anamnesi = data.get("anamnesi")

    findings: list[str] = []

    # ── Raccogli dati da esercizi principali (no avviamento/stretching) ──
    push_sets = 0
    pull_sets = 0
    patterns_used: set[str] = set()
    muscle_sets: dict[str, float] = {}
    rep_aligned = 0
    rep_total = 0
    target_range = REP_RANGES.get(plan.obiettivo)

    for sess in sessions:
        for we in exercises_by_session.get(sess.id, []):
            ex = exercise_map.get(we.id_esercizio)
            if not ex:
                continue
            cat = ex.categoria
            if cat in ("stretching", "mobilita", "avviamento"):
                continue

            pattern = ex.pattern_movimento
            patterns_used.add(pattern)

            # Push/Pull
            if pattern in PUSH_PATTERNS:
                push_sets += we.serie
            if pattern in PULL_PATTERNS:
                pull_sets += we.serie

            # Muscoli (primari: credito pieno, secondari: mezzo credito)
            primari = parse_json_field(ex.muscoli_primari)
            for m in primari:
                muscle_sets[m] = muscle_sets.get(m, 0) + we.serie
            secondari = parse_json_field(ex.muscoli_secondari)
            for m in secondari:
                muscle_sets[m] = muscle_sets.get(m, 0) + we.serie * 0.5

            # Rep alignment
            if target_range:
                parsed = _parse_reps(we.ripetizioni)
                if parsed is not None:
                    rep_total += 1
                    if target_range[0] <= parsed <= target_range[1]:
                        rep_aligned += 1

    # ── Push/Pull ratio ──
    if push_sets > 0 and pull_sets > 0:
        ratio = push_sets / pull_sets
        if ratio > 1.5:
            findings.append(
                f"Rapporto Push/Pull: {push_sets}:{pull_sets} — SBILANCIATO verso push"
            )
        elif ratio < 0.67:
            findings.append(
                f"Rapporto Push/Pull: {push_sets}:{pull_sets} — SBILANCIATO verso pull"
            )
        else:
            findings.append(
                f"Rapporto Push/Pull: {push_sets}:{pull_sets} — BILANCIATO"
            )
    elif push_sets > 0 and pull_sets == 0:
        findings.append("ATTENZIONE: zero esercizi pull (trazione)")
    elif pull_sets > 0 and push_sets == 0:
        findings.append("ATTENZIONE: zero esercizi push (spinta)")

    # ── Pattern mancanti ──
    missing_fund = FUNDAMENTAL_PATTERNS - patterns_used
    missing_comp = COMPLEMENTARY_PATTERNS - patterns_used
    if missing_fund:
        labels = [PATTERN_LABELS.get(p, p) for p in sorted(missing_fund)]
        findings.append(f"Pattern fondamentali mancanti: {', '.join(labels)}")
    if missing_comp:
        labels = [PATTERN_LABELS.get(p, p) for p in sorted(missing_comp)]
        findings.append(f"Pattern complementari mancanti: {', '.join(labels)}")
    if not missing_fund and not missing_comp:
        findings.append("Tutti i pattern di movimento sono coperti")

    # ── Volume per muscolo (top 5) ──
    if muscle_sets:
        sorted_muscles = sorted(muscle_sets.items(), key=lambda x: x[1], reverse=True)
        vol_lines = [
            f"{MUSCLE_LABELS.get(m, m)}: {int(s)} serie"
            for m, s in sorted_muscles[:5]
        ]
        findings.append(f"Volume muscolare (top 5): {', '.join(vol_lines)}")

    # ── Rep alignment ──
    if target_range and rep_total > 0:
        pct = int((rep_aligned / rep_total) * 100)
        label = "OTTIMO" if pct >= 80 else "BUONO" if pct >= 60 else "DA MIGLIORARE"
        findings.append(
            f"Reps allineate obiettivo ({plan.obiettivo} {target_range[0]}-{target_range[1]}): "
            f"{pct}% — {label}"
        )

    # ── Anamnesi warnings ──
    if anamnesi:
        contras_found: list[str] = []
        for sess in sessions:
            for we in exercises_by_session.get(sess.id, []):
                ex = exercise_map.get(we.id_esercizio)
                if not ex:
                    continue
                contras = parse_json_field(ex.controindicazioni)
                if contras:
                    contras_found.append(f"{ex.nome} (controindicazioni: {', '.join(contras[:2])})")
        if contras_found:
            findings.append(
                f"Esercizi con controindicazioni presenti: {'; '.join(contras_found[:3])}"
            )

    return "\n".join(f"- {f}" for f in findings) if findings else ""


# ═══════════════════════════════════════════════════════════
# SYSTEM PROMPTS — v2 (specializzati per blocco)
# ═══════════════════════════════════════════════════════════

COMMON_RULES = """\
REGOLE ASSOLUTE:
1. Scrivi in ITALIANO corretto e professionale (ma accessibile a un non-esperto)
2. USA SOLO le informazioni fornite — NON inventare esercizi, muscoli o dettagli non presenti nei dati
3. Se un dato non e' disponibile, omettilo — non inventare
4. Il tono deve essere incoraggiante ma professionale
5. Formattazione: solo titoli (##, ###), grassetto (**), elenchi puntati (-), testo normale
6. NON usare tabelle, code blocks o formattazione avanzata"""

SYSTEM_PANORAMICA = f"""\
Sei un personal trainer professionista con laurea in scienze motorie e 15 anni di esperienza.
Scrivi la PANORAMICA del programma di allenamento.

{COMMON_RULES}

ISTRUZIONI SPECIFICHE:
- Scrivi 150-300 parole
- Spiega l'obiettivo della scheda, a chi si rivolge, la filosofia dietro la struttura
- Se ricevi dati anamnesi, menziona come il programma tiene conto della situazione fisica
- Se ricevi un'ANALISI QUALITA', integra le osservazioni in modo naturale nel testo
- NON descrivere i singoli esercizi — quelli verranno dopo
- Inizia direttamente con il contenuto, SENZA scrivere "## Panoramica" o titoli"""

SYSTEM_SESSION = f"""\
Sei un personal trainer professionista con laurea in scienze motorie e 15 anni di esperienza.
Scrivi la guida dettagliata per UNA SINGOLA SESSIONE di allenamento.

{COMMON_RULES}

ISTRUZIONI SPECIFICHE:
- Per OGNI esercizio elencato, scrivi una sezione con "### Nome Esercizio" contenente:
  - **Perche' questo esercizio**: motivazione della scelta rispetto all'obiettivo
  - **Come eseguirlo**: indicazioni pratiche (postura, movimento, respirazione)
  - **Cosa sentire**: sensazioni muscolari attese durante l'esecuzione
  - **Attenzione a**: errori comuni da evitare
- Segui ESATTAMENTE l'ordine degli esercizi come fornito nel prompt
- NON omettere nessun esercizio — devi coprirli TUTTI
- Se hai dati anamnesi e un esercizio ha controindicazioni pertinenti, aggiungi un avviso
- Circa 100-200 parole per esercizio
- NON aggiungere introduzione o chiusura alla sessione — solo i singoli esercizi"""

SYSTEM_CONSIGLI = f"""\
Sei un personal trainer professionista con laurea in scienze motorie e 15 anni di esperienza.
Scrivi i CONSIGLI GENERALI per accompagnare il programma di allenamento.

{COMMON_RULES}

ISTRUZIONI SPECIFICHE:
- Scrivi 3-5 consigli pratici su: riscaldamento, idratazione, recupero, progressione, alimentazione
- Se hai dati anamnesi, includi raccomandazioni specifiche per la situazione del cliente
- Se ricevi un'ANALISI QUALITA', integra suggerimenti pertinenti in modo naturale
- Usa il formato elenco (- ) per ogni consiglio con grassetto per il titolo
- Circa 150-250 parole totali
- Inizia direttamente con i consigli, SENZA scrivere "## Consigli" o titoli"""


# ═══════════════════════════════════════════════════════════
# BLOCK GENERATORS — v2
# ═══════════════════════════════════════════════════════════


def _generate_panoramica(data: dict, quality_text: str) -> dict:
    """Genera il blocco panoramica del programma."""
    plan: WorkoutPlan = data["plan"]
    client: Optional[Client] = data["client"]
    anamnesi: Optional[dict] = data["anamnesi"]
    sessions: list[WorkoutSession] = data["sessions"]

    lines: list[str] = []
    lines.append("DATI SCHEDA ALLENAMENTO:")
    lines.append(f"Nome: {plan.nome}")
    lines.append(f"Obiettivo: {plan.obiettivo}")
    lines.append(f"Livello: {plan.livello}")
    lines.append(f"Durata: {plan.durata_settimane} settimane, {plan.sessioni_per_settimana} sessioni/settimana")
    if plan.note:
        lines.append(f"Note del trainer: {plan.note}")

    lines.append(f"\nSessioni ({len(sessions)}):")
    for sess in sessions:
        focus = f" — Focus: {sess.focus_muscolare}" if sess.focus_muscolare else ""
        lines.append(f"  {sess.numero_sessione}. {sess.nome_sessione}{focus}")

    if client:
        lines.append("\nPROFILO CLIENTE:")
        if client.sesso:
            lines.append(f"Sesso: {client.sesso}")
        if client.data_nascita:
            lines.append(f"Data nascita: {client.data_nascita}")
        if anamnesi:
            lines.append("Anamnesi:")
            lines.append(format_anamnesi_for_prompt(anamnesi))

    if quality_text:
        lines.append("\nANALISI QUALITA' STRUTTURALE:")
        lines.append(quality_text)

    lines.append("\nScrivi la panoramica del programma.")

    prompt = "\n".join(lines)
    try:
        content = call_ollama(SYSTEM_PANORAMICA, prompt, num_predict=1024)
        return {"type": "panoramica", "content": content.strip()}
    except RuntimeError as e:
        logger.error("Panoramica generation failed: %s", e)
        return {"type": "panoramica", "content": "", "error": str(e)}


def _generate_session_block(
    data: dict,
    sess: WorkoutSession,
    session_exercises: list[WorkoutExercise],
    quality_text: str,
) -> dict:
    """Genera il blocco commentary per una singola sessione."""
    plan: WorkoutPlan = data["plan"]
    exercise_map: dict[int, Exercise] = data["exercise_map"]
    anamnesi: Optional[dict] = data.get("anamnesi")

    lines: list[str] = []
    lines.append(f"CONTESTO: Scheda '{plan.nome}', obiettivo {plan.obiettivo}, livello {plan.livello}")
    lines.append(f"\nSESSIONE {sess.numero_sessione}: {sess.nome_sessione}")
    if sess.focus_muscolare:
        lines.append(f"Focus muscolare: {sess.focus_muscolare}")
    if sess.durata_minuti:
        lines.append(f"Durata: {sess.durata_minuti} minuti")
    if sess.note:
        lines.append(f"Note sessione: {sess.note}")

    # Esercizi in ordine esatto
    principal_exercises = []
    warmup_exercises = []
    stretch_exercises = []

    for we in session_exercises:
        ex = exercise_map.get(we.id_esercizio)
        if not ex:
            continue
        if ex.categoria in ("avviamento",):
            warmup_exercises.append((we, ex))
        elif ex.categoria in ("stretching", "mobilita"):
            stretch_exercises.append((we, ex))
        else:
            principal_exercises.append((we, ex))

    if warmup_exercises:
        lines.append("\nAVVIAMENTO:")
        for i, (we, ex) in enumerate(warmup_exercises, 1):
            lines.append(f"\n{i}.")
            lines.append(format_exercise_for_prompt(we, ex))

    if principal_exercises:
        lines.append("\nESERCIZI PRINCIPALI:")
        for i, (we, ex) in enumerate(principal_exercises, 1):
            lines.append(f"\n{i}.")
            lines.append(format_exercise_for_prompt(we, ex))

    if stretch_exercises:
        lines.append("\nSTRETCHING/MOBILITA:")
        for i, (we, ex) in enumerate(stretch_exercises, 1):
            lines.append(f"\n{i}.")
            lines.append(format_exercise_for_prompt(we, ex))

    if anamnesi:
        lines.append("\nANAMNESI CLIENTE:")
        lines.append(format_anamnesi_for_prompt(anamnesi))

    lines.append("\nScrivi la guida per OGNI esercizio elencato sopra, nell'ordine esatto.")

    prompt = "\n".join(lines)
    try:
        content = call_ollama(SYSTEM_SESSION, prompt, num_predict=2048)
        return {
            "type": "session",
            "session_numero": sess.numero_sessione,
            "session_nome": sess.nome_sessione,
            "content": content.strip(),
        }
    except RuntimeError as e:
        logger.error("Session %d generation failed: %s", sess.numero_sessione, e)
        return {
            "type": "session",
            "session_numero": sess.numero_sessione,
            "session_nome": sess.nome_sessione,
            "content": "",
            "error": str(e),
        }


def _generate_consigli(data: dict, quality_text: str) -> dict:
    """Genera il blocco consigli generali."""
    plan: WorkoutPlan = data["plan"]
    anamnesi: Optional[dict] = data.get("anamnesi")

    lines: list[str] = []
    lines.append(f"CONTESTO: Scheda '{plan.nome}', obiettivo {plan.obiettivo}, livello {plan.livello}")
    lines.append(f"Durata: {plan.durata_settimane} settimane, {plan.sessioni_per_settimana} sessioni/settimana")

    if anamnesi:
        lines.append("\nANAMNESI CLIENTE:")
        lines.append(format_anamnesi_for_prompt(anamnesi))

    if quality_text:
        lines.append("\nANALISI QUALITA' STRUTTURALE:")
        lines.append(quality_text)

    lines.append("\nScrivi 3-5 consigli pratici personalizzati per questo programma.")

    prompt = "\n".join(lines)
    try:
        content = call_ollama(SYSTEM_CONSIGLI, prompt, num_predict=1024)
        return {"type": "consigli", "content": content.strip()}
    except RuntimeError as e:
        logger.error("Consigli generation failed: %s", e)
        return {"type": "consigli", "content": "", "error": str(e)}


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════


def generate_commentary(session: Session, plan: WorkoutPlan) -> str:
    """
    Genera il commento AI v2 per una scheda allenamento.

    V2: genera blocchi separati (panoramica + 1 per sessione + consigli)
    con chiamate Ollama focalizzate. Output JSON strutturato.

    Il caller (router) si occupa di salvare su plan.ai_commentary e committare.
    """
    data = _fetch_workout_data(session, plan)

    if not data["sessions"]:
        raise ValueError(
            "La scheda non ha sessioni — aggiungi almeno una sessione prima di generare"
        )

    quality_text = _analyze_quality(data)

    sessions_list: list[WorkoutSession] = data["sessions"]
    exercises_by_session = data["exercises_by_session"]
    total_exercises = sum(len(v) for v in exercises_by_session.values())

    logger.info(
        "Generating v2 commentary for plan %d (%d sessions, %d exercises, client=%s)",
        plan.id,
        len(sessions_list),
        total_exercises,
        "yes" if data["client"] else "no",
    )

    blocks: list[dict] = []

    # 1. Panoramica
    logger.info("  [1/%d] Generating panoramica...", len(sessions_list) + 2)
    blocks.append(_generate_panoramica(data, quality_text))

    # 2. Un blocco per sessione
    for i, sess in enumerate(sessions_list):
        session_exercises = exercises_by_session.get(sess.id, [])
        logger.info(
            "  [%d/%d] Generating session %d: %s (%d exercises)...",
            i + 2, len(sessions_list) + 2,
            sess.numero_sessione, sess.nome_sessione,
            len(session_exercises),
        )
        blocks.append(
            _generate_session_block(data, sess, session_exercises, quality_text)
        )

    # 3. Consigli
    logger.info("  [%d/%d] Generating consigli...", len(sessions_list) + 2, len(sessions_list) + 2)
    blocks.append(_generate_consigli(data, quality_text))

    result = {"version": 2, "blocks": blocks}
    return json.dumps(result, ensure_ascii=False)
