"""Sector classification — ``/api/v2/sector``."""

from app.api.v2.entities import router_for

router = router_for("sector", "sectors")
