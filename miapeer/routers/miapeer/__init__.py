from fastapi import APIRouter

from miapeer.routers.miapeer import (
    application,
    application_role,
    permission,
    role,
    user,
)

router = APIRouter(
    prefix="/miapeer/v1",
    responses={404: {"description": "Not found"}},
)

router.include_router(application.router)
router.include_router(role.router)
router.include_router(application_role.router)
router.include_router(user.router)
router.include_router(permission.router)
