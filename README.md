# OpsMesh

**AI-powered incident intelligence and workflow platform**

OpsMesh is a production-grade system that ingests logs, events, and incidents, then applies intelligent processing to deduplicate alerts, score severity, identify root causes, and generate response recommendations—all visible through a real-time dashboard.

---

## Why OpsMesh?

Modern operations teams are overwhelmed by alert noise. OpsMesh reduces cognitive load by:

- **Clustering similar incidents** to eliminate duplicate alerts
- **Scoring severity** based on rules and ML signals
- **Generating AI-powered response suggestions** for faster resolution
- **Maintaining full audit trails** for compliance and learning

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INGESTION                               │
│   Log Sources  •  Webhooks  •  Manual Input  •  API Clients     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Gateway                            │
│           REST API  •  Auth  •  Validation  •  Rate Limiting    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│      PostgreSQL         │   │      Redis Queue        │
│  Incidents • Audit Logs │   │    Job Dispatch         │
└─────────────────────────┘   └───────────┬─────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Worker Pipeline                            │
│   Normalize  →  Deduplicate  →  Score Severity  →  AI Suggest   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    Next.js Dashboard    │   │      AI Layer           │
│ Incidents • Timeline    │   │ OpenAI-compatible API   │
│ Search • Analytics      │   │ Response Generation     │
└─────────────────────────┘   └─────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Backend** | FastAPI (Python 3.11+), Pydantic |
| **Database** | PostgreSQL 16 |
| **Queue/Cache** | Redis 7 |
| **Workers** | RQ (Redis Queue) |
| **AI** | OpenAI-compatible API abstraction |
| **Auth** | Clerk / Auth.js (planned) |
| **Observability** | OpenTelemetry, Prometheus/Grafana (planned) |
| **Infrastructure** | Docker, GitHub Actions |
| **Deployment** | Vercel (frontend), Railway/Render/Fly.io (backend) |

---

## Key Features

### v1 (Current Focus)
- [ ] Incident ingestion API
- [ ] Dashboard with incident list
- [ ] Deduplication and clustering
- [ ] Severity scoring engine
- [ ] AI-generated response suggestions
- [ ] Incident timeline
- [ ] Search and filtering
- [ ] Basic authentication
- [ ] Audit logging
- [ ] Dockerized local development
- [ ] Test suite
- [ ] CI/CD pipeline

### v2 (Planned)
- [ ] Slack/email alerting
- [ ] Multi-tenant support
- [ ] Role-based access control
- [ ] Cost/latency dashboard
- [ ] LLM fallback routing
- [ ] Benchmark/evaluation panel

---

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- pnpm (`npm install -g pnpm`)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/opsmesh.git
cd opsmesh

# Start infrastructure (Postgres + Redis)
docker compose up postgres redis -d

# Start the API
cd apps/api
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.opsmesh.main:app --reload --port 8000

# In another terminal, start the frontend
cd apps/web
pnpm install
pnpm dev
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## API Overview

### Health Check
```bash
GET /health
# Response: { "status": "healthy", "service": "opsmesh-api" }
```

### Incidents (Coming Week 2)
```bash
GET  /api/v1/incidents           # List incidents
POST /api/v1/incidents           # Create incident
GET  /api/v1/incidents/{id}      # Get incident details
PUT  /api/v1/incidents/{id}      # Update incident
```

---

## Project Structure

```
opsmesh/
├── apps/
│   ├── web/                 # Next.js frontend
│   ├── api/                 # FastAPI backend
│   └── worker/              # Background job processor
├── packages/
│   ├── ui/                  # Shared UI components
│   ├── schemas/             # Shared types/contracts
│   └── prompts/             # AI prompts and policies
├── infra/
│   ├── docker/              # Docker configurations
│   └── github-actions/      # CI/CD workflows
├── docs/
│   ├── architecture/        # System design docs
│   ├── adr/                 # Architecture Decision Records
│   └── api/                 # API documentation
├── tests/
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── docker-compose.yml
└── README.md
```

---

## Testing

```bash
# API tests
cd apps/api
source .venv/bin/activate
pytest tests/ -v

# Frontend tests (coming soon)
cd apps/web
pnpm test
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Monorepo** | Shared types, atomic commits, unified CI |
| **FastAPI** | Async-first, auto-generated docs, Pydantic validation |
| **Next.js App Router** | Server components, streaming, modern patterns |
| **Redis for queues** | Simple, reliable, excellent Python support |
| **PostgreSQL** | ACID compliance, JSON support, scalability |

---

## Roadmap

| Week | Focus |
|------|-------|
| 1 | Foundation: repo setup, Docker, CI |
| 2 | Incident ingestion and dashboard |
| 3 | Worker pipeline and async processing |
| 4 | Clustering and deduplication |
| 5 | Severity scoring engine |
| 6 | AI response suggestions |
| 7 | Timeline and auditability |
| 8 | Auth and access control |
| 9 | Testing and reliability |
| 10 | Polish and observability |
| 11 | Deployment and demo |
| 12 | Launch and documentation |

---

## Contributing

This is a personal portfolio project, but suggestions and feedback are welcome! Please open an issue to discuss any changes.

---

## License

MIT

---

## Author

Built by [Your Name] — AI Systems / Platform Engineer

*Demonstrating production-grade backend engineering, event-driven architecture, and AI integration.*
