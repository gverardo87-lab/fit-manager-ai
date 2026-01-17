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

from core.config import MAIN_LLM_MODEL
from langchain.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM


class WorkoutGenerator:
    """Generatore di programmi allenamento basato su HYBRID (built-in + KB + LLM)."""
    
    def __init__(self, hybrid_chain=None):
        """
        Inizializza il generatore con hybrid knowledge.
        
        Args:
            hybrid_chain: Istanza di HybridKnowledgeChain (opzionale)
                Se None, carica automaticamente
        """
        from core.knowledge_chain import get_hybrid_chain
        
        self.hybrid_chain = hybrid_chain or get_hybrid_chain()
        
        # Verifica disponibilità della hybrid chain
        if not self.hybrid_chain:
            raise RuntimeError("HybridKnowledgeChain non disponibile")
        
        # Estrai LLM dalla hybrid chain se disponibile
        self.llm = self.hybrid_chain.llm if self.hybrid_chain else None
        
        # Nota: Non serve retriever/cross_encoder, sono nella hybrid_chain
        print(f"[OK] WorkoutGenerator inizializzato (KB loaded: {self.hybrid_chain.is_kb_loaded()})")
    
    # ─────────────────────────────────────────────────────────
    # GENERAZIONE SCHEDA CON HYBRID (built-in + KB)
    # ─────────────────────────────────────────────────────────
    
    def generate_workout_plan(
        self,
        client_profile: Dict[str, Any],
        weeks: int = 4,
        sessions_per_week: int = 3
    ) -> Dict[str, Any]:
        """
        Genera un piano di allenamento personalizzato usando HYBRID approach.
        
        - Cerca esercizi specifici nel KB per il goal
        - Usa built-in exercise database come fallback
        - Ibridizza KB + built-in
        - Personalizza con LLM
        """
        
        try:
            # Step 1: PRIMA COSA - Cerca nel KB gli esercizi per questo GOAL
            kb_exercises = None
            kb_methodology = None
            kb_sources = []
            
            if self.hybrid_chain.kb_available:
                print(f"[SEARCH KB] Cercando esercizi per goal: {client_profile['goal']}")
                kb_exercises = self._search_kb_exercises_for_goal(client_profile['goal'])
                kb_methodology = self._search_kb_methodology(client_profile['goal'], client_profile['level'])
                if kb_exercises or kb_methodology:
                    print(f"[FOUND] Trovati dati KB per {client_profile['goal']}")
                    kb_sources = [doc.metadata.get('source', 'Unknown') for doc in (kb_exercises or [])]
            
            # Step 2: Recupera template di workout built-in (fallback)
            template = self.hybrid_chain.exercise_db.get_workout_template(
                goal=client_profile['goal'],
                level=client_profile['level'],
                days_per_week=client_profile.get('disponibilita_giorni', 3)
            )
            
            # Step 3: Recupera periodizzazione
            periodization = self.hybrid_chain.get_periodization(
                periodization_type='linear',
                weeks=weeks
            )
            
            # Step 4: Recupera strategie progressione
            progression = self.hybrid_chain.get_progression_strategy(client_profile['goal'])
            
            # Step 5: Se LLM disponibile, personalizza CON DATI KB
            if self.llm:
                response = self._personalize_with_llm(
                    template=template,
                    periodization=periodization,
                    client_profile=client_profile,
                    weeks=weeks,
                    sessions_per_week=sessions_per_week,
                    kb_exercises=kb_exercises,
                    kb_methodology=kb_methodology,
                    kb_sources=kb_sources
                )
            else:
                response = self._build_basic_plan(
                    template=template,
                    periodization=periodization,
                    progression=progression,
                    client_profile=client_profile,
                    weeks=weeks,
                    sessions_per_week=sessions_per_week
                )
            
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'error': f"Errore nella generazione: {str(e)}",
                'client_name': client_profile.get('nome', 'Unknown')
            }
    
    def _build_basic_plan(self, template, periodization, progression, client_profile, weeks, sessions_per_week) -> Dict[str, Any]:
        """Costruisce un piano base senza LLM"""
        
        # Formatta la metodologia dal template
        methodology = f"""
## Metodologia di Allenamento

**Goal**: {client_profile.get('goal').upper()}
**Livello**: {client_profile.get('level').upper()}
**Durata**: {weeks} settimane

### Approccio
Utilizziamo un approccio {client_profile.get('goal')}-focused con periodizzazione lineare.

**Template Base**:
{json.dumps(template, indent=2, ensure_ascii=False) if template else 'Template non disponibile'}
"""
        
        # Crea lo schedule settimanale
        weekly_schedule = []
        if periodization:
            for phase in periodization.get('phases', []):
                weekly_schedule.append({
                    'week': f"Fase: {phase.get('phase', 'N/A')}",
                    'content': f"""
Settimane: {phase.get('weeks', 'N/A')}
Reps: {phase.get('reps', 'N/A')}
Intensità: {phase.get('intensity', 'N/A')}

Focus: {phase.get('phase', 'N/A')}
"""
                })
        
        # Dettagli esercizi dal template
        exercises_details = "## Esercizi Consigliati\n\n"
        if template and 'exercises' in template:
            for exc in template['exercises']:
                exercises_details += f"- {exc}\n"
        else:
            exercises_details += "Seleziona esercizi dal database built-in basandoti sul goal e livello."
        
        # Strategia progressione
        progression_text = "## Strategia di Progressione\n\n"
        if progression:
            progression_text += json.dumps(progression, indent=2, ensure_ascii=False)
        
        # Recovery
        recovery_text = f"""## Raccomandazioni Recovery

**Frequenza allenamenti**: {sessions_per_week} giorni/settimana
**Durata sessione**: {client_profile.get('tempo_sessione_minuti', 60)} minuti

### Deload
Ogni 4 settimane, ridurre il volume del 40% e l'intensità del 20%.

### Sleep & Nutrition
- 7-9 ore di sonno per notte
- Proteine: 1.6-2.2g per kg di peso corporeo
- Calorie adattate al goal
"""
        
        return {
            'client_name': client_profile.get('nome'),
            'goal': client_profile.get('goal'),
            'level': client_profile.get('level'),
            'duration_weeks': weeks,
            'sessions_per_week': sessions_per_week,
            'methodology': methodology,
            'weekly_schedule': weekly_schedule,
            'exercises_details': exercises_details,
            'progressive_overload_strategy': progression_text,
            'recovery_recommendations': recovery_text,
            'sources': [],
            'kb_used': False,
            'note': '✅ Utilizziamo template built-in. Per customizzazione avanzata, carica la KB.'
        }
    
    def _personalize_with_llm(self, template, periodization, client_profile, weeks, sessions_per_week, kb_exercises=None, kb_methodology=None, kb_sources=None) -> Dict[str, Any]:
        """Personalizza il piano con LLM, usando dati KB se disponibili"""
        
        # Costruisci contesto KB se disponibile
        kb_context = ""
        if kb_methodology:
            kb_context += f"METODOLOGIA DA KB:\n{kb_methodology[:1500]}\n\n"
        
        if kb_exercises:
            kb_context += "ESERCIZI TROVATI NEL KB:\n"
            for doc in kb_exercises[:3]:
                kb_context += f"- {doc.page_content[:300]}\n"
        
        prompt_template = """
Sei un esperto trainer professionale certificato. Genera una scheda di allenamento DETTAGLIATA e STRUTTURATA.

CLIENTE:
- Nome: {nome}
- Goal: {goal}
- Livello: {level}
- Disponibilità: {giorni}/settimana
- Durata sessione: {tempo} minuti
- Limitazioni: {limitazioni}
- Preferenze: {preferenze}

{kb_context}

TEMPLATE BASE:
{template}

PERIODIZZAZIONE:
{periodization}

GENERA UNA RISPOSTA STRUTTURATA CON:

## METODOLOGIA
Descrivi l'approccio di allenamento adatto al cliente (2-3 paragrafi). Se hai dati dal KB, usali per personalizzare.

## WEEKLY SCHEDULE
Per ogni settimana della periodizzazione, descrivi:
- Giorni di allenamento
- Focus muscolare di ogni sessione
- Volume e intensità

## ESERCIZI DETTAGLIATI
Per ogni sessione tipo:
- Nome esercizio
- Serie x Reps
- Tempo di riposo
- RPE (Scala di sforzo 1-10)

Se hai esercizi dal KB per il goal "{goal}", incorporali nella scheda.

## PROGRESSIONE
Come aumentare il carico ogni settimana.

## RECOVERY
Raccomandazioni su sonno, nutrizione, stretching.

Rispondi in italiano e sii SPECIFICO e PRATICO. Sfrutta i dati disponibili nel KB.
"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=['nome', 'goal', 'level', 'giorni', 'tempo', 'limitazioni', 'preferenze', 'template', 'periodization', 'kb_context']
        )
        
        chain = prompt | self.llm
        
        try:
            response_text = chain.invoke({
                'nome': client_profile.get('nome'),
                'goal': client_profile.get('goal'),
                'level': client_profile.get('level'),
                'giorni': client_profile.get('disponibilita_giorni', 3),
                'tempo': client_profile.get('tempo_sessione_minuti', 60),
                'limitazioni': client_profile.get('limitazioni', 'Nessuna'),
                'preferenze': client_profile.get('preferenze', 'N/A'),
                'template': json.dumps(template, ensure_ascii=False) if template else 'Template non disponibile',
                'periodization': json.dumps(periodization, ensure_ascii=False) if periodization else 'Periodizzazione non disponibile',
                'kb_context': kb_context
            })
            
            # Estrai sezioni dalla risposta LLM
            sections = {
                'methodology': self._extract_section(response_text, 'METODOLOGIA'),
                'weekly_schedule': [{'week': 'LLM Personalized', 'content': self._extract_section(response_text, 'WEEKLY SCHEDULE')}],
                'exercises_details': self._extract_section(response_text, 'ESERCIZI DETTAGLIATI'),
                'progressive_overload_strategy': self._extract_section(response_text, 'PROGRESSIONE'),
                'recovery_recommendations': self._extract_section(response_text, 'RECOVERY'),
                'sources': kb_sources or []
            }
            
            return {
                'client_name': client_profile.get('nome'),
                'goal': client_profile.get('goal'),
                'level': client_profile.get('level'),
                'duration_weeks': weeks,
                'sessions_per_week': sessions_per_week,
                'methodology': sections['methodology'],
                'weekly_schedule': sections['weekly_schedule'],
                'exercises_details': sections['exercises_details'],
                'progressive_overload_strategy': sections['progressive_overload_strategy'],
                'recovery_recommendations': sections['recovery_recommendations'],
                'sources': sections['sources'],
                'kb_used': bool(kb_exercises or kb_methodology)  # True se ho usato dati KB
            }
        except Exception as e:
            import traceback
            print(f"❌ Errore LLM personalization: {e}")
            traceback.print_exc()
            # Fallback a built-in plan
            return self._build_basic_plan(
                template=template,
                periodization=periodization,
                progression=None,
                client_profile=client_profile,
                weeks=weeks,
                sessions_per_week=sessions_per_week
            )
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Estrae una sezione dalla risposta LLM"""
        if not text or section_name not in text:
            return f"{section_name} non disponibile nel piano generato."
        
        # Cerca il header della sezione
        lines = text.split('\n')
        start_idx = -1
        for i, line in enumerate(lines):
            if section_name.lower() in line.lower():
                start_idx = i + 1
                break
        
        if start_idx == -1:
            return f"{section_name} non trovato."
        
        # Raccoglie le linee fino alla prossima sezione
        end_idx = len(lines)
        for i in range(start_idx, len(lines)):
            if lines[i].startswith('##') and i > start_idx:
                end_idx = i
                break
        
        content = '\n'.join(lines[start_idx:end_idx]).strip()
        return content if content else f"{section_name} vuota."
    
    def retrieve_training_methodology(self, goal: str, level: str) -> List[Dict[str, Any]]:
        """Legacy method - compatibilità"""
        return self.hybrid_chain.get_exercise_methodology(goal, level)
    
    def retrieve_exercise_details(self, exercise_name: str) -> List[Dict[str, Any]]:
        """Legacy method - compatibilità"""
        return self.hybrid_chain.retrieve_exercise_info(exercise_name)
        if not documents:
            return "Nessun documento trovato."
        
        context_parts = []
        for doc in documents:
            source = doc.metadata.get('source', 'Sconosciuta')
            page = doc.metadata.get('page', '?')
            content = doc.page_content[:500]  # Limita per evitare contesto troppo grande
            
            context_parts.append(f"[{source}, pag. {page}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _search_kb_exercises_for_goal(self, goal: str) -> Optional[List]:
        """Cerca nel KB esercizi specifici per un goal (es. calisthenics, strength, etc)"""
        if not self.hybrid_chain.kb_available or not self.hybrid_chain.retriever:
            return None
        
        try:
            # Query specifica per esercizi del goal
            queries = [
                f"esercizi {goal}",
                f"{goal} exercises movements",
                f"allenamento {goal}"
            ]
            
            all_docs = []
            for q in queries:
                try:
                    docs = self.hybrid_chain.retriever.invoke(q)
                    all_docs.extend(docs)
                except:
                    pass
            
            if not all_docs:
                return None
            
            # Re-rank con cross-encoder se disponibile
            if self.hybrid_chain.cross_encoder:
                scores = self.hybrid_chain.cross_encoder.predict(
                    [[f"{goal} exercises", doc.page_content[:200]] for doc in all_docs]
                )
                # Sort by score
                scored_docs = list(zip(scores, all_docs))
                scored_docs.sort(key=lambda x: x[0], reverse=True)
                return [doc for score, doc in scored_docs[:5]]  # Top 5
            
            return all_docs[:5]
            
        except Exception as e:
            print(f"[ERROR] Errore nella ricerca KB esercizi: {e}")
            return None
    
    def _search_kb_methodology(self, goal: str, level: str) -> Optional[str]:
        """Cerca nel KB la metodologia per goal + level"""
        if not self.hybrid_chain.kb_available or not self.hybrid_chain.retriever:
            return None
        
        try:
            query = f"{goal} {level} training methodology programming"
            docs = self.hybrid_chain.retriever.invoke(query)
            
            if not docs:
                return None
            
            # Prendi il documento più rilevante
            if self.hybrid_chain.cross_encoder:
                scores = self.hybrid_chain.cross_encoder.predict(
                    [[f"{goal} {level} training", doc.page_content[:300]] for doc in docs]
                )
                best_idx = scores.argmax()
                return docs[best_idx].page_content
            
            return docs[0].page_content
            
        except Exception as e:
            print(f"[ERROR] Errore nella ricerca KB metodologia: {e}")
            return None
    
    def retrieve_programming_principles(self) -> List[Dict[str, Any]]:
        """Legacy method - compatibilità"""
        return {}


# ─────────────────────────────────────────────────────────
# TESTING
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        gen = WorkoutGenerator()
        print("✅ WorkoutGenerator funziona!")
    except Exception as e:
        print(f"❌ Errore: {e}")
        print(f"Goal: {result['goal']}")
        print(f"Durata: {result['duration_weeks']} settimane")
        print(f"Fonti consultate: {len(result.get('sources', []))}")


if __name__ == "__main__":
    test_workout_generator()
