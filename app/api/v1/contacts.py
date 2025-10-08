"""
Contact Endpoints
Manage GHL contacts
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.contact import Contact
from app.models.location import Location
from app.models.oauth import GHLAgencyToken
from app.services.ghl_client import GHLClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_contacts(
    location_id: str = Query(...),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List contacts for a location

    Parameters:
    - location_id: GHL location ID (required)
    - page: Page number (default 1)
    - limit: Results per page (default 20, max 100)
    - search: Search by name or email

    Example:
        GET /api/v1/contacts?location_id=ABC123&page=1&limit=20&search=john
    """
    try:
        # Find location
        location = db.query(Location).filter(
            Location.location_id == location_id
        ).first()

        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        # Build query
        query = db.query(Contact).filter(Contact.location_id == location.id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Contact.contact_name.ilike(search_pattern)) |
                (Contact.email.ilike(search_pattern)) |
                (Contact.first_name.ilike(search_pattern)) |
                (Contact.last_name.ilike(search_pattern))
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        contacts = query.order_by(Contact.date_added.desc()).offset(offset).limit(limit).all()

        return {
            "contacts": [
                {
                    "id": contact.id,
                    "externalId": contact.external_id,
                    "contactName": contact.contact_name,
                    "firstName": contact.first_name,
                    "lastName": contact.last_name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "source": contact.source,
                    "dateAdded": contact.date_added.isoformat() if contact.date_added else None,
                    "aiStatus": contact.ai_status,
                    "aiQualityGrade": contact.ai_quality_grade,
                    "aiSalesGrade": contact.ai_sales_grade,
                    "opportunitiesCount": contact.opportunities_count,
                    "totalPipelineValue": contact.total_pipeline_value,
                    "assignedTo": contact.assigned_to,
                    "lastTouchDate": contact.last_touch_date.isoformat() if contact.last_touch_date else None,
                }
                for contact in contacts
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contact_id}")
async def get_contact(
    contact_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed contact information

    Example:
        GET /api/v1/contacts/contact_123
    """
    try:
        contact = db.query(Contact).filter(
            Contact.external_id == contact_id
        ).first()

        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        return {
            "id": contact.id,
            "externalId": contact.external_id,
            "locationId": contact.location.location_id,
            "contactName": contact.contact_name,
            "firstName": contact.first_name,
            "lastName": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "timezone": contact.timezone,
            "country": contact.country,
            "source": contact.source,
            "dateAdded": contact.date_added.isoformat() if contact.date_added else None,
            "category": contact.category,
            "channel": contact.channel,
            "assignedTo": contact.assigned_to,
            "createdBy": contact.created_by,
            "aiStatus": contact.ai_status,
            "aiSummary": contact.ai_summary,
            "aiQualityGrade": contact.ai_quality_grade,
            "aiSalesGrade": contact.ai_sales_grade,
            "touchSummary": contact.touch_summary,
            "engagementSummary": contact.engagement_summary,
            "lastTouchDate": contact.last_touch_date.isoformat() if contact.last_touch_date else None,
            "lastMessage": contact.last_message,
            "speedToLead": contact.speed_to_lead,
            "crmTasks": contact.crm_tasks,
            "opportunitiesCount": contact.opportunities_count,
            "totalPipelineValue": contact.total_pipeline_value,
            "tags": contact.tags,
            "createdAt": contact.created_at.isoformat(),
            "updatedAt": contact.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_contacts(
    location_id: str = Query(...),
    background_tasks: BackgroundTasks = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Sync contacts from GHL API

    For large contact lists, only syncs one page at a time
    Use background_sync for full sync

    Parameters:
    - location_id: GHL location ID
    - page: Which page to sync (default 1)
    - limit: Contacts per page (default 100)

    Example:
        POST /api/v1/contacts/sync?location_id=ABC123&page=1&limit=100
    """
    try:
        # Find location
        location = db.query(Location).filter(
            Location.location_id == location_id
        ).first()

        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        # Get token
        token = db.query(GHLAgencyToken).filter(
            GHLAgencyToken.company_id == location.company_id,
            GHLAgencyToken.app_id == settings.GHL_APP_ID
        ).first()

        if not token:
            raise HTTPException(
                status_code=404,
                detail="No OAuth token found"
            )

        # Get location-specific token
        client = GHLClient(access_token=token.access_token)
        location_token = await client.get_location_token(
            company_id=location.company_id,
            location_id=location_id
        )

        if not location_token:
            raise HTTPException(
                status_code=400,
                detail="Failed to get location access token"
            )

        # Search contacts
        location_client = GHLClient(access_token=location_token)
        contacts_data = await location_client.search_contacts(
            location_id=location_id,
            page=page,
            limit=limit
        )

        contacts_list = contacts_data.get("contacts", [])
        total_contacts = contacts_data.get("total", 0)

        # Process contacts
        synced = 0
        updated = 0

        for contact_data in contacts_list:
            external_id = contact_data.get("id")
            if not external_id:
                continue

            # Check if contact exists
            existing_contact = db.query(Contact).filter(
                Contact.external_id == external_id,
                Contact.location_id == location.id
            ).first()

            # Prepare contact values
            contact_values = {
                "contact_name": contact_data.get("contactName", "").title(),
                "first_name": contact_data.get("firstName", "").title(),
                "last_name": contact_data.get("lastName", "").title(),
                "email": contact_data.get("email"),
                "phone": contact_data.get("phone"),
                "timezone": contact_data.get("timezone"),
                "country": contact_data.get("country"),
                "source": contact_data.get("source"),
                "tags": str(contact_data.get("tags", [])),
            }

            if existing_contact:
                for key, value in contact_values.items():
                    if value is not None:
                        setattr(existing_contact, key, value)
                updated += 1
            else:
                new_contact = Contact(
                    external_id=external_id,
                    location_id=location.id,
                    **contact_values
                )
                db.add(new_contact)
                synced += 1

        db.commit()

        # Update location contact count
        location.contacts_count = total_contacts
        db.commit()

        return {
            "success": True,
            "synced": synced,
            "updated": updated,
            "total": synced + updated,
            "totalContacts": total_contacts,
            "page": page,
            "hasMore": (page * limit) < total_contacts,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{location_id}")
async def get_contact_stats(
    location_id: str,
    db: Session = Depends(get_db),
):
    """
    Get contact statistics for a location

    Example:
        GET /api/v1/contacts/stats/ABC123
    """
    try:
        location = db.query(Location).filter(
            Location.location_id == location_id
        ).first()

        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        total = db.query(Contact).filter(Contact.location_id == location.id).count()

        # Count by AI status
        statuses = {}
        status_counts = db.query(
            Contact.ai_status,
            db.func.count(Contact.id)
        ).filter(
            Contact.location_id == location.id
        ).group_by(Contact.ai_status).all()

        for status, count in status_counts:
            statuses[status] = count

        # Count by grade
        quality_grades = {}
        quality_counts = db.query(
            Contact.ai_quality_grade,
            db.func.count(Contact.id)
        ).filter(
            Contact.location_id == location.id
        ).group_by(Contact.ai_quality_grade).all()

        for grade, count in quality_counts:
            quality_grades[grade] = count

        return {
            "locationId": location_id,
            "totalContacts": total,
            "byStatus": statuses,
            "byQualityGrade": quality_grades,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
