"""People collection HTTP composition over People Access services."""

from fastapi import APIRouter

from app.modules.people_access.service import PeopleCollectionService
from app.modules.record.service import router_for


router = APIRouter()
router.include_router(router_for("users/roles", "roles", service=PeopleCollectionService("roles")))
router.include_router(router_for("users", "users", service=PeopleCollectionService("users")))
router.include_router(router_for("officers", "officers", service=PeopleCollectionService("officers")))
