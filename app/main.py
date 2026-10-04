from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import initialize_database, ping_db
from app.routes import auth_router, expenses_router, groups_router, users_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Expense Split backend powered by FastAPI, MongoDB, and LangChain Hugging Face.",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(groups_router)
app.include_router(expenses_router)


@app.get("/")
async def read_root() -> dict:
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "status": "ok",
    }


@app.get("/health")
async def health_check() -> dict:
    db_ok = await ping_db()
    return {
        "ready": db_ok,
        "service": settings.app_name,
    }
