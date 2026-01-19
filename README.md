# WardOps Digital Twin

> 🏥 SimCity for Hospital Ops — An interactive command center with discrete-event simulation and AI copilot.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)

## 🚀 Quick Start

### Option 1: With Docker (Recommended)
```bash
docker compose up --build
```

### Option 2: Without Docker (Local Development)
```powershell
# 1. Setup backend (one-time)
cd backend
.\setup.ps1

# 2. Start backend
.\start.ps1

# 3. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Prerequisites for local setup:**
- PostgreSQL 16 with `wardops` database created
- Redis running on localhost:6379
- Python 3.11+ and Node.js 20+

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗺️ **Interactive Floor Map** | Real-time bed status with smooth animations |
| ⏱️ **Timeline Replay** | Scrub through a hospital day at 1x/2x/5x speed |
| 📊 **Dashboards** | Sankey flow, queue charts, KPI cards |
| 🔬 **Scenario Builder** | Create what-if scenarios with sliders or natural language |
| ⚙️ **DES Simulation** | Discrete-event simulation engine with bottleneck attribution |
| 🤖 **AI Copilot** | LLM assistant with tool-calling and policy RAG |
| 🎨 **Modern UI** | Dark mode, command palette (⌘K), keyboard shortcuts |

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, TailwindCSS, shadcn/ui, Framer Motion, Recharts |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis 7, Celery |
| AI | OpenAI API with function calling |

## 📁 Project Structure

```
WardOps/
├── frontend/           # Next.js application
│   ├── src/app/        # Pages (command center, scenario, compare)
│   ├── src/components/ # React components
│   └── src/stores/     # Zustand state management
├── backend/            # FastAPI application
│   ├── app/api/        # REST + WebSocket routes
│   ├── app/simulation/ # DES engine
│   └── app/llm/        # Tool router + copilot
└── docker-compose.yml  # One-command deployment
```

## 🛠️ Development

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Local Development

```bash
# Start infrastructure only
docker compose up postgres redis -d

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://postgres:postgres@localhost:5432/wardops` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `OPENAI_API_KEY` | For LLM copilot | (optional for demo) |

### Running Tests

```bash
cd backend
pytest -v
```

## 📖 Documentation

Additional documentation files are available locally in the project directory for detailed guides on architecture, demo scripts, and project planning.

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `⌘/Ctrl + K` | Open command palette |
| `Space` | Play/pause timeline |
| `T` | Toggle dark mode |
| `→` / `←` | Step forward/backward |

## 🔌 API Reference

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
GET  /api/health              # Health check
POST /api/demo/load           # Load synthetic data
GET  /api/units               # List units
GET  /api/beds/{unit_id}      # Get beds
GET  /api/patients/{id}/trace # Patient journey
POST /api/scenarios           # Create scenario
POST /api/simulation/run      # Run simulation
POST /api/copilot/chat        # AI chat
```

## 🔒 Safety Notes

- **No medical advice**: Copilot refuses diagnosis/treatment questions
- **Synthetic data only**: No real patient data
- **Operational focus**: All analytics are for ops optimization

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ as a demonstration of modern full-stack development patterns.
