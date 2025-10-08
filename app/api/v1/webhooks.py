"""
Webhook Endpoints
Handles incoming webhooks from GHL
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any
import logging
import json

from app.core.database import get_db
from app.models.webhook import WebhookEvent
from app.models.location import Location

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/events")
async def handle_webhook_event(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle incoming GHL webhook events

    Supported event types:
    - INSTALL: App installed on location
    - UNINSTALL: App uninstalled from location
    - LOCATION_UPDATE: Location data changed
    - CONTACT_CREATE: New contact created
    - CONTACT_UPDATE: Contact updated
    - CONTACT_DELETE: Contact deleted
    - OPPORTUNITY_CREATE: New opportunity created
    - OPPORTUNITY_UPDATE: Opportunity updated

    Example payload:
        {
            "type": "INSTALL",
            "locationId": "ABC123",
            "companyId": "XYZ789",
            "userId": "user_123",
            "timestamp": "2024-10-07T12:00:00.000Z"
        }
    """
    try:
        # Parse request body
        body = await request.body()
        payload_str = body.decode("utf-8")
        payload = json.loads(payload_str)

        # Extract event data
        event_type = payload.get("type")
        location_id = payload.get("locationId")
        company_id = payload.get("companyId")
        user_id = payload.get("userId")
        timestamp_str = payload.get("timestamp")

        # Parse timestamp
        event_timestamp = None
        if timestamp_str:
            try:
                event_timestamp = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
            except Exception as e:
                logger.warning(f"Failed to parse timestamp: {e}")

        # Log the event
        webhook_event = WebhookEvent(
            event_type=event_type,
            location_id=location_id,
            company_id=company_id,
            user_id=user_id,
            payload=payload_str,
            event_timestamp=event_timestamp,
            processed="pending",
        )
        db.add(webhook_event)
        db.commit()

        # Process event based on type
        try:
            if event_type == "INSTALL":
                await handle_install_event(payload, db)
            elif event_type == "UNINSTALL":
                await handle_uninstall_event(payload, db)
            elif event_type == "LOCATION_UPDATE":
                await handle_location_update_event(payload, db)
            # Add more event handlers as needed

            # Mark as processed
            webhook_event.processed = "success"
            db.commit()

        except Exception as processing_error:
            logger.error(f"Error processing webhook event: {processing_error}", exc_info=True)
            webhook_event.processed = "failed"
            webhook_event.error_message = str(processing_error)
            db.commit()

        return {"success": True, "message": "Event received and processed"}

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def handle_install_event(payload: Dict[str, Any], db: Session):
    """Handle app installation event"""
    location_id = payload.get("locationId")
    company_id = payload.get("companyId")

    if not location_id:
        logger.warning("Install event missing locationId")
        return

    # Find or create location
    location = db.query(Location).filter(
        Location.location_id == location_id
    ).first()

    if location:
        location.is_installed = True
        location.company_id = company_id
    else:
        location = Location(
            location_id=location_id,
            name=f"GHL Location {location_id}",
            company_id=company_id,
            is_installed=True,
        )
        db.add(location)

    db.commit()
    logger.info(f"App installed for location: {location_id}")


async def handle_uninstall_event(payload: Dict[str, Any], db: Session):
    """Handle app uninstallation event"""
    location_id = payload.get("locationId")

    if not location_id:
        logger.warning("Uninstall event missing locationId")
        return

    # Mark location as uninstalled
    location = db.query(Location).filter(
        Location.location_id == location_id
    ).first()

    if location:
        location.is_installed = False
        db.commit()
        logger.info(f"App uninstalled for location: {location_id}")


async def handle_location_update_event(payload: Dict[str, Any], db: Session):
    """Handle location data update event"""
    location_id = payload.get("locationId")

    if not location_id:
        logger.warning("Location update event missing locationId")
        return

    # Find location
    location = db.query(Location).filter(
        Location.location_id == location_id
    ).first()

    if location:
        # Update location data from payload
        location_data = payload.get("data", {})

        if "name" in location_data:
            location.name = location_data["name"]
        if "address" in location_data:
            location.address = location_data["address"]
        if "city" in location_data:
            location.city = location_data["city"]
        if "state" in location_data:
            location.state = location_data["state"]
        if "country" in location_data:
            location.country = location_data["country"]
        if "postalCode" in location_data:
            location.postal_code = location_data["postalCode"]

        db.commit()
        logger.info(f"Location updated: {location_id}")


@router.get("/events")
async def list_webhook_events(
    limit: int = 50,
    event_type: str = None,
    location_id: str = None,
    db: Session = Depends(get_db),
):
    """
    List recent webhook events (for debugging)

    Example:
        GET /api/v1/webhooks/events?limit=20&event_type=INSTALL
    """
    try:
        query = db.query(WebhookEvent)

        if event_type:
            query = query.filter(WebhookEvent.event_type == event_type)
        if location_id:
            query = query.filter(WebhookEvent.location_id == location_id)

        events = query.order_by(WebhookEvent.created_at.desc()).limit(limit).all()

        return {
            "events": [
                {
                    "id": event.id,
                    "type": event.event_type,
                    "locationId": event.location_id,
                    "companyId": event.company_id,
                    "timestamp": event.event_timestamp.isoformat() if event.event_timestamp else None,
                    "processed": event.processed,
                    "createdAt": event.created_at.isoformat(),
                }
                for event in events
            ],
            "count": len(events),
        }

    except Exception as e:
        logger.error(f"Error listing webhook events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
