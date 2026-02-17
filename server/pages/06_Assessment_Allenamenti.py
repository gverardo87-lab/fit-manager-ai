# file: server/pages/04_Assessment_Allenamenti.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from core.crm_db import CrmDBManager
from core.repositories import ClientRepository
import os

db = CrmDBManager()
client_repo = ClientRepository()

st.set_page_config(page_title="Assessment & Allenamenti", page_icon="🏋️", layout="wide")

st.title("🏋️ Assessment & Programmi Allenamento")

st.info("""
📋 **Gestione Professionale Assessment PT**
- Assessment iniziale completo (45-60 minuti di colloquio)
- Followup mensili / variabili
- Timeline di progressione visuale
- Tracking completo di misure e performance
""")

# ════════════════════════════════════════════════════════════
# SIDEBAR: Selezione cliente
# ════════════════════════════════════════════════════════════

st.sidebar.subheader("👥 Seleziona Cliente")
clienti_raw = client_repo.get_all_active()
clienti = [{'id': c.id, 'nome': c.nome, 'cognome': c.cognome} for c in clienti_raw]

if not clienti:
    st.warning("Nessun cliente attivo nel sistema. Crea un cliente in 👤 Clienti")
    st.stop()

cliente_dict = {f"{c['nome']} {c['cognome']}" : c['id'] for c in clienti}
cliente_nome = st.sidebar.selectbox("Cliente", list(cliente_dict.keys()))
id_cliente = cliente_dict[cliente_nome]

cliente_obj = client_repo.get_by_id(id_cliente)
if cliente_obj:
    cliente_info = {
        'id': cliente_obj.id,
        'nome': cliente_obj.nome,
        'cognome': cliente_obj.cognome,
        'lezioni_residue': cliente_obj.crediti_residui or 0
    }
else:
    st.error("Cliente non trovato")
    st.stop()
assessment_initial = db.get_assessment_initial(id_cliente)

st.sidebar.divider()
st.sidebar.write(f"**📋 Pagina di Assessment e Allenamento**")
st.sidebar.info("🔙 Per modificare anagrafica e contratti, vai a **👤 Clienti**")

# ════════════════════════════════════════════════════════════
# MAIN TABS
# ════════════════════════════════════════════════════════════

if assessment_initial:
    # Cliente ha già assessment iniziale
    tab1, tab2, tab3 = st.tabs([
        "📊 Profilo & Timeline",
        "➕ Nuovo Followup",
        "📈 Grafici Progressione"
    ])
else:
    # Cliente senza assessment iniziale
    tab1, tab2 = st.tabs([
        "📋 Nuovo Assessment Iniziale",
        "❓ Info"
    ])

# ════════════════════════════════════════════════════════════
# TAB 1: PROFILO CLIENTE & TIMELINE (o Assessment Iniziale)
# ════════════════════════════════════════════════════════════

if assessment_initial:
    # ─── CLIENT PROFILE ───
    with tab1:
        st.subheader("📊 Profilo Attuale Cliente")
        
        # Mostra foto se disponibili
        col_foto1, col_foto2, col_foto3 = st.columns(3)
        
        if assessment_initial.get('foto_fronte_path') and os.path.exists(assessment_initial['foto_fronte_path']):
            with col_foto1:
                st.image(assessment_initial['foto_fronte_path'], caption="Fronte", use_container_width=True)
        
        if assessment_initial.get('foto_lato_path') and os.path.exists(assessment_initial['foto_lato_path']):
            with col_foto2:
                st.image(assessment_initial['foto_lato_path'], caption="Lato", use_container_width=True)
        
        if assessment_initial.get('foto_dietro_path') and os.path.exists(assessment_initial['foto_dietro_path']):
            with col_foto3:
                st.image(assessment_initial['foto_dietro_path'], caption="Dietro", use_container_width=True)
        
        st.divider()
        
        # Metriche attuali
        latest_followup = db.get_assessment_followup_latest(id_cliente)
        current_data = latest_followup if latest_followup else assessment_initial
        
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        
        with col_m1:
            st.metric("💪 Peso", f"{current_data.get('peso_kg', 'N/A')} kg")
        with col_m2:
            st.metric("📊 Massa Grassa", f"{current_data.get('massa_grassa_pct', 'N/A')}%")
        with col_m3:
            st.metric("📏 Petto", f"{current_data.get('circonferenza_petto_cm', 'N/A')} cm")
        with col_m4:
            st.metric("⭕ Vita", f"{current_data.get('circonferenza_vita_cm', 'N/A')} cm")
        with col_m5:
            st.metric("🦵 Quadricipite", f"{current_data.get('circonferenza_quadricipite_sx_cm', 'N/A')} cm")
        
        st.divider()
        
        # TIMELINE ASSESSMENTS
        st.subheader("📋 Timeline Assessments")
        
        timeline = db.get_assessment_timeline(id_cliente)
        
        for i, item in enumerate(timeline):
            data = item['data']
            tipo = item['type']
            
            if tipo == 'initial':
                with st.expander(f"🟢 **ASSESSMENT INIZIALE** - {data.get('data_assessment', 'N/A')}", expanded=(i==0)):
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.write("**Antropometria**")
                        st.write(f"• Altezza: {data.get('altezza_cm')} cm")
                        st.write(f"• Peso: {data.get('peso_kg')} kg")
                        st.write(f"• Massa Grassa: {data.get('massa_grassa_pct')}%")
                        st.write(f"• Petto: {data.get('circonferenza_petto_cm')} cm")
                        st.write(f"• Vita: {data.get('circonferenza_vita_cm')} cm")
                        st.write(f"• Fianchi: {data.get('circonferenza_fianchi_cm')} cm")
                        st.write(f"• Bicipite SX: {data.get('circonferenza_bicipite_sx_cm')} cm")
                        st.write(f"• Bicipite DX: {data.get('circonferenza_bicipite_dx_cm')} cm")
                        st.write(f"• Quadricipite SX: {data.get('circonferenza_quadricipite_sx_cm')} cm")
                        st.write(f"• Quadricipite DX: {data.get('circonferenza_quadricipite_dx_cm')} cm")
                        st.write(f"• Coscia SX: {data.get('circonferenza_coscia_sx_cm')} cm")
                        st.write(f"• Coscia DX: {data.get('circonferenza_coscia_dx_cm')} cm")
                    
                    with col_info2:
                        st.write("**Test di Forza**")
                        st.write(f"• Push-up: {data.get('pushups_reps')} reps")
                        if data.get('pushups_note'):
                            st.caption(f"  Note: {data['pushups_note']}")
                        
                        st.write(f"• Panca: {data.get('panca_peso_kg')} kg x {data.get('panca_reps')} reps")
                        if data.get('panca_note'):
                            st.caption(f"  Note: {data['panca_note']}")
                        
                        st.write(f"• Rematore: {data.get('rematore_peso_kg')} kg x {data.get('rematore_reps')} reps")
                        if data.get('rematore_note'):
                            st.caption(f"  Note: {data['rematore_note']}")
                        
                        st.write(f"• Lat Machine: {data.get('lat_machine_peso_kg')} kg x {data.get('lat_machine_reps')} reps")
                        if data.get('lat_machine_note'):
                            st.caption(f"  Note: {data['lat_machine_note']}")
                        
                        st.write(f"• Squat Bastone: {data.get('squat_bastone_note', 'N/A')}")
                        st.write(f"• Squat Macchina: {data.get('squat_macchina_peso_kg')} kg x {data.get('squat_macchina_reps')} reps")
                        if data.get('squat_macchina_note'):
                            st.caption(f"  Note: {data['squat_macchina_note']}")
                    
                    st.divider()
                    
                    col_mob1, col_mob2 = st.columns(2)
                    
                    with col_mob1:
                        st.write("**Mobilità**")
                        st.write(f"• Spalle: {data.get('mobilita_spalle_note', 'N/A')}")
                        st.write(f"• Gomiti: {data.get('mobilita_gomiti_note', 'N/A')}")
                        st.write(f"• Polsi: {data.get('mobilita_polsi_note', 'N/A')}")
                        st.write(f"• Anche: {data.get('mobilita_anche_note', 'N/A')}")
                        st.write(f"• Schiena: {data.get('mobilita_schiena_note', 'N/A')}")
                    
                    with col_mob2:
                        st.write("**Anamnesi**")
                        st.write(f"**Infortuni Pregessi**")
                        st.text_area("", value=data.get('infortuni_pregessi', 'Nessuno'), disabled=True, height=60, key=f"infortuni_pregessi_init_{i}")
                        
                        st.write(f"**Infortuni Attuali**")
                        st.text_area("", value=data.get('infortuni_attuali', 'Nessuno'), disabled=True, height=60, key=f"infortuni_attuali_init_{i}")
                        
                        st.write(f"**Limitazioni**")
                        st.text_area("", value=data.get('limitazioni', 'Nessuna'), disabled=True, height=60, key=f"limitazioni_init_{i}")
                    
                    st.divider()
                    
                    st.write("**Goals**")
                    col_goal1, col_goal2 = st.columns(2)
                    with col_goal1:
                        st.write("Quantificabili:")
                        st.text_area("", value=data.get('goals_quantificabili', ''), disabled=True, height=80, key=f"goals_quant_{i}")
                    with col_goal2:
                        st.write("Benessere:")
                        st.text_area("", value=data.get('goals_benessere', ''), disabled=True, height=80, key=f"goals_ben_{i}")
                    
                    st.divider()
                    
                    st.write("**Note Colloquio**")
                    st.text_area("", value=data.get('note_colloquio', ''), disabled=True, height=100, key=f"note_colloquio_{i}")
            
            else:  # followup
                delta_peso = ""
                delta_vita = ""
                
                if i > 0:
                    prev_data = timeline[i-1]['data']
                    if prev_data.get('peso_kg') and data.get('peso_kg'):
                        delta_peso = f" ({data['peso_kg'] - prev_data['peso_kg']:+.1f} kg)"
                    if prev_data.get('circonferenza_vita_cm') and data.get('circonferenza_vita_cm'):
                        delta_vita = f" ({data['circonferenza_vita_cm'] - prev_data['circonferenza_vita_cm']:+.1f} cm)"
                
                with st.expander(f"🔵 **FOLLOWUP** - {data.get('data_followup', 'N/A')}{delta_peso}{delta_vita}"):
                    col_fu1, col_fu2 = st.columns(2)
                    
                    with col_fu1:
                        st.write("**Misure**")
                        st.write(f"• Peso: {data.get('peso_kg')} kg")
                        st.write(f"• Massa Grassa: {data.get('massa_grassa_pct')}%")
                        st.write(f"• Petto: {data.get('circonferenza_petto_cm')} cm")
                        st.write(f"• Vita: {data.get('circonferenza_vita_cm')} cm")
                        st.write(f"• Fianchi: {data.get('circonferenza_fianchi_cm')} cm")
                        st.write(f"• Bicipite SX: {data.get('circonferenza_bicipite_sx_cm')} cm")
                        st.write(f"• Bicipite DX: {data.get('circonferenza_bicipite_dx_cm')} cm")
                        st.write(f"• Quadricipite SX: {data.get('circonferenza_quadricipite_sx_cm')} cm")
                        st.write(f"• Quadricipite DX: {data.get('circonferenza_quadricipite_dx_cm')} cm")
                        st.write(f"• Coscia SX: {data.get('circonferenza_coscia_sx_cm')} cm")
                        st.write(f"• Coscia DX: {data.get('circonferenza_coscia_dx_cm')} cm")
                    
                    with col_fu2:
                        st.write("**Performance Test**")
                        st.write(f"• Push-up: {data.get('pushups_reps')} reps")
                        st.write(f"• Panca: {data.get('panca_peso_kg')} kg x {data.get('panca_reps')} reps")
                        st.write(f"• Rematore: {data.get('rematore_peso_kg')} kg x {data.get('rematore_reps')} reps")
                        st.write(f"• Squat: {data.get('squat_peso_kg')} kg x {data.get('squat_reps')} reps")
                    
                    st.divider()
                    
                    st.write("**Progresso Goals**")
                    st.text_area("", value=data.get('goals_progress', ''), disabled=True, height=80, key=f"goals_progress_fu_{data['id']}")
                    
                    st.write("**Note Followup**")
                    st.text_area("", value=data.get('note_followup', ''), disabled=True, height=80, key=f"note_followup_fu_{data['id']}")

else:
    # ─── NUOVO ASSESSMENT INIZIALE ───
    with tab1:
        st.subheader("📋 Assessment Iniziale Completo")
        st.info("Compila il form con i dati raccolti durante il colloquio di 45-60 minuti")
        
        # Form in espandibili per organizzare meglio
        with st.form("form_assessment_initial", clear_on_submit=True):
            
            # SEZIONE 1: ANTROPOMETRIA
            with st.expander("📏 Antropometria Base", expanded=True):
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    altezza_cm = st.number_input("Altezza (cm)", min_value=100, max_value=250, value=170)
                with col_a2:
                    peso_kg = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=75.0, step=0.1)
                with col_a3:
                    massa_grassa_pct = st.number_input("Massa Grassa (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.1)
            
            # SEZIONE 2: CIRCONFERENZE
            with st.expander("📐 Circonferenze Corporee", expanded=True):
                col_c1, col_c2, col_c3 = st.columns(3)
                
                with col_c1:
                    circ_petto = st.number_input("Petto (cm)", min_value=50.0, max_value=150.0, value=100.0, step=0.1)
                    circ_vita = st.number_input("Vita (cm)", min_value=40.0, max_value=150.0, value=80.0, step=0.1)
                    circ_fianchi = st.number_input("Fianchi (cm)", min_value=50.0, max_value=150.0, value=95.0, step=0.1)
                
                with col_c2:
                    circ_bic_sx = st.number_input("Bicipite SX (cm)", min_value=15.0, max_value=60.0, value=30.0, step=0.1)
                    circ_bic_dx = st.number_input("Bicipite DX (cm)", min_value=15.0, max_value=60.0, value=30.0, step=0.1)
                    circ_quad_sx = st.number_input("Quadricipite SX (cm)", min_value=30.0, max_value=80.0, value=55.0, step=0.1)
                
                with col_c3:
                    circ_quad_dx = st.number_input("Quadricipite DX (cm)", min_value=30.0, max_value=80.0, value=55.0, step=0.1)
                    circ_coscia_sx = st.number_input("Coscia SX (cm)", min_value=30.0, max_value=80.0, value=55.0, step=0.1)
                    circ_coscia_dx = st.number_input("Coscia DX (cm)", min_value=30.0, max_value=80.0, value=55.0, step=0.1)
            
            # SEZIONE 3: TEST DI FORZA
            with st.expander("💪 Test di Forza", expanded=True):
                
                st.write("**Push-up**")
                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    pushup_note = st.text_input("Note esecuzione (es: a terra, su ginocchia)", placeholder="")
                with col_p2:
                    pushup_reps = st.number_input("Reps", min_value=0, value=10, step=1)
                
                st.divider()
                
                st.write("**Panca Piana**")
                col_pb1, col_pb2, col_pb3 = st.columns([2, 1, 1])
                with col_pb1:
                    panca_note = st.text_input("Note postura/esecuzione", placeholder="")
                with col_pb2:
                    panca_peso = st.number_input("Peso (kg)", min_value=0.0, value=40.0, step=0.5)
                with col_pb3:
                    panca_reps = st.number_input("Reps##panca", min_value=0, value=10, step=1)
                
                st.divider()
                
                st.write("**Rematore**")
                col_rem1, col_rem2, col_rem3 = st.columns([2, 1, 1])
                with col_rem1:
                    rem_note = st.text_input("Note esecuzione", placeholder="")
                with col_rem2:
                    rem_peso = st.number_input("Peso (kg)##rem", min_value=0.0, value=40.0, step=0.5)
                with col_rem3:
                    rem_reps = st.number_input("Reps##rem", min_value=0, value=10, step=1)
                
                st.divider()
                
                st.write("**Lat Machine**")
                col_lat1, col_lat2, col_lat3 = st.columns([2, 1, 1])
                with col_lat1:
                    lat_note = st.text_input("Note esecuzione##lat", placeholder="")
                with col_lat2:
                    lat_peso = st.number_input("Peso (kg)##lat", min_value=0.0, value=40.0, step=0.5)
                with col_lat3:
                    lat_reps = st.number_input("Reps##lat", min_value=0, value=10, step=1)
                
                st.divider()
                
                st.write("**Squat**")
                col_sq1, col_sq2 = st.columns(2)
                with col_sq1:
                    squat_bastone_note = st.text_area("Squat con Bastone - Note esecuzione/postura", placeholder="", height=60)
                with col_sq2:
                    sq_peso = st.number_input("Squat Macchina - Peso (kg)", min_value=0.0, value=60.0, step=0.5)
                    sq_reps = st.number_input("Squat Macchina - Reps", min_value=0, value=10, step=1)
                    squat_macchina_note = st.text_input("Squat Macchina - Note", placeholder="")
            
            # SEZIONE 4: MOBILITÀ
            with st.expander("🧘 Test di Mobilità", expanded=True):
                col_mob1, col_mob2 = st.columns(2)
                
                with col_mob1:
                    mob_spalle = st.text_area("Mobilità Spalle", placeholder="Note su ROM e eventuali limitazioni", height=60)
                    mob_gomiti = st.text_area("Mobilità Gomiti", placeholder="", height=60)
                    mob_polsi = st.text_area("Mobilità Polsi", placeholder="", height=60)
                
                with col_mob2:
                    mob_anche = st.text_area("Mobilità Anche", placeholder="", height=60)
                    mob_schiena = st.text_area("Mobilità Schiena", placeholder="", height=60)
            
            # SEZIONE 5: ANAMNESI
            with st.expander("⚠️ Anamnesi Medica & Limitazioni", expanded=True):
                col_an1, col_an2 = st.columns(2)
                
                with col_an1:
                    infortuni_pregessi = st.text_area("Infortuni Passati", placeholder="Descrivere eventuali infortuni pregessi rilevanti", height=80)
                    infortuni_attuali = st.text_area("Infortuni/Dolori Attuali", placeholder="Limitazioni attuali", height=80)
                
                with col_an2:
                    limitazioni = st.text_area("Altre Limitazioni", placeholder="Es: allergie, problemi articolari, ecc", height=80)
                    storia_medica = st.text_area("Storia Medica Rilevante", placeholder="Patologie, interventi chirurgici, ecc", height=80)
            
            # SEZIONE 6: GOALS
            with st.expander("🎯 Goals Quantificabili & Benessere", expanded=True):
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    goals_quant = st.text_area("Goals Quantificabili", placeholder="Es: perdere 5kg, guadagnare 3kg muscolo, squattare 100kg, ecc", height=100)
                
                with col_g2:
                    goals_benessere = st.text_area("Goals Benessere Personale", placeholder="Es: sentirmi più forte, energia, postura, ecc", height=100)
            
            # SEZIONE 7: FOTO & NOTE FINALI
            with st.expander("📸 Foto & Note Finali"):
                st.write("**Upload Foto (opzionale)**")
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    foto_fronte = st.file_uploader("Foto Fronte", type=["jpg", "jpeg", "png"], key="foto_fronte")
                
                with col_f2:
                    foto_lato = st.file_uploader("Foto Lato", type=["jpg", "jpeg", "png"], key="foto_lato")
                
                with col_f3:
                    foto_dietro = st.file_uploader("Foto Dietro", type=["jpg", "jpeg", "png"], key="foto_dietro")
                
                st.divider()
                
                note_colloquio = st.text_area("Note Finali Colloquio", placeholder="Osservazioni generali, comportamento, motivazione, ecc", height=100)
            
            # BOTTONE SALVA
            col_submit1, col_submit2 = st.columns([2, 1])
            with col_submit1:
                submitted = st.form_submit_button("💾 Salva Assessment Iniziale", type="primary", use_container_width=True)
            
            if submitted:
                # Salva foto se uploadate
                foto_paths = {}
                
                if foto_fronte:
                    foto_dir = st.session_state.get("foto_dir", f"data/foto/{id_cliente}")
                    os.makedirs(foto_dir, exist_ok=True)
                    fronte_path = f"{foto_dir}/fronte.jpg"
                    with open(fronte_path, "wb") as f:
                        f.write(foto_fronte.getbuffer())
                    foto_paths['foto_fronte_path'] = fronte_path
                
                if foto_lato:
                    foto_dir = st.session_state.get("foto_dir", f"data/foto/{id_cliente}")
                    os.makedirs(foto_dir, exist_ok=True)
                    lato_path = f"{foto_dir}/lato.jpg"
                    with open(lato_path, "wb") as f:
                        f.write(foto_lato.getbuffer())
                    foto_paths['foto_lato_path'] = lato_path
                
                if foto_dietro:
                    foto_dir = st.session_state.get("foto_dir", f"data/foto/{id_cliente}")
                    os.makedirs(foto_dir, exist_ok=True)
                    dietro_path = f"{foto_dir}/dietro.jpg"
                    with open(dietro_path, "wb") as f:
                        f.write(foto_dietro.getbuffer())
                    foto_paths['foto_dietro_path'] = dietro_path
                
                # Preparare dati per salvataggio
                dati_assessment = {
                    'altezza_cm': altezza_cm,
                    'peso_kg': peso_kg,
                    'massa_grassa_pct': massa_grassa_pct,
                    'circonferenza_petto_cm': circ_petto,
                    'circonferenza_vita_cm': circ_vita,
                    'circonferenza_bicipite_sx_cm': circ_bic_sx,
                    'circonferenza_bicipite_dx_cm': circ_bic_dx,
                    'circonferenza_fianchi_cm': circ_fianchi,
                    'circonferenza_quadricipite_sx_cm': circ_quad_sx,
                    'circonferenza_quadricipite_dx_cm': circ_quad_dx,
                    'circonferenza_coscia_sx_cm': circ_coscia_sx,
                    'circonferenza_coscia_dx_cm': circ_coscia_dx,
                    'pushups_reps': pushup_reps,
                    'pushups_note': pushup_note,
                    'panca_peso_kg': panca_peso,
                    'panca_reps': panca_reps,
                    'panca_note': panca_note,
                    'rematore_peso_kg': rem_peso,
                    'rematore_reps': rem_reps,
                    'rematore_note': rem_note,
                    'lat_machine_peso_kg': lat_peso,
                    'lat_machine_reps': lat_reps,
                    'lat_machine_note': lat_note,
                    'squat_bastone_note': squat_bastone_note,
                    'squat_macchina_peso_kg': sq_peso,
                    'squat_macchina_reps': sq_reps,
                    'squat_macchina_note': squat_macchina_note,
                    'mobilita_spalle_note': mob_spalle,
                    'mobilita_gomiti_note': mob_gomiti,
                    'mobilita_polsi_note': mob_polsi,
                    'mobilita_anche_note': mob_anche,
                    'mobilita_schiena_note': mob_schiena,
                    'infortuni_pregessi': infortuni_pregessi,
                    'infortuni_attuali': infortuni_attuali,
                    'limitazioni': limitazioni,
                    'storia_medica': storia_medica,
                    'goals_quantificabili': goals_quant,
                    'goals_benessere': goals_benessere,
                    'note_colloquio': note_colloquio,
                    **foto_paths
                }
                
                # Salva nel database
                db.save_assessment_initial(id_cliente, dati_assessment)
                
                st.success("✅ Assessment Iniziale Salvato!")
                st.balloons()
                st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 2: NUOVO FOLLOWUP (solo se assessment initial esiste)
# ════════════════════════════════════════════════════════════

if assessment_initial:
    with tab2:
        st.subheader("➕ Nuovo Followup Assessment")
        st.info("Compila il followup mensile (o secondo frequenza cliente)")
        
        with st.form("form_followup", clear_on_submit=True):
            
            with st.expander("📐 Misure Corporee", expanded=True):
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    peso_fu = st.number_input("Peso (kg)##fu", min_value=30.0, max_value=200.0, value=float(assessment_initial.get('peso_kg', 75)), step=0.1)
                    massa_grassa_fu = st.number_input("Massa Grassa (%)##fu", min_value=0.0, max_value=100.0, value=float(assessment_initial.get('massa_grassa_pct', 20)), step=0.1)
                
                with col_f2:
                    circ_petto_fu = st.number_input("Petto (cm)##fu", min_value=50.0, max_value=150.0, value=float(assessment_initial.get('circonferenza_petto_cm', 100)), step=0.1)
                    circ_vita_fu = st.number_input("Vita (cm)##fu", min_value=40.0, max_value=150.0, value=float(assessment_initial.get('circonferenza_vita_cm', 80)), step=0.1)
                    circ_fianchi_fu = st.number_input("Fianchi (cm)##fu", min_value=50.0, max_value=150.0, value=float(assessment_initial.get('circonferenza_fianchi_cm', 95)), step=0.1)
                
                with col_f3:
                    circ_bic_sx_fu = st.number_input("Bicipite SX (cm)##fu", min_value=15.0, max_value=60.0, value=float(assessment_initial.get('circonferenza_bicipite_sx_cm', 30)), step=0.1)
                    circ_bic_dx_fu = st.number_input("Bicipite DX (cm)##fu", min_value=15.0, max_value=60.0, value=float(assessment_initial.get('circonferenza_bicipite_dx_cm', 30)), step=0.1)
                    circ_quad_sx_fu = st.number_input("Quadricipite SX (cm)##fu", min_value=30.0, max_value=80.0, value=float(assessment_initial.get('circonferenza_quadricipite_sx_cm', 55)), step=0.1)
                    circ_quad_dx_fu = st.number_input("Quadricipite DX (cm)##fu", min_value=30.0, max_value=80.0, value=float(assessment_initial.get('circonferenza_quadricipite_dx_cm', 55)), step=0.1)
                    circ_coscia_sx_fu = st.number_input("Coscia SX (cm)##fu", min_value=30.0, max_value=80.0, value=float(assessment_initial.get('circonferenza_coscia_sx_cm', 55)), step=0.1)
                    circ_coscia_dx_fu = st.number_input("Coscia DX (cm)##fu", min_value=30.0, max_value=80.0, value=float(assessment_initial.get('circonferenza_coscia_dx_cm', 55)), step=0.1)
            
            with st.expander("💪 Performance Test (Subset)", expanded=True):
                col_perf1, col_perf2 = st.columns(2)
                
                with col_perf1:
                    pushup_reps_fu = st.number_input("Push-up (Reps)##fu", min_value=0, value=int(assessment_initial.get('pushups_reps', 10)), step=1)
                    panca_peso_fu = st.number_input("Panca - Peso (kg)##fu", min_value=0.0, value=float(assessment_initial.get('panca_peso_kg', 40)), step=0.5)
                    panca_reps_fu = st.number_input("Panca - Reps##fu", min_value=0, value=int(assessment_initial.get('panca_reps', 10)), step=1)
                
                with col_perf2:
                    rem_peso_fu = st.number_input("Rematore - Peso (kg)##fu", min_value=0.0, value=float(assessment_initial.get('rematore_peso_kg', 40)), step=0.5)
                    rem_reps_fu = st.number_input("Rematore - Reps##fu", min_value=0, value=int(assessment_initial.get('rematore_reps', 10)), step=1)
                    sq_peso_fu = st.number_input("Squat - Peso (kg)##fu", min_value=0.0, value=float(assessment_initial.get('squat_macchina_peso_kg', 60)), step=0.5)
                    sq_reps_fu = st.number_input("Squat - Reps##fu", min_value=0, value=int(assessment_initial.get('squat_macchina_reps', 10)), step=1)
            
            with st.expander("🎯 Progresso Goals & Note"):
                goals_progress_fu = st.text_area("Progresso verso Goals", placeholder="Es: On track, exceeded, behind, ecc. Descrivi lo stato di progresso", height=100)
                
                foto_fronte_fu = st.file_uploader("Foto Fronte (opzionale)##fu", type=["jpg", "jpeg", "png"], key="foto_fronte_fu")
                foto_lato_fu = st.file_uploader("Foto Lato (opzionale)##fu", type=["jpg", "jpeg", "png"], key="foto_lato_fu")
                foto_dietro_fu = st.file_uploader("Foto Dietro (opzionale)##fu", type=["jpg", "jpeg", "png"], key="foto_dietro_fu")
                
                note_followup_fu = st.text_area("Note Followup", placeholder="Osservazioni generali, adattamenti programma, ecc", height=80)
            
            col_submit_fu1, col_submit_fu2 = st.columns([2, 1])
            with col_submit_fu1:
                submitted_fu = st.form_submit_button("💾 Salva Followup", type="primary", use_container_width=True)
            
            if submitted_fu:
                # Salva foto se uploadate
                foto_paths_fu = {}
                
                if foto_fronte_fu:
                    foto_dir = f"data/foto/{id_cliente}"
                    os.makedirs(foto_dir, exist_ok=True)
                    fronte_path = f"{foto_dir}/fronte_followup_{date.today()}.jpg"
                    with open(fronte_path, "wb") as f:
                        f.write(foto_fronte_fu.getbuffer())
                    foto_paths_fu['foto_fronte_path'] = fronte_path
                
                if foto_lato_fu:
                    foto_dir = f"data/foto/{id_cliente}"
                    os.makedirs(foto_dir, exist_ok=True)
                    lato_path = f"{foto_dir}/lato_followup_{date.today()}.jpg"
                    with open(lato_path, "wb") as f:
                        f.write(foto_lato_fu.getbuffer())
                    foto_paths_fu['foto_lato_path'] = lato_path
                
                if foto_dietro_fu:
                    foto_dir = f"data/foto/{id_cliente}"
                    os.makedirs(foto_dir, exist_ok=True)
                    dietro_path = f"{foto_dir}/dietro_followup_{date.today()}.jpg"
                    with open(dietro_path, "wb") as f:
                        f.write(foto_dietro_fu.getbuffer())
                    foto_paths_fu['foto_dietro_path'] = dietro_path
                
                dati_followup = {
                    'peso_kg': peso_fu,
                    'massa_grassa_pct': massa_grassa_fu,
                    'circonferenza_petto_cm': circ_petto_fu,
                    'circonferenza_vita_cm': circ_vita_fu,
                    'circonferenza_bicipite_sx_cm': circ_bic_sx_fu,
                    'circonferenza_bicipite_dx_cm': circ_bic_dx_fu,
                    'circonferenza_fianchi_cm': circ_fianchi_fu,
                    'circonferenza_quadricipite_sx_cm': circ_quad_sx_fu,
                    'circonferenza_quadricipite_dx_cm': circ_quad_dx_fu,
                    'circonferenza_coscia_sx_cm': circ_coscia_sx_fu,
                    'circonferenza_coscia_dx_cm': circ_coscia_dx_fu,
                    'pushups_reps': pushup_reps_fu,
                    'panca_peso_kg': panca_peso_fu,
                    'panca_reps': panca_reps_fu,
                    'rematore_peso_kg': rem_peso_fu,
                    'rematore_reps': rem_reps_fu,
                    'squat_peso_kg': sq_peso_fu,
                    'squat_reps': sq_reps_fu,
                    'goals_progress': goals_progress_fu,
                    'note_followup': note_followup_fu,
                    **foto_paths_fu
                }
                
                db.save_assessment_followup(id_cliente, dati_followup)
                
                st.success("✅ Followup Salvato!")
                st.balloons()
                st.rerun()
    
    # ════════════════════════════════════════════════════════════
    # TAB 3: GRAFICI PROGRESSIONE
    # ════════════════════════════════════════════════════════════
    
    with tab3:
        st.subheader("📈 Grafici Progressione")
        
        timeline = db.get_assessment_timeline(id_cliente)
        
        if len(timeline) > 1:
            # Preparare data per grafici
            dates = []
            pesi = []
            vite = []
            petti = []
            pushups_vals = []
            panca_pesi = []
            
            for item in timeline:
                data = item['data']
                dates.append(data.get('data_assessment') or data.get('data_followup'))
                pesi.append(data.get('peso_kg'))
                vite.append(data.get('circonferenza_vita_cm'))
                petti.append(data.get('circonferenza_petto_cm'))
                pushups_vals.append(data.get('pushups_reps'))
                panca_pesi.append(data.get('panca_peso_kg'))
            
            # GRAFICI
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                df_peso = pd.DataFrame({'Data': dates, 'Peso': pesi}).dropna()
                if len(df_peso) > 0:
                    fig_peso = px.line(
                        df_peso,
                        x='Data',
                        y='Peso',
                        title="📊 Progressione Peso",
                        markers=True,
                        labels={'Peso': 'Kg', 'Data': 'Data'}
                    )
                    fig_peso.update_traces(line_color='#667eea')
                    st.plotly_chart(fig_peso, use_container_width=True)
            
            with col_g2:
                df_vita = pd.DataFrame({'Data': dates, 'Vita': vite}).dropna()
                if len(df_vita) > 0:
                    fig_vita = px.line(
                        df_vita,
                        x='Data',
                        y='Vita',
                        title="⭕ Progressione Circonferenza Vita",
                        markers=True,
                        labels={'Vita': 'cm', 'Data': 'Data'}
                    )
                    fig_vita.update_traces(line_color='#ef4444')
                    st.plotly_chart(fig_vita, use_container_width=True)
            
            col_g3, col_g4 = st.columns(2)
            
            with col_g3:
                df_petto = pd.DataFrame({'Data': dates, 'Petto': petti}).dropna()
                if len(df_petto) > 0:
                    fig_petto = px.line(
                        df_petto,
                        x='Data',
                        y='Petto',
                        title="💪 Progressione Circonferenza Petto",
                        markers=True,
                        labels={'Petto': 'cm', 'Data': 'Data'}
                    )
                    fig_petto.update_traces(line_color='#10b981')
                    st.plotly_chart(fig_petto, use_container_width=True)
            
            with col_g4:
                df_pushups = pd.DataFrame({'Data': dates, 'Push-ups': pushups_vals}).dropna()
                if len(df_pushups) > 0:
                    fig_pushups = px.line(
                        df_pushups,
                        x='Data',
                        y='Push-ups',
                        title="🏋️ Progressione Push-ups",
                        markers=True,
                        labels={'Push-ups': 'Reps', 'Data': 'Data'}
                    )
                    fig_pushups.update_traces(line_color='#f59e0b')
                    st.plotly_chart(fig_pushups, use_container_width=True)
            
            col_g5, col_g6 = st.columns(2)
            
            with col_g5:
                df_panca = pd.DataFrame({'Data': dates, 'Panca': panca_pesi}).dropna()
                if len(df_panca) > 0:
                    fig_panca = px.line(
                        df_panca,
                        x='Data',
                        y='Panca',
                        title="🏋️ Progressione Panca (kg)",
                        markers=True,
                        labels={'Panca': 'Kg', 'Data': 'Data'}
                    )
                    fig_panca.update_traces(line_color='#8b5cf6')
                    st.plotly_chart(fig_panca, use_container_width=True)
        
        else:
            st.info("📌 Hai bisogno di almeno 2 assessments (iniziale + 1 followup) per visualizzare i grafici di progressione.")

# ════════════════════════════════════════════════════════════
# TAB INFO (mostra solo se no assessment)
# ════════════════════════════════════════════════════════════

if not assessment_initial:
    with tab2:
        st.info("""
        ℹ️ **Creare Assessment Iniziale**
        
        Completa l'assessment iniziale nella **Tab 1** per iniziare a tracciare i progressi del cliente.
        """)
