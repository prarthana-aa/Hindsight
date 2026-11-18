"""Database initialization and ORM metadata registration tests."""

from sqlalchemy import create_engine, inspect
from fastapi.testclient import TestClient

import backend.database as database
import backend.main as main


def test_create_all_tables_registers_every_model_without_touching_local_db():
    """Initialization creates the complete schema on an independent SQLite engine."""
    original_engine = database.engine
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    database.engine = test_engine

    try:
        database.create_all_tables()
        assert database.REQUIRED_TABLES.issubset(set(inspect(test_engine).get_table_names()))
    finally:
        database.engine = original_engine
        test_engine.dispose()


def test_fastapi_lifespan_runs_system_initialization(monkeypatch):
    """The application must execute initialization before serving requests."""
    initialized = []
    monkeypatch.setattr(main, "init_system_data", lambda: initialized.append(True))

    with TestClient(main.app):
        pass

    assert initialized == [True]
