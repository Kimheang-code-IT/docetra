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
- The worker starts separately on the private network only. APScheduler runs inside the API by default (`SCHEDULER_IN_API=true`); set it to `false` and run `python -m app.main scheduler` separately when using multiple API workers/instances.

## Frontend deploy

The SPA is built and served by the `nginx` Compose service (no Node runtime container):

```bash
cd infrastructure
docker compose up -d --build nginx   # builds frontend (NUXT_STATIC_SPA=true) into an nginx image
# browse http://localhost:8080 — nginx serves the SPA and proxies /api → api:8000
```

For a bare build outside Docker: `cd frontend && NUXT_STATIC_SPA=true pnpm generate`, then serve `frontend/.output/public` with nginx (history fallback to `200.html`).

Runtime config: same-origin `/api/v2` is the default (nginx proxies it). Set `NUXT_PUBLIC_SITE_URL` (build arg) for canonical/OG URLs; cookie sessions are the default `authMode`.

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

## Continuous deployment (GitHub Actions)

`.github/workflows/cd.yml` deploys automatically after the **CI workflow** (`.github/workflows/ci.yml`) passes (unit, contract, integration, migrations).

- **Triggers**: the `CD` workflow runs when `CI` completes successfully on `dev` or `main` (`workflow_run`), or manual **Run workflow** (`workflow_dispatch`). Pull requests never deploy. On `dev`, the tested commit is first merged into `main` by the `promote` job.
- **Deploys the exact tested commit** (`workflow_run.head_sha`) over SSH — `git fetch` + `git checkout --force <sha>`, then `docker compose build` / `up -d --remove-orphans`, image prune, and a readiness gate on `GET /ready`.
- If `DEPLOY_SSH_KEY` is unset the deploy step is skipped with a warning, so CI stays green until you configure CD.

### Server preparation (167.71.244.107)

1. Install Docker + Compose v2; ensure the deploy user can run Docker (`usermod -aG docker <user>`).
2. Clone the repo to the deploy path, e.g. `/opt/docetra`.
3. Create `infrastructure/.env.production` from `.env.example` and fill in every `CHANGE_ME` / production checklist value, including `HTTP_PORT` and `BACKEND_ENV_FILE=.env.production`.
4. Create a dedicated deploy key and authorize it:
   ```bash
   ssh-keygen -t ed25519 -C "docetra-cd" -f docetra_cd
   # append docetra_cd.pub to the server user's ~/.ssh/authorized_keys
   ```
5. Open the firewall for the app port (`HTTP_PORT`, default 8080) and, if a host nginx terminates TLS, 80/443.

### GitHub repository secrets (Settings → Secrets and variables → Actions)

| Secret | Required | Purpose |
| --- | --- | --- |
| `DEPLOY_USER` | no | SSH user on the server (defaults to `root`) |
| `DEPLOY_SSH_KEY` | yes | Private deploy key (contents of `docetra_cd`) |
| `DEPLOY_PATH` | yes | Absolute repo path on the server, e.g. `/opt/docetra` |
| `DEPLOY_HOST` | no | Defaults to `167.71.244.107` |
| `DEPLOY_PORT` | no | SSH port (default `22`) |
| `DEPLOY_KNOWN_HOSTS` | no | Pinned host key line (recommended); otherwise `ssh-keyscan` is used |
| `DEPLOY_ENV_FILE` | no | Defaults to `infrastructure/.env.production` |
| `DEPLOY_HEALTH_URL` | no | Defaults to `http://127.0.0.1:8080/ready` |

Optional: create a **`production` environment** (Settings → Environments) with required reviewers so deploys wait for approval.

### Quick setup

```bash
# 1. On your machine: create a deploy key pair
ssh-keygen -t ed25519 -C "docetra-cd" -f docetra_cd

# 2. Authorize the public key on the server
ssh-copy-id -i docetra_cd.pub root@167.71.244.107

# 3. Prepare the server (Docker + repo + production env)
ssh root@167.71.244.107
sudo usermod -aG docker "$USER" && newgrp docker
sudo git clone <repo-url> /opt/docetra && cd /opt/docetra
cp infrastructure/.env.example infrastructure/.env.production   # then fill in all values
exit

# 4. Store the GitHub Actions secrets (run in the repo root)
gh secret set DEPLOY_USER  --body "root"                     # optional (this is the default)
gh secret set DEPLOY_PATH  --body "/opt/docetra"
gh secret set DEPLOY_SSH_KEY < docetra_cd
gh secret set DEPLOY_HOST  --body "167.71.244.107"           # optional (this is the default)
gh secret set DEPLOY_KNOWN_HOSTS < <(ssh-keyscan -H 167.71.244.107 2>/dev/null)  # optional, recommended
```

Push to `dev` (or `main`), or run the **CD** workflow manually from the Actions tab. The `deploy` job runs only after CI passes.

## Security posture

- Loopback-only publication of data services; only api (and nginx) on the edge network.
- Containers: read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, tmpfs for /tmp, non-root user.
- Secrets only via env files (gitignored); CI runs gitleaks.
- HttpOnly + Secure + SameSite cookies; CSRF double-submit header; rate limiting on auth.

## Known deployment considerations

- Single-box RabbitMQ/Redis/MinIO are availability trade-offs acceptable at target scale (documented in compose comments).
- The frontend image is a static SPA baked into nginx (`frontend/Dockerfile`); there is no SSR/Node server. `SCHEDULER_IN_API=true` means the API is not horizontally scalable without duplicating scheduled jobs.
- Backup profile is manual/on-schedule, not built-in continuous backup.
