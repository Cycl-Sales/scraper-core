"""
OAuth Endpoints
Handles GHL OAuth authorization flow
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.oauth import GHLAgencyToken, GHLApplication
from app.models.location import Location
from app.services.ghl_client import GHLClient, GHLOAuthHelper

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/authorize")
async def authorize(
    location_id: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
):
    """
    Initiate OAuth flow
    Redirects user to GHL authorization page

    Example:
        GET /api/v1/oauth/authorize?locationId=ABC123
    """
    try:
        auth_url = GHLOAuthHelper.get_authorization_url(
            location_id=location_id, company_id=company_id
        )

        return {
            "authorizationUrl": auth_url,
            "locationId": location_id,
            "companyId": company_id,
        }

    except Exception as e:
        logger.error(f"Error generating authorization URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    OAuth callback endpoint
    GHL redirects here after user authorizes the app

    Example:
        GET /api/v1/oauth/callback?code=AUTH_CODE&state=STATE_DATA
    """
    try:
        # Decode state to get metadata
        state_data = GHLOAuthHelper.decode_state(state) if state else {}
        location_id = state_data.get("locationId")
        company_id = state_data.get("companyId")

        # Exchange code for tokens
        client = GHLClient(access_token="")  # Temporary, just for token exchange
        token_data = await client.exchange_code_for_token(code)

        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 86400)
        token_company_id = token_data.get("companyId") or company_id

        if not all([access_token, refresh_token, token_company_id]):
            raise HTTPException(status_code=400, detail="Invalid token response")

        # Get app configuration
        app = db.query(GHLApplication).filter(
            GHLApplication.app_id == settings.GHL_APP_ID,
            GHLApplication.is_active == True
        ).first()

        if not app:
            raise HTTPException(status_code=400, detail="No active GHL application found")

        # Store agency token
        agency_token = db.query(GHLAgencyToken).filter(
            GHLAgencyToken.company_id == token_company_id,
            GHLAgencyToken.app_id == settings.GHL_APP_ID
        ).first()

        token_expiry = datetime.now() + timedelta(seconds=expires_in)

        if agency_token:
            # Update existing token
            agency_token.access_token = access_token
            agency_token.refresh_token = refresh_token
            agency_token.token_expiry = token_expiry
            agency_token.updated_at = datetime.now()
        else:
            # Create new token
            agency_token = GHLAgencyToken(
                company_id=token_company_id,
                app_id=settings.GHL_APP_ID,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
            db.add(agency_token)

        db.commit()

        # If this is a company-level install, sync all locations
        if token_company_id and not location_id:
            client_with_token = GHLClient(access_token=access_token)
            locations = await client_with_token.get_installed_locations(
                company_id=token_company_id,
                app_id=settings.GHL_APP_ID
            )

            # Store/update locations
            for loc_data in locations:
                loc_id = loc_data.get("_id")
                loc_name = loc_data.get("name", f"Location {loc_id}")

                location = db.query(Location).filter(
                    Location.location_id == loc_id
                ).first()

                if location:
                    location.name = loc_name
                    location.is_installed = True
                    location.company_id = token_company_id
                    location.app_id = settings.GHL_APP_ID
                else:
                    location = Location(
                        location_id=loc_id,
                        name=loc_name,
                        is_installed=True,
                        company_id=token_company_id,
                        app_id=settings.GHL_APP_ID,
                    )
                    db.add(location)

            db.commit()

        # Redirect to frontend with success
        redirect_url = f"{settings.FRONTEND_URL}/oauth/success?companyId={token_company_id}"
        if location_id:
            redirect_url += f"&locationId={location_id}"

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        # Redirect to frontend with error
        error_url = f"{settings.FRONTEND_URL}/oauth/error?message={str(e)}"
        return RedirectResponse(url=error_url)


@router.get("/status")
async def oauth_status(
    location_id: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Check OAuth connection status

    Example:
        GET /api/v1/oauth/status?companyId=ABC123
    """
    try:
        if not company_id and not location_id:
            raise HTTPException(
                status_code=400,
                detail="Either company_id or location_id is required"
            )

        # Check for agency token
        if company_id:
            token = db.query(GHLAgencyToken).filter(
                GHLAgencyToken.company_id == company_id,
                GHLAgencyToken.app_id == settings.GHL_APP_ID
            ).first()

            if token:
                is_expired = token.token_expiry < datetime.now() if token.token_expiry else False

                return {
                    "connected": True,
                    "companyId": company_id,
                    "appId": settings.GHL_APP_ID,
                    "tokenExpiry": token.token_expiry.isoformat() if token.token_expiry else None,
                    "isExpired": is_expired,
                    "lastUpdated": token.updated_at.isoformat(),
                }

        return {
            "connected": False,
            "companyId": company_id,
            "locationId": location_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_token(
    company_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Manually refresh an access token

    Example:
        POST /api/v1/oauth/refresh?company_id=ABC123
    """
    try:
        # Get current token
        token = db.query(GHLAgencyToken).filter(
            GHLAgencyToken.company_id == company_id,
            GHLAgencyToken.app_id == settings.GHL_APP_ID
        ).first()

        if not token:
            raise HTTPException(status_code=404, detail="No token found for company")

        # Refresh the token
        client = GHLClient(access_token=token.access_token)
        new_token_data = await client.refresh_access_token(token.refresh_token)

        if not new_token_data:
            raise HTTPException(status_code=400, detail="Failed to refresh token")

        # Update stored token
        token.access_token = new_token_data.get("access_token")
        token.refresh_token = new_token_data.get("refresh_token", token.refresh_token)
        token.token_expiry = datetime.now() + timedelta(
            seconds=new_token_data.get("expires_in", 86400)
        )
        token.updated_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": "Token refreshed successfully",
            "tokenExpiry": token.token_expiry.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=str(e))
