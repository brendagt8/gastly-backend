from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionCategoryUpdate, TransactionOut
from app.services.categorizer import categorize
from app.services.gmail_service import fetch_new_bank_emails

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    month: str | None = None,  # formato YYYY-MM; si no se pasa, devuelve el mes actual
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = month or date.today().strftime("%Y-%m")
    year, mon = target.split("-")
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.date >= date(int(year), int(mon), 1),
        )
        .order_by(desc(Transaction.date), desc(Transaction.created_at))
    )
    return result.scalars().all()


@router.post("", response_model=TransactionOut, status_code=201)
async def add_manual_transaction(
    body: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = Transaction(
        user_id=current_user.id,
        merchant=body.merchant,
        amount=body.amount,
        category=body.category,
        bank="Efectivo",
        date=body.tx_date or date.today(),
        manual=True,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


@router.patch("/{transaction_id}/category", response_model=TransactionOut)
async def recategorize(
    transaction_id: str,
    body: TransactionCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    tx.category = body.category
    tx.recategorized = True
    await db.commit()
    await db.refresh(tx)
    return tx


@router.post("/sync", response_model=list[TransactionOut])
async def sync_gmail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lee correos bancarios nuevos de Gmail y los guarda como transacciones."""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Gmail no conectado")

    email_txs = fetch_new_bank_emails(
        current_user.google_access_token,
        current_user.google_refresh_token,
    )

    saved = []
    for email_id, parsed in email_txs:
        existing = await db.execute(select(Transaction).where(Transaction.email_id == email_id))
        if existing.scalar_one_or_none():
            continue  # ya procesado

        category = await categorize(parsed.merchant, parsed.bank)

        tx = Transaction(
            user_id=current_user.id,
            merchant=parsed.merchant,
            amount=parsed.amount,
            category=category,
            bank=parsed.bank,
            card_last4=parsed.card_last4,
            date=parsed.date,
            email_id=email_id,
        )
        db.add(tx)
        saved.append(tx)

    if saved:
        await db.commit()
        for tx in saved:
            await db.refresh(tx)

    return saved
