#!/usr/bin/env python3
# server/pages/02_Assistente_Esperto.py
"""
Assistente Esperto Unificato
Pagina singola ottimizzata per RAG e chat basata su vector store.
Sostituisce: 02_Expert_Chat_Enhanced.py e 03_Esperto_Tecnico.py
"""

import streamlit as st
from pathlib import Path
import fitz  # PyMuPDF
import os
import sys
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.knowledge_chain import get_hybrid_chain
from core.error_handler import logger

# ════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Assistente Esperto",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════
# INITIALIZATION
# ════════════════════════════════════════════════════════════

@st.cache_resource
def get_knowledge_system():
    """Carica il sistema di knowledge ibrido una sola volta"""
    try:
        hybrid = get_hybrid_chain()
        return hybrid
    except Exception as e:
        logger.error(f"Errore inizializzazione knowledge: {e}")
        return None

# Inizializza il sistema
knowledge = get_knowledge_system()

# Inizializza session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'viewing_doc' not in st.session_state:
    st.session_state.viewing_doc = None

if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# ════════════════════════════════════════════════════════════
# SIDEBAR: CONFIGURAZIONE E STATO KB
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🧠 Assistente Esperto")
    st.divider()
    
    # Stato della knowledge base
    st.subheader("📚 Knowledge Base")
    
    if knowledge:
        kb_status = knowledge.get_knowledge_status()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Esercizi Built-in", kb_status.get('built_in_exercises', 0))
        with col2:
            st.metric("KB Caricata", "Sì" if kb_status.get('kb_loaded') else "No")
        
        st.divider()
        
        # Opzioni di ricerca
        st.subheader("🔍 Opzioni di Ricerca")
        
        search_mode = st.radio(
            "Modalità di ricerca",
            ["Intelligente (RAG)", "Per esercizio", "Per categoria"],
            help="Intelligente: sfrutta il vector store. Per esercizio: cerca esercizi specifici. Per categoria: filtra per tipo."
        )
        
        if search_mode == "Per categoria":
            category = st.selectbox(
                "Categoria",
                ["Periodizzazione", "Progressione", "Recovery", "Nutrizione", "Biomeccanica"],
                help="Seleziona una categoria di interesse"
            )
        
        st.divider()
        st.caption(f"Modalità: {kb_status.get('mode', 'HYBRID')}")
        st.caption(f"Status: {kb_status.get('status', 'Non disponibile')}")
    else:
        st.error("❌ Knowledge system non disponibile")

# ════════════════════════════════════════════════════════════
# MAIN INTERFACE - LAYOUT
# ════════════════════════════════════════════════════════════

st.title("🧠 Assistente Esperto Fitness")

st.markdown("""
Assistente intelligente basato su knowledge base e training metodologie.  
Fai domande su esercizi, programmi, nutrizione, periodizzazione e molto altro.
""")

st.divider()

# Due colonne: chat + documento
col_chat, col_doc = st.columns([2, 1], gap="medium")

# ════════════════════════════════════════════════════════════
# COLONNA SINISTRA: CHAT
# ════════════════════════════════════════════════════════════

with col_chat:
    st.subheader("💬 Chat")
    
    # Container messaggi scrollabile
    message_container = st.container(height=600, border=True)
    
    with message_container:
        if not st.session_state.messages:
            st.info("""
            👋 Benvenuto! Sono l'Assistente Esperto.
            
            Posso aiutarti con:
            - 💪 Dettagli esercizi e tecniche di esecuzione
            - 📊 Programmi di allenamento e periodizzazione
            - 📈 Strategie di progressione e overload
            - 😴 Recovery e nutrizione
            - 🏆 Consigli basati su metodologie scientifiche
            
            **Fai una domanda per iniziare!**
            """)
        else:
            for idx, message in enumerate(st.session_state.messages):
                with st.chat_message(message['role'], avatar="🧠" if message['role'] == "assistant" else "👤"):
                    # Contenuto principale
                    st.markdown(message['content'])
                    
                    # Fonti (se presenti)
                    if 'sources' in message and message['sources']:
                        with st.expander(f"📚 {len(message['sources'])} fonti consultate"):
                            for src_idx, source in enumerate(message['sources']):
                                col_src1, col_src2 = st.columns([3, 1])
                                with col_src1:
                                    st.caption(f"**{source.get('source', 'Sconosciuta')}** (pag. {source.get('page', '?')})")
                                with col_src2:
                                    if st.button(
                                        "📄 Apri",
                                        key=f"doc_{idx}_{src_idx}",
                                        help="Visualizza il documento originale"
                                    ):
                                        st.session_state.viewing_doc = source
                                        st.rerun()
    
    st.divider()
    
    # Input chat
    user_query = st.chat_input(
        placeholder="Es: Come eseguire correttamente lo squat? Qual è il miglior programma per l'ipertrofia?",
        key="expert_input"
    )
    
    if user_query:
        # Aggiungi query all'history
        st.session_state.messages.append({
            "role": "user",
            "content": user_query
        })
        
        # Genera risposta
        with st.spinner("🔄 Consultando la knowledge base..."):
            try:
                # Retrieval RAG
                if knowledge and knowledge.llm:
                    # Retrieva documenti dal KB
                    retrieved_docs = []
                    sources = []
                    
                    if knowledge.kb_available and knowledge.retriever:
                        try:
                            docs = knowledge.retriever.invoke(user_query)
                            retrieved_docs = docs[:5]  # Top 5 documents
                            
                            # Estrai fonti
                            for doc in retrieved_docs:
                                sources.append({
                                    'source': doc.metadata.get('source', 'Sconosciuta'),
                                    'page': doc.metadata.get('page', '?'),
                                    'content': doc.page_content[:200]
                                })
                        except Exception as e:
                            logger.warning(f"Errore retrieval: {e}")
                    
                    # Build context per LLM
                    context = ""
                    if retrieved_docs:
                        context = "\n\n---\n\n".join([
                            f"[{doc.metadata.get('source', 'Fonte sconosciuta')}, pag. {doc.metadata.get('page', '?')}]\n{doc.page_content}"
                            for doc in retrieved_docs[:3]
                        ])
                    
                    # Prompt per LLM
                    prompt = f"""Sei un esperto di fitness e allenamento. Rispondi dettagliatamente alla domanda.

DOMANDA: {user_query}

CONTESTO DAI DOCUMENTI:
{context if context else "Nessun documento pertinente trovato. Utilizza le tue conoscenze built-in."}

Rispondi in italiano, in modo chiaro e professionale. Includi dettagli pratici e consigli specifici."""
                    
                    # Genera risposta
                    response = knowledge.llm.invoke(prompt)
                    
                    # Aggiungi risposta all'history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })
                else:
                    st.error("❌ Sistema non disponibile. Knowledge chain non inizializzata.")
            
            except Exception as e:
                logger.error(f"Errore generazione risposta: {e}")
                st.error(f"❌ Errore: {str(e)}")
        
        st.rerun()

# ════════════════════════════════════════════════════════════
# COLONNA DESTRA: VISUALIZZATORE DOCUMENTI
# ════════════════════════════════════════════════════════════

with col_doc:
    st.subheader("📄 Documento in Analisi")
    
    if st.session_state.viewing_doc:
        doc_ref = st.session_state.viewing_doc
        
        st.info(f"""
        📄 **{doc_ref.get('source', 'Documento')}**
        
        Pagina: {doc_ref.get('page', '?')}
        """)
        
        # Prova a visualizzare il PDF
        try:
            kb_path = Path("knowledge_base/documents")
            
            # Cerca il file PDF
            source_name = doc_ref.get('source', '')
            pdf_files = list(kb_path.glob(f"*{source_name.split('.')[0]}*")) if kb_path.exists() else []
            
            if pdf_files:
                pdf_path = pdf_files[0]
                
                try:
                    pdf_doc = fitz.open(pdf_path)
                    
                    page_num = int(doc_ref.get('page', 1))
                    page_index = page_num - 1
                    
                    if 0 <= page_index < len(pdf_doc):
                        page = pdf_doc.load_page(page_index)
                        
                        # Renderizza la pagina
                        pix = page.get_pixmap(dpi=120)
                        img_data = pix.tobytes("png")
                        
                        st.image(img_data, use_column_width=True, caption=f"Pagina {page_num}")
                        
                        # Download button
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="📥 Scarica PDF",
                                data=f,
                                file_name=pdf_path.name,
                                mime="application/pdf",
                                use_container_width=True
                            )
                    else:
                        st.warning(f"Pagina {page_num} non trovata nel documento.")
                    
                    pdf_doc.close()
                
                except Exception as e:
                    st.error(f"Errore visualizzazione PDF: {e}")
            else:
                st.warning("📭 Documento non trovato nel sistema locale.")
                
                # Mostra lo snippet del documento
                if 'content' in doc_ref:
                    st.markdown("#### Anteprima Contenuto:")
                    st.text_area(
                        "Snippet",
                        value=doc_ref['content'],
                        height=200,
                        disabled=True,
                        label_visibility="collapsed"
                    )
        
        except Exception as e:
            logger.error(f"Errore visualizzazione documento: {e}")
            st.info("ℹ️ Impossibile visualizzare il documento. Dettagli nei log.")
    
    else:
        st.info("""
        📭 Nessun documento selezionato.
        
        Clicca su **Apri** accanto a una fonte nella chat per visualizzarla qui.
        """)

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()

col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    if st.button("🗑️ Cancella Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.viewing_doc = None
        st.rerun()

with col_footer2:
    if st.button("↺ Refresh Knowledge", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.caption("""
**Assistente Esperto Fitness** | Basato su Hybrid Knowledge (Built-in + Vector Store)  
Consulta sempre un professionista prima di iniziare qualsiasi nuovo programma di allenamento.
""")
