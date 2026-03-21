# Project Brain: Espaço Você

## 🌟 Overview
**Espaço Você** (Your Space) is an empathic AI-driven diary application designed as an educational project for **Estácio College** (ADS - Analysis and Systems Development). It aims to provide users with a personalized mentoring experience, where an AI assistant tracks their daily reflections, sentiments, and provides context-aware feedback.

## 🚀 Key Features
- **Personalized Memory**: The AI (Llama 3.3 70B via Groq) accesses the user's historical diary entries to understand patterns and connect insights.
- **User Profiling**: Dynamic user data (Name, Email, Plan) is stored in a database and used to personalize prompts.
- **SQLite Persistence**: All interactions (Reflections, Sentiments, AI Feedback) are stored locally in an SQLite database.
- **Terminal Integration**: A simple terminal interface to interact with the AI and view previous logs.

## 🛠️ Technology Stack
- **Languages**: Python (Backend)
- **Frameworks/Libraries**:
  - `sqlite3`: Database management.
  - `groq`: Integration with Llama models.
  - `python-dotenv`: Environment variable management.
- **Database**: SQLite (`espaco_voce.db`).
- **Deployment/Execution**: Local execution via terminal.

## 📁 Project Structure
- `Backend/`:
  - `banco_dados.py`: Handles database connections, queries, and terminal visualizer.
  - `LLM/`:
    - `ia_manager.py`: Core logic for AI interaction, prompt engineering, and context management.
- `SQL/`:
  - `espaco_voce.db`: The SQLite database file.
  - `espaco_voce.sqbpro`: SQLite Browser project file for schema management.
- `Curadoria/`: (Likely content or research materials).
- `PlanejamentoEV.odt`: Project planning document.

## 🔑 AI Integration Details
- **Model**: `llama-3.3-70b-versatile` (via Groq API).
- **Prompt Strategy**: Empathic Mentor. It uses a system prompt that injects:
  - User's name and identity.
  - Current sentiment (e.g., Happy, Neutral).
  - Memory of the last 12 diary entries.
- **Goal**: "Not just repeat facts. Try to connect the points. Use history to understand who the user is."
