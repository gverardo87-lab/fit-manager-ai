# file: server/pages/11_Anagrafica.py (Versione FitManager - Edit Mode)
from __future__ import annotations
import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Cartella Atleti", page_icon="📋", layout="wide")

st.title("📋 Cartella Clinica Atleti")

# --- HELPER FUNCTIONS ---
def calcola_bmi(peso, altezza_cm):
    if not altezza_cm or not peso: return 0
    h_m = altezza_cm / 100
    return round(peso / (h_m ** 2), 1)

def calcola_bmr_harris_benedict(sesso, peso, altezza_cm, anni):
    if not peso or not altezza_cm or not anni: return 0
    base = (10 * peso) + (6.25 * altezza_cm) - (5 * anni)
    if sesso == "Uomo": return int(base + 5)
    else: return int(base - 161)

# --- CARICAMENTO LISTA ATLETI ---
df_atleti = db.get_dipendenti_df()
atleti_map = {row.name: f"{row['cognome']} {row['nome']}" for _, row in df_atleti.iterrows()} if not df_atleti.empty else {}

# --- SELETTORE MODALITÀ ---
col_sel1, col_sel2 = st.columns([1, 3])
with col_sel1:
    mode = st.radio("Azione", ["➕ Nuovo Iscritto", "✏️ Modifica Esistente"], horizontal=True, label_visibility="collapsed")

atleta_id_sel = None
dati_pre = {} # Dati precompilati

# Se MODIFICA, mostra selectbox e carica dati
if mode == "✏️ Modifica Esistente":
    if not atleti_map:
        st.warning("Nessun atleta da modificare.")
        st.stop()
    
    with col_sel2:
        atleta_id_sel = st.selectbox("Seleziona Atleta", options=atleti_map.keys(), format_func=lambda x: atleti_map[x])
    
    # Caricamento dati DB
    record = db.get_atleta_by_id(atleta_id_sel)
    if record:
        # Parsing JSON Anamnesi
        anamnesi = {}
        try:
            if record['anamnesi_json']: anamnesi = json.loads(record['anamnesi_json'])
        except: pass
        
        # Parsing Data
        d_nascita = date(1990, 1, 1)
        if record['data_nascita']:
            try: d_nascita = datetime.strptime(record['data_nascita'], "%Y-%m-%d").date()
            except: pass

        dati_pre = {
            "nome": record['nome'], "cognome": record['cognome'], "sesso": record['sesso'] or "Uomo",
            "nascita": d_nascita, "email": record['email'] or "", "tel": record['telefono'] or "",
            "peso": float(record['peso_iniziale']) if record['peso_iniziale'] else 70.0,
            "altezza": int(record['altezza']) if record['altezza'] else 170,
            "ruolo": record['ruolo'] or "10 Ingressi", "obiettivo": record['obiettivo'] or "Dimagrimento",
            "livello": record['livello_attivita'] or "Sedentario", "attivo": bool(record['attivo']),
            # JSON Fields
            "sonno": anamnesi.get('sonno_medio', 7), "stress": anamnesi.get('stress', 5),
            "infortuni": anamnesi.get('infortuni', ""), "farmaci": anamnesi.get('farmaci', ""),
            "alim": anamnesi.get('alimentazione', "Onnivoro"), "freq": anamnesi.get('frequenza_target', 3),
            "note": anamnesi.get('note_private', "")
        }
else:
    # Modalità NUOVO (Valori default)
    dati_pre = {
        "nome": "", "cognome": "", "sesso": "Uomo", "nascita": date(1990, 1, 1),
        "email": "", "tel": "", "peso": 70.0, "altezza": 170,
        "ruolo": "10 Ingressi", "obiettivo": "Dimagrimento", "livello": "Sedentario", "attivo": True,
        "sonno": 7, "stress": 5, "infortuni": "", "farmaci": "", "alim": "Onnivoro", "freq": 3, "note": ""
    }

# --- FORM WIZARD (Unico per Insert e Update) ---
container_title = f"Dati Atleta: {dati_pre['cognome']} {dati_pre['nome']}" if mode == "✏️ Modifica Esistente" else "Nuova Anamnesi"
with st.container(border=True):
    st.subheader(container_title)
    
    with st.form("anamnesi_form"):
        tab1, tab2, tab3, tab4 = st.tabs(["👤 Generalità", "📏 Biometria", "🏥 Salute", "🎯 Obiettivi"])
        
        with tab1:
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome*", value=dati_pre['nome'])
            cognome = c2.text_input("Cognome*", value=dati_pre['cognome'])
            
            c3, c4 = st.columns(2)
            sesso = c3.radio("Sesso", ["Uomo", "Donna"], index=0 if dati_pre['sesso']=="Uomo" else 1, horizontal=True)
            data_nascita = c4.date_input("Data Nascita", value=dati_pre['nascita'])
            
            c5, c6 = st.columns(2)
            email = c5.text_input("Email", value=dati_pre['email'])
            telefono = c6.text_input("Telefono", value=dati_pre['tel'])

        with tab2:
            bc1, bc2, bc3 = st.columns(3)
            peso = bc1.number_input("Peso (kg)*", 30.0, 200.0, value=dati_pre['peso'], step=0.1)
            altezza = bc2.number_input("Altezza (cm)*", 100, 250, value=dati_pre['altezza'])
            
            eta = (date.today() - data_nascita).days // 365
            bmi = calcola_bmi(peso, altezza)
            bmr = calcola_bmr_harris_benedict(sesso, peso, altezza, eta)
            
            bc3.metric("BMR Stimato", f"{bmr} Kcal", delta=f"BMI: {bmi}")

        with tab3:
            sc1, sc2 = st.columns(2)
            livello_attivita = sc1.select_slider("Livello Attività", options=["Sedentario", "Leggermente Attivo", "Moderatamente Attivo", "Molto Attivo", "Estremo"], value=dati_pre['livello'])
            sonno = sc1.slider("Ore Sonno", 4, 12, dati_pre['sonno'])
            stress = sc1.slider("Livello Stress", 1, 10, dati_pre['stress'])
            
            infortuni = sc2.text_area("Infortuni", value=dati_pre['infortuni'])
            farmaci = sc2.text_area("Farmaci", value=dati_pre['farmaci'])
            alim = sc2.selectbox("Alimentazione", ["Onnivoro", "Vegetariano", "Vegano", "Disordinato"], index=["Onnivoro", "Vegetariano", "Vegano", "Disordinato"].index(dati_pre['alim']) if dati_pre['alim'] in ["Onnivoro", "Vegetariano", "Vegano", "Disordinato"] else 0)

        with tab4:
            oc1, oc2 = st.columns(2)
            # Gestione indici sicura per selectbox
            obj_list = ["Dimagrimento", "Ipertrofia (Massa)", "Ricomposizione", "Performance", "Posturale"]
            sub_list = ["10 Ingressi", "Semestrale Open", "Coaching Online", "Consulenza Singola"]
            
            try: obj_idx = obj_list.index(dati_pre['obiettivo'])
            except: obj_idx = 0
            
            try: sub_idx = sub_list.index(dati_pre['ruolo'])
            except: sub_idx = 0
            
            obiettivo = oc1.selectbox("Obiettivo", obj_list, index=obj_idx)
            abbonamento = oc1.selectbox("Abbonamento", sub_list, index=sub_idx)
            freq = oc2.slider("Freq. Target", 1, 7, dati_pre['freq'])
            note = oc2.text_area("Note Admin", value=dati_pre['note'])
            
            if mode == "✏️ Modifica Esistente":
                attivo = st.checkbox("Atleta Attivo", value=dati_pre['attivo'])
            else:
                attivo = True

        st.markdown("---")
        btn_label = "💾 AGGIORNA ATLETA" if mode == "✏️ Modifica Esistente" else "💾 CREA NUOVO ATLETA"
        submitted = st.form_submit_button(btn_label, type="primary", use_container_width=True)

        if submitted:
            if not nome or not cognome:
                st.error("Nome e Cognome obbligatori.")
            else:
                # Dati pronti per DB
                payload = {
                    "nome": nome, "cognome": cognome, "sesso": sesso,
                    "data_nascita": data_nascita.strftime("%Y-%m-%d"),
                    "email": email, "telefono": telefono,
                    "peso": peso, "altezza": altezza,
                    "abbonamento": abbonamento, "obiettivo": obiettivo,
                    "livello_attivita": livello_attivita,
                    "attivo": attivo,
                    "anamnesi_dettagli": {
                        "bmi_start": bmi, "bmr_start": bmr,
                        "sonno_medio": sonno, "stress": stress,
                        "infortuni": infortuni, "farmaci": farmaci,
                        "alimentazione": alim, "frequenza_target": freq,
                        "note_private": note
                    }
                }
                
                try:
                    if mode == "✏️ Modifica Esistente":
                        db.update_atleta_completo(atleta_id_sel, payload)
                        st.success("✅ Modifiche salvate!")
                    else:
                        db.add_atleta_completo(payload)
                        st.success("✅ Atleta creato!")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore DB: {e}")

# --- LISTA VELOCE SOTTO ---
if not df_atleti.empty:
    st.divider()
    with st.expander("🔍 Consulta Elenco Rapido"):
        st.dataframe(df_atleti[['cognome', 'nome', 'obiettivo', 'telefono', 'ruolo']], use_container_width=True)