from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

try:
    import psycopg2  # noqa: F401
except ModuleNotFoundError:
    if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        SQLALCHEMY_DATABASE_URL = settings.test_database_url

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Import model modules so metadata is registered before create_all().
from app.models import entities  # noqa: F401,E402

try:
    Base.metadata.create_all(bind=engine)
except Exception:  # pragma: no cover - safe guard for environment-specific DB setup
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
