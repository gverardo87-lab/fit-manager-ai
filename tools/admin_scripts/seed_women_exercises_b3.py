"""
Seed Batch 3 — Esercizi Donne 18-50 / Posturale & Rehab.

Crea 8 esercizi nuovi (non presenti nel DB) con campi base compilati
deterministicamente. I campi descrittivi (descrizione_anatomica, setup,
coaching_cues, errori_comuni, controindicazioni, note_sicurezza) vengono
popolati nella fase successiva da activate_batch.py --ids.

Esercizi (tutti bodyweight/band, photo-optional o con foto in seguito):
  1. Monster Walk con Elastico      — adductor/isolation/band/beginner
  2. Fire Hydrant                   — hip_thrust/bodyweight/bodyweight/beginner
  3. Wall Angel                     — mobility/mobilita/bodyweight/beginner
  4. Chin Tuck                      — mobility/mobilita/bodyweight/beginner
  5. TVA Activation                 — core/bodyweight/bodyweight/beginner
  6. 90/90 Hip Stretch              — stretch/stretching/bodyweight/beginner
  7. Foam Roller Thoracic Extension — mobility/mobilita/bodyweight/beginner
  8. Glute Bridge Bilaterale        — hip_thrust/compound/band/beginner

Idempotente: salta esercizi con stesso nome gia' presenti.

Eseguire dalla root:
  python -m tools.admin_scripts.seed_women_exercises_b3 [--db dev|prod|both] [--dry-run]
"""

import argparse
import os
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# DATI ESERCIZI — Rigore anatomico/biomeccanico (NSCA/ACSM/Sahrmann)
# ================================================================
# Campi deterministici: esecuzione, muscoli, classificazione biomeccanica.
# I campi Ollama (descrizione_anatomica, descrizione_biomeccanica, setup,
# coaching_cues, errori_comuni, controindicazioni, note_sicurezza) vengono
# generati nella fase di enrichment di activate_batch.py.

EXERCISES: list[dict] = [
    {
        "nome": "Monster Walk con Elastico",
        "nome_en": "Lateral Band Walk (Monster Walk)",
        "categoria": "isolation",
        "pattern_movimento": "adductor",
        "force_type": "pull",
        "lateral_pattern": "bilateral",
        "muscoli_primari": '["glutes", "adductors"]',
        "muscoli_secondari": '["glutes", "hip_flexors"]',
        "attrezzatura": "band",
        "difficolta": "beginner",
        "rep_range_forza": "3x10-12",
        "rep_range_ipertrofia": "3x15-20",
        "rep_range_resistenza": "3x20-25",
        "ore_recupero": 24,
        "catena_cinetica": "closed",
        "piano_movimento": "frontal",
        "tipo_contrazione": "dynamic",
        "esecuzione": (
            "Posiziona un elastico mini-band appena sopra le ginocchia. "
            "Assumi una posizione di mezzo squat (flessione anca 20-30 gradi, ginocchia allineate sulle punte). "
            "Mantieni il core attivo e la schiena neutra. "
            "Esegui passi laterali di 30-40 cm mantenendo la tensione dell'elastico: "
            "porta il piede guida lateralmente, poi segui con il piede trail senza avvicinare troppo i piedi. "
            "Cammina per 10-15 passi in una direzione, poi torna nella direzione opposta. "
            "Mantieni le ginocchia in linea con le punte per tutta la durata: "
            "evita che collassino verso l'interno (valgismo). "
            "La tensione dell'elastico deve essere continua — non lasciare che i piedi si avvicinino troppo."
        ),
        "respirazione": "Respiro costante e ritmico con i passi. Evitare apnea.",
        "tempo_consigliato": "2-0-2-0",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "Fire Hydrant",
        "nome_en": "Fire Hydrant",
        "categoria": "bodyweight",
        "pattern_movimento": "hip_thrust",
        "force_type": "pull",
        "lateral_pattern": "unilateral",
        "muscoli_primari": '["glutes"]',
        "muscoli_secondari": '["glutes", "hip_flexors"]',
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "rep_range_forza": "3x10-15",
        "rep_range_ipertrofia": "3x15-20",
        "rep_range_resistenza": "3x20-25",
        "ore_recupero": 24,
        "catena_cinetica": "open",
        "piano_movimento": "frontal",
        "tipo_contrazione": "dynamic",
        "esecuzione": (
            "Posizionati in quadrupedia: polsi sotto le spalle, ginocchia sotto le anche. "
            "Mantieni la schiena in posizione neutra (non iperestendere ne' flettere la colonna). "
            "Inspira. Con l'espirazione, solleva lateralmente la coscia destra mantenendo il ginocchio flesso a 90 gradi "
            "finche' la coscia e' parallela al suolo (abduzione anca ~45 gradi). "
            "Non ruotare il bacino ne' compensare alzando il fianco controlaterale. "
            "Abbassa lentamente controllando il movimento. "
            "Completa le ripetizioni su un lato prima di passare all'altro. "
            "Progressione: aggiungere mini-band sopra le ginocchia o cavigliera pesata."
        ),
        "respirazione": "Espira in fase concentrica (sollevamento), inspira in fase eccentrica (abbassamento).",
        "tempo_consigliato": "2-1-2-0",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "Wall Angel",
        "nome_en": "Wall Angel",
        "categoria": "mobilita",
        "pattern_movimento": "mobility",
        "force_type": "pull",
        "lateral_pattern": "bilateral",
        "muscoli_primari": '["traps", "back"]',
        "muscoli_secondari": '["traps", "shoulders", "back"]',
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "rep_range_forza": None,
        "rep_range_ipertrofia": None,
        "rep_range_resistenza": "2x10-15 rip",
        "ore_recupero": 0,
        "catena_cinetica": "closed",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
        "esecuzione": (
            "Mettiti in piedi con la schiena contro una parete. Avvicina talloni, glutei, scapole e testa alla parete. "
            "Posiziona le braccia a 90 gradi ('cactus position'): gomiti all'altezza delle spalle, polsi flessi a 90 gradi. "
            "Verifica che gomiti e polsi tocchino la parete. "
            "Mantenendo il contatto della schiena bassa con la parete (no iperestensione lombare), "
            "scivola le braccia verso l'alto lungo la parete finche' sono quasi distese sopra la testa. "
            "Arresta il movimento prima che la schiena bassa si stacchi dalla parete o che i polsi perdano il contatto. "
            "Scendi lentamente nella posizione di partenza. "
            "La qualita' del movimento e' piu' importante del ROM: "
            "meglio un range ridotto con scapole depresse che un range pieno con compensi cervicali."
        ),
        "respirazione": "Espira salendo, inspira scendendo. Respirazione diaframmatica.",
        "tempo_consigliato": "3-1-3-1",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "Chin Tuck",
        "nome_en": "Chin Tuck (Cervical Retraction)",
        "categoria": "mobilita",
        "pattern_movimento": "mobility",
        "force_type": "static",
        "lateral_pattern": "bilateral",
        "muscoli_primari": '["back"]',
        "muscoli_secondari": '["traps"]',
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "rep_range_forza": None,
        "rep_range_ipertrofia": None,
        "rep_range_resistenza": "3x10 (hold 5-10s)",
        "ore_recupero": 0,
        "catena_cinetica": "open",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "isometric",
        "esecuzione": (
            "Siediti o stai in piedi con postura neutra. "
            "Guarda dritto davanti a te. "
            "Senza inclinare ne' ruotare la testa, porta il mento verso la gola in senso orizzontale "
            "come se volessi creare un 'doppio mento'. "
            "La testa si muove all'indietro sul piano orizzontale — NON verso il basso. "
            "Tieni la posizione 5-10 secondi mantenendo la respirazione. "
            "Rilascia lentamente. "
            "Senti l'allungamento nella nuca e la contrazione dei muscoli profondi anteriori del collo. "
            "Progressione: aggiungere leggera resistenza con il pollice sotto il mento."
        ),
        "respirazione": "Respiro normale durante il mantenimento isometrico.",
        "tempo_consigliato": "0-5-0-0",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "TVA Activation - Abdominal Hollowing",
        "nome_en": "TVA Activation (Abdominal Hollowing / Drawing-In Maneuver)",
        "categoria": "bodyweight",
        "pattern_movimento": "core",
        "force_type": "static",
        "lateral_pattern": "bilateral",
        "muscoli_primari": '["core"]',
        "muscoli_secondari": '["core", "back"]',
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "rep_range_forza": None,
        "rep_range_ipertrofia": None,
        "rep_range_resistenza": "3x10 (hold 10s)",
        "ore_recupero": 0,
        "catena_cinetica": "open",
        "piano_movimento": "multi",
        "tipo_contrazione": "isometric",
        "esecuzione": (
            "Posizionati in decubito supino con ginocchia flesse, piedi appoggiati al suolo. "
            "Posiziona le mani sull'addome basso (2 cm dentro la SIAS - spina iliaca antero-superiore). "
            "Inspirazione profonda diaframmatica: l'addome si espande. "
            "Espirazione: 'porta l'ombelico verso la colonna' senza trattenere il respiro e senza "
            "contrarre i glutei o gli addominali superficiali (retto dell'addome). "
            "Devi sentire sotto le dita una leggera tensione profonda, non un irrigidimento. "
            "Mantieni l'attivazione 10 secondi respirando normalmente (non trattenere l'aria). "
            "Progressione: in quadrupedia, poi da seduto, poi in piedi. "
            "NOTA CLINICA: fondamentale per diastasi dei retti e lombalgia. "
            "Non confondere con il 'bracing' (irrigidimento globale) — l'hollowing e' attivazione selettiva del TVA."
        ),
        "respirazione": "Respirazione normale durante il mantenimento — mai trattenere il respiro.",
        "tempo_consigliato": "0-10-0-0",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "90/90 Hip Stretch",
        "nome_en": "90/90 Hip Mobility Stretch",
        "categoria": "stretching",
        "pattern_movimento": "stretch",
        "force_type": "static",
        "lateral_pattern": "unilateral",
        "muscoli_primari": '["glutes"]',
        "muscoli_secondari": '["adductors", "hip_flexors"]',
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "rep_range_forza": None,
        "rep_range_ipertrofia": None,
        "rep_range_resistenza": "2x60s per lato",
        "ore_recupero": 0,
        "catena_cinetica": "open",
        "piano_movimento": "multi",
        "tipo_contrazione": "static",
        "esecuzione": (
            "Siediti sul pavimento. "
            "Gamba anteriore: coscia a 90 gradi rispetto al tronco, gamba a 90 gradi rispetto alla coscia "
            "(rotazione esterna anca). Piede flessione dorsale neutra. "
            "Gamba posteriore: coscia a 90 gradi rispetto al tronco verso il lato opposto, "
            "gamba a 90 gradi verso l'indietro (rotazione interna anca). "
            "Entrambi i ginocchi a 90 gradi. Siediti dritto, bacino neutro. "
            "Per intensificare: inclina lentamente il tronco in avanti sopra la gamba anteriore "
            "mantenendo la schiena piatta (non arrotondare). "
            "Mantieni 30-60 secondi, poi cambia lato. "
            "Lo stretch si sente nel gluteo della gamba anteriore e nell'anca della gamba posteriore."
        ),
        "respirazione": "Respiro profondo e lento. Ogni espirazione approfondisce lo stretch.",
        "tempo_consigliato": "0-60-0-0",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "Foam Roller Thoracic Extension",
        "nome_en": "Thoracic Extension on Foam Roller",
        "categoria": "mobilita",
        "pattern_movimento": "mobility",
        "force_type": "static",
        "lateral_pattern": "bilateral",
        "muscoli_primari": '["back"]',
        "muscoli_secondari": '["back", "traps"]',
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "rep_range_forza": None,
        "rep_range_ipertrofia": None,
        "rep_range_resistenza": "1x5-8 estensioni per segmento (3-4 segmenti)",
        "ore_recupero": 0,
        "catena_cinetica": "open",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "static",
        "esecuzione": (
            "Posiziona il foam roller orizzontale sotto la zona toracica media (T4-T8). "
            "Siediti davanti al roller, poi sdraiati appoggiando la schiena. "
            "Intreccia le mani dietro la testa per supportare il collo "
            "(NON tirare il collo in flessione). "
            "Appoggia i piedi al suolo, ginocchia flesse. "
            "Con un respiro profondo, lascia che il peso della testa e del tronco superiore "
            "favorisca l'estensione toracica sul roller. "
            "Mantieni 5-10 secondi, poi solleva leggermente il tronco. "
            "Sposta il roller di 3-4 cm verso l'alto e ripeti. "
            "Lavora su 3-4 segmenti toracici (mai sul tratto lombare o cervicale). "
            "ATTENZIONE: il roller deve essere sempre in zona TORACICA (tra scapole e vertebre toraciche), "
            "mai lombare (rischio iperestensione) ne' cervicale."
        ),
        "respirazione": "Inspirazione profonda in fase di estensione — favorisce l'apertura toracica.",
        "tempo_consigliato": "0-10-0-0",
        "is_builtin": True,
        "in_subset": True,
    },
    {
        "nome": "Glute Bridge Bilaterale con Elastico",
        "nome_en": "Banded Glute Bridge",
        "categoria": "compound",
        "pattern_movimento": "hip_thrust",
        "force_type": "push",
        "lateral_pattern": "bilateral",
        "muscoli_primari": '["glutes"]',
        "muscoli_secondari": '["hamstrings", "back"]',
        "attrezzatura": "band",
        "difficolta": "beginner",
        "rep_range_forza": "4x6-8",
        "rep_range_ipertrofia": "3x12-15",
        "rep_range_resistenza": "3x20-25",
        "ore_recupero": 48,
        "catena_cinetica": "closed",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
        "esecuzione": (
            "Sdraiati in decubito supino, ginocchia flesse a 90 gradi, piedi appoggiati al suolo "
            "alla larghezza delle anche. Posiziona un elastico mini-band sopra le ginocchia. "
            "Braccia lungo i fianchi con palmi rivolti verso il basso per stabilita'. "
            "Inspira. Con l'espirazione, spingi i talloni nel suolo e solleva il bacino "
            "contraendo intensamente i glutei. "
            "Spingi anche verso l'esterno contro la resistenza dell'elastico "
            "per mantenere l'allineamento ginocchio-piede (no valgismo). "
            "In cima al movimento: bacino sollevato, colonna neutra, "
            "ginocchia allineate con le anche, non iperestendere la lombare. "
            "Mantieni 1-2 secondi di contrazione in cima. "
            "Abbassa controllando il movimento. "
            "Progressioni: aumentare resistenza elastico, aggiungere peso su cosce, "
            "hip thrust con spalle su panca."
        ),
        "respirazione": "Espira in fase concentrica (sollevamento bacino), inspira in eccentrica.",
        "tempo_consigliato": "2-2-2-0",
        "is_builtin": True,
        "in_subset": True,
    },
]

# ================================================================
# HELPER
# ================================================================

def get_db_paths(db_arg: str) -> list[str]:
    paths = []
    if db_arg in ("dev", "both"):
        paths.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if db_arg in ("prod", "both"):
        paths.append(os.path.join(BASE_DIR, "crm.db"))
    return paths


def seed_db(db_path: str, dry_run: bool) -> list[int]:
    """Inserisce gli esercizi nel DB. Salta quelli con nome gia' presente.
    Ritorna lista di IDs inseriti."""
    db_name = os.path.basename(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc).isoformat()

    inserted_ids: list[int] = []
    skipped: list[str] = []

    print(f"\n{'=' * 60}")
    print(f"  SEED BATCH 3 — {db_name}")
    print(f"{'=' * 60}")

    for ex in EXERCISES:
        nome = ex["nome"]

        # Idempotenza: salta se gia' presente (per nome)
        existing = conn.execute(
            "SELECT id FROM esercizi WHERE nome = ? AND deleted_at IS NULL", (nome,)
        ).fetchone()

        if existing:
            skipped.append(nome)
            print(f"  SKIP [{existing['id']}] {nome} (gia' presente)")
            continue

        if dry_run:
            print(f"  DRY-RUN: inserirei '{nome}'")
            continue

        # Prepara tutti i campi
        fields = {
            "trainer_id": None,  # builtin
            "nome": ex["nome"],
            "nome_en": ex.get("nome_en"),
            "categoria": ex["categoria"],
            "pattern_movimento": ex["pattern_movimento"],
            "force_type": ex.get("force_type"),
            "lateral_pattern": ex.get("lateral_pattern"),
            "muscoli_primari": ex.get("muscoli_primari"),
            "muscoli_secondari": ex.get("muscoli_secondari"),
            "attrezzatura": ex["attrezzatura"],
            "difficolta": ex["difficolta"],
            "rep_range_forza": ex.get("rep_range_forza"),
            "rep_range_ipertrofia": ex.get("rep_range_ipertrofia"),
            "rep_range_resistenza": ex.get("rep_range_resistenza"),
            "ore_recupero": ex.get("ore_recupero", 24),
            "catena_cinetica": ex.get("catena_cinetica"),
            "piano_movimento": ex.get("piano_movimento"),
            "tipo_contrazione": ex.get("tipo_contrazione"),
            "esecuzione": ex.get("esecuzione"),
            "respirazione": ex.get("respirazione"),
            "tempo_consigliato": ex.get("tempo_consigliato"),
            "is_builtin": 1 if ex.get("is_builtin") else 0,
            "in_subset": 1 if ex.get("in_subset") else 0,
            "created_at": now,
        }

        cols = ", ".join(fields.keys())
        placeholders = ", ".join("?" * len(fields))
        values = list(fields.values())

        cursor = conn.execute(
            f"INSERT INTO esercizi ({cols}) VALUES ({placeholders})",
            values,
        )
        new_id = cursor.lastrowid
        inserted_ids.append(new_id)
        print(f"  INSERT [{new_id}] {nome}")

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n  Inseriti: {len(inserted_ids)}")
    print(f"  Saltati (gia' presenti): {len(skipped)}")
    if inserted_ids:
        print(f"  IDs inseriti: {inserted_ids}")
        print(f"\n  PROSSIMO PASSO — Enrichment Ollama su questi IDs:")
        print(f"    python -m tools.admin_scripts.activate_batch --db both "
              f"--ids '{','.join(str(i) for i in inserted_ids)}' "
              f"--skip-enrich  # <-- rimuovi --skip-enrich per avviare Ollama")

    return inserted_ids


# ================================================================
# MAIN
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Seed Batch 3 — Esercizi donne / posturale / rehab"
    )
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  SEED WOMEN EXERCISES — Batch 3 (8 esercizi nuovi)")
    print("=" * 60)
    print(f"  DB: {args.db} | Dry-run: {args.dry_run}")
    print(f"  Esercizi: {len(EXERCISES)}")

    db_paths = get_db_paths(args.db)
    if not db_paths:
        print("ERROR: nessun database trovato.")
        return

    all_ids: list[int] = []
    for db_path in db_paths:
        ids = seed_db(db_path, args.dry_run)
        # Raccogliamo IDs solo dal primo DB (sono gli stessi per entrambi)
        if not all_ids:
            all_ids = ids

    if all_ids and not args.dry_run:
        print(f"\n{'=' * 60}")
        print("  PROSSIMI PASSI (in ordine):")
        ids_str = ",".join(str(i) for i in all_ids)
        print(f"  1. Enrichment Ollama (batch 3):")
        print(f"     python -m tools.admin_scripts.activate_batch --db both --ids '{ids_str}' --force-no-photo")
        print(f"  2. Pipeline deterministica:")
        print(f"     python -m tools.admin_scripts.populate_taxonomy --db both")
        print(f"     python -m tools.admin_scripts.populate_conditions --db both")
        print(f"     python -m tools.admin_scripts.populate_exercise_relations --db both")
        print(f"     python -m tools.admin_scripts.fill_subset_gaps --db both")
        print(f"     python -m tools.admin_scripts.verify_exercise_quality --db both")
        print(f"  3. Rebuild catalog:")
        print(f"     python -m tools.admin_scripts.build_catalog --source crm_dev")
        print("=" * 60)


if __name__ == "__main__":
    main()
