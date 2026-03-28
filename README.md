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
| **Auth** | JWT (access + refresh tokens), bcrypt, RBAC |
| **Observability** | OpenTelemetry, Prometheus/Grafana (planned) |
| **Infrastructure** | Docker, GitHub Actions |
| **Deployment** | Vercel (frontend), Railway/Render/Fly.io (backend) |

---

## Key Features

### v1 (Current Focus)
- [x] Incident ingestion API
- [x] Dashboard with incident list
- [x] Deduplication fingerprinting
- [x] Incident clustering (exact + fuzzy matching)
- [x] Severity scoring engine
- [x] Worker pipeline with RQ
- [x] Cluster API (list, detail, stats, resolve)
- [x] Dashboard tabs (Incidents / Clusters)
- [x] AI-generated response suggestions
- [x] Incident timeline
- [x] Search and filtering
- [x] JWT authentication (access + refresh tokens)
- [x] Role-based access control (admin/analyst/viewer)
- [x] Audit logging
- [x] Dockerized local development
- [x] Test suite (179 tests)
- [x] CI/CD pipeline

### v2 (Planned)
- [ ] Slack/email alerting
- [ ] Multi-tenant support
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
git clone https://github.com/saifhaque18/opsmesh.git
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

# In another terminal, start the worker (Week 3+)
cd apps/api
source .venv/bin/activate
python -m src.opsmesh.worker.run
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

### Incidents (requires auth)
```bash
GET    /api/v1/incidents               # List incidents (with filters)
POST   /api/v1/incidents               # Create incident (auto-queued)
GET    /api/v1/incidents/stats         # Dashboard statistics
GET    /api/v1/incidents/{id}          # Get incident details
PATCH  /api/v1/incidents/{id}          # Update incident (analyst+)
DELETE /api/v1/incidents/{id}          # Delete incident (analyst+)
```

### Pipeline (Week 3)
```bash
GET    /api/v1/incidents/pipeline/stats   # Queue depths & failed counts
GET    /api/v1/incidents/{id}/job         # Processing job status
POST   /api/v1/incidents/{id}/reprocess   # Re-queue for processing
```

### Clusters (Week 4)
```bash
GET    /api/v1/clusters                   # List clusters (with filters)
GET    /api/v1/clusters/stats             # Cluster statistics
GET    /api/v1/clusters/{id}              # Cluster detail with incidents
PATCH  /api/v1/clusters/{id}/resolve      # Mark cluster as resolved
```

### Authentication (Week 8)
```bash
POST   /api/v1/auth/register              # Create new user account
POST   /api/v1/auth/login                 # Authenticate and receive tokens
POST   /api/v1/auth/refresh               # Refresh access token
```

### Users (Week 8 - Admin only)
```bash
GET    /api/v1/users/me                   # Get current user profile
GET    /api/v1/users                      # List all users (admin)
PATCH  /api/v1/users/{id}                 # Update user (admin)
DELETE /api/v1/users/{id}                 # Deactivate user (admin)
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

Built by **Saiful Haque Saif** — AI Systems / Platform Engineer

*Demonstrating production-grade backend engineering, event-driven architecture, and AI integration.*
