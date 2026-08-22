"""Officer collection — ``/api/v2/officers``."""

from app.api.v2.entities import router_for

router = router_for("officers", "officers")
