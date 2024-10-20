from fastapi import APIRouter

from miapeer.routers.quantum import (
    account,
    budget,
    category,
    payee,
    portfolio,
    repeat_option,
    scheduled_transaction,
    transaction,
    transaction_type,
)

router = APIRouter(
    prefix="/quantum/v1",
    responses={404: {"description": "Not found"}},
)

router.include_router(account.router)
router.include_router(budget.router)
router.include_router(category.router)
router.include_router(payee.router)
router.include_router(portfolio.router)
router.include_router(repeat_option.router)
router.include_router(scheduled_transaction.router)
router.include_router(transaction.router)
router.include_router(transaction_type.router)
