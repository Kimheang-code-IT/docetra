"""Purpose classification — ``/api/v2/purpose``."""

from app.api.v2.entities import router_for

router = router_for("purpose", "purposes")
