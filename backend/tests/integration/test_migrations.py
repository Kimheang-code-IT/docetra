"""Alembic schema lifecycle: single head, upgrade → downgrade → upgrade.

Runs against a throwaway database on the Postgres reachable via
``MIGRATION_DATABASE_URL`` so the live API database is never touched.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text

pytestmark = [pytest.mark.integration, pytest.mark.migration]

BACKEND_DIR = Path(__file__).resolve().parents[2]
BASE_URL = os.getenv("MIGRATION_DATABASE_URL", "")

CORE_TABLES = {
    "audit_log",
    "notification_audit_log",
    "outbox",
    "record",
    "record_type",
    "users",
}


def _scratch_url(base: str, name: str) -> str:
    return base.rsplit("/", 1)[0] + "/" + name


def _alembic(url: str, *args: str) -> str:
    env = {**os.environ, "DATABASE_URL": url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic {' '.join(args)} failed:\n{result.stderr}\n{result.stdout}"
    return result.stdout


def _tables(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def scratch_database():
    if not BASE_URL:
        pytest.skip("MIGRATION_DATABASE_URL not set")
    admin_url = _scratch_url(BASE_URL, "postgres")
    name = f"docetra_mig_{uuid.uuid4().hex[:8]}"
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = _scratch_url(BASE_URL, name)
    try:
        yield url
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def test_single_migration_head(scratch_database):
    output = _alembic(scratch_database, "heads")
    heads = [line for line in output.splitlines() if line.strip()]
    assert len(heads) == 1, output
    assert "0012_drop_favorites" in heads[0], output


def test_upgrade_downgrade_upgrade_cycle(scratch_database):
    _alembic(scratch_database, "upgrade", "head")
    upgraded = _tables(scratch_database)
    assert CORE_TABLES <= upgraded, sorted(CORE_TABLES - upgraded)

    current = _alembic(scratch_database, "current")
    assert "0012_drop_favorites" in current, current

    _alembic(scratch_database, "downgrade", "base")
    downgraded = _tables(scratch_database)
    assert not (CORE_TABLES & downgraded), sorted(CORE_TABLES & downgraded)

    _alembic(scratch_database, "upgrade", "head")
    assert CORE_TABLES <= _tables(scratch_database)
