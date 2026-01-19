# WardOps Digital Twin

> 🏥 SimCity for Hospital Ops — An interactive command center with discrete-event simulation and AI copilot.

**WardOps** is an interactive digital twin platform for hospital operations management, combining discrete-event simulation with AI-powered decision support. Built as a modern full-stack application, it provides hospital administrators and operations teams with real-time insights, scenario planning capabilities, and an intelligent copilot to optimize patient flow, resource allocation, and operational efficiency.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-20+-green.svg)

## 🎯 Problem Statement

Hospital operations are complex systems with interdependent processes, limited resources, and unpredictable patient arrivals. Traditional approaches to operations management often rely on intuition, spreadsheets, or outdated systems that can't model the dynamic nature of healthcare workflows. WardOps addresses this gap by providing:

- **Real-time visibility** into hospital operations and patient flow
- **Predictive analytics** through discrete-event simulation
- **Scenario planning** to test operational changes before implementation
- **AI-assisted decision making** for complex operational questions

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
| 🗺️ **Interactive Floor Map** | Real-time bed status visualization with smooth animations, drag-and-drop bed management, and occupancy heatmaps |
| ⏱️ **Timeline Replay** | Scrub through a hospital day at variable speeds (1x/2x/5x), pause/resume functionality, and time-based analytics |
| 📊 **Dashboards** | Comprehensive KPI cards, Sankey flow diagrams showing patient movement, queue length charts, and utilization metrics |
| 🔬 **Scenario Builder** | Create what-if scenarios using intuitive sliders or natural language input, compare multiple scenarios side-by-side |
| ⚙️ **DES Simulation** | Advanced discrete-event simulation engine with bottleneck detection, resource attribution, and Monte Carlo analysis |
| 🤖 **AI Copilot** | LLM-powered assistant with function calling, policy-aware responses, and contextual operational recommendations |
| 🎨 **Modern UI** | Dark/light mode toggle, command palette (⌘K), keyboard shortcuts, responsive design, and accessibility features |

## � Use Cases

WardOps serves multiple stakeholders in healthcare operations:

### For Hospital Administrators
- **Capacity Planning**: Optimize bed utilization and predict future resource needs
- **Performance Monitoring**: Track key operational metrics and identify improvement opportunities
- **Strategic Planning**: Test the impact of policy changes or infrastructure investments

### For Operations Managers
- **Daily Operations**: Monitor real-time patient flow and identify bottlenecks
- **Staffing Optimization**: Determine optimal staffing levels based on patient arrival patterns
- **Emergency Response**: Simulate the impact of surge events and plan resource allocation

### For Clinical Teams
- **Patient Flow**: Understand patient journeys and identify delays in care delivery
- **Quality Improvement**: Analyze process variations and implement standardized workflows
- **Training**: Use simulation scenarios for staff training and process familiarization

## �🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, TailwindCSS, shadcn/ui, Framer Motion, Recharts |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis 7, Celery |
| AI | OpenAI API with function calling |

## 🏛️ Architecture Overview

WardOps follows a modern microservices-inspired architecture with clear separation of concerns:

### Frontend Layer
- **Next.js 14** with App Router for server-side rendering and API routes
- **TypeScript** for type safety and better developer experience
- **Zustand** for client-side state management
- **WebSocket** connections for real-time updates

### Backend Layer
- **FastAPI** for high-performance async API endpoints
- **SQLAlchemy** with async support for database operations
- **Celery** for background task processing and simulation runs
- **Pydantic** for data validation and serialization

### Data Layer
- **PostgreSQL** with pgvector for storing simulation data and embeddings
- **Redis** for caching and real-time data streaming
- **Alembic** for database migrations and schema versioning

### AI Layer
- **OpenAI API** integration with function calling for tool use
- **Vector embeddings** for policy-aware responses
- **Context-aware prompting** for operational recommendations

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

## 🤝 Contributing

We welcome contributions! WardOps is built as a demonstration of modern development practices and serves as a learning resource.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run tests: `cd backend && pytest -v`
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to your fork: `git push origin feature/your-feature`
7. Create a Pull Request

### Areas for Contribution
- **Simulation Models**: Improve the DES engine with more realistic healthcare processes
- **UI/UX Enhancements**: Add new visualization types or improve user interactions
- **AI Features**: Enhance the copilot with additional tools or better prompting
- **Performance**: Optimize database queries, caching, or frontend rendering
- **Testing**: Add more comprehensive test coverage

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

**WardOps** demonstrates modern full-stack development patterns including:
- Event-driven architecture with WebSockets
- AI integration with large language models
- Scalable async Python backends
- Type-safe React applications
- Containerized deployment with Docker
- Comprehensive testing strategies

Built with ❤️ for healthcare operations optimization.
