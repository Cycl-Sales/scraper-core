"""
GHL API Client
Handles all interactions with GoHighLevel API
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings


class GHLClient:
    """GoHighLevel API Client"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = settings.GHL_API_BASE_URL
        self.api_version = settings.GHL_API_VERSION

    def _get_headers(self) -> Dict[str, str]:
        """Get standard API headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Version": self.api_version,
            "Accept": "application/json",
        }

    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 86400,
                "companyId": "..."
            }
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.GHL_CLIENT_ID,
                    "client_secret": settings.GHL_CLIENT_SECRET,
                    "redirect_uri": settings.GHL_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                return response.json()
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an expired access token

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 86400
            }
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.GHL_CLIENT_ID,
                    "client_secret": settings.GHL_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                return response.json()
            return None

    async def get_location_info(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a location"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/locations/{location_id}",
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                return response.json()
            return None

    async def get_installed_locations(
        self, company_id: str, app_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all locations where the app is installed

        Returns:
            List of location objects
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/installedLocations",
                params={
                    "companyId": company_id,
                    "appId": app_id,
                    "isInstalled": True,
                    "limit": limit,
                },
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("locations", [])
            return []

    async def get_location_token(
        self, company_id: str, location_id: str
    ) -> Optional[str]:
        """
        Exchange agency token for location-specific token

        Returns:
            Location access token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/locationToken",
                data={
                    "companyId": company_id,
                    "locationId": location_id,
                },
                headers={
                    **self._get_headers(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            return None

    async def search_contacts(
        self,
        location_id: str,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Search contacts for a location

        Returns:
            {
                "contacts": [...],
                "total": 1234,
                "count": 100
            }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/contacts/search",
                json={
                    "locationId": location_id,
                    "page": page,
                    "pageLimit": limit,
                    "sort": [{"field": "dateUpdated", "direction": "desc"}],
                },
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                return response.json()
            return {"contacts": [], "total": 0, "count": 0}

    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a contact"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/contacts/{contact_id}",
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                return response.json()
            return None

    async def get_opportunities(
        self, location_id: str, contact_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get opportunities for a location or contact"""
        params = {"location_id": location_id}
        if contact_id:
            params["contact_id"] = contact_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/opportunities/search",
                params=params,
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("opportunities", [])
            return []

    async def get_tasks(
        self, location_id: str, contact_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks for a location or contact"""
        params = {"locationId": location_id}
        if contact_id:
            params["contactId"] = contact_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tasks/search",
                params=params,
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("tasks", [])
            return []


class GHLOAuthHelper:
    """Helper methods for GHL OAuth flow"""

    @staticmethod
    def get_authorization_url(
        location_id: Optional[str] = None, company_id: Optional[str] = None
    ) -> str:
        """
        Generate OAuth authorization URL

        Args:
            location_id: Optional location ID to include in state
            company_id: Optional company ID to include in state

        Returns:
            Authorization URL
        """
        import base64
        import json

        # Create state parameter with metadata
        state_data = {
            "locationId": location_id,
            "companyId": company_id,
            "appId": settings.GHL_APP_ID,
            "timestamp": datetime.now().isoformat(),
        }

        # Encode state
        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

        # Build URL
        auth_url = (
            f"https://marketplace.gohighlevel.com/oauth/chooselocation"
            f"?response_type=code"
            f"&client_id={settings.GHL_CLIENT_ID}"
            f"&redirect_uri={settings.GHL_REDIRECT_URI}"
            f"&scope=locations.readonly contacts.readonly opportunities.readonly"
            f"&state={state}"
        )

        return auth_url

    @staticmethod
    def decode_state(state: str) -> Dict[str, Any]:
        """Decode OAuth state parameter"""
        import base64
        import json

        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            return json.loads(decoded)
        except Exception:
            return {}
