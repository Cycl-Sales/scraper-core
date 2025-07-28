# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging
import requests
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class CyclSalesOAuthController(http.Controller):
    @http.route('/cs-vision/oauth', type='http', auth='none', methods=['GET'], csrf=False)
    def cs_vision_oauth(self, **kwargs):
        code = kwargs.get('code')
        if not code:
            _logger.error('[CSVisionOAuth] Missing code parameter in request')
            return Response('Missing code parameter in request', status=400)
        try:
            # Dynamically fetch credentials from cyclsales.application
            APP_ID = '684c5cc0736d09f78555981f'
            CyclApp = request.env['cyclsales.application'].sudo()
            app = CyclApp.search([('app_id', '=', APP_ID)], limit=1)
            if not app:
                _logger.error(f'[CSVisionOAuth] No cyclsales.application found for app_id={APP_ID}')
                return Response(f'No application found for app_id={APP_ID}', status=400)
            CLIENT_ID = app.client_id
            CLIENT_SECRET = app.client_secret
            REDIRECT_URI = 'https://97412a74865a.ngrok-free.app'
            TOKEN_URL = 'https://services.leadconnectorhq.com/oauth/token'

            payload = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'user_type': 'Company',
                'redirect_uri': REDIRECT_URI,
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            resp = requests.post(TOKEN_URL, data=payload, headers=headers)
            _logger.info(f"[CSVisionOAuth] Token exchange response: {resp.status_code} {resp.text}")
            if resp.status_code != 200:
                return Response(f'Failed to exchange code for tokens: {resp.text}', status=400)
            token_data = resp.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in')
            # Calculate expiry datetime string
            token_expiry = None
            if expires_in:
                try:
                    token_expiry = (datetime.utcnow() + timedelta(seconds=int(expires_in))).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    _logger.error(f"[CSVisionOAuth] Error calculating token_expiry: {e}")

            company_id = token_data.get('companyId')
            location_id = token_data.get('locationId')
            # Always use app_id from the application record
            app_id = app.app_id

            if not all([access_token, refresh_token, expires_in]):
                _logger.error(f"[CSVisionOAuth] Missing required fields in token response: {token_data}")
                return Response('Missing required fields in token response', status=400)

            # Update the cyclsales.application record
            app.write({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expiry': token_expiry,
            })
            _logger.info(f"[CSVisionOAuth] Updated cyclsales.application id={app.id}")

            # Always call fetch_and_sync_installed_locations if company_id is present
            if company_id:
                try:
                    app.fetch_and_sync_installed_locations(company_id)
                    _logger.info(f"[CSVisionOAuth] Synced installed locations for app_id={app_id}, company_id={company_id}")
                except Exception as e:
                    _logger.error(f"[CSVisionOAuth] Error syncing installed locations: {str(e)}")
            else:
                _logger.warning("[CSVisionOAuth] Cannot sync installed locations: company_id is missing.")

            # Create or update installed.location for this specific location
            if location_id and company_id:
                InstalledLocation = request.env['installed.location'].sudo()
                location = InstalledLocation.search([
                    ('location_id', '=', location_id),
                    ('company_id', '=', company_id),
                    ('app_id', '=', app_id)
                ], limit=1)
                vals = {
                    'location_id': location_id,
                    'company_id': company_id,
                    'app_id': app_id,
                    'is_installed': True,
                }
                if location:
                    location.write(vals)
                    _logger.info(f"[CSVisionOAuth] Updated installed.location id={location.id}")
                else:
                    location = InstalledLocation.create(vals)
                    _logger.info(f"[CSVisionOAuth] Created installed.location id={location.id}")
            else:
                _logger.warning("[CSVisionOAuth] Cannot create/update installed.location: location_id or company_id is missing.")

            return Response('App installation successful! You may close this window.', status=200)
        except Exception as e:
            _logger.error(f"[CSVisionOAuth] Error in OAuth install: {str(e)}", exc_info=True)
            return Response(f'Error: {str(e)}', status=500) 