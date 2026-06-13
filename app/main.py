from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.seed import seed_defaults
from app.api.routes import auth, transactions, budgets, goals, categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_defaults()
    yield


app = FastAPI(
    title="Gastly API",
    description="Backend para la app de finanzas personales Gastly",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL, "http://localhost:8081", "http://localhost:19006"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(categories.router)


@app.get("/")
async def root():
    return {"status": "ok", "app": "Gastly API v0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
