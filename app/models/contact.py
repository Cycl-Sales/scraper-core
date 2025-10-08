"""
Contact Models
Stores GHL contact data and related information
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Contact(BaseModel):
    """
    GHL Contact
    Represents a contact/lead in GHL
    """
    __tablename__ = "contacts"

    # GHL identifiers
    external_id = Column(String(255), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)

    # Basic info
    contact_name = Column(String(500), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)

    # Location data
    timezone = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)

    # Tracking
    source = Column(String(255), nullable=True)
    date_added = Column(DateTime(timezone=True), nullable=True, index=True)
    business_id = Column(String(255), nullable=True)

    # Categorization
    tags = Column(Text, nullable=True)  # JSON string
    category = Column(String(255), default="manual")
    channel = Column(String(255), default="manual")

    # Assignment
    assigned_to = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)

    # Analytics fields
    ai_status = Column(String(100), default="not_contacted")
    ai_summary = Column(Text, default="Read")
    ai_quality_grade = Column(String(50), default="no_grade")
    ai_sales_grade = Column(String(50), default="no_grade")

    # Activity metrics
    touch_summary = Column(String(255), default="no_touches")
    engagement_summary = Column(Text, nullable=True)
    last_touch_date = Column(DateTime(timezone=True), nullable=True)
    last_message = Column(Text, nullable=True)
    speed_to_lead = Column(String(100), nullable=True)

    # CRM data
    crm_tasks = Column(String(100), default="no_tasks")
    opportunities_count = Column(Integer, default=0)
    total_pipeline_value = Column(Float, default=0.0)

    # Attribution
    attribution = Column(Text, nullable=True)  # JSON string
    followers = Column(Text, nullable=True)  # JSON string

    # Data sync status
    details_fetched = Column(String(20), default="false")

    # Relationships
    location = relationship("Location", back_populates="contacts")
    opportunities = relationship("Opportunity", back_populates="contact", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="contact", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_contact_location', 'external_id', 'location_id', unique=True),
        Index('idx_contact_date', 'location_id', 'date_added'),
    )


class Opportunity(BaseModel):
    """
    GHL Opportunity/Pipeline
    Represents a sales opportunity
    """
    __tablename__ = "opportunities"

    # GHL identifiers
    external_id = Column(String(255), nullable=False, unique=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)

    # Opportunity info
    name = Column(String(500), nullable=True)
    pipeline_id = Column(String(255), nullable=True)
    pipeline_stage_id = Column(String(255), nullable=True)
    status = Column(String(100), nullable=True)

    # Financial
    monetary_value = Column(Float, default=0.0)

    # Dates
    created_date = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    contact = relationship("Contact", back_populates="opportunities")


class Task(BaseModel):
    """
    GHL Task
    Represents a CRM task
    """
    __tablename__ = "tasks"

    # GHL identifiers
    external_id = Column(String(255), nullable=False, unique=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)

    # Task info
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)

    # Assignment
    assigned_to = Column(String(255), nullable=True)

    # Dates
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    contact = relationship("Contact", back_populates="tasks")


class Conversation(BaseModel):
    """
    GHL Conversation
    Represents a conversation thread with a contact
    """
    __tablename__ = "conversations"

    # GHL identifiers
    external_id = Column(String(255), nullable=False, unique=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)

    # Conversation info
    channel = Column(String(100), nullable=True)  # SMS, email, etc.
    last_message_date = Column(DateTime(timezone=True), nullable=True)
    unread_count = Column(Integer, default=0)

    # Related contact
    contact = relationship("Contact", backref="conversations")
