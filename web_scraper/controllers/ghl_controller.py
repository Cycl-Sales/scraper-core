from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import datetime, timedelta
import requests
from urllib.parse import urljoin

_logger = logging.getLogger(__name__)

GHL_CLIENT_ID = '6834710f642d2825854891ec-mb55bysi'
GHL_CLIENT_SECRET = '39812a82-545f-4ac4-ace4-0c0e8f3c12c8'
GHL_REDIRECT_URI = 'https://ed4a-180-191-20-127.ngrok-free.app/app-install'
GHL_TOKEN_URL = 'https://services.leadconnectorhq.com/oauth/token'
GHL_INSTALLED_LOCATIONS_URL = 'https://services.leadconnectorhq.com/oauth/installedLocations'


class GHLController(http.Controller):
    @http.route('/app-install', type='http', auth='public', methods=['GET'], csrf=False)
    def app_install(self, **kwargs):
        code = kwargs.get('code')
        if not code:
            return 'Missing code parameter in request', 400
        try:
            # Exchange code for tokens
            payload = {
                'client_id': GHL_CLIENT_ID,
                'client_secret': GHL_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'user_type': 'Company',
                'redirect_uri': GHL_REDIRECT_URI,
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            resp = requests.post(GHL_TOKEN_URL, data=payload, headers=headers)
            _logger.info(f"GHL token exchange response: {resp.status_code} {resp.text}")
            if resp.status_code != 200:
                return f'Failed to exchange code for tokens: {resp.text}', 400
            token_data = resp.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in')
            company_id = token_data.get('companyId')
            if not all([access_token, refresh_token, expires_in, company_id]):
                return request.render('web_scraper.ghl_install_error', {'error': f'Missing fields in token response: {token_data}'})
            token_expiry = datetime.now() + timedelta(seconds=int(expires_in))
            # Store or update the agency token
            AgencyToken = request.env['ghl.agency.token'].sudo()
            agency = AgencyToken.search([('company_id', '=', company_id)], limit=1)
            vals = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expiry': token_expiry,
                'company_id': company_id,
            }
            if agency:
                agency.write(vals)
            else:
                AgencyToken.create(vals)
            # Fetch installed locations
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            resp = requests.get(GHL_INSTALLED_LOCATIONS_URL, headers=headers)
            if resp.status_code == 200:
                locations = resp.json().get('locations', [])
                Location = request.env['ghl.location'].sudo()
                for loc in locations:
                    location_id = loc.get('locationId')
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
            else:
                _logger.error(f"Failed to fetch installed locations: {resp.status_code} {resp.text}")
            return request.render('web_scraper.ghl_install_success', {'message': 'GHL Agency App Installation Successful! Locations have been synced.'})
        except Exception as e:
            _logger.error(f"Error in GHL app installation: {str(e)}")
            return f'Error: {str(e)}', 500

    @http.route('/app-events', type='http', auth='public', methods=['POST'], csrf=False)
    def app_events(self, **kwargs):
        try:
            data = request.httprequest.get_data()
            _logger.info(f"Received GHL app event: {data}")
            try:
                event = json.loads(data)
            except Exception as e:
                _logger.error(f"Failed to parse event JSON: {e}")
                return Response('Invalid JSON', status=400)
            event_type = event.get('type')
            location_id = event.get('locationId')
            company_id = event.get('companyId')
            user_id = event.get('userId')
            timestamp_str = event.get('timestamp')
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
            request.env['web.scraper.event.log'].sudo().create({
                'name': name,
                'event_type': event_type,
                'payload': data.decode() if isinstance(data, bytes) else str(data),
                'location_id': location_id,
                'company_id': company_id,
                'user_id': user_id,
                'timestamp': timestamp,
            })
            # Update GHL Location is_installed
            if event_type == 'INSTALL' and location_id:
                loc = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
                if loc:
                    loc.write({'is_installed': True})
                else:
                    request.env['ghl.location'].sudo().create({
                        'location_id': location_id,
                        'name': f'GHL Location {location_id}',
                        'is_installed': True,
                    })
            elif event_type == 'UNINSTALL' and location_id:
                loc = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
                if loc:
                    loc.write({'is_installed': False})
            return Response('Event received', status=200)
        except Exception as e:
            _logger.error(f"Error in /app-events: {str(e)}")
            return Response(f'Error: {str(e)}', status=500)
