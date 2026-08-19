from __future__ import annotations

import os

import pytest
from sqlalchemy import text

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///./test.db")

from app.database import Base, engine


@pytest.fixture(autouse=True)
def reset_database():
    # Ensure each test starts with a clean state to avoid stale SQLite data from previous runs.
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'DELETE FROM "{table.name}"'))
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'DELETE FROM "{table.name}"'))
