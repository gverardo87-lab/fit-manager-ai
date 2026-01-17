# core/knowledge_chain.py (Versione IBRIDA - Built-in + KB Ottimale)
"""
Hybrid Knowledge Chain System

Supporta due modalità:
1. Built-in Knowledge (sempre disponibile): exercise_database.py
2. User Knowledge Base (opzionale): PDF caricati dall'utente

Fallback automatico: se KB non caricato, usa built-in knowledge.
Upgrade: quando utente carica PDF, ibridizza con built-in.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import (
    VECTORSTORE_DIR,
    EMBEDDING_MODEL,
    MAIN_LLM_MODEL,
    CROSS_ENCODER_MODEL
)
from core.exercise_database import exercise_db, PeriodizationTemplates, ProgressionStrategies
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
import streamlit as st
from sentence_transformers.cross_encoder import CrossEncoder


class HybridKnowledgeChain:
    """
    Sistema di conoscenza ibrido che combina:
    - Built-in Exercise Database (sempre disponibile)
    - User Knowledge Base (se caricato)
    
    Permette generazione workout ANCHE SENZA KB, con fallback intelligente.
    """
    
    def __init__(self):
        self.kb_available = False
        self.retriever = None
        self.llm = None
        self.cross_encoder = None
        self.exercise_db = exercise_db
        self._initialize()
    
    def _initialize(self):
        """Inizializza la hybrid chain"""
        self._load_kb_optional()
        self._load_llm()
    
    def _load_kb_optional(self):
        """Carica KB se disponibile, fallback a built-in"""
        print("--- Inizializzazione Hybrid Knowledge Chain... ---")
        
        # Prova a caricare KB user
        if Path(VECTORSTORE_DIR).is_dir():
            try:
                embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
                vectorstore = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
                self.retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
                self.kb_available = True
                print("[OK] Knowledge Base utente caricata")
            except Exception as e:
                print(f"[WARN] KB non disponibile: {e}")
                self.kb_available = False
        else:
            print("[WARN] Knowledge Base vuota - usando built-in knowledge")
            self.kb_available = False
        
        # Carica cross-encoder se KB disponibile
        if self.kb_available:
            try:
                self.cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
                print("[OK] Cross-Encoder caricato")
            except Exception as e:
                print(f"[WARN] Cross-Encoder fallito: {e}")
    
    def _load_llm(self):
        """Carica LLM"""
        try:
            self.llm = OllamaLLM(model=MAIN_LLM_MODEL, temperature=0.2)
            print("[OK] LLM caricato")
        except Exception as e:
            print(f"[WARN] LLM fallito: {e}")
            self.llm = None
    
    def get_exercise_methodology(self, goal: str, level: str) -> Dict[str, Any]:
        """
        Recupera metodologia di allenamento.
        
        Flusso:
        1. Prova KB user (se disponibile)
        2. Fallback a built-in templates
        3. Ibrida i risultati
        """
        
        if self.kb_available and self.retriever:
            # Prova KB user
            query = f"{goal} {level} training methodology"
            try:
                kb_results = self.retriever.invoke(query)
                if kb_results and self._score_relevance(kb_results) > 0.5:
                    return {
                        'source': 'user_kb',
                        'methodology': kb_results[0].page_content,
                        'reference': kb_results[0].metadata.get('source', 'Unknown')
                    }
            except:
                pass
        
        # Fallback a built-in
        template = exercise_db.get_workout_template(goal, level)
        return {
            'source': 'built_in',
            'template': template,
            'note': '[OK] Utilizziamo metodologia built-in (carica PDF per customizzazione)'
        }
    
    def retrieve_exercise_info(self, exercise_name: str) -> Dict[str, Any]:
        """Recupera informazioni su un esercizio"""
        
        # Prova built-in prima
        exercises = exercise_db.search_exercises(exercise_name)
        if exercises:
            return {
                'source': 'built_in',
                'exercise': exercises[0].to_dict(),
            }
        
        # Fallback a KB se disponibile
        if self.kb_available and self.retriever:
            try:
                kb_results = self.retriever.invoke(f"exercise {exercise_name}")
                if kb_results:
                    return {
                        'source': 'user_kb',
                        'content': kb_results[0].page_content,
                        'reference': kb_results[0].metadata.get('source', 'Unknown')
                    }
            except:
                pass
        
        return {
            'source': 'none',
            'error': f'Esercizio "{exercise_name}" non trovato'
        }
    
    def get_periodization(self, periodization_type: str, weeks: int) -> Dict[str, Any]:
        """Recupera template di periodizzazione"""
        
        templates = {
            'linear': PeriodizationTemplates.get_linear_periodization,
            'block': PeriodizationTemplates.get_block_periodization,
            'undulating': PeriodizationTemplates.get_undulating_periodization,
        }
        
        template_fn = templates.get(periodization_type)
        if template_fn:
            return template_fn(weeks)
        
        # Default
        return PeriodizationTemplates.get_linear_periodization(weeks)
    
    def get_progression_strategy(self, goal: str) -> Dict[str, Any]:
        """Raccomandarioni strategie di progressione per goal"""
        strategies = ProgressionStrategies.recommend_for_goal(goal)
        return {
            'recommended': strategies,
            'all_available': ProgressionStrategies.get_all_strategies()
        }
    
    def _score_relevance(self, documents: List[Document]) -> float:
        """Assegna score di rilevanza a documenti"""
        if not documents:
            return 0.0
        
        if self.cross_encoder:
            # Usa cross-encoder
            scores = self.cross_encoder.predict([[d.page_content[:100]] for d in documents])
            return float(scores[0]) if scores else 0.0
        
        # Fallback: assume rilevante
        return 0.7
    
    def is_kb_loaded(self) -> bool:
        """Verifica se KB è caricato"""
        return self.kb_available
    
    def get_knowledge_status(self) -> Dict[str, Any]:
        """Ritorna status della knowledge chain"""
        return {
            'built_in_exercises': exercise_db.count_exercises(),
            'kb_loaded': self.kb_available,
            'kb_available_for_enhancement': not self.kb_available,
            'llm_available': self.llm is not None,
            'mode': 'HYBRID',
            'status': '[OK] Pronto' if self.llm else '[ERROR] LLM non disponibile'
        }


# ═══════════════════════════════════════════════════════════════════════════
# LEGACY FUNCTIONS (per compatibilità con workout_generator.py)
# ═══════════════════════════════════════════════════════════════════════════

# Istanza globale
_hybrid_chain = HybridKnowledgeChain()


@st.cache_resource
def get_knowledge_chain():
    """Legacy function - ritorna retriever e llm"""
    return _hybrid_chain.retriever, _hybrid_chain.llm


@st.cache_resource
def get_cross_encoder():
    """Legacy function - ritorna cross encoder"""
    return _hybrid_chain.cross_encoder


def get_hybrid_chain() -> HybridKnowledgeChain:
    """Ritorna la hybrid chain per nuovo codice"""
    return _hybrid_chain


def rerank_documents(query: str, documents: List[Document], cross_encoder) -> List[Document]:
    """Legacy rerank function"""
    if not documents or cross_encoder is None:
        return documents
    
    print(f"--- Riordino di {len(documents)} documenti... ---")
    pairs = [[query, doc.page_content] for doc in documents]
    scores = cross_encoder.predict(pairs)
    
    for i in range(len(documents)):
        documents[i].metadata['relevance_score'] = scores[i]
    
    reranked_docs = sorted(documents, key=lambda x: x.metadata['relevance_score'], reverse=True)
    print(f"--- Documenti riordinati. Top score: {reranked_docs[0].metadata['relevance_score']:.2f} ---")
    return reranked_docs[:4]


def get_expert_response(user_query: str) -> Dict[str, Any]:
    """Legacy expert response function"""
    retriever, llm = get_knowledge_chain()
    cross_encoder = get_cross_encoder()
    
    error_response = {"answer": "Errore: modelli non disponibili", "sources": []}
    if llm is None:
        return error_response
    
    if retriever is None:
        return {"answer": "Usando built-in knowledge (carica KB per customizzazione)", "sources": []}
    
    retrieved_docs = retriever.invoke(user_query)
    if not retrieved_docs:
        return {"answer": "Non ho trovato informazioni pertinenti", "sources": []}
    
    reranked_docs = rerank_documents(user_query, retrieved_docs, cross_encoder)
    context = "\n\n---\n\n".join([f"Fonte: {doc.metadata['source']}, Pagina: {doc.metadata['page']}\nContenuto: {doc.page_content}" for doc in reranked_docs])
    
    prompt_template = """
    Sei un esperto di training. Rispondi basandoti ESCLUSIVAMENTE su questo contesto.
    Se il contesto non contiene l'informazione, dillo esplicitamente.
    
    CONTESTO: {context}
    DOMANDA: {question}
    
    RISPOSTA:
    """
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = prompt | llm
    
    try:
        final_answer = chain.invoke({"context": context, "question": user_query})
    except Exception as e:
        return {"answer": f"Errore: {e}", "sources": []}
    
    sources = []
    for doc in reranked_docs:
        sources.append({
            "source": doc.metadata.get('source', 'Sconosciuta'),
            "page": doc.metadata.get('page', '?'),
            "doc_id": doc.metadata.get('doc_id')
        })
    
    return {"answer": final_answer, "sources": sources}


def generate_response_with_sources(llm, results, query):
    """Legacy function per generare response con sources"""
    response_data = get_expert_response(query)
    return response_data["answer"], response_data["sources"]