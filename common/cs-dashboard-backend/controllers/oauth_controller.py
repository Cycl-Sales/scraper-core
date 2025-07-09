# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request, Response
import json
import logging
import requests
from urllib.parse import parse_qs, urlparse
from datetime import timedelta, datetime
from .cors_utils import get_cors_headers

_logger = logging.getLogger(__name__)


class GHLOAuthController(http.Controller):

    @http.route('/api/dashboard/oauth/callback', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def ghl_oauth_callback(self, **kwargs):
        """
        Handle GHL OAuth callback for application installation
        This endpoint receives the authorization code from GHL after user installs the app
        """
        try:
            _logger.info(f"GHL OAuth callback received with kwargs: {kwargs}")
            _logger.info(f"Request params: {request.params}")
            _logger.info(f"Request data: {request.httprequest.data}")

            # Get the authorization code from the callback
            code = kwargs.get('code')
            state = kwargs.get('state')
            location_id = kwargs.get('locationId')
            company_id = kwargs.get('companyId')
            app_id = kwargs.get('appId')  # Get app_id from callback parameters
            print(f"Kwargs: {kwargs}")
            
            # If location_id is not provided, try to extract it from state
            if not location_id and state:
                location_id = state
            
            # If still not found, try companyId (for company-level installs)
            if not location_id and company_id:
                location_id = company_id
            
            # As a last resort, try to parse from request.params or request.httprequest.data
            if not location_id:
                # Try to parse from request.params
                location_id = request.params.get('locationId') or request.params.get('companyId') or request.params.get('state')
                # Try to parse from POST body if available
                if not location_id and request.httprequest.data:
                    try:
                        data = json.loads(request.httprequest.data.decode())
                        location_id = data.get('locationId') or data.get('companyId') or data.get('state')
                    except Exception:
                        pass

            # Exchange authorization code for access token
            token_result = self._exchange_code_for_token(code, app_id)

            if not token_result:
                _logger.error("Failed to exchange authorization code for access token")
                return Response(
                    json.dumps({
                        'error': 'Token exchange failed',
                        'message': 'Unable to exchange authorization code for access token'
                    }),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            access_token, refresh_token = token_result

            # If only companyId is present (no locationId), treat as company-level install
            if company_id and (not kwargs.get('locationId') and not state):
                # Store the agency token
                self._store_ghl_credentials(company_id, access_token, refresh_token, state, app_id)
                # Fetch and sync all locations for this company
                synced_locations = self._sync_all_company_locations(company_id, access_token, app_id)
                success_data = {
                    'success': True,
                    'message': 'GHL company-level installation successful. Locations have been synced.',
                    'companyId': company_id,
                    'locations': synced_locations,
                    'redirectUrl': self._get_redirect_url(company_id)
                }
                _logger.info(f"GHL OAuth completed successfully for company: {company_id}")
                return Response(
                    json.dumps(success_data),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

            # Otherwise, treat as location-level install
            if not location_id:
                _logger.error("No company/location ID received in OAuth callback")
                return Response(
                    json.dumps({
                        'error': 'No company/location ID received',
                        'message': 'The OAuth callback is missing the required company/location ID'
                    }),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            _logger.info(f"OAuth callback - Code: {code[:10]}..., State: {state}, Location: {location_id}, App: {app_id}")

            # Store the access token and location information
            self._store_ghl_credentials(location_id, access_token, refresh_token, state, app_id)

            # Get location details from GHL API
            location_info = self._get_location_info(access_token, location_id, app_id)

            # Create or update GHL location record
            self._create_or_update_location(location_id, location_info, access_token)

            # Return success response
            success_data = {
                'success': True,
                'message': 'GHL application installed successfully',
                'locationId': location_id,
                'locationName': location_info.get('name', 'Unknown Location'),
                'redirectUrl': self._get_redirect_url(location_id)
            }

            _logger.info(f"GHL OAuth completed successfully for location: {location_id}")

            return Response(
                json.dumps(success_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error in GHL OAuth callback: {str(e)}")
            return Response(
                json.dumps({
                    'error': 'OAuth callback failed',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    def _exchange_code_for_token(self, code, app_id=None):
        """
        Exchange authorization code for access token using GHL API
        """
        try:
            # Get active CyclSales application configuration
            if app_id:
                # Use specific app if app_id is provided
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('app_id', '=', app_id),
                    ('is_active', '=', True)
                ], limit=1)
            else:
                # Get the first active application
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)
            
            if not cyclsales_app:
                _logger.error("No active CyclSales application configuration found")
                return None

            # GHL OAuth token endpoint (using default GHL endpoint)
            token_url = "https://services.leadconnectorhq.com/oauth/token"

            # Get app credentials from CyclSales application
            client_id = cyclsales_app.client_id
            client_secret = cyclsales_app.client_secret
            redirect_uri = f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/api/dashboard/oauth/callback"

            _logger.info(f"Using CyclSales app - Name: {cyclsales_app.name}, Client ID: {client_id[:10]}..., Redirect URI: {redirect_uri}")

            if not all([client_id, client_secret]):
                _logger.error("Missing CyclSales application configuration")
                return None

            # Prepare token exchange request
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            # Make token exchange request
            response = requests.post(token_url, data=token_data, headers=headers)

            if response.status_code == 200:
                token_response = response.json()
                access_token = token_response.get('access_token')
                refresh_token = token_response.get('refresh_token', '')
                
                # Update the CyclSales application with the new tokens
                cyclsales_app.write({
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_expiry': fields.Datetime.now() + timedelta(hours=1),  # Default 1 hour expiry
                })
                
                _logger.info(f"Successfully exchanged code for access token for app: {cyclsales_app.name}")
                return access_token, refresh_token
            else:
                _logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            _logger.error(f"Error exchanging code for token: {str(e)}")
            return None

    def _store_ghl_credentials(self, location_id, access_token, refresh_token, state=None, app_id=None):
        """
        Store GHL credentials in the system using CyclSales application model
        """
        try:
            # Get active CyclSales application
            if app_id:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('app_id', '=', app_id),
                    ('is_active', '=', True)
                ], limit=1)
            else:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)
            
            if not cyclsales_app:
                _logger.error("No active CyclSales application found")
                return
            
            app_id = cyclsales_app.app_id
            app_name = cyclsales_app.name
            
            # Check if GHL agency token record exists for this app
            ghl_token = request.env['ghl.agency.token'].sudo().search([
                ('company_id', '=', location_id),
                ('app_id', '=', app_id),
            ], limit=1)

            token_data = {
                'company_id': location_id,
                'app_id': app_id,
                'app_name': app_name,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expiry': fields.Datetime.now() + timedelta(hours=1),  # Default 1 hour expiry
            }

            if ghl_token:
                # Update existing record
                ghl_token.write(token_data)
                _logger.info(f"Updated GHL token for location: {location_id} (app: {app_name})")
            else:
                # Create new record
                request.env['ghl.agency.token'].sudo().create(token_data)
                _logger.info(f"Created new GHL token for location: {location_id} (app: {app_name})")

        except Exception as e:
            _logger.error(f"Error storing GHL credentials: {str(e)}")

    def _get_location_info(self, access_token, location_id, app_id=None):
        """
        Get location information from GHL API
        """
        try:
            # Get active CyclSales application for API version
            if app_id:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('app_id', '=', app_id),
                    ('is_active', '=', True)
                ], limit=1)
            else:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)
            
            if not cyclsales_app:
                _logger.error("No active CyclSales application found")
                return {'name': 'Unknown Location'}

            # GHL locations API endpoint (using default GHL API base URL)
            api_base_url = "https://services.leadconnectorhq.com"
            location_url = f"{api_base_url}/locations/{location_id}"

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Version': '2021-07-28'  # Default GHL API version
            }

            response = requests.get(location_url, headers=headers)

            if response.status_code == 200:
                location_data = response.json()
                _logger.info(f"Retrieved location info for: {location_id}")
                return location_data
            else:
                _logger.error(f"Failed to get location info: {response.status_code}")
                return {'name': 'Unknown Location'}

        except Exception as e:
            _logger.error(f"Error getting location info: {str(e)}")
            return {'name': 'Unknown Location'}

    def _create_or_update_location(self, location_id, location_info, access_token):
        """
        Create or update GHL location record in the system
        """
        try:
            # Check if location exists
            ghl_location = request.env['ghl.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            location_data = {
                'location_id': location_id,
                'name': location_info.get('name', 'Unknown Location'),
                'active': True,
            }

            if ghl_location:
                # Update existing location
                ghl_location.write(location_data)
                _logger.info(f"Updated GHL location: {location_id}")
            else:
                # Create new location
                request.env['ghl.location'].sudo().create(location_data)
                _logger.info(f"Created new GHL location: {location_id}")

        except Exception as e:
            _logger.error(f"Error creating/updating location: {str(e)}")

    def _get_redirect_url(self, location_id):
        """
        Generate redirect URL for successful installation
        """
        # You can customize this based on your frontend URL structure
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/dashboard?locationId={location_id}&installed=true"

    @http.route('/api/dashboard/oauth/authorize', type='http', auth='none', methods=['GET'], csrf=False)
    def ghl_oauth_authorize(self, **kwargs):
        """
        Generate OAuth authorization URL for GHL app installation
        """
        try:
            location_id = kwargs.get('locationId')
            state = kwargs.get('state')
            app_id = kwargs.get('appId')  # Get app_id from parameters

            if not location_id:
                return Response(
                    json.dumps({'error': 'Location ID is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get active CyclSales application configuration
            if app_id:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('app_id', '=', app_id),
                    ('is_active', '=', True)
                ], limit=1)
            else:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)
            
            if not cyclsales_app:
                return Response(
                    json.dumps({'error': 'No active CyclSales application configuration found'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Generate authorization URL using CyclSales app credentials
            redirect_uri = f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/api/dashboard/oauth/callback"
            auth_url = f"https://marketplace.gohighlevel.com/oauth/chooselocation?response_type=code&client_id={cyclsales_app.client_id}&redirect_uri={redirect_uri}&scope=locations.readonly&state={location_id}"

            return Response(
                json.dumps({
                    'authorizationUrl': auth_url,
                    'locationId': location_id,
                    'state': state,
                    'appId': cyclsales_app.app_id,
                    'appName': cyclsales_app.name
                }),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error generating authorization URL: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/oauth/status', type='http', auth='none', methods=['GET'], csrf=False)
    def ghl_oauth_status(self, **kwargs):
        """
        Check OAuth status for a location
        """
        try:
            location_id = kwargs.get('locationId')
            app_id = kwargs.get('appId')  # Get app_id from parameters

            if not location_id:
                return Response(
                    json.dumps({'error': 'Location ID is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get active CyclSales application
            if app_id:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('app_id', '=', app_id),
                    ('is_active', '=', True)
                ], limit=1)
            else:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)
            
            app_id = cyclsales_app.app_id if cyclsales_app else None
            
            # Check if location has active token for this app
            ghl_token = request.env['ghl.agency.token'].sudo().search([
                ('company_id', '=', location_id),
                ('app_id', '=', app_id)
            ], limit=1)

            status_data = {
                'locationId': location_id,
                'appId': app_id,
                'appName': cyclsales_app.name if cyclsales_app else None,
                'isConnected': bool(ghl_token),
                'lastUpdated': ghl_token.create_date.isoformat() if ghl_token else None
            }

            return Response(
                json.dumps(status_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error checking OAuth status: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/events', type='json', auth='none', methods=['POST'], csrf=False)
    def ghl_event_webhook(self, **kwargs):
        """
        Endpoint to receive and log GHL event webhooks for debugging and location management.
        Logs all incoming data, parses the event, and manages ghl.location records.
        """
        try:
            raw_data = request.httprequest.data
            json_data = None
            if raw_data:
                try:
                    json_data = json.loads(raw_data.decode())
                except Exception as e:
                    _logger.error(f"Failed to parse JSON: {e}")
            _logger.info(f"GHL Event Webhook received with kwargs: {kwargs}")
            _logger.info(f"Request params: {request.params}")
            _logger.info(f"Request data: {raw_data}")
            _logger.info(f"Parsed JSON: {json_data}")
            print(f"GHL Event Webhook - kwargs: {kwargs}")
            print(f"GHL Event Webhook - params: {request.params}")
            print(f"GHL Event Webhook - data: {raw_data}")
            print(f"GHL Event Webhook - parsed JSON: {json_data}")

            # --- Event Management Logic (similar to ghl_controller.py) ---
            event_type = json_data.get('type') if json_data else None
            location_id = json_data.get('locationId') if json_data else None
            company_id = json_data.get('companyId') if json_data else None
            user_id = json_data.get('userId') if json_data else None
            timestamp_str = json_data.get('timestamp') if json_data else None
            timestamp = False
            if timestamp_str:
                try:
                    if '.' in timestamp_str:
                        timestamp = datetime.strptime(timestamp_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
                    else:
                        timestamp = datetime.strptime(timestamp_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                except Exception as e:
                    _logger.error(f"Failed to parse timestamp: {e}")
                    timestamp = False
            name = f"{event_type or 'Event'} - {location_id or ''}"
            # Log the event (if you have a model for this, otherwise just log)
            try:
                request.env['web.scraper.event.log'].sudo().create({
                    'name': name,
                    'event_type': event_type,
                    'payload': raw_data.decode() if isinstance(raw_data, bytes) else str(raw_data),
                    'location_id': location_id,
                    'company_id': company_id,
                    'user_id': user_id,
                    'timestamp': timestamp,
                })
            except Exception as e:
                _logger.warning(f"Could not log event to web.scraper.event.log: {e}")
            # Update GHL Location is_installed
            GHLLocation = request.env['ghl.location'].sudo()
            if event_type == 'INSTALL' and location_id:
                loc = GHLLocation.search([('location_id', '=', location_id)], limit=1)
                if loc:
                    loc.write({'is_installed': True})
                else:
                    GHLLocation.create({
                        'location_id': location_id,
                        'name': f'GHL Location {location_id}',
                        'is_installed': True,
                    })
            elif event_type == 'UNINSTALL' and location_id:
                loc = GHLLocation.search([('location_id', '=', location_id)], limit=1)
                if loc:
                    loc.write({'is_installed': False})
            return {
                'success': True,
                'message': 'Event received and processed',
                'received_kwargs': kwargs,
                'received_params': dict(request.params),
                'received_data': raw_data.decode() if raw_data else None,
                'received_json': json_data,
            }
        except Exception as e:
            _logger.error(f"Error in GHL Event Webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/dashboard/locations', type='http', auth='none', methods=['GET'], csrf=False)
    def get_ghl_locations(self, **kwargs):
        try:
            _logger.info("Starting get_ghl_locations endpoint")
            app_id = kwargs.get('appId')  # Get app_id from parameters
            
            # Get active CyclSales application
            if app_id:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('app_id', '=', app_id),
                    ('is_active', '=', True)
                ], limit=1)
            else:
                cyclsales_app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)
            
            app_id = cyclsales_app.app_id if cyclsales_app else None
            _logger.info(f"CyclSales app found: {cyclsales_app}, app_id: {app_id}")
            print(f"App ID: {app_id}")
            
            agency_token = request.env['ghl.agency.token'].sudo().search([
                ('app_id', '=', app_id)
            ], order='create_date desc', limit=1)
            _logger.info(f"Agency token found: {agency_token}")
            print(f"Agency token: {agency_token}")
            
            if not agency_token or not agency_token.access_token:
                _logger.error("No valid agency token found")
                return Response(
                    json.dumps({'success': False, 'error': 'No valid agency token found.'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get the company_id from the agency token
            company_id = agency_token.company_id
            _logger.info(f"Company ID: {company_id}")
            print(f"Company ID: {company_id}")
            
            # Use the correct GHL API endpoint for installed locations
            url = f"https://services.leadconnectorhq.com/oauth/installedLocations?isInstalled=true&companyId={company_id}&appId={app_id}"
            _logger.info(f"Calling GHL API: {url}")
            print(f"Calling GHL API: {url}")
            
            headers = {
                'Authorization': f'Bearer {agency_token.access_token}',
                'Version': '2021-07-28'  # Default GHL API version
            }
            _logger.info(f"Headers: {headers}")
            print(f"Headers: {headers}")
            
            resp = requests.get(url, headers=headers)
            _logger.info(f"GHL API response: {resp.status_code} - {resp.text}")
            print(f"GHL API response: {resp.status_code} - {resp.text}")
            if resp.status_code == 200:
                return Response(
                    json.dumps({'success': True, 'locations': resp.json()}),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )
            else:
                return Response(
                    json.dumps({'success': False, 'error': f"Failed to fetch locations: {resp.status_code} {resp.text}"}),
                    content_type='application/json',
                    status=resp.status_code,
                    headers=get_cors_headers(request)
                )
        except Exception as e:
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    def _sync_all_company_locations(self, company_id, access_token, app_id=None):
        """
        Fetch and sync all installed locations for a company (company-level install)
        """
        try:
            app_id = app_id or ''
            url = f'https://services.leadconnectorhq.com/oauth/installedLocations?isInstalled=true&companyId={company_id}&appId={app_id}'
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Version': '2021-07-28',
            }
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                locations = resp.json().get('locations', [])
                Location = request.env['ghl.location'].sudo()
                synced = []
                for loc in locations:
                    location_id = loc.get('_id')
                    name = loc.get('name') or f'GHL Location {location_id}'
                    rec = Location.search([('location_id', '=', location_id)], limit=1)
                    vals = {
                        'location_id': location_id,
                        'name': name,
                        'is_installed': True,
                    }
                    if rec:
                        rec.write(vals)
                    else:
                        Location.create(vals)
                    synced.append({'location_id': location_id, 'name': name})
                return synced
            else:
                _logger.error(f"Failed to fetch installed locations: {resp.status_code} {resp.text}")
                return []
        except Exception as e:
            _logger.error(f"Error syncing company locations: {str(e)}")
            return []


class CORSPreflightOAuthController(http.Controller):
    @http.route('/api/dashboard/oauth/<path:anything>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def cors_preflight_oauth(self, **kwargs):
        """Handle CORS preflight requests for OAuth endpoints"""
        return Response(
            "",
            status=200,
            headers=get_cors_headers(request)
        )
