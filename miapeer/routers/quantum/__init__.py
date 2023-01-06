from fastapi import APIRouter

from miapeer.routers.quantum import (
    portfolio,
    account,
    payee,
    transaction_type,
    category,
    transaction,
    scheduled_transaction,
)

router = APIRouter(
    prefix="/quantum/v1",
    responses={404: {"description": "Not found"}},
)

router.include_router(portfolio.router)
router.include_router(account.router)
router.include_router(payee.router)
router.include_router(transaction_type.router)
router.include_router(category.router)
router.include_router(transaction.router)
router.include_router(scheduled_transaction.router)
