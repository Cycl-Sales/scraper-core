"""
OAuth Token Models
Stores GHL OAuth credentials for agencies and locations
"""
from sqlalchemy import Column, String, DateTime, Boolean, Index
from app.models.base import BaseModel


class GHLApplication(BaseModel):
    """
    GHL Application Configuration
    Stores client credentials for GHL marketplace apps
    """
    __tablename__ = "ghl_applications"

    name = Column(String(255), nullable=False)
    app_id = Column(String(255), unique=True, nullable=False, index=True)
    client_id = Column(String(255), nullable=False)
    client_secret = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_app_id_active', 'app_id', 'is_active'),
    )


class GHLAgencyToken(BaseModel):
    """
    Agency-level OAuth Tokens
    Stores access/refresh tokens for company-level installations
    """
    __tablename__ = "ghl_agency_tokens"

    company_id = Column(String(255), nullable=False, index=True)
    app_id = Column(String(255), nullable=False, index=True)
    access_token = Column(String(1024), nullable=False)
    refresh_token = Column(String(1024), nullable=False)
    token_expiry = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_company_app', 'company_id', 'app_id', unique=True),
    )


class GHLLocationToken(BaseModel):
    """
    Location-level OAuth Tokens
    Stores access tokens for specific GHL locations
    """
    __tablename__ = "ghl_location_tokens"

    location_id = Column(String(255), nullable=False, index=True)
    app_id = Column(String(255), nullable=False, index=True)
    access_token = Column(String(1024), nullable=False)
    refresh_token = Column(String(1024), nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_location_app', 'location_id', 'app_id', unique=True),
    )
