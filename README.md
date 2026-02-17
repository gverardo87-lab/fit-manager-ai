# 🏋️ FitManager AI Studio

**AI-powered fitness management platform for personal trainers**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.36.0-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 What is FitManager AI?

A **privacy-first** fitness studio management platform that combines:
- **CRM**: Client management, measurements, anamnesis
- **AI Workout Programming**: RAG-based workout generation (local LLM via Ollama)
- **Financial Intelligence**: MRR tracking, margin analysis, cash flow
- **Scheduling**: Calendar integration for appointments
- **Document Explorer**: Upload PDFs (training manuals, research) for AI-powered Q&A

**Competitive Advantage**: Unlike cloud-based SaaS (Trainerize, TrueCoach), FitManager runs **AI models locally** (Ollama). Client health data **never leaves your infrastructure**.

---

## ⚡ Quick Start

### Prerequisites
- **Python 3.9+**
- **Ollama** (for local LLM): [Download here](https://ollama.ai/download)

### Installation

```powershell
# 1. Clone repository
git clone <repo-url>
cd FitManager_AI_Studio

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -e .

# 4. Install Ollama models
ollama pull llama3.2
ollama pull mistral

# 5. Run application
streamlit run server/app.py
```

Open browser at `http://localhost:8501`

---

## 📁 Project Structure

```
FitManager_AI_Studio/
├── core/                   # Business logic (CRM, workouts, financial analytics)
├── server/                 # Streamlit UI (multi-page web app)
│   ├── app.py             # Main dashboard
│   └── pages/             # Feature pages (Clients, Workouts, Finance, etc.)
├── knowledge_base/         # RAG system (PDF ingestion, ChromaDB)
├── data/                   # SQLite databases (crm.db, schedule.db)
├── .copilot-instructions.md  # AI assistant rules (read this!)
└── ROADMAP.md             # Feature roadmap
```

---

## 🚀 Key Features

### ✅ Current Features

- **Client Management**
  - Add/edit clients with full profiles
  - Track body measurements over time
  - Store medical history (anamnesi)
  - Client status tracking (Active/Inactive/Lead)

- **AI Workout Programming**
  - Generate personalized workout plans (RAG-based)
  - 72 exercises database with movement patterns
  - Periodization (strength/hypertrophy/endurance)
  - Intra-week variation (Day 1 ≠ Day 3, Day 2 ≠ Day 4)

- **Financial Intelligence**
  - Monthly Recurring Revenue (MRR) tracking
  - Hourly margin analysis
  - Cash flow visualization (Plotly charts)
  - Expense tracking (fixed/variable)

- **Scheduling & Agenda**
  - Calendar view for appointments
  - Shift management (1-on-1, group classes, online)
  - Client appointment history

- **Document Explorer**
  - Upload PDFs (training manuals, research papers)
  - AI-powered Q&A with semantic search
  - Citations to source documents

### 🚧 In Development (see [ROADMAP.md](ROADMAP.md))

- Heavy vs Volume days (intensity variation)
- Smart accessory selection
- Exercise database refactoring (JSON-based, scalable to 1000+)

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit 1.36.0 (Python web framework) |
| **Backend** | Python 3.9+, SQLite |
| **AI/LLM** | Ollama (llama3.2, mistral, qwen2.5) - Local models |
| **RAG** | LangChain + ChromaDB + sentence-transformers |
| **Validation** | Pydantic v2 |
| **Charts** | Plotly, Streamlit native charts |

**Why Local LLM?** Privacy compliance (GDPR). Client health data stays on your server, never sent to cloud APIs.

---

## 📖 Documentation

- **[.copilot-instructions.md](.copilot-instructions.md)**: Coding standards, architecture rules (required reading for AI assistants)
- **[ROADMAP.md](ROADMAP.md)**: Planned features
- **[knowledge_base/README.md](knowledge_base/README.md)**: RAG system documentation

---

## 🧪 Usage Examples

### Create a Client
1. Navigate to **03_Clienti** page
2. Fill form: Name, Surname, Email, Phone
3. Click **Aggiungi Cliente**
4. Track measurements over time (weight, body fat %, circumferences)

### Generate Workout Plan
1. Navigate to **07_Programma Allenamento** page
2. Select client, training level, goal (strength/hypertrophy/endurance)
3. Choose split (Upper/Lower, Full Body, Push/Pull/Legs)
4. Click **Genera Programma**
5. AI generates 8-week periodized plan (JSON output)

### Upload Training Manual
1. Navigate to **08_Document Explorer** page
2. Upload PDF (e.g., NSCA training manual)
3. Ask questions: "What's the optimal rep range for hypertrophy?"
4. RAG system retrieves relevant sections + generates answer

---

## 🔐 Security & Privacy

- **Local AI**: All LLM inference runs on Ollama (local server)
- **Local Storage**: SQLite databases stored locally (no cloud sync)
- **Parameterized Queries**: All SQL queries use parameters (anti SQL-injection)
- **No Telemetry**: No analytics tracking (privacy-first)
- **GDPR Ready**: Export/delete client data functionality

---

## 🤝 Contributing

**For AI Assistants** (GitHub Copilot, Cursor, etc.):  
Read [.copilot-instructions.md](.copilot-instructions.md) first. It contains:
- Mandatory design patterns
- Anti-patterns to avoid
- Code style conventions
- Security rules

**For Human Contributors**:  
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow coding standards in `.copilot-instructions.md`
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **Ollama Team**: Local LLM infrastructure
- **LangChain**: RAG framework
- **Streamlit**: Rapid web app development
- **Fitness Community**: Feedback and feature requests

---

**Version**: 3.0.0  
**Last Updated**: February 17, 2026  
**Maintained by**: G. Verardo

*For detailed technical documentation, see [.copilot-instructions.md](.copilot-instructions.md)*
