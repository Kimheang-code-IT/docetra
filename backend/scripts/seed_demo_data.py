"""Seed complete demo/test data through the public API.

Creates realistic data for every frontend page so the UI can be exercised
end to end. Idempotent: entities are titled with a "Demo " prefix and the
script skips anything that already exists.

Usage:
    DOCETRA_API_BASE=http://127.0.0.1:8001 \\
    ADMIN_EMAIL=admin@docetra.test ADMIN_PASSWORD=Docetra-Admin-2025 \\
    python scripts/seed_demo_data.py
"""

from __future__ import annotations

import io
import os
import sys
import time

import httpx

BASE = os.getenv("DOCETRA_API_BASE", "http://127.0.0.1:8001").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@docetra.test")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Docetra-Admin-2025")

TODAY = "2026-02-10"
DT = "2026-02-10T09:00:00Z"

client = httpx.Client(base_url=BASE, timeout=60.0, follow_redirects=True)
created = {"ok": 0, "skip": 0, "fail": 0}


def login() -> None:
    for attempt in range(6):
        r = client.post("/api/v2/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        if r.status_code == 200:
            return
        time.sleep(min(2 ** attempt, 10))
    raise SystemExit(f"login failed: {r.status_code} {r.text[:200]}")


def csrf() -> dict:
    token = client.cookies.get("XSRF-TOKEN")
    return {"X-CSRF-Token": token or ""}


def find(resource: str, title: str, id_field: str = "id") -> str | None:
    r = client.get(f"/api/v2/{resource}", params={"q": title, "limit": 20})
    if r.status_code != 200:
        return None
    for row in r.json().get("data") or []:
        if row.get("title") == title or row.get("name") == title:
            return row.get(id_field)
    return None


def create(resource: str, payload: dict, label: str, find_title: str | None = None) -> dict:
    if find_title and (existing := find(resource, find_title)):
        created["skip"] += 1
        return {"id": existing}
    r = client.post(f"/api/v2/{resource}", json=payload, headers=csrf())
    if r.status_code in (200, 201):
        created["ok"] += 1
        return r.json()["data"]
    created["fail"] += 1
    print(f"  !! {label}: {r.status_code} {r.text[:180]}")
    return {}


def main() -> None:
    login()
    print(f"logged in as {ADMIN_EMAIL} @ {BASE}")
    H = csrf()

    # ------------------------------------------------------------------
    # Organization: sectors (incl. sub-sector), purposes
    # ------------------------------------------------------------------
    print("sectors + purposes")
    sectors = {}
    for name in ("Demo Agriculture", "Demo Construction", "Demo Information Technology"):
        row = create("sector", {"name": name, "isActive": True}, f"sector {name}", name)
        if row:
            sectors[name] = row["id"]
    if "Demo Information Technology" in sectors:
        create("sector", {"name": "Demo Software", "parentId": sectors["Demo Information Technology"], "isActive": True},
               "sub-sector", "Demo Software")
    purposes = {}
    for name in ("Demo Partnership", "Demo Procurement", "Demo Regulation"):
        row = create("purpose", {"name": name, "isActive": True}, f"purpose {name}", name)
        if row:
            purposes[name] = row["id"]

    # Departments: main + sub-departments
    print("departments (hierarchy)")
    admin = create("organizations/department",
                   {"name": "Demo Administration Dept", "isActive": True, "description": "Main demo department"},
                   "main department", "Demo Administration Dept")
    create("organizations/department",
           {"name": "Demo Finance Dept", "parentId": admin.get("id"), "isActive": True},
           "sub department", "Demo Finance Dept")
    create("organizations/department",
           {"name": "Demo IT Dept", "parentId": admin.get("id"), "isActive": True},
           "sub department", "Demo IT Dept")
    create("organizations/department", {"name": "Demo Planning Dept", "isActive": True},
           "main department", "Demo Planning Dept")

    # Companies with sector + purpose
    print("companies")
    for name, sector, purpose in (
        ("Demo Alpha Co Ltd", "Demo Agriculture", "Demo Partnership"),
        ("Demo Beta Group", "Demo Construction", "Demo Procurement"),
        ("Demo Gamma Corp", "Demo Information Technology", "Demo Regulation"),
    ):
        create("organizations/company",
               {"name": name, "sectorId": sectors.get(sector), "purposeId": purposes.get(purpose), "isActive": True,
                "taxId": f"DEMO-{abs(hash(name)) % 999999:06d}"},
               f"company {name}", name)

    # ------------------------------------------------------------------
    # People: officers, roles, users
    # ------------------------------------------------------------------
    print("officers")
    roles_list = client.get("/api/v2/users/roles", params={"limit": 5}).json().get("data") or []
    any_role_id = roles_list[0]["id"] if roles_list else None
    officers = {}
    for name, org in (
        ("Demo Officer Alice", "Demo Administration Dept"),
        ("Demo Officer Bob", "Demo Finance Dept"),
        ("Demo Officer Chan", "Demo IT Dept"),
        ("Demo Officer Dara", "Demo Planning Dept"),
        ("Demo Partner Eang", "Demo Alpha Co Ltd"),
        ("Demo Partner Fa", "Demo Beta Group"),
    ):
        r = client.get("/api/v2/officers", params={"q": name, "limit": 5})
        existing = next((x for x in (r.json().get("data") or []) if x.get("name") == name), None)
        if existing:
            officers[name] = existing["id"]
            created["skip"] += 1
            continue
        r = client.get("/api/v2/organizations/department" if "Dept" in org else "/api/v2/organizations/company",
                       params={"q": org, "limit": 5})
        org_row = next((x for x in (r.json().get("data") or []) if x.get("name") == org), {})
        res = client.post("/api/v2/officers", json={"name": name, "organizationId": org_row.get("id"),
                                                    "roleId": any_role_id, "isActive": True}, headers=H)
        if res.status_code in (200, 201):
            officers[name] = res.json()["data"]["id"]
            created["ok"] += 1
        else:
            created["fail"] += 1
            print(f"  !! officer {name}: {res.status_code} {res.text[:150]}")

    print("roles + users")
    catalog = client.get("/api/v2/users/permission-catalog").json().get("data") or []
    def codes_for(prefixes: list[str], actions: list[str] | None = None) -> list[dict]:
        grouped: dict[str, set[str]] = {}
        for item in catalog:
            code = item.get("permissionPrefix") or item.get("code") or ""
            if any(code.startswith(p) for p in prefixes):
                doc = item.get("documentType") or ""
                if not doc:
                    continue
                for action in (item.get("actions") or []):
                    if actions is None or action in actions:
                        grouped.setdefault(doc, set()).add(action)
        return [{"documentType": doc, "actions": sorted(acts)} for doc, acts in sorted(grouped.items())]

    editor = create("users/roles",
                    {"code": "demo_editor", "name": "Demo Editor", "description": "Demo role: edit records",
                     "status": "active",
                     "permissionRows": codes_for(["records.", "dashboard", "archive"],
                                                 ["view", "create", "edit", "comment", "export", "transition", "assign", "archive", "restore"])},
                    "editor role", "Demo Editor")
    viewer = create("users/roles",
                    {"code": "demo_viewer", "name": "Demo Viewer", "description": "Demo role: read-only",
                     "status": "active",
                     "permissionRows": codes_for(["records.", "dashboard", "archive"], ["view"])},
                    "viewer role", "Demo Viewer")

    # If the roles already existed, refresh their permission rows (create()
    # skipped them) so member users get the synced permission set.
    for role_row, payload_rows in ((editor, None), (viewer, None)):
        if not role_row or not role_row.get("id"):
            continue
        detail = client.get(f"/api/v2/users/roles/{role_row['id']}")
        if detail.status_code != 200:
            continue
        current = detail.json()["data"]
        if current.get("permissionRows"):
            continue  # already populated
        res = client.put(f"/api/v2/users/roles/{role_row['id']}",
                         json={"name": current.get("name"), "description": current.get("description"),
                               "status": current.get("status", "active"), "permissions": None,
                               "permissionRows": codes_for(["records.", "dashboard", "archive"],
                                                           ["view"] if current.get("name") == "Demo Viewer"
                                                           else ["view", "create", "edit", "comment", "export",
                                                                 "transition", "assign", "archive", "restore"])},
                         headers={**H, "If-Match": str(current.get("version"))})
        if res.status_code in (200, 201):
            created["ok"] += 1
        else:
            created["fail"] += 1
            print(f"  !! role refresh {current.get('name')}: {res.status_code} {res.text[:150]}")

    for email, name, role, pw in (
        ("editor@docetra.test", "Demo Editor User", editor, "Docetra-Editor-2025"),
        ("viewer@docetra.test", "Demo Viewer User", viewer, "Docetra-Viewer-2025"),
    ):
        if email and role and not find("users", name):
            res = client.post("/api/v2/users",
                              json={"name": name, "email": email, "roleId": role["id"], "password": pw,
                                    "status": "active"}, headers=H)
            if res.status_code in (200, 201):
                created["ok"] += 1
            else:
                created["fail"] += 1
                print(f"  !! user {email}: {res.status_code} {res.text[:150]}")
        else:
            created["skip"] += 1

    # ------------------------------------------------------------------
    # Configuration: attribute catalog + a custom record type
    # ------------------------------------------------------------------
    print("attribute catalog")
    attrs = {}
    for code, name, ftype, extra in (
        ("demo_priority", "Demo Priority", "select", {"options": [
            {"value": "high", "label": "High"}, {"value": "medium", "label": "Medium"}, {"value": "low", "label": "Low"}]}),
        ("demo_budget", "Demo Budget", "number", {}),
        ("demo_deadline", "Demo Deadline", "date", {}),
        ("demo_remarks", "Demo Remarks", "textarea", {}),
    ):
        if not find("configuration/record-attributes", name):
            res = client.post("/api/v2/configuration/record-attributes",
                              json={"code": code, "name": name, "fieldType": ftype, **extra}, headers=H)
            if res.status_code in (200, 201):
                attrs[code] = res.json()["data"]["id"]
                created["ok"] += 1
            else:
                created["fail"] += 1
                print(f"  !! attribute {code}: {res.status_code} {res.text[:150]}")
        else:
            created["skip"] += 1

    # ------------------------------------------------------------------
    # Meetings: topics + meetings across stages
    # ------------------------------------------------------------------
    print("meeting topics + meetings")
    topics = {}
    for title in ("Demo Q1 Planning", "Demo Budget Review", "Demo Team Sync"):
        row = create("records/meeting_topic",
                     {"title": title, "description": f"Demo topic {title}", "recordTime": DT, "status": "active"},
                     f"topic {title}", title)
        if row:
            topics[title] = row["id"]
    archived_topic = create("records/meeting_topic",
                            {"title": "Demo Old Topic", "recordTime": DT, "status": "active"},
                            "archived topic", "Demo Old Topic")
    if archived_topic:
        r = client.get(f"/api/v2/records/meeting_topic/{archived_topic['id']}")
        ver = r.json()["data"]["version"]
        client.post(f"/api/v2/records/meeting_topic/{archived_topic['id']}/archive",
                    json={"expected": ver}, headers=H)

    def meeting(title, stage, topic=None, order=None, completed=False, letter=None, mode="offline"):
        payload = {
            "title": title, "letterNumber": letter or f"DEMO-MTG-{abs(hash(title)) % 999:03d}",
            "letterDate": TODAY, "meetingDate": DT, "meetingMode": mode,
            "location": "Demo meeting room", "durationMinutes": 60,
            "participants": list(officers)[:2], "internalUnits": [],
            "externalUnits": [], "tags": ["demo"], "status": "active", "recordTime": DT,
        }
        if stage:
            payload["stage"] = stage
        if topic:
            payload.update({"topicId": topic, "topicTitle": next((k for k, v in topics.items() if v == topic), ""),
                            "sortOrder": order or 0})
        row = create("records/meeting_history", payload, f"meeting {title}", title)
        return row

    t1, t2, t3 = (topics.get(k) for k in ("Demo Q1 Planning", "Demo Budget Review", "Demo Team Sync"))
    if t1:
        meeting("Demo Kickoff Meeting", "intake", topic=t1, order=0)
        meeting("Demo Scope Review", "review", topic=t1, order=1)
    if t2:
        meeting("Demo Budget Session", "approval", topic=t2, order=0)
        meeting("Demo Finance Follow-up", "intake", topic=t2, order=1)
    if t3:
        meeting("Demo Weekly Sync", "intake", topic=t3, order=0, mode="online")
        meeting("Demo Retrospective", "review", topic=t3, order=1)
    meeting("Demo Unassigned Meeting A", "intake")
    meeting("Demo Unassigned Meeting B", "review", mode="hybrid")
    meeting("Demo Completed Meeting January", "completed", completed=True)
    meeting("Demo Completed Meeting February", "completed", completed=True)

    # ------------------------------------------------------------------
    # Documents: incoming / outgoing / combined / master list
    # ------------------------------------------------------------------
    print("documents")
    DOC_STAGES = ["created", "record_created", "waiting_related_document",
                  "submitted_director", "reply", "finished_final"]

    def document(resource, title, stage, extra=None, letter=None):
        payload = {
            "title": title, "letterNumber": letter or f"DEMO-{abs(hash(title)) % 99999:05d}",
            "documentType": "Demo Letter", "recordTime": DT, "status": "active",
            "stage": stage, "tags": ["demo"],
        }
        payload.update(extra or {})
        return create(f"records/{resource}", payload, f"{resource} {title}", title)

    org_alpha, dept_admin = None, None
    r = client.get("/api/v2/organizations/company", params={"q": "Demo Alpha", "limit": 5})
    org_alpha = (r.json().get("data") or [{}])[0].get("id")
    r = client.get("/api/v2/organizations/department", params={"q": "Demo Administration", "limit": 5})
    dept_admin = (r.json().get("data") or [{}])[0].get("id")

    incoming = []
    for i, stage in enumerate(DOC_STAGES):
        row = document("incoming_document", f"Demo Incoming {chr(65+i)} Report", stage,
                       {"senderOrganization": org_alpha, "officeInCharge": dept_admin,
                        "involvedOfficers": list(officers.values())[:2],
                        "receivedDate": TODAY, "waiting": stage == "waiting_related_document"})
        if row:
            incoming.append(row["id"])

    for i, stage in enumerate(DOC_STAGES[:5]):
        document("outgoing_document", f"Demo Outgoing {chr(65+i)} Notice", stage,
                 {"recipientOrganization": org_alpha, "sentDate": TODAY})

    for i in range(4):
        document("document", f"Demo General Document {chr(65+i)}", DOC_STAGES[i], {"documentDate": TODAY})

    for i in range(3):
        document("master_list_request", f"Demo Master List Request {chr(65+i)}", "created",
                 {"letterDate": TODAY})

    # ------------------------------------------------------------------
    # Attachments: real bytes upload + URL attachment
    # ------------------------------------------------------------------
    print("attachments")
    if incoming:
        target = incoming[0]
        def upload(name, content, mime):
            ver = client.get(f"/api/v2/records/incoming_document/{target}").json()["data"]["version"]
            r = client.post(f"/api/v2/records/incoming_document/{target}/attachments/upload",
                            files={"file": (name, io.BytesIO(content), mime)},
                            headers={**H, "If-Match": str(ver)})
            if r.status_code in (200, 201):
                created["ok"] += 1
            else:
                created["fail"] += 1
                print(f"  !! attachment upload {name}: {r.status_code} {r.text[:150]}")

        pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<<>>\n%%EOF"
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
            "1f15c4890000000d4944415478da63fcffff3f0300050201f34a24d50000000049454e44ae426082")
        upload("demo-report.pdf", pdf, "application/pdf")
        upload("demo-chart.png", png, "image/png")

    # ------------------------------------------------------------------
    # Comments on a couple of records
    # ------------------------------------------------------------------
    print("comments")
    if incoming:
        for body in ("Demo comment: please review section 2.", "Demo comment: waiting for signature."):
            r = client.post(f"/api/v2/records/incoming_document/{incoming[0]}/comments",
                            json={"body": body}, headers=H)
            if r.status_code in (200, 201):
                created["ok"] += 1
            else:
                created["fail"] += 1
                print(f"  !! comment: {r.status_code} {r.text[:120]}")

    # ------------------------------------------------------------------
    # Archive: archive one record of a couple of types
    # ------------------------------------------------------------------
    print("archive samples")
    for resource, title in (("records/incoming_document", "Demo Incoming F Report"),
                            ("records/outgoing_document", "Demo Outgoing E Notice"),
                            ("records/meeting_history", "Demo Unassigned Meeting B")):
        rid = find(resource, title)
        if not rid:
            created["skip"] += 1
            continue
        detail = client.get(f"/api/v2/{resource}/{rid}")
        if detail.status_code != 200:
            created["fail"] += 1
            print(f"  !! fetch {title}: {detail.status_code} {detail.text[:150]}")
            continue
        ver = detail.json()["data"]["version"]
        r = client.post(f"/api/v2/{resource}/{rid}/archive", json={"expected": ver}, headers={**H, "If-Match": str(ver)})
        if r.status_code in (200, 201):
            created["ok"] += 1
        else:
            created["fail"] += 1
            print(f"  !! archive {title}: {r.status_code} {r.text[:120]}")

    # ------------------------------------------------------------------
    # Portal: file upload metadata + Drive sources
    # ------------------------------------------------------------------
    print("portal")
    for name in ("Demo Manual v1.pdf", "Demo Budget Sheet.xlsx", "Demo Photo.png"):
        if not find("portal/file-uploads", name):
            res = client.post("/api/v2/portal/file-uploads",
                              json={"name": name, "mimeType": "application/pdf",
                                    "sizeBytes": 1024 * 42, "storageSource": "minio",
                                    "status": "active"}, headers=H)
            if res.status_code in (200, 201):
                created["ok"] += 1
            else:
                created["fail"] += 1
                print(f"  !! file upload {name}: {res.status_code} {res.text[:150]}")
        else:
            created["skip"] += 1

    for folder in ("Demo Drive Folder A", "Demo Drive Folder B"):
        if not find("portal/google-drive-sync", folder):
            res = client.post("/api/v2/portal/google-drive-sync/sources",
                              json={"name": folder, "folderName": folder, "folderId": "demo-folder-id",
                                    "status": "active"}, headers=H)
            if res.status_code in (200, 201):
                created["ok"] += 1
            else:
                created["fail"] += 1
                print(f"  !! drive source {folder}: {res.status_code} {res.text[:150]}")
        else:
            created["skip"] += 1

    # Portal logs feed on the generic entity lifecycle audit trail — archive
    # and restore one Drive source so /portal/portal-logs has rows.
    if (sid := find("portal/google-drive-sync", "Demo Drive Folder B")):
        detail = client.get(f"/api/v2/portal/google-drive-sync/{sid}")
        ver = detail.json().get("data", {}).get("version")
        if ver is not None:
            a = client.post(f"/api/v2/portal/google-drive-sync/{sid}/archive",
                            json={"expected": ver}, headers={**H, "If-Match": str(ver)})
            ver2 = client.get(f"/api/v2/portal/google-drive-sync/{sid}").json().get("data", {}).get("version")
            r2 = client.post(f"/api/v2/portal/google-drive-sync/{sid}/restore",
                             json={"expected": ver2}, headers={**H, "If-Match": str(ver2 or ver)})
            if a.status_code in (200, 201) and r2.status_code in (200, 201):
                created["ok"] += 2
            else:
                created["fail"] += 1
                print(f"  !! portal log seed: {a.status_code} {a.text[:120]}")

    print(f"\nDONE  created={created['ok']}  skipped(existing)={created['skip']}  failed={created['fail']}")
    return 0 if created["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
