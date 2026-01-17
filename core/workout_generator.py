# core/workout_generator.py (Generatore di Allenamenti basato su RAG)
"""
Generatore intelligente di schede di allenamento usando RAG (Retrieval-Augmented Generation).

Utilizza la knowledge base di documenti tecnici (metodologie di allenamento, anatomia, 
biomeccanica) per generare programmi personalizzati basati su profilo cliente.

Flusso:
1. Input cliente (goal, livello, disponibilità) 
2. Query RAG per recuperare metodologie rilevanti
3. Generazione con LLM di scheda personalizzata
4. Validazione e salvataggio in DB
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.knowledge_chain import get_knowledge_chain, get_cross_encoder, rerank_documents
from core.config import MAIN_LLM_MODEL
from langchain.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM


class WorkoutGenerator:
    """Generatore di programmi allenamento basato su RAG e personalizzazione cliente."""
    
    def __init__(self):
        """Inizializza il generatore con retriever e LLM."""
        self.retriever, self.llm = get_knowledge_chain()
        self.cross_encoder = get_cross_encoder()
        
        if not self.retriever or not self.llm:
            raise RuntimeError("Impossibile inizializzare WorkoutGenerator: Knowledge Chain non disponibile")
    
    # ─────────────────────────────────────────────────────────
    # METODI DI QUERY SULLA KNOWLEDGE BASE
    # ─────────────────────────────────────────────────────────
    
    def retrieve_training_methodology(self, goal: str, level: str) -> List[Dict[str, Any]]:
        """
        Recupera metodologie di allenamento rilevanti basate su goal e livello.
        
        Args:
            goal: 'strength', 'hypertrophy', 'endurance', 'fat_loss', 'functional'
            level: 'beginner', 'intermediate', 'advanced'
        
        Returns:
            Lista di documenti rilevanti con score
        """
        query = f"Metodologia allenamento {goal} per {level} - programmazione periodizzata esercizi"
        
        retrieved_docs = self.retriever.invoke(query)
        if not retrieved_docs:
            return []
        
        reranked = rerank_documents(query, retrieved_docs, self.cross_encoder)
        return reranked
    
    def retrieve_exercise_details(self, exercise_name: str) -> List[Dict[str, Any]]:
        """
        Recupera dettagli tecnici di uno specifico esercizio.
        
        Args:
            exercise_name: Nome dell'esercizio (es. 'squat', 'panca piana')
        
        Returns:
            Lista di documenti con dettagli anatomici e tecnica
        """
        query = f"Esercizio {exercise_name} anatomia biomeccanica tecnica corretta varianti"
        
        retrieved_docs = self.retriever.invoke(query)
        if not retrieved_docs:
            return []
        
        reranked = rerank_documents(query, retrieved_docs, self.cross_encoder)
        return reranked
    
    def retrieve_programming_principles(self) -> List[Dict[str, Any]]:
        """
        Recupera principi fondamentali di programmazione dell'allenamento.
        
        Returns:
            Lista di documenti su periodizzazione, progressione, recovery
        """
        query = "Principi programmazione allenamento periodizzazione progressione sovraccarico recupero"
        
        retrieved_docs = self.retriever.invoke(query)
        if not retrieved_docs:
            return []
        
        reranked = rerank_documents(query, retrieved_docs, self.cross_encoder)
        return reranked
    
    # ─────────────────────────────────────────────────────────
    # GENERAZIONE SCHEDA CON RAG
    # ─────────────────────────────────────────────────────────
    
    def generate_workout_plan(
        self,
        client_profile: Dict[str, Any],
        weeks: int = 4,
        sessions_per_week: int = 3
    ) -> Dict[str, Any]:
        """
        Genera un piano di allenamento personalizzato usando RAG.
        
        Args:
            client_profile: {
                'nome': str,
                'goal': 'strength'|'hypertrophy'|'endurance'|'fat_loss'|'functional',
                'level': 'beginner'|'intermediate'|'advanced',
                'age': int,
                'disponibilita_giorni': int,  # giorni a settimana
                'tempo_sessione_minuti': int,
                'limitazioni': str,  # infortuni, limitazioni particolari
                'preferenze': str  # attrezzi, esercizi preferiti
            }
            weeks: Durata del programma in settimane
            sessions_per_week: Numero di sessioni per settimana
        
        Returns:
            Piano di allenamento strutturato:
            {
                'client_name': str,
                'goal': str,
                'duration_weeks': int,
                'sessions_per_week': int,
                'methodology': str,
                'weekly_schedule': [...],
                'exercises_details': {...},
                'progressive_overload_strategy': str,
                'recovery_recommendations': str,
                'sources': [...]
            }
        """
        # Step 1: Recupera metodologie rilevanti dal KB
        methodology_docs = self.retrieve_training_methodology(
            client_profile['goal'],
            client_profile['level']
        )
        
        # Step 2: Recupera principi di programmazione
        programming_docs = self.retrieve_programming_principles()
        
        # Step 3: Costruisci il contesto dalla knowledge base
        methodology_context = self._format_context(methodology_docs)
        programming_context = self._format_context(programming_docs)
        
        # Step 4: Genera con LLM
        prompt = self._build_generation_prompt(
            client_profile,
            methodology_context,
            programming_context,
            weeks,
            sessions_per_week
        )
        
        try:
            raw_response = self.llm.invoke(prompt)
            
            # Step 5: Parse e struttura la risposta
            workout_plan = self._parse_workout_response(
                raw_response,
                client_profile,
                weeks,
                sessions_per_week
            )
            
            # Step 6: Aggiungi fonti
            sources = self._extract_sources(methodology_docs + programming_docs)
            workout_plan['sources'] = sources
            
            return workout_plan
            
        except Exception as e:
            return {
                'error': f"Errore nella generazione: {str(e)}",
                'client_name': client_profile.get('nome', 'Unknown')
            }
    
    def _format_context(self, documents: List) -> str:
        """Formatta i documenti in contesto per il prompt."""
        if not documents:
            return "Nessun documento trovato."
        
        context_parts = []
        for doc in documents:
            source = doc.metadata.get('source', 'Sconosciuta')
            page = doc.metadata.get('page', '?')
            content = doc.page_content[:500]  # Limita per evitare contesto troppo grande
            
            context_parts.append(f"[{source}, pag. {page}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _build_generation_prompt(
        self,
        profile: Dict[str, Any],
        methodology: str,
        programming: str,
        weeks: int,
        sessions_per_week: int
    ) -> str:
        """Costruisce il prompt per la generazione della scheda."""
        
        prompt_template = """
**RUOLO**: Sei un Coach Professionista di Personal Training con 15+ anni di esperienza.
Specializzato in programmazione dell'allenamento basata su evidenze scientifiche.

**COMPITO**: Generare un piano di allenamento personalizzato per il cliente.

**PROFILO CLIENTE**:
- Nome: {nome}
- Obiettivo: {goal} ({goal_description})
- Livello: {level} 
- Età: {age} anni
- Disponibilità: {disponibilita} giorni/settimana
- Durata sessione: {tempo_sessione} minuti
- Limitazioni: {limitazioni}
- Preferenze: {preferenze}

**METODOLOGIA CONSIGLIATA** (da Knowledge Base):
{methodology}

**PRINCIPI DI PROGRAMMAZIONE** (da Knowledge Base):
{programming}

**GENERARE UN PIANO DI {weeks} SETTIMANE CON {sessions_per_week} SESSIONI A SETTIMANA**

Struttura la risposta esattamente così:

---METODOLOGIA---
[Descrivi brevemente la metodologia scelta e perché è appropriata]

---SETTIMANA 1---
**Lunedì - [Focus]**
- Esercizio 1: [Nome] - [Serie]x[Reps] - Riposo [X] sec
- Esercizio 2: [Nome] - [Serie]x[Reps] - Riposo [X] sec
- Esercizio 3: [Nome] - [Serie]x[Reps] - Riposo [X] sec
[Continua per altre sessioni della settimana]

[RIPETI per settimane 2, 3, 4 se applicabile]

---DETTAGLI ESERCIZI---
- Esercizio 1:
  * Muscoli primari: [...]
  * Muscoli secondari: [...]
  * Tecnica: [descrizione breve]
[Continua per tutti gli esercizi unici]

---PROGRESSIONE---
[Strategia di progressione week-by-week]

---RECOVERY---
[Raccomandazioni specifiche per il cliente]

---

Basa TUTTO sulla metodologia e i principi forniti sopra.
Cita sempre la fonte: "[NomeFile, pag. X]"
"""
        
        goal_descriptions = {
            'strength': 'Aumento della forza massimale',
            'hypertrophy': 'Crescita muscolare',
            'endurance': 'Resistenza cardiovascolare',
            'fat_loss': 'Perdita di grasso corporeo',
            'functional': 'Fitness funzionale'
        }
        
        return prompt_template.format(
            nome=profile.get('nome', 'Cliente'),
            goal=profile.get('goal', 'general'),
            goal_description=goal_descriptions.get(profile.get('goal'), ''),
            level=profile.get('level', 'intermediate'),
            age=profile.get('age', 30),
            disponibilita=profile.get('disponibilita_giorni', 3),
            tempo_sessione=profile.get('tempo_sessione_minuti', 60),
            limitazioni=profile.get('limitazioni', 'Nessuna'),
            preferenze=profile.get('preferenze', 'Nessuna'),
            weeks=weeks,
            sessions_per_week=sessions_per_week,
            methodology=methodology,
            programming=programming
        )
    
    def _parse_workout_response(
        self,
        response: str,
        profile: Dict[str, Any],
        weeks: int,
        sessions_per_week: int
    ) -> Dict[str, Any]:
        """Parse la risposta generata in una struttura dati."""
        
        # Estrazione sezioni dal testo
        sections = {
            'methodology': self._extract_section(response, 'METODOLOGIA'),
            'weekly_schedule': self._extract_weekly_schedule(response, weeks),
            'exercises_details': self._extract_section(response, 'DETTAGLI ESERCIZI'),
            'progression': self._extract_section(response, 'PROGRESSIONE'),
            'recovery': self._extract_section(response, 'RECOVERY')
        }
        
        return {
            'client_name': profile.get('nome'),
            'goal': profile.get('goal'),
            'level': profile.get('level'),
            'duration_weeks': weeks,
            'sessions_per_week': sessions_per_week,
            'generated_at': datetime.now().isoformat(),
            'methodology': sections['methodology'],
            'weekly_schedule': sections['weekly_schedule'],
            'exercises_details': sections['exercises_details'],
            'progressive_overload_strategy': sections['progression'],
            'recovery_recommendations': sections['recovery']
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Estrae una sezione delimitata dal testo."""
        try:
            start_marker = f"---{section_name}---"
            end_marker = "---"
            
            start_idx = text.find(start_marker)
            if start_idx == -1:
                return f"Sezione '{section_name}' non trovata"
            
            start_idx += len(start_marker)
            end_idx = text.find(end_marker, start_idx)
            
            if end_idx == -1:
                end_idx = len(text)
            
            return text[start_idx:end_idx].strip()
        except Exception:
            return ""
    
    def _extract_weekly_schedule(self, text: str, weeks: int) -> List[Dict[str, str]]:
        """Estrae il programma settimanale dal testo."""
        schedule = []
        
        for week_num in range(1, weeks + 1):
            marker = f"---SETTIMANA {week_num}---"
            if marker in text:
                start_idx = text.find(marker)
                
                # Trova la prossima settimana o fine sezione
                next_marker = f"---SETTIMANA {week_num + 1}---"
                end_idx = text.find(next_marker)
                
                if end_idx == -1:
                    end_idx = text.find("---DETTAGLI ESERCIZI---")
                
                if end_idx == -1:
                    end_idx = len(text)
                
                week_content = text[start_idx:end_idx]
                schedule.append({
                    'week': week_num,
                    'content': week_content.strip()
                })
        
        return schedule
    
    def _extract_sources(self, documents: List) -> List[Dict[str, str]]:
        """Estrae le fonti dai documenti."""
        sources = []
        seen = set()
        
        for doc in documents:
            source_name = doc.metadata.get('source', 'Sconosciuta')
            page = str(doc.metadata.get('page', '?'))
            ref = f"{source_name}:{page}"
            
            if ref not in seen:
                sources.append({
                    'source': source_name,
                    'page': page,
                    'doc_id': doc.metadata.get('doc_id')
                })
                seen.add(ref)
        
        return sources


# ─────────────────────────────────────────────────────────
# UTILITY E TESTING
# ─────────────────────────────────────────────────────────

def test_workout_generator():
    """Testa il generatore con un profilo cliente esempio."""
    
    try:
        generator = WorkoutGenerator()
        print("✅ WorkoutGenerator inizializzato")
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return
    
    # Profilo cliente di test
    test_profile = {
        'nome': 'Mario Rossi',
        'goal': 'hypertrophy',
        'level': 'intermediate',
        'age': 28,
        'disponibilita_giorni': 4,
        'tempo_sessione_minuti': 60,
        'limitazioni': 'Lieve dolore al ginocchio sinistro',
        'preferenze': 'Preferisco esercizi con bilanciere'
    }
    
    print("\n📝 Generazione piano per:", test_profile['nome'])
    print("Recuperando dai documenti...")
    
    result = generator.generate_workout_plan(test_profile, weeks=4, sessions_per_week=4)
    
    if 'error' in result:
        print(f"❌ Errore: {result['error']}")
    else:
        print(f"\n✅ Piano generato per {result['client_name']}")
        print(f"Goal: {result['goal']}")
        print(f"Durata: {result['duration_weeks']} settimane")
        print(f"Fonti consultate: {len(result.get('sources', []))}")


if __name__ == "__main__":
    test_workout_generator()
