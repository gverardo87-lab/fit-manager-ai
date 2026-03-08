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
    AnalisiTonnellaggio,
    TonnellaggioSlotAnalisi,
    VolumeEffettivo,
    ContributoEsercizio,
    DettaglioMuscolo,
    DettaglioRapporto,
    DettaglioRecovery,
)
from .muscle_contribution import (
    compute_effective_sets,
    compute_hypertrophy_sets,
    get_contribution,
    _get_hypertrophy_weight,
)
from .volume_model import get_scaled_volume_target, classify_volume
from .balance_ratios import analyze_balance as _analyze_balance, BALANCE_RATIOS
from .load_model import compute_tonnage, classify_intensity_zone


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
    Output: AnalisiPiano con volume, balance, warnings, score + dati strutturati
    """
    warnings: list[str] = []

    # 1. Analisi Volume
    volume_analysis = _analyze_volume(piano, warnings)

    # 2. Analisi Bilanciamento
    balance_analysis = _analyze_plan_balance(piano, warnings)

    # 3. Analisi Frequenza
    freq = _analyze_frequency(piano, warnings)

    # 4. Analisi Recupero
    overlaps = _analyze_recovery(piano, warnings)

    # 5. Analisi Tonnellaggio (opzionale — solo con carico_kg)
    tonnellaggio = _analyze_tonnage(piano)

    # Score composito
    score = _compute_score(volume_analysis, balance_analysis, warnings)

    # ── Dati strutturati per Scientific Analysis Tab ──

    # Contributi per esercizio per muscolo (drill-down)
    dettaglio_muscoli = _build_dettaglio_muscoli(piano, volume_analysis, freq)

    # Dettaglio rapporti biomeccanici
    dettaglio_rapporti = _build_dettaglio_rapporti(piano)

    # Frequenza come dict[str, int]
    frequenza_dict = {m.value: f for m, f in freq.items()}

    # Recovery overlaps strutturati
    recovery_overlaps = _build_recovery_overlaps(piano, overlaps)

    return AnalisiPiano(
        volume=volume_analysis,
        balance=balance_analysis,
        warnings=warnings,
        score=score,
        dettaglio_muscoli=dettaglio_muscoli,
        dettaglio_rapporti=dettaglio_rapporti,
        frequenza_per_muscolo=frequenza_dict,
        recovery_overlaps=recovery_overlaps,
        tonnellaggio=tonnellaggio,
    )


# ════════════════════════════════════════════════════════════
# 1. ANALISI VOLUME
# ════════════════════════════════════════════════════════════


def _analyze_volume(
    piano: TemplatePiano, warnings: list[str]
) -> AnalisiVolume:
    """
    Calcola il volume IPERTROFICO per ogni muscolo e confronta con target.

    Il volume ipertrofico sconta il contributo da stabilizzazione (0.2 → 0)
    e riduce il sinergismo minore (0.4 → 50%), basandosi sulla soglia EMG
    del 40% MVC per lo stimolo ipertrofico (Schoenfeld 2017, Israetel 2020).

    Questo evita di contare volume "fantasma" da stabilizzazione che non
    contribuisce alla crescita muscolare ma infiava i conteggi MRV.
    """
    all_slots: list[tuple[P, int]] = []
    for sessione in piano.sessioni:
        for slot in sessione.slots:
            all_slots.append((slot.pattern, slot.serie))

    hypertrophy = compute_hypertrophy_sets(all_slots)
    volume_totale = sum(hypertrophy.values())

    per_muscolo: list[VolumeEffettivo] = []
    sotto_mev: list[str] = []
    sopra_mrv: list[str] = []

    for muscolo in M:
        target = get_scaled_volume_target(muscolo, piano.livello, piano.obiettivo)
        serie = round(hypertrophy.get(muscolo, 0.0), 1)
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
        session_volume = compute_hypertrophy_sets(session_slots)

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
# DATI STRUTTURATI — Scientific Analysis Tab
# ════════════════════════════════════════════════════════════


def _build_dettaglio_muscoli(
    piano: TemplatePiano,
    volume_analysis: AnalisiVolume,
    freq: dict[M, int],
) -> list[DettaglioMuscolo]:
    """
    Costruisce il dettaglio per muscolo con breakdown dei contributi per esercizio.

    Per ogni muscolo mostra quali esercizi (slot) contribuiscono al volume
    ipertrofico, con il contributo EMG e le serie ipertrofiche risultanti.
    """
    # Raccogli tutti gli slot con nome leggibile
    named_slots: list[tuple[str, P, int]] = []
    for sessione in piano.sessioni:
        for idx, slot in enumerate(sessione.slots, 1):
            nome = f"{sessione.nome} — {slot.pattern.value} #{idx}"
            named_slots.append((nome, slot.pattern, slot.serie))

    dettagli: list[DettaglioMuscolo] = []

    for ve in volume_analysis.per_muscolo:
        muscolo = ve.muscolo
        contributi: list[ContributoEsercizio] = []

        for nome, pattern, serie in named_slots:
            contribution_map = get_contribution(pattern)
            emg = contribution_map.get(muscolo, 0.0)
            if emg <= 0:
                continue

            weight = _get_hypertrophy_weight(emg)
            serie_ipertrofiche = round(serie * weight, 2)

            contributi.append(ContributoEsercizio(
                nome_esercizio=nome,
                pattern=pattern,
                serie=serie,
                contributo_emg=emg,
                serie_ipertrofiche=serie_ipertrofiche,
            ))

        dettagli.append(DettaglioMuscolo(
            muscolo=muscolo,
            serie_effettive=ve.serie_effettive,
            target_mev=ve.target_mev,
            target_mav_min=ve.target_mav_min,
            target_mav_max=ve.target_mav_max,
            target_mrv=ve.target_mrv,
            stato=ve.stato,
            frequenza=freq.get(muscolo, 0),
            contributi=contributi,
        ))

    return dettagli


def _build_dettaglio_rapporti(
    piano: TemplatePiano,
) -> list[DettaglioRapporto]:
    """
    Costruisce il dettaglio per ogni rapporto biomeccanico con volume per lato.

    Espone i dati interni di balance_ratios.py in formato strutturato
    per il drill-down nella tab analisi.
    """
    all_slots: list[tuple[P, int]] = []
    for sessione in piano.sessioni:
        for slot in sessione.slots:
            all_slots.append((slot.pattern, slot.serie))

    effective = compute_effective_sets(all_slots)
    dettagli: list[DettaglioRapporto] = []

    for ratio in BALANCE_RATIOS:
        is_pattern_ratio = ratio.numeratore[0] in {p.value for p in P}

        if is_pattern_ratio:
            num_patterns = {P(v) for v in ratio.numeratore if v in {p.value for p in P}}
            den_patterns = {P(v) for v in ratio.denominatore if v in {p.value for p in P}}
            num_val = sum(s for p, s in all_slots if p in num_patterns)
            den_val = sum(s for p, s in all_slots if p in den_patterns)
        else:
            num_val = sum(
                effective.get(m, 0.0)
                for m in M
                if m.value in ratio.numeratore
            )
            den_val = sum(
                effective.get(m, 0.0)
                for m in M
                if m.value in ratio.denominatore
            )

        if den_val > 0:
            valore = round(num_val / den_val, 2)
        elif num_val > 0:
            valore = 99.0
        else:
            valore = ratio.target

        dettagli.append(DettaglioRapporto(
            nome=ratio.nome,
            valore=valore,
            target=ratio.target,
            tolleranza=ratio.tolleranza,
            in_tolleranza=abs(valore - ratio.target) <= ratio.tolleranza,
            volume_numeratore=round(num_val, 1),
            volume_denominatore=round(den_val, 1),
            fonte=ratio.fonte,
        ))

    return dettagli


def _build_recovery_overlaps(
    piano: TemplatePiano,
    overlaps: list[tuple[str, str, list[str]]],
) -> list[DettaglioRecovery]:
    """
    Costruisce i dettagli di recovery overlap con serie per muscolo in ogni sessione.
    """
    # Pre-calcola volume per sessione
    session_volumes: dict[str, dict[M, float]] = {}
    for sessione in piano.sessioni:
        slots = [(s.pattern, s.serie) for s in sessione.slots]
        session_volumes[sessione.nome] = compute_effective_sets(slots)

    dettagli: list[DettaglioRecovery] = []
    for sess_a_name, sess_b_name, muscles in overlaps:
        vol_a = session_volumes.get(sess_a_name, {})
        vol_b = session_volumes.get(sess_b_name, {})

        dettagli.append(DettaglioRecovery(
            sessione_a=sess_a_name,
            sessione_b=sess_b_name,
            muscoli_overlap=muscles,
            serie_overlap_a={
                m: round(vol_a.get(M(m), 0.0), 1) for m in muscles
            },
            serie_overlap_b={
                m: round(vol_b.get(M(m), 0.0), 1) for m in muscles
            },
        ))

    return dettagli


# ════════════════════════════════════════════════════════════
# 5. ANALISI TONNELLAGGIO (Volume-Load)
# ════════════════════════════════════════════════════════════
#
# Il tonnellaggio e' la metrica gold standard per quantificare il
# carico di allenamento totale (Haff & Triplett, NSCA 2016):
#
#   Tonnellaggio = Σ(serie × rep_medie × carico_kg)
#
# Questa analisi e' OPZIONALE: si attiva solo quando almeno uno
# slot nel piano ha carico_kg compilato. Se nessuno slot ha peso,
# ritorna None e il frontend non mostra la sezione.
#
# L'intensita' relativa (% 1RM) richiede conoscenza del 1RM del
# soggetto. Senza 1RM, vengono comunque calcolati il tonnellaggio
# e le zone NSCA basate sulla tabella NSCA_REP_MAX_PCT.
#
# Fonti:
#   - Haff & Triplett (NSCA 2016) cap. 15 — Volume-Load definition
#   - McBride et al. (2009) — Tonnage as training load metric
#   - Kraemer & Ratamess (2004) — Relative intensity


def _analyze_tonnage(piano: TemplatePiano) -> AnalisiTonnellaggio | None:
    """
    Analisi biomeccanica volume-load con tensione meccanica per muscolo.

    Due livelli:
    1. Tonnellaggio grezzo per slot/sessione — Σ(serie × rep × kg)
    2. Tensione meccanica per muscolo — tonnage × coefficiente EMG

    La tensione meccanica e' il dato biomeccanico reale: quanto carico
    attraversa ogni gruppo muscolare, pesato per il suo livello di
    attivazione in ciascun pattern di movimento.

    Formula per muscolo M:
      tensione[M] = Σ over slots with load:
          (serie × rep_medie × carico_kg) × contribution[pattern][M]

    Esempio: Squat 100kg × 3s × 10r = 3000 kg tonnellaggio grezzo
      - Quadricipiti (EMG 1.0): 3000 × 1.0 = 3000 kg tensione meccanica
      - Glutei (EMG 0.7):       3000 × 0.7 = 2100 kg
      - Core (EMG 0.4):         3000 × 0.4 = 1200 kg
      - Polpacci (EMG 0.2):     3000 × 0.2 =  600 kg

    Fonti:
      - Schoenfeld (2010): tensione meccanica = driver primario ipertrofia
      - Contreras (2010): coefficienti EMG per pattern
      - Haff & Triplett (NSCA 2016): definizione volume-load

    Ritorna None se nessuno slot ha carico_kg compilato.
    """
    from .load_model import get_intensity_for_reps

    has_load = any(
        slot.carico_kg is not None and slot.carico_kg > 0
        for sessione in piano.sessioni
        for slot in sessione.slots
    )
    if not has_load:
        return None

    slot_details: list[TonnellaggioSlotAnalisi] = []
    tonnellaggio_per_sessione: dict[str, float] = {}
    tonnellaggio_totale = 0.0
    zone_counts: dict[str, int] = {}

    # Accumulatori tensione muscolare
    tensione_meccanica: dict[M, float] = {}
    tensione_ipertrofica: dict[M, float] = {}

    for sessione in piano.sessioni:
        session_tonnage = 0.0
        for slot in sessione.slots:
            if slot.carico_kg is None or slot.carico_kg <= 0:
                continue

            rep_medie = (slot.rep_min + slot.rep_max) / 2
            tonnage = compute_tonnage(
                slot.serie, slot.rep_min, slot.rep_max, slot.carico_kg
            )
            session_tonnage += tonnage
            tonnellaggio_totale += tonnage

            # ── Tensione meccanica per muscolo ──
            # tonnage × coefficiente EMG = forza meccanica sul muscolo
            contribution_map = get_contribution(slot.pattern)
            for muscolo, emg_coeff in contribution_map.items():
                # Tensione meccanica: tonnage × EMG (tutto il lavoro meccanico)
                mech = tonnage * emg_coeff
                tensione_meccanica[muscolo] = (
                    tensione_meccanica.get(muscolo, 0.0) + mech
                )

                # Tensione ipertrofica: tonnage × hypertrophy weight
                # (sconta stabilizzatori sotto soglia EMG 40% MVC)
                hyp_weight = _get_hypertrophy_weight(emg_coeff)
                if hyp_weight > 0:
                    hyp = tonnage * hyp_weight
                    tensione_ipertrofica[muscolo] = (
                        tensione_ipertrofica.get(muscolo, 0.0) + hyp
                    )

            # Zona intensita' — tabella NSCA con RIR=2 assumption
            avg_reps = round(rep_medie)
            estimated_pct = get_intensity_for_reps(avg_reps, rir=2.0)
            zona_nome, _ = classify_intensity_zone(estimated_pct)
            zone_counts[zona_nome] = zone_counts.get(zona_nome, 0) + slot.serie

            slot_details.append(TonnellaggioSlotAnalisi(
                pattern=slot.pattern.value,
                sessione=sessione.nome,
                serie=slot.serie,
                rep_medie=round(rep_medie, 1),
                carico_kg=slot.carico_kg,
                tonnellaggio=tonnage,
                intensita_relativa=None,
                zona_intensita=zona_nome,
            ))

        tonnellaggio_per_sessione[sessione.nome] = round(session_tonnage, 1)

    zona_prevalente = None
    if zone_counts:
        zona_prevalente = max(zone_counts, key=zone_counts.get)  # type: ignore[arg-type]

    return AnalisiTonnellaggio(
        tonnellaggio_totale=round(tonnellaggio_totale, 1),
        tonnellaggio_per_sessione=tonnellaggio_per_sessione,
        intensita_media_ponderata=None,
        slot_detail=slot_details,
        zona_prevalente=zona_prevalente,
        tensione_per_muscolo={
            m.value: round(v, 1) for m, v in tensione_meccanica.items()
        },
        tensione_ipertrofica_per_muscolo={
            m.value: round(v, 1) for m, v in tensione_ipertrofica.items()
        },
    )


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
    # Peso differenziato per qualita' della copertura:
    #   "ottimale"  = 1.0 — nel range MAV, stimolo ideale
    #   "sopra_mav" = 0.8 — sopra MAV ma sotto MRV, volume alto ma recuperabile
    #   "mev_mav"   = 0.5 — sopra MEV, stimolo presente ma sub-ottimale
    #   "sotto_mev" = 0.0 — nessuno stimolo
    #   "sopra_mrv" = 0.0 — overtraining, penalizzato (non e' copertura utile)
    _COVERAGE_WEIGHT = {
        "ottimale": 1.0,
        "sopra_mav": 0.8,
        "mev_mav": 0.5,
        "sotto_mev": 0.0,
        "sopra_mrv": 0.0,
    }
    covered = sum(
        _COVERAGE_WEIGHT.get(v.stato, 0.0)
        for v in volume.per_muscolo
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
