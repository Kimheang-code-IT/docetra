"""Unauthenticated access must fail closed on protected collections."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

PROTECTED_LISTS = [
    "/api/v2/records/document",
    "/api/v2/records/meeting_history",
    "/api/v2/organizations/department",
    "/api/v2/users",
    "/api/v2/settings/storage",
    "/api/v2/dashboard/summary",
]


@pytest.mark.parametrize("path", PROTECTED_LISTS)
def test_protected_list_requires_auth(api_client, path):
    response = api_client.get(path)
    assert response.status_code == 401, f"{path} → {response.status_code} {response.text}"


def test_settings_patch_requires_auth(api_client):
    response = api_client.patch("/api/v2/settings/app-info", json={"shortName": "NoAuth"})
    # CSRF may fire first (403) or auth (401) — either means rejected.
    assert response.status_code in {401, 403}, response.text
