# ⚡ QUICK START - Workout Engine

**Tempo**: 5 minuti per capire come funziona

---

## 🎯 THE IDEA

FitManager AI now generates **personalized workout programs** using **AI + Knowledge Base**.

Instead of:
```
Manual → PT creates Excel spreadsheet → Email to client
```

Now:
```
Client data → AI RAG → Generate smart program → Save in system
```

---

## 🚀 3 QUICK STEPS

### Step 1: ADD DOCUMENTS
Put PDF files in: `knowledge_base/documents/`

Examples:
- `Linear_Periodization.pdf`
- `Exercise_Anatomy.pdf`
- `Training_Principles.pdf`

(Suggested sources: StartingStrength, 5/3/1, Muscle Hypertrophy guides)

### Step 2: INGEST
```bash
python knowledge_base/ingest.py
```

Wait for: `Vector Store created in: 'knowledge_base/vectorstore'`

### Step 3: GENERATE
1. Open Streamlit: `streamlit run server/app.py`
2. Click: "🏋️ Programma Allenamento"
3. Select client
4. Fill form:
   - Goal: Hypertrophy / Strength / Fat Loss / Endurance
   - Level: Beginner / Intermediate / Advanced
   - Days/week: 3-5
   - Time/session: 60 min
   - Limitations: (optional)
5. Click: "🤖 Genera Programma"
6. Wait 20-40 seconds (LLM generating)
7. View results
8. Click: "💾 Salva Programma"

---

## 📊 WHAT YOU GET

The AI generates:

```
📋 PROGRAMMA DI ALLENAMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔬 Metodologia
   [Why this approach fits the client]

📅 Schedule Settimanale
   Lunedì - Upper Body Push
   ├─ Esercizio 1: Panca Piana 4x6
   ├─ Esercizio 2: Spalle 4x8
   └─ Esercizio 3: Tricipiti 3x10
   
   Martedì - Lower Body
   ├─ Esercizio 1: Squat 4x5
   ├─ Esercizio 2: Stacco 4x5
   └─ Esercizio 3: Gambe Accessorie 3x10
   ...

💪 Dettagli Esercizi
   Panca Piana:
   - Muscoli primari: Petto, Spalle Anteriori
   - Muscoli secondari: Tricipiti
   - Tecnica: Scapola retratta, piedi su panca...

📈 Progressione
   Settimana 1-2: Volume base
   Settimana 3-4: Aumenta intensità del 5%
   Settimana 5-6: Deload (ridotta)
   Settimana 7-8: Peak

😴 Recovery
   - Dormi 7-9 ore
   - 2 rest days per settimana
   - Stretching 10 min al termine
   - Mangia 0.8g proteina per kg peso

📚 Fonti
   - Linear_Periodization.pdf, pag. 12
   - Exercise_Anatomy.pdf, pag. 45
```

---

## 💾 WHERE PROGRAMS ARE SAVED

Database: `data/crm.db`

Table: `workout_plans`
```sql
SELECT * FROM workout_plans 
WHERE id_cliente = 5
ORDER BY data_creazione DESC;
```

All fields are **JSON-compatible**, so you can:
- Export to PDF (Streamlit export)
- Send via email
- Share with nutrition app
- Track progress over time

---

## 🧠 HOW THE AI WORKS

```
"Generate hypertrophy program for intermediate"

      ↓

RAG Query to Documents:
├─ "Periodizzazione per ipertrofia"
├─ "Esercizi per crescita muscolare"
└─ "Progressione sovraccarico"

      ↓

Retrieve from PDF Library:
├─ Linear_Periodization.pdf (page 12)
├─ Hypertrophy_Guide.pdf (pages 5-20)
└─ Training_Principles.pdf (page 8)

      ↓

Re-rank by Relevance (Cross-Encoder)

      ↓

Build AI Prompt with Context:
"Based on these methodologies...
and this client profile...
generate a 4-week hypertrophy program"

      ↓

LLM Response (Ollama/Llama3):
[Generates structured workout plan with citations]

      ↓

Parse & Save to DB

      ↓

Display in Streamlit
```

---

## 🎓 KEY CONCEPTS

### RAG (Retrieval-Augmented Generation)
The AI doesn't know about training by itself. It **reads your PDFs** and generates based on that content.

Benefit: **No hallucinations** (AI can't make up exercises)

### Knowledge Base
All your training PDFs become a "smart book" that the AI can query instantly.

You can add:
- Periodization models
- Exercise libraries
- Anatomy references
- Nutrition guides
- Recovery protocols

### Privacy-First AI
✅ Everything runs **locally** (no cloud)
✅ Your data never leaves your server
✅ Zero tracking
✅ GDPR compliant by design

---

## 📱 CLIENT EXPERIENCE

When client views their program (in future mobile app):

```
CLIENT APP
━━━━━━━━━━━━━━━━━━━━━━
Your Program
├─ Goal: Hypertrophy
├─ Duration: 8 weeks
├─ Sessions: 4 days/week

📅 Today's Workout
   Leg Day
   ├─ Squat 4x5 (200 kg)
   ├─ RDL 4x8 (180 kg)
   └─ Leg Press 3x12 (300 kg)

✅ LOG WORKOUT
   [Record sets/reps]

📊 PROGRESS
   [Charts of strength gains]

💬 MESSAGE COACH
   [Ask question about form]
```

---

## 🔍 TROUBLESHOOTING

### "Knowledge Base not found"
```bash
python knowledge_base/ingest.py
```
Make sure `knowledge_base/documents/` has PDF files.

### "Ollama not responding"
```bash
# Terminal 1:
ollama serve

# Terminal 2:
ollama pull llama3:8b-instruct-q4_K_M
```

### "Responses not relevant"
→ Add more specific PDFs to your knowledge base
→ Example: "Linear Periodization for Hypertrophy.pdf"

### "Too slow (>1 minute)"
→ Normal on first generation (LLM is thinking)
→ Subsequent generations use cache, faster

---

## 🚀 ADVANCED USAGE

### Custom Periodization Models
Add to knowledge base:
- `MyGym_Hypertrophy_Protocol.pdf`
- `Competition_Prep_Cycle.pdf`
- `Deload_Guidelines.pdf`

AI will **automatically** incorporate them.

### Track Client Progress
After each workout session:
- Log reps/weight in "📈 Progresso"
- AI learns and **adapts future programs**

### Export Programs
(Future feature)
```
Right-click program → Export as PDF/Email
Share directly with client
```

---

## 📈 EXAMPLE FLOW

**Monday 9:00 AM**
```
PT Opens FitManager
└─ "Programma Allenamento"
   └─ Select: "Marco Bianchi"
   └─ Goal: Strength
   └─ Level: Advanced
   └─ Disponibilità: 4 days/week
   └─ Time: 75 min
   └─ "Genera" → Wait 30 sec
   └─ View results (8-week periodized program)
   └─ "Salva"
   └─ Condividi link con Marco

Marco visualizza il suo programma e inizia l'allenamento!
```

---

## 📚 DOCUMENT RECOMMENDATIONS

To build a strong knowledge base, add:

**Essential:**
- [ ] Starting Strength (Mark Rippetoe) - PDF
- [ ] 5/3/1 (Jim Wendler) - PDF
- [ ] Bigger Leaner Stronger (Michael Matthews) - PDF

**Intermediate:**
- [ ] Greg Nuckols - Hypertrophy Guide
- [ ] Bret Contreras - Glute Lab
- [ ] Dan John - Never Let Go

**Advanced:**
- [ ] Gray's Anatomy (key sections)
- [ ] Journal articles on periodization
- [ ] Individual PT templates

---

## ✅ CHECKLIST

- [ ] Read this Quick Start
- [ ] Gather 3-5 training PDFs
- [ ] Copy to `knowledge_base/documents/`
- [ ] Run `python knowledge_base/ingest.py`
- [ ] Open Streamlit
- [ ] Go to "🏋️ Programma Allenamento"
- [ ] Test generation with a client
- [ ] Save program
- [ ] View in "Programmi Salvati"
- [ ] Celebrate! 🎉

---

## 🎯 NEXT WEEKS

After you test workout generation:
- Week 2: Mobile App (so clients can access)
- Week 3: Payment Integration (Stripe)
- Week 4: Client Booking (self-service)

---

**TL;DR**: Add PDFs → Click button → AI generates personalized programs → Save in system → Repeat

Enjoy! 🏋️‍♂️
