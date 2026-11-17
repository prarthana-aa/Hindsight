"""
Authentication Router.
Handles user registration, login, demo access, and profile retrieval.
"""

from datetime import datetime, timezone
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import (
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
)
from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from ..seed_demo import seed_demo_account
from ..config import DEMO_USER_EMAIL

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: UserSignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user account with simulated KYC-lite check.
    """
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash simulated PAN for audit privacy
    pan_hash = None
    if payload.simulated_pan:
        pan_clean = payload.simulated_pan.strip().upper()
        pan_hash = hashlib.sha256(pan_clean.encode("utf-8")).hexdigest()

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        age=payload.age,
        income_band=payload.income_band,
        employment_type=payload.employment_type,
        pan_hash=pan_hash,
        kyc_status="verified",  # Simulated KYC instant clearance
        consent_ts=datetime.now(timezone.utc),
        is_demo=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "name": user.full_name}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_demo=user.is_demo,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password.
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "name": user.full_name}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_demo=user.is_demo,
    )


@router.post("/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)):
    """
    Instant 1-click Demo Account login.
    Pre-loads realistic portfolio, history, and virtual cash balance.
    """
    demo_user = seed_demo_account(db, reset_if_exists=False)

    token = create_access_token(
        data={"sub": demo_user.id, "email": demo_user.email, "name": demo_user.full_name}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=demo_user.id,
        email=demo_user.email,
        full_name=demo_user.full_name,
        is_demo=True,
    )


@router.post("/demo/reset", response_model=TokenResponse)
def reset_demo(db: Session = Depends(get_db)):
    """
    Resets the demo account state back to factory defaults with 1 click.
    """
    demo_user = seed_demo_account(db, reset_if_exists=True)

    token = create_access_token(
        data={"sub": demo_user.id, "email": demo_user.email, "name": demo_user.full_name}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=demo_user.id,
        email=demo_user.email,
        full_name=demo_user.full_name,
        is_demo=True,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """
    Get the authenticated user's profile details.
    """
    return user

