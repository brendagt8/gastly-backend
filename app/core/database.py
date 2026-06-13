from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# PostgreSQL (RDS): pool_pre_ping descarta conexiones muertas tras
# reinicios/failovers de RDS; pool_recycle evita que el idle timeout del
# servidor cierre conexiones que el pool cree vivas.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    # Crea las tablas que aún no existan. create_all es idempotente: no toca las
    # que ya están. El esquema se gestiona desde los modelos; al ser una BD sin
    # datos, cambiarlo es recrearla.
    import app.models  # noqa: F401 — registra todos los modelos en Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
