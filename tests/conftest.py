"""
Pytest Fixtures: In-Memory SQLite Database, Test Session, TestClient, and Test Users.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models import User
from backend.auth import hash_password, create_access_token
from backend.services.price_service import seed_prices_from_csv


@pytest.fixture(scope="session")
def test_engine():
    """
    Session-wide in-memory SQLite engine using StaticPool so all connections share the memory DB.
    """
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    TestSession = sessionmaker(bind=eng)
    init_session = TestSession()
    seed_prices_from_csv(init_session)
    init_session.close()
    return eng


@pytest.fixture(scope="function")
def db(test_engine):
    """
    Function-scoped database session.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient with overridden get_db dependency.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db) -> User:
    """
    Create a clean test user in the database.
    """
    user = User(
        email="testinvestor@hindsight.app",
        hashed_password=hash_password("TestSecret123"),
        full_name="Priya Patel",
        age=30,
        income_band="10L-20L",
        employment_type="Product Designer",
        pan_hash="abc1234567890123456789012345678901234567890123456789012345678901",
        kyc_status="verified",
        consent_ts=datetime.now(timezone.utc),
        is_demo=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user) -> dict:
    """
    Bearer authorization headers for test_user.
    """
    token = create_access_token(
        data={"sub": test_user.id, "email": test_user.email, "name": test_user.full_name}
    )
    return {"Authorization": f"Bearer {token}"}
