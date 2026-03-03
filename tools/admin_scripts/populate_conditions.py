"""
Popola esercizi_condizioni — mapping deterministico esercizio → condizioni mediche.

Per gli esercizi con in_subset=1:
  1. Scansiona campo 'controindicazioni' (JSON array di frasi testuali IT)
  2. Keyword matching → condizioni mediche dal catalogo (47 condizioni)
  3. Pattern-based rules → condizioni aggiuntive (cardiaco, metabolico)
  4. Severita': avoid (controindicazione diretta), caution (rischio, adattare)

v2: +9 condizioni generiche (31-39). Ogni condizione generica include
    le keyword di TUTTE le condizioni specifiche della stessa zona,
    garantendo che il set di esercizi mappati sia un superset.

Zero Ollama. 100% deterministico e replicabile.

Idempotente: pulisce e rigenera ad ogni esecuzione.
Eseguire dalla root:
  python -m tools.admin_scripts.populate_conditions [--db dev|prod|both] [--dry-run]
"""

import argparse
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# KEYWORD → CONDITION MAPPING
# ================================================================
# Ogni entry: (keyword_list, condition_id, severita, nota)
# keyword_list: basta che UNA keyword sia presente nella stringa
# Le keyword sono lowercase, il matching e' case-insensitive

KEYWORD_RULES: list[tuple[list[str], int, str, str]] = [
    # ── SCHIENA / LOMBARE ──
    (["ernia", "hernia discale"], 1, "avoid",
     "Carico assiale e flessione lombare controindicati con ernia discale."),
    (["lombalgia", "mal di schiena", "lombare"], 1, "caution",
     "Monitorare carico assiale. Evitare flessione lombare sotto carico."),
    (["scoliosi"], 3, "caution",
     "Adattare carichi. Evitare sovraccarico asimmetrico."),
    (["stenosi spinale"], 4, "avoid",
     "Compressione spinale: evitare estensione e carico assiale pesante."),
    (["spondilolistesi"], 5, "avoid",
     "Instabilita' vertebrale: evitare iperestensione e carico assiale."),

    # ── CERVICALE / COLLO ──
    (["cervicale", "collo", "cervicobrachialgia"], 2, "caution",
     "Proteggere il rachide cervicale. Evitare compressione assiale."),

    # ── SPALLA ──
    (["subacromiale", "impingement"], 6, "modify",
     "Impingement sub-acromiale: ridurre ROM overhead, usare presa neutra, evitare abduzione >90° sotto carico."),
    (["cuffia dei rotatori", "cuffia rotatori"], 7, "avoid",
     "Lesione cuffia: evitare rotazione esterna sotto carico."),
    (["instabilit" + chr(224) + " scapolare", "instabilit" + chr(224) + " gleno"], 8, "caution",
     "Instabilita' gleno-omerale: ridurre ROM e carico."),
    (["spalla congelata", "capsulite"], 9, "avoid",
     "Capsulite adesiva: evitare forzare ROM."),
    (["spalla", "spalle"], 6, "caution",
     "Attenzione alla spalla: verificare ROM e dolore."),

    # ── GINOCCHIO ──
    (["crociato", "lca"], 10, "avoid",
     "Lesione LCA: evitare taglio, rotazione e carico in valgismo."),
    (["menisco"], 11, "avoid",
     "Lesione menisco: evitare flessione profonda sotto carico."),
    (["femoro-rotulea", "rotula", "sindrome femoro"], 12, "modify",
     "Sindrome femoro-rotulea: limitare flessione a 90 gradi, evitare leg extension a ROM completo."),
    (["artrosi ginocchio", "artrosi grave del ginocchio",
      "artrosi grave delle ginocchia", "gonartrosi"], 13, "modify",
     "Artrosi ginocchio: ridurre carico e impatto. Preferire catena cinetica chiusa con ROM ridotto."),
    (["ginocchio", "ginocchia"], 10, "caution",
     "Attenzione al ginocchio: monitorare allineamento e carico."),

    # ── ANCA ──
    (["artrosi anca", "coxartrosi", "artrosi severa dell'anca",
      "artrosi dell'anca"], 14, "modify",
     "Coxartrosi: ridurre ROM (evitare flessione >90°) e impatto. Preferire esercizi a catena chiusa."),
    (["conflitto femoro-acetabolare", "impingement anca"], 15, "modify",
     "FAI: limitare flessione anca a 90°, evitare adduzione + rotazione interna sotto carico."),
    (["anca"], 14, "caution",
     "Attenzione all'anca: monitorare ROM e dolore."),

    # ── GOMITO ──
    (["epicondilite", "gomito del tennista"], 16, "avoid",
     "Epicondilite: evitare presa stretta e movimenti di polso."),
    (["gomito"], 16, "caution",
     "Attenzione al gomito: monitorare carico in presa e flessione."),

    # ── POLSO ──
    (["tunnel carpale"], 17, "modify",
     "Tunnel carpale: usare presa neutra, evitare estensione polso sotto carico. Grip padded consigliato."),
    (["polso", "avambraccio", "frattura al polso", "frattura al radio"], 17, "caution",
     "Attenzione al polso: adattare presa e ROM."),

    # ── CAVIGLIA / PIEDE ──
    (["fascite plantare", "plantare"], 18, "caution",
     "Fascite plantare: evitare impatto ripetuto."),
    (["caviglia", "achille"], 19, "caution",
     "Instabilita' caviglia: attenzione a equilibrio e impatto."),

    # ── CARDIOVASCOLARE ──
    (["ipertensione", "pressione sanguigna"], 20, "caution",
     "Ipertensione: evitare Valsalva e carichi massimali."),
    (["cardiopatia", "cardiaci gravi", "cardiovascol"], 21, "caution",
     "Patologia cardiovascolare: monitorare FC e intensita'."),
    (["problemi cardiaci"], 20, "caution",
     "Problemi cardiaci: evitare sforzi massimali e apnea prolungata."),

    # ── METABOLICO ──
    (["osteoporosi"], 24, "caution",
     "Osteoporosi: evitare impatto e flessione vertebrale sotto carico."),

    # ── NEUROLOGICO ──
    (["sciatica", "radicolopatia", "nervo sciatico"], 26, "caution",
     "Sciatica: evitare flessione lombare sotto carico."),
    (["piriforme"], 27, "caution",
     "Sindrome piriforme: evitare flessione + rotazione anca."),

    # ── SPECIAL ──
    (["gravidanza"], 29, "caution",
     "Gravidanza: evitare posizioni supine e carichi addominali diretti."),
    (["diastasi"], 30, "avoid",
     "Diastasi retti: evitare crunch, sit-up e pressione intra-addominale."),

    # ═══════════════════════════════════════════════════════
    # CONDIZIONI AGGIUNTIVE (40-47)
    # ═══════════════════════════════════════════════════════

    # ── Fibromialgia (40) ──
    (["fibromialgia", "fibromialgica"], 40, "caution",
     "Fibromialgia: monitorare volume e intensita'. Privilegiare bassa intensita'."),

    # ── Ipermobilita' articolare / EDS (41) ──
    (["ipermobilita", "ehlers", "iper-lassita", "lassita articolare"], 41, "caution",
     "Ipermobilita': evitare ROM estremi. Enfatizzare stabilizzazione attiva."),

    # ── Ipotiroidismo (42) ──
    (["ipotiroidismo", "tiroide"], 42, "caution",
     "Ipotiroidismo: recuperi piu' lunghi, monitorare affaticamento."),

    # ── BPCO (43) ──
    (["bpco", "broncopneumopatia", "enfisema", "bronchite cronica"], 43, "caution",
     "BPCO: evitare apnea, monitorare saturazione e dispnea."),

    # ── Diabete Tipo 1 (44) ──
    (["diabete tipo 1", "diabete insulinodipendente", "insulina"], 44, "caution",
     "Diabete T1: rischio ipoglicemia durante esercizio. Zuccheri rapidi a portata."),

    # ── Neuropatia periferica (45) ──
    (["neuropatia", "formicolio piedi", "perdita sensibilita"], 45, "caution",
     "Neuropatia: attenzione a equilibrio e propriocezione. Evitare superfici instabili."),

    # ── Artrosi spalla (46) ──
    (["artrosi spalla", "artrosi gleno-omerale"], 46, "caution",
     "Artrosi spalla: ridurre ROM overhead e carico eccentrico."),

    # ── Artrosi mani/polsi (47) ──
    (["artrosi mani", "artrosi polso", "rizoartrosi"], 47, "caution",
     "Artrosi mani/polsi: adattare presa, evitare carichi pesanti in grip."),

    # ═══════════════════════════════════════════════════════
    # CONDIZIONI GENERICHE POST-TRAUMATICHE (31-37)
    # Superset: include keyword specifiche + generiche zona
    # ═══════════════════════════════════════════════════════

    # ── Polso/Mano (31) — superset di cond 17 ──
    (["polso", "avambraccio", "tunnel carpale",
      "frattura polso", "frattura radio", "frattura al polso", "frattura al radio"], 31, "caution",
     "Esiti post-traumatici polso: adattare presa e carico sul polso."),

    # ── Ginocchio (32) — superset di cond 10, 11, 12, 13 ──
    (["ginocchio", "ginocchia", "crociato", "lca", "menisco",
      "femoro-rotulea", "rotula", "gonartrosi",
      "frattura ginocchio"], 32, "caution",
     "Esiti post-traumatici ginocchio: monitorare allineamento e carico."),

    # ── Spalla (33) — superset di cond 6, 7, 8, 9 ──
    (["spalla", "spalle", "subacromiale", "impingement",
      "cuffia dei rotatori", "cuffia rotatori",
      "capsulite", "spalla congelata",
      "frattura spalla", "frattura clavicola", "frattura omero",
      "lussazione spalla"], 33, "caution",
     "Esiti post-traumatici spalla: verificare ROM e carico overhead."),

    # ── Caviglia/Piede (34) — superset di cond 18, 19 ──
    (["caviglia", "achille", "fascite plantare", "plantare",
      "frattura caviglia", "frattura piede", "frattura metatarso",
      "distorsione"], 34, "caution",
     "Esiti post-traumatici caviglia: attenzione a equilibrio e impatto."),

    # ── Anca (35) — superset di cond 14, 15 ──
    (["anca", "coxartrosi", "artrosi anca",
      "conflitto femoro-acetabolare", "impingement anca",
      "frattura femore", "frattura anca", "protesi anca"], 35, "caution",
     "Esiti post-traumatici anca: monitorare ROM e carico."),

    # ── Colonna (36) — superset di cond 1, 3, 4, 5 ──
    (["colonna", "vertebrale", "ernia", "hernia discale",
      "scoliosi", "stenosi spinale", "spondilolistesi",
      "frattura vertebrale", "frattura vertebra"], 36, "caution",
     "Esiti post-traumatici colonna: proteggere rachide, evitare carichi assiali pesanti."),

    # ── Gomito (37) — superset di cond 16 ──
    (["gomito", "epicondilite", "gomito del tennista",
      "frattura gomito"], 37, "caution",
     "Esiti post-traumatici gomito: monitorare carico in presa e flessione."),

    # ═══════════════════════════════════════════════════════
    # CONDIZIONI GENERICHE SINTOMATOLOGICHE (38-39)
    # ═══════════════════════════════════════════════════════

    # ── Cervicalgia (38) — superset di cond 2 ──
    (["cervical", "collo", "cervicobrachialgia",
      "ernia cervicale"], 38, "caution",
     "Cervicalgia: proteggere rachide cervicale, evitare compressione e carico overhead."),

    # ── Lombalgia (39) — superset di cond 1 ──
    (["lombalgia", "mal di schiena", "lombare", "schiena",
      "ernia", "hernia discale"], 39, "caution",
     "Lombalgia: proteggere rachide lombare, evitare flessione sotto carico."),
]

# ── Pattern-based rules (NO keyword match needed) ──
# Queste regole si applicano in base a categoria/pattern, non al testo controindicazioni

PATTERN_CONDITION_RULES: list[tuple[dict, int, str, str]] = [

    # ═══════════════════════════════════════════════════════════
    # SPALLA (6, 7, 8, 9, 33, 46)
    # ═══════════════════════════════════════════════════════════

    # ── Conflitto sub-acromiale (6) ──
    ({"pattern_movimento": "push_v"}, 6, "avoid",
     "Push verticale controindicato: compressione sub-acromiale in abduzione/elevazione."),
    ({"pattern_movimento": "pull_v"}, 6, "modify",
     "Pull verticale: ridurre ROM overhead, evitare abduzione >90 gradi."),

    # ── Cuffia dei rotatori (7) ──
    ({"pattern_movimento": "push_v"}, 7, "avoid",
     "Push verticale: rotazione esterna sotto carico controindicata."),
    ({"pattern_movimento": "push_h"}, 7, "modify",
     "Push orizzontale: ridurre carico, presa neutra, evitare ROM estremo."),
    ({"pattern_movimento": "pull_v"}, 7, "modify",
     "Pull verticale: ridurre carico overhead, monitorare dolore."),

    # ── Instabilita' gleno-omerale (8) ──
    ({"pattern_movimento": "push_v"}, 8, "modify",
     "Push verticale: ridurre ROM, evitare end-range. No behind-neck press."),
    ({"pattern_movimento": "push_h"}, 8, "modify",
     "Push orizzontale: evitare abduzione + rotazione esterna a fine ROM."),
    ({"pattern_movimento": "pull_v"}, 8, "modify",
     "Pull verticale: ridurre carico overhead, evitare end-range."),

    # ── Capsulite adesiva (9) ──
    ({"pattern_movimento": "push_v"}, 9, "avoid",
     "Push verticale controindicato: ROM bloccato, forzare aggrava la capsulite."),
    ({"pattern_movimento": "pull_v"}, 9, "avoid",
     "Pull verticale controindicato: trazione su ROM limitato aggrava."),
    ({"pattern_movimento": "push_h"}, 9, "modify",
     "Push orizzontale: ROM limitato dalla capsulite, adattare escursione e carico."),
    ({"pattern_movimento": "pull_h"}, 9, "modify",
     "Pull orizzontale: adattare ROM, monitorare dolore. Evitare estensione forzata."),

    # ── Esiti post-traumatici spalla (33) ──
    ({"pattern_movimento": "push_v"}, 33, "modify",
     "Push verticale post-trauma spalla: ridurre ROM overhead, progressione graduale."),
    ({"pattern_movimento": "pull_v"}, 33, "modify",
     "Pull verticale post-trauma spalla: monitorare ROM overhead, progressione graduale."),

    # ── Artrosi spalla (46) ──
    ({"pattern_movimento": "push_v"}, 46, "modify",
     "Push overhead + artrosi spalla: ridurre ROM e carico, presa neutra."),
    ({"pattern_movimento": "push_h"}, 46, "caution",
     "Push orizzontale + artrosi spalla: monitorare dolore e ROM."),
    ({"pattern_movimento": "pull_h"}, 46, "caution",
     "Pull orizzontale + artrosi spalla: monitorare carico e ROM."),
    ({"pattern_movimento": "pull_v"}, 46, "modify",
     "Pull verticale + artrosi spalla: ridurre ROM overhead, carico moderato."),

    # ═══════════════════════════════════════════════════════════
    # GINOCCHIO (10, 11, 12, 13, 32)
    # ═══════════════════════════════════════════════════════════

    # ── LCA (10) ──
    ({"pattern_movimento": "squat"}, 10, "modify",
     "Squat con LCA: evitare valgismo e rotazione sotto carico. Profondita' controllata."),

    # ── Menisco (11) ──
    ({"pattern_movimento": "squat"}, 11, "modify",
     "Squat con menisco: evitare flessione profonda sotto carico. Max 90 gradi."),

    # ── Femoro-rotulea (12) ──
    ({"pattern_movimento": "squat"}, 12, "modify",
     "Squat con femoro-rotulea: limitare flessione a 90 gradi. Evitare leg extension a ROM completo."),

    # ── Gonartrosi (13) ──
    ({"pattern_movimento": "squat"}, 13, "modify",
     "Squat con gonartrosi: ridurre carico e impatto. Catena chiusa con ROM ridotto."),

    # ── Esiti post-traumatici ginocchio (32) ──
    ({"pattern_movimento": "squat"}, 32, "modify",
     "Squat post-trauma ginocchio: monitorare allineamento, progressione graduale."),

    # ═══════════════════════════════════════════════════════════
    # ANCA (14, 15, 35)
    # ═══════════════════════════════════════════════════════════

    # ── Coxartrosi (14) ──
    ({"pattern_movimento": "squat"}, 14, "modify",
     "Squat con coxartrosi: limitare flessione anca >90 gradi, evitare impatto."),
    ({"pattern_movimento": "hinge"}, 14, "modify",
     "Hinge con coxartrosi: ridurre ROM flessione anca, catena chiusa preferibile."),

    # ── Conflitto femoro-acetabolare (15) ──
    ({"pattern_movimento": "squat"}, 15, "modify",
     "Squat con FAI: limitare flessione anca a 90 gradi. Evitare adduzione + rotazione interna."),
    ({"pattern_movimento": "hinge"}, 15, "modify",
     "Hinge con FAI: limitare flessione anca, monitorare impingement anteriore."),

    # ── Esiti post-traumatici anca (35) ──
    ({"pattern_movimento": "squat"}, 35, "modify",
     "Squat post-trauma anca: monitorare ROM flessione, progressione graduale."),
    ({"pattern_movimento": "hinge"}, 35, "modify",
     "Hinge post-trauma anca: monitorare ROM flessione anca, progressione graduale."),

    # ═══════════════════════════════════════════════════════════
    # COLONNA (3, 4, 5, 36, 38, 39)
    # ═══════════════════════════════════════════════════════════

    # ── Scoliosi (3) ──
    ({"pattern_movimento": "squat"}, 3, "modify",
     "Squat con scoliosi: adattare stance, evitare sovraccarico asimmetrico."),
    ({"pattern_movimento": "hinge"}, 3, "modify",
     "Hinge con scoliosi: monitorare allineamento, carichi simmetrici."),
    ({"pattern_movimento": "carry"}, 3, "modify",
     "Carry con scoliosi: evitare carichi unilaterali pesanti. Preferire bilaterali."),

    # ── Stenosi spinale (4) ──
    ({"pattern_movimento": "squat"}, 4, "avoid",
     "Squat controindicato con stenosi: compressione assiale aggrava la stenosi."),
    ({"pattern_movimento": "hinge"}, 4, "avoid",
     "Hinge controindicato con stenosi: carico assiale + estensione aggravano stenosi."),
    ({"pattern_movimento": "carry"}, 4, "avoid",
     "Carry controindicato con stenosi: carico assiale su colonna stenotica."),

    # ── Spondilolistesi (5) ──
    ({"pattern_movimento": "squat"}, 5, "avoid",
     "Squat controindicato con spondilolistesi: carico assiale con iperestensione."),
    ({"pattern_movimento": "hinge"}, 5, "avoid",
     "Hinge controindicato con spondilolistesi: iperestensione lombare pericolosa."),
    ({"pattern_movimento": "carry"}, 5, "modify",
     "Carry con spondilolistesi: solo carichi moderati, postura strettamente controllata."),

    # ── Esiti post-traumatici colonna (36) ──
    ({"pattern_movimento": "squat"}, 36, "modify",
     "Squat post-trauma colonna: proteggere rachide, progressione graduale."),
    ({"pattern_movimento": "hinge"}, 36, "modify",
     "Hinge post-trauma colonna: proteggere rachide lombare, carichi moderati."),

    # ── Cervicalgia (38) ──
    ({"pattern_movimento": "push_v"}, 38, "modify",
     "Push verticale con cervicalgia: compressione cervicale, ridurre carico overhead."),

    # ── Lombalgia (39) ──
    ({"pattern_movimento": "hinge"}, 39, "modify",
     "Hinge con lombalgia: proteggere rachide lombare. Evitare flessione sotto carico pesante."),
    ({"pattern_movimento": "squat"}, 39, "modify",
     "Squat con lombalgia: monitorare carico assiale, profondita' controllata."),

    # ═══════════════════════════════════════════════════════════
    # CAVIGLIA / PIEDE (18, 19, 34)
    # ═══════════════════════════════════════════════════════════

    # ── Fascite plantare (18) ──
    ({"categoria": "cardio"}, 18, "modify",
     "Cardio con fascite plantare: evitare impatto ripetuto. Preferire bike/ellittica."),
    ({"pattern_movimento": "squat"}, 18, "caution",
     "Squat con fascite plantare: calzatura adeguata, monitorare dolore plantare."),

    # ── Instabilita' caviglia (19) ──
    ({"categoria": "cardio"}, 19, "modify",
     "Cardio con caviglia instabile: evitare cambi di direzione. Preferire bike."),
    ({"pattern_movimento": "squat"}, 19, "caution",
     "Squat con caviglia instabile: monitorare stabilita', evitare squat profondi."),

    # ── Esiti post-traumatici caviglia (34) ──
    ({"categoria": "cardio"}, 34, "modify",
     "Cardio post-trauma caviglia: impatto progressivo, preferire bike inizialmente."),

    # ═══════════════════════════════════════════════════════════
    # POLSO / MANO / GOMITO (31, 37, 47)
    # ═══════════════════════════════════════════════════════════

    # ── Esiti post-traumatici polso (31) ──
    ({"pattern_movimento": "pull_h"}, 31, "modify",
     "Pull orizzontale post-trauma polso: adattare presa, grip padded consigliato."),
    ({"pattern_movimento": "carry"}, 31, "modify",
     "Carry post-trauma polso: adattare presa, carichi moderati, straps se necessario."),

    # ── Esiti post-traumatici gomito (37) ──
    ({"pattern_movimento": "push_h"}, 37, "modify",
     "Push orizzontale post-trauma gomito: monitorare carico articolare gomito."),
    ({"pattern_movimento": "pull_h"}, 37, "modify",
     "Pull orizzontale post-trauma gomito: monitorare flessione sotto carico."),

    # ── Artrosi mani/polsi (47) ──
    ({"pattern_movimento": "pull_h"}, 47, "modify",
     "Pull orizzontale con artrosi mani: adattare presa, grip padded consigliato."),
    ({"pattern_movimento": "carry"}, 47, "modify",
     "Carry con artrosi mani: ridurre presa, usare straps se necessario."),
    ({"pattern_movimento": "push_h"}, 47, "modify",
     "Push orizzontale con artrosi mani: monitorare dolore in presa."),

    # ═══════════════════════════════════════════════════════════
    # CARDIOVASCOLARE (20, 21, 22)
    # ═══════════════════════════════════════════════════════════

    # ── Ipertensione (20) ──
    ({"categoria": "compound"}, 20, "modify",
     "Compound con ipertensione: evitare Valsalva e carichi massimali. Monitorare PA."),
    ({"categoria": "cardio"}, 20, "caution",
     "Attivita' cardio: monitorare FC in soggetti ipertesi."),

    # ── Cardiopatia (21) ──
    ({"categoria": "compound"}, 21, "modify",
     "Compound con cardiopatia: monitorare FC, sforzo graduato. Evitare massimali."),

    # ── Insufficienza cardiaca (22) ──
    ({"categoria": "compound"}, 22, "avoid",
     "Compound controindicato: elevata domanda cardiaca pericolosa con insufficienza."),
    ({"categoria": "cardio"}, 22, "modify",
     "Cardio con insufficienza cardiaca: solo bassa intensita', monitoraggio FC stretto."),

    # ═══════════════════════════════════════════════════════════
    # METABOLICO (23, 24, 25)
    # ═══════════════════════════════════════════════════════════

    # ── Diabete T2 (23) ──
    ({"categoria": "compound"}, 23, "caution",
     "Compound con diabete T2: monitorare glicemia prima e dopo esercizio."),
    ({"categoria": "cardio"}, 23, "caution",
     "Cardio con diabete T2: rischio ipoglicemia, monitorare glicemia."),

    # ── Osteoporosi (24) ──
    ({"pattern_movimento": "squat"}, 24, "caution",
     "Squat: carico assiale benefico ma moderare intensita' con osteoporosi."),
    ({"pattern_movimento": "hinge"}, 24, "caution",
     "Hinge: carico assiale benefico ma moderare con osteoporosi."),

    # ── Obesita' BMI>35 (25) ──
    ({"pattern_movimento": "squat"}, 25, "modify",
     "Squat con obesita' grave: adattare stance, profondita' limitata, proteggere ginocchia."),
    ({"categoria": "cardio"}, 25, "modify",
     "Cardio con obesita' grave: basso impatto, preferire bike/nuoto. Progressione graduale."),
    ({"categoria": "compound"}, 25, "caution",
     "Compound con obesita' grave: adattare tecnica per ROM limitato."),

    # ═══════════════════════════════════════════════════════════
    # NEUROLOGICO (26, 27, 45)
    # ═══════════════════════════════════════════════════════════

    # ── Sciatica (26) ──
    ({"pattern_movimento": "hinge"}, 26, "modify",
     "Hinge con sciatica: evitare flessione lombare sotto carico. Monitorare irradiazione."),
    ({"pattern_movimento": "squat"}, 26, "caution",
     "Squat con sciatica: monitorare sintomi nervosi, profondita' controllata."),

    # ── Piriforme (27) ──
    ({"pattern_movimento": "hinge"}, 27, "modify",
     "Hinge con piriforme: evitare flessione + rotazione anca simultanea."),
    ({"pattern_movimento": "squat"}, 27, "caution",
     "Squat con piriforme: evitare squat profondo, monitorare dolore gluteo."),

    # ── Neuropatia periferica (45) ──
    ({"categoria": "cardio"}, 45, "modify",
     "Cardio con neuropatia: rischio caduta. Evitare superfici instabili, preferire bike."),
    ({"categoria": "compound"}, 45, "caution",
     "Compound con neuropatia: attenzione propriocezione. Evitare esercizi su una gamba."),

    # ═══════════════════════════════════════════════════════════
    # RESPIRATORIO (28, 43)
    # ═══════════════════════════════════════════════════════════

    # ── Asma da sforzo (28) ──
    ({"categoria": "cardio"}, 28, "caution",
     "Cardio: attenzione con asma da sforzo, preriscaldamento adeguato."),

    # ── BPCO (43) ──
    ({"categoria": "cardio"}, 43, "caution",
     "Cardio + BPCO: evitare apnea, monitorare saturazione e dispnea."),

    # ═══════════════════════════════════════════════════════════
    # REUMATOLOGICO (40, 41)
    # ═══════════════════════════════════════════════════════════

    # ── Fibromialgia (40) ──
    ({"categoria": "compound"}, 40, "caution",
     "Compound + fibromialgia: monitorare volume e intensita'. Preferire carichi moderati."),

    # ── Ipermobilita' / EDS (41) ──
    ({"pattern_movimento": "stretch"}, 41, "avoid",
     "Stretching controindicato: mai stirare articolazioni ipermobili."),
    ({"pattern_movimento": "mobility"}, 41, "avoid",
     "Mobilita' controindicata: non aumentare ROM gia' eccessivo."),
    ({"categoria": "compound"}, 41, "modify",
     "Compound con ipermobilita': evitare end-range e lock-out. Enfatizzare stabilizzazione attiva."),

    # ═══════════════════════════════════════════════════════════
    # SPECIAL (29, 30, 42, 44)
    # ═══════════════════════════════════════════════════════════

    # ── Gravidanza (29) ──
    ({"pattern_movimento": "core"}, 29, "modify",
     "Core + gravidanza: solo esercizi in posizione laterale o quadrupedia. Evitare posizione supina dopo 20 settimane."),

    # ── Diastasi (30) ──
    ({"pattern_movimento": "core"}, 30, "modify",
     "Core + diastasi: solo esercizi in posizione laterale o quadrupedia. Evitare crunch, sit-up, plank frontale."),

    # ── Ipotiroidismo (42) ──
    ({"categoria": "compound"}, 42, "modify",
     "Compound + ipotiroidismo: recuperi 3-5 min, volume ridotto (-20%). Monitorare affaticamento."),

    # ── Diabete T1 (44) ──
    ({"categoria": "cardio"}, 44, "caution",
     "Cardio + diabete T1: rischio ipoglicemia. Zuccheri rapidi a portata."),
]


from api.services.condition_rules import match_keywords as _match_keywords


def process_db(db_path: str, dry_run: bool = False) -> dict:
    """Processa un singolo database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Carica esercizi subset
    exercises = conn.execute(
        "SELECT id, nome, controindicazioni, categoria, pattern_movimento "
        "FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchall()

    # Carica condizioni per verifica
    conditions = {
        row[0]: row[1]
        for row in conn.execute("SELECT id, nome FROM condizioni_mediche").fetchall()
    }

    stats = {"exercises": len(exercises), "mappings": 0, "exercises_with_conditions": 0}

    if not dry_run:
        # Pulisci mapping esistenti per subset
        subset_ids = [e[0] for e in exercises]
        if subset_ids:
            placeholders = ",".join("?" * len(subset_ids))
            conn.execute(
                f"DELETE FROM esercizi_condizioni WHERE id_esercizio IN ({placeholders})",
                subset_ids,
            )

    all_mappings: list[tuple[int, int, str, str]] = []

    for ex_id, ex_nome, ex_controindicazioni, ex_cat, ex_pattern in exercises:
        exercise_conditions: dict[int, tuple[str, str]] = {}  # condition_id → (severita, nota)

        # 1. Parse controindicazioni JSON
        contra_texts: list[str] = []
        if ex_controindicazioni:
            try:
                parsed = json.loads(ex_controindicazioni)
                if isinstance(parsed, list):
                    contra_texts = [str(t) for t in parsed]
            except (json.JSONDecodeError, TypeError):
                pass

        # 2. Keyword matching su ogni testo controindicazione
        full_text = " ".join(contra_texts)
        for keywords, cond_id, severity, nota in KEYWORD_RULES:
            if cond_id not in conditions:
                continue
            if _match_keywords(full_text, keywords):
                # Prendi la severita' piu' alta (avoid > caution > modify)
                existing = exercise_conditions.get(cond_id)
                if existing is None or (severity == "avoid" and existing[0] != "avoid"):
                    exercise_conditions[cond_id] = (severity, nota)

        # 3. Pattern-based rules (override keyword severity, never downgrade from avoid)
        for rule_filter, cond_id, severity, nota in PATTERN_CONDITION_RULES:
            if cond_id not in conditions:
                continue
            match = True
            for key, val in rule_filter.items():
                actual = {"categoria": ex_cat, "pattern_movimento": ex_pattern}.get(key)
                if actual != val:
                    match = False
                    break
            if match:
                existing = exercise_conditions.get(cond_id)
                if existing is None:
                    exercise_conditions[cond_id] = (severity, nota)
                elif existing[0] != "avoid":
                    # Pattern rule sovrascrive caution/modify da keyword
                    # con severita' clinica specifica per pattern movimento.
                    # Mai degradare da avoid (keyword).
                    exercise_conditions[cond_id] = (severity, nota)

        # Accumula mapping
        for cond_id, (sev, nota) in exercise_conditions.items():
            all_mappings.append((ex_id, cond_id, sev, nota))

        if exercise_conditions:
            stats["exercises_with_conditions"] += 1

    stats["mappings"] = len(all_mappings)

    if not dry_run and all_mappings:
        conn.executemany(
            "INSERT INTO esercizi_condizioni (id_esercizio, id_condizione, severita, nota) "
            "VALUES (?, ?, ?, ?)",
            all_mappings,
        )
        conn.commit()

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Popola esercizi_condizioni (deterministico)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true", help="Simula senza scrivere")
    args = parser.parse_args()

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(("DEV", os.path.join(BASE_DIR, "crm_dev.db")))
    if args.db in ("prod", "both"):
        dbs.append(("PROD", os.path.join(BASE_DIR, "crm.db")))

    for label, path in dbs:
        if not os.path.exists(path):
            print(f"  SKIP {label}: {path} non trovato")
            continue
        print(f"\n=== {label} ({path}) ===")
        stats = process_db(path, dry_run=args.dry_run)
        mode = "DRY RUN" if args.dry_run else "SCRITTO"
        print(f"  Esercizi processati: {stats['exercises']}")
        print(f"  Esercizi con condizioni: {stats['exercises_with_conditions']}")
        print(f"  Mapping totali: {stats['mappings']} [{mode}]")


if __name__ == "__main__":
    main()
