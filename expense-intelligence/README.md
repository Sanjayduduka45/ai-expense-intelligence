# AI Expense Intelligence

> **Roast • Analyze • Recover**

An AI-powered personal expense intelligence platform that analyzes your monthly spending, delivers an honest (sometimes brutal) AI-generated roast, and provides a data-driven recovery plan.

---

## Architecture

```
Streamlit UI  →  FastAPI  →  Validation  →  Expense / Data Services  →  AI Services  →  Gemini API
```

> **Rule**: Streamlit never calls Gemini directly. All AI interactions go through the FastAPI service layer.

---

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend / API | FastAPI |
| Language | Python 3.11+ |
| Data processing | Pandas + NumPy |
| Visualisation | Plotly |
| AI | Google Gemini API |
| Validation | Pydantic |
| Configuration | `.env` + `pydantic-settings` |

---

## Project layout

```
expense-intelligence/
├── app/
│   ├── frontend/
│   │   ├── streamlit_app.py        # Streamlit entry point
│   │   ├── components/             # Reusable UI widgets
│   │   ├── pages/                  # Multi-page app pages
│   │   └── utils/
│   │       └── api_client.py       # HTTP client (Streamlit → FastAPI)
│   ├── backend/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── api/
│   │   │   └── health.py           # GET /health
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── services/               # Business + AI service layer
│   │   └── core/
│   │       └── config.py           # Settings via pydantic-settings
│   └── shared/
│       └── constants.py            # Cross-cutting constants
├── tests/
│   └── test_phase0_foundation.py
├── data/
│   └── sample/                     # Dev sample files (never commit real data)
├── docs/
├── .env.example                    # Placeholder — copy to .env and fill in
├── .gitignore
├── requirements.txt
├── run.py                          # Convenience launcher
└── README.md
```

---

## Quick start

### 1 — Clone and set up the environment

```bash
git clone <repo-url>
cd expense-intelligence

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2 — Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in GEMINI_API_KEY (and any other values)
```

### 3 — Run the backend

```bash
# Option A — convenience launcher
python run.py backend

# Option B — uvicorn directly
uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend is available at:
- API: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/health
- Interactive docs: http://127.0.0.1:8000/docs

### 4 — Run the frontend

Open a **second terminal** (with the same venv activated):

```bash
# Option A — convenience launcher
python run.py frontend

# Option B — streamlit directly
streamlit run app/frontend/streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```

Frontend is available at: http://127.0.0.1:8501

### 5 — Run tests

```bash
pytest tests/ -v
```

---

## Security notes

- **Never** commit a real `.env` file — it is listed in `.gitignore`.
- **Never** commit personal financial data. The `data/uploads/` and `data/personal/` directories are git-ignored.
- API keys are loaded exclusively from environment variables via `pydantic-settings`. They are never logged or printed.

---

## Development phases

| Phase | Scope |
|---|---|
| **0 (current)** | Project foundation — health endpoint, app shell |
| 1 | Expense data upload & validation |
| 2 | Spending pattern analysis & visualisation |
| 3 | Gemini AI roast + recovery plan |
| 4 | AI assistant chatbot |
| 5 | Polish, error handling, deployment |

---

## Licence

MIT
