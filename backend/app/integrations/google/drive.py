"""Pure Google Drive API client.

No database access lives here: integrations never import business modules.
Orchestration of sync jobs belongs to ``app.modules.storage_integration``.
"""

from __future__ import annotations

import httpx


async def list_folder_files(token: str, folder_id: str) -> list[dict]:
    query = f"'{folder_id}' in parents and trashed = false"
    params = {
        "q": query,
        "pageSize": 1000,
        "fields": "files(id,name,mimeType,size,webViewLink,modifiedTime,createdTime,parents,md5Checksum)",
        "orderBy": "modifiedTime desc",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json().get("files") or []
