#!/usr/bin/env python3
# server/pages/06_Programma_Allenamento.py
"""
Generatore di Programmi Allenamento - UI Premium v2.0
Interfaccia moderna e interattiva per generare workout personalizzati
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.repositories import ClientRepository, WorkoutRepository, CardImportRepository
from core.models import WorkoutPlanCreate, ProgressRecordCreate
from core.card_parser import CardParser, ParsedCard, ParsedExercise, ParsedCardMetadata
from core.db_migrations import DBMigrations
from core.pattern_extractor import PatternExtractor
from core.workout_ai_pipeline import WorkoutAIPipeline
from core.exercise_archive import ExerciseArchive
from core.repositories import TrainerDNARepository
from core.error_handler import logger
from core.config import DB_CRM_PATH
from core.ui_components import (
    load_custom_css,
    render_card, render_metric_box, render_workout_summary,
    create_section_header, render_success_message, render_error_message,
    render_progress_bar, render_badges, render_status_indicator,
    render_divider, render_exercise_card,
    render_confirm_delete, render_confirm_action
)
import json

# PAGE CONFIG
st.set_page_config(page_title="Generatore Programmi", page_icon=":material/fitness_center:", layout="wide")
load_custom_css()

# INITIALIZATION
DBMigrations(DB_CRM_PATH).run_all()
client_repo = ClientRepository()
workout_repo = WorkoutRepository()
card_import_repo = CardImportRepository()
card_parser = CardParser()

@st.cache_resource
def get_pattern_extractor():
    return PatternExtractor()

@st.cache_resource
def get_ai_pipeline():
    return WorkoutAIPipeline()


if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None
if 'show_workout_details' not in st.session_state:
    st.session_state.show_workout_details = False
if 'selected_week' not in st.session_state:
    st.session_state.selected_week = 1
if 'deleting_plan_id' not in st.session_state:
    st.session_state.deleting_plan_id = None
if 'deleting_card_id' not in st.session_state:
    st.session_state.deleting_card_id = None

# SIDEBAR
with st.sidebar:
    st.markdown("### 🏋️ Generatore Programmi")
    clienti_raw = client_repo.get_all_active()
    clienti = [{'id': c.id, 'nome': c.nome, 'cognome': c.cognome} for c in clienti_raw]
    
    if not clienti:
        st.error("❌ Nessun cliente attivo")
        st.info("Vai alla sezione Clienti per crearne uno")
        st.stop()
    
    cliente_dict = {f"{c['nome']} {c['cognome']}": c['id'] for c in clienti}
    cliente_nome = st.selectbox("Seleziona Cliente", list(cliente_dict.keys()))
    id_cliente = cliente_dict[cliente_nome]
    cliente_obj = client_repo.get_by_id(id_cliente)
    if cliente_obj:
        cliente_info = {
            'id': cliente_obj.id,
            'nome': cliente_obj.nome,
            'cognome': cliente_obj.cognome,
            'lezioni_residue': cliente_obj.lezioni_residue or 0
        }
    else:
        st.error("Cliente non trovato")
        st.stop()

    st.divider()

    st.markdown("#### 🏋️ Workout Generator")
    st.success("✅ Professional Mode", icon="⭐")
    st.caption("174+ esercizi | 5 modelli periodizzazione | 3 modalita'")

# MAIN CONTENT
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🏋️ Generatore Programmi")
    st.caption("Crea workout personalizzati con IA avanzata")
with col_header2:
    st.metric("Cliente", cliente_info['nome'].split()[0])

st.divider()

# TABS
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🆕 Genera Nuovo", "📋 Salvati", "📈 Progresso",
    "📂 Importa Schede", "🧬 Trainer DNA", "🗃️ Archivio Esercizi"
])

# ═════════════════════════════════════════════════════════════
# TAB 1: GENERA NUOVO
# ═════════════════════════════════════════════════════════════

with tab1:
    create_section_header("Configurazione", "Compila i parametri per il programma", "⚙️")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 🎯 Obiettivo")
        goal = st.selectbox(
            "Seleziona l'obiettivo principale",
            ["strength", "hypertrophy", "endurance", "fat_loss", "functional"],
            format_func=lambda x: {
                "strength": "💪 Forza Massimale",
                "hypertrophy": "📦 Ipertrofia (Massa)",
                "endurance": "🏃 Resistenza",
                "fat_loss": "🔥 Perdita Grasso",
                "functional": "⚙️ Funzionale"
            }.get(x, x),
            label_visibility="collapsed"
        )
        
        st.markdown("### 📊 Livello")
        level = st.selectbox(
            "Livello di esperienza",
            ["beginner", "intermediate", "advanced"],
            format_func=lambda x: {
                "beginner": "🟢 Principiante (0-6 mesi)",
                "intermediate": "🟡 Intermedio (6-36 mesi)",
                "advanced": "🔴 Avanzato (36+ mesi)"
            }.get(x, x),
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("### ⏰ Disponibilità")
        disponibilita_giorni = st.slider("Giorni/settimana", 1, 7, 3, label_visibility="collapsed")
        
        st.markdown("### ⏱️ Durata Sessione")
        tempo_sessione = st.slider("Minuti", 30, 180, 60, 15, label_visibility="collapsed")
    
    st.divider()
    
    col3, col4, col5 = st.columns(3, gap="large")

    with col3:
        st.markdown("### 📅 Durata Programma")
        durata_settimane = st.selectbox("Settimane", [4, 6, 8, 12, 16], index=2, label_visibility="collapsed")

    with col4:
        st.markdown("### 🔬 Periodizzazione")
        periodization_model = st.selectbox(
            "Modello Scientifico",
            ["linear", "block", "dup", "conjugate", "rpe"],
            format_func=lambda x: {
                "linear": "📈 Linear (Principianti)",
                "block": "🧱 Block (Intermedi)",
                "dup": "📊 DUP (Avanzati)",
                "conjugate": "⚡ Conjugate (Powerlifting)",
                "rpe": "🎯 RPE Auto-Reg"
            }.get(x, x),
            label_visibility="collapsed"
        )

    with col5:
        st.markdown("### ⚠️ Limitazioni")
        limitazioni = st.text_input("Es: Mal schiena, ginocchio...", label_visibility="collapsed")
    
    st.divider()
    
    st.markdown("### 🏋️ Equipaggiamento Disponibile")

    col_e1, col_e2, col_e3 = st.columns(3)

    with col_e1:
        st.markdown("**Free Weights**")
        eq_barbell = st.checkbox("🏋️ Bilanciere", value=True, key="eq_bar")
        eq_dumbbell = st.checkbox("🔩 Manubri", value=True, key="eq_db")
        eq_kettlebell = st.checkbox("⚫ Kettlebell", value=False, key="eq_kb")
        eq_ez_bar = st.checkbox("〰️ EZ Bar", value=False, key="eq_ez")

    with col_e2:
        st.markdown("**Machines & Cable**")
        eq_machine = st.checkbox("🤖 Macchine", value=True, key="eq_mach")
        eq_cable = st.checkbox("🔌 Cavi", value=True, key="eq_cable")
        eq_smith = st.checkbox("🏗️ Smith Machine", value=False, key="eq_smith")

    with col_e3:
        st.markdown("**Bodyweight & Other**")
        eq_bodyweight = st.checkbox("💪 Corpo Libero", value=True, key="eq_bw")
        eq_bands = st.checkbox("🎀 Bande Elastiche", value=False, key="eq_bands")
        eq_suspension = st.checkbox("🔗 TRX/Anelli", value=False, key="eq_trx")
        eq_cardio = st.checkbox("🏃 Cardio Equipment", value=False, key="eq_cardio")

    st.divider()

    # Modalita' Generazione + Enhancement
    st.markdown("### 🤖 Modalita' Generazione")

    # Check DNA status
    dna_repo = TrainerDNARepository()
    dna_status = dna_repo.get_dna_status() or {}
    dna_cards = dna_status.get('total_cards', 0)
    dna_level = dna_status.get('dna_level', 'none')
    has_dna = dna_cards >= 1

    col_mode, col_ai1, col_ai2 = st.columns([2, 1, 1])

    with col_mode:
        mode_options = ["Solo Archivio"]
        mode_values = ["archive"]
        if has_dna:
            mode_options.append("Solo DNA")
            mode_values.append("dna")
            mode_options.append("Combinata (DNA + Archivio)")
            mode_values.append("combined")

        mode_display = st.selectbox(
            "Scegli la strategia di generazione",
            mode_options,
            index=0,
            help=(
                "**Solo Archivio**: usa 174+ esercizi catalogati + templates scientifici\n\n"
                "**Solo DNA**: usa la struttura delle tue schede importate\n\n"
                "**Combinata**: struttura DNA + selezione dall'archivio"
            ),
            key="gen_mode",
        )
        gen_mode = mode_values[mode_options.index(mode_display)]

        if not has_dna:
            st.caption("Importa almeno 1 scheda per sbloccare DNA e Combinata")
        elif gen_mode != 'archive':
            st.caption(f"DNA {dna_level} - {dna_cards} schede, {dna_status.get('total_patterns', 0)} pattern")

    with col_ai1:
        use_assessment = st.toggle("📋 Assessment", value=True, key="toggle_assessment",
                                    help="Arricchisce profilo da assessment (limitazioni, forza, composizione corporea)")
    with col_ai2:
        use_ai = st.toggle("🧠 Coaching AI", value=True, key="toggle_ai",
                            help="Aggiunge cues tecnici via LLM (richiede Ollama)")

    st.divider()

    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    with col_btn1:
        generate_btn = st.button("🤖 Genera Programma", type="primary", use_container_width=True, key="btn_gen")
    with col_btn2:
        reset_btn = st.button("🔄 Reset", use_container_width=True, key="btn_reset")
    with col_btn3:
        clear_btn = st.button("🗑️ Cancella", use_container_width=True, key="btn_clear")
    
    if reset_btn:
        st.session_state.current_workout = None
        st.session_state.show_workout_details = False
        st.rerun()
    
    if clear_btn:
        st.session_state.messages = []
        st.rerun()
    
    if generate_btn:
        equipment_list = []
        if eq_barbell: equipment_list.append("barbell")
        if eq_dumbbell: equipment_list.append("dumbbell")
        if eq_kettlebell: equipment_list.append("kettlebell")
        if eq_ez_bar: equipment_list.append("ez_bar")
        if eq_machine: equipment_list.append("machine")
        if eq_cable: equipment_list.append("cable")
        if eq_smith: equipment_list.append("smith_machine")
        if eq_bodyweight: equipment_list.append("bodyweight")
        if eq_bands: equipment_list.append("band")
        if eq_suspension: equipment_list.append("trx")
        if eq_cardio: equipment_list.append("cardio_machine")

        client_profile = {
            'nome': cliente_info['nome'],
            'goal': goal,
            'level': level,
            'age': datetime.now().year - cliente_info.get('data_nascita_year', 1995),
            'disponibilita_giorni': disponibilita_giorni,
            'tempo_sessione_minuti': tempo_sessione,
            'limitazioni': limitazioni or 'Nessuna',
            'equipment': equipment_list if equipment_list else ['barbell', 'dumbbell']
        }

        mode_labels = {'archive': 'Solo Archivio', 'dna': 'Solo DNA', 'combined': 'Combinata'}
        spinner_msg = f"🤖 Generazione ({mode_labels.get(gen_mode, gen_mode)})..."

        with st.spinner(spinner_msg):
            try:
                pipeline = get_ai_pipeline()
                workout_plan = pipeline.generate_with_ai(
                    client_id=id_cliente,
                    client_profile=client_profile,
                    weeks=durata_settimane,
                    periodization_model=periodization_model,
                    sessions_per_week=disponibilita_giorni,
                    mode=gen_mode,
                    use_assessment=use_assessment,
                    use_ai=use_ai,
                )

                if 'error' in workout_plan:
                    render_error_message(workout_plan['error'])
                else:
                    ai_meta = workout_plan.get('ai_metadata', {})
                    mode_used = ai_meta.get('mode', gen_mode)
                    parts = [f"Modalita': {mode_labels.get(mode_used, mode_used)}"]
                    if ai_meta.get('assessment_used'):
                        parts.append("Assessment integrato")
                    if ai_meta.get('ai_enhanced'):
                        parts.append(f"{ai_meta.get('coaching_cues_added', 0)} coaching cues AI")
                    render_success_message(f"✨ Programma generato! {' | '.join(parts)}")

                    st.session_state['current_workout'] = workout_plan
                    st.session_state['show_workout_details'] = True
                    st.session_state['selected_week'] = 1

            except Exception as e:
                logger.error(f"Errore: {str(e)}")
                render_error_message(f"Errore generazione: {str(e)}")
    
    # ═════════════════════════════════════════════════════════════
    # VISUALIZZAZIONE RISULTATI
    # ═════════════════════════════════════════════════════════════

    if st.session_state.get('show_workout_details') and st.session_state.get('current_workout'):

        workout = st.session_state['current_workout']

        st.divider()
        create_section_header("Programma Generato", f"Per {workout.get('client_name', 'Cliente')}", "📋")

        # Summary cards
        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        with col_s1:
            st.metric("🎯 Obiettivo", workout.get('goal', 'N/A').upper())
        with col_s2:
            st.metric("📊 Livello", workout.get('level', 'N/A').upper())
        with col_s3:
            st.metric("📅 Durata", f"{len(workout.get('weekly_schedule', {}))} sett.")
        with col_s4:
            st.metric("💪 Split", workout.get('split_type', 'N/A').replace('_', ' ').title())
        with col_s5:
            st.metric("🔬 Modello", workout.get('periodization_model', 'N/A').split()[0])

        st.divider()

        # Week selector
        total_weeks = len(workout.get('weekly_schedule', {}))
        if total_weeks > 0:
            selected_week = st.selectbox(
                "📅 Seleziona Settimana",
                options=list(range(1, total_weeks + 1)),
                index=st.session_state.selected_week - 1,
                format_func=lambda x: f"Settimana {x}"
            )
            st.session_state.selected_week = selected_week

            week_key = f"week_{selected_week}"
            week_data = workout.get('weekly_schedule', {}).get(week_key, {})

            if week_data:
                # Week info
                col_w1, col_w2, col_w3 = st.columns(3)
                with col_w1:
                    focus = week_data.get('focus', 'N/A')
                    if week_data.get('is_deload', False):
                        st.warning(f"⚠️ **DELOAD WEEK** - Focus: {focus}")
                    else:
                        st.info(f"🎯 Focus: **{focus.title()}**")
                with col_w2:
                    st.metric("Intensità", f"{int(week_data.get('intensity_percent', 0) * 100)}%")
                with col_w3:
                    st.metric("Sessioni", len(week_data.get('sessions', {})))

                st.divider()

                # Sessions - LAYOUT COMPATTO SCANNERIZZABILE
                sessions = week_data.get('sessions', {})
                for day_key, session in sessions.items():
                    day_num = day_key.split('_')[1]

                    with st.expander(f"🗓️ **Giorno {day_num}**", expanded=(int(day_num) == 1)):

                        # Warmup compatto
                        warmup = session.get('warmup', {})
                        if warmup and warmup.get('exercises'):
                            warmup_text = " • ".join([ex.get('name', 'N/A') for ex in warmup.get('exercises', [])])
                            st.caption(f"🔥 **Riscaldamento (10'):** {warmup_text}")
                            st.divider()

                        # Main workout - TABELLA COMPATTA
                        main_exercises = session.get('main_workout', [])

                        # Header tabella
                        col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 1, 1, 1, 1])
                        with col_h1:
                            st.markdown("**Esercizio**")
                        with col_h2:
                            st.markdown("**Sets**")
                        with col_h3:
                            st.markdown("**Reps**")
                        with col_h4:
                            st.markdown("**Rest**")
                        with col_h5:
                            st.markdown("**Load**")

                        st.divider()

                        # Lista esercizi COMPATTA
                        for idx, exercise in enumerate(main_exercises, 1):
                            col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns([3, 1, 1, 1, 1])

                            with col_e1:
                                ex_name = exercise.get('italian_name', exercise.get('name', 'N/A'))
                                muscles = exercise.get('primary_muscles', [])
                                muscle_str = muscles[0][:3].upper() if muscles else ''

                                # Nome + Video button inline
                                video_url = exercise.get('video_url', '')
                                if video_url:
                                    if st.button(f"📹", key=f"v_{selected_week}_{day_num}_{idx}", help="Guarda video"):
                                        st.session_state[f'video_{selected_week}_{day_num}_{idx}'] = not st.session_state.get(f'video_{selected_week}_{day_num}_{idx}', False)

                                st.markdown(f"**{idx}. {ex_name}**")
                                st.caption(f"🎯 {muscle_str}")

                            with col_e2:
                                st.markdown(f"**{exercise.get('sets', '-')}**")
                            with col_e3:
                                st.markdown(f"**{exercise.get('reps', '-')}**")
                            with col_e4:
                                st.caption(f"{exercise.get('rest_seconds', 0)}s")
                            with col_e5:
                                intensity = exercise.get('intensity_percent', 0)
                                st.caption(f"{int(intensity*100)}%")

                            # Video embed (se richiesto)
                            if st.session_state.get(f'video_{selected_week}_{day_num}_{idx}', False):
                                st.video(video_url)

                            # Dettagli tecnici (opzionale, non obbligatorio)
                            has_details = (
                                exercise.get('setup_instructions') or
                                exercise.get('execution_steps') or
                                exercise.get('form_cues') or
                                exercise.get('common_mistakes')
                            )

                            if has_details:
                                if st.button(f"📖 Dettagli Tecnici", key=f"detail_{selected_week}_{day_num}_{idx}", help="Mostra dettagli tecnici"):
                                    st.session_state[f'show_detail_{selected_week}_{day_num}_{idx}'] = not st.session_state.get(f'show_detail_{selected_week}_{day_num}_{idx}', False)
                                
                                if st.session_state.get(f'show_detail_{selected_week}_{day_num}_{idx}', False):
                                    detail_tab1, detail_tab2 = st.tabs(["Setup & Esecuzione", "Form & Errori"])

                                    with detail_tab1:
                                        setup = exercise.get('setup_instructions', [])
                                        if setup:
                                            st.markdown("**📋 Setup:**")
                                            for s in setup[:3]:
                                                st.caption(f"• {s}")

                                        execution = exercise.get('execution_steps', [])
                                        if execution:
                                            st.markdown("**🔄 Esecuzione:**")
                                            for e in execution[:4]:
                                                st.caption(f"• {e}")

                                    with detail_tab2:
                                        form_cues = exercise.get('form_cues', [])
                                        if form_cues:
                                            st.markdown("**✅ Punti Chiave:**")
                                            for fc in form_cues[:3]:
                                                st.caption(f"• {fc}")

                                        mistakes = exercise.get('common_mistakes', [])
                                        if mistakes:
                                            st.markdown("**❌ Errori da Evitare:**")
                                            for m in mistakes[:3]:
                                                st.caption(f"• {m}")

                            st.divider()

                        # Cooldown compatto
                        cooldown = session.get('cooldown', {})
                        if cooldown and cooldown.get('exercises'):
                            cooldown_text = " • ".join([ex.get('name', 'N/A') for ex in cooldown.get('exercises', [])])
                            st.caption(f"🧘 **Defaticamento (10'):** {cooldown_text}")

        st.divider()

        # Actions
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)

        with col_act1:
            if st.button("💾 Salva", type="primary", use_container_width=True, key="btn_save"):
                try:
                    plan = WorkoutPlanCreate(
                        id_cliente=id_cliente,
                        data_inizio=date.today(),
                        goal=workout.get('goal'),
                        level=workout.get('level'),
                        duration_weeks=len(workout.get('weekly_schedule', {})),
                        sessions_per_week=workout.get('sessions_per_week'),
                        methodology=workout.get('periodization_model'),
                        weekly_schedule=workout.get('weekly_schedule'),
                        exercises_details=workout.get('exercises_details'),
                        progressive_overload_strategy=workout.get('progressive_overload_strategy'),
                        recovery_recommendations=workout.get('recovery_recommendations'),
                        sources=workout.get('sources'),
                    )
                    workout_repo.save_plan(plan)
                    render_success_message("✅ Programma salvato!")
                except Exception as e:
                    render_error_message(f"❌ Errore: {str(e)}")

        with col_act2:
            if st.button("📥 Download JSON", use_container_width=True, key="btn_json"):
                workout_json = json.dumps(workout, indent=2, ensure_ascii=False)
                st.download_button(
                    label="⬇️ Scarica JSON",
                    data=workout_json,
                    file_name=f"workout_{workout.get('client_name', 'cliente')}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

        with col_act3:
            if st.button("🔄 Rigenera", use_container_width=True, key="btn_regen"):
                st.session_state.show_workout_details = False
                st.rerun()

        with col_act4:
            if st.button("🖨️ Stampa", use_container_width=True, key="btn_print"):
                st.info("📄 Funzione stampa/PDF in sviluppo...")

# ═════════════════════════════════════════════════════════════
# TAB 2: PROGRAMMI SALVATI
# ═════════════════════════════════════════════════════════════

with tab2:
    create_section_header("Programmi Salvati", "Gestisci i programmi del cliente", "📋")
    
    try:
        programmi_raw = workout_repo.get_plans_by_client(id_cliente)
        programmi = [p.model_dump() for p in programmi_raw]
        
        if not programmi:
            st.info("📭 Nessun programma. Creane uno dalla tab Genera Nuovo")
        else:
            for idx, piano in enumerate(programmi):
                with st.expander(
                    f"📅 {piano.get('goal', '?').upper()} - {piano.get('data_inizio', '?')}",
                    expanded=(idx == 0)
                ):
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Goal", piano.get('goal', '?').upper())
                    with col_info2:
                        st.metric("Durata", f"{piano.get('duration_weeks', '?')} sett.")
                    with col_info3:
                        st.metric("Stato", "Attivo" if piano.get('attivo') else "Completato")
                    
                    st.divider()
                    
                    col_act1, col_act2, col_act3 = st.columns(3)
                    with col_act1:
                        if st.button("👁️ Visualizza", key=f"view_{idx}"):
                            st.info("Visualizzazione...")
                    with col_act2:
                        if st.button("📝 Modifica", key=f"edit_{idx}"):
                            st.info("Modifica in sviluppo...")
                    with col_act3:
                        if st.button("🗑️ Elimina", key=f"del_{idx}"):
                            st.session_state.deleting_plan_id = piano.get('id')
                            st.rerun()

                    if st.session_state.deleting_plan_id == piano.get('id'):
                        def _delete_plan(plan_id):
                            workout_repo.delete_plan(plan_id)
                            render_success_message("Programma eliminato")
                        render_confirm_delete(
                            item_id=piano.get('id'),
                            session_key='deleting_plan_id',
                            details=f"Stai per eliminare il programma **{piano.get('nome', 'Senza nome')}**.",
                            confirm_callback=_delete_plan,
                            key_prefix=f"confirm_del_plan_{idx}"
                        )
    
    except Exception as e:
        render_error_message(f"Errore: {str(e)}")

# ═════════════════════════════════════════════════════════════
# TAB 3: PROGRESSO
# ═════════════════════════════════════════════════════════════

with tab3:
    create_section_header("Progresso & Analytics", "Traccia i risultati", "📈")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        render_metric_box("Programmi Completati", "3", "Ultimi 3 mesi", "🏆", "success")
    with col_m2:
        render_metric_box("Aderenza Media", "92%", "Ultimo programma", "✅", "primary")
    with col_m3:
        render_metric_box("Ultimo Update", "Oggi", "18:30", "🕐", "default")
    
    st.divider()
    
    st.markdown("### 📊 Registra Progresso")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        pushups = st.number_input("Push-ups", 0, 100, 0, label_visibility="collapsed")
    with col_p2:
        vo2 = st.number_input("VO2 Max", 0.0, 100.0, 0.0, 0.5, label_visibility="collapsed")
    with col_p3:
        weight = st.number_input("Peso (kg)", 0.0, 500.0, 0.0, 0.1, label_visibility="collapsed")
    
    note = st.text_area("Note", placeholder="Aggiungi note...", label_visibility="collapsed", height=80)
    
    if st.button("💾 Salva Progresso", type="primary", use_container_width=True, key="btn_progress"):
        try:
            record = ProgressRecordCreate(
                id_cliente=id_cliente,
                data=date.today(),
                pushup_reps=pushups if pushups > 0 else None,
                vo2_estimate=vo2 if vo2 > 0 else None,
                note=note if note else None,
            )
            workout_repo.add_progress_record(record)
            render_success_message("✅ Progresso registrato!")
        except Exception as e:
            render_error_message(f"❌ Errore: {str(e)}")

# ═════════════════════════════════════════════════════════════
# TAB 4: IMPORTA SCHEDE
# ═════════════════════════════════════════════════════════════

with tab4:
    create_section_header("Importa Schede Allenamento", "Carica le tue schede Excel/Word per costruire il Trainer DNA", "📂")

    st.info("📌 Importa le schede dei tuoi clienti per permettere all'AI di imparare il tuo stile di programmazione.")

    col_imp1, col_imp2 = st.columns([2, 1], gap="large")

    with col_imp1:
        uploaded_file = st.file_uploader(
            "Carica scheda allenamento",
            type=['xlsx', 'xls', 'docx', 'doc'],
            key="card_uploader",
            help="Formati supportati: Excel (.xlsx, .xls) e Word (.docx, .doc)"
        )

    with col_imp2:
        st.markdown("### 👤 Associa a Cliente")
        assoc_options = {"Template Generico (nessun cliente)": None}
        for c in clienti:
            assoc_options[f"{c['nome']} {c['cognome']}"] = c['id']
        assoc_choice = st.selectbox(
            "Cliente associato",
            list(assoc_options.keys()),
            label_visibility="collapsed",
            key="import_client_select"
        )
        assoc_client_id = assoc_options[assoc_choice]

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
        file_type = "excel" if file_ext in ("xlsx", "xls") else "word"

        if st.button("🔍 Importa e Analizza", type="primary", use_container_width=True, key="btn_import_card"):
            with st.spinner("📊 Analisi della scheda in corso..."):
                try:
                    parsed = card_parser.parse_file(file_bytes, file_name)

                    # Save to DB
                    exercises_data = [
                        {
                            'name': ex.name,
                            'canonical_id': ex.canonical_id,
                            'match_score': ex.match_score,
                            'sets': ex.sets,
                            'reps': ex.reps,
                            'rest_seconds': ex.rest_seconds,
                            'load_note': ex.load_note,
                            'notes': ex.notes,
                            'day_section': ex.day_section,
                        }
                        for ex in parsed.exercises
                    ]
                    metadata_data = {
                        'detected_goal': parsed.metadata.detected_goal,
                        'detected_split': parsed.metadata.detected_split,
                        'detected_weeks': parsed.metadata.detected_weeks,
                        'detected_sessions_per_week': parsed.metadata.detected_sessions_per_week,
                        'trainer_notes': parsed.metadata.trainer_notes,
                        'sheet_names': parsed.metadata.sheet_names,
                        'days_found': getattr(parsed.metadata, 'days_found', []),
                        'client_name': getattr(parsed.metadata, 'client_name', None),
                    }

                    card_id = card_import_repo.save_card(
                        id_cliente=assoc_client_id,
                        file_name=file_name,
                        file_type=file_type,
                        raw_content=parsed.raw_text[:10000],  # limit size
                        parsed_exercises=exercises_data,
                        parsed_metadata=metadata_data,
                    )

                    if card_id:
                        render_success_message(f"✅ Scheda importata! ID: {card_id} - {len(parsed.exercises)} esercizi trovati")
                        st.session_state['last_parsed_card'] = parsed
                        st.session_state['last_card_id'] = card_id
                    else:
                        render_error_message("❌ Errore nel salvataggio della scheda")

                except Exception as e:
                    logger.error(f"Card import error: {e}")
                    render_error_message(f"❌ Errore nell'analisi: {str(e)}")

    # Preview of last parsed card
    if st.session_state.get('last_parsed_card'):
        parsed = st.session_state['last_parsed_card']

        st.divider()
        st.markdown("### 📊 Anteprima Dati Estratti")

        col_prev1, col_prev2, col_prev3, col_prev4 = st.columns(4)
        with col_prev1:
            render_metric_box("Esercizi", str(len(parsed.exercises)), "trovati", "🏋️", "primary")
        with col_prev2:
            conf_pct = f"{int(parsed.parse_confidence * 100)}%"
            conf_color = "success" if parsed.parse_confidence >= 0.7 else "default"
            render_metric_box("Confidenza", conf_pct, "parsing", "🎯", conf_color)
        with col_prev3:
            goal_display = parsed.metadata.detected_goal or "Non rilevato"
            render_metric_box("Goal", goal_display.replace("_", " ").title(), "rilevato", "🎯", "default")
        with col_prev4:
            split_display = parsed.metadata.detected_split or "Non rilevato"
            render_metric_box("Split", split_display.replace("_", " ").title(), "rilevato", "📊", "default")

        # Exercise table
        with st.expander("📋 Esercizi Estratti", expanded=True):
            if parsed.exercises:
                ex_data = []
                for ex in parsed.exercises:
                    match_indicator = "✅" if ex.match_score >= 0.8 else ("🟡" if ex.match_score >= 0.6 else "❌")
                    ex_data.append({
                        "Match": match_indicator,
                        "Esercizio": ex.name,
                        "ID Canonico": ex.canonical_id or "-",
                        "Score": f"{ex.match_score:.0%}",
                        "Serie": ex.sets or "-",
                        "Reps": ex.reps or "-",
                        "Recupero": f"{ex.rest_seconds}s" if ex.rest_seconds else "-",
                        "Carico": ex.load_note or "-",
                    })
                st.dataframe(pd.DataFrame(ex_data), use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Nessun esercizio riconosciuto. Prova un file con formato tabellare.")

        # Metadata
        with st.expander("🔍 Metadata Rilevati"):
            meta_col1, meta_col2 = st.columns(2)
            with meta_col1:
                st.markdown(f"**Goal:** {parsed.metadata.detected_goal or 'Non rilevato'}")
                st.markdown(f"**Split:** {parsed.metadata.detected_split or 'Non rilevato'}")
            with meta_col2:
                st.markdown(f"**Settimane:** {parsed.metadata.detected_weeks or 'Non rilevato'}")
                st.markdown(f"**Sessioni/sett:** {parsed.metadata.detected_sessions_per_week or 'Non rilevato'}")
            if parsed.metadata.trainer_notes:
                st.markdown("**Note del Trainer:**")
                for note_item in parsed.metadata.trainer_notes[:5]:
                    st.caption(f"• {note_item}")

    # Imported cards list
    st.divider()
    st.markdown("### 📚 Schede Importate")

    all_cards = card_import_repo.get_all_cards()
    if not all_cards:
        st.info("📭 Nessuna scheda importata. Carica il tuo primo file Excel/Word!")
    else:
        for card in all_cards:
            client_name = f"{card.get('nome', '')} {card.get('cognome', '')}".strip() or "Template Generico"
            ex_count = len(card.get('parsed_exercises', []) or [])
            status_icon = {
                'parsed': '✅',
                'extracted': '🧬',
                'pending': '⏳',
                'error': '❌',
            }.get(card.get('extraction_status', 'pending'), '❓')

            with st.expander(
                f"{status_icon} **{card['file_name']}** - {client_name} ({ex_count} esercizi)",
                expanded=False
            ):
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                with col_c1:
                    st.metric("Tipo", card.get('file_type', '?').upper())
                with col_c2:
                    st.metric("Esercizi", ex_count)
                with col_c3:
                    st.metric("Stato", card.get('extraction_status', '?'))
                with col_c4:
                    st.metric("Pattern DNA", "Si" if card.get('pattern_extracted') else "No")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if card.get('extraction_status') == 'parsed' and not card.get('pattern_extracted'):
                        if st.button("🧬 Estrai Pattern DNA", key=f"extract_{card['id']}", type="primary"):
                            with st.spinner("🧠 Analisi pattern in corso..."):
                                try:
                                    extractor = get_pattern_extractor()
                                    # Reconstruct ParsedCard from stored data
                                    exercises_raw = card.get('parsed_exercises', []) or []
                                    meta_raw = card.get('parsed_metadata', {}) or {}
                                    p_exercises = [
                                        ParsedExercise(
                                            name=e.get('name', ''),
                                            canonical_id=e.get('canonical_id'),
                                            match_score=e.get('match_score', 0),
                                            sets=e.get('sets'),
                                            reps=e.get('reps'),
                                            rest_seconds=e.get('rest_seconds'),
                                            load_note=e.get('load_note'),
                                            notes=e.get('notes'),
                                        )
                                        for e in exercises_raw
                                    ]
                                    p_card = ParsedCard(
                                        raw_text=card.get('raw_content', ''),
                                        exercises=p_exercises,
                                        metadata=ParsedCardMetadata(
                                            detected_goal=meta_raw.get('detected_goal'),
                                            detected_split=meta_raw.get('detected_split'),
                                            detected_weeks=meta_raw.get('detected_weeks'),
                                            detected_sessions_per_week=meta_raw.get('detected_sessions_per_week'),
                                            trainer_notes=meta_raw.get('trainer_notes', []),
                                            sheet_names=meta_raw.get('sheet_names', []),
                                        ),
                                        parse_confidence=0.0,
                                    )
                                    result = extractor.extract_from_card(card['id'], p_card)
                                    if result.get('success'):
                                        render_success_message(
                                            f"🧬 Pattern estratti! Metodo: {result['method']}, "
                                            f"{result['patterns_saved']} pattern salvati nel DNA"
                                        )
                                        st.rerun()
                                    else:
                                        render_error_message(f"❌ {result.get('error', 'Errore sconosciuto')}")
                                except Exception as e:
                                    logger.error(f"Pattern extraction error: {e}")
                                    render_error_message(f"❌ Errore estrazione: {str(e)}")
                    elif card.get('pattern_extracted'):
                        st.success("🧬 Pattern estratti")
                with col_btn2:
                    if st.button("🗑️ Elimina", key=f"del_card_{card['id']}"):
                        st.session_state.deleting_card_id = card['id']
                        st.rerun()

                if st.session_state.deleting_card_id == card['id']:
                    def _delete_card(card_id):
                        card_import_repo.delete_card(card_id)
                        render_success_message("Scheda eliminata")
                    render_confirm_action(
                        item_id=card['id'],
                        session_key='deleting_card_id',
                        message=f"Vuoi eliminare la scheda **{card.get('nome', 'Importata')}**?",
                        confirm_label="🗑️ Elimina Scheda",
                        confirm_callback=_delete_card,
                        key_prefix=f"confirm_del_card_{card['id']}"
                    )

# ═════════════════════════════════════════════════════════════
# TAB 5: TRAINER DNA DASHBOARD
# ═════════════════════════════════════════════════════════════

with tab5:
    create_section_header("Trainer DNA", "Il sistema impara il tuo stile ad ogni scheda importata", "🧬")

    dna_repo_dash = TrainerDNARepository()
    dna_status_dash = dna_repo_dash.get_dna_status() or {}
    dna_summary = dna_repo_dash.get_active_patterns()

    total_cards = dna_status_dash.get('total_cards', 0)
    total_patterns = dna_status_dash.get('total_patterns', 0)
    avg_conf = dna_status_dash.get('average_confidence', 0)
    dna_level_dash = dna_status_dash.get('dna_level', 'none')

    # Level indicator
    level_config = {
        'learning': {'color': 'default', 'label': 'In Apprendimento', 'icon': '📚', 'progress': 0.2},
        'developing': {'color': 'primary', 'label': 'In Sviluppo', 'icon': '🔬', 'progress': 0.6},
        'established': {'color': 'success', 'label': 'Consolidato', 'icon': '🏆', 'progress': 1.0},
    }
    lconf = level_config.get(dna_level_dash, level_config['learning'])

    col_dna1, col_dna2, col_dna3, col_dna4 = st.columns(4)
    with col_dna1:
        render_metric_box("Schede Importate", str(total_cards), "nel database", "📂", "primary")
    with col_dna2:
        render_metric_box("Pattern Appresi", str(total_patterns), "estratti", "🧬", "primary")
    with col_dna3:
        render_metric_box("Livello DNA", lconf['label'], lconf['icon'], "🎯", lconf['color'])
    with col_dna4:
        render_metric_box("Confidenza Media", f"{int(avg_conf * 100)}%", "dei pattern", "📊", lconf['color'])

    # Progress bar
    st.divider()
    st.markdown("### 📈 Progresso DNA")
    progress_val = min(total_cards / 10, 1.0) if total_cards > 0 else 0.0
    st.progress(progress_val)
    if total_cards == 0:
        st.caption("Importa le tue schede per iniziare a costruire il DNA")
    elif total_cards < 3:
        st.caption(f"📚 Fase di apprendimento - {3 - total_cards} schede al prossimo livello")
    elif total_cards < 10:
        st.caption(f"🔬 DNA in sviluppo - {10 - total_cards} schede per consolidamento")
    else:
        st.caption("🏆 DNA consolidato - il sistema conosce bene il tuo stile!")

    if dna_summary:
        st.divider()

        # Preferred exercises
        with st.expander("🏋️ Esercizi Preferiti", expanded=True):
            if dna_summary.preferred_exercises:
                cols = st.columns(3)
                for i, ex in enumerate(dna_summary.preferred_exercises[:15]):
                    with cols[i % 3]:
                        st.markdown(f"• {ex}")
            else:
                st.info("Nessun esercizio preferito ancora rilevato")

        # Pattern details
        with st.expander("📊 Pattern Estratti"):
            pattern_data = []
            if dna_summary.preferred_set_scheme:
                pattern_data.append({"Tipo": "Schema Set/Reps", "Valore": dna_summary.preferred_set_scheme})
            if dna_summary.preferred_split:
                pattern_data.append({"Tipo": "Split Preferito", "Valore": dna_summary.preferred_split})
            if dna_summary.accessory_philosophy:
                pattern_data.append({"Tipo": "Filosofia Accessori", "Valore": dna_summary.accessory_philosophy})
            if dna_summary.ordering_style:
                pattern_data.append({"Tipo": "Ordine Esercizi", "Valore": dna_summary.ordering_style})

            if pattern_data:
                st.dataframe(pd.DataFrame(pattern_data), use_container_width=True, hide_index=True)
            else:
                st.info("I pattern verranno estratti dopo l'analisi delle schede importate")

        # Pipeline status
        with st.expander("🔧 Stato Pipeline AI"):
            try:
                pipeline = get_ai_pipeline()
                status = pipeline.get_pipeline_status()
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("LLM", "Attivo" if status.get('llm_available') else "Non disponibile")
                with col_s2:
                    st.metric("Methodology RAG", f"{status.get('methodology_docs', 0)} documenti")
                with col_s3:
                    st.metric("DNA Level", status.get('dna_level', 'none'))
            except Exception:
                st.warning("Pipeline AI non ancora inizializzata")
    else:
        st.divider()
        st.info("📭 Nessun pattern DNA disponibile. Importa le tue schede dalla tab 'Importa Schede' e poi estrai i pattern.")

# ═════════════════════════════════════════════════════════════
# TAB 6: ARCHIVIO ESERCIZI
# ═════════════════════════════════════════════════════════════

with tab6:
    create_section_header("Archivio Esercizi", "174+ esercizi catalogati con metadata completa", "🗃️")

    @st.cache_resource
    def get_exercise_archive():
        return ExerciseArchive()

    archive = get_exercise_archive()

    # KPI
    total_count = archive.count()
    col_ak1, col_ak2, col_ak3 = st.columns(3)
    with col_ak1:
        render_metric_box("Esercizi Totali", str(total_count), "nel database", "🏋️", "primary")
    with col_ak2:
        render_metric_box("Pattern", "9", "movement patterns", "🔄", "default")
    with col_ak3:
        render_metric_box("Equipment", "8", "tipologie attrezzi", "🔧", "default")

    st.divider()

    # Filtri
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filter_pattern = st.selectbox(
            "Movement Pattern",
            ["Tutti", "push_h", "push_v", "pull_h", "pull_v", "squat", "hinge", "core", "rotation", "carry"],
            key="arch_pattern"
        )
    with col_f2:
        filter_equipment = st.selectbox(
            "Equipment",
            ["Tutti", "barbell", "dumbbell", "machine", "cable", "bodyweight", "kettlebell", "band", "trx"],
            key="arch_equip"
        )
    with col_f3:
        filter_difficulty = st.selectbox(
            "Difficolta'",
            ["Tutti", "beginner", "intermediate", "advanced"],
            format_func=lambda x: {"Tutti": "Tutti", "beginner": "Principiante", "intermediate": "Intermedio", "advanced": "Avanzato"}.get(x, x),
            key="arch_diff"
        )
    with col_f4:
        filter_search = st.text_input("Cerca per nome", key="arch_search", placeholder="Es: squat, bench...")

    # Carica e filtra
    all_exercises = archive.get_all()
    filtered = all_exercises

    if filter_pattern != "Tutti":
        filtered = [e for e in filtered if e.get('movement_pattern') == filter_pattern]
    if filter_equipment != "Tutti":
        filtered = [e for e in filtered if e.get('equipment') == filter_equipment]
    if filter_difficulty != "Tutti":
        filtered = [e for e in filtered if e.get('difficulty') == filter_difficulty]
    if filter_search:
        search_lower = filter_search.lower()
        filtered = [e for e in filtered if search_lower in (e.get('name', '') + ' ' + (e.get('italian_name') or '')).lower()]

    st.caption(f"Mostrando {len(filtered)} di {total_count} esercizi")

    if filtered:
        # Tabella
        table_data = []
        for ex in filtered:
            muscles = ex.get('primary_muscles', [])
            if isinstance(muscles, str):
                try:
                    muscles = json.loads(muscles)
                except (json.JSONDecodeError, TypeError):
                    muscles = [muscles]
            table_data.append({
                "Nome": ex.get('name', ''),
                "Italiano": ex.get('italian_name') or '-',
                "Pattern": ex.get('movement_pattern', ''),
                "Muscoli": ', '.join(muscles[:3]) if muscles else '-',
                "Equipment": ex.get('equipment', ''),
                "Livello": ex.get('difficulty', ''),
                "Forza": ex.get('rep_range_strength') or '-',
                "Ipertrofia": ex.get('rep_range_hypertrophy') or '-',
            })

        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
            height=500,
        )
    else:
        st.info("Nessun esercizio trovato con i filtri selezionati")

# FOOTER
st.divider()
col_foot1, col_foot2, col_foot3 = st.columns(3)
with col_foot1:
    st.caption(f"Cliente: {cliente_info['nome']}")
with col_foot2:
    st.caption("v3.0 Unified Generator")
with col_foot3:
    st.caption(datetime.now().strftime('%d %b %Y - %H:%M'))
