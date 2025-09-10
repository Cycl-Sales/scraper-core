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
            # Parse query parameters
            query_params = parse_qs(parsed_url.query) if parsed_url.query else {} 
            
            # Try to parse JSON from request data
            json_data = None
            if request.httprequest.data:
                try:
                    json_data = json.loads(request.httprequest.data.decode()) 
                except Exception as e:
                    # _logger.info(f"Failed to parse JSON from request data: {e}")  # Reduced logging for production
            
            # ===== EXTRACT KEY PARAMETERS =====
            code = kwargs.get('code')
            state = kwargs.get('state')
            location_id = kwargs.get('locationId')
            company_id = kwargs.get('companyId')
            app_id = kwargs.get('appId')
            
            # Also try to get from request.params
            code_from_params = request.params.get('code')
            state_from_params = request.params.get('state')
            location_id_from_params = request.params.get('locationId')
            company_id_from_params = request.params.get('companyId')
            app_id_from_params = request.params.get('appId')
            
            # Also try to get from query string
            code_from_query = query_params.get('code', [None])[0] if query_params else None
            state_from_query = query_params.get('state', [None])[0] if query_params else None
            location_id_from_query = query_params.get('locationId', [None])[0] if query_params else None
            company_id_from_query = query_params.get('companyId', [None])[0] if query_params else None
            app_id_from_query = query_params.get('appId', [None])[0] if query_params else None
            
            # Use the first available value for each parameter
            final_code = code or code_from_params or code_from_query
            final_state = state or state_from_params or state_from_query
            final_location_id = location_id or location_id_from_params or location_id_from_query
            final_company_id = company_id or company_id_from_params or company_id_from_query
            final_app_id = app_id or app_id_from_params or app_id_from_query
            
            
            # ===== COMPREHENSIVE LOGGING END =====
            
            # Use the final parameter values we extracted
            code = final_code
            state = final_state
            location_id = final_location_id
            company_id = final_company_id
            app_id = final_app_id
            
            # Try to decode state parameter if it exists
            state_data = None
            if state:
                try:
                    import base64
                    import json as json_module
                    state_decoded = base64.urlsafe_b64decode(state.encode()).decode()
                    state_data = json_module.loads(state_decoded)
                    
                    # Extract values from decoded state
                    if not location_id and state_data.get('locationId'):
                        location_id = state_data.get('locationId')
                    
                    if not company_id and state_data.get('companyId'):
                        company_id = state_data.get('companyId')
                    
                    if not app_id and state_data.get('appId'):
                        app_id = state_data.get('appId')
                        
                except Exception as e:
                    _logger.info(f"Failed to decode state parameter: {e}")
                    # Fallback: use state as location_id if decoding fails
                    if not location_id:
                        location_id = state
                        _logger.info(f"Using state as location_id (fallback): {location_id}")
            
            # If location_id is not provided, try to extract it from state
            if not location_id and state:
                location_id = state
                _logger.info(f"Using state as location_id: {location_id}")
            
            # If still not found, try companyId (for company-level installs)
            if not location_id and company_id:
                location_id = company_id
                _logger.info(f"Using company_id as location_id: {location_id}")
            
            # As a last resort, try to parse from request.params or request.httprequest.data
            if not location_id:
                _logger.info("Location ID still not found, trying additional sources...")
                # Try to parse from request.params
                location_id = request.params.get('locationId') or request.params.get('companyId') or request.params.get('state')
                _logger.info(f"Location ID from request.params: {location_id}")
                # Try to parse from POST body if available
                if not location_id and request.httprequest.data:
                    try:
                        data = json.loads(request.httprequest.data.decode())
                        location_id = data.get('locationId') or data.get('companyId') or data.get('state')
                        _logger.info(f"Location ID from request data: {location_id}")
                    except Exception as e:
                        _logger.info(f"Failed to parse location ID from request data: {e}")

           
            token_result = self._exchange_code_for_token(code, app_id)

            
            if not token_result:
                return Response(
                    json.dumps({
                        'error': 'Token exchange failed',
                        'message': 'Unable to exchange authorization code for access token',
                        'debug_info': {
                            'code_received': bool(code),
                            'app_id_used': app_id,
                            'location_id': location_id,
                            'company_id': company_id
                        }
                    }),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            access_token, refresh_token = location_token_result
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
                return Response(
                    json.dumps(success_data),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

            # Otherwise, treat as location-level install
            if not location_id:
                # For GHL app installations, we need to store the tokens temporarily
                # and wait for the webhook events to provide the company/location context
                temp_token_key = f"temp_ghl_tokens_{code}"
                
                # Store tokens temporarily (they will be associated with company/location via webhook)
                temp_tokens = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'app_id': app_id,
                    'timestamp': datetime.now().isoformat(),
                    'code': code
                }
                
                # Store in a temporary location (could be Redis, database, or file)
                # For now, we'll use a simple in-memory storage (not production-ready)
                if not hasattr(self, '_temp_tokens'):
                    self._temp_tokens = {}
                
                self._temp_tokens[temp_token_key] = temp_tokens
                
                # Return success response indicating we're waiting for webhook events
                success_data = {
                    'success': True,
                    'message': 'GHL app installation initiated successfully. Waiting for webhook events to complete setup.',
                    'status': 'pending_webhook',
                    'code': code
                }
                
                return Response(
                    json.dumps(success_data),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

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

            return Response(
                json.dumps(success_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return Response(
                json.dumps({
                    'error': 'OAuth callback failed',
                    'message': str(e),
                    'debug_info': {
                        'exception_type': type(e).__name__,
                        'traceback': traceback.format_exc()
                    }
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
            company_id = kwargs.get('companyId')  # Get company_id from parameters
            state = kwargs.get('state')
            app_id = kwargs.get('appId')  # Get app_id from parameters

                # _logger.info(f"OAuth authorize called with - locationId: {location_id}, companyId: {company_id}, appId: {app_id}")  # Reduced logging for production

            if not location_id and not company_id:
                return Response(
                    json.dumps({'error': 'Either Location ID or Company ID is required'}),
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

            # Create a comprehensive state parameter that includes both company and location info
            import base64
            import json as json_module
            
            state_data = {
                'locationId': location_id,
                'companyId': company_id,
                'appId': cyclsales_app.app_id,
                'timestamp': fields.Datetime.now().isoformat()
            }
            
            # Encode state data to avoid URL encoding issues
            state_encoded = base64.urlsafe_b64encode(json_module.dumps(state_data).encode()).decode()
            
            # _logger.info(f"Generated state data: {state_data}")  # Reduced logging for production
            # _logger.info(f"Encoded state: {state_encoded}")  # Reduced logging for production

            # Generate authorization URL using CyclSales app credentials
            redirect_uri = f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/api/dashboard/oauth/callback"
            auth_url = f"https://marketplace.gohighlevel.com/oauth/chooselocation?response_type=code&client_id={cyclsales_app.client_id}&redirect_uri={redirect_uri}&scope=locations.readonly&state={state_encoded}"

            # _logger.info(f"Generated authorization URL: {auth_url}")  # Reduced logging for production

            return Response(
                json.dumps({
                    'authorizationUrl': auth_url,
                    'locationId': location_id,
                    'companyId': company_id,
                    'state': state_encoded,
                    'appId': cyclsales_app.app_id,
                    'appName': cyclsales_app.name,
                    'stateData': state_data
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

    @http.route('/api/dashboard/events', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def ghl_event_webhook(self, **kwargs):
        """
        Endpoint to receive and log GHL event webhooks for debugging and location management.
        Logs all incoming data, parses the event, and manages ghl.location records.
        """
        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )
        
        try:
            raw_data = request.httprequest.data
            json_data = None
            if raw_data:
                try:
                    json_data = json.loads(raw_data.decode())
                except Exception as e:
                    _logger.error(f"Failed to parse JSON: {e}")
            # _logger.info(f"GHL Event Webhook received with kwargs: {kwargs}")  # Reduced logging for production
            # _logger.info(f"Request params: {request.params}")  # Reduced logging for production
            # _logger.info(f"Request data: {raw_data}")  # Reduced logging for production
            # _logger.info(f"Parsed JSON: {json_data}")  # Reduced logging for production
            # print(f"GHL Event Webhook - kwargs: {kwargs}")  # Reduced logging for production
            # print(f"GHL Event Webhook - params: {request.params}")  # Reduced logging for production
            # print(f"GHL Event Webhook - data: {raw_data}")  # Reduced logging for production
            # print(f"GHL Event Webhook - parsed JSON: {json_data}")  # Reduced logging for production

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
            # Check for stored temporary tokens and complete installation
            if event_type == 'INSTALL':
                # _logger.info("=" * 50)  # Reduced logging for production
                # _logger.info("PROCESSING INSTALL EVENT")  # Reduced logging for production
                # _logger.info("=" * 50)  # Reduced logging for production
                # _logger.info(f"Event type: {event_type}")  # Reduced logging for production
                # _logger.info(f"Install type: {json_data.get('installType')}")  # Reduced logging for production
                # _logger.info(f"Company ID: {company_id}")  # Reduced logging for production
                # _logger.info(f"Location ID: {location_id}")  # Reduced logging for production
                # _logger.info(f"App ID: {json_data.get('appId')}")  # Reduced logging for production
                
                # Check if we have stored temporary tokens
                if hasattr(self, '_temp_tokens') and self._temp_tokens:
                    # _logger.info(f"Found {len(self._temp_tokens)} stored temporary tokens")  # Reduced logging for production
                    
                    # Look for tokens that match this installation
                    matching_tokens = None
                    for temp_key, temp_data in self._temp_tokens.items():
                        # _logger.info(f"Checking temp token key: {temp_key}")  # Reduced logging for production
                        # _logger.info(f"Temp token app_id: {temp_data.get('app_id')}")  # Reduced logging for production
                        # _logger.info(f"Event app_id: {json_data.get('appId')}")  # Reduced logging for production
                        
                        # Match by app_id
                        if temp_data.get('app_id') == json_data.get('appId'):
                            matching_tokens = temp_data
                            # _logger.info(f"Found matching tokens for app_id: {json_data.get('appId')}")  # Reduced logging for production
                            break
                    
                    if matching_tokens:
                        # _logger.info("=" * 50)  # Reduced logging for production
                        # _logger.info("COMPLETING GHL INSTALLATION")  # Reduced logging for production
                        # _logger.info("=" * 50)  # Reduced logging for production
                        
                        access_token = matching_tokens['access_token']
                        refresh_token = matching_tokens['refresh_token']
                        app_id = matching_tokens['app_id']
                        
                        _logger.info(f"Using stored tokens for app_id: {app_id}")
                        _logger.info(f"Company ID: {company_id}")
                        _logger.info(f"Location ID: {location_id}")
                        
                        # Store the credentials based on installation type
                        if json_data.get('installType') == 'Company':
                            # Company-level installation
                            if company_id:
                                # Store company-level credentials
                                company_cred = request.env['ghl.company.credential'].sudo().search([
                                    ('company_id', '=', company_id)
                                ], limit=1)
                                
                                if company_cred:
                                    company_cred.write({
                                        'access_token': access_token,
                                        'refresh_token': refresh_token,
                                        'app_id': app_id,
                                        'last_updated': fields.Datetime.now()
                                    })
                                    _logger.info(f"Updated company credentials for company_id: {company_id}")
                                else:
                                    request.env['ghl.company.credential'].sudo().create({
                                        'company_id': company_id,
                                        'access_token': access_token,
                                        'refresh_token': refresh_token,
                                        'app_id': app_id,
                                        'last_updated': fields.Datetime.now()
                                    })
                                    _logger.info(f"Created company credentials for company_id: {company_id}")
                            else:
                                _logger.warning("Company-level installation but no company_id provided")
                        
                        elif json_data.get('installType') == 'Location':
                            # Location-level installation
                            if location_id:
                                # Store location-level credentials
                                location_cred = request.env['ghl.location.credential'].sudo().search([
                                    ('location_id', '=', location_id)
                                ], limit=1)
                                
                                if location_cred:
                                    location_cred.write({
                                        'access_token': access_token,
                                        'refresh_token': refresh_token,
                                        'app_id': app_id,
                                        'last_updated': fields.Datetime.now()
                                    })
                                    _logger.info(f"Updated location credentials for location_id: {location_id}")
                                else:
                                    request.env['ghl.location.credential'].sudo().create({
                                        'location_id': location_id,
                                        'access_token': access_token,
                                        'refresh_token': refresh_token,
                                        'app_id': app_id,
                                        'last_updated': fields.Datetime.now()
                                    })
                                    _logger.info(f"Created location credentials for location_id: {location_id}")
                            else:
                                _logger.warning("Location-level installation but no location_id provided")
                        
                        # Clean up temporary tokens
                        del self._temp_tokens[temp_key]
                        _logger.info("Cleaned up temporary tokens")
                        
                        # Update or create ghl.location record
                        if location_id:
                            location_record = request.env['ghl.location'].sudo().search([
                                ('location_id', '=', location_id)
                            ], limit=1)
                            
                            if location_record:
                                location_record.write({
                                    'is_installed': True,
                                    'last_updated': fields.Datetime.now()
                                })
                                _logger.info(f"Updated ghl.location record for location_id: {location_id}")
                            else:
                                request.env['ghl.location'].sudo().create({
                                    'location_id': location_id,
                                    'company_id': company_id,
                                    'is_installed': True,
                                    'last_updated': fields.Datetime.now()
                                })
                                _logger.info(f"Created ghl.location record for location_id: {location_id}")
                        
                        _logger.info("GHL installation completed successfully")
                        return Response(
                            json.dumps({'success': True, 'message': 'Installation completed'}),
                            content_type='application/json',
                            status=200,
                            headers=get_cors_headers(request)
                        )
                    else:
                        _logger.warning(f"No matching temporary tokens found for app_id: {json_data.get('appId')}")
                else:
                    _logger.warning("No temporary tokens stored")
            
            # Return success response
            return Response(
                json.dumps({'success': True, 'message': 'Event processed'}),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )
            
        except Exception as e:
            _logger.error(f"Error processing GHL event webhook: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

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
