from fastapi import APIRouter

from miapeer.routers.quantum import (
    portfolio,
    account,
    payee,
)

router = APIRouter(
    prefix="/quantum/v1",
    responses={404: {"description": "Not found"}},
)

router.include_router(portfolio.router)
router.include_router(account.router)
router.include_router(payee.router)
