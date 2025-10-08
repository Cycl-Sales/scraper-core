"""
Location Models
Stores GHL location data
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Location(BaseModel):
    """
    GHL Location
    Represents a GHL sub-account/location
    """
    __tablename__ = "locations"

    # GHL identifiers
    location_id = Column(String(255), unique=True, nullable=False, index=True)
    company_id = Column(String(255), nullable=True, index=True)
    app_id = Column(String(255), nullable=True, index=True)

    # Basic info
    name = Column(String(500), nullable=False)
    address = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(50), nullable=True)
    timezone = Column(String(100), nullable=True)

    # Status
    is_installed = Column(Boolean, default=False)

    # Contact info
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)

    # Analytics (cached values)
    contacts_count = Column(Integer, default=0)
    opportunities_count = Column(Integer, default=0)

    # OpenAI API key (location-specific)
    openai_api_key = Column(String(255), nullable=True)

    # Automation template
    automation_template = Column(String(255), nullable=True)

    # Relationships
    contacts = relationship("Contact", back_populates="location", cascade="all, delete-orphan")


class LocationDetail(BaseModel):
    """
    Extended Location Details
    Stores additional location metadata from GHL API
    """
    __tablename__ = "location_details"

    location_id = Column(Integer, ForeignKey("locations.id"), unique=True, nullable=False)

    # Business info
    business_name = Column(String(500), nullable=True)
    logo_url = Column(String(1000), nullable=True)
    domain = Column(String(500), nullable=True)

    # Social links
    facebook_url = Column(String(500), nullable=True)
    instagram = Column(String(255), nullable=True)
    linkedin = Column(String(500), nullable=True)
    twitter = Column(String(255), nullable=True)
    youtube = Column(String(500), nullable=True)

    # Settings (JSON would be better but keeping it simple)
    settings_json = Column(Text, nullable=True)

    # Relationship
    location = relationship("Location", backref="details")
