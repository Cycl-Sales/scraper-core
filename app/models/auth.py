"""
Authentication Models
API keys, user sessions, and token blacklist
"""
from sqlalchemy import Column, String, DateTime, Boolean, Index, Text
from datetime import datetime
from app.models.base import BaseModel


class APIKey(BaseModel):
    """
    API Key for programmatic access
    Each client gets a unique API key
    """
    __tablename__ = "api_keys"

    # API Key (hashed)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Key prefix for identification (first 8 chars, unhashed)
    key_prefix = Column(String(16), nullable=False)

    # Owner information
    owner_id = Column(String(255), nullable=False, index=True)
    owner_type = Column(String(50), nullable=False)  # user, location, service

    # Key metadata
    name = Column(String(255), nullable=False)  # "Production API", "Testing", etc.
    description = Column(Text, nullable=True)

    # Permissions
    scopes = Column(Text, nullable=True)  # JSON list of allowed scopes

    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # IP Restrictions
    allowed_ips = Column(Text, nullable=True)  # JSON list of allowed IPs

    __table_args__ = (
        Index('idx_apikey_owner', 'owner_id', 'owner_type'),
        Index('idx_apikey_active', 'is_active', 'expires_at'),
    )


class TokenBlacklist(BaseModel):
    """
    Blacklisted JWT tokens (for logout)
    Tokens here are invalid even if not expired
    """
    __tablename__ = "token_blacklist"

    # Token identifier (jti claim)
    jti = Column(String(255), unique=True, nullable=False, index=True)

    # Token type
    token_type = Column(String(20), nullable=False)  # access, refresh

    # User who owned the token
    user_id = Column(String(255), nullable=False, index=True)

    # Original expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Reason for blacklisting
    reason = Column(String(255), nullable=True)  # logout, security, etc.

    __table_args__ = (
        Index('idx_blacklist_expiry', 'expires_at'),
    )


class UserSession(BaseModel):
    """
    Active user sessions
    Track login sessions for security monitoring
    """
    __tablename__ = "user_sessions"

    # Session identifier
    session_id = Column(String(255), unique=True, nullable=False, index=True)

    # User
    user_id = Column(String(255), nullable=False, index=True)

    # Session data
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)  # City, Country

    # Tokens
    refresh_token_hash = Column(String(255), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # 2FA
    requires_2fa = Column(Boolean, default=False)
    is_2fa_verified = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expiry', 'expires_at'),
    )


class TwoFactorAuth(BaseModel):
    """
    2FA/MFA secrets for users
    """
    __tablename__ = "two_factor_auth"

    # User
    user_id = Column(String(255), unique=True, nullable=False, index=True)

    # TOTP secret
    totp_secret = Column(String(255), nullable=False)

    # Backup codes (hashed)
    backup_codes = Column(Text, nullable=True)  # JSON array of hashed codes

    # Status
    is_enabled = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Recovery
    recovery_email = Column(String(255), nullable=True)
    recovery_phone = Column(String(50), nullable=True)


class IPWhitelist(BaseModel):
    """
    IP Whitelist for restricted endpoints
    """
    __tablename__ = "ip_whitelist"

    # IP address or CIDR range
    ip_address = Column(String(45), nullable=False, index=True)
    cidr_range = Column(String(50), nullable=True)

    # Owner
    owner_id = Column(String(255), nullable=False, index=True)
    owner_type = Column(String(50), nullable=False)  # user, location, global

    # Metadata
    description = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_whitelist_ip_active', 'ip_address', 'is_active'),
    )
