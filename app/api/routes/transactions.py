from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.bank_sender import BankSender
from app.schemas.transaction import TransactionCreate, TransactionCategoryUpdate, TransactionOut
from app.services.categorizer import categorize
from app.services.gmail_service import fetch_new_bank_emails

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def _active_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(
        select(Category).where(Category.active.is_(True)).order_by(Category.sort_order)
    )
    return list(result.scalars().all())


async def _validate_category(db: AsyncSession, category: str) -> None:
    if category not in {c.id for c in await _active_categories(db)}:
        raise HTTPException(status_code=400, detail=f"Categoría inválida: {category}")


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    month: str | None = None,  # formato YYYY-MM; si no se pasa, devuelve el mes actual
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = month or date.today().strftime("%Y-%m")
    year, mon = (int(p) for p in target.split("-"))
    month_start = date(year, mon, 1)
    month_end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.date >= month_start,
            Transaction.date < month_end,
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
    await _validate_category(db, body.category)
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
    await _validate_category(db, body.category)
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

    # Sync incremental: buscar desde el último correo sincronizado (con colchón
    # de 3 días por correos retrasados); el dedup por email_id cubre el traslape.
    last_sync = await db.execute(
        select(func.max(Transaction.created_at)).where(
            Transaction.user_id == current_user.id,
            Transaction.email_id.is_not(None),
        )
    )
    # created_at es timezone-aware en Postgres, así que .timestamp() es correcto
    last_dt = last_sync.scalar()
    after_ts = int((last_dt - timedelta(days=3)).timestamp()) if last_dt else None

    # Remitentes bancarios reconocidos (tabla bank_senders)
    senders = await db.execute(select(BankSender).where(BankSender.active.is_(True)))
    sender_map = {s.email.lower(): s.parser_key for s in senders.scalars().all()}

    categories = await _active_categories(db)

    # El cliente de Gmail es síncrono: correrlo en threadpool para no bloquear el event loop
    email_txs, refreshed_token = await run_in_threadpool(
        fetch_new_bank_emails,
        current_user.google_access_token,
        current_user.google_refresh_token,
        after_ts,
        sender_map,
    )
    if refreshed_token:
        # Google renueva el access token cada hora; persistirlo evita
        # re-refrescarlo en cada sync
        current_user.google_access_token = refreshed_token

    saved = []
    for email_id, parsed in email_txs:
        existing = await db.execute(
            select(Transaction).where(
                Transaction.email_id == email_id,
                Transaction.user_id == current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            continue  # ya procesado

        category = await categorize(parsed.merchant, parsed.bank, categories)

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

    if saved or refreshed_token:
        await db.commit()
        for tx in saved:
            await db.refresh(tx)

    return saved
