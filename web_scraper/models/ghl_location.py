from odoo import models, fields, api
import logging
from datetime import datetime, timedelta
import requests
from odoo.exceptions import ValidationError
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)

GHL_CLIENT_ID = '6834710f642d2825854891ec-mb55bysi'
GHL_CLIENT_SECRET = '39812a82-545f-4ac4-ace4-0c0e8f3c12c8'
GHL_TOKEN_URL = 'https://services.leadconnectorhq.com/oauth/token'
GHL_REDIRECT_URI = 'https://ed4a-180-191-20-127.ngrok-free.app/app-install'

class GHLLocation(models.Model):
    _name = 'ghl.location'
    _description = 'GHL Location'
    _order = 'name'

    name = fields.Char(string='Location Name', required=True)
    location_id = fields.Char(string='GHL Location ID', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Created On', readonly=True)
    last_sync_date = fields.Datetime(string='Last Sync Date')
    notes = fields.Text(string='Notes')
    is_installed = fields.Boolean(string='Is Installed', default=False)
    market_location_id = fields.Many2one('market.location', string='Market Location', ondelete='restrict')

    _sql_constraints = [
        ('location_id_uniq', 'unique(location_id)', 'GHL Location ID must be unique!')
    ]

    @api.constrains('market_location_id')
    def _check_market_location_capacity(self):
        for rec in self:
            if rec.market_location_id and rec.market_location_id.market_size_id:
                max_capacity = rec.market_location_id.market_size_id.capacity
                count = self.search_count([('market_location_id', '=', rec.market_location_id.id)])
                if max_capacity and count > max_capacity:
                    raise ValidationError(_('Too many GHL Locations for this Market Location. Maximum allowed: %s') % max_capacity)

    def get_location_contacts(self):
        for rec in self:
            if not rec.location_id:
                _logger.error(f"Missing location_id for GHL Location {rec.id}")
                continue
            # Get agency token
            agency_token = self.env['ghl.agency.token'].sudo().search([], limit=1)
            if not agency_token or not agency_token.access_token:
                _logger.error("No agency access token found for GHL API call.")
                continue
            url = f'https://services.leadconnectorhq.com/contacts/?locationId={rec.location_id}'
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {agency_token.access_token}',
                'Version': '2021-07-28',
            }
            try:
                resp = requests.get(url, headers=headers)
                _logger.info(f"GHL contacts response for location {rec.location_id}: {resp.status_code} {resp.text}")
            except Exception as e:
                _logger.error(f"Error calling contacts API for location {rec.location_id}: {e}")

    @api.model_create_multi
    def create(self, vals_list):
        # Ensure vals_list is always a list
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        records = super(GHLLocation, self).create(vals_list)
        for record in records:
            record.sync_installed_locations()
        return records

    def sync_installed_locations(self):
        agency_token = self.env['ghl.agency.token'].sudo().search([], order='create_date desc', limit=1)
        if not agency_token or not agency_token.access_token:
            _logger.error("No agency access token found for GHL API call in sync_installed_locations.")
            return

        company_id = agency_token.company_id
        app_id = "6834710f642d2825854891ec"  # Or agency_token.app_id if you have that field
        print(f"company_id: {company_id}, app_id: {app_id}")
        url = f'https://services.leadconnectorhq.com/oauth/installedLocations?isInstalled=true&companyId={company_id}&appId={app_id}'

        # Check if token is expired
        current_time = Datetime.now()
        token_expiry = agency_token.token_expiry
        if token_expiry < current_time:
            _logger.info("GHL agency token has expired, attempting to refresh...")
            refresh_url = "https://services.leadconnectorhq.com/oauth/token"
            refresh_payload = {
                "client_id": agency_token.company_id,
                "grant_type": "refresh_token",
                "refresh_token": agency_token.refresh_token
            }
            refresh_headers = {
                'Content-Type': 'application/json'
            }
            try:
                resp = requests.post(refresh_url, json=refresh_payload, headers=refresh_headers, timeout=10)
                resp.raise_for_status()
                token_data = resp.json()
                # Update the token record
                agency_token.write({
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token', agency_token.refresh_token),
                    'token_expiry': Datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
                })
                _logger.info("Successfully refreshed GHL agency token.")
            except Exception as e:
                _logger.error(f"Failed to refresh GHL agency token: {e}")
                return

        # Use the (possibly refreshed) access token
        headers = {
            'Accept': 'application/json',
            'Version': '2021-07-28',
            'Authorization': f'Bearer {agency_token.access_token}',
        }
        _logger.info(f"Requesting {url} with headers: {headers}")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            _logger.info(f"Response status: {resp.status_code}, body: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            for loc in data.get('locations', []):
                location_id = loc.get('_id')
                name = loc.get('name')
                if location_id and name:
                    rec = self.sudo().search([('location_id', '=', location_id)], limit=1)
                    if rec:
                        rec.name = name
                        _logger.info(f"Updated GHL Location {rec.id} name to {name}")
        except Exception as e:
            _logger.error(f"Error syncing installed locations: {e}") 