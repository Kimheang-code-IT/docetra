# Docetra

A document management platform: rich-text authoring, file uploads, records,
organisation and people access, with a Nuxt frontend and a multi-process FastAPI
backend.

## Architecture

The backend deliberately runs as **separate processes**. User count does not
justify folding RabbitMQ work into the API process.

```text
1x api | 1x worker | 1x scheduler | 1x postgres | 1x redis | 1x rabbitmq | 1x minio
```

| Process | Role |
| --- | --- |
| `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` | HTTP API |
| `python -m app.main worker` | Outbox publisher, export completion, queue consumers |
| `python -m app.main scheduler` | UTC meeting reminders and reconcile ticks |
| `python -m app.main telegram` | Dedicated Telegram bot long-polling process |

HTTP handlers **publish** jobs (Drive sync, exports, notifications, scans);
workers consume them. The scheduler never delivers Telegram or email itself.

## Stack

| Area | Technology |
| --- | --- |
| API | FastAPI, SQLAlchemy 2, Alembic |
| Queue / cache | RabbitMQ, Redis |
| Scheduling | APScheduler |
| Storage | PostgreSQL, MinIO (S3-compatible) |
| Frontend | Nuxt, Vue 3, Nuxt UI, Tailwind CSS, Pinia |
| Authoring | TipTap rich-text editor |
| Uploads | Uppy |
| Tables / charts | TanStack Table, Apache ECharts |
| i18n | `@nuxtjs/i18n` |
| Tests | pytest, Vitest, Playwright |
| Security | gitleaks |

## Repository layout

```text
backend/            FastAPI API, worker, scheduler and Telegram processes
frontend/           Nuxt application
infrastructure/     Compose files, env templates, nginx config
docs/specification/ Product specification
.github/            Workflows and templates
AGENTS.md           Agent/contributor guidance for this codebase
```

Backend modules are organised as `admin_config`, `organization`, `people_access`,
`record` and `storage_integration`. The frontend adapters that call the API live in
`frontend/app/utils/constants/api-endpoints.ts`.

## Configuration

Tuned defaults for a small team are in `infrastructure/.env.example`:

| Setting | Small default | Notes |
| --- | --- | --- |
| `WORKER_CONCURRENCY` | `2` | Cap in-flight handlers |
| `WORKER_PREFETCH` | `2` | RabbitMQ QoS; keep low until lag appears |
| `SCHEDULER_*` | UTC, 15m reconcile / 1m reminders | Scheduler only publishes; workers execute |

## Tests

```powershell
python -m pytest -q                                      # unit + contract
python -m pytest tests/unit/modules -q                   # all modules
python -m pytest tests/unit/security -q                  # security helpers
python -m pytest tests/integration -m integration -q     # needs Docker API
```

See `backend/tests/README.md` for details.
