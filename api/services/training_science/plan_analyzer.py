"""
Training Science Engine — Analizzatore completo di piani di allenamento.

Questo modulo analizza un piano (generato dal sistema o creato manualmente)
e produce un report scientifico completo su 4 dimensioni:

  1. VOLUME — Serie effettive per muscolo vs target MEV/MAV/MRV
  2. BILANCIAMENTO — Rapporti biomeccanici push:pull, quad:ham, ant:post
  3. FREQUENZA — Quante volte/settimana ogni muscolo e' stimolato
  4. RECUPERO — Overlap muscolare tra sessioni consecutive

L'analisi e' DETERMINISTICA e SPIEGABILE: ogni warning ha una fonte
scientifica e un motivo concreto. Zero black box.

Fonti:
  - Israetel — "Scientific Principles of Hypertrophy Training" (2020)
  - Schoenfeld — "Dose-response for RT volume" (2017)
  - Schoenfeld — "Effects of RT frequency on hypertrophy" (2016)
  - NSCA — "Essentials of Strength Training" (2016) cap. 21-22
  - Sahrmann — "Movement System Impairment Syndromes" (2002)
"""

from .types import (
    PatternMovimento as P,
    GruppoMuscolare as M,
    TemplatePiano,
    AnalisiVolume,
    AnalisiBalance,
    AnalisiPiano,
    VolumeEffettivo,
)
from .muscle_contribution import compute_effective_sets
from .volume_model import get_scaled_volume_target, classify_volume
from .balance_ratios import analyze_balance as _analyze_balance


# ════════════════════════════════════════════════════════════
# SOGLIA RECUPERO — Overlap muscolare tra sessioni consecutive
# ════════════════════════════════════════════════════════════
#
# Il recupero muscolare richiede 48-72h (NSCA 2016).
# Se due sessioni consecutive sollecitano gli stessi muscoli
# con volume significativo, c'e' rischio di recupero incompleto.
#
# Soglia: se un muscolo riceve >= 3 serie effettive in entrambe
# le sessioni consecutive, genera un warning di recupero.
_RECOVERY_OVERLAP_THRESHOLD = 3.0


def analyze_plan(
    piano: TemplatePiano,
) -> AnalisiPiano:
    """
    Analisi completa di un piano di allenamento su 4 dimensioni.

    Input: TemplatePiano (generato o manuale)
    Output: AnalisiPiano con volume, balance, warnings, score
    """
    warnings: list[str] = []

    # 1. Analisi Volume
    volume_analysis = _analyze_volume(piano, warnings)

    # 2. Analisi Bilanciamento
    balance_analysis = _analyze_plan_balance(piano, warnings)

    # 3. Analisi Frequenza
    _analyze_frequency(piano, warnings)

    # 4. Analisi Recupero
    _analyze_recovery(piano, warnings)

    # Score composito
    score = _compute_score(volume_analysis, balance_analysis, warnings)

    return AnalisiPiano(
        volume=volume_analysis,
        balance=balance_analysis,
        warnings=warnings,
        score=score,
    )


# ════════════════════════════════════════════════════════════
# 1. ANALISI VOLUME
# ════════════════════════════════════════════════════════════


def _analyze_volume(
    piano: TemplatePiano, warnings: list[str]
) -> AnalisiVolume:
    """
    Calcola il volume effettivo per ogni muscolo e confronta con target.

    Il volume effettivo e' calcolato dalla matrice di contribuzione EMG:
    ogni esercizio contribuisce proporzionalmente all'attivazione muscolare.
    """
    # Raccogli tutti gli slot del piano
    all_slots: list[tuple[P, int]] = []
    for sessione in piano.sessioni:
        for slot in sessione.slots:
            all_slots.append((slot.pattern, slot.serie))

    effective = compute_effective_sets(all_slots)
    volume_totale = sum(effective.values())

    per_muscolo: list[VolumeEffettivo] = []
    sotto_mev: list[str] = []
    sopra_mrv: list[str] = []

    for muscolo in M:
        target = get_scaled_volume_target(muscolo, piano.livello, piano.obiettivo)
        serie = round(effective.get(muscolo, 0.0), 1)
        stato = classify_volume(serie, target)

        per_muscolo.append(VolumeEffettivo(
            muscolo=muscolo,
            serie_effettive=serie,
            target_mev=target.mev,
            target_mav_min=target.mav_min,
            target_mav_max=target.mav_max,
            target_mrv=target.mrv,
            stato=stato,
        ))

        if stato == "sotto_mev":
            sotto_mev.append(muscolo.value)
            warnings.append(
                f"Volume insufficiente: {muscolo.value} a {serie} serie/sett "
                f"(MEV = {target.mev}). Nessuno stimolo di crescita. "
                f"Fonte: Israetel RP 2020."
            )
        elif stato == "sopra_mrv":
            sopra_mrv.append(muscolo.value)
            warnings.append(
                f"Volume eccessivo: {muscolo.value} a {serie} serie/sett "
                f"(MRV = {target.mrv}). Rischio overtraining e regressione. "
                f"Fonte: Israetel RP 2020."
            )

    return AnalisiVolume(
        per_muscolo=per_muscolo,
        volume_totale_settimana=round(volume_totale, 1),
        muscoli_sotto_mev=sotto_mev,
        muscoli_sopra_mrv=sopra_mrv,
    )


# ════════════════════════════════════════════════════════════
# 2. ANALISI BILANCIAMENTO
# ════════════════════════════════════════════════════════════


def _analyze_plan_balance(
    piano: TemplatePiano, warnings: list[str]
) -> AnalisiBalance:
    """
    Verifica i rapporti biomeccanici del piano.

    I rapporti fuori tolleranza generano warning con fonte e
    indicazione della direzione dello squilibrio.
    """
    all_slots: list[tuple[P, int]] = []
    for sessione in piano.sessioni:
        for slot in sessione.slots:
            all_slots.append((slot.pattern, slot.serie))

    balance = _analyze_balance(all_slots)

    for squilibrio in balance.squilibri:
        warnings.append(f"Squilibrio biomeccanico: {squilibrio}")

    return balance


# ════════════════════════════════════════════════════════════
# 3. ANALISI FREQUENZA
# ════════════════════════════════════════════════════════════


def _analyze_frequency(
    piano: TemplatePiano, warnings: list[str]
) -> dict[M, int]:
    """
    Conta quante sessioni stimolano ogni muscolo.

    Un muscolo e' considerato "stimolato" in una sessione se riceve
    >= 2 serie effettive (soglia minima per contare come stimolo,
    Krieger 2010).

    Fonte: Schoenfeld 2016 — freq >= 2x/settimana superiore a 1x
    per ipertrofia.
    """
    freq: dict[M, int] = {m: 0 for m in M}
    min_series_for_stimulus = 2.0

    for sessione in piano.sessioni:
        session_slots: list[tuple[P, int]] = [
            (slot.pattern, slot.serie) for slot in sessione.slots
        ]
        session_volume = compute_effective_sets(session_slots)

        for muscolo in M:
            if session_volume.get(muscolo, 0.0) >= min_series_for_stimulus:
                freq[muscolo] += 1

    # Warning per muscoli con freq < 2
    for muscolo, f in freq.items():
        if f < 2:
            # Muscoli secondari con MEV=0 possono avere freq < 2 senza problemi
            target = get_scaled_volume_target(muscolo, piano.livello, piano.obiettivo)
            if target.mev > 0:
                warnings.append(
                    f"Frequenza bassa: {muscolo.value} stimolato solo {f}x/settimana. "
                    f"Schoenfeld 2016: freq >= 2x ottimale per MPS."
                )

    return freq


# ════════════════════════════════════════════════════════════
# 4. ANALISI RECUPERO
# ════════════════════════════════════════════════════════════


def _analyze_recovery(
    piano: TemplatePiano, warnings: list[str]
) -> list[tuple[str, str, list[str]]]:
    """
    Verifica l'overlap muscolare tra sessioni consecutive.

    Se due sessioni back-to-back sovraccaricano gli stessi muscoli,
    il recupero puo' essere insufficiente (48-72h, NSCA 2016).

    Ritorna lista di (sessione_a, sessione_b, muscoli_overlap).
    """
    overlaps: list[tuple[str, str, list[str]]] = []

    for i in range(len(piano.sessioni) - 1):
        sess_a = piano.sessioni[i]
        sess_b = piano.sessioni[i + 1]

        vol_a = compute_effective_sets(
            [(s.pattern, s.serie) for s in sess_a.slots]
        )
        vol_b = compute_effective_sets(
            [(s.pattern, s.serie) for s in sess_b.slots]
        )

        overlap_muscles: list[str] = []
        for muscolo in M:
            a = vol_a.get(muscolo, 0.0)
            b = vol_b.get(muscolo, 0.0)
            if a >= _RECOVERY_OVERLAP_THRESHOLD and b >= _RECOVERY_OVERLAP_THRESHOLD:
                overlap_muscles.append(muscolo.value)

        if overlap_muscles:
            overlaps.append((sess_a.nome, sess_b.nome, overlap_muscles))
            warnings.append(
                f"Recupero: {sess_a.nome} → {sess_b.nome} condividono "
                f"volume alto su {', '.join(overlap_muscles)}. "
                f"Considerare 48h di distanza. Fonte: NSCA 2016."
            )

    return overlaps


# ════════════════════════════════════════════════════════════
# SCORE COMPOSITO
# ════════════════════════════════════════════════════════════
#
# Il punteggio e' una sintesi quantitativa della qualita' del piano.
# Non e' un voto scolastico — e' un indicatore per il trainer.
#
# Composizione (trasparente e deterministica):
#   Volume coverage:    40 punti (% muscoli in range MAV)
#   Balance:            25 punti (% rapporti in tolleranza)
#   Frequency:          20 punti (% muscoli con freq >= 2)
#   Recovery:           15 punti (assenza overlap critici)


def _compute_score(
    volume: AnalisiVolume,
    balance: AnalisiBalance,
    warnings: list[str],
) -> float:
    """
    Calcola il punteggio composito 0-100 del piano.

    Ogni componente ha un peso preciso e trasparente.
    Il punteggio e' DETERMINATO dai dati — zero soggettivita'.
    """
    total_muscles = len(volume.per_muscolo)

    # Volume coverage (40 punti)
    # Muscoli con stato "ottimale" o "sopra_mav" contano come coperti
    covered = sum(
        1 for v in volume.per_muscolo
        if v.stato in ("ottimale", "sopra_mav")
    )
    volume_score = (covered / total_muscles) * 40 if total_muscles > 0 else 0

    # Balance (25 punti)
    total_ratios = len(balance.rapporti)
    balanced = total_ratios - len(balance.squilibri)
    balance_score = (balanced / total_ratios) * 25 if total_ratios > 0 else 0

    # Frequency (20 punti)
    freq_warnings = sum(1 for w in warnings if "Frequenza bassa" in w)
    freq_score = max(0, 20 - freq_warnings * 4)

    # Recovery (15 punti)
    recovery_warnings = sum(1 for w in warnings if "Recupero:" in w)
    recovery_score = max(0, 15 - recovery_warnings * 5)

    return round(volume_score + balance_score + freq_score + recovery_score, 1)
