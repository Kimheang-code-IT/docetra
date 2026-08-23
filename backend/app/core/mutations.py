"""Merge optimistic concurrency tokens from JSON, If-Match, and query."""

from __future__ import annotations

from fastapi import Request
from pydantic import BaseModel

from app.core.concurrency import header_match, parse_version_token


def request_mutation_body(request: Request, body: BaseModel | dict | None = None) -> dict:
    if body is None:
        data: dict = {}
    elif isinstance(body, BaseModel):
        data = body.model_dump(exclude_unset=True)
    else:
        data = dict(body)
    token = parse_version_token(
        data.get("version"),
        header_match(request.headers),
        request.query_params.get("version"),
    )
    if token is not None:
        data["version"] = token
    return data
