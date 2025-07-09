from odoo import models, fields


class GHLAgencyToken(models.Model):
    _name = 'ghl.agency.token'
    _description = 'GHL Agency OAuth Token'

    company_id = fields.Char(string='Company ID', required=True, index=True)
    app_id = fields.Char(string='App ID', required=True, index=True,
                         help='GHL Application ID to differentiate between different apps')
    app_name = fields.Selection([
        ('web_scraper', 'Web Scraper'),
        ('dashboard', 'Advanced Dashboard')
    ], string='Application Name', required=True, default='dashboard')
    access_token = fields.Char(string='Access Token', required=True)
    refresh_token = fields.Char(string='Refresh Token', required=True)
    token_expiry = fields.Datetime(string='Token Expiry', required=True)
    create_date = fields.Datetime(string='Created On', readonly=True)
