"""Sole registration aggregator for SQLAlchemy mapped classes.

Every mapped class has exactly one canonical owner module. This package imports
the owner modules so ``Base.metadata`` is fully populated for Alembic and for
runtime use. It must contain no business behavior and no model definitions.
"""

from app.db.base import Base

# Canonical model owners (imports populate Base.metadata; never re-exported here).
from app.modules.admin_config import model as _admin_config_model  # noqa: F401
from app.modules.organization import model as _organization_model  # noqa: F401
from app.modules.people_access import model as _people_access_model  # noqa: F401
from app.modules.record import model as _record_model  # noqa: F401
from app.modules.storage_integration import model as _storage_integration_model  # noqa: F401
from app.platform.audit import model as _platform_audit_model  # noqa: F401
from app.platform.messaging import model as _platform_messaging_model  # noqa: F401

__all__ = ["Base"]
