from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.budget import BudgetSet, BudgetOut

router = APIRouter(prefix="/budgets", tags=["budgets"])


async def _active_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(
        select(Category).where(Category.active.is_(True)).order_by(Category.sort_order)
    )
    return list(result.scalars().all())


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
    for cat in await _active_categories(db):
        if cat.id not in existing:
            b = Budget(user_id=current_user.id, category=cat.id, amount=cat.default_budget, month=target)
            db.add(b)
            existing[cat.id] = b

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
    if category not in {c.id for c in await _active_categories(db)}:
        raise HTTPException(status_code=400, detail=f"Categoría inválida: {category}")
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
