import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import auth
from app.config import settings
from app.db import Base, engine
from app.digest import make_scheduler
from app.routers import digest, library

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Small schema, so create_all on startup instead of a migration tool
    Base.metadata.create_all(engine)
    scheduler = make_scheduler() if settings.scheduler_enabled else None
    if scheduler:
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Resurface API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cache"],
)
app.include_router(auth.router)
app.include_router(library.router)
app.include_router(digest.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True}
