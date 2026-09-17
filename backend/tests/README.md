# Backend tests

## Layout

```text
tests/
  unit/
    core/                 # JWT, production config, secrets
    shared/               # pagination, envelopes, validators
    security/             # require_permission, rate-limit helpers, catalog
    jobs/                 # outbox publisher, export consumer, scheduler jobs
    platform/             # audit trail + outbox model contracts
    modules/
      record/
      organization/
      people_access/
      storage_integration/
      admin_config/
      reporting_support/
  contract/               # OpenAPI paths vs frontend (no Docker)
  integration/            # live Docker API
    modules/              # per-module smoke
    test_modules_together.py
    test_migrations.py    # alembic cycle against a scratch Postgres
```

## Commands

From `backend/`:

```powershell
# Fast (default CI): unit + contract — skips integration
python -m pytest -q

# One module
python -m pytest tests/unit/modules/record -q

# Jobs, scheduler, and platform audit/outbox
python -m pytest tests/unit/jobs tests/unit/platform -q

# Security unit checks
python -m pytest tests/unit/security tests/unit/core/test_production_security.py -q

# Live API (Compose must be up)
python -m pytest tests/integration -m integration -q

# Alembic upgrade → downgrade → upgrade (scratch Postgres via MIGRATION_DATABASE_URL)
python -m pytest tests/integration/test_migrations.py -m migration -q

# Cross-module together + per-module integration
python -m pytest tests/integration/modules tests/integration/test_modules_together.py -m integration -q
```

Start the stack from repo root:

```powershell
docker compose -f infrastructure/docker-compose.yml up --build -d
```

## Markers

| Marker | Meaning |
|--------|---------|
| *(none / default)* | Unit + contract (`addopts = -m 'not integration'`) |
| `integration` | Needs running API at `DOCETRA_API_BASE` (default `http://127.0.0.1:8000`) |
| `migration` | Alembic upgrade/downgrade cycle against `MIGRATION_DATABASE_URL` (scratch DB) |
