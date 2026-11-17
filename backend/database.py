"""
Database Engine and Session Configuration.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DB_URL

# For SQLite, check_same_thread=False allows FastAPI threads to share sessions safely
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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
    Create all tables in the SQLite database schema if they do not exist.
    """
    Base.metadata.create_all(bind=engine)
    _migrate_legacy_ledger()


def _migrate_legacy_ledger():
    """Upgrade databases created before WalletLedger gained its sequence key."""
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
