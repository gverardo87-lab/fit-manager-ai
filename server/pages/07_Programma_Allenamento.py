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

from core.crm_db import CrmDBManager
from core.workflow_engine import fitness_workflow
from core.error_handler import logger
from core.ui_components import (
    render_card, render_metric_box, render_workout_summary,
    create_section_header, render_success_message, render_error_message,
    render_progress_bar, render_badges, render_status_indicator,
    render_divider, render_exercise_card
)

# PAGE CONFIG
st.set_page_config(page_title="Generatore Programmi", page_icon="🏋️", layout="wide")

# INITIALIZATION
db = CrmDBManager()

def is_kb_available() -> bool:
    """Controlla dinamicamente se la KB è disponibile"""
    if hasattr(fitness_workflow, 'hybrid_chain') and fitness_workflow.hybrid_chain:
        if fitness_workflow.hybrid_chain.is_kb_loaded():
            return True
    kb_path = Path("knowledge_base/vectorstore")
    if kb_path.is_dir() and (kb_path / "chroma.sqlite3").exists():
        return True
    if fitness_workflow.initialized and fitness_workflow.workout_generator:
        return True
    return False

if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None
if 'show_workout_details' not in st.session_state:
    st.session_state.show_workout_details = False

# SIDEBAR
with st.sidebar:
    st.markdown("### 🏋️ Generatore Programmi")
    clienti = db.get_clienti_attivi()
    
    if not clienti:
        st.error("❌ Nessun cliente attivo")
        st.info("Vai alla sezione Clienti per crearne uno")
        st.stop()
    
    cliente_dict = {f"{c['nome']} {c['cognome']}": c['id'] for c in clienti}
    cliente_nome = st.selectbox("Seleziona Cliente", list(cliente_dict.keys()))
    id_cliente = cliente_dict[cliente_nome]
    cliente_info = db.get_cliente_full(id_cliente)
    
    st.divider()
    
    st.markdown("#### 📚 Knowledge Base")
    kb_available = is_kb_available()
    if kb_available:
        st.success("✅ KB Caricata", icon="✅")
    else:
        st.info("📭 Built-in Mode", icon="ℹ️")

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
    
    col3, col4 = st.columns(2, gap="large")
    
    with col3:
        st.markdown("### 📅 Durata Programma")
        durata_settimane = st.selectbox("Settimane", [4, 6, 8, 12, 16, 24], index=2, label_visibility="collapsed")
    
    with col4:
        st.markdown("### ⚠️ Limitazioni")
        limitazioni = st.text_input("Es: Mal schiena, ginocchio...", label_visibility="collapsed")
    
    st.divider()
    
    st.markdown("### 🏋️ Equipaggiamento")
    col_equip1, col_equip2, col_equip3, col_equip4 = st.columns(4)
    
    with col_equip1:
        pref_bilanciere = st.checkbox("Bilanciere", value=True)
    with col_equip2:
        pref_manubri = st.checkbox("Manubri", value=True)
    with col_equip3:
        pref_cardio = st.checkbox("Cardio", value=False)
    with col_equip4:
        pref_calisthenics = st.checkbox("Calisthenics", value=False)
    
    preferenze = []
    if pref_bilanciere: preferenze.append("bilanciere")
    if pref_manubri: preferenze.append("manubri")
    if pref_cardio: preferenze.append("cardio")
    if pref_calisthenics: preferenze.append("calisthenics")
    
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
        client_profile = {
            'nome': cliente_info['nome'],
            'goal': goal,
            'level': level,
            'age': datetime.now().year - cliente_info.get('data_nascita_year', 1995),
            'disponibilita_giorni': disponibilita_giorni,
            'tempo_sessione_minuti': tempo_sessione,
            'limitazioni': limitazioni or 'Nessuna',
            'preferenze': ', '.join(preferenze) if preferenze else 'Nessuna'
        }
        
        with st.spinner("🔄 Generazione in corso..."):
            try:
                workout_plan = fitness_workflow.generate_personalized_plan(
                    client_profile,
                    weeks=durata_settimane,
                    sessions_per_week=disponibilita_giorni
                )
                
                if 'error' in workout_plan:
                    render_error_message(workout_plan['error'])
                else:
                    # Mostra indicatore KB se usato
                    kb_used = workout_plan.get('kb_used', False)
                    if kb_used:
                        render_success_message(f"✨ Programma generato usando la tua Knowledge Base ({len(workout_plan.get('sources', []))} fonti)")
                    else:
                        st.info("📚 Programma generato con database built-in. Carica più PDF per personalizzazione avanzata!")
                    
                    st.session_state['current_workout'] = workout_plan
                    st.session_state['show_workout_details'] = True
            
            except Exception as e:
                logger.error(f"Errore: {str(e)}")
                render_error_message(f"Errore: {str(e)}")
    
    # ═════════════════════════════════════════════════════════════
    # VISUALIZZAZIONE RISULTATI
    # ═════════════════════════════════════════════════════════════
    
    if st.session_state.get('show_workout_details') and st.session_state.get('current_workout'):
        
        workout = st.session_state['current_workout']
        
        st.divider()
        create_section_header("Programma Generato", f"Per {workout.get('client_name', 'Cliente')}", "📋")
        
        # Summary
        render_workout_summary(
            goal=workout.get('goal', 'N/A').upper(),
            level=workout.get('level', 'N/A').upper(),
            duration=f"{workout.get('duration_weeks', 0)} settimane",
            frequency=f"{workout.get('sessions_per_week', 0)} gg/sett",
            exercises=len(workout.get('weekly_schedule', []))
        )
        
        st.divider()
        
        col_det1, col_det2 = st.columns(2, gap="large")
        
        with col_det1:
            with st.expander("🔬 Metodologia", expanded=True):
                st.markdown(workout.get('methodology', 'N/A'))
        
        with col_det2:
            with st.expander("📈 Progressione", expanded=True):
                st.markdown(workout.get('progressive_overload_strategy', 'N/A'))
        
        with st.expander("📅 Schedule Settimanale", expanded=True):
            for idx, week in enumerate(workout.get('weekly_schedule', [])):
                st.markdown(f"#### Fase {idx + 1}: {week.get('week', 'N/A')}")
                st.text(week.get('content', 'N/A'))
                st.divider()
        
        with st.expander("💪 Dettagli Esercizi", expanded=False):
            st.markdown(workout.get('exercises_details', 'N/A'))
        
        with st.expander("😴 Recovery", expanded=False):
            st.markdown(workout.get('recovery_recommendations', 'N/A'))
        
        with st.expander("📚 Fonti", expanded=False):
            sources = workout.get('sources', [])
            if sources:
                for src in sources:
                    # Le fonti possono essere stringhe o dict
                    if isinstance(src, dict):
                        st.caption(f"**{src.get('source', '?')}** - Pag. {src.get('page', '?')}")
                    else:
                        st.caption(f"📄 {src}")
            else:
                st.info("Programma generato con template built-in")
        
        st.divider()
        
        col_save1, col_save2, col_save3 = st.columns(3)
        
        with col_save1:
            if st.button("💾 Salva", type="primary", use_container_width=True, key="btn_save"):
                try:
                    db.save_workout_plan(id_cliente, workout, date.today())
                    render_success_message("Programma salvato!")
                except Exception as e:
                    render_error_message(f"Errore: {str(e)}")
        
        with col_save2:
            if st.button("🔄 Rigenera", use_container_width=True, key="btn_regen"):
                st.session_state.show_workout_details = False
                st.rerun()
        
        with col_save3:
            if st.button("📥 Esporta", use_container_width=True, key="btn_export"):
                st.info("Esportazione PDF in sviluppo...")

# ═════════════════════════════════════════════════════════════
# TAB 2: PROGRAMMI SALVATI
# ═════════════════════════════════════════════════════════════

with tab2:
    create_section_header("Programmi Salvati", "Gestisci i programmi del cliente", "📋")
    
    try:
        programmi = db.get_workout_plans_for_cliente(id_cliente)
        
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
                            db.delete_workout_plan(piano.get('id'))
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
            db.add_progress_record(id_cliente, date.today(), pushups, vo2, note)
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
