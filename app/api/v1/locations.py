"""
Location Endpoints
Manage GHL locations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.location import Location
from app.models.oauth import GHLAgencyToken
from app.services.ghl_client import GHLClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_locations(
    company_id: Optional[str] = Query(None),
    is_installed: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """
    List all locations

    Filters:
    - company_id: Filter by company
    - is_installed: Filter by installation status
    - limit: Max results (default 100, max 500)
    - offset: Pagination offset

    Example:
        GET /api/v1/locations?company_id=ABC123&is_installed=true&limit=50
    """
    try:
        query = db.query(Location)

        if company_id:
            query = query.filter(Location.company_id == company_id)
        if is_installed is not None:
            query = query.filter(Location.is_installed == is_installed)

        total = query.count()
        locations = query.offset(offset).limit(limit).all()

        return {
            "locations": [
                {
                    "id": loc.id,
                    "locationId": loc.location_id,
                    "companyId": loc.company_id,
                    "name": loc.name,
                    "address": loc.address,
                    "city": loc.city,
                    "state": loc.state,
                    "country": loc.country,
                    "postalCode": loc.postal_code,
                    "isInstalled": loc.is_installed,
                    "contactsCount": loc.contacts_count,
                    "opportunitiesCount": loc.opportunities_count,
                    "createdAt": loc.created_at.isoformat(),
                    "updatedAt": loc.updated_at.isoformat(),
                }
                for loc in locations
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{location_id}")
async def get_location(
    location_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a location

    Example:
        GET /api/v1/locations/ABC123
    """
    try:
        location = db.query(Location).filter(
            Location.location_id == location_id
        ).first()

        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        return {
            "id": location.id,
            "locationId": location.location_id,
            "companyId": location.company_id,
            "name": location.name,
            "address": location.address,
            "city": location.city,
            "state": location.state,
            "country": location.country,
            "postalCode": location.postal_code,
            "timezone": location.timezone,
            "email": location.email,
            "phone": location.phone,
            "website": location.website,
            "isInstalled": location.is_installed,
            "contactsCount": location.contacts_count,
            "opportunitiesCount": location.opportunities_count,
            "automationTemplate": location.automation_template,
            "createdAt": location.created_at.isoformat(),
            "updatedAt": location.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_locations(
    company_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Sync locations from GHL API
    Fetches all installed locations for a company and updates local database

    Example:
        POST /api/v1/locations/sync?company_id=ABC123
    """
    try:
        # Get agency token
        token = db.query(GHLAgencyToken).filter(
            GHLAgencyToken.company_id == company_id,
            GHLAgencyToken.app_id == settings.GHL_APP_ID
        ).first()

        if not token:
            raise HTTPException(
                status_code=404,
                detail="No OAuth token found for this company"
            )

        # Fetch locations from GHL
        client = GHLClient(access_token=token.access_token)
        ghl_locations = await client.get_installed_locations(
            company_id=company_id,
            app_id=settings.GHL_APP_ID,
            limit=500
        )

        synced_count = 0
        updated_count = 0

        # Store/update each location
        for loc_data in ghl_locations:
            loc_id = loc_data.get("_id")
            if not loc_id:
                continue

            location = db.query(Location).filter(
                Location.location_id == loc_id
            ).first()

            location_values = {
                "name": loc_data.get("name", f"Location {loc_id}"),
                "address": loc_data.get("address"),
                "city": loc_data.get("city"),
                "state": loc_data.get("state"),
                "country": loc_data.get("country"),
                "postal_code": loc_data.get("postalCode"),
                "company_id": company_id,
                "app_id": settings.GHL_APP_ID,
                "is_installed": loc_data.get("isInstalled", True),
            }

            if location:
                for key, value in location_values.items():
                    setattr(location, key, value)
                updated_count += 1
            else:
                location = Location(
                    location_id=loc_id,
                    **location_values
                )
                db.add(location)
                synced_count += 1

        db.commit()

        return {
            "success": True,
            "synced": synced_count,
            "updated": updated_count,
            "total": synced_count + updated_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing locations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{location_id}/refresh")
async def refresh_location(
    location_id: str,
    db: Session = Depends(get_db),
):
    """
    Refresh location details from GHL API

    Example:
        POST /api/v1/locations/ABC123/refresh
    """
    try:
        # Find location
        location = db.query(Location).filter(
            Location.location_id == location_id
        ).first()

        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        # Get agency token
        token = db.query(GHLAgencyToken).filter(
            GHLAgencyToken.company_id == location.company_id,
            GHLAgencyToken.app_id == settings.GHL_APP_ID
        ).first()

        if not token:
            raise HTTPException(
                status_code=404,
                detail="No OAuth token found for this location's company"
            )

        # Fetch fresh data from GHL
        client = GHLClient(access_token=token.access_token)
        location_data = await client.get_location_info(location_id)

        if not location_data:
            raise HTTPException(
                status_code=404,
                detail="Location not found in GHL"
            )

        # Update location
        loc_info = location_data.get("location", {})
        location.name = loc_info.get("name", location.name)
        location.address = loc_info.get("address", location.address)
        location.city = loc_info.get("city", location.city)
        location.state = loc_info.get("state", location.state)
        location.country = loc_info.get("country", location.country)
        location.postal_code = loc_info.get("postalCode", location.postal_code)
        location.timezone = loc_info.get("timezone", location.timezone)
        location.email = loc_info.get("email", location.email)
        location.phone = loc_info.get("phone", location.phone)
        location.website = loc_info.get("website", location.website)

        db.commit()

        return {
            "success": True,
            "message": "Location refreshed successfully",
            "locationId": location_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing location: {e}")
        raise HTTPException(status_code=500, detail=str(e))
