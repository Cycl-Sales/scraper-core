"""
Webhook Event Models
Stores incoming webhook events from GHL
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from app.models.base import BaseModel


class WebhookEvent(BaseModel):
    """
    GHL Webhook Event Log
    Stores all incoming webhook events for auditing and debugging
    """
    __tablename__ = "webhook_events"

    # Event data
    event_type = Column(String(100), nullable=False, index=True)
    location_id = Column(String(255), nullable=True, index=True)
    company_id = Column(String(255), nullable=True, index=True)
    user_id = Column(String(255), nullable=True)

    # Payload
    payload = Column(Text, nullable=False)  # JSON string

    # Timing
    event_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Processing status
    processed = Column(String(20), default="pending")  # pending, success, failed
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_webhook_type_location', 'event_type', 'location_id'),
        Index('idx_webhook_processed', 'processed', 'created_at'),
    )
