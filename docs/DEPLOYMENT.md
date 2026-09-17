# Docetra — Deployment

## Prerequisites

- Docker + Compose v2 (single box for small teams; ~20 users sizing).
- Domain + TLS certificate (nginx) for production.
- `.env.production` built from `.env.example` with real secrets.

## Production deploy (backend stack)

```bash
cd infrastructure
cp .env.example .env.production    # fill in all secrets — never commit
# required: POSTGRES_PASSWORD, RABBITMQ_PASSWORD, MINIO_ROOT_PASSWORD,
#           SESSION_SECRET, JWT_SECRET, PASSWORD_RESET_SECRET, SETTINGS_ENCRYPTION_KEY,
#           SESSION_COOKIE_SECURE=true, S3_*, SMTP_*, GOOGLE_DRIVE_* (if used)
docker compose --env-file .env.production -f docker-compose.yml up -d --build
```

- API container runs `alembic upgrade head` on start (schema at head `0012`).
- Health: `GET /health` (liveness), `GET /ready` (readiness: DB/Redis/broker).
- Worker + scheduler start separately and attach to the private network only.

## Frontend deploy

```bash
cd frontend
pnpm install
pnpm build          # static/hosted Nuxt build
# serve via nginx (infrastructure/nginx/docetra.conf.example) pointing /api → api:8000
```

Runtime config: `NUXT_PUBLIC_API_BASE` (or equivalent `runtimeConfig.public`) must point at the API origin; `authMode` defaults to cookie sessions.

## First-run bootstrap

1. Register the first admin (`POST /auth/register` — bootstrap rules apply).
2. Login seeds/refreshes permission catalog; menus derive from record surfaces (`GET /records/_meta/surfaces`).
3. Settings → Storage: create/test/set-default the storage provider (MinIO or S3).
4. Settings → App Info/Config: branding, SMTP (test-connection → send-test), Telegram bots (optional).
5. Configuration: record types/attributes as needed (built-ins auto-seed).

## Backups & maintenance

- `infrastructure/scripts/backup.sh|.ps1` — runs the `operations` profile: `pg_dump` (custom format) + `mc mirror` of the S3 bucket into the `backend_backups` volume. Schedule via cron/Task Scheduler.
- Restore: `pg_restore` into a fresh postgres volume; `mc mirror --reverse` for objects.
- Log rotation: nginx access/error + container logs (docker logging driver).
- `GET /metrics` for Prometheus-style scraping; `GET /health` for load-balancer probes.

## Upgrades

1. Pull new image / rebuild.
2. `docker compose ... up -d` — migrations run automatically on API start (additive-only policy).
3. Verify `GET /ready`, login smoke test, dashboard load.

## Security posture

- Loopback-only publication of data services; only api (and nginx) on the edge network.
- Containers: read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, tmpfs for /tmp, non-root user.
- Secrets only via env files (gitignored); CI runs gitleaks.
- HttpOnly + Secure + SameSite cookies; CSRF double-submit header; rate limiting on auth.

## Known deployment considerations

- Single-box RabbitMQ/Redis/MinIO are availability trade-offs acceptable at target scale (documented in compose comments).
- No frontend container image exists (static build); document or add one if containerized delivery is required — see GAP_ANALYSIS.
- Backup profile is manual/on-schedule, not built-in continuous backup.
