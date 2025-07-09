# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class GHLOAuthConfig(models.Model):
    _name = 'ghl.oauth.config'
    _description = 'GHL OAuth Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', required=True, default='Default GHL OAuth Config')
    is_active = fields.Boolean(string='Active', default=True)

    # OAuth App Credentials
    client_id = fields.Char(string='Client ID', required=True, help='Your GHL app client ID')
    client_secret = fields.Char(string='Client Secret', required=True, help='Your GHL app client secret')
    redirect_uri = fields.Char(string='Redirect URI', required=True, help='OAuth callback URL')
    app_id = fields.Char(string='App ID', required=True, help='GHL Application ID for this OAuth config')

    # OAuth URLs
    authorization_url = fields.Char(
        string='Authorization URL',
        default='https://marketplace.gohighlevel.com/oauth/chooselocation',
        help='GHL authorization URL'
    )
    token_url = fields.Char(
        string='Token URL',
        default='https://services.leadconnectorhq.com/oauth/token',
        help='GHL token exchange URL'
    )

    # API Configuration
    api_base_url = fields.Char(
        string='API Base URL',
        default='https://services.leadconnectorhq.com',
        help='GHL API base URL'
    )
    api_version = fields.Char(
        string='API Version',
        default='2021-07-28',
        help='GHL API version'
    )

    # Scopes
    scopes = fields.Text(
        string='OAuth Scopes',
        default='locations.readonly contacts.readonly',
        help='Space-separated list of OAuth scopes'
    )

    # Additional Settings
    auto_refresh_tokens = fields.Boolean(
        string='Auto Refresh Tokens',
        default=True,
        help='Automatically refresh access tokens when they expire'
    )
    token_expiry_buffer = fields.Integer(
        string='Token Expiry Buffer (minutes)',
        default=5,
        help='Minutes before expiry to refresh token'
    )

    # Methods
    @api.model
    def get_active_config(self):
        """Get the active OAuth configuration"""
        config = self.search([('is_active', '=', True)], limit=1)
        if not config:
            _logger.warning("No active GHL OAuth configuration found")
            return None
        return config

    def get_authorization_url(self, location_id=None, state=None):
        """Generate authorization URL for OAuth flow"""
        if not self.is_active:
            return None

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scopes
        }

        if location_id:
            params['locationId'] = location_id
        if state:
            params['state'] = state

        # Build query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_url}?{query_string}"

    def validate_config(self):
        """Validate OAuth configuration"""
        errors = []

        if not self.client_id:
            errors.append("Client ID is required")
        if not self.client_secret:
            errors.append("Client Secret is required")
        if not self.redirect_uri:
            errors.append("Redirect URI is required")
        if not self.authorization_url:
            errors.append("Authorization URL is required")
        if not self.token_url:
            errors.append("Token URL is required")

        return errors

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure only one active config"""
        # Handle both single dict and list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('is_active'):
                # Deactivate other configs
                self.search([('is_active', '=', True)]).write({'is_active': False})
                break

        return super().create(vals_list)

    def write(self, vals):
        """Override write to ensure only one active config"""
        if vals.get('is_active'):
            # Deactivate other configs
            self.search([('is_active', '=', True), ('id', 'not in', self.ids)]).write({'is_active': False})
        return super().write(vals)

    def copy(self, default=None):
        """Override copy to ensure unique names"""
        default = default or {}
        default['name'] = f"{self.name} (Copy)"
        default['is_active'] = False
        return super().copy(default)
