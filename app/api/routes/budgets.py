from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.budget import Budget
from app.schemas.budget import BudgetSet, BudgetOut

router = APIRouter(prefix="/budgets", tags=["budgets"])

CATEGORIES = ["despensa", "salidas", "gasolina", "salud", "suscripciones", "ropa", "otros"]
DEFAULT_AMOUNTS = {
    "despensa": 3000, "salidas": 2000, "gasolina": 1500, "salud": 1000,
    "suscripciones": 500, "ropa": 2000, "otros": 1000,
}


@router.get("", response_model=list[BudgetOut])
async def get_budgets(
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = month or date.today().strftime("%Y-%m")
    result = await db.execute(
        select(Budget).where(Budget.user_id == current_user.id, Budget.month == target)
    )
    existing = {b.category: b for b in result.scalars().all()}

    # Crear entradas por defecto para categorías sin presupuesto
    for cat in CATEGORIES:
        if cat not in existing:
            b = Budget(user_id=current_user.id, category=cat, amount=DEFAULT_AMOUNTS[cat], month=target)
            db.add(b)
            existing[cat] = b

    if any(b.id is None for b in existing.values()):
        await db.commit()
        for b in existing.values():
            if b.id is None:
                await db.refresh(b)

    return list(existing.values())


@router.put("/{category}", response_model=BudgetOut)
async def set_budget(
    category: str,
    body: BudgetSet,
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = month or date.today().strftime("%Y-%m")
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.category == category,
            Budget.month == target,
        )
    )
    budget = result.scalar_one_or_none()
    if budget:
        budget.amount = body.amount
    else:
        budget = Budget(user_id=current_user.id, category=category, amount=body.amount, month=target)
        db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget
