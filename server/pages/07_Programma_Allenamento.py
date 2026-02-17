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

from core.repositories import ClientRepository, WorkoutRepository
from core.models import WorkoutPlanCreate, ProgressRecordCreate
from core.workout_generator_v2 import WorkoutGeneratorV2
from core.error_handler import logger
from core.ui_components import (
    render_card, render_metric_box, render_workout_summary,
    create_section_header, render_success_message, render_error_message,
    render_progress_bar, render_badges, render_status_indicator,
    render_divider, render_exercise_card
)
import json

# PAGE CONFIG
st.set_page_config(page_title="Generatore Programmi", page_icon="🏋️", layout="wide")

# INITIALIZATION
client_repo = ClientRepository()
workout_repo = WorkoutRepository()
workout_gen = WorkoutGeneratorV2()

if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None
if 'show_workout_details' not in st.session_state:
    st.session_state.show_workout_details = False
if 'selected_week' not in st.session_state:
    st.session_state.selected_week = 1

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

    st.markdown("#### 🏋️ Workout Generator V2")
    st.success("✅ Professional Mode", icon="⭐")
    st.caption("500+ esercizi | 5 modelli periodizzazione")

# MAIN CONTENT
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🏋️ Generatore Programmi")
    st.caption("Crea workout personalizzati con IA avanzata")
with col_header2:
    st.metric("Cliente", cliente_info['nome'].split()[0])

st.divider()

# TABS
tab1, tab2, tab3 = st.tabs(["🆕 Genera Nuovo", "📋 Salvati", "📈 Progresso"])

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
        if eq_bands: equipment_list.append("resistance_band")
        if eq_suspension: equipment_list.append("suspension_trainer")
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

        with st.spinner("🔄 Generazione programma professionale..."):
            try:
                workout_plan = workout_gen.generate_professional_workout(
                    client_profile=client_profile,
                    weeks=durata_settimane,
                    periodization_model=periodization_model,
                    sessions_per_week=disponibilita_giorni
                )

                if 'error' in workout_plan:
                    render_error_message(workout_plan['error'])
                else:
                    render_success_message(f"✨ Programma professionale generato con {periodization_model.upper()} periodization!")

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
                            workout_repo.delete_plan(piano.get('id'))
                            render_success_message("Eliminato")
                            st.rerun()
    
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

# FOOTER
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption(f"Cliente: {cliente_info['nome']}")
with col_f2:
    st.caption("v2.0 Premium UI")
with col_f3:
    st.caption(datetime.now().strftime('%d %b %Y - %H:%M'))
