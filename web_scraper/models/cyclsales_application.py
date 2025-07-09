# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class CyclSalesApplication(models.Model):
    _name = 'cyclsales.application'
    _description = 'CyclSales GHL Marketplace Application'
    _order = 'name'

    name = fields.Char(string='App Name', required=True, help='Name of the GHL marketplace application')
    client_id = fields.Char(string='Client ID', required=True, help='OAuth Client ID for the application')
    client_secret = fields.Char(string='Client Secret', required=True, help='OAuth Client Secret for the application')
    app_id = fields.Char(string='App ID', required=True, help='GHL Application ID')
    access_token = fields.Char(string='Access Token', help='Current access token for the application')
    refresh_token = fields.Char(string='Refresh Token', help='Refresh token for token renewal')
    token_expiry = fields.Datetime(string='Token Expiry', help='When the current access token expires')
    is_active = fields.Boolean(string='Active', default=True, help='Whether this application is currently active')
    notes = fields.Text(string='Notes', help='Additional notes about this application')

    # Computed fields
    token_status = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('missing', 'Missing')
    ], string='Token Status', compute='_compute_token_status', store=True, readonly=True)

    # Timestamps
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)

    @api.depends('access_token', 'token_expiry')
    def _compute_token_status(self):
        """Compute the status of the access token"""
        for record in self:
            if not record.access_token:
                record.token_status = 'missing'
            elif record.token_expiry and fields.Datetime.now() > record.token_expiry:
                record.token_status = 'expired'
            else:
                record.token_status = 'valid'

    @api.constrains('client_id', 'app_id')
    def _check_unique_identifiers(self):
        """Ensure client_id and app_id are unique"""
        for record in self:
            if record.client_id:
                duplicate_client = self.search([
                    ('client_id', '=', record.client_id),
                    ('id', '!=', record.id)
                ])
                if duplicate_client:
                    raise ValidationError(
                        _("Client ID '%s' is already used by another application.") % record.client_id)

            if record.app_id:
                duplicate_app = self.search([
                    ('app_id', '=', record.app_id),
                    ('id', '!=', record.id)
                ])
                if duplicate_app:
                    raise ValidationError(_("App ID '%s' is already used by another application.") % record.app_id)

    def action_refresh_token(self):
        """Action to refresh the access token"""
        self.ensure_one()
        try:
            if not self.refresh_token:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Token Refresh'),
                        'message': _('No refresh token available for %s.') % self.name,
                        'type': 'warning',
                    }
                }

            # GHL OAuth token endpoint
            token_url = "https://services.leadconnectorhq.com/oauth/token"

            # Prepare token refresh request
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            import requests
            response = requests.post(token_url, data=token_data, headers=headers)
            print(response.text)
            if response.status_code == 200:
                token_response = response.json()
                new_access_token = token_response.get('access_token')
                new_refresh_token = token_response.get('refresh_token', self.refresh_token)
                expires_in = token_response.get('expires_in')
                # Set token_expiry based on expires_in if available
                if expires_in:
                    expiry = fields.Datetime.now() + timedelta(seconds=int(expires_in))
                else:
                    expiry = fields.Datetime.now() + timedelta(hours=1)
                print(expiry)
                # Update the application with new tokens and expiry
                self.write({
                    'access_token': new_access_token,
                    'refresh_token': new_refresh_token,
                    'token_expiry': expiry,
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Token Refresh'),
                        'message': _('Token refreshed successfully for %s.') % self.name,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Token Refresh'),
                        'message': _('Failed to refresh token for %s: %s') % (self.name, response.text),
                        'type': 'danger',
                    }
                }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Token Refresh'),
                    'message': _('Error refreshing token for %s: %s') % (self.name, str(e)),
                    'type': 'danger',
                }
            }

    def action_test_connection(self):
        """Action to test the application connection"""
        self.ensure_one()
        try:
            if not self.access_token:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('No access token available for %s.') % self.name,
                        'type': 'warning',
                    }
                }

            # Use the provided companyId for the test
            company_id = 'Ipg8nKDPLYKsbtodR6LN'
            app_id = str(self.app_id)  # Ensure it's a string
            test_url = f"https://services.leadconnectorhq.com/oauth/installedLocations?companyId={company_id}&appId={app_id}&isInstalled=true"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Version': '2021-07-28',
                'Accept': 'application/json',
            }

            import requests
            response = requests.get(test_url, headers=headers)

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Connection test successful for %s.') % self.name,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Connection test failed for %s: %s') % (self.name, response.text),
                        'type': 'danger',
                    }
                }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Error testing connection for %s: %s') % (self.name, str(e)),
                    'type': 'danger',
                }
            }
