# 📚 KNOWLEDGE BASE - GUIDA SETUP

**File di configurazione per ingestione documenti PDF e generazione AI programmi allenamento**

---

## 🎯 COSA VA IN QUESTA CARTELLA

Inserisci qui tutti i PDF con metodologie di allenamento, anatomia e biomeccanica:

```
knowledge_base/
├── documents/
│   ├── Metodologie_Allenamento/
│   │   ├── Linear_Periodization.pdf
│   │   ├── Block_Periodization.pdf
│   │   ├── Undulating_Periodization.pdf
│   │   └── Training_Principles.pdf
│   ├── Anatomia_Biomeccanica/
│   │   ├── Anatomy_Muscles.pdf
│   │   ├── Biomechanics_Movement.pdf
│   │   └── Exercise_Mechanics.pdf
│   ├── Esercizi/
│   │   ├── Upper_Body_Exercises.pdf
│   │   ├── Lower_Body_Exercises.pdf
│   │   └── Core_Training.pdf
│   ├── Nutrizione/
│   │   ├── Nutrition_for_Strength.pdf
│   │   └── Macro_Calculation.pdf
│   └── Recovery/
│       ├── Sleep_Recovery.pdf
│       └── Stretching_Mobility.pdf
├── vectorstore/        # Generato automaticamente
│   ├── ...embeddings...
└── ask.py, ingest.py
```

---

## 🚀 SETUP INIZIALE

### Passo 1: Raccogli i PDF
Ottieni o crea documenti PDF su:

**ESSENZIALI:**
- Principi di periodizzazione (linear, block, undulating)
- Elenco esercizi con anatomia
- Biomeccanica movimento

**CONSIGLIATI:**
- Protocolli per goal specifici (forza, ipertrofia, cardio, fat loss)
- Nutrizione per l'allenamento
- Recovery e mobilità

### Passo 2: Metti i PDF qui
Copia i PDF nella cartella `documents/` (crea sottocartelle se vuoi organizzare)

### Passo 3: Esegui Ingest
```bash
# Dal root del progetto:
python knowledge_base/ingest.py
```

Output atteso:
```
INFO: Librerie importate correttamente.
--- Estrazione da: Linear_Periodization.pdf ---
  > Estratte 45 pagine.
--- Suddivisione semantica dei documenti in chunk ---
  > Documenti suddivisi in 2847 chunk totali.
--- Inizio creazione del Vector Store ---
--- Vector Store creato in: 'knowledge_base/vectorstore' ---
```

### Passo 4: Testa il RAG
```bash
python knowledge_base/ask.py
```

```
*** Assistente Tecnico da Documentazione Attivo (Test da Console) ***

Inserisci la tua domanda (o scrivi 'esci' per terminare): 
> Come si programma l'ipertrofia per un principiante?

--- Chiamo l'esperto... (potrebbe richiedere un po' di tempo) ---

========================================
   RISPOSTA DELL'ESPERTO
========================================
La programmazione per l'ipertrofia prevede... [risposta basata su PDF]

----------------------------------------
   FONTI CONSULTATE
----------------------------------------
- Linear_Periodization.pdf, Pagina: 12
- Training_Principles.pdf, Pagina: 5
========================================
```

---

## 📚 RECOMMENDED DOCUMENTS

### 1. **Periodization Models**
- Lyle McDonald - "The Periodized Diet"
- Louie Simmons - "Westside Book of Knowledge"
- Dan John - "Never Let Go"

### 2. **Exercise Science**
- Greg Nuckols - "Science and Development of Muscle Hypertrophy"
- Mike Israetel - "Everyman's Guide to Growth"
- Bret Contreras - "Glute Lab"

### 3. **Coaching Manuals**
- Starting Strength - Mark Rippetoe
- 5/3/1 - Jim Wendler
- Bigger Leaner Stronger - Michael Matthews

### 4. **Anatomy & Biomechanics**
- Gray's Anatomy for Athletes
- Movement System Impairment Syndromes - Sahrmann
- Assessment and Treatment of Muscle Imbalance - Janda

---

## 🔄 WORKFLOW DI GENERAZIONE

```
User Input (Goal, Level, Disponibilità)
           ↓
         RAG Query
           ↓
Retrieve Metodologie Rilevanti (ChromaDB)
           ↓
Cross-Encoder Re-ranking (Top 4)
           ↓
LLM Prompt con Contesto
           ↓
Generate Workout Plan
           ↓
Parse & Validate
           ↓
Save in DB + Display
```

**Tempi:**
- Query retrieval: ~1-2 sec
- LLM generation: ~10-30 sec (dipende da Ollama)
- Total: ~15-45 secondi

---

## 🛠️ TROUBLESHOOTING

### Problema: "Database della conoscenza non trovato"
**Soluzione:**
```bash
python knowledge_base/ingest.py
```

Assicurati che `documents/` contiene almeno un PDF.

### Problema: "LLM non risponde / timeout"
**Soluzione:**
Assicurati che Ollama è avviato:
```bash
ollama serve
```

E che il modello è installato:
```bash
ollama pull llama3:8b-instruct-q4_K_M
```

### Problema: "Risposte poco rilevanti"
**Soluzione:**
- Aggiungi più documenti sulla metodologia specifica
- Usa query più specifiche (es. "periodizzazione lineare per ipertrofia" vs "allenamento")
- Usa esercizi di re-ranking (cross-encoder)

---

## 📊 METRICS

Traccia le performance della tua knowledge base:

| Metrica | Target | Attuale |
|---------|--------|---------|
| Documenti | 10+ | _ |
| Pagine totali | 200+ | _ |
| Chunk | 2000+ | _ |
| Latency retrieval | <2s | _ |
| LLM generation | <30s | _ |
| Relevance score | >0.5 | _ |

---

## 🔐 PRIVACY & SECURITY

✅ **FitManager AI è Privacy-First:**
- ✅ LLM locale (Ollama) - niente cloud
- ✅ Dati rimangono sul server
- ✅ Nessun tracking esterno
- ✅ GDPR compliant per design

**Implicazioni:**
- Tutte le query rimangono locali
- Puoi condividere PDF sensibili senza rischi
- Nessun vendor lock-in

---

## 🎓 COME USARE CON I CLIENTI

1. **Generazione Programma**: Client profilo → RAG retrieval → LLM generation → Programma personalizzato
2. **Spiegazione Esercizi**: Cliente chiede "come fare uno squat?" → Chat RAG tira da KB
3. **Coaching Support**: Trainer ha reference veloce su anatomia, metodologia, nutrizione

---

## 📝 NOTES

- Il knowledge base viene caricato una sola volta all'avvio (@st.cache_resource)
- Cross-encoder è ottimizzato per query tecnico/scientifico
- Temperature del LLM: 0.2 (preferisce precisione vs creatività)
- K retrieval: 10 documenti (poi re-ranked a 4)

---

*Setup completato: 17 Gennaio 2026*
