from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.schemas.goal import GoalSet, GoalOut

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=GoalOut | None)
async def get_goal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Goal).where(Goal.user_id == current_user.id))
    return result.scalar_one_or_none()


@router.put("", response_model=GoalOut)
async def set_goal(
    body: GoalSet,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Goal).where(Goal.user_id == current_user.id))
    goal = result.scalar_one_or_none()
    if goal:
        goal.description = body.description
    else:
        goal = Goal(user_id=current_user.id, description=body.description)
        db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal
