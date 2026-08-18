import asyncio
import time
from collections import Counter

from fastapi import Request
from fastapi.responses import PlainTextResponse

_lock = asyncio.Lock()
_requests = Counter()
_duration = Counter()
_started = time.monotonic()


async def observe(request: Request, status: int, elapsed: float) -> None:
    route = request.scope.get("route")
    path = getattr(route, "path", "unmatched")
    key = (request.method, path, str(status))
    async with _lock:
        _requests[key] += 1
        _duration[key] += elapsed


async def prometheus_response() -> PlainTextResponse:
    async with _lock:
        request_rows = list(_requests.items())
        duration_rows = list(_duration.items())
    lines = [
        "# HELP docetra_uptime_seconds Process uptime in seconds.",
        "# TYPE docetra_uptime_seconds gauge",
        f"docetra_uptime_seconds {time.monotonic() - _started:.3f}",
        "# HELP docetra_http_requests_total HTTP requests by method, route and status.",
        "# TYPE docetra_http_requests_total counter",
    ]
    for (method, path, status), count in request_rows:
        lines.append(f'docetra_http_requests_total{{method="{method}",route="{path}",status="{status}"}} {count}')
    lines.extend(["# HELP docetra_http_request_duration_seconds_total Total request duration.", "# TYPE docetra_http_request_duration_seconds_total counter"])
    for (method, path, status), total in duration_rows:
        lines.append(f'docetra_http_request_duration_seconds_total{{method="{method}",route="{path}",status="{status}"}} {total:.6f}')
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
