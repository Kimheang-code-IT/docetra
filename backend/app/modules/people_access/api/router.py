"""people_access HTTP — auth, users/roles, officers."""

from fastapi import APIRouter

from app.modules.people_access.api import auth, officers, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(officers.router)
