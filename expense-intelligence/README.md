# AI Expense Intelligence

> **Roast • Analyze • Recover**

AI Expense Intelligence is a privacy-first, full-stack financial intelligence platform. It analyzes your transaction exports, calculates factual spending metrics, delivers a witty evidence-backed AI roast, surfaces actionable recovery plans with monthly/yearly savings, and provides an interactive conversational assistant.

---

## 🏛️ System Architecture

```
                                 ┌─────────────────────────────────────────────────┐
                                 │              Streamlit Cloud Frontend           │
                                 │     (Upload • Preview • 5 KPIs • Charts)        │
                                 │     (Roast & Recovery • AI Assistant Chat)      │
                                 └────────────────────────┬────────────────────────┘
                                                          │ HTTP (BACKEND_URL)
                                                          ▼
                                 ┌─────────────────────────────────────────────────┐
                                 │           FastAPI Backend (Render / Railway)    │
                                 │                                                 │
                                 │  ┌──────────────────┐    ┌───────────────────┐  │
                                 │  │ Ingestion &      │    │ Deterministic     │  │
                                 │  │ Sanitization     │───▶│ Analytics Engine  │  │
                                 │  │ (CSV Validation) │    │ (Pandas & NumPy)  │  │
                                 │  └──────────────────┘    └─────────┬─────────┘  │
                                 │                                    │            │
                                 │                                    ▼            │
                                 │                          ┌───────────────────┐  │
                                 │                          │ Gemini AI Service │  │
                                 │                          │ (Quarantine Tags) │  │
                                 │                          └─────────┬─────────┘  │
                                 └────────────────────────────────────┼────────────┘
                                                                      │ Encrypted HTTPS
                                                                      ▼
                                                            ┌───────────────────┐
                                                            │ Google Gemini API │
                                                            └───────────────────┘
```

### Key Architectural Principles:
1. **Frontend/Backend Isolation**: The Streamlit frontend **never** communicates directly with Google Gemini. All AI queries, data validation, and calculations execute strictly on the FastAPI backend.
2. **Secrets Security**: `GEMINI_API_KEY` exists exclusively in the backend environment. It is never logged, exposed via API responses, or delivered to the browser.
3. **Deterministic Separation**: Factual financial metrics (totals, time series, category %, largest expenses) are strictly calculated by Pandas/NumPy before any LLM prompt is assembled.
4. **Prompt Injection Defense**: All user-supplied transaction descriptions and questions are quarantined within `<user_financial_data>...</user_financial_data>` XML boundary tags.

---

## 🛠️ Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | Streamlit + Plotly | Responsive 5-stage narrative UI, interactive charts, metric KPIs |
| **Backend** | FastAPI + Uvicorn | High-performance async REST API with centralized exception handlers |
| **Analytics Engine** | Pandas + NumPy | Deterministic financial analytics, Pareto concentration, IQR outlier detection |
| **AI Intelligence** | Google Gemini SDK | Structured JSON output for evidence-based roasts & prioritized recovery plans |
| **Validation** | Pydantic v2 + Pydantic Settings | Strict request/response validation and environment loading |
| **Testing** | Pytest + HTTPX | 93 automated unit, integration, and security test cases |

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.11, 3.12, or 3.13
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Setup Environment
```bash
git clone <repo-url>
cd expense-intelligence

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install production and test dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` and set your `GEMINI_API_KEY`:
```ini
GEMINI_API_KEY=AIzaSy...your_actual_key
APP_ENV=development
LOG_LEVEL=INFO
```

### 4. Start the Application

#### Option A: Convenient Launcher
Open two terminal windows (with `.venv` activated):

*Terminal 1 (Backend):*
```bash
python run.py backend
```

*Terminal 2 (Frontend):*
```bash
python run.py frontend
```

#### Option B: Direct Commands

*Terminal 1 (FastAPI Backend):*
```bash
uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```
- API Root: `http://127.0.0.1:8000`
- Health Check: `http://127.0.0.1:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

*Terminal 2 (Streamlit Frontend):*
```bash
streamlit run app/frontend/streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```
- Frontend Dashboard: `http://127.0.0.1:8501`

---

## 🧪 Running Tests

Execute the comprehensive automated test suite (93 tests covering API foundation, ingestion, deterministic analytics, Gemini integration, assistant chat, and security hardening):

```bash
pytest tests/ -v
```

---

## 🚀 Production Deployment Guide

### Part 1: Deploy Backend (Render or Railway)

#### Deploying on Render:
1. Create a new account at [Render](https://render.com/).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository.
4. Select **Python** runtime and configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`
5. In **Environment Variables**, add:
   - `APP_ENV` = `production`
   - `LOG_LEVEL` = `INFO`
   - `GEMINI_API_KEY` = `your_gemini_api_key`
   - `CORS_ORIGINS` = `https://your-app-name.streamlit.app`
6. Click **Deploy**. Note your backend URL (e.g., `https://ai-expense-backend.onrender.com`).

#### Deploying on Railway:
1. Create a new project at [Railway](https://railway.app/).
2. Select **Deploy from GitHub repo**.
3. Railway automatically detects the [Procfile](file:///Users/sanjayduduka/Capstone%20Mirai/expense-intelligence/Procfile) (`web: uvicorn app.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`).
4. Under **Variables**, configure `GEMINI_API_KEY`, `APP_ENV=production`, and `CORS_ORIGINS`.
5. Under **Settings** $\rightarrow$ **Networking**, generate a public domain.

---

### Part 2: Deploy Frontend (Streamlit Cloud)

1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **New app** and select your GitHub repository.
3. Configure deployment settings:
   - **Main file path**: `app/frontend/streamlit_app.py`
4. Under **Advanced settings** $\rightarrow$ **Secrets**, configure your backend URL:
   ```toml
   BACKEND_URL = "https://ai-expense-backend.onrender.com"
   ```
5. Click **Deploy**.

---

## 🔒 Security & Privacy Notes

- **Zero Hardcoded Secrets**: Credentials are read strictly from environment variables.
- **Log Redaction**: Automatic `SensitiveDataFilter` masks all API keys in logging output (`[REDACTED_API_KEY]`).
- **Path Traversal Neutralization**: All uploaded file paths are sanitized via `Path(filename).name` and stripped of null bytes.
- **CSV Formula Injection Defense**: Escapes values starting with `=`, `+`, `-`, `@`, `\t`, `\r` with single-quote prepending.
- **Strict Production CORS**: Wildcard origins (`*`) are programmatically rejected when `APP_ENV=production`.
- **Centralized Error Masking**: Internal server errors return sanitized JSON messages and never expose tracebacks or credentials to clients.

---

## 📄 License

MIT
