# file: server/pages/11_Anagrafica.py (Versione FitManager 2.4 - Pro Anamnesis)
from __future__ import annotations
import streamlit as st
import pandas as pd
import json
from datetime import date, timedelta, datetime
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Atleti & Contratti", page_icon="📝", layout="wide")

st.title("📝 Gestione Atleti & Contratti")

# --- CARICAMENTO DATI PER SELEZIONE ---
try:
    df_atleti = db.get_dipendenti_df(solo_attivi=True)
    atleti_map = {row.name: f"{row['cognome']} {row['nome']}" for _, row in df_atleti.iterrows()} if not df_atleti.empty else {}
except Exception:
    df_atleti = pd.DataFrame()
    atleti_map = {}

# --- MODALITÀ: NUOVO O MODIFICA ---
col_mode, col_sel = st.columns([1, 3])
with col_mode:
    mode = st.radio("Modalità Operativa", ["➕ Nuovo Contratto", "✏️ Modifica Dati"], horizontal=True, label_visibility="collapsed")

atleta_id_sel = None
dati_pre = {}

if mode == "✏️ Modifica Dati":
    if not atleti_map:
        st.warning("Nessun atleta presente nel database.")
        st.stop()
    with col_sel:
        atleta_id_sel = st.selectbox("Seleziona Atleta da Modificare", options=atleti_map.keys(), format_func=lambda x: atleti_map[x])
    
    # FETCH DATI DAL DB
    full_data = db.get_atleta_detail(atleta_id_sel)
    if full_data:
        # Parsing date e json
        try: d_nascita = datetime.strptime(full_data['data_nascita'], "%Y-%m-%d").date()
        except: d_nascita = date(1990, 1, 1)
        
        anamnesi = {}
        if full_data.get('anamnesi_json'):
            try: anamnesi = json.loads(full_data['anamnesi_json'])
            except: pass
            
        abb_attivo = full_data.get('abbonamento_attivo', {}) or {}
        
        # Parsing date abbonamento
        try: d_start_abb = datetime.strptime(abb_attivo.get('data_inizio'), "%Y-%m-%d").date()
        except: d_start_abb = date.today()
        try: d_end_abb = datetime.strptime(abb_attivo.get('data_scadenza'), "%Y-%m-%d").date() if abb_attivo.get('data_scadenza') else None
        except: d_end_abb = None

        dati_pre = {
            "nome": full_data['nome'], "cognome": full_data['cognome'], "sesso": full_data.get('sesso', "Uomo"), 
            "nascita": d_nascita, "email": full_data.get('email', ""), "tel": full_data.get('telefono', ""),
            "peso": full_data.get('peso_iniziale'), "altezza": full_data.get('altezza'),
            "obiettivo": full_data.get('obiettivo'), "livello": full_data.get('livello_attivita'),
            
            # Anamnesi Avanzata
            "professione": anamnesi.get('professione', ""),
            "fumo": anamnesi.get('fumo', "No"),
            "sport_history": anamnesi.get('sport_history', ""),
            "infortuni": anamnesi.get('infortuni', ""),
            "intolleranze": anamnesi.get('intolleranze', ""),
            
            # Contratto (Full Edit)
            "pacchetto": abb_attivo.get('tipo_pacchetto', "10 Ingressi"),
            "prezzo": abb_attivo.get('prezzo_pattuito', 0.0),
            "start_date": d_start_abb,
            "end_date": d_end_abb,
            "ingressi": abb_attivo.get('ingressi_totali', 0),
            "note_contratto": abb_attivo.get('note_contratto', "")
        }
else:
    # DEFAULT VUOTI
    dati_pre = {
        "nome": "", "cognome": "", "sesso": "Uomo", "nascita": date(1990,1,1),
        "email": "", "tel": "", "peso": 70.0, "altezza": 170,
        "obiettivo": "Dimagrimento", "livello": "Sedentario",
        "professione": "", "fumo": "No", "sport_history": "", "infortuni": "", "intolleranze": "",
        "pacchetto": "10 Ingressi", "prezzo": 0.0, "start_date": date.today(), "end_date": None, "ingressi": 10, "note_contratto": ""
    }

# --- FORM UNIFICATO ---
form_title = f"Modifica Scheda: {dati_pre.get('cognome','')} {dati_pre.get('nome','')}" if mode == "✏️ Modifica Dati" else "Nuova Registrazione"

with st.expander(form_title, expanded=True):
    with st.form("main_form"):
        t1, t2, t3, t4 = st.tabs(["1. Generalità", "2. Biometria", "3. Anamnesi PT", "4. Amministrazione"])
        
        with t1:
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome*", value=dati_pre['nome'])
            cognome = c2.text_input("Cognome*", value=dati_pre['cognome'])
            sesso = st.radio("Sesso", ["Uomo", "Donna"], index=0 if dati_pre['sesso']=="Uomo" else 1, horizontal=True)
            nascita = st.date_input("Data di Nascita", value=dati_pre['nascita'], min_value=date(1940,1,1))
            c3, c4 = st.columns(2)
            email = c3.text_input("Email", value=dati_pre['email'])
            tel = c4.text_input("Telefono", value=dati_pre['tel'])

        with t2:
            bc1, bc2 = st.columns(2)
            peso = bc1.number_input("Peso (kg)", 40.0, 150.0, float(dati_pre['peso'] or 70.0), step=0.1)
            altezza = bc2.number_input("Altezza (cm)", 120, 230, int(dati_pre['altezza'] or 170))
            
            obiettivi_list = ["Dimagrimento", "Ipertrofia", "Performance", "Posturale", "Ricomposizione"]
            try: obj_idx = obiettivi_list.index(dati_pre['obiettivo'])
            except: obj_idx = 0
            obiettivo = st.selectbox("Obiettivo Primario", obiettivi_list, index=obj_idx)

        with t3:
            st.markdown("##### 🧬 Profilazione Clinica")
            ac1, ac2 = st.columns(2)
            
            # Recupero sicuro del livello attività
            lv_options = ["Sedentario", "Leggermente Attivo", "Moderatamente Attivo", "Molto Attivo", "Estremo", "Attivo", "Sportivo"]
            lv_val = dati_pre['livello'] if dati_pre['livello'] in lv_options else "Sedentario"
            
            livello = ac1.select_slider("Livello Attività", options=lv_options, value=lv_val)
            professione = ac2.text_input("Professione (es. Impiegato, Muratore)", value=dati_pre['professione'])
            
            ac3, ac4 = st.columns(2)
            fumo = ac3.radio("Fumatore?", ["No", "Sì, occasionale", "Sì, abituale"], index=["No", "Sì, occasionale", "Sì, abituale"].index(dati_pre['fumo']) if dati_pre['fumo'] in ["No", "Sì, occasionale", "Sì, abituale"] else 0)
            sport_hist = ac4.text_input("Anzianità Allenamento (anni/mesi)", value=dati_pre['sport_history'])
            
            st.markdown("---")
            mc1, mc2 = st.columns(2)
            infortuni = mc1.text_area("🚑 Infortuni / Patologie", value=dati_pre['infortuni'], height=100)
            intolleranze = mc2.text_area("🍎 Intolleranze / Note Nutrizione", value=dati_pre['intolleranze'], height=100)

        with t4:
            st.markdown("##### 💳 Configurazione Contratto")
            if mode == "✏️ Modifica Dati":
                st.warning("⚠️ Stai modificando un contratto attivo. Cambia questi dati solo in caso di errore.")
            
            cc1, cc2 = st.columns(2)
            
            # Gestione sicura index pacchetto
            pk_opts = ["10 Ingressi", "20 Ingressi", "Mensile Open", "Trimestrale Open", "Annuale", "Coaching Online", "Consulenza"]
            try: pk_idx = pk_opts.index(dati_pre['pacchetto'])
            except: pk_idx = 0
            
            # Logica UI: Se cambio pacchetto (solo in Nuovo), aggiorna prezzi default
            # In Streamlit standard questo richiede rerun, qui facciamo manuale o lasciamo libertà
            tipo_abb = cc1.selectbox("Tipo Pacchetto", pk_opts, index=pk_idx)
            
            # Prezzo
            prezzo_finale = cc2.number_input("Prezzo Pattuito (€)", value=float(dati_pre['prezzo']), step=10.0)
            
            dc1, dc2 = st.columns(2)
            d_start = dc1.date_input("Data Inizio", value=dati_pre['start_date'])
            d_end = dc2.date_input("Data Scadenza", value=dati_pre['end_date'])
            
            ingressi = cc1.number_input("Ingressi Totali (se a consumo)", value=int(dati_pre['ingressi']))
            note_contr = cc2.text_area("Note Amministrative", value=dati_pre['note_contratto'], height=100)
            
            # Acconto solo in fase di creazione (non ha senso editarlo qui, i pagamenti vanno gestiti a parte in futuro)
            acconto = 0.0
            metodo = None
            if mode == "➕ Nuovo Contratto":
                st.divider()
                pc1, pc2 = st.columns(2)
                acconto = pc1.number_input("Acconto Versato Oggi (€)", 0.0, prezzo_finale, 0.0)
                metodo = pc2.selectbox("Metodo Pagamento", ["Contanti", "Bonifico", "POS"])

        st.markdown("---")
        btn_txt = "💾 AGGIORNA DATI" if mode == "✏️ Modifica Dati" else "📝 REGISTRA NUOVO ATLETA"
        
        if st.form_submit_button(btn_txt, type="primary", use_container_width=True):
            if not nome or not cognome:
                st.error("Nome e Cognome obbligatori!")
            else:
                payload = {
                    "nome": nome, "cognome": cognome, "sesso": sesso, "data_nascita": nascita.strftime("%Y-%m-%d"),
                    "email": email, "telefono": tel, "peso": peso, "altezza": altezza,
                    "obiettivo": obiettivo, "livello_attivita": livello,
                    "anamnesi_dettagli": {
                        "infortuni": infortuni, "intolleranze": intolleranze,
                        "professione": professione, "fumo": fumo, "sport_history": sport_hist
                    },
                    # Dati Contratto (Sempre inviati per update o create)
                    "abbonamento": {
                        "tipo": tipo_abb, "prezzo": prezzo_finale, "start_date": d_start,
                        "end_date": d_end, "ingressi": ingressi, "note": note_contr
                    }
                }
                
                # Acconto solo se nuovo
                if mode == "➕ Nuovo Contratto":
                    payload['acconto'] = acconto
                    payload['metodo_pag'] = metodo
                
                try:
                    if mode == "✏️ Modifica Dati":
                        db.update_atleta_completo(atleta_id_sel, payload)
                        st.success("✅ Scheda e Contratto aggiornati correttamente!")
                    else:
                        db.add_atleta_completo(payload)
                        st.success("🎉 Nuovo atleta registrato con successo!")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore DB: {e}")

# --- DASHBOARD RAPIDA ---
st.divider()
if not df_atleti.empty:
    st.subheader("📊 Elenco Atleti")
    st.dataframe(
        df_atleti[['cognome', 'nome', 'pacchetto', 'scadenza', 'saldo_aperto', 'telefono']],
        column_config={
            "saldo_aperto": st.column_config.NumberColumn("Da Saldare", format="%.2f €"),
            "scadenza": st.column_config.DateColumn("Scadenza")
        },
        use_container_width=True, hide_index=True
    )