#!/usr/bin/env python3
# file: server/pages/05_Programma_Allenamento.py
# Gestione Programmi di Allenamento Personalizzati con RAG

import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from core.crm_db import CrmDBManager
from core.workflow_engine import fitness_workflow
from core.error_handler import handle_streamlit_errors, logger

db = CrmDBManager()

# ════════════════════════════════════════════════════════════
# DYNAMIC KB CHECK (Non statico, controlla ogni volta)
# ════════════════════════════════════════════════════════════

def is_kb_available() -> bool:
    """Controlla dinamicamente se la KB è disponibile"""
    # Check 1: Se hybrid_chain ha esercizi dal vectorstore
    if hasattr(fitness_workflow, 'hybrid_chain') and fitness_workflow.hybrid_chain:
        if fitness_workflow.hybrid_chain.is_kb_loaded():
            return True
    
    # Check 2: Se il vectorstore fisicamente esiste
    kb_path = Path("knowledge_base/vectorstore")
    if kb_path.is_dir() and (kb_path / "chroma.sqlite3").exists():
        return True
    
    # Check 3: Se il workout_generator è inizializzato
    if fitness_workflow.initialized and fitness_workflow.workout_generator:
        return True
    
    return False


# ════════════════════════════════════════════════════════════
# SIDEBAR: Selezione Cliente
# ════════════════════════════════════════════════════════════

st.sidebar.subheader("👥 Seleziona Cliente")
clienti = db.get_clienti_attivi()

if not clienti:
    st.warning("❌ Nessun cliente attivo. Vai a 👤 Clienti per crearne uno.")
    st.stop()

cliente_dict = {f"{c['nome']} {c['cognome']}": c['id'] for c in clienti}
cliente_nome = st.sidebar.selectbox("Cliente", list(cliente_dict.keys()))
id_cliente = cliente_dict[cliente_nome]

cliente_info = db.get_cliente_full(id_cliente)

st.sidebar.divider()
st.sidebar.markdown("""
### 📊 Informazioni Cliente
- **Livello Fitness**: [a selezionare]
- **Goal Principale**: [a selezionare]
- **Disponibilità**: [giorni/settimana]
""")

# ════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ════════════════════════════════════════════════════════════

st.title("🏋️ Generatore Programmi Allenamento")

# Controllo dinamico della KB
kb_is_available = is_kb_available()

if kb_is_available:
    st.success("✅ Knowledge Base caricata - Puoi generare programmi personalizzati!")
else:
    st.info("""
    ℹ️ **Utilizzando Generator Built-in**
    
    Il sistema usa i template built-in di allenamento.  
    Per personalizzare con la tua knowledge base:
    1. Aggiungi PDF a `knowledge_base/documents/`
    2. Esegui `python knowledge_base/ingest.py`
    3. Aggiorna la pagina per sfruttare i tuoi contenuti
    """)

st.info("""
🤖 **Generazione Intelligente con IA**
Questo modulo usa una knowledge base di metodologie di allenamento per generare 
schede personalizzate basate su:
- Obiettivo (forza, ipertrofia, resistenza, perdita grasso)
- Livello di esperienza
- Disponibilità di tempo e attrezzi
- Limitazioni fisiche o infortuni
""")

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs([
    "🆕 Genera Nuovo Programma",
    "📋 Programmi Salvati",
    "📈 Progresso & Test"
])

# ════════════════════════════════════════════════════════════
# TAB 1: GENERA NUOVO PROGRAMMA
# ════════════════════════════════════════════════════════════

with tab1:
    st.subheader("📝 Configurazione Programma")
    
    # Colonne per i parametri di base
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Obiettivo Principale**")
        goal = st.selectbox(
            "Goal",
            ["strength", "hypertrophy", "endurance", "fat_loss", "functional"],
            format_func=lambda x: {
                "strength": "💪 Forza Massimale",
                "hypertrophy": "📦 Ipertrofia (Massa)",
                "endurance": "🏃 Resistenza Cardio",
                "fat_loss": "🔥 Perdita di Grasso",
                "functional": "⚙️ Fitness Funzionale"
            }.get(x, x)
        )
    
    with col2:
        st.markdown("**📊 Livello di Esperienza**")
        level = st.selectbox(
            "Level",
            ["beginner", "intermediate", "advanced"],
            format_func=lambda x: {
                "beginner": "🟢 Principiante (0-6 mesi)",
                "intermediate": "🟡 Intermedio (6-36 mesi)",
                "advanced": "🔴 Avanzato (36+ mesi)"
            }.get(x, x)
        )
    
    st.divider()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**⏰ Disponibilità Settimanale**")
        disponibilita_giorni = st.slider(
            "Giorni/settimana disponibili",
            min_value=1,
            max_value=7,
            value=3,
            label_visibility="collapsed"
        )
    
    with col4:
        st.markdown("**⏱️ Durata Sessione**")
        tempo_sessione = st.slider(
            "Minuti per sessione",
            min_value=30,
            max_value=180,
            value=60,
            step=15,
            label_visibility="collapsed"
        )
    
    st.divider()
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("**📅 Durata Programma**")
        durata_settimane = st.selectbox(
            "Settimane",
            [4, 6, 8, 12, 16, 24],
            index=0,
            label_visibility="collapsed"
        )
    
    with col6:
        st.markdown("**⚠️ Limitazioni/Infortuni**")
        limitazioni = st.text_input(
            "Descrivi eventuali limitazioni",
            placeholder="es. Mal di schiena, problema ginocchio...",
            label_visibility="collapsed"
        )
    
    st.divider()
    
    st.markdown("**📌 Preferenze Specifiche**")
    
    col7, col8, col9 = st.columns(3)
    
    with col7:
        preferisci_bilanciere = st.checkbox("✅ Bilanciere", value=True)
    
    with col8:
        preferisci_manubri = st.checkbox("✅ Manubri", value=True)
    
    with col9:
        preferisci_cardio = st.checkbox("✅ Cardio", value=False)
    
    preferenze = []
    if preferisci_bilanciere:
        preferenze.append("bilanciere")
    if preferisci_manubri:
        preferenze.append("manubri")
    if preferisci_cardio:
        preferenze.append("cardio")
    
    # ─────────────────────────────────────────────────────────
    # PULSANTE GENERAZIONE
    # ─────────────────────────────────────────────────────────
    
    st.divider()
    
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        # Pulsante sempre disponibile (hybrid fallback a built-in)
        if st.button("🤖 Genera Programma Personalizzato", type="primary", use_container_width=True):
            
            # Profilo cliente per la generazione
            client_profile = {
                'nome': cliente_info['nome'],
                'goal': goal,
                'level': level,
                'age': datetime.now().year - cliente_info.get('data_nascita_year', 1995),
                'disponibilita_giorni': disponibilita_giorni,
                'tempo_sessione_minuti': tempo_sessione,
                'limitazioni': limitazioni or 'Nessuna',
                'preferenze': ', '.join(preferenze) if preferenze else 'Nessuna preferenza'
            }
            
            with st.spinner("🔄 Generazione del programma in corso..."):
                try:
                    # Genera il programma
                    workout_plan = fitness_workflow.generate_personalized_plan(
                        client_profile,
                        weeks=durata_settimane,
                        sessions_per_week=disponibilita_giorni
                    )
                    
                    if 'error' in workout_plan:
                        st.error(f"❌ Errore: {workout_plan['error']}")
                    else:
                        st.success("✅ Programma generato con successo!")
                        
                        # Salva in sessione
                        st.session_state['current_workout'] = workout_plan
                        st.session_state['show_workout_details'] = True
                        
                except Exception as e:
                    logger.error(f"Errore generazione programma: {str(e)}")
                    st.error(f"❌ Errore nella generazione: {str(e)}")
    
    with col_btn2:
        st.button("❌", key="reset_gen", use_container_width=True)
    
    # ─────────────────────────────────────────────────────────
    # VISUALIZZAZIONE PROGRAMMA GENERATO
    # ─────────────────────────────────────────────────────────
    
    if st.session_state.get('show_workout_details') and 'current_workout' in st.session_state:
        
        workout = st.session_state['current_workout']
        
        st.divider()
        st.markdown("## 📊 Programma Generato")
        
        # Metodologia
        with st.expander("🔬 Metodologia", expanded=True):
            st.markdown(workout.get('methodology', 'N/A'))
        
        # Schedule settimanale
        with st.expander("📅 Schedule Settimanale", expanded=True):
            for idx, week in enumerate(workout.get('weekly_schedule', [])):
                st.markdown(f"#### Settimana/Fase {idx + 1}: {week.get('week', 'N/A')}")
                st.text(week.get('content', 'Nessun dettaglio disponibile'))
                st.divider()
        
        # Esercizi dettagliati
        with st.expander("💪 Dettagli Esercizi", expanded=False):
            st.text(workout.get('exercises_details', 'N/A'))
        
        # Progressione
        with st.expander("📈 Strategia di Progressione", expanded=False):
            st.markdown(workout.get('progressive_overload_strategy', 'N/A'))
        
        # Recovery
        with st.expander("😴 Raccomandazioni Recovery", expanded=False):
            st.markdown(workout.get('recovery_recommendations', 'N/A'))
        
        # Fonti
        with st.expander("📚 Fonti Consultate", expanded=False):
            sources = workout.get('sources', [])
            if sources:
                for source in sources:
                    st.write(f"- **{source['source']}**, pag. {source['page']}")
            else:
                st.write("Nessuna fonte disponibile")
        
        # Pulsante salvataggio
        st.divider()
        col_save1, col_save2 = st.columns(2)
        
        with col_save1:
            if st.button("💾 Salva Programma", type="primary", use_container_width=True):
                try:
                    # Salva il programma in DB
                    db_result = db.save_workout_plan(
                        id_cliente=id_cliente,
                        plan_data=workout,
                        data_inizio=date.today()
                    )
                    
                    st.success("✅ Programma salvato con successo!")
                    logger.info(f"Programma salvato per cliente {id_cliente}")
                    
                except Exception as e:
                    st.error(f"❌ Errore salvataggio: {str(e)}")
        
        with col_save2:
            if st.button("🔄 Rigenerare", use_container_width=True):
                st.session_state['show_workout_details'] = False
                st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 2: PROGRAMMI SALVATI
# ════════════════════════════════════════════════════════════

with tab2:
    st.subheader("📋 I Tuoi Programmi Salvati")
    
    # Recupera programmi dal DB
    try:
        programmi = db.get_workout_plans_for_cliente(id_cliente)
        
        if not programmi:
            st.info("📭 Nessun programma salvato ancora. Creane uno dalla tab '🆕 Genera Nuovo Programma'")
        else:
            for idx, piano in enumerate(programmi):
                with st.expander(
                    f"📅 {piano.get('goal', 'Programma')} - {piano.get('data_inizio', 'Data non specificata')}",
                    expanded=(idx == 0)
                ):
                    col_info1, col_info2, col_info3 = st.columns(3)
                    
                    with col_info1:
                        st.metric("Goal", piano.get('goal', 'N/A').upper())
                    
                    with col_info2:
                        st.metric("Livello", piano.get('level', 'N/A').capitalize())
                    
                    with col_info3:
                        st.metric("Durata", f"{piano.get('duration_weeks', '?')} sett.")
                    
                    st.divider()
                    
                    # Breve preview della metodologia
                    st.markdown("**Metodologia:**")
                    st.text(piano.get('methodology', 'N/A')[:300] + "...")
                    
                    # Pulsanti azioni
                    col_act1, col_act2, col_act3 = st.columns(3)
                    
                    with col_act1:
                        if st.button("👁️ Visualizza Completo", key=f"view_{idx}"):
                            st.session_state[f'view_full_{idx}'] = True
                    
                    with col_act2:
                        if st.button("📊 Stampa", key=f"print_{idx}"):
                            st.info("Funzionalità di stampa in sviluppo")
                    
                    with col_act3:
                        if st.button("🗑️ Elimina", key=f"delete_{idx}"):
                            try:
                                db.delete_workout_plan(piano['id'])
                                st.success("✅ Programma eliminato")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Errore: {str(e)}")
                    
                    # Mostra dettagli completi se richiesto
                    if st.session_state.get(f'view_full_{idx}'):
                        st.divider()
                        
                        tabs_detail = st.tabs([
                            "Schedule", "Esercizi", "Progressione", "Recovery", "Fonti"
                        ])
                        
                        with tabs_detail[0]:
                            st.text(piano.get('weekly_schedule', 'N/A'))
                        
                        with tabs_detail[1]:
                            st.text(piano.get('exercises_details', 'N/A'))
                        
                        with tabs_detail[2]:
                            st.markdown(piano.get('progressive_overload_strategy', 'N/A'))
                        
                        with tabs_detail[3]:
                            st.markdown(piano.get('recovery_recommendations', 'N/A'))
                        
                        with tabs_detail[4]:
                            sources = piano.get('sources', [])
                            if sources:
                                for s in sources:
                                    st.write(f"- {s.get('source', '?')}, pag. {s.get('page', '?')}")
    
    except Exception as e:
        st.error(f"❌ Errore nel recupero programmi: {str(e)}")

# ════════════════════════════════════════════════════════════
# TAB 3: PROGRESSO & TEST
# ════════════════════════════════════════════════════════════

with tab3:
    st.subheader("📈 Tracking Progresso")
    
    st.info("""
    📊 Monitora i tuoi progressi nel tempo:
    - Performance dei test
    - Misurazioni corporee
    - Feedback sullo stato fisico
    """)
    
    # Sezione test di performance
    st.markdown("## 🏃 Test di Performance")
    
    col_test1, col_test2 = st.columns(2)
    
    with col_test1:
        st.markdown("**Pushup Test**")
        pushup_reps = st.number_input(
            "Numero di pushup consecutivi",
            min_value=0,
            value=0,
            label_visibility="collapsed"
        )
    
    with col_test2:
        st.markdown("**VO2 Max Estimate**")
        vo2_estimate = st.number_input(
            "ml/kg/min",
            min_value=0.0,
            value=0.0,
            label_visibility="collapsed"
        )
    
    st.divider()
    
    # Note generali
    note_progresso = st.text_area(
        "Note sul tuo progresso",
        placeholder="Come ti senti? Migliori? Difficoltà?",
        height=100
    )
    
    if st.button("💾 Registra Progresso", type="primary", use_container_width=True):
        try:
            db.add_progress_record(
                id_cliente=id_cliente,
                data=date.today(),
                pushup_reps=pushup_reps,
                vo2_estimate=vo2_estimate,
                note=note_progresso
            )
            st.success("✅ Progresso registrato!")
            logger.info(f"Progresso registrato per cliente {id_cliente}")
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()
st.caption("""
🤖 **Powered by**: RAG + Ollama (Local AI, Privacy-First)
📚 **Knowledge Base**: Metodologie allenamento, Anatomia, Biomeccanica
⚠️ **Disclaimer**: Questi programmi sono suggerimenti. Consulta un professionista prima di iniziare.
""")
