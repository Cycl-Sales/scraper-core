"""
Authentication Endpoints
Login, logout, token refresh, 2FA
"""
from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.auth import (
    create_token_pair,
    verify_refresh_token,
    get_current_user,
    hash_password,
    verify_password
)
from app.core.two_factor import two_factor_auth
from app.models.auth import TwoFactorAuth as TwoFactorModel

router = APIRouter()


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    requires_2fa: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class Setup2FAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list


class Verify2FARequest(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login

    Returns JWT tokens for authentication
    """
    # TODO: Fetch user from database
    # user = db.query(User).filter(User.email == credentials.email).first()
    # if not user or not verify_password(credentials.password, user.password_hash):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")

    # For now, demo implementation
    user_id = "demo_user_123"
    role = "user"

    # Check if 2FA is enabled
    two_fa = db.query(TwoFactorModel).filter(
        TwoFactorModel.user_id == user_id
    ).first()

    if two_fa and two_fa.is_enabled:
        # Return temporary token, require 2FA verification
        return {
            "access_token": "",
            "refresh_token": "",
            "token_type": "bearer",
            "expires_in": 0,
            "requires_2fa": True
        }

    # Create token pair
    tokens = create_token_pair(user_id, role)

    return {
        **tokens,
        "requires_2fa": False
    }


@router.post("/refresh")
async def refresh_tokens(request: RefreshRequest):
    """
    Refresh access token using refresh token

    Returns new access token
    """
    # Verify refresh token
    payload = verify_refresh_token(request.refresh_token)

    user_id = payload.get("sub")

    # TODO: Verify user still exists and is active
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user or not user.is_active:
    #     raise HTTPException(status_code=401, detail="User not found")

    # Create new token pair
    tokens = create_token_pair(user_id, role="user")

    return tokens


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user

    Blacklists the current access token
    """
    # TODO: Add token to blacklist
    # jti = current_user.get("jti")
    # blacklist_entry = TokenBlacklist(
    #     jti=jti,
    #     user_id=current_user["user_id"],
    #     token_type="access",
    #     expires_at=...,
    #     reason="logout"
    # )
    # db.add(blacklist_entry)
    # db.commit()

    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user


# 2FA Endpoints

@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Setup 2FA for current user

    Returns QR code and backup codes
    """
    user_id = current_user["user_id"]
    user_email = "user@example.com"  # TODO: Fetch from user record

    # Check if already set up
    existing_2fa = db.query(TwoFactorModel).filter(
        TwoFactorModel.user_id == user_id
    ).first()

    if existing_2fa and existing_2fa.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="2FA already enabled"
        )

    # Generate 2FA setup
    setup_data = two_factor_auth.setup_2fa(user_email)

    # Store in database (not enabled yet until verified)
    if existing_2fa:
        existing_2fa.totp_secret = setup_data["secret"]
        existing_2fa.backup_codes = str(setup_data["backup_codes_hashed"])
        existing_2fa.is_enabled = False
    else:
        two_fa_record = TwoFactorModel(
            user_id=user_id,
            totp_secret=setup_data["secret"],
            backup_codes=str(setup_data["backup_codes_hashed"]),
            is_enabled=False
        )
        db.add(two_fa_record)

    db.commit()

    return {
        "secret": setup_data["secret"],
        "qr_code": setup_data["qr_code"],
        "backup_codes": setup_data["backup_codes"]
    }


@router.post("/2fa/verify")
async def verify_2fa(
    request: Verify2FARequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify 2FA token and enable 2FA

    Called after setup to confirm the user can generate valid codes
    """
    user_id = current_user["user_id"]

    # Get 2FA record
    two_fa = db.query(TwoFactorModel).filter(
        TwoFactorModel.user_id == user_id
    ).first()

    if not two_fa:
        raise HTTPException(status_code=404, detail="2FA not set up")

    # Verify token
    if not two_factor_auth.verify_token(two_fa.totp_secret, request.token):
        raise HTTPException(status_code=400, detail="Invalid 2FA token")

    # Enable 2FA
    two_fa.is_enabled = True
    two_fa.verified_at = datetime.now()
    db.commit()

    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    request: Verify2FARequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable 2FA

    Requires valid 2FA token to disable
    """
    user_id = current_user["user_id"]

    # Get 2FA record
    two_fa = db.query(TwoFactorModel).filter(
        TwoFactorModel.user_id == user_id
    ).first()

    if not two_fa or not two_fa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA not enabled")

    # Verify token before disabling
    if not two_factor_auth.verify_token(two_fa.totp_secret, request.token):
        raise HTTPException(status_code=400, detail="Invalid 2FA token")

    # Disable 2FA
    two_fa.is_enabled = False
    db.commit()

    return {"message": "2FA disabled successfully"}


@router.post("/2fa/login")
async def login_with_2fa(
    credentials: LoginRequest,
    two_fa_token: str,
    db: Session = Depends(get_db)
):
    """
    Complete login with 2FA token

    After initial login returns requires_2fa=True,
    call this endpoint with the 2FA token
    """
    # TODO: Verify credentials first
    user_id = "demo_user_123"

    # Get 2FA record
    two_fa = db.query(TwoFactorModel).filter(
        TwoFactorModel.user_id == user_id
    ).first()

    if not two_fa or not two_fa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA not required")

    # Verify 2FA token
    if not two_factor_auth.verify_token(two_fa.totp_secret, two_fa_token):
        raise HTTPException(status_code=400, detail="Invalid 2FA token")

    # Create token pair
    tokens = create_token_pair(user_id, role="user")

    return tokens


from datetime import datetime
