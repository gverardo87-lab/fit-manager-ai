"""
Costanti di mapping free-exercise-db → FitManager AI Studio.

Usato da:
- fdb_diagnostic.py (analisi match)
- import_fdb_images.py (import immagini matchati)
- import_fdb_new_exercises.py (import nuovi esercizi)
"""

import re

# ════════════════════════════════════════════════════════════
# MUSCLE MAP: FDB 17 → nostri 14
# ════════════════════════════════════════════════════════════

FDB_MUSCLE_MAP: dict[str, str] = {
    "abdominals": "core",
    "abductors": "glutes",
    "adductors": "adductors",
    "biceps": "biceps",
    "calves": "calves",
    "chest": "chest",
    "forearms": "forearms",
    "glutes": "glutes",
    "hamstrings": "hamstrings",
    "lats": "lats",
    "lower back": "back",
    "middle back": "back",
    "neck": "traps",
    "quadriceps": "quadriceps",
    "shoulders": "shoulders",
    "traps": "traps",
    "triceps": "triceps",
}

# ════════════════════════════════════════════════════════════
# EQUIPMENT MAP: FDB 13 → nostre 8
# ════════════════════════════════════════════════════════════

FDB_EQUIPMENT_MAP: dict[str | None, str] = {
    "barbell": "barbell",
    "dumbbell": "dumbbell",
    "cable": "cable",
    "machine": "machine",
    "body only": "bodyweight",
    "kettlebells": "kettlebell",
    "bands": "band",
    "exercise ball": "bodyweight",
    "foam roll": "bodyweight",
    "medicine ball": "dumbbell",
    "e-z curl bar": "barbell",
    "other": "bodyweight",
    None: "bodyweight",
}

# ════════════════════════════════════════════════════════════
# CATEGORY MAP: FDB 7 → nostre 7
# mechanic == "isolation" raffina strength → isolation
# ════════════════════════════════════════════════════════════

FDB_CATEGORY_MAP: dict[str, str] = {
    "strength": "compound",       # raffinato da mechanic
    "stretching": "stretching",
    "cardio": "cardio",
    "plyometrics": "bodyweight",
    "powerlifting": "compound",
    "olympic weightlifting": "compound",
    "strongman": "compound",
}

# ════════════════════════════════════════════════════════════
# DIFFICULTY MAP
# ════════════════════════════════════════════════════════════

FDB_DIFFICULTY_MAP: dict[str, str] = {
    "beginner": "beginner",
    "intermediate": "intermediate",
    "expert": "advanced",
}

# ════════════════════════════════════════════════════════════
# NAME ALIASES: FDB name → nostro nome_en (curato manualmente)
# Aggiungere qui i match non trovati automaticamente
# ════════════════════════════════════════════════════════════

FDB_NAME_ALIASES: dict[str, str] = {
    # FDB name -> nostro nome_en
    # Squat / Lower
    "Barbell Full Squat": "Back Squat",
    "Barbell Deadlift": "Conventional Deadlift",
    "Barbell Glute Bridge": "Glute Bridge",
    "Barbell Walking Lunge": "Walking Lunges",
    "Barbell Step Ups": "Step Up",
    "Barbell Lunge": "Reverse Lunge",
    "Split Squat with Dumbbells": "Bulgarian Split Squat",
    "Barbell Seated Calf Raise": "Seated Calf Raises",
    "Leg Extensions": "Leg Extension",
    "Standing Calf Raises": "Standing Machine Calf Raise",
    "Donkey Calf Raises": "Donkey Calf Raise",
    "Calf Press On The Leg Press Machine": "Calf Press on Leg Press",
    "Seated Leg Curl": "Leg Curl",
    "Pull Through": "Cable Pull Through",
    "One-Leg Kettlebell Deadlift": "Single Leg RDL",
    "Kettlebell Sumo Deadlift High Pull": "Dumbbell Sumo Squat",
    # Push
    "Barbell Incline Bench Press - Medium Grip": "Incline Bench Press",
    "Decline Barbell Bench Press": "Decline Bench Press",
    "Pushups": "Push-ups",
    "Close-Grip Barbell Bench Press": "Close Grip Bench Press",
    "Dumbbell Flyes": "Dumbbell Fly",
    "Incline Dumbbell Flyes": "Incline Dumbbell Fly",
    "Machine Bench Press": "Machine Chest Press",
    "Diamond Push-Ups": "Diamond Push-ups",
    "Push-Ups - Close Triceps Position": "Diamond Push-ups",
    "Pike Push Press": "Pike Push-ups",
    # Shoulders
    "Standing Military Press": "Overhead Press",
    "Arnold Dumbbell Press": "Arnold Press",
    "Side Lateral Raise": "Lateral Raises",
    "Cable Seated Lateral Raise": "Cable Lateral Raise",
    "Cable Rear Delt Fly": "Rear Delt Fly",
    "Reverse Machine Flyes": "Reverse Pec Deck",
    "Machine Shoulder (Military) Press": "Machine Shoulder Press",
    "Front Dumbbell Raise": "Front Raise",
    "Upright Barbell Row": "Upright Row",
    # Pull
    "Bent Over Barbell Row": "Barbell Bent Over Row",
    "One-Arm Dumbbell Row": "Dumbbell Single Arm Row",
    "Seated Cable Rows": "Seated Cable Row",
    "Bent-Arm Dumbbell Pullover": "Cable Pullover",
    "Close-Grip Front Lat Pulldown": "Close Grip Lat Pulldown",
    "One Arm Lat Pulldown": "Single Arm Lat Pulldown",
    "Band Assisted Pull-Up": "Assisted Pull-ups",
    "Pullups": "Pull-ups",
    "V-Bar Pulldown": "Lat Pulldown",
    "Wide-Grip Lat Pulldown": "Wide Grip Lat Pulldown",
    # Arms
    "Dumbbell Bicep Curl": "Dumbbell Curl",
    "Hammer Curls": "Hammer Curl",
    "Cable Hammer Curls - Rope Attachment": "Cable Curl",
    "Concentration Curls": "Concentration Curl",
    "Lying Triceps Press": "Skull Crusher",
    "Dip Machine": "Tricep Dips",
    "Triceps Pushdown - Rope Attachment": "Rope Tricep Pushdown",
    "Triceps Pushdown": "Cable Pushdown",
    "Tricep Dumbbell Kickback": "Tricep Kickback",
    "Standing Dumbbell Triceps Extension": "Overhead Tricep Extension",
    "Cable Rope Overhead Triceps Extension": "Cable Overhead Extension",
    "Palms-Up Barbell Wrist Curl Over A Bench": "Wrist Curl",
    "Palms-Down Wrist Curl Over A Bench": "Reverse Wrist Curl",
    # Core
    "Side Bridge": "Side Plank",
    "V-Up": "V-ups",
    "Bicycle Crunches": "Bicycle Crunch",
    "Dead Bug": "Dead Bugs",
    "Barbell Ab Rollout - On Knees": "Ab Wheel Rollout",
    "Cross-Body Crunch": "Bicycle Crunch",
    # Carry / Functional
    "Farmer's Walk": "Farmer Walk",
    "Kettlebell Turkish Get-Up (Squat style)": "Turkish Get-Up",
    "Goblet Squat": "Kettlebell Goblet Squat",
    "Kettlebell One-Arm Row": "Kettlebell Row",
    # Traps
    "Barbell Shrug": "Barbell Shrugs",
    "Dumbbell Shrug": "Dumbbell Shrugs",
    # Cardio / Conditioning
    "Jogging-Treadmill": "Running",
    "Stationary Bike": "Cycling",
    "Rowing, Stationary": "Rowing Machine",
    "Rope Jumping": "Jump Rope",
    "Battling Ropes": "Battle Ropes",
    "Box Jump (Multiple Response)": "Box Jumps",
    "Burpee": "Burpees",
    # Stretching
    "Butterfly": "Butterfly Stretch",
    "Pigeon": "Piriformis Stretch",
    "Seated Floor Hamstring Stretch": "Standing Hamstring Stretch",
    "Cat Stretch": "Cat-Cow Stretch",
    # Bodyweight
    "Handstand Push-Ups": "Handstand Push-Up",
    "Ring Dips": "Ring Dip",
    "Muscle Up": "Bar Muscle-Up",
    "Straight-Arm Pulldown": "Straight-Arm Lat Pulldown",
    "Nordic Hamstrings": "Nordic Hamstring Curl",
    # Kettlebell
    "Kettlebell Pirate Ships": "Kettlebell Swing",
    "Clean and Press": "Kettlebell Clean and Press",
    "Single-Arm Kettlebell Clean": "Kettlebell Clean",
    "One-Arm Kettlebell Snatch": "Kettlebell Snatch",
    # Band
    "Face Pull": "Band Face Pull",
}

# Alias bidirezionale: nostro nome_en -> FDB name (per ricerche inverse)
REVERSE_ALIASES: dict[str, str] = {v: k for k, v in FDB_NAME_ALIASES.items()}

# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def normalize_name(name: str) -> str:
    """Normalizza nome per matching: lowercase, strip, rimuovi punteggiatura extra."""
    n = name.lower().strip()
    # Rimuovi suffissi tipo " - medium grip", " (version 2)"
    n = re.sub(r"\s*[-–]\s*(medium|wide|narrow|close)\s+grip.*$", "", n, flags=re.IGNORECASE)
    n = re.sub(r"\s*\(.*?\)\s*$", "", n)
    # Normalizza spazi e trattini
    n = re.sub(r"[-_]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def map_muscles(fdb_muscles: list[str]) -> list[str]:
    """Converte lista muscoli FDB → nostri, rimuove duplicati, preserva ordine."""
    seen: set[str] = set()
    result: list[str] = []
    for m in fdb_muscles:
        mapped = FDB_MUSCLE_MAP.get(m.lower())
        if mapped and mapped not in seen:
            seen.add(mapped)
            result.append(mapped)
    return result


def map_category(fdb_exercise: dict) -> str:
    """Mappa categoria FDB → nostra. Raffina con mechanic."""
    cat = FDB_CATEGORY_MAP.get(fdb_exercise.get("category", ""), "compound")
    if cat == "compound" and fdb_exercise.get("mechanic") == "isolation":
        cat = "isolation"
    return cat


def map_equipment(fdb_exercise: dict) -> str:
    """Mappa equipment FDB → nostro."""
    return FDB_EQUIPMENT_MAP.get(fdb_exercise.get("equipment"), "bodyweight")


def map_difficulty(fdb_exercise: dict) -> str:
    """Mappa difficulty FDB → nostro."""
    return FDB_DIFFICULTY_MAP.get(fdb_exercise.get("level", ""), "intermediate")


def infer_pattern(fdb_exercise: dict) -> str:
    """Inferisci pattern_movimento da nome + muscoli + force + category."""
    name_lower = fdb_exercise.get("name", "").lower()
    primary = [m.lower() for m in fdb_exercise.get("primaryMuscles", [])]
    category = fdb_exercise.get("category", "")

    # Categorie dirette
    if category == "stretching":
        return "stretch"
    if category == "cardio":
        return "core"

    # Keywords nel nome (piu' affidabile)
    kw_map = [
        (["squat", "lunge", "leg press", "step up", "step-up", "hack ", "sissy"], "squat"),
        (["deadlift", "rdl", "romanian", "good morning", "hip thrust", "glute bridge",
          "swing", "hyperextension", "back extension", "pull through"], "hinge"),
        (["bench press", "push-up", "push up", "pushup", "floor press", "chest fly",
          "flye", "dip", "chest press", "pec "], "push_h"),
        (["overhead press", "military press", "shoulder press", "lateral raise",
          "front raise", "arnold", "upright row", "pike push"], "push_v"),
        (["row", "bent over", "face pull", "reverse fly", "rear delt",
          "seated cable", "t-bar"], "pull_h"),
        (["pulldown", "pull-up", "pullup", "chin-up", "chinup", "chin up",
          "lat pull", "pull down"], "pull_v"),
        (["crunch", "plank", "sit-up", "sit up", "ab ", "hollow", "v-up",
          "leg raise", "dead bug", "bird dog"], "core"),
        (["twist", "rotation", "woodchop", "pallof", "russian twist",
          "windmill", "landmine rotation"], "rotation"),
        (["carry", "walk", "farmer", "suitcase"], "carry"),
    ]

    for keywords, pattern in kw_map:
        if any(kw in name_lower for kw in keywords):
            return pattern

    # Fallback su muscoli primari
    if "quadriceps" in primary:
        return "squat"
    if any(m in primary for m in ["lower back", "hamstrings", "glutes"]):
        return "hinge"
    if "chest" in primary:
        return "push_h"
    if "shoulders" in primary:
        return "push_v"
    if any(m in primary for m in ["middle back", "lats"]):
        return "pull_h"
    if "biceps" in primary:
        return "pull_h"
    if "triceps" in primary:
        return "push_h"
    if "abdominals" in primary:
        return "core"
    if "forearms" in primary:
        return "carry"
    if "calves" in primary:
        return "squat"
    if "traps" in primary:
        return "pull_v"

    return "core"  # fallback ultimo
