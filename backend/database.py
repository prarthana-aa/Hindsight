"""
Database Engine and Session Configuration.
"""
import os
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DB_URL

_engine_options = {"echo": False}
if DB_URL.startswith("sqlite"):
    # SQLite needs this option for FastAPI's threaded request handling. It is
    # not a valid PostgreSQL connection option.
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_URL, **_engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
logger = logging.getLogger(__name__)

REQUIRED_TABLES = {
    "users",
    "risk_profiles",
    "goals",
    "portfolios",
    "wallet_ledger",
    "orders",
    "holdings",
    "prices",
    "audit_log",
}


def get_db():
    """
    FastAPI dependency yielding a database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """
    Create missing tables without altering or deleting existing records.

    The legacy SQLite ledger rewrite is intentionally opt-in. It is not run
    during production startup and is never applicable to PostgreSQL.
    """
    # Import the model module explicitly at the initialization boundary. This
    # guarantees every declarative model is registered before create_all(),
    # regardless of router/service import order.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    missing_tables = REQUIRED_TABLES.difference(inspect(engine).get_table_names())
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"Database initialization incomplete; missing tables: {missing}")

    logger.info(
        "Database schema ready: dialect=%s host=%s database=%s tables=%d",
        engine.url.get_backend_name(),
        engine.url.host or "local",
        engine.url.database or "default",
        len(REQUIRED_TABLES),
    )

    if engine.url.get_backend_name() == "sqlite" and os.getenv("ALLOW_LEGACY_SQLITE_MIGRATION", "false").lower() == "true":
        _migrate_legacy_ledger()


def _migrate_legacy_ledger():
    """Upgrade databases created before WalletLedger gained its sequence key."""
    if engine.url.get_backend_name() != "sqlite":
        return
    inspector = inspect(engine)
    if "wallet_ledger" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("wallet_ledger")}
    if "seq" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE wallet_ledger_new (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                id VARCHAR(36) UNIQUE NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                entry_type VARCHAR(10) NOT NULL,
                amount NUMERIC(18, 4) NOT NULL,
                running_balance NUMERIC(18, 4) NOT NULL,
                reference_id VARCHAR(100),
                memo VARCHAR(500) NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        connection.execute(text("""
            INSERT INTO wallet_ledger_new
                (id, user_id, entry_type, amount, running_balance, reference_id, memo, created_at)
            SELECT id, user_id, entry_type, amount, running_balance, reference_id, memo, created_at
            FROM wallet_ledger
            ORDER BY created_at ASC, rowid ASC
        """))
        connection.execute(text("DROP TABLE wallet_ledger"))
        connection.execute(text("ALTER TABLE wallet_ledger_new RENAME TO wallet_ledger"))
