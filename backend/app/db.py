from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.types import Float

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


class days_between(FunctionElement):  # noqa: N801 — reads like a SQL function at call sites
    """days_between(later, earlier) as a fractional number of days.

    Postgres and SQLite spell date arithmetic differently, so the scoring query compiles
    to the right SQL per dialect instead of pulling rows into Python.
    """

    type = Float()
    inherit_cache = True


@compiles(days_between, "postgresql")
def _days_pg(element, compiler, **kw):
    later, earlier = (compiler.process(c, **kw) for c in element.clauses)
    return f"(EXTRACT(EPOCH FROM ({later} - {earlier})) / 86400.0)"


@compiles(days_between, "sqlite")
def _days_sqlite(element, compiler, **kw):
    later, earlier = (compiler.process(c, **kw) for c in element.clauses)
    return f"(julianday({later}) - julianday({earlier}))"
