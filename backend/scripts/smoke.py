import os
import sys

import httpx


def main() -> int:
    base = os.getenv("SMOKE_BASE_URL", "http://api:8000").rstrip("/")
    email = os.getenv("SMOKE_ADMIN_EMAIL") or os.getenv("ADMIN_EMAIL")
    password = os.getenv("SMOKE_ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD")
    host_header = os.getenv("SMOKE_HOST_HEADER", "localhost")
    if not email or not password:
        print("SMOKE_ADMIN_EMAIL and SMOKE_ADMIN_PASSWORD are required", file=sys.stderr)
        return 2
    with httpx.Client(base_url=base, timeout=20, headers={"Host": host_header}) as client:
        health = client.get("/health")
        ready = client.get("/ready")
        login = client.post("/api/v2/auth/login", json={"email": email, "password": password})
        me = client.get("/api/v2/auth/me")
        openapi = client.get("/api/v2/openapi.json")
    results = {
        "health": health.status_code,
        "ready": ready.status_code,
        "login": login.status_code,
        "me": me.status_code,
        "openapi": openapi.status_code,
        "paths": len(openapi.json().get("paths", {})) if openapi.is_success else 0,
    }
    print(results)
    return 0 if all(results[key] == 200 for key in ("health", "ready", "login", "me", "openapi")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
