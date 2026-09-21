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

## Continuous integration & delivery (GitHub Actions)

- **CI** (`.github/workflows/ci.yml`): gitleaks, backend lint/unit/contract (coverage floor 35%), frontend lint/typecheck/unit, live API integration (Docker), and the Alembic migration cycle.
- **CD** (`.github/workflows/cd.yml`) runs after `CI` succeeds:
  1. `promote` — fast-forward/merge the tested `dev` commit into `main`.
  2. `build` — build the backend (`backend/Dockerfile`) and frontend (`frontend/Dockerfile`) images and push to **GitHub Container Registry**.
  3. `deploy` — SSH to the server and **pull** the images for the tested commit. The server never builds.

> Deployments run for successful `main` **and** `dev` runs, always using the CI-tested `sha-<short>` image. (A `GITHUB_TOKEN` push — the `dev → main` promote — does not trigger workflows, so deploying the tested commit directly keeps production and `main` identical.) Add a `production` environment with required reviewers if you want an approval gate.

Image refs: `ghcr.io/<owner>/docetra-backend:<tag>` and `ghcr.io/<owner>/docetra-frontend:<tag>`, where `<tag>` is `sha-<short>`, the branch name, and `latest` (main only). `<owner>` is lowercase.

Deploy always uses the immutable `sha-<short>` tag for the tested commit.

### Server preparation (pull-only)

1. Install Docker + Compose v2; ensure the deploy user can run Docker (`usermod -aG docker <user>`), and open `HTTP_PORT` (default 8080) plus 80/443 if host nginx terminates TLS.
2. Clone the repo to the deploy path, e.g. `/opt/docetra`.
3. Create `infrastructure/.env.production` from `.env.example`, fill every `CHANGE_ME` / production checklist value, and set `BACKEND_ENV_FILE=.env.production`, `HTTP_PORT`, `NUXT_PUBLIC_SITE_URL`, and both image names:
   ```ini
   DOCETRA_BACKEND_IMAGE=ghcr.io/<owner>/docetra-backend:latest
   DOCETRA_FRONTEND_IMAGE=ghcr.io/<owner>/docetra-frontend:latest
   ```
   (The deploy overrides these with the per-release `sha-<short>` tag.)
4. Make the GHCR packages readable by the server: set them **public**, or store a PAT with `read:packages` in the `GHCR_TOKEN` / `GHCR_USER` secrets (CD logs in before pulling).
5. Create a dedicated deploy key and authorize it:
   ```bash
   ssh-keygen -t ed25519 -C "docetra-cd" -f docetra_cd
   # append docetra_cd.pub to the server user's ~/.ssh/authorized_keys
   ```

### GitHub repository secrets (Settings → Secrets and variables → Actions)

| Secret | Required | Purpose |
| --- | --- | --- |
| `DEPLOY_SSH_KEY` | yes | Private deploy key (contents of `docetra_cd`) |
| `DEPLOY_PATH` | yes | Absolute repo path on the server, e.g. `/opt/docetra` |
| `DEPLOY_USER` | no | SSH user on the server (defaults to `root`) |
| `DEPLOY_HOST` | no | Defaults to `167.71.244.107` |
| `DEPLOY_PORT` | no | SSH port (default `22`) |
| `DEPLOY_KNOWN_HOSTS` | no | Pinned host key line (recommended); otherwise `ssh-keyscan` is used |
| `DEPLOY_ENV_FILE` | no | Defaults to `infrastructure/.env.production` |
| `DEPLOY_HEALTH_URL` | no | Defaults to `http://127.0.0.1:8080/ready` |
| `GHCR_TOKEN` | if private packages | PAT with `read:packages` so the server can pull |
| `GHCR_USER` | if private packages | GitHub username for `GHCR_TOKEN` |

Repository **variable** `NUXT_PUBLIC_SITE_URL` (Settings → Variables) sets the SPA build arg (defaults to `https://docetra.minidev.in`). Optional: create a **`production` environment** with required reviewers so deploys wait for approval.

### What the deploy does

On the server: `git fetch` + `git checkout --force <sha>` → `docker compose pull api worker telegram nginx` → `docker compose up -d --no-build --remove-orphans` → `docker image prune -f` → readiness gate on `GET /ready`. It never runs `docker compose build`.

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
cp infrastructure/.env.example infrastructure/.env.production   # then fill in all values + image names
exit

# 4. Store the GitHub Actions secrets (run in the repo root)
gh secret set DEPLOY_PATH  --body "/opt/docetra"
gh secret set DEPLOY_SSH_KEY < docetra_cd
gh secret set DEPLOY_KNOWN_HOSTS < <(ssh-keyscan -H 167.71.244.107 2>/dev/null)  # optional, recommended
# If the GHCR packages are private:
gh secret set GHCR_USER --body "<github-user>"
gh secret set GHCR_TOKEN < ghcr_read_token.txt
```

Push to `dev` (auto-promoted to `main`) or run the **CD** workflow manually from the Actions tab. The `deploy` job runs only after CI passes.

## Security posture

- Loopback-only publication of data services; only api (and nginx) on the edge network.
- Containers: read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, tmpfs for /tmp, non-root user.
- Secrets only via env files (gitignored); CI runs gitleaks.
- HttpOnly + Secure + SameSite cookies; CSRF double-submit header; rate limiting on auth.

## Known deployment considerations

- Single-box RabbitMQ/Redis/MinIO are availability trade-offs acceptable at target scale (documented in compose comments).
- The frontend image is a static SPA baked into nginx (`frontend/Dockerfile`); there is no SSR/Node server. `SCHEDULER_IN_API=true` means the API is not horizontally scalable without duplicating scheduled jobs.
- Backup profile is manual/on-schedule, not built-in continuous backup.
